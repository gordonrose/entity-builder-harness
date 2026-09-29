// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.fixture.source-operations.task
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Supply an inert local module reference for source accounting.
//   portability: {class: reusable, targets: [entity-builder]}
//   effects: [read-only]
//   used_by:
//   - id: deploy.test.operation-contracts-cli
//     path: scripts/04.deploy/operational-realization-gate/test_operation_contracts_cli.py

import { value } from "./dependency.mjs";
export const result = value;
