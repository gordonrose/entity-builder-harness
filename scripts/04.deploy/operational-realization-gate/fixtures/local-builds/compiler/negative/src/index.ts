// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.fixture.local-typescript-negative-index
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture, sre]
//   kind: fixture
//   purpose: Produce a genuine TypeScript assignment diagnostic without executing code.
//   portability: {class: reusable, targets: [entity-builder]}
//   used_by:
//   - id: deploy.test.operational-realization-typescript-observer
//     path: scripts/04.deploy/operational-realization-gate/test_typescript_observer.py
export const answer: number = "deliberate-type-error";
