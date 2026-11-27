// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-scheduling-worker-handler
//   version: 1
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.scheduling
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Bind the core-platform proof worker handler to its own scope and database identity.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoints.runnable-program-index
//     path: infra/04.deploy/03.product/entrypoints/runnable-program-index.yml

import { createSchedulingTargetHandler } from "./shared/scheduling/invocation";
import { createKanbienCoreServerSchedulingApp } from "./kanbien-core-server-persistence-scheduling.app";
import { createKanbienCoreServerPostgreSqlPersistenceRuntime } from "./kanbien-core-server-persistence-postgresql";
import { kanbienCoreAcceptanceDiagnosticCatalog } from "./kanbien-core-server-persistence-diagnostics";

export const handler = createSchedulingTargetHandler({
  purpose: "worker", schema: "platform",
  dispatchUsername: "core_scheduling_dispatch", workerUsername: "core_scheduling_worker",
  appDiagnosticCatalogs: [kanbienCoreAcceptanceDiagnosticCatalog],
  createApp(resources) {
    return createKanbienCoreServerSchedulingApp({ ...resources,
      persistence: createKanbienCoreServerPostgreSqlPersistenceRuntime({ pool: resources.pool, schema: "platform",
        ...(resources.diagnosticDefinitions === undefined ? {} : { diagnosticDefinitions: resources.diagnosticDefinitions }) }) });
  },
});
