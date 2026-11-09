import { accessSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { mkdirSync, readdirSync, writeFileSync } from "node:fs";
import path, { join } from "node:path";

const runtimeRoot = ".cache/platform-adapter-aws-queue-sqs-runtime";
const testDirectory = join(runtimeRoot, "platform/adapters/aws/queue/sqs/tests");

writePackageShim("@kanbien/core", {
  ".": join(runtimeRoot, "packages/core/src/index.js"),
  "./config": join(runtimeRoot, "packages/core/src/config/index.js"),
  "./diagnostics": join(runtimeRoot, "packages/core/src/diagnostics/index.js"),
  "./shared": join(runtimeRoot, "packages/core/src/shared/index.js"),
});

const sourceDirectory = "platform/adapters/aws/queue/sqs/tests";
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
  if (result.status !== 0) {
    process.exitCode = result.status ?? 1;
    break;
  }
}

function writePackageShim(packageName, exportsMap) {
  const packageRoot = join(runtimeRoot, "node_modules", ...packageName.split("/"));
  mkdirSync(packageRoot, { recursive: true });

  const packageExports = {};
  for (const [exportName, targetPath] of Object.entries(exportsMap)) {
    const shimPath = exportName === "."
      ? join(packageRoot, "index.js")
      : join(packageRoot, exportName.slice(2), "index.js");
    mkdirSync(path.dirname(shimPath), { recursive: true });
    writeFileSync(shimPath, `module.exports = require(${JSON.stringify(relativeRequirePath(shimPath, targetPath))});\n`);
    packageExports[exportName] = exportName === "." ? "./index.js" : `./${exportName.slice(2)}/index.js`;
  }

  writeFileSync(
    join(packageRoot, "package.json"),
    `${JSON.stringify({ name: packageName, type: "commonjs", exports: packageExports }, null, 2)}\n`,
  );
}

function relativeRequirePath(fromFile, toFile) {
  const relativePath = path.relative(path.dirname(fromFile), toFile).replaceAll(path.sep, "/");
  return relativePath.startsWith(".") ? relativePath : `./${relativePath}`;
}
