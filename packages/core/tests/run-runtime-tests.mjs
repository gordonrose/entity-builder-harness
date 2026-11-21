import { accessSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const sourceDirectory = "packages/core/tests";
const compiledDirectory = ".cache/packages-core-runtime/tests";

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

// Source-led discovery prevents stale compiled files from creating extra cases.
const testFiles = runtimeSources(sourceDirectory).sort()
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
