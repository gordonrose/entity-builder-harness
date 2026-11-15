// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-configuration
//   version: 7
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Preserve the historical persistence configuration import path through the canonical shared implementation.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-migration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-restore-verifier
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts

export * from "./shared/persistence/configuration";
