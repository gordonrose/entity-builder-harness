// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.fixture.source-operations.dependency
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Supply inert dependency bytes for source mutation tests.
//   portability: {class: reusable, targets: [entity-builder]}
//   effects: [read-only]
//   used_by:
//   - id: deploy.test.operation-contracts-cli
//     path: scripts/04.deploy/operational-realization-gate/test_operation_contracts_cli.py

export const value = "local-source-fixture";
