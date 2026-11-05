import { deepEqual, equal } from "node:assert/strict";
import {
  fixedTenantResolver,
  tenantContext,
  tenantId,
  coreTenancyBoundaryDiagnostic,
  coreTenancyBoundaryDiagnosticRecord,
  observeCoreTenancyDiagnostic,
  type TenantContext,
} from "../src/tenancy/index";
import { createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, type DiagnosticRecord } from "../src/diagnostics/index";

async function main(): Promise<void> {
  const id = tenantId("tenant-123");
  equal(id, "tenant-123");

  const context = tenantContext({ tenantId: id });
  deepEqual(context, {
    tenantId: "tenant-123",
    isolationKey: "tenant-123",
  });

  const customIsolationContext = tenantContext({
    tenantId: id,
    isolationKey: "tenant:tenant-123",
  });
  deepEqual(customIsolationContext, {
    tenantId: "tenant-123",
    isolationKey: "tenant:tenant-123",
  });

  const resolver = fixedTenantResolver<{ readonly host: string }>(context);
  const resolved = await resolver.resolve({ host: "tenant-123.example.test" });
  deepEqual(resolved, context);

  const missingResolver = fixedTenantResolver<{ readonly host: string }>(null);
  const missing = await missingResolver.resolve({ host: "unknown.example.test" });
  equal(missing, null);

  const acceptedContext: TenantContext = resolved ?? context;
  equal(acceptedContext.tenantId, id);
  const canary = "private-tenant-constructor-canary";
  const observed: DiagnosticRecord[] = [];
  const diagnostics = { onDiagnostic(record: DiagnosticRecord) { observed.push(record); } };
  for (const [property, field] of [["tenantId", "tenant-id"], ["isolationKey", "isolation-key"]] as const) {
    for (const failure of [canary, Object.freeze(new Error(canary)), 19, null]) {
      observed.length = 0;
      let caught = false, reads = 0;
      try { tenantContext(Object.defineProperty({ tenantId: id }, property, { get() { reads++; throw failure; } }), diagnostics); }
      catch (error) { caught = true; equal(error, failure); }
      equal(caught, true); equal(reads, 1);
      deepEqual(observed, [{ schema: "core/diagnostic-record/v1", code: "core.tenancy.boundary-failed", definitionVersion: 1,
        detail: { operation: "tenant-context", phase: "input-projection", field, reason: "threw", effect: "value-not-produced" } }]);
    }
  }
  const reads: string[] = [];
  let tenantReads = 0;
  observed.length = 0;
  const changed = tenantContext({ get tenantId() { reads.push("tenant"); return tenantId(++tenantReads === 1 ? "first" : "second"); }, get isolationKey() { reads.push("isolation"); return undefined; } } as unknown as Parameters<typeof tenantContext>[0], diagnostics);
  deepEqual(changed, { tenantId: "first", isolationKey: "second" });
  deepEqual(reads, ["tenant", "isolation", "tenant"]);
  equal(observed.length, 0);
  equal(tenantContext({ tenantId: id, isolationKey: "" }, diagnostics).isolationKey, "", "no new isolation policy");
  let fallbackReads = 0;
  observed.length = 0;
  try { tenantContext({ get tenantId() { if (++fallbackReads === 1) return id; throw canary; } }, diagnostics); }
  catch (error) { equal(error, canary); }
  equal(fallbackReads, 2);
  deepEqual(observed[0]?.detail, { operation: "tenant-context", phase: "input-projection", field: "tenant-id", reason: "threw", effect: "value-not-produced" });
  const sourceDefinition = defineDiagnostic({ code: "tenantfixture.source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
  } as const);
  const sources = Array.from({ length: 9 }, (_, ordinal) => { const result = createDiagnosticRecord(sourceDefinition, { ordinal }); if (!result.ok) throw new Error("Invalid source fixture"); return result.value; });
  const own = coreTenancyBoundaryDiagnosticRecord({ operation: "tenant-context", phase: "input-projection", field: "tenant-id", reason: "threw", effect: "value-not-produced" });
  observed.length = 0;
  deepEqual(observeCoreTenancyDiagnostic({ ...diagnostics, diagnosticDefinitions: [sourceDefinition] }, own, { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) }), { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) });
  deepEqual(observed, [own, ...sources]);
  equal(parseDiagnosticRecord(coreTenancyBoundaryDiagnostic, own).ok, true);
  equal(parseDiagnosticRecord(coreTenancyBoundaryDiagnostic, { ...own, detail: { ...own.detail, field: canary } }).ok, false);
  let accessorReads = 0;
  observed.length = 0;
  observeCoreTenancyDiagnostic(diagnostics, own, Object.defineProperty({}, "diagnosticRecord", { get() { accessorReads++; throw canary; } }));
  equal(accessorReads, 0); equal(observed.length, 2);
  deepEqual(observed[1], { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-inaccessible" } });
  for (const sink of [() => { throw canary; }, () => Promise.reject(canary), () => Object.assign(Promise.reject(canary), { then() { throw canary; } }), () => ({ then(_ok: unknown, reject: (reason: unknown) => void) { reject(canary); } })]) {
    let caught = false;
    try { tenantContext(Object.defineProperty({ tenantId: id }, "isolationKey", { get() { throw canary; } }), { onDiagnostic: sink }); }
    catch (error) { caught = true; equal(error, canary); }
    equal(caught, true);
  }
  await new Promise<void>((resolve) => setImmediate(resolve));
  equal(JSON.stringify(observed).includes(canary), false);
}

main()
  .then(() => {
    console.log("packages/core tenancy runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
