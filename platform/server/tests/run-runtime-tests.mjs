// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.test.platform-server-workspace-runtime
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture, sre]
//   kind: script
//   purpose: Run emitted runtime tests with freshly reconciled workspace package exports.
//   portability: {class: reusable, targets: [entity-builder]}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.script.operational-realization-local-runtime
//     path: scripts/04.deploy/operational-realization-gate/local_runtime.py

import { prepareWorkspaceRuntime } from '../../../scripts/04.deploy/build-platform-shell-image/workspace-runtime.mjs';
import { spawnSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { join } from "node:path";

const runtimeRoot = '.cache/platform-server-runtime';
prepareWorkspaceRuntime('platform/server/tsconfig.runtime-test.json', runtimeRoot);

const testDirectory = join(runtimeRoot, 'platform/server/tests');
const testFiles = readdirSync(testDirectory).filter(name => name.endsWith('-runtime.test.js')).sort();
if (!testFiles.length) throw new Error('workspace-runtime-tests-empty');
for (const testFile of testFiles) {
  const result = spawnSync(process.execPath, [join(testDirectory, testFile)], {stdio: 'inherit'});
  if (result.status !== 0) { process.exitCode = result.status ?? 1; break; }
}
