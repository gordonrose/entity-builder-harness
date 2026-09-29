// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.fixture.local-typescript-positive-index
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture, sre]
//   kind: fixture
//   purpose: Provide an inert typed import for genuine compiler emission tests.
//   portability: {class: reusable, targets: [entity-builder]}
//   used_by:
//   - id: deploy.test.operational-realization-typescript-observer
//     path: scripts/04.deploy/operational-realization-gate/test_typescript_observer.py
import { twice } from "./math";
export const answer: number = twice(21);
