// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.administration-main
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Run only the selected isolated feature administration operation as a one-shot task.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { runEntitySmokeAdministration } from "./entity-smoke/administration";
import { reportEntitySmokeFailure } from "./entity-smoke/diagnostics";
export { runEntitySmokeAdministration } from "./entity-smoke/administration";
if (typeof require !== "undefined" && require.main === module) void runEntitySmokeAdministration().catch(cause => {
  reportEntitySmokeFailure("administration", "unknown", cause); process.exitCode = 1;
});

