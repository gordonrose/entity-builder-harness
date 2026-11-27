// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.shared-scheduling-administration
//   version: 4
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Observe accepted migration prefixes and grant or prove scheduler identities only against complete immutable scope manifests.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts
//   - id: infra.04-deploy.entity-smoke.administration
//     path: infra/04.deploy/03.product/entrypoints/entity-smoke/administration.ts

import { createHash } from "node:crypto";
import { entityId, isoDateTime, isoDateTimeFromDate, systemUuidGenerator, uuid, type ISODateTime } from "@kanbien/core/shared";
import { createPlatformSchedule, platformOutboxQueueMessage, type PlatformSchedule } from "@kanbien/platform-persistence";
import type { PlatformJobName } from "@kanbien/platform-contracts";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { readPostgreSqlMigrationPrefix, postgreSqlPersistenceConfigurationTextRules, postgreSqlLoginNameRule, type PostgreSqlConnectionPool, type PostgreSqlMigrationManifest,
  createPostgreSqlPlatformScheduleStore, createPostgreSqlPlatformOutboxStore, createPostgreSqlPlatformProcessingStore,
  type PostgreSqlPersistenceConfiguration, type PostgreSqlTransactionalClient } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { AdministrationObservation, type PersistenceTaskDiagnosticOptions } from "./operation-diagnostics";
import { ensureBoundedLoginRole, ensureRdsIamAuthentication, requireBoundedExistingRole, postgreSqlPasswordAuthenticationPredicate } from "./role-credential";

type Privilege = "SELECT" | "INSERT" | "UPDATE" | "DELETE";
export type SchedulingDatabaseRole = "http" | "dispatch" | "worker";
export interface SchedulingDatabasePolicy {
  readonly database: string;
  readonly manifest: PostgreSqlMigrationManifest;
  readonly otherSchema: string;
  readonly migrationUsername: string;
  readonly httpUsername: string;
  readonly dispatchUsername: string;
  readonly workerUsername: string;
  readonly applicationTable: string;
  readonly httpApplicationPrivileges: readonly Privilege[];
  readonly workerApplicationPrivileges: readonly Privilege[];
}
export interface SchedulingDatabaseManifest {
  readonly schema: "kanbien/scheduling-database-state/v1";
  readonly manifest_sha256: string;
  readonly migration_count: number;
}
export interface SchedulingDatabaseState extends SchedulingDatabaseManifest {
  /** Initial synthetic qualification only, not a general production-readiness decision.
   * The activation controller requires every count to be zero BEFORE seeding
   * its separately owned proof rows. Future waiting/retry work is included. */
  readonly work_inventory: {
    readonly waiting_schedules: number;
    /** Pending OR leased; future retries remain actionable. */
    readonly pending_outbox: number;
    /** Claimed OR retry-eligible, irrespective of lease or retry time. */
    readonly active_processing: number;
  };
}

export interface SchedulingMigrationPrefix {
  readonly schema: "kanbien/scheduling-migration-prefix/v1";
  readonly manifest_sha256: string;
  readonly manifest_migration_count: number;
  readonly minimum_applied_migrations: number;
  readonly applied_migrations: number;
  readonly applied_prefix_sha256: string;
  readonly state: "partial" | "complete";
}

interface SchedulingProofBinding {
  readonly pool: PostgreSqlConnectionPool;
  readonly configuration: PostgreSqlPersistenceConfiguration;
  readonly policy: SchedulingDatabasePolicy;
  readonly jobName: PlatformJobName;
  readonly messageType: string;
}
export type SchedulingProofApplication =
  | { readonly kind: "acceptance"; readonly present: false }
  | { readonly kind: "acceptance"; readonly present: true; readonly fact_digest: string }
  | { readonly kind: "entity"; readonly present: false }
  | { readonly kind: "entity"; readonly present: true; readonly visibility: "active" | "archived"; readonly lifecycle_state: "active" | "deleted";
      readonly deleted_at?: string; readonly restore_eligible_until?: string };
export type SchedulingProofSelection =
  | { readonly kind: "schedule"; readonly id: unknown }
  | { readonly kind: "subject"; readonly id: unknown; readonly dueAt?: unknown; readonly subjectKind: string };

/** The operation owner reserves the identifier before submission. Never choose
 * a replacement ID here: a lost task response must reconcile the original. */
