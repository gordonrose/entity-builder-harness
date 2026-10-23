// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-verifier
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-23"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Run a private server-mediated persistence verification without a database credential or direct database route.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { createHash } from "node:crypto";

export async function runKanbienCoreServerPersistenceVerifier(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const mode = env["PERSISTENCE_VERIFIER_MODE"];
  const baseUrl = env["KANBIEN_PRIVATE_PERSISTENCE_URL"];
  const recordId = env["PERSISTENCE_ACCEPTANCE_RECORD_ID"];
  const fact = env["PERSISTENCE_ACCEPTANCE_FACT"];
  if (!isMode(mode) || !isPrivateBaseUrl(baseUrl) || !isRecordId(recordId) || typeof fact !== "string" || fact.length < 1 || fact.length > 256) return rejected("VERIFIER_CONFIGURATION_INVALID");
  const factDigest = createHash("sha256").update(fact).digest("hex");
  try {
    const create = mode === "create";
    const response = await fetch(`${baseUrl}/internal/persistence-acceptance${create ? "" : `?record_id=${encodeURIComponent(recordId)}`}`, {
      method: create ? "POST" : mode === "cleanup" ? "DELETE" : "GET",
      signal: AbortSignal.timeout(30_000),
      ...(create ? { headers: { "content-type": "application/json" }, body: JSON.stringify({ record_id: recordId, fact_digest: factDigest }) } : {}),
    });
    const body: unknown = await response.json().catch(() => undefined);
    if (mode === "create" && (response.status === 201 || response.status === 200) && hasOutcome(body, ["created", "already-exists"])) return accepted("KANBIEN_CORE_PERSISTENCE_RECORD_ACCEPTED");
    if (mode === "read" && response.status === 200 && hasRecord(body, recordId, factDigest)) return accepted("KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED");
    if (mode === "cleanup" && response.status === 200 && hasOutcome(body, ["deleted"])) return accepted("KANBIEN_CORE_PERSISTENCE_RECORD_CLEANED_UP");
    return rejected("KANBIEN_CORE_PERSISTENCE_VERIFICATION_REJECTED");
  } catch {
    return rejected("KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE");
  }
}

function accepted(code: string): void { console.log(JSON.stringify({ verdict: "accepted", code })); }
function rejected(code: string): void { console.error(JSON.stringify({ verdict: "rejected", code })); process.exitCode = 1; }
function isMode(value: unknown): value is "create" | "read" | "cleanup" { return value === "create" || value === "read" || value === "cleanup"; }
function isPrivateBaseUrl(value: unknown): value is string { return typeof value === "string" && /^http:\/\/[a-z0-9-]+\.kanbien-core-platform\.internal:3000$/.test(value); }
function isRecordId(value: unknown): value is string { return typeof value === "string" && /^core-persistence-[a-z0-9-]{8,80}$/.test(value); }
function hasOutcome(value: unknown, outcomes: readonly string[]): boolean { return typeof value === "object" && value !== null && "outcome" in value && outcomes.includes((value as { outcome?: unknown }).outcome as string); }
function hasRecord(value: unknown, id: string, digest: string): boolean {
  if (!hasOutcome(value, ["found"]) || typeof value !== "object" || value === null || !("record" in value)) return false;
  const record = (value as { record?: unknown }).record;
  return typeof record === "object" && record !== null && (record as { id?: unknown }).id === id && (record as { factDigest?: unknown }).factDigest === digest;
}
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceVerifier();
