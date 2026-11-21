// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-role-credential
//   version: 3
//   status: draft
//   created_on: "2026-10-25"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Preserve the historical persistence role-credential import path through the canonical shared implementation.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-runtime-credential
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.ts

export * from "./shared/persistence/role-credential";
