// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-entity-smoke-scheduling-dispatch-handler
//   version: 1
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.scheduling
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Bind the Entity Smoke dispatch handler to its own scope and database identity.
//   portability: { class: internal, targets: [entity-smoke] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoints.runnable-program-index
//     path: infra/04.deploy/03.product/entrypoints/runnable-program-index.yml

import { createSchedulingTargetHandler } from "./shared/scheduling/invocation";
import { testEntityDiagnosticCatalog } from "@kanbien/app-entity-smoke";
import { createEntitySmokeSchedulingApp } from "./entity-smoke/runtime";

export const handler = createSchedulingTargetHandler({
  purpose: "dispatch", schema: "entity_smoke",
  dispatchUsername: "entity_smoke_scheduling_dispatch", workerUsername: "entity_smoke_scheduling_worker",
  appDiagnosticCatalogs: [testEntityDiagnosticCatalog],
  createApp: createEntitySmokeSchedulingApp,
});
