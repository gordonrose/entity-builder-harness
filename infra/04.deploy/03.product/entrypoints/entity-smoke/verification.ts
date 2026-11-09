// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.verification
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Verify the private feature through its public HTTP boundary without database credentials or mutation replay.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createHash } from "node:crypto";
import { isDeepStrictEqual } from "node:util";
import { systemClock, uuid, isoDateTime, type Clock } from "@kanbien/core/shared";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import { createTestEntitySchema, type CreateTestEntityInput } from "@kanbien/app-entity-smoke";
import { entitySmokeRecordDigest as recordDigest } from "./proof-facts";

export type EntitySmokeProofOperation = "create" | "read" | "observe-create" | "cleanup" | "lifecycle" | "ready" | "unready";
type Step = "configuration" | "release" | "liveness" | "readiness" | "create" | "read" | "update" | "list" | "archive" | "restore-archive" | "delete" | "restore-deleted" | "purge-eligibility";
type Condition = "invalid-input" | "request-failed" | "request-deadline-exceeded" | "status-mismatch" | "invalid-response" | "missing-record" | "multiple-records" | "facts-mismatch" | "digest-mismatch";
export const entitySmokeProofDiagnostic = defineDiagnostic({
  code: "entity-smoke-target.proof-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["create", "read", "observe-create", "cleanup", "lifecycle", "ready", "unready"] },
    step: { type: "enum", values: ["configuration", "release", "liveness", "readiness", "create", "read", "update", "list", "archive", "restore-archive", "delete", "restore-deleted", "purge-eligibility"] },
    condition: { type: "enum", values: ["invalid-input", "request-failed", "request-deadline-exceeded", "status-mismatch", "invalid-response", "missing-record", "multiple-records", "facts-mismatch", "digest-mismatch"] },
    effect: { type: "enum", values: ["not-started", "not-assessed", "unknown"] },
  } },
} as const);
export interface EntitySmokeProofOptions {
  readonly operation: EntitySmokeProofOperation;
  readonly baseUrl: string;
  readonly label: string;
  readonly expectedSource: string;
  readonly expectedDigest?: string;
  readonly localFixture?: boolean;
  readonly clock?: Clock;
  readonly sleep?: (milliseconds: number) => Promise<void>;
  readonly request?: typeof fetch;
}
const codes = { create: "ENTITY_SMOKE_RECORD_CREATED", read: "ENTITY_SMOKE_RECORD_RETRIEVED", "observe-create": "ENTITY_SMOKE_RECORD_RECONCILED", cleanup: "ENTITY_SMOKE_SYNTHETIC_RECORD_LOGICALLY_DELETED", lifecycle: "ENTITY_SMOKE_LIFECYCLE_PROVEN", ready: "ENTITY_SMOKE_HEALTHY", unready: "ENTITY_SMOKE_LIVE_NOT_READY" } as const;

/** A read phase never creates a missing record. Test-only dependencies control
 * time/transport; the environment entrypoint does not accept injected policies. */
