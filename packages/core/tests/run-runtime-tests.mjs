import { readdirSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const testDirectory = ".cache/packages-core-runtime/tests";
const testFiles = readdirSync(testDirectory)
  .filter((fileName) => fileName.endsWith("-runtime.test.js"))
  .sort();

if (testFiles.length === 0) {
  throw new Error(`No packages/core runtime tests found in ${testDirectory}.`);
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