export async function seedSchedulingProof(options: SchedulingProofBinding & { readonly id: unknown; readonly dueAt: unknown },
  diagnostics?: PersistenceTaskDiagnosticOptions) {
  const observation = new AdministrationObservation("administration", diagnostics);
  return observation.runAsync(async () => {
    validateProofBinding(options, observation);
    const id = checkedProofId(options.id, observation), dueAt = checkedProofTime(options.dueAt, observation);
    const schedule = createPlatformSchedule({ jobName: options.jobName, dueAt }, { generate: () => uuid(id) });
    if (!schedule.ok) throw schedule.error;
    return transaction(options.pool, observation, false, async client => {
      observation.location("set-local-role", "identifier");
      await client.query({ text: `SET LOCAL ROLE ${quote(options.policy.migrationUsername)}` });
      const store = createPostgreSqlPlatformScheduleStore({ configuration: options.configuration, pool: clientPool(client) });
      observation.location("relation-query", "identifier");
      const prior = await store.get(schedule.value.id);
      let disposition: "created" | "already-exists" = "already-exists";
      if (prior !== null) {
        if (prior.jobName !== schedule.value.jobName || prior.dueAt !== schedule.value.dueAt || prior.subject !== undefined) throw rejected(observation, "row", "predicate-rejected");
      } else {
        observation.location("runtime-insert", "row");
        const created = await store.create(schedule.value);
        if (!created.ok) throw created.error;
        disposition = "created";
      }
      return { schema: "kanbien/scheduling-proof-seed/v1" as const, schedule_id: id, job_name: String(options.jobName), due_at: dueAt, disposition };
    });
  });
}

/** One exact selection, one read-only snapshot. This reports facts, not a
 * successful scheduler verdict; the custody-bound collector judges the chain. */
