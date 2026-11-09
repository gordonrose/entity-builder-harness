import { deepEqual, equal } from "node:assert/strict";
import { parseDiagnosticRecord } from "@kanbien/core/diagnostics";
import { recordLifecyclePolicy, recordRetentionPolicyReference } from "@kanbien/core/persistence";
import { fixedClock, ok, systemUuidGenerator, uuid, type UUID, type UuidGenerator } from "@kanbien/core/shared";
import { validatePlatformDiagnosticCatalog } from "@kanbien/platform-contracts";
import {
  createTestEntitySchema, createTestEntityService, inMemoryTestEntityRepository,
  testEntityDiagnosticCatalog, updateTestEntitySchema, updateTestEntityService,
  type CreateTestEntityInput, type TestEntityServiceDependencies,
} from "../../../src/index";

async function main(): Promise<void> {
  const canary = "PRIVATE-SUBMITTED-CONTENT";
  const input: CreateTestEntityInput = {
    integerValue: 7, uuidValue: "b0b1c2d3-e4f5-4a67-8b90-123456789abc",
    occurredAt: "2026-11-01T10:00:00Z", label: "Example", status: "draft", enabled: true,
    categories: ["alpha"], notes: ["text"], description: null, reviewedAt: null, secondaryCategories: null,
  };
  const reference = recordRetentionPolicyReference("test-entity.retention");
  if (!reference.ok) throw new Error("Expected retention reference.");
  const policy = recordLifecyclePolicy({ recoveryWindowMs: 60_000, retentionPolicy: reference.value, legalHoldCheckRequired: true });
  if (!policy.ok) throw new Error("Expected lifecycle policy.");
  let generated = 0;
  let saves = 0;
  const repository = inMemoryTestEntityRepository();
  const deps: TestEntityServiceDependencies = {
    repository: { ...repository, create(entity) { saves++; return repository.create(entity); }, save(entity) { saves++; return repository.save(entity); } },
    clock: fixedClock(new Date("2026-11-06T12:00:00Z")), lifecyclePolicy: policy.value,
    uuidGenerator: { generate() { generated++; return ok("a0b1c2d3-e4f5-4a67-8b90-123456789abc" as UUID); } },
  };
  const catalog = validatePlatformDiagnosticCatalog(testEntityDiagnosticCatalog);
  equal(catalog.ok, true);
  const definition = testEntityDiagnosticCatalog.definitions[0];
  equal(definition.code, "entity-smoke.test-entity.validation-failed");
  const oldCatalog = validatePlatformDiagnosticCatalog({ ...testEntityDiagnosticCatalog,
    definitions: [{ ...definition, code: "test-entity.validation-failed" }],
  });
  equal(oldCatalog.ok, false);
  if (oldCatalog.ok) throw new Error("Expected old namespace rejection.");
  deepEqual(oldCatalog.error.diagnosticRecord?.detail, {
    registration: "diagnostic-catalog", field: "definitions", condition: "ownership-mismatch", phase: "definitions", effect: "rejected",
  });

  const cases: { input: unknown; field: string; reason: string }[] = [];
  for (const field of Object.keys(input)) {
    const missing: Record<string, unknown> = { ...input };
    delete missing[field];
    cases.push({ input: missing, field, reason: "missing" });
  }
  const invalidValues: [keyof CreateTestEntityInput, unknown, string][] = [
    ["integerValue", 1.5, "invalid-value"], ["uuidValue", canary, "invalid-format"],
    ["occurredAt", canary, "invalid-format"], ["label", " ", "invalid-value"],
    ["label", canary.repeat(20), "invalid-value"], ["status", canary, "invalid-value"],
    ["enabled", canary, "wrong-type"], ["categories", canary, "wrong-type"],
    ["categories", [canary], "invalid-item"], ["notes", canary, "wrong-type"],
    ["notes", [false], "invalid-item"], ["notes", [canary.repeat(30)], "invalid-item"],
    ["description", false, "wrong-type"], ["reviewedAt", canary, "invalid-format"],
    ["secondaryCategories", canary, "wrong-type"], ["secondaryCategories", [canary], "invalid-item"],
  ];
  for (const [field, value, reason] of invalidValues) cases.push({ input: { ...input, [field]: value }, field, reason });
  for (const value of [null, [], canary, 5]) cases.push({ input: value, field: "input", reason: "wrong-type" });
  for (const sample of cases) {
    const result = await createTestEntityService(sample.input as CreateTestEntityInput, deps);
    equal(result.ok, false);
    if (result.ok) throw new Error("Expected validation rejection.");
    equal(result.error.code, "TEST_ENTITY_VALIDATION_FAILED");
    deepEqual(result.error.diagnosticRecord, {
      schema: "core/diagnostic-record/v1", code: definition.code, definitionVersion: 1,
      detail: { field: sample.field, reason: sample.reason },
    });
    equal(JSON.stringify(result.error).includes(canary), false);
    equal(parseDiagnosticRecord(definition, result.error.diagnosticRecord).ok, true);
  }
  equal(generated, 0);
  equal(saves, 0);
  deepEqual(createTestEntitySchema.diagnose?.({ ...input, uuidValue: canary, enabled: canary })?.detail,
    { field: "uuidValue", reason: "invalid-format" });
  equal(createTestEntitySchema.explain({ ...input, uuidValue: canary, enabled: canary }).issues.length, 2);
  equal(createTestEntitySchema.diagnose?.(input), undefined);
  equal(updateTestEntitySchema.diagnose?.({}), undefined);

  const created = await createTestEntityService(input, deps);
  equal(created.ok, true);
  if (!created.ok) throw new Error("Expected creation.");
  for (const [field, value, reason] of invalidValues) {
    const result = await updateTestEntityService(created.value.id, { [field]: value }, deps);
    equal(result.ok, false);
    if (result.ok) throw new Error("Expected update rejection.");
    equal(result.error.diagnosticRecord?.code, definition.code);
    equal(result.error.diagnosticRecord?.definitionVersion, 1);
    deepEqual(result.error.diagnosticRecord?.detail, { field, reason });
    equal(JSON.stringify(result.error).includes(canary), false);
  }
  equal(saves, 1);
  equal(generated, 1);
  deepEqual(await repository.get(created.value.id), created.value);
  equal((await updateTestEntityService(created.value.id,
    { description: "text", reviewedAt: "2026-11-06T12:00:00Z", secondaryCategories: [] }, deps)).ok, true);
  equal((await updateTestEntityService(created.value.id,
    { description: null, reviewedAt: null, secondaryCategories: null }, deps)).ok, true);

  const source = uuid(canary);
  if (source.ok) throw new Error("Expected UUID failure.");
  const failed = await createTestEntityService(input, { ...deps, uuidGenerator: {
    generate() { generated++; return source; },
  } });
  equal(failed.ok, false);
  if (failed.ok) throw new Error("Expected generation failure.");
  equal(failed.error.code, "TEST_ENTITY_ID_GENERATION_FAILED");
  equal(failed.error.diagnosticRecord, source.error.diagnosticRecord);
  equal(failed.error.relatedDiagnosticRecords, undefined, "do not invent companions for a primary-only source");
  equal(generated, 2);
  equal(saves, 3);
  equal(JSON.stringify(failed.error).includes(canary), false);

  // Exercise the real Core producer through the public feature service. A
  // constructed companion would not prove the normal invalid-output path.
  for (const condition of ["invalid-output", "generation-threw", "crypto-unavailable"] as const) {
    let nativeCalls = 0;
    let generatorCalls = 0;
    let clockCalls = 0;
    let repositoryCalls = 0;
    let sourceResult: ReturnType<UuidGenerator["generate"]> | undefined;
    const unexpectedRepositoryCall = (): never => {
      repositoryCalls++;
      throw new Error("UUID failure must precede every repository call.");
    };
    const originalCrypto = Object.getOwnPropertyDescriptor(globalThis, "crypto");
    try {
      Object.defineProperty(globalThis, "crypto", { configurable: true, value:
        condition === "crypto-unavailable" ? undefined : { randomUUID() {
          nativeCalls++;
          if (condition === "generation-threw") throw new Error(canary);
          return canary;
        } },
      });
      const result = await createTestEntityService(input, { ...deps,
        clock: { now() { clockCalls++; throw new Error("UUID failure must precede time generation."); } },
        repository: { get: unexpectedRepositoryCall, create: unexpectedRepositoryCall,
          save: unexpectedRepositoryCall, listByStatus: unexpectedRepositoryCall },
        uuidGenerator: { generate() { generatorCalls++; sourceResult = systemUuidGenerator.generate(); return sourceResult; } },
      });
      equal(result.ok, false, condition);
      if (result.ok || sourceResult === undefined || sourceResult.ok) throw new Error("Expected actual Core generation failure.");
      equal(result.error.code, "TEST_ENTITY_ID_GENERATION_FAILED", condition);
      equal(result.error.defaultMessage, "A test entity ID could not be created.", condition);
      deepEqual(result.error.diagnosticRecord, {
        schema: "core/diagnostic-record/v1", code: "core.shared.uuid-generation-failed", definitionVersion: 1,
        detail: { reason: condition === "invalid-output" ? "generated-value-invalid" : "generation-threw" },
      }, condition);
      equal(result.error.diagnosticRecord, sourceResult.error.diagnosticRecord, "preserve the original primary");
      equal(result.error.relatedDiagnosticRecords, sourceResult.error.relatedDiagnosticRecords, "preserve the original companion array");
      deepEqual(result.error.relatedDiagnosticRecords, condition === "invalid-output" ? [{
        schema: "core/diagnostic-record/v1", code: "core.shared.uuid-invalid", definitionVersion: 1,
        detail: { reason: "invalid-format" },
      }] : undefined, "invocation failure is not evidence of invalid generated output");
      equal(generatorCalls, 1, "never replay UUID generation");
      equal(nativeCalls, condition === "crypto-unavailable" ? 0 : 1, condition);
      equal(clockCalls, 0, "failed identity prevents timestamp generation");
      equal(repositoryCalls, 0, "failed identity prevents reads and writes");
      equal(JSON.stringify(result.error).includes(canary), false, "never include the generated value or native cause");
    } finally {
      if (originalCrypto === undefined) equal(Reflect.deleteProperty(globalThis, "crypto"), true);
      else Object.defineProperty(globalThis, "crypto", originalCrypto);
      deepEqual(Object.getOwnPropertyDescriptor(globalThis, "crypto"), originalCrypto,
        "restore the exact original Crypto descriptor, including after assertion failure");
    }
  }

  equal(parseDiagnosticRecord(definition, { schema: "core/diagnostic-record/v1", code: definition.code,
    definitionVersion: 1, detail: { field: "uuidValue", reason: "invalid-format", value: canary } }).ok, false);
  equal(parseDiagnosticRecord(definition, { schema: "core/diagnostic-record/v1", code: definition.code,
    definitionVersion: 99, detail: { field: "uuidValue", reason: "invalid-format" } }).ok, false);
  console.log("apps/entity-smoke diagnostic caller tests passed.");
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
