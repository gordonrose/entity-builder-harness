import { spawnSync } from "node:child_process";
import { mkdirSync, readdirSync, writeFileSync } from "node:fs";
import path, { join } from "node:path";

const runtimeRoot = ".cache/platform-server-runtime";
const testDirectory = join(runtimeRoot, "platform/server/tests");
const coreModules = [
  "audit",
  "authn",
  "authz",
  "config",
  "diagnostics",
  "events",
  "i18n",
  "logging",
  "monitoring",
  "queues",
  "shared",
  "tenancy",
  "validation",
];

writePackageShim("@kanbien/core", {
  ".": join(runtimeRoot, "packages/core/src/index.js"),
  ...Object.fromEntries(coreModules.map((moduleName) => [`./${moduleName}`, join(runtimeRoot, `packages/core/src/${moduleName}/index.js`)])),
});
writePackageShim("@kanbien/platform-contracts", {
  ".": join(runtimeRoot, "platform/contracts/src/index.js"),
});
writePackageShim("@kanbien/platform-config", {
  ".": join(runtimeRoot, "platform/config/src/index.js"),
});
writePackageShim("@kanbien/platform-health", {
  ".": join(runtimeRoot, "platform/health/src/index.js"),
});
writePackageShim("@kanbien/platform-observability", {
  ".": join(runtimeRoot, "platform/observability/src/index.js"),
});
writePackageShim("@kanbien/platform-runtime", {
  ".": join(runtimeRoot, "platform/runtime/src/index.js"),
});
writePackageShim("@kanbien/platform-security", {
  ".": join(runtimeRoot, "platform/security/src/index.js"),
});
writePackageShim("@kanbien/platform-testing", {
  ".": join(runtimeRoot, "platform/testing/src/index.js"),
});

const testFiles = readdirSync(testDirectory)
  .filter((fileName) => fileName.endsWith("-runtime.test.js"))
  .sort();

if (testFiles.length === 0) {
  throw new Error(`No platform/server runtime tests found in ${testDirectory}.`);
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
