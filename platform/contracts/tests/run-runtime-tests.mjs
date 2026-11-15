import { accessSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { loadWorkspaceGraph, selectWorkspaceProject } from "../../../scripts/repo/workspace-build/declarations.mjs";
import { prepareWorkspaceRuntime } from "../../../scripts/repo/workspace-build/runtime-packages.mjs";

const runtimeRoot = ".cache/platform-contracts-runtime";
const testDirectory = ".cache/platform-contracts-runtime/platform/contracts/tests";
const repository = process.cwd();
const selection = { roots: [selectWorkspaceProject(loadWorkspaceGraph(repository), "platform/contracts/tsconfig.runtime-test.json")], includeRootDevDependencies: true };
prepareWorkspaceRuntime({ repository, compiledRoot: runtimeRoot, selection });

const sourceDirectory = "platform/contracts/tests";
function runtimeSources(directory, relativeDirectory = "") {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const relativePath = join(relativeDirectory, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Runtime test discovery does not support symlinks: ${relativePath}`);
    if (entry.isDirectory()) return runtimeSources(join(directory, entry.name), relativePath);
    return entry.isFile() && entry.name.endsWith("-runtime.test.ts") ? [relativePath] : [];
  });
}
const testFiles = runtimeSources(sourceDirectory).sort().map((fileName) => fileName.replace(/\.ts$/, ".js"));
if (testFiles.length === 0) throw new Error(`No runtime tests found in ${sourceDirectory}.`);
for (const testFile of testFiles) {
  try { accessSync(join(testDirectory, testFile)); }
  catch { throw new Error(`Compiled runtime test unavailable: ${testFile}`); }
}

for (const testFile of testFiles) {
  const result = spawnSync(process.execPath, [join(testDirectory, testFile)], {
    stdio: "inherit",
  });

  if (result.status !== 0) {
    process.exitCode = result.status ?? 1;
    break;
  }
}
