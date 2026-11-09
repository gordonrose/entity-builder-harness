// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.migration-main
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Run the isolated explicitly selected migration operation as a one-shot task.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { runEntitySmokeMigration } from "./entity-smoke/migrations";
import { reportEntitySmokeFailure } from "./entity-smoke/diagnostics";
export { runEntitySmokeMigration } from "./entity-smoke/migrations";
if (typeof require !== "undefined" && require.main === module) void runEntitySmokeMigration().catch(cause => {
  reportEntitySmokeFailure("migration", "unknown", cause); process.exitCode = 1;
});

