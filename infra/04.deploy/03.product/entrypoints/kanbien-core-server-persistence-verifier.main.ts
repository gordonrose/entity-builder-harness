// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-verifier
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-31"
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
import { PersistenceTaskObservations, VerificationObservation, type PersistenceTaskDiagnosticOptions } from "./kanbien-core-server-persistence-operation-diagnostics";

export async function runKanbienCoreServerPersistenceVerifier(env: NodeJS.ProcessEnv = process.env, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observations = new PersistenceTaskObservations("verification", diagnostics);
  const observation = new VerificationObservation("verification", observations.options);
  return observation.run(async () => {
  const mode = observation.at("input-projection", "mode", () => env["PERSISTENCE_VERIFIER_MODE"]);
  const baseUrl = observation.at("input-projection", "base-url", () => env["KANBIEN_PRIVATE_PERSISTENCE_URL"]);
  const recordId = observation.at("input-projection", "record-id", () => env["PERSISTENCE_ACCEPTANCE_RECORD_ID"]);
  const fact = observation.at("input-projection", "fact", () => env["PERSISTENCE_ACCEPTANCE_FACT"]);
  observation.location("predicate", "mode");
  if (!isMode(mode, observation) || !isPrivateBaseUrl(baseUrl, observation)) return rejected("VERIFIER_CONFIGURATION_INVALID", observations, observation);
  if (mode === "health-ready" || mode === "health-unready") { observation.location("health-settlement"); return verifyHealth(baseUrl, mode, observations); }
  if (!isRecordId(recordId, observation)) return rejected("VERIFIER_CONFIGURATION_INVALID", observations, observation);
  observation.location("predicate", "fact");
  let factCondition: "wrong-type" | "empty" | "too-long" = "wrong-type";
  if (typeof fact !== "string" || (factCondition = "empty", fact.length < 1) || (factCondition = "too-long", fact.length > 256)) {
    observation.rejected("fact", factCondition); return rejected("VERIFIER_CONFIGURATION_INVALID", observations, observation);
  }
  observation.location("fact-digest", "fact");
  const factDigest = createHash("sha256").update(fact).digest("hex");
  try {
    const create = mode === "create";
    const response = await observation.invoke("fetch", () => fetch(observation.at("request-projection", "record-id", () => `${baseUrl}/internal/persistence-acceptance${create ? "" : `?record_id=${encodeURIComponent(recordId)}`}`), observation.invocationArgument("fetch", {
      method: create ? "POST" : mode === "cleanup" ? "DELETE" : "GET",
      signal: observation.at("request-timeout", undefined, () => AbortSignal.timeout(30_000)),
      ...(create ? { headers: { "content-type": "application/json" }, body: observation.at("request-projection", "body", () => JSON.stringify({ record_id: recordId, fact_digest: factDigest })) } : {}),
    })));
    observation.location("response-json", "body");
    const body: unknown = await response.json().catch((cause: unknown) => { observation.failed(cause, "rejected"); return undefined; });
    observation.location("response-predicate");
    if (mode === "create" && observation.matches("status", "status-mismatch", () => response.status === 201 || response.status === 200) && hasOutcome(body, ["created", "already-exists"], observation)) return accepted("KANBIEN_CORE_PERSISTENCE_RECORD_ACCEPTED", observations, observation);
    if (mode === "read" && observation.matches("status", "status-mismatch", () => response.status === 200) && hasRecord(body, recordId, factDigest, observation)) return accepted("KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", observations, observation);
    if (mode === "cleanup" && observation.matches("status", "status-mismatch", () => response.status === 200) && hasOutcome(body, ["deleted"], observation)) return accepted("KANBIEN_CORE_PERSISTENCE_RECORD_CLEANED_UP", observations, observation);
    observation.rejected();
    return rejected("KANBIEN_CORE_PERSISTENCE_VERIFICATION_REJECTED", observations, observation);
  } catch (cause) {
    observation.failed(cause);
    return rejected("KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE", observations, observation);
  }
  }).catch((cause: unknown) => { observations.publishUncaught(); throw cause; });
}

/**
 * The verifier remains credential-free and server-mediated.  These probes
 * deliberately observe only HTTP status: liveness must remain true through a
 * dependency outage, while readiness tracks the PostgreSQL dependency.
 */
