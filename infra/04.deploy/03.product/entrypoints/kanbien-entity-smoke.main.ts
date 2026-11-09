// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.main
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Start only the isolated entity-smoke server; migrations are a separate task.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { runEntitySmokeMain } from "./entity-smoke/runtime";
import { reportEntitySmokeFailure } from "./entity-smoke/diagnostics";
export { runEntitySmokeMain } from "./entity-smoke/runtime";
if (typeof require !== "undefined" && require.main === module) void runEntitySmokeMain().catch(cause => {
  reportEntitySmokeFailure("startup", "unknown", cause); process.exitCode = 1;
});

