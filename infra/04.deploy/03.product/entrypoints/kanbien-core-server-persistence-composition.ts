// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-composition
//   version: 2
//   status: draft
//   created_on: "2026-11-02"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Select and connect the supported persistence implementation without changing operation semantics.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts

import { createNodePostgreSqlTokenConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { postgresqlConfigurationImplementation, selectPersistenceConfigurationImplementation } from "./shared/persistence/configuration-implementation";
export { persistenceImplementationDiagnostic } from "./shared/persistence/configuration-implementation";
import type { KanbienCorePersistenceRuntime } from "./kanbien-core-server-persistence.app";
import { createKanbienCoreServerPostgreSqlPersistenceRuntime } from "./kanbien-core-server-persistence-postgresql";

const postgresql = Object.freeze({
  ...postgresqlConfigurationImplementation,
  createPool: createNodePostgreSqlTokenConnectionPool,
  createRuntime: (options: Parameters<typeof createKanbienCoreServerPostgreSqlPersistenceRuntime>[0]): KanbienCorePersistenceRuntime =>
    createKanbienCoreServerPostgreSqlPersistenceRuntime(options),
});
export type KanbienCorePersistenceImplementation = typeof postgresql;

export function selectPersistenceImplementation(value: unknown) {
  const selected = selectPersistenceConfigurationImplementation(value);
  return selected.ok ? { ok: true as const, value: postgresql } : selected;
}
