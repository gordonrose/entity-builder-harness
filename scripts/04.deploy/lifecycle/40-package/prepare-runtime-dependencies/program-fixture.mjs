// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.runtime-dependency-program-fixture
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: testing
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Copy actual program declarations into disposable installed-dependency fixtures without inventing workload bindings.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: deploy.test.runtime-dependency-preparation
//     path: scripts/04.deploy/lifecycle/40-package/prepare-runtime-dependencies/prepare-test.mjs

import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { readProgramBuildInputs } from "../../20-build/runnable-program-contract/build-inputs.mjs";

const source = fileURLToPath(new URL("../../../../../", import.meta.url));
export function copyProgramFixture(repository, programId) {
  const selected = readProgramBuildInputs(source, { programId });
  const files = new Set([...selected.manifestPaths.filter(path => path !== "package-lock.json"),
    ...selected.inputs.sourceFiles, ...Object.values(selected.inputs.packages).flatMap(exports =>
      Object.values(exports).filter(path => path.endsWith(".json")))]);
  for (const relative of files) {
    const target = join(repository, relative);
    mkdirSync(dirname(target), { recursive: true });
    copyFileSync(join(source, relative), target);
  }
}
