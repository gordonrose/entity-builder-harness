// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.verifier-main
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Run one explicitly selected private feature proof phase without database credentials.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { verifyEntitySmokeFeature, type EntitySmokeProofOperation } from "./entity-smoke/verification";
import { entitySmokeConfigurationError, reportEntitySmokeFailure } from "./entity-smoke/diagnostics";

export async function runEntitySmokeVerifier(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const operation = env["ENTITY_SMOKE_VERIFICATION_OPERATION"];
  if (!operation || !["create", "read", "observe-create", "cleanup", "lifecycle", "ready", "unready"].includes(operation)) {
    reportEntitySmokeFailure("verification", "not-started", entitySmokeConfigurationError("operation", "invalid")); process.exitCode = 1; return;
  }
  // This workload has no credential/secret/SQL configuration delivery.
  if (Object.keys(env).some(key => key.startsWith("PERSISTENCE_") || key === "ENTITY_SMOKE_LOCAL_QUALIFICATION_TOKEN")) {
    reportEntitySmokeFailure("verification", "not-started", entitySmokeConfigurationError("identity", "mismatch")); process.exitCode = 1; return;
  }
  try {
    const result = await verifyEntitySmokeFeature({ operation: operation as EntitySmokeProofOperation,
      baseUrl: env["ENTITY_SMOKE_VERIFICATION_URL"] ?? "", label: env["ENTITY_SMOKE_PROOF_LABEL"] ?? "",
      expectedSource: env["ENTITY_SMOKE_EXPECTED_SOURCE"] ?? "",
      ...(env["ENTITY_SMOKE_EXPECTED_DIGEST"] === undefined ? {} : { expectedDigest: env["ENTITY_SMOKE_EXPECTED_DIGEST"] }),
      localFixture: env["NODE_ENV"] === "test" });
    console.log(JSON.stringify(result));
  } catch (cause) { reportEntitySmokeFailure("verification", ["create", "cleanup", "lifecycle"].includes(operation) ? "unknown" : "not-assessed", cause); process.exitCode = 1; }
}
if (typeof require !== "undefined" && require.main === module) void runEntitySmokeVerifier().catch(cause => {
  reportEntitySmokeFailure("verification", "unknown", cause); process.exitCode = 1;
});

