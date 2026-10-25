// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.code.core-server-persistence-runtime-contract
//   version: 1
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: script
//   purpose: Own the executable wrapper contract shared by persistence payload generation and validation.
//   portability: { class: internal, targets: [] }
//   effects: [read-only]
//   used_by:
//   - id: deploy.command.build-core-server-persistence-image.prepare-runtime
//     path: scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs
//   - id: deploy.command.build-core-server-persistence-image.verify-runtime
//     path: scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/verify-runtime.mjs

export const runtimeEntrypoints = {
  "kanbien-core-server-persistence.main": "runKanbienCoreServerPersistenceMain",
  "kanbien-core-server-persistence-verifier.main": "runKanbienCoreServerPersistenceVerifier",
  "kanbien-core-server-persistence-migration.main": "runKanbienCoreServerPersistenceMigration",
  "kanbien-core-server-persistence-restore-verifier.main": "runKanbienCoreServerPersistenceRestoreVerifier",
};
export function wrapperSource(entry, exported) {
  return `const { ${exported} } = require("./infra/04.deploy/03.product/entrypoints/${entry}.js");\nvoid ${exported}().catch(() => { process.exitCode = 1; });\n`;
}
