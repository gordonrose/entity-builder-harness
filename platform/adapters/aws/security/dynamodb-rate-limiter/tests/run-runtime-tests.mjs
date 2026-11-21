import { accessSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { deepEqual } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve, join } from "node:path";
import { loadWorkspaceGraph, selectWorkspaceProject } from "../../../../../../scripts/repo/workspace-build/declarations.mjs";
import { prepareWorkspaceRuntime } from "../../../../../../scripts/repo/workspace-build/runtime-packages.mjs";

const root = resolve(".cache/platform-adapter-aws-security-dynamodb-rate-limiter-runtime");
const sourceRoot = process.cwd();
const load = createRequire(join(root, "package-fixture.cjs"));
const selection = { roots: [selectWorkspaceProject(loadWorkspaceGraph(sourceRoot), "platform/adapters/aws/security/dynamodb-rate-limiter/tsconfig.runtime-test.json")], includeRootDevDependencies: true };
const inputs = prepareWorkspaceRuntime({ repository: sourceRoot, compiledRoot: root, selection });
for (const [name, exports] of Object.entries(inputs.packages)) {
  for (const [entry, target] of Object.entries(exports)) {
    if (target.endsWith(".json")) deepEqual(load(name + entry.slice(1)),
      JSON.parse(readFileSync(join(sourceRoot, target), "utf8")),
      "Nested catalogue exports must resolve to the source-owned JSON, not a dangling code shim.");
  }
}

const testDirectory = join(root, "platform/adapters/aws/security/dynamodb-rate-limiter/tests");
const sourceDirectory = "platform/adapters/aws/security/dynamodb-rate-limiter/tests";
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
  const result = spawnSync(process.execPath, [join(testDirectory, testFile)], { stdio: "inherit" });
  if (result.status !== 0) { process.exitCode = result.status ?? 1; break; }
}
