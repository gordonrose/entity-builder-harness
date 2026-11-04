import { mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const testDirectory = ".cache/platform-contracts-runtime/platform/contracts/tests";
const coreRoot = ".cache/platform-contracts-runtime/node_modules/@kanbien/core";
mkdirSync(join(coreRoot, "diagnostics"), { recursive: true });
writeFileSync(join(coreRoot, "package.json"), JSON.stringify({ name: "@kanbien/core", type: "commonjs", exports: { ".": "./index.js", "./diagnostics": "./diagnostics/index.js" } }));
writeFileSync(join(coreRoot, "index.js"), 'module.exports = require("../../../packages/core/src/index.js");\n');
writeFileSync(join(coreRoot, "diagnostics/index.js"), 'module.exports = require("../../../../packages/core/src/diagnostics/index.js");\n');
const testFiles = readdirSync(testDirectory)
  .filter((fileName) => fileName.endsWith("-runtime.test.js"))
  .sort();

if (testFiles.length === 0) {
  throw new Error(`No platform/contracts runtime tests found in ${testDirectory}.`);
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
