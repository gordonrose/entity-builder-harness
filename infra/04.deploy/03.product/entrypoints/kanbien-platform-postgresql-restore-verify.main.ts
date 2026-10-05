// Verify the one fixed harmless smoke record on an isolated restored database.
// The host is supplied only by the governed recovery runner and is restricted
// to the reviewed staging RDS recovery-name pattern before a TLS connection.

import { outboxEntryId } from "@kanbien/core/persistence";
import { postgreSqlPersistenceFoundationMigration } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import {
  type RestoreVerificationFailureCategory,
  type RestoreVerificationFailureDetails,
  type RestoreVerificationObserved,
  type RestoreVerificationPhase,
  closePool,
  configurationFromEnvironment,
  connectionPool,
  secretFromEnvironment,
  writeOutcome,
  writeRestoreVerificationFailure,
} from "./kanbien-platform-postgresql-task";
import { kanbienPlatformSmokePostgreSqlMigration } from "./kanbien-platform-postgresql-persistence";

const fixedWorkItem = "postgresql-stage6-smoke-20260926-a";

async function main(): Promise<void> {
  let pool;
  let phase: RestoreVerificationPhase = "input-validation";
  const observed: Record<"migration_checksums" | "accepted_work_item" | "published_outbox" | "completed_processing", RestoreVerificationObserved> = {
    migration_checksums: "not-queried",
    accepted_work_item: "not-queried",
    published_outbox: "not-queried",
    completed_processing: "not-queried",
  };
  try {
    const configuration = configurationFromEnvironment();
    const runtime = secretFromEnvironment("RELATIONAL_RUNTIME_SECRET_JSON");
    const restoreHost = restoreHostFromEnvironment();
    pool = connectionPool({ ...runtime, host: restoreHost }, configuration.runtimeSecretArn, configuration.schema);
    phase = "connection";
    await pool.query({ text: "SELECT 1" });
    phase = "migration-checksum-verification";
    const foundationMigration = postgreSqlPersistenceFoundationMigration(configuration.schema);
    const smokeMigration = kanbienPlatformSmokePostgreSqlMigration(configuration.schema);
    const migrationHistory = await pool.query<{ readonly count: string }>({
      text: 'SELECT COUNT(*)::text AS count FROM "platform_smoke"."platform_migration_history" WHERE (migration_id = $1 AND checksum = $2) OR (migration_id = $3 AND checksum = $4)',
      values: [foundationMigration.id, foundationMigration.checksum, smokeMigration.id, smokeMigration.checksum],
    });
    observed.migration_checksums = countBucket(migrationHistory.rows[0]?.count);
    phase = "work-item-verification";
    const workItem = await pool.query<{ readonly count: string }>({
      text: 'SELECT COUNT(*)::text AS count FROM "platform_smoke"."platform_smoke_work_item" WHERE id = $1 AND state = $2',
      values: [fixedWorkItem, "accepted"],
    });
    observed.accepted_work_item = countBucket(workItem.rows[0]?.count);
    phase = "outbox-verification";
    const outbox = await pool.query<{ readonly count: string }>({
      text: 'SELECT COUNT(*)::text AS count FROM "platform_smoke"."platform_outbox" WHERE id = $1 AND state = $2 AND published_at IS NOT NULL',
      values: [String(outboxEntryId("platform-smoke.work-item-accepted." + fixedWorkItem)), "published"],
    });
    observed.published_outbox = countBucket(outbox.rows[0]?.count);
    phase = "processing-state-verification";
    const processing = await pool.query<{ readonly count: string }>({
      text: 'SELECT COUNT(*)::text AS count FROM "platform_smoke"."platform_processing" WHERE outbox_entry_id = $1 AND state = $2 AND completion_outcome = $3 AND completed_at IS NOT NULL',
      values: [String(outboxEntryId("platform-smoke.work-item-accepted." + fixedWorkItem)), "completed", "succeeded"],
    });
    observed.completed_processing = countBucket(processing.rows[0]?.count);
    if (migrationHistory.rows[0]?.count !== "2" || workItem.rows[0]?.count !== "1" || outbox.rows[0]?.count !== "1" || processing.rows[0]?.count !== "1") {
      throw new Error("RELATIONAL_RESTORE_PROOF_NOT_FOUND");
    }
    writeOutcome("restore_verified", "succeeded");
  } catch (error) {
    writeRestoreVerificationFailure(restoreVerificationFailureDetails(error, phase, observed));
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

export function restoreVerificationFailureDetails(
  error: unknown,
  phase: RestoreVerificationPhase,
  observed: Readonly<Record<"migration_checksums" | "accepted_work_item" | "published_outbox" | "completed_processing", RestoreVerificationObserved>>,
): RestoreVerificationFailureDetails {
  const code = errorProperty(error, "code");
  const message = errorProperty(error, "message");
  const failure_category: RestoreVerificationFailureCategory =
    message === "RELATIONAL_TASK_CERTIFICATE_AUTHORITY_UNAVAILABLE" ? "restore-certificate-authority-unavailable"
      : message === "RELATIONAL_RESTORE_PROOF_NOT_FOUND" && observed.migration_checksums !== "two" ? "restore-migration-checksum-mismatch"
        : message === "RELATIONAL_RESTORE_PROOF_NOT_FOUND" && observed.completed_processing !== "one" ? "restore-processing-state-mismatch"
          : message === "RELATIONAL_RESTORE_PROOF_NOT_FOUND" ? "restore-missing-proof-data"
            : code === "28P01" || code === "28000" ? "restore-database-authentication-failure"
              : code === "42501" ? "restore-database-authorization-failure"
                : ["ECONNREFUSED", "ECONNRESET", "ENETUNREACH", "ENOTFOUND", "ETIMEDOUT"].includes(code ?? "") ? "restore-database-connectivity-failure"
                  : ["CERT_HAS_EXPIRED", "ERR_TLS_CERT_ALTNAME_INVALID", "SELF_SIGNED_CERT_IN_CHAIN", "UNABLE_TO_VERIFY_LEAF_SIGNATURE"].includes(code ?? "") ? "restore-database-tls-failure"
                    : phase === "input-validation" ? "restore-input-validation-failure"
                      : "restore-database-query-failure";
  const details: RestoreVerificationFailureDetails = {
    failure_phase: phase,
    failure_category,
    expected: { migration_checksums: "two", accepted_work_item: "one", published_outbox: "one", completed_processing: "one" },
    observed,
  };
  const database_error_code = databaseErrorCode(code);
  return database_error_code === undefined ? details : { ...details, database_error_code };
}

function errorProperty(error: unknown, property: "code" | "message"): string | undefined {
  if (typeof error !== "object" || error === null) return undefined;
  const value = (error as Readonly<Record<string, unknown>>)[property];
  return typeof value === "string" ? value : undefined;
}

function databaseErrorCode(value: string | undefined): string | undefined {
  return value !== undefined && /^[0-9A-Z]{5}$/.test(value) ? value : undefined;
}

function countBucket(value: string | undefined): RestoreVerificationObserved {
  if (value === "0") return "zero";
  if (value === "1") return "one";
  if (value === "2") return "two";
  return "other";
}

function restoreHostFromEnvironment(): string {
  const candidate = process.env["RELATIONAL_RESTORE_HOST"];
  if (candidate === undefined || !/^kanbien-staging-platform-relational-restore-proof-[a-z0-9-]+\.[a-z0-9-]+\.eu-west-1\.rds\.amazonaws\.com$/.test(candidate)) {
    throw new Error("RELATIONAL_RESTORE_HOST_INVALID");
  }
  return candidate;
}

void main();