export async function observeSchedulingProof(options: SchedulingProofBinding & {
  readonly selection: SchedulingProofSelection;
  readonly readApplication: (client: PostgreSqlTransactionalClient, id: string) => Promise<SchedulingProofApplication>;
}, diagnostics?: PersistenceTaskDiagnosticOptions) {
  const observation = new AdministrationObservation("administration", diagnostics);
  return observation.runAsync(async () => {
    validateProofBinding(options, observation);
    const id = checkedProofId(options.selection.id, observation);
    const dueAt = options.selection.kind === "subject" && options.selection.dueAt !== undefined ? checkedProofTime(options.selection.dueAt, observation) : undefined;
    return transaction(options.pool, observation, true, async client => {
      observation.location("set-local-role", "identifier");
      await client.query({ text: `SET LOCAL ROLE ${quote(options.policy.migrationUsername)}` });
      await client.query({ text: "SET LOCAL statement_timeout = '5000ms'" });
      const pool = clientPool(client), configuration = options.configuration;
      // Some existing store readers report a malformed row and return null.
      // A proof must not confuse that observation with genuine physical absence.
      let readDiagnostic: DiagnosticRecord | undefined;
      const stores = { configuration, pool, onDiagnostic(record: DiagnosticRecord) { readDiagnostic ??= record; } };
      async function checkedRead<T>(read: () => Promise<T>): Promise<T> {
        readDiagnostic = undefined;
        const value = await read();
        if (readDiagnostic !== undefined) throw Object.assign(new Error("PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED"), { diagnosticRecord: readDiagnostic });
        return value;
      }
      let selectedId: string | undefined = id;
      if (options.selection.kind === "subject") {
        observation.location("relation-query", "identifier");
        const selected = await client.query<{ id: string }>({
          text: `SELECT id FROM ${quote(configuration.schema)}.platform_schedule WHERE subject_kind=$1 AND subject_id=$2${dueAt === undefined ? "" : " AND due_at=$3"} ORDER BY id LIMIT 2`,
          values: [options.selection.subjectKind, id, ...(dueAt === undefined ? [] : [dueAt])],
        });
        if (selected.rows.length > 1) throw rejected(observation, "row", "count-mismatch");
        if (dueAt === undefined && selected.rows.length !== 0) throw rejected(observation, "row", "predicate-rejected");
        selectedId = selected.rows.length === 0 ? undefined : checkedProofId(selected.rows[0]?.id, observation);
      }
      observation.location("relation-query", "row");
      const schedule = selectedId === undefined ? null : await checkedRead(() => createPostgreSqlPlatformScheduleStore(stores).get(entityId<"PlatformScheduleId">(selectedId!)));
      if (schedule !== null && (String(schedule.id) !== selectedId || schedule.jobName !== options.jobName || options.selection.kind === "schedule" && schedule.subject !== undefined
        || options.selection.kind === "subject" && (schedule.subject?.kind !== options.selection.subjectKind || schedule.subject.id !== id || schedule.dueAt !== dueAt))) throw rejected(observation, "row", "predicate-rejected");
      const outbox = schedule?.outboxEntryId === undefined ? null : await checkedRead(() => createPostgreSqlPlatformOutboxStore(stores).get(schedule.outboxEntryId!));
      if (outbox !== null && (outbox.entry.id !== schedule?.outboxEntryId || outbox.entry.subject.kind !== "platform.schedule"
        || String(outbox.entry.subject.id) !== String(schedule?.id) || outbox.entry.messageType !== options.messageType || outbox.entry.messageVersion !== 1
        || outbox.entry.tenantId !== undefined)) throw rejected(observation, "row", "predicate-rejected");
      const processing = schedule?.outboxEntryId === undefined ? null : await checkedRead(() => createPostgreSqlPlatformProcessingStore(stores).get(schedule.outboxEntryId!));
      if (processing !== null && processing.outboxEntryId !== schedule?.outboxEntryId) throw rejected(observation, "row", "id-mismatch");
      const application = await options.readApplication(client, id);
      observation.location("relation-query", "row");
      const time = await client.query<{ observed_at: Date }>({ text: "SELECT clock_timestamp() AS observed_at" });
      if (time.rows.length !== 1 || !(time.rows[0]?.observed_at instanceof Date) || !Number.isFinite(time.rows[0].observed_at.getTime())) throw rejected(observation, "row", "predicate-rejected");
      const observedAt = isoDateTimeFromDate(time.rows[0].observed_at);
      const deliveryMessage = outbox === null ? null : platformOutboxQueueMessage(outbox.entry, observedAt);
      if (deliveryMessage !== null && !deliveryMessage.ok) throw deliveryMessage.error;
      return { schema: "kanbien/scheduling-proof-observation/v1" as const,
        selection: options.selection.kind === "schedule" ? { kind: "schedule" as const, id } : { kind: "subject" as const, id, ...(dueAt === undefined ? {} : { due_at: dueAt }) },
        observed_at: observedAt, schedule: schedule === null ? null : scheduleProjection(schedule),
        delivery_message: deliveryMessage === null ? null : deliveryMessage.value,
        outbox: outbox === null ? null : { id: String(outbox.entry.id), state: outbox.state, attempt: Number(outbox.attempt), created_at: outbox.entry.createdAt,
          ...(outbox.publishedAt === undefined ? {} : { published_at: outbox.publishedAt }) },
        processing: processing === null ? null : { outbox_entry_id: String(processing.outboxEntryId), state: processing.state, attempt: Number(processing.attempt),
          ...(processing.releasedAt === undefined ? {} : { released_at: processing.releasedAt }), ...(processing.retryAt === undefined ? {} : { retry_at: processing.retryAt }),
          ...(processing.completion === undefined ? {} : { completion: { outcome: processing.completion.outcome, completed_at: processing.completion.completedAt } }) },
        application };
    });
  });
}
function scheduleProjection(schedule: PlatformSchedule) {
  return { id: String(schedule.id), job_name: String(schedule.jobName), due_at: schedule.dueAt, state: schedule.state,
    ...(schedule.subject === undefined ? {} : { subject: { kind: String(schedule.subject.kind), id: String(schedule.subject.id) } }),
    ...(schedule.outboxEntryId === undefined ? {} : { outbox_entry_id: String(schedule.outboxEntryId) }) };
}
function validateProofBinding(options: SchedulingProofBinding, observation: AdministrationObservation): void {
  validatePolicy(options.policy, observation);
  if (options.configuration.schema !== options.policy.manifest.schema || options.configuration.database !== options.policy.database) throw rejected(observation, "configuration", "predicate-rejected");
}
function checkedProofId(value: unknown, observation: AdministrationObservation): string {
  if (typeof value !== "string") throw rejected(observation, "identifier", value === undefined ? "missing" : "wrong-type");
  const checked = uuid(value);
  if (!checked.ok) throw observation.rejected(checked.error, "identifier", "pattern", undefined, checked.error);
  return checked.value;
}
function checkedProofTime(value: unknown, observation: AdministrationObservation): ISODateTime {
  if (typeof value !== "string") throw rejected(observation, "configuration", value === undefined ? "missing" : "wrong-type");
  const checked = isoDateTime(value);
  if (!checked.ok) throw observation.rejected(checked.error, "configuration", "pattern", undefined, checked.error);
  return checked.value;
}