export async function verifyEntitySmokeFeature(options: EntitySmokeProofOptions) {
  let step: Step = "configuration", mutationInvoked = false;
  const steps: Step[] = [], clock = options.clock ?? systemClock;
  const reject: (condition: Condition) => never = condition => {
    const checked = createDiagnosticRecord(entitySmokeProofDiagnostic, { operation: options.operation, step, condition,
      effect: mutationInvoked ? "unknown" : step === "configuration" ? "not-started" : "not-assessed" });
    throw { code: "ENTITY_SMOKE_PROOF_NOT_CONFIRMED", defaultMessage: "The private feature proof was not confirmed.",
      ...(checked.ok ? { diagnosticRecord: checked.value } : {}) };
  };
  if (!Object.hasOwn(codes, options.operation) || !/^entity-smoke-[a-f0-9]{24}$/.test(options.label) ||
      !(/^[a-f0-9]{40}$/.test(options.expectedSource) || options.localFixture === true && options.expectedSource === "local-uncommitted")) reject("invalid-input");
  const base = (() => { try { return new URL(options.baseUrl); } catch { return reject("invalid-input"); } })();
  const privateHost = base.hostname === "entity-smoke.kanbien-core-platform.internal";
  const fixtureHost = options.localFixture === true && ["entity-smoke", "127.0.0.1"].includes(base.hostname);
  if (base.protocol !== "http:" || (!privateHost && !fixtureHost) || base.username || base.password || base.pathname !== "/" || base.search || base.hash || privateHost && base.port !== "3000") reject("invalid-input");
  if (["read", "cleanup"].includes(options.operation) && !/^[a-f0-9]{64}$/.test(options.expectedDigest ?? "")) reject("invalid-input");
  const request = options.request ?? fetch;
  async function call(path: string, expected: number, command?: Record<string, unknown>): Promise<unknown> {
    let response: Response;
    const signal = AbortSignal.timeout(5000);
    try {
      if (command && ["create", "update", "archive", "restore-archive", "delete", "restore-deleted"].includes(String(command.action))) mutationInvoked = true;
      response = await request(new URL(path, base), { ...(command === undefined ? {} : {
        method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(command),
      }), redirect: "error", signal });
    } catch { return reject(signal.aborted ? "request-deadline-exceeded" : "request-failed"); }
    if (response.status !== expected) reject("status-mismatch");
    try { return await response.json(); } catch { return reject("invalid-response"); }
  }
  async function command(action: string, fields: Record<string, unknown> = {}, expected = 200) {
    return call("/entity-smoke/test-entity", expected, { action, ...fields });
  }
  const mark = () => { if (!steps.includes(step)) steps.push(step); };
  step = "release";
  const release = object(await call("/internal/release-verification", 200));
  if (object(release?.release)?.sourceCommitSha !== options.expectedSource) reject("facts-mismatch"); mark();
  step = "liveness"; await call("/livez", 200); mark();
  step = "readiness"; await call("/readyz", options.operation === "unready" ? 503 : 200); mark();
  if (options.operation === "ready" || options.operation === "unready") return result();
  const label = options.label + (options.operation === "lifecycle" ? "-lifecycle" : "");
  const input: CreateTestEntityInput = { integerValue: 7, uuidValue: "b0b1c2d3-e4f5-4a67-8b90-123456789abc",
    occurredAt: "2026-11-07T12:00:00.000Z", label, status: "draft", enabled: false, categories: ["alpha", "gamma"],
    notes: ["synthetic first note", ""], description: null, reviewedAt: null, secondaryCategories: null };
  step = "list";
  const existing = await listed("draft", label);
  if (["read", "observe-create", "cleanup"].includes(options.operation)) {
    if (existing.length === 0) reject("missing-record");
    if (existing.length !== 1) reject("multiple-records");
    step = "read";
    const record = recordFrom(await command("get", { id: existing[0]!.id }), input);
    const digest = recordDigest(record);
    // Reconciliation observes an already reserved label after the original
    // create task is terminal. It validates every original fact and returns
    // the observed ID-bound digest, never creates a replacement record. The
    // controller must retain this before permitting any later proof phase.
    if (options.operation !== "observe-create" && digest !== options.expectedDigest) reject("digest-mismatch");
    mark();
    if (options.operation === "cleanup") {
      // Retention/acceptance authority belongs to the controller. This task
      // can only logically delete the exact original, never issue SQL/purge.
      step = "delete";
      if (object(object(await command("delete", { id: record.id }))?.lifecycle)?.state !== "deleted") reject("facts-mismatch");
      await command("get", { id: record.id }, 404);
      if ((await listed("draft", label)).length !== 0) reject("facts-mismatch");
      mark();
    }
    return result(digest);
  }
  if (existing.length !== 0) reject("multiple-records");
  step = "create";
  const record = recordFrom(await command("create", { input }, 201), input);
  const id = record.id as string, digest = recordDigest(record); mark();
  step = "read";
  if (!isDeepStrictEqual(recordFrom(await command("get", { id }), input), record)) reject("facts-mismatch");
  mark();
  if (options.operation === "create") return result(digest);

  step = "update";
  const changes = { integerValue: -42, status: "active", enabled: true, categories: ["beta"], notes: ["edited"],
    description: "", reviewedAt: "2026-11-08T00:00:00.000Z", secondaryCategories: [] };
  const updated = object(await command("update", { id, input: changes }));
  if (!updated || !Object.entries(changes).every(([key, value]) => isDeepStrictEqual(updated[key], value)) || updated.createdAt !== record.createdAt) reject("facts-mismatch");
  mark();
  step = "list";
  if ((await listed("draft", label)).length !== 0 || (await listed("active", label)).length !== 1) reject("facts-mismatch"); mark();
  step = "archive";
  if (object(await command("archive", { id }))?.visibility !== "archived") reject("facts-mismatch"); mark();
  step = "restore-archive";
  if (object(await command("restore-archive", { id }))?.visibility !== "active") reject("facts-mismatch"); mark();
  step = "delete";
  const firstDelete = object(await command("delete", { id }));
  if (object(firstDelete?.lifecycle)?.state !== "deleted") reject("facts-mismatch");
  await command("get", { id }, 404);
  await command("restore-archive", { id }, 404);
  await command("update", { id, input: { description: "must not change" } }, 404);
  if ((await listed("active", label)).length !== 0) reject("facts-mismatch"); mark();
  step = "purge-eligibility";
  if (object(await command("assess-purge", { id, retentionSatisfied: true, legalHold: false }))?.eligibility !== "within-recovery-window") reject("facts-mismatch");
  step = "restore-deleted";
  if (object(object(await command("restore-deleted", { id }))?.lifecycle)?.state !== "active") reject("facts-mismatch"); mark();
  step = "delete";
  const deleted = object(object(await command("delete", { id }))?.lifecycle);
  if (!deleted || deleted.state !== "deleted" || typeof deleted.restoreEligibleUntil !== "string") return reject("invalid-response");
  if (typeof deleted.deletedAt !== "string") reject("invalid-response");
  const window = Date.parse(deleted.restoreEligibleUntil as string) - Date.parse(deleted.deletedAt as string);
  if (window !== 60_000) reject("invalid-response");
  // Wait after receiving the committed deletion, rather than compare two
  // hosts' wall clocks. Production has no clock/policy override.
  await (options.sleep ?? (milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))))(window + 50);
  step = "restore-deleted";
  const expired = object(await command("restore-deleted", { id }, 400));
  if (object(expired?.error)?.code !== "PERSISTENCE_RESTORE_WINDOW_EXPIRED") reject("facts-mismatch");
  step = "purge-eligibility";
  for (const [retentionSatisfied, legalHold, expected] of [[false, false, "retention-not-met"], [true, true, "legal-hold"], [true, false, "eligible"]] as const) {
    if (object(await command("assess-purge", { id, retentionSatisfied, legalHold }))?.eligibility !== expected) reject("facts-mismatch");
  }
  await command("purge", { id }, 400); mark();
  return result(digest);

  async function listed(status: string, selectedLabel: string) {
    const values = await command("list", { status });
    if (!Array.isArray(values)) return reject("invalid-response");
    return values.flatMap(value => { const item = object(value); return item?.label === selectedLabel ? [item] : []; });
  }
  function recordFrom(value: unknown, expected: CreateTestEntityInput): Record<string, unknown> {
    const item = object(value);
    if (!item || !createTestEntitySchema.validate(item) || typeof item.id !== "string" || !uuid(item.id).ok ||
        typeof item.createdAt !== "string" || !isoDateTime(item.createdAt).ok || typeof item.updatedAt !== "string" || !isoDateTime(item.updatedAt).ok ||
        item.visibility !== "active" || !isDeepStrictEqual(item.lifecycle, { state: "active" }) ||
        !Object.entries(expected).every(([key, content]) => isDeepStrictEqual(item[key], content))) return reject("facts-mismatch");
    return item;
  }
  function result(digest?: string) {
    return { schema: "deploy/entity-smoke-task-proof/v1", verdict: "passed", operation: options.operation, code: codes[options.operation],
      source_revision: options.expectedSource, proof_label_sha256: createHash("sha256").update(options.label).digest("hex"),
      ...(digest === undefined ? {} : { record_digest: digest }), steps, checked_at: clock.now().toISOString() };
  }
}
function object(value: unknown): Record<string, unknown> | undefined { return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : undefined; }

