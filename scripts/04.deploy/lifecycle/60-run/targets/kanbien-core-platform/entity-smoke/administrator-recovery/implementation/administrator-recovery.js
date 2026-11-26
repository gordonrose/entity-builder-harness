// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.library.entity-smoke.administrator-recovery
//   version: 2
//   status: draft
//   created_on: "2026-11-11"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Reject the retired administrator recovery incident program without credentials, provider or database access.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   effects: [read-only]
//   used_by:
//   - id: aws.standard.operational-realization-applicability
//     path: .agentic/aws/standards/operational-realization-applicability.md
"use strict";
// Original incident results remain historical evidence; do not rerun its SQL.
console.log(JSON.stringify({
  schema: "deploy/entity-smoke-administrator-recovery/v1",
  verdict: "blocked",
  condition: "administrator-recovery-retired",
  effect: "not-started"
}));
process.exitCode = 1;
