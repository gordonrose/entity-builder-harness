import { accessSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { deepEqual } from "node:assert/strict";
import { copyFileSync, mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(".cache/platform-adapter-aws-security-dynamodb-rate-limiter-runtime");
const sourceRoot = fileURLToPath(new URL("../../../../../../", import.meta.url));
const load = createRequire(join(root, "package-fixture.cjs"));
for (const [name, source] of [["@kanbien/core", "packages/core"], ["@kanbien/platform-security", "platform/security"]]) {
  const directory = join(root, "node_modules", ...name.split("/"));
  mkdirSync(directory, { recursive: true });
  const manifest = JSON.parse(readFileSync(join(sourceRoot, source, "package.json"), "utf8"));
  const exports = {};
  for (const [entry, target] of Object.entries(manifest.exports)) {
    const file = entry === "." ? "index.cjs" : target.endsWith(".json") ? entry.slice(2) : `${entry.slice(2)}.cjs`;
    exports[entry] = `./${file}`;
    mkdirSync(dirname(join(directory, file)), { recursive: true });
    if (target.endsWith(".json")) copyFileSync(join(sourceRoot, source, target), join(directory, file));
    else writeFileSync(join(directory, file), `module.exports = require(${JSON.stringify(join(root, source, target.replace(/\.ts$/, ".js")))});\n`);
  }
  writeFileSync(join(directory, "package.json"), JSON.stringify({ name, type: "commonjs", exports }));
  for (const [entry, target] of Object.entries(manifest.exports)) {
    if (target.endsWith(".json")) deepEqual(load(name + entry.slice(1)),
      JSON.parse(readFileSync(join(sourceRoot, source, target), "utf8")),
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
