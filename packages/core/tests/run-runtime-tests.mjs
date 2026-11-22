import { accessSync, readdirSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";
import { selectAffectedRuntimeTests } from "../../../scripts/repo/workspace-build/runtime-test-selection.mjs";

const repositoryRoot = resolve(process.cwd());
const sourceDirectory = resolve(repositoryRoot, "packages/core/tests");
const compiledDirectory = resolve(repositoryRoot, ".cache/packages-core-runtime/tests");

function runtimeSources(directory, relativeDirectory = "") {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const relativePath = join(relativeDirectory, entry.name);
    if (entry.isSymbolicLink()) {
      throw new Error(`Core test discovery does not support symlinks: ${relativePath}`);
    }
    if (entry.isDirectory()) return runtimeSources(join(directory, entry.name), relativePath);
    return entry.isFile() && entry.name.endsWith("-runtime.test.ts") ? [relativePath] : [];
  });
}

function changedPaths() {
  const value = process.env.REPO_CHECK_CHANGED_PATHS;
  if (value === undefined) return undefined;
  try {
    const parsed = JSON.parse(value);
    if (!Array.isArray(parsed) || !parsed.every(path => typeof path === "string")) throw new Error();
    return parsed;
  } catch {
    throw new Error("Core runtime-test changed-path context is invalid.");
  }
}

function selectedRuntimeSources() {
  const all = runtimeSources(sourceDirectory).sort();
  const changed = changedPaths();
  if (changed === undefined) return all;
  const selection = selectAffectedRuntimeTests({
    root: repositoryRoot,
    sourceDirectory: "packages/core/src",
    testDirectory: "packages/core/tests",
    changedPaths: changed,
  });
  if (selection.mode === "full") return all;
  return selection.testFiles.map(path => {
    const value = relative(sourceDirectory, resolve(repositoryRoot, path));
    if (!value || value === ".." || value.startsWith(`..${sep}`)) throw new Error("Core runtime-test selection escaped its test root.");
    return value;
  }).sort();
}

// Source-led discovery prevents stale compiled files from creating extra cases.
const testFiles = selectedRuntimeSources()
  .map((fileName) => join(compiledDirectory, fileName.replace(/\.ts$/, ".js")));

if (testFiles.length === 0) {
  throw new Error(`No packages/core runtime tests found in ${sourceDirectory}.`);
}

// Reject incomplete compilation before executing any case.
for (const testFile of testFiles) {
  try { accessSync(testFile); }
  catch { throw new Error(`Compiled Core runtime test unavailable: ${testFile}`); }
}

for (const testFile of testFiles) {
  const result = spawnSync(process.execPath, [testFile], {
    stdio: "inherit",
  });

  if (result.status !== 0) {
    process.exitCode = result.status ?? 1;
    break;
  }
}
