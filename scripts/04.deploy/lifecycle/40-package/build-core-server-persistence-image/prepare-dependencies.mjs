// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.core-server-persistence.prepare-dependencies
//   version: 1
//   status: draft
//   created_on: "2026-11-14"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Bind baseline PostgreSQL and observability dependency roots to the common installed-lock resolver.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { createDependencyPreparation } from "../prepare-runtime-dependencies/prepare.mjs";
import { readProgramBuildInputs } from "../../20-build/runnable-program-contract/build-inputs.mjs";

const preparation = createDependencyPreparation({
  roots: repository => Object.keys(readProgramBuildInputs(repository, { programId: "kanbien-core-server-persistence" }).externalOwners).sort(),
  schema: "deploy/core-server-persistence-dependencies/v1",
  code: "PERSISTENCE_DEPENDENCIES_NOT_PREPARED",
});
export const { dependencyClosure, prepareDependencies } = preparation;
preparation.run(import.meta.url);
