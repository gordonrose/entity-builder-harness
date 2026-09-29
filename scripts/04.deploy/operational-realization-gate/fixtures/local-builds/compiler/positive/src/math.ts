// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.fixture.local-typescript-positive-math
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture, sre]
//   kind: fixture
//   purpose: Provide an inert local dependency for genuine compiler resolution tests.
//   portability: {class: reusable, targets: [entity-builder]}
//   used_by:
//   - id: deploy.test.operational-realization-typescript-observer
//     path: scripts/04.deploy/operational-realization-gate/test_typescript_observer.py
export function twice(value: number): number { return value * 2; }
