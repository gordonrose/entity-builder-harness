// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: core.config.source-read-observation-contracts
//   version: 2
//   status: active
//   created_on: "2026-10-27"
//   updated_on: "2026-11-02"
//   layer: 03.product
//   domain: configuration
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Define provider-neutral configuration source-read observations without retaining source values or native errors.
//   portability: { class: reusable, targets: [entity-builder] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-configuration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts
/** A source-access observation does not identify the underlying cause. */
export const configSourceReadFailureReasons = Object.freeze([
  "not-found", "read-denied", "not-a-directory", "is-a-directory", "unclassified-read-failure",
] as const);
export type ConfigSourceReadFailureReason = (typeof configSourceReadFailureReasons)[number];