/** Journal evidence only: no scheduler tables, permissions or activation claim. */
export async function observeSchedulingMigrationPrefix(pool: PostgreSqlConnectionPool, policy: SchedulingDatabasePolicy,
  diagnostics?: PersistenceTaskDiagnosticOptions): Promise<SchedulingMigrationPrefix> {
  const observation = new AdministrationObservation("migration-state", diagnostics);
  return observation.runAsync(async () => {
    validatePolicy(policy, observation);
    return transaction(pool, observation, true, async client => {
      await acquireObservationLock(client, policy, observation);
      observation.location("set-local-role", "identifier");
      await client.query({ text: `SET LOCAL ROLE ${quote(policy.migrationUsername)}` });
      await requireSchemaOwnership(client, policy, observation);
      observation.location("history-read", "migration-count");
      await client.query({ text: "SET LOCAL statement_timeout = '5000ms'" });
      const result = await readPostgreSqlMigrationPrefix(client, policy.manifest);
      if (!result.ok) throw result.error;
      observation.location("relation-query", "relation-name");
      const owner = await client.query<{ owner: string }>({ text: "SELECT pg_get_userbyid(c.relowner) AS owner FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=$1 AND c.relname='platform_migration_history' AND c.relkind IN ('r','p')", values: [policy.manifest.schema] });
      if (owner.rows.length !== 1 || owner.rows[0]?.owner !== policy.migrationUsername) throw rejected(observation, "relation-name", "predicate-rejected");
      return { schema: "kanbien/scheduling-migration-prefix/v1", manifest_sha256: migrationDigest(policy.manifest.migrations),
        manifest_migration_count: policy.manifest.migrations.length, minimum_applied_migrations: policy.manifest.continuation!.minimumAppliedMigrations,
        applied_migrations: result.value, applied_prefix_sha256: migrationDigest(policy.manifest.migrations.slice(0, result.value)),
        state: result.value === policy.manifest.migrations.length ? "complete" : "partial" };
    });
  });
}

/** Target composition supplies this policy; no arbitrary SQL or role is accepted from a request. */
export async function observeSchedulingDatabaseState(pool: PostgreSqlConnectionPool, policy: SchedulingDatabasePolicy,
  diagnostics?: PersistenceTaskDiagnosticOptions): Promise<SchedulingDatabaseState> {
  const observation = new AdministrationObservation("migration-state", diagnostics);
  return observation.runAsync(async () => {
    validatePolicy(policy, observation);
    return transaction(pool, observation, true, async client => {
      await acquireObservationLock(client, policy, observation);
      observation.location("set-local-role", "identifier");
      await client.query({ text: `SET LOCAL ROLE ${quote(policy.migrationUsername)}` });
      return requireCompleteState(client, policy, observation);
    });
  });
}

export async function grantSchedulingDatabaseAccess(pool: PostgreSqlConnectionPool, policy: SchedulingDatabasePolicy,
  diagnostics?: PersistenceTaskDiagnosticOptions): Promise<SchedulingDatabaseState> {
  const observation = new AdministrationObservation("application-access", diagnostics);
  return observation.runAsync(async () => {
    validatePolicy(policy, observation);
    return transaction(pool, observation, false, async client => {
      await client.query({ text: "SELECT pg_advisory_xact_lock(hashtext($1))", values: [`kanbien-postgresql-migration:${policy.manifest.schema}`] });
      observation.location("set-local-role", "identifier");
      await client.query({ text: `SET LOCAL ROLE ${quote(policy.migrationUsername)}` });
      const state = await requireCompleteState(client, policy, observation);
      await client.query({ text: "RESET ROLE" });
      const connection = clientPool(client);
      for (const [ordinal, role] of roles.entries()) {
        observation.location("runtime-boundary", "role-facts", ordinal);
        const username = roleName(policy, role);
        if (role !== "http") {
          await ensureBoundedLoginRole(connection, { username }, diagnostics);
          await ensureRdsIamAuthentication(connection, { username }, diagnostics);
        } else await requireBoundedExistingRole(connection, { username }, { requireLogin: true }, diagnostics);
        await requireIsolatedRole(connection, username, observation);
        observation.location("database-access", "identifier", ordinal);
        await client.query({ text: `GRANT CONNECT ON DATABASE ${quote(policy.database)} TO ${quote(username)}` });
      }
      observation.location("set-local-role", "identifier");
      await client.query({ text: `SET LOCAL ROLE ${quote(policy.migrationUsername)}` });
      for (const [ordinal, role] of roles.entries()) {
        observation.location("grant-runtime", "identifier", ordinal);
        const username = quote(roleName(policy, role)), schema = quote(policy.manifest.schema);
        await client.query({ text: `REVOKE ALL ON SCHEMA ${schema} FROM ${username}` });
        await client.query({ text: `GRANT USAGE ON SCHEMA ${schema} TO ${username}` });
        await client.query({ text: `REVOKE ALL ON ALL TABLES IN SCHEMA ${schema} FROM ${username}` });
        await client.query({ text: `REVOKE ALL ON ALL SEQUENCES IN SCHEMA ${schema} FROM ${username}` });
        await client.query({ text: `REVOKE ALL ON ALL FUNCTIONS IN SCHEMA ${schema} FROM ${username}` });
        await client.query({ text: `ALTER DEFAULT PRIVILEGES IN SCHEMA ${schema} REVOKE ALL ON TABLES FROM ${username}` });
        for (const [table, privileges] of Object.entries(matrix(policy, role))) {
          if (privileges.length > 0) await client.query({ text: `GRANT ${privileges.join(", ")} ON ${schema}.${quote(table)} TO ${username}` });
        }
      }
      observation.location("set-local-role", "identifier");
      await client.query({ text: "RESET ROLE" });
      const administrator = await client.query<{ allowed: boolean }>({ text: `SELECT ${postgreSqlPasswordAuthenticationPredicate} AS allowed` });
      if (administrator.rows[0]?.allowed !== true) throw rejected(observation, "member", "not-true");
      return state;
    });
  });
}

