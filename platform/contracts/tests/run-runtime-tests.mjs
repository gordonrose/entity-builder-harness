import { accessSync } from "node:fs";
import { mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const testDirectory = ".cache/platform-contracts-runtime/platform/contracts/tests";
const coreRoot = ".cache/platform-contracts-runtime/node_modules/@kanbien/core";
mkdirSync(join(coreRoot, "diagnostics"), { recursive: true });
writeFileSync(join(coreRoot, "package.json"), JSON.stringify({ name: "@kanbien/core", type: "commonjs", exports: { ".": "./index.js", "./diagnostics": "./diagnostics/index.js" } }));
writeFileSync(join(coreRoot, "index.js"), 'module.exports = require("../../../packages/core/src/index.js");\n');
writeFileSync(join(coreRoot, "diagnostics/index.js"), 'module.exports = require("../../../../packages/core/src/diagnostics/index.js");\n');
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
