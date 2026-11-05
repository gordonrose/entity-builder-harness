import { deepEqual, equal } from "node:assert/strict";
import {
  fixedAuthenticator,
  principal,
  principalId,
  coreAuthnBoundaryDiagnostic,
  coreAuthnBoundaryDiagnosticRecord,
  observeCoreAuthnDiagnostic,
  type PrincipalClaims,
  type PrincipalClaimValue,
} from "../src/authn/index";
import { tenantId } from "../src/tenancy/index";
import { createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, type DiagnosticRecord } from "../src/diagnostics/index";

function sameThrow(action: () => unknown, expected: unknown): void {
  let caught = false;
  try { action(); } catch (error) { caught = true; equal(error, expected); }
  equal(caught, true);
}

async function main(): Promise<void> {
  const actorId = principalId("principal-123");
  const currentTenantId = tenantId("tenant-123");
  const claims = {
    email: "person@example.test",
    provider: "test-idp",
    profile: { locale: "en-GB" },
    roles: ["viewer"],
  } satisfies PrincipalClaims;
  const scopes = ["profile:read", "session:refresh"];

  const actor = principal({
    id: actorId,
    type: "user",
    subject: "oidc:test-idp:subject-123",
    currentTenantId,
    claims,
    scopes,
  });

  deepEqual(actor, {
    id: "principal-123",
    type: "user",
    subject: "oidc:test-idp:subject-123",
    currentTenantId: "tenant-123",
    claims: {
      email: "person@example.test",
      provider: "test-idp",
      profile: { locale: "en-GB" },
      roles: ["viewer"],
    },
    scopes: ["profile:read", "session:refresh"],
  });

  claims.email = "changed@example.test";
  claims.profile.locale = "fr-FR";
  claims.roles.push("admin");
  scopes.push("changed:scope");
  equal(actor.claims.email, "person@example.test");
  deepEqual(actor.claims.profile, { locale: "en-GB" });
  deepEqual(actor.claims.roles, ["viewer"]);
  deepEqual(actor.scopes, ["profile:read", "session:refresh"]);

  const service = principal({
    id: principalId("service-rag-builder"),
    type: "service",
    subject: "service:rag-builder",
  });
  deepEqual(service, {
    id: "service-rag-builder",
    type: "service",
    subject: "service:rag-builder",
    claims: {},
  });

  const authenticator = fixedAuthenticator<{ readonly token: string }>(actor);
  const authenticated = await authenticator.authenticate({ token: "opaque-token" });
  deepEqual(authenticated, actor);

  const unauthenticated = await fixedAuthenticator<{ readonly token: string }>(null).authenticate({
    token: "invalid-token",
  });
  equal(unauthenticated, null);

  const canary = "private-identity-constructor-canary";
  const observed: DiagnosticRecord[] = [];
  const diagnostics = { onDiagnostic(record: DiagnosticRecord) { observed.push(record); } };
  const base = { id: actorId, type: "user" as const, subject: canary };
  for (const [property, field] of [["id", "id"], ["type", "type"], ["subject", "subject"], ["currentTenantId", "current-tenant-id"], ["claims", "claims"], ["scopes", "scopes"]] as const) {
    for (const failure of [canary, Object.freeze(new Error(canary)), 17, null]) {
      observed.length = 0;
      let reads = 0;
      const hostile = Object.defineProperty({ ...base }, property, { get() { reads++; throw failure; } });
      sameThrow(() => principal(hostile, diagnostics), failure);
      equal(reads, 1);
      deepEqual(observed, [{ schema: "core/diagnostic-record/v1", code: "core.authn.boundary-failed", definitionVersion: 1,
        detail: { operation: "principal", phase: "input-projection", field, reason: "threw", effect: "value-not-produced" } }]);
    }
  }
  const order: string[] = [];
  const changing = {
    get id() { order.push("id"); return actorId; },
    get type() { order.push("type"); return "user" as const; },
    get subject() { order.push("subject"); return canary; },
    get currentTenantId() { order.push("tenant"); return currentTenantId; },
    get claims() { order.push("claims"); return {}; },
    get scopes() { order.push("scopes"); return scopes; },
  };
  observed.length = 0;
  principal(changing, diagnostics);
  deepEqual(order, ["id", "type", "subject", "tenant", "tenant", "claims", "scopes", "scopes"]);
  equal(observed.length, 0, "ordinary constructors remain quiet");
  const eager: string[] = [];
  let jsonFailure: unknown;
  try { principal({ ...base, claims: { get first() { eager.push("first"); return new Date() as never; }, get second() { eager.push("second"); return true; } } }, diagnostics); }
  catch (error) { jsonFailure = error; }
  equal(jsonFailure instanceof TypeError, true);
  deepEqual(eager, ["first", "second"], "Object.entries remains eager before JSON copying");
  equal(observed[0]?.code, "core.authn.boundary-failed");
  deepEqual(observed[0]?.detail, { operation: "principal", phase: "claims-copy", field: "claims", reason: "threw", effect: "value-not-produced" });
  equal(observed.length, 2, "shared JSON primary remains independent of the owning claims location");
  equal(observed[1]?.code, "core.shared.json-invalid");
  const iterationFailure = Object.freeze(new Error(canary));
  observed.length = 0;
  const enumerationOrder: string[] = [];
  sameThrow(() => principal({ ...base, claims: { get first() { enumerationOrder.push("first"); return new Date() as never; }, get second(): PrincipalClaimValue { enumerationOrder.push("second"); throw iterationFailure; } } }, diagnostics), iterationFailure);
  deepEqual(enumerationOrder, ["first", "second"]);
  deepEqual(observed[0]?.detail, { operation: "principal", phase: "claims-enumeration", field: "claims", reason: "threw", effect: "value-not-produced" });
  equal(observed.length, 1, "later eager entry failure precedes any JSON copying");
  let tenantReads = 0;
  observed.length = 0;
  sameThrow(() => principal({ ...base, get currentTenantId() { if (++tenantReads === 1) return currentTenantId; throw iterationFailure; } }, diagnostics), iterationFailure);
  equal(tenantReads, 2);
  deepEqual(observed[0]?.detail, { operation: "principal", phase: "input-projection", field: "current-tenant-id", reason: "threw", effect: "value-not-produced" });
  const iterable = { [Symbol.iterator]() { throw iterationFailure; } } as unknown as readonly string[];
  observed.length = 0;
  sameThrow(() => principal({ ...base, scopes: iterable }, diagnostics), iterationFailure);
  deepEqual(observed[0]?.detail, { operation: "principal", phase: "scopes-copy", field: "scopes", reason: "threw", effect: "value-not-produced" });
  const sourceDefinition = defineDiagnostic({ code: "identityfixture.source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
  } as const);
  const sources = Array.from({ length: 9 }, (_, ordinal) => { const result = createDiagnosticRecord(sourceDefinition, { ordinal }); if (!result.ok) throw new Error("Invalid source fixture"); return result.value; });
  const failure = Object.freeze({ diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) });
  observed.length = 0;
  sameThrow(() => principal(Object.defineProperty({ ...base }, "subject", { get() { throw failure; } }), { ...diagnostics, diagnosticDefinitions: [sourceDefinition] }), failure);
  deepEqual(observed.slice(1), sources);
  equal(observed.length, 10, "own observation never replaces source companion eight");
  let diagnosticReads = 0;
  const accessor = Object.defineProperty({}, "diagnosticRecord", { get() { diagnosticReads++; throw canary; } });
  observed.length = 0;
  sameThrow(() => principal(Object.defineProperty({ ...base }, "subject", { get() { throw accessor; } }), diagnostics), accessor);
  equal(diagnosticReads, 0); equal(observed.length, 2);
  deepEqual(observed[1], { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-inaccessible" } });
  for (const badSource of [{ diagnosticRecord: sources[0] }, { diagnosticRecord: { ...sources[0], detail: { ordinal: canary } } }]) {
    observed.length = 0;
    sameThrow(() => principal(Object.defineProperty({ ...base }, "subject", { get() { throw badSource; } }), diagnostics), badSource);
    equal(observed.length, 1, "unselected and malformed evidence is not delivered");
  }
  const own = coreAuthnBoundaryDiagnosticRecord({ operation: "principal", phase: "claims-enumeration", field: "claims", reason: "threw", effect: "value-not-produced" });
  equal(parseDiagnosticRecord(coreAuthnBoundaryDiagnostic, own).ok, true);
  equal(parseDiagnosticRecord(coreAuthnBoundaryDiagnostic, { ...own, detail: { ...own.detail, field: canary } }).ok, false);
  const returned = observeCoreAuthnDiagnostic({ ...diagnostics, diagnosticDefinitions: [sourceDefinition] }, own, failure);
  deepEqual(returned, { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) });
  for (const sink of [() => { throw canary; }, () => Promise.reject(canary), () => Object.assign(Promise.reject(canary), { then() { throw canary; } }), () => ({ then(_ok: unknown, reject: (reason: unknown) => void) { reject(canary); } })]) {
    sameThrow(() => principal(Object.defineProperty({ ...base }, "subject", { get() { throw iterationFailure; } }), { onDiagnostic: sink }), iterationFailure);
  }
  await new Promise<void>((resolve) => setImmediate(resolve));
  equal(JSON.stringify(observed).includes(canary), false);
}

main()
  .then(() => {
    console.log("packages/core authn runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
