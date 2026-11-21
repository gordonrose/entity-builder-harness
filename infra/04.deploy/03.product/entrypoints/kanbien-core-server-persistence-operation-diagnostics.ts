// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-operation-diagnostics
//   version: 2
//   status: draft
//   created_on: "2026-10-31"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Preserve the historical persistence operation-diagnostics import path through the canonical shared implementation.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts

export * from "./shared/persistence/operation-diagnostics";
