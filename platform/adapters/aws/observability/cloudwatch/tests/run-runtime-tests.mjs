import { spawnSync } from "node:child_process"; // Run the compiled CommonJS runtime test in a deterministic Node process.
import { mkdirSync, writeFileSync } from "node:fs"; // Create a local compiled-package shim without modifying the repository source tree.
import path, { join } from "node:path"; // Build portable runtime and shim paths.

const runtimeRoot = process.env["KANBIEN_CLOUDWATCH_OTEL_RUNTIME_ROOT"] ?? ".cache/platform-adapter-aws-observability-cloudwatch-runtime"; // Permit a disposable output root when a governed worktree cache is intentionally read-only.
writePackageShim("@kanbien/platform-observability", { ".": join(runtimeRoot, "platform/observability/src/index.js") });
writePackageShim("@kanbien/platform-contracts", { ".": join(runtimeRoot, "platform/contracts/src/index.js") });
writePackageShim("@kanbien/core", { // Point the Core workspace package at compiled JavaScript rather than its TypeScript source.
  ...Object.fromEntries(["audit", "authn", "authz", "config", "diagnostics", "events", "i18n", "logging", "persistence", "queues", "security", "tenancy", "validation"].map((name) => [`./${name}`, join(runtimeRoot, `packages/core/src/${name}/index.js`)])),
  ".": join(runtimeRoot, "packages/core/src/index.js"), // Map the Core public barrel to emitted JavaScript.
  "./monitoring": join(runtimeRoot, "packages/core/src/monitoring/index.js"), // Map the monitoring subpath imported by the adapter.
  "./shared": join(runtimeRoot, "packages/core/src/shared/index.js"), // Map the shared subpath imported by the test.
}); // Finish the compiled Core package shim.

for (const testFile of ["cloudwatch-otel-adapter-runtime.test.js", "cloudwatch-otel-lifecycle-runtime.test.js"]) {
  const result = spawnSync(process.execPath, [join(runtimeRoot, "platform/adapters/aws/observability/cloudwatch/tests", testFile)], { stdio: "inherit" });
  if (result.status !== 0) { process.exitCode = result.status ?? 1; break; }
}

function writePackageShim(packageName, exportsMap) { // Write one CommonJS-compatible package shim under the compiled runtime root.
  const packageRoot = join(runtimeRoot, "node_modules", ...packageName.split("/")); // Resolve the shim package directory.
  mkdirSync(packageRoot, { recursive: true }); // Ensure nested scoped-package directories exist.

  const packageExports = {}; // Build the package export map alongside shim files.
  for (const [exportName, targetPath] of Object.entries(exportsMap)) { // Create a shim file for every requested subpath.
    const shimPath = exportName === "." // Select the public-barrel file location.
      ? join(packageRoot, "index.js") // Use index.js for the main package export.
      : join(packageRoot, exportName.slice(2), "index.js"); // Use a nested index.js for each subpath export.
    mkdirSync(path.dirname(shimPath), { recursive: true }); // Ensure the nested subpath directory exists.
    writeFileSync(shimPath, `module.exports = require(${JSON.stringify(relativeRequirePath(shimPath, targetPath))});\n`); // Redirect CommonJS resolution to the emitted JavaScript module.
    packageExports[exportName] = exportName === "." ? "./index.js" : `./${exportName.slice(2)}/index.js`; // Add the same path to package exports.
  }

  writeFileSync( // Write the minimal package manifest that enables Node export resolution.
    join(packageRoot, "package.json"), // Target the scoped package metadata file.
    `${JSON.stringify({ name: packageName, type: "commonjs", exports: packageExports }, null, 2)}\n`, // Preserve a readable deterministic manifest.
  ); // Finish the package manifest write.
}

function relativeRequirePath(fromFile, toFile) { // Resolve an emitted module relative to its generated shim file.
  const relativePath = path.relative(path.dirname(fromFile), toFile).replaceAll(path.sep, "/"); // Create portable slash-normalized paths.
  return relativePath.startsWith(".") ? relativePath : `./${relativePath}`; // Ensure Node receives an explicit relative require path.
}