/** Each pool must authenticate as its selected LOGIN role, never SET ROLE from administrator. */
export async function proveSchedulingDatabaseAccess(policy: SchedulingDatabasePolicy,
  createAuthenticatedPool: (role: SchedulingDatabaseRole, username: string) => PostgreSqlConnectionPool,
  diagnostics?: PersistenceTaskDiagnosticOptions): Promise<SchedulingDatabaseManifest> {
  const observation = new AdministrationObservation("runtime-privilege", diagnostics);
  return observation.runAsync(async () => {
    validatePolicy(policy, observation);
    for (const [ordinal, role] of roles.entries()) {
      observation.location("pool-construction", "identifier", ordinal);
      const username = roleName(policy, role), pool = createAuthenticatedPool(role, username);
      let failed = false;
      try {
        await requireBoundedExistingRole(pool, { username }, { requireLogin: true }, diagnostics);
        await requireIsolatedRole(pool, username, observation);
        await transaction(pool, observation, false, async client => {
          observation.location("identity-boundary", "identifier", ordinal);
          const identity = await client.query<{ current_user: string; session_user: string; database: string }>({ text: "SELECT current_user, session_user, current_database() AS database" });
          if (identity.rows.length !== 1 || identity.rows[0]?.current_user !== username || identity.rows[0]?.session_user !== username || identity.rows[0]?.database !== policy.database) throw rejected(observation, "identifier", "id-mismatch", ordinal);
          const grants = matrix(policy, role);
          const schemaRights = await client.query<{ allowed: boolean }>({ text: "SELECT has_database_privilege(current_user, $1, 'CONNECT') AND NOT has_database_privilege(current_user, $1, 'CREATE') AND has_schema_privilege(current_user, $2, 'USAGE') AND NOT has_schema_privilege(current_user, $2, 'CREATE') AS allowed", values: [policy.database, policy.manifest.schema] });
          if (schemaRights.rows[0]?.allowed !== true) throw rejected(observation, "schema", "not-true", ordinal);
          for (const [table, allowed] of Object.entries(grants)) {
            const relation = `${quote(policy.manifest.schema)}.${quote(table)}`;
            // Effective rights include PUBLIC and inherited memberships. Check each
            // right independently: a missing SELECT must not hide an unsafe INSERT.
            for (const privilege of [...privileges, "TRUNCATE", "REFERENCES", "TRIGGER"] as const) {
              const rights = await client.query<{ allowed: boolean }>({ text: "SELECT has_table_privilege(current_user, $1, $2) AS allowed", values: [relation, privilege] });
              if (rights.rows.length !== 1 || rights.rows[0]?.allowed !== (allowed as readonly string[]).includes(privilege)) throw rejected(observation, "member", "predicate-rejected", ordinal);
            }
            for (const privilege of privileges) {
              const statement = privilege === "SELECT" ? `SELECT * FROM ${relation} LIMIT 0`
                : privilege === "INSERT" ? `INSERT INTO ${relation} SELECT * FROM ${relation} WHERE FALSE`
                : privilege === "UPDATE" ? `UPDATE ${relation} SET ${quote(primaryColumn(table))} = ${quote(primaryColumn(table))} WHERE FALSE`
                : `DELETE FROM ${relation} WHERE FALSE`;
              observation.location("permission-code", "provider-code", ordinal);
              await probe(client, statement, allowed.includes(privilege), observation);
            }
          }
          const schema = quote(policy.manifest.schema);
          await probe(client, `CREATE TABLE ${schema}.scheduling_privilege_probe (id text)`, false, observation);
          await probe(client, `SELECT * FROM ${quote(policy.otherSchema)}.platform_schedule LIMIT 0`, false, observation);
          await probe(client, `INSERT INTO ${schema}.platform_migration_history (migration_id, checksum, tool_version) VALUES ('v9999_permission_probe', '${"0".repeat(64)}', 'permission-probe')`, false, observation);
          // Real owned INSERT/UPDATE statements, all rolled back. Existing rows are never selected for mutation.
          if (role === "dispatch") {
            const id = proofIdentifier();
            await client.query({ text: `INSERT INTO ${schema}.platform_outbox (id, subject_kind, subject_id, message_type, message_version, delivery_policy, created_at, state, attempt) VALUES ($1, 'platform.schedule', $1, 'platform.schedule.run', 1, 'at-least-once', CURRENT_TIMESTAMP, 'pending', 0)`, values: [id] });
            await client.query({ text: `UPDATE ${schema}.platform_outbox SET attempt = 1 WHERE id = $1`, values: [id] });
          }
          if (role === "worker") {
            await client.query({ text: `INSERT INTO ${schema}.platform_processing (outbox_entry_id, state, attempt) VALUES ($1, 'retry-eligible', 1)`, values: [proofIdentifier()] });
          }
        }, true);
      } catch (cause) { failed = true; observation.failed(cause); throw cause; }
      finally { await cleanup(observation, failed, [{ phase: "pool-end", action: () => pool.end() }]); }
    }
    return stateFor(policy);
  });
}