async function verifyHealth(baseUrl: string, mode: "health-ready" | "health-unready", observations: PersistenceTaskObservations): Promise<void> {
  const observation = new VerificationObservation("health", observations.options);
  const liveObservation = new VerificationObservation("health", observations.options);
  const readyObservation = new VerificationObservation("health", observations.options);
  try {
    const [live, ready] = await observation.invoke("health-settlement", () => Promise.all([
      liveObservation.invoke("live-fetch", () => fetch(`${baseUrl}/livez`, liveObservation.invocationArgument("live-fetch", { signal: liveObservation.at("live-timeout", undefined, () => AbortSignal.timeout(30_000)) }))),
      readyObservation.invoke("ready-fetch", () => fetch(`${baseUrl}/readyz`, readyObservation.invocationArgument("ready-fetch", { signal: readyObservation.at("ready-timeout", undefined, () => AbortSignal.timeout(30_000)) }))),
    ]));
    if (mode === "health-ready" && observation.matches("live-status", "status-mismatch", () => live.status === 200) && observation.matches("ready-status", "status-mismatch", () => ready.status === 200)) return accepted("KANBIEN_CORE_PERSISTENCE_HEALTHY", observations, observation);
    if (mode === "health-unready" && observation.matches("live-status", "status-mismatch", () => live.status === 200) && observation.matches("ready-ok", "unexpected-ok", () => !ready.ok)) return accepted("KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", observations, observation);
    observation.rejected();
    return rejected("KANBIEN_CORE_PERSISTENCE_HEALTH_VERIFICATION_REJECTED", observations, observation);
  } catch (cause) {
    observation.failed(cause);
    return rejected("KANBIEN_CORE_PERSISTENCE_HEALTH_VERIFICATION_UNAVAILABLE", observations, observation);
  }
}

function accepted(code: string, observations: PersistenceTaskObservations, observation: VerificationObservation): void { observation.location("result-projection"); console.log((observations.markSerializationReached(), JSON.stringify({ verdict: "accepted", code }))); observations.markPublished(); }
function rejected(code: string, observations: PersistenceTaskObservations, observation: VerificationObservation): void { observation.location("result-projection"); console.error((observations.markSerializationReached(), JSON.stringify(observations.failure(code)))); observations.markPublished(); process.exitCode = 1; }
function isMode(value: unknown, observation: VerificationObservation): value is "create" | "read" | "cleanup" | "health-ready" | "health-unready" { observation.location("predicate", "mode"); const valid = value === "create" || value === "read" || value === "cleanup" || value === "health-ready" || value === "health-unready"; if (!valid) observation.rejected("mode", value === undefined ? "missing" : typeof value !== "string" ? "wrong-type" : "unsupported"); return valid; }
function isPrivateBaseUrl(value: unknown, observation: VerificationObservation): value is string { observation.location("predicate", "base-url"); const valid = typeof value === "string" && /^http:\/\/[a-z0-9-]+\.kanbien-core-platform\.internal:3000$/.test(value); if (!valid) observation.rejected("base-url", value === undefined ? "missing" : typeof value !== "string" ? "wrong-type" : "pattern"); return valid; }
function isRecordId(value: unknown, observation: VerificationObservation): value is string { observation.location("predicate", "record-id"); const valid = typeof value === "string" && /^core-persistence-[a-z0-9-]{8,80}$/.test(value); if (!valid) observation.rejected("record-id", value === undefined ? "missing" : typeof value !== "string" ? "wrong-type" : "pattern"); return valid; }
function hasOutcome(value: unknown, outcomes: readonly string[], observation: VerificationObservation): boolean { return observation.matches("body", "wrong-type", () => typeof value === "object") && observation.matches("body", "wrong-type", () => value !== null) && observation.matches("outcome", "missing", () => "outcome" in (value as object)) && observation.matches("outcome", "wrong-outcome", () => outcomes.includes((value as { outcome?: unknown }).outcome as string)); }
function hasRecord(value: unknown, id: string, digest: string, observation: VerificationObservation): boolean {
  if (!hasOutcome(value, ["found"], observation) || typeof value !== "object" || value === null || !observation.matches("record", "missing-record", () => "record" in value)) return false;
  const record = observation.at("response-predicate", "record", () => (value as { record?: unknown }).record);
  return observation.matches("record", "wrong-type", () => typeof record === "object") && observation.matches("record", "wrong-type", () => record !== null) && observation.matches("record-id-result", "id-mismatch", () => (record as { id?: unknown }).id === id) && observation.matches("fact-digest-result", "digest-mismatch", () => (record as { factDigest?: unknown }).factDigest === digest);
}
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceVerifier();
