import { accessSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, relative, join, sep } from "node:path";

const runtimeRoot = ".cache/platform-adapter-aws-runtime-ecs-fargate-runtime";
const coreModules = ["audit", "authn", "authz", "config", "diagnostics", "events", "i18n", "logging", "monitoring", "persistence", "queues", "security", "shared", "tenancy", "validation"];
const packages = {
  "@kanbien/core": { ".": "packages/core/src/index.js", ...Object.fromEntries(coreModules.map((name) => [`./${name}`, `packages/core/src/${name}/index.js`])) },
  ...Object.fromEntries(["config", "contracts", "health", "observability", "runtime", "security", "server"].map((name) => [`@kanbien/platform-${name}`, { ".": `platform/${name}/src/index.js` }])),
};
for (const [name, exportsMap] of Object.entries(packages)) {
  const packageRoot = join(runtimeRoot, "node_modules", ...name.split("/"));
  const exports = {};
  for (const [key, target] of Object.entries(exportsMap)) {
    const shim = join(packageRoot, key === "." ? "index.js" : `${key.slice(2)}/index.js`);
    mkdirSync(dirname(shim), { recursive: true });
    const source = relative(dirname(shim), join(runtimeRoot, target)).replaceAll(sep, "/");
    writeFileSync(shim, `module.exports = require(${JSON.stringify(source.startsWith(".") ? source : `./${source}`)});\n`);
    exports[key] = key === "." ? "./index.js" : `${key}/index.js`;
  }
  writeFileSync(join(packageRoot, "package.json"), JSON.stringify({ name, type: "commonjs", exports }));
}

const testDirectory = join(runtimeRoot, "platform/adapters/aws/runtime/ecs-fargate/tests");
const sourceDirectory = "platform/adapters/aws/runtime/ecs-fargate/tests";
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
