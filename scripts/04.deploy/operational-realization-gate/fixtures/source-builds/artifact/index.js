// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.fixture.build-artifact
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture]
//   kind: script
//   purpose: Supply inert handwritten JavaScript bytes for local artifact accounting tests.
//   portability: {class: source-only, targets: [entity-builder]}
//   effects: [read-only]
//   used_by:
//   - id: deploy.test.build-contracts-cli
//     path: scripts/04.deploy/operational-realization-gate/test_build_contracts_cli.py
"use strict";
exports.value = 1;