async function acquireObservationLock(client: PostgreSqlTransactionalClient, policy: SchedulingDatabasePolicy, observation: AdministrationObservation): Promise<void> {
  // This SELECT fixes the repeatable-read snapshot. Never wait here and
  // later present a pre-wait snapshot after another migration commits.
  // A successful observation remains point-in-time, not activation authority.
  observation.location("history-read", "row");
  const lock = await client.query<{ acquired: boolean }>({ text: "SELECT pg_try_advisory_xact_lock(hashtext($1)) AS acquired", values: [`kanbien-postgresql-migration:${policy.manifest.schema}`] });
  if (lock.rows.length !== 1) throw rejected(observation, "row", "count-mismatch");
  if (lock.rows[0]?.acquired !== true) throw rejected(observation, "row", "not-true");
}

async function requireSchemaOwnership(client: PostgreSqlTransactionalClient, policy: SchedulingDatabasePolicy, observation: AdministrationObservation): Promise<void> {
  observation.location("schema-ownership", "schema");
  const destination = await client.query<{ database: string; owner: string }>({ text: "SELECT current_database() AS database, pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname=$1", values: [policy.manifest.schema] });
  if (destination.rows.length !== 1 || destination.rows[0]?.database !== policy.database || destination.rows[0]?.owner !== policy.migrationUsername) throw rejected(observation, "schema", "predicate-rejected");
}

async function requireCompleteState(client: PostgreSqlTransactionalClient, policy: SchedulingDatabasePolicy, observation: AdministrationObservation): Promise<SchedulingDatabaseState> {
  await requireSchemaOwnership(client, policy, observation);
  observation.location("history-read", "migration-count");
  const history = await client.query<{ migration_id: string; checksum: string }>({ text: `SELECT migration_id, checksum FROM ${quote(policy.manifest.schema)}.platform_migration_history ORDER BY migration_id LIMIT $1`, values: [policy.manifest.migrations.length + 1] });
  if (history.rows.length !== policy.manifest.migrations.length) throw rejected(observation, "migration-count", "count-mismatch");
  for (const [ordinal, row] of history.rows.entries()) {
    if (row.migration_id !== policy.manifest.migrations[ordinal]!.id) throw rejected(observation, "migration-id", "id-mismatch", ordinal);
    if (row.checksum !== policy.manifest.migrations[ordinal]!.checksum) throw rejected(observation, "migration-checksum", "checksum-mismatch", ordinal);
  }
  observation.location("relation-query", "relation-name");
  const expectedTables = ["platform_schedule", "platform_outbox", "platform_processing", "platform_record_change", "platform_migration_history", policy.applicationTable];
  const tables = await client.query<{ name: string; owner: string }>({ text: "SELECT c.relname AS name, pg_get_userbyid(c.relowner) AS owner FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=$1 AND c.relkind IN ('r','p') AND c.relname=ANY($2::text[])", values: [policy.manifest.schema, expectedTables] });
  if (tables.rows.length !== expectedTables.length || tables.rows.some(row => row.owner !== policy.migrationUsername)) throw rejected(observation, "relation-name", "predicate-rejected");
  const shape = await client.query<{ allowed: boolean }>({ text: "SELECT (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=$1 AND ((table_name='platform_schedule' AND column_name IN ('outbox_entry_id','subject_kind','subject_id')) OR (table_name='platform_processing' AND column_name='retry_at'))) = 4 AND EXISTS (SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname=$1 AND t.relname='platform_schedule' AND c.conname='platform_schedule_state_check' AND pg_get_constraintdef(c.oid) LIKE '%blocked-invalid-row%' AND pg_get_constraintdef(c.oid) LIKE '%blocked-job-unavailable%') AS allowed", values: [policy.manifest.schema] });
  if (shape.rows[0]?.allowed !== true) throw rejected(observation, "relation-kind", "not-true");
  const functions = await client.query<{ count: number }>({ text: "SELECT COUNT(*)::integer AS count FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=$1", values: [policy.manifest.schema] });
  if (functions.rows[0]?.count !== 0) throw rejected(observation, "function-count", "not-zero");
  const other = await client.query<{ exists: boolean }>({ text: "SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=$1 AND c.relname='platform_schedule' AND c.relkind IN ('r','p')) AS exists", values: [policy.otherSchema] });
  if (other.rows[0]?.exists !== true) throw rejected(observation, "relation-name", "missing");
  // A bounded read-only snapshot informs the initial empty-before-proof gate.
  // Never infer emptiness from a failed query or exclude a caller-selected ID.
  observation.location("runtime-read", "read-count");
  await client.query({ text: "SET LOCAL statement_timeout = '5000ms'" });
  const schema = quote(policy.manifest.schema);
  const inventory = await client.query<SchedulingDatabaseState["work_inventory"]>({ text: `SELECT
    (SELECT COUNT(*)::integer FROM ${schema}.platform_schedule WHERE state='waiting') AS waiting_schedules,
    (SELECT COUNT(*)::integer FROM ${schema}.platform_outbox WHERE state IN ('pending','leased')) AS pending_outbox,
    (SELECT COUNT(*)::integer FROM ${schema}.platform_processing WHERE state IN ('claimed','retry-eligible')) AS active_processing` });
  const row = inventory.rows[0];
  const values = row === undefined ? [] : [row.waiting_schedules, row.pending_outbox, row.active_processing];
  if (inventory.rows.length !== 1 || values.length !== 3 || values.some(value => !Number.isSafeInteger(value) || value < 0)) throw rejected(observation, "read-count", "predicate-rejected");
  return { ...stateFor(policy), work_inventory: { waiting_schedules: row!.waiting_schedules, pending_outbox: row!.pending_outbox, active_processing: row!.active_processing } };
}

