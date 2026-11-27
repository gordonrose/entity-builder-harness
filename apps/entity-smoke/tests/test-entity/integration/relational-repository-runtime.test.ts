import { deepEqual, equal, rejects } from "node:assert/strict";
import { entityId, fixedClock, isoDateTimeFromDate, ok, type UUID } from "@kanbien/core/shared";
import { recordLifecyclePolicy, recordRetentionPolicyReference } from "@kanbien/core/persistence";
import { createTestEntityService, deleteTestEntityService, getTestEntityService,
  relationalTestEntityRepository, restoreLogicallyDeletedTestEntityService,
  type TestEntityRelationalExecutor, type TestEntityError } from "../../../src/index";

async function main(): Promise<void> {
  const id = entityId<"TestEntity">("a0b1c2d3-e4f5-4a67-8b90-123456789abc");
  const moment = "2026-11-07T12:00:00.000Z";
  const canary = "synthetic-private-row-and-input-canary";
  const row = { id, integer_value: "9007199254740991", uuid_value: "b0b1c2d3-e4f5-4a67-8b90-123456789abc",
    occurred_at: new Date(moment), label: canary, status: "draft", enabled: false,
    categories: ["alpha", "gamma"], notes: [canary, ""], description: null,
    reviewed_at: null, secondary_categories: null, visibility: "active", lifecycle: { state: "active" },
    created_at: new Date(moment), updated_at: new Date(moment) };
  const statements: { text: string; values: readonly unknown[]; operation: "read" | "write" | "create" }[] = [];
  let rows: readonly Readonly<Record<string, unknown>>[] = [row];
  let rowCount: number | null = 1;
  let failure: TestEntityError | undefined;
  const executor: TestEntityRelationalExecutor = { async execute(statement, operation) {
    statements.push({ ...statement, operation });
    return failure === undefined ? ok({ rows, rowCount }) : { ok: false, error: failure };
  } };
  const repository = relationalTestEntityRepository(executor);
  const reference = recordRetentionPolicyReference("test-entity.retention");
  if (!reference.ok) throw new Error("Expected policy reference.");
  const policy = recordLifecyclePolicy({ recoveryWindowMs: 60_000, retentionPolicy: reference.value, legalHoldCheckRequired: true });
  if (!policy.ok) throw new Error("Expected lifecycle policy.");
  const deps = { repository, clock: fixedClock(new Date(moment)), uuidGenerator: { generate: () => ok(id as unknown as UUID) }, lifecyclePolicy: policy.value };
  const input = { integerValue: Number.MAX_SAFE_INTEGER, uuidValue: row.uuid_value, occurredAt: moment,
    label: canary, status: "draft" as const, enabled: false, categories: ["alpha", "gamma"] as const,
    notes: [canary, ""], description: null, reviewedAt: null, secondaryCategories: null };
  const created = await createTestEntityService(input, deps);
  equal(created.ok, true); if (!created.ok) throw new Error("Expected save.");
  deepEqual(created.value, { ...input, id, visibility: "active", lifecycle: { state: "active" }, createdAt: moment, updatedAt: moment });
  const write = statements[0]!;
  equal(write.operation, "create"); equal(write.text.includes(canary), false);
  equal(write.text.includes("ON CONFLICT"), false, "creation must not overwrite an existing ID");
  deepEqual(write.values, [id, Number.MAX_SAFE_INTEGER, row.uuid_value, moment, canary, "draft", false,
    '["alpha","gamma"]', JSON.stringify([canary, ""]), null, null, null, "active", '{"state":"active"}', moment, moment]);
  equal(write.text.includes("created_at = EXCLUDED.created_at"), false, "an edit must not rewrite creation time");
  deepEqual(await getTestEntityService(id, deps), created.value);
  rows = [{ ...row, description: "", reviewed_at: new Date(moment), secondary_categories: [] }];
  const nonNull = await repository.get(id);
  equal(nonNull?.description, ""); equal(nonNull?.reviewedAt, moment); deepEqual(nonNull?.secondaryCategories, []);
  if (nonNull === null) throw new Error("Expected row.");
  await repository.save(nonNull, nonNull);
  equal(statements.at(-1)!.text.startsWith("UPDATE __SCHEMA__.test_entity SET "), true, "saving must not recreate a missing row");
  equal(statements.at(-1)!.text.includes("created_at ="), false);
  equal(statements.at(-1)!.values[11], "[]", "empty categories are JSON, not SQL NULL");
  deepEqual(statements.at(-1)!.values.slice(0, 15), [id, Number.MAX_SAFE_INTEGER, row.uuid_value, moment, canary, "draft", false,
    '["alpha","gamma"]', JSON.stringify([canary, ""]), "", moment, "[]", "active", '{"state":"active"}', moment]);
  deepEqual(statements.at(-1)!.values.slice(15), [id, Number.MAX_SAFE_INTEGER, row.uuid_value, moment, canary, "draft", false,
    '["alpha","gamma"]', JSON.stringify([canary, ""]), "", moment, "[]", "active", '{"state":"active"}', moment, moment]);
  equal(statements.at(-1)!.text.includes("updated_at = $15 WHERE id = $1"), true, "parameters stay contiguous after omitting created_at");
  equal(statements.at(-1)!.text.includes("lifecycle IS NOT DISTINCT FROM $29 AND created_at IS NOT DISTINCT FROM $30 AND updated_at IS NOT DISTINCT FROM $31"), true);
  equal((statements.at(-1)!.text.match(/IS NOT DISTINCT FROM/g) ?? []).length, 16, "every stored field participates in stale-write protection");

  rows = [row]; await repository.listByStatus("draft");
  const listing = statements.at(-1)!;
  deepEqual(listing.values, ["draft"]);
  equal(listing.text.includes("status = $1 AND lifecycle->>'state' = 'active' ORDER BY created_at, id"), true);
  const deletedLifecycle = { state: "deleted", deletedAt: moment, restoreEligibleUntil: "2026-11-07T12:01:00.000Z", retentionPolicy: "test-entity.retention" };
  rows = [{ ...row, visibility: "archived", lifecycle: deletedLifecycle }];
  await relationalTestEntityRepository(executor, { lockForMutation: true }).get(id);
  equal(statements.at(-1)!.text.endsWith("WHERE id = $1 FOR UPDATE"), true, "deletion transaction reads lock the selected row");
  rowCount = 1; rows = [{ id }];
  const deletedAt = isoDateTimeFromDate(new Date(moment)), asOf = isoDateTimeFromDate(new Date("2026-11-07T12:05:00.001Z"));
  const purged = await repository.purgeArchivedDeleted({ id, deletedAt, asOf, retentionWindowMs: 300000 });
  equal(purged.ok, true); if (!purged.ok) throw new Error("Expected purge query success.");
  equal(purged.value, true);
  const purge = statements.at(-1)!;
  deepEqual(purge.values, [id, deletedAt, asOf, 300000]);
  equal(purge.text, "DELETE FROM __SCHEMA__.test_entity WHERE id = $1 AND visibility = 'archived' AND lifecycle->>'state' = 'deleted' AND lifecycle->>'deletedAt' = $2 AND (lifecycle->>'deletedAt')::timestamptz + ($4::double precision * interval '1 millisecond') < $3::timestamptz AND (lifecycle->>'restoreEligibleUntil')::timestamptz < $3::timestamptz RETURNING id");
  rowCount = 0; rows = [];
  deepEqual(await repository.purgeArchivedDeleted({ id, deletedAt, asOf, retentionWindowMs: 300000 }), ok(false));
  for (const [count, returned] of [[null, []], [1, []], [0, [{ id }]], [2, [{ id }, { id }]], [1, [{ id: canary }]]] as const) {
    rowCount = count; rows = returned;
    const result = await repository.purgeArchivedDeleted({ id, deletedAt, asOf, retentionWindowMs: 300000 });
    equal(result.ok, false); if (result.ok) throw new Error("Expected uncertain purge response rejection.");
    deepEqual(result.error.diagnosticRecord?.detail, { field: "row-count", reason: "invalid-shape", effect: "not-returned" });
    equal(JSON.stringify(result).includes(canary), false);
  }
  rows = []; rowCount = 1;
  equal(await repository.get(id), null); deepEqual(await repository.listByStatus("draft"), []);

  // The raw repository keeps deleted facts for restore; ordinary get does not.
  rows = [row]; const deleted = await deleteTestEntityService(id, deps);
  equal(deleted.ok, true);
  const deletion = JSON.parse(String(statements.at(-1)!.values[13]));
  rows = [{ ...row, lifecycle: deletion }];
  equal((await repository.get(id))?.lifecycle.state, "deleted");
  equal(await getTestEntityService(id, deps), null);
  const restored = await restoreLogicallyDeletedTestEntityService(id, deps);
  equal(restored.ok, true); equal(statements.at(-1)!.values[13], '{"state":"active"}');
  const beforeExpiry = statements.length;
  const expired = await restoreLogicallyDeletedTestEntityService(id, { ...deps, clock: fixedClock(new Date("2026-11-07T12:01:00.001Z")) });
  equal(expired.ok, false); equal(statements.length, beforeExpiry + 1, "expired restoration reads but never writes");

  for (const [field, malformed] of [
    ["id", { ...row, id: canary }], ["attributes", { ...row, integer_value: "9007199254740992" }],
    ["attributes", { ...row, categories: [canary] }], ["attributes", { ...row, enabled: "false" }],
    ["attributes", { ...row, secondary_categories: undefined }], ["timestamps", { ...row, updated_at: new Date(NaN) }],
    ["visibility", { ...row, visibility: canary }], ["lifecycle", { ...row, lifecycle: { state: "deleted" } }],
  ] as const) {
    rows = [malformed];
    await rejects(() => repository.get(id), (error: TestEntityError) => {
      equal(error.code, "TEST_ENTITY_STORED_RECORD_INVALID");
      deepEqual(error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "entity-smoke.test-entity.stored-record-invalid", definitionVersion: 1,
        detail: { field, reason: "invalid-shape", effect: "not-returned" } });
      equal(JSON.stringify(error).includes(canary), false); return true;
    });
    rows = [row, malformed];
    const beforeMalformedList = statements.length;
    await rejects(() => repository.listByStatus("draft"), (error: TestEntityError) => {
      deepEqual(error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "entity-smoke.test-entity.stored-record-invalid", definitionVersion: 1,
        detail: { field, reason: "invalid-shape", effect: "not-returned" } });
      equal(JSON.stringify(error).includes(canary), false); return true;
    });
    equal(statements.length, beforeMalformedList + 1, "malformed list rows neither return a partial list nor retry the query");
  }
  rows = [row, row];
  await rejects(() => repository.get(id), (error: TestEntityError) => error.code === "TEST_ENTITY_STORED_RECORD_INVALID");
  rows = []; rowCount = 0;
  const emptyWrite = await repository.save(created.value, created.value);
  equal(emptyWrite.ok, false); if (!emptyWrite.ok) deepEqual(emptyWrite.error.diagnosticRecord?.detail, { condition: "changed-or-missing", effect: "not-saved" });
  if (emptyWrite.ok) throw new Error("Expected empty write rejection.");
  for (const [count, returnedRows] of [[0, []], [null, [row]], [2, [row]], [1, [row, row]]] as const) {
    rowCount = count; rows = returnedRows;
    for (const operation of ["create", "save"] as const) {
      const beforeInvalidCount = statements.length;
      const result: Awaited<ReturnType<typeof repository.create>> = await repository[operation](created.value, created.value);
      equal(result.ok, false, "write count and returned rows must both prove one selected record");
      if (result.ok) throw new Error("Expected invalid write evidence rejection.");
      deepEqual(result.error.diagnosticRecord, operation === "save" && count === 0
        ? { schema: "core/diagnostic-record/v1", code: "entity-smoke.test-entity.write-conflict", definitionVersion: 1, detail: { condition: "changed-or-missing", effect: "not-saved" } }
        : { schema: "core/diagnostic-record/v1", code: "entity-smoke.test-entity.stored-record-invalid", definitionVersion: 1,
          detail: { field: "row-count", reason: "invalid-shape", effect: "not-returned" } });
      equal(statements.length, beforeInvalidCount + 1, "uncertain write evidence cannot authorize replay");
    }
  }
  const related = [emptyWrite.error.diagnosticRecord!];
  failure = { code: "SYNTHETIC_PROVIDER_FAILURE", defaultMessage: "The operation did not complete.", diagnosticRecord: emptyWrite.error.diagnosticRecord,
    relatedDiagnosticRecords: related };
  const beforeFailure = statements.length;
  const failed = await repository.save(created.value, created.value); equal(failed.ok, false);
  if (!failed.ok) {
    equal(failed.error, failure, "preserve the exact selected error envelope");
    equal(failed.error.relatedDiagnosticRecords, related, "preserve source companion-array identity");
  }
  equal(statements.length, beforeFailure + 1, "never retry a failed write");
  await rejects(() => repository.get(id), error => error === failure);
  await rejects(() => repository.listByStatus("draft"), error => error === failure);
  const failedCreate = await repository.create(created.value);
  equal(failedCreate.ok, false);
  if (!failedCreate.ok) equal(failedCreate.error, failure, "create retains the same complete source envelope");
  console.log("entity-smoke relational repository mapping and failure cases passed (injected executor only).");
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