async function requireIsolatedRole(pool: PostgreSqlConnectionPool, username: string, observation: AdministrationObservation): Promise<void> {
  observation.location("runtime-role-query", "member");
  const result = await pool.query<{ allowed: boolean }>({ text: "WITH RECURSIVE memberships(oid) AS (SELECT oid FROM pg_roles WHERE rolname=$1 UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON p.oid=m.member) SELECT NOT EXISTS (SELECT 1 FROM memberships m JOIN pg_roles r ON r.oid=m.oid WHERE r.rolname NOT IN ($1, 'rds_iam')) AS allowed", values: [username] });
  if (result.rows[0]?.allowed !== true) throw rejected(observation, "member", "not-true");
}
async function probe(client: PostgreSqlTransactionalClient, text: string, permitted: boolean, observation: AdministrationObservation): Promise<void> {
  await client.query({ text: "SAVEPOINT scheduling_permission_probe" });
  let failed = false;
  try {
    let succeeded = false, code: unknown, failure: unknown;
    try { await client.query({ text }); succeeded = true; }
    catch (cause) { failure = cause; code = typeof cause === "object" && cause !== null ? Object.getOwnPropertyDescriptor(cause, "code")?.value : undefined; }
    if (permitted && !succeeded) throw failure;
    if (!permitted && (succeeded || code !== "42501")) throw observation.rejected(new Error("PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED"), "provider-code", succeeded ? "permission-permitted" : "denial-code-mismatch", undefined, failure);
  } catch (cause) { failed = true; observation.failed(cause); throw cause; }
  finally {
    await cleanup(observation, failed, [
      { phase: "rollback", action: () => client.query({ text: "ROLLBACK TO SAVEPOINT scheduling_permission_probe" }) },
      { phase: "permission-code", action: () => client.query({ text: "RELEASE SAVEPOINT scheduling_permission_probe" }) },
    ]);
  }
}
async function transaction<T>(pool: PostgreSqlConnectionPool, observation: AdministrationObservation, readOnly: boolean,
  action: (client: PostgreSqlTransactionalClient) => Promise<T>, rollback = false): Promise<T> {
  observation.location("pool-connect"); const client = await pool.connect();
  let failed = false, rollbackAttempted = false;
  try {
    observation.location("begin"); await client.query({ text: readOnly ? "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY" : "BEGIN" });
    await client.query({ text: "SET LOCAL lock_timeout = '30000ms'" });
    const value = await action(client);
    observation.location(rollback ? "rollback" : "commit"); rollbackAttempted = rollback; await client.query({ text: rollback ? "ROLLBACK" : "COMMIT" });
    return value;
  } catch (cause) {
    failed = true;
    observation.failed(cause); const restore = observation.checkpoint();
    try { if (!rollbackAttempted) { observation.location("rollback"); await client.query({ text: "ROLLBACK" }); } }
    catch (rollbackCause) { observation.failed(rollbackCause); }
    restore(); throw cause;
  } finally { await cleanup(observation, failed, [{ phase: "client-release", action: () => client.release() }]); }
}
/** Report every cleanup fault while retaining the first operation failure. */
async function cleanup(observation: AdministrationObservation, primaryFailed: boolean,
  steps: readonly { phase: Parameters<AdministrationObservation["location"]>[0]; action: () => unknown | Promise<unknown> }[]): Promise<void> {
  const restore = observation.checkpoint();
  let failed = false, failure: unknown;
  for (const step of steps) {
    observation.location(step.phase);
    try { await step.action(); }
    catch (cause) { observation.failed(cause); if (!failed) { failed = true; failure = cause; } }
  }
  restore();
  if (!primaryFailed && failed) throw observation.retained(failure);
}
function matrix(policy: SchedulingDatabasePolicy, role: SchedulingDatabaseRole): Record<string, readonly Privilege[]> {
  return { platform_schedule: role === "http" ? ["SELECT", "INSERT", "UPDATE"] : role === "dispatch" ? ["SELECT", "UPDATE"] : ["SELECT"],
    platform_outbox: role === "http" ? ["SELECT", "INSERT"] : role === "dispatch" ? ["SELECT", "INSERT", "UPDATE"] : ["SELECT"],
    platform_processing: role === "worker" ? ["SELECT", "INSERT", "UPDATE"] : [],
    platform_record_change: [], platform_migration_history: [],
    [policy.applicationTable]: role === "http" ? policy.httpApplicationPrivileges : role === "worker" ? policy.workerApplicationPrivileges : [] };
}
function primaryColumn(table: string): string { return table === "platform_processing" ? "outbox_entry_id" : table === "platform_migration_history" ? "migration_id" : table === "core_server_persistence_acceptance" ? "record_id" : "id"; }
function roleName(policy: SchedulingDatabasePolicy, role: SchedulingDatabaseRole): string { return role === "http" ? policy.httpUsername : role === "dispatch" ? policy.dispatchUsername : policy.workerUsername; }
function clientPool(client: PostgreSqlTransactionalClient): PostgreSqlConnectionPool { return { query: statement => client.query(statement), connect: async () => client, end: async () => undefined }; }
function migrationDigest(migrations: PostgreSqlMigrationManifest["migrations"]): string { return createHash("sha256").update(JSON.stringify(migrations.map(({ id, checksum }) => ({ id, checksum })))).digest("hex"); }
function stateFor(policy: SchedulingDatabasePolicy): SchedulingDatabaseManifest { return { schema: "kanbien/scheduling-database-state/v1", manifest_sha256: migrationDigest(policy.manifest.migrations), migration_count: policy.manifest.migrations.length }; }
function quote(value: string): string { return `"${value}"`; }
function proofIdentifier(): string {
  const generated = systemUuidGenerator.generate();
  if (!generated.ok) throw generated.error;
  return `scheduler-permission-${generated.value}`;
}
const roles = ["http", "dispatch", "worker"] as const;
const privileges = ["SELECT", "INSERT", "UPDATE", "DELETE"] as const;
function validatePolicy(policy: SchedulingDatabasePolicy, observation: AdministrationObservation): void {
  const identifiers = [policy.database, policy.manifest.schema, policy.otherSchema, policy.migrationUsername, policy.httpUsername, policy.dispatchUsername, policy.workerUsername, policy.applicationTable];
  for (const [ordinal, identifier] of identifiers.entries()) {
    const rule = ordinal >= 3 && ordinal <= 6 ? postgreSqlLoginNameRule : postgreSqlPersistenceConfigurationTextRules.schema;
    if (typeof identifier !== "string" || !rule.pattern.test(identifier)) throw rejected(observation, "identifier", "pattern", ordinal);
  }
  if (new Set([policy.migrationUsername, policy.httpUsername, policy.dispatchUsername, policy.workerUsername]).size !== 4 || policy.manifest.schema === policy.otherSchema) throw rejected(observation, "identifier", "predicate-rejected");
  if (policy.manifest.migrations.length === 0 || ["platform_schedule", "platform_outbox", "platform_processing", "platform_record_change", "platform_migration_history"].includes(policy.applicationTable) || [...policy.httpApplicationPrivileges, ...policy.workerApplicationPrivileges].some(value => !privileges.includes(value))) throw rejected(observation, "configuration", "predicate-rejected");
}
function rejected(observation: AdministrationObservation, field: Parameters<AdministrationObservation["rejected"]>[1], condition: Parameters<AdministrationObservation["rejected"]>[2], ordinal?: number): Error {
  return observation.rejected(new Error("PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED"), field, condition, ordinal);
}
