#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.build-platform-shell-image.prepare-runtime
//   version: 2
//   status: active
//   created_on: "2026-07-10"
//   updated_on: "2026-10-31"
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - agentic
//   - sre
//   kind: script
//   purpose: Prepare CommonJS package shims for the platform shell image runtime payload.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.script.build-platform-shell-image
//     path: scripts/04.deploy/build-platform-shell-image/script.sh

import { mkdirSync, writeFileSync } from "node:fs";
import path, { join } from "node:path";

const runtimeRoot = ".cache/platform-shell-image-build";
let preparationPhase = "package-shim";
let preparationLocation = {};
try {
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
  "persistence",
  "queues",
  "security",
  "shared",
  "tenancy",
  "validation",
];

writePackageShim("@kanbien/core", {
  ".": join(runtimeRoot, "packages/core/src/index.js"),
  ...Object.fromEntries(coreModules.map((moduleName) => [`./${moduleName}`, join(runtimeRoot, `packages/core/src/${moduleName}/index.js`)])),
});
writePackageShim("@kanbien/app-platform-smoke", {
  ".": join(runtimeRoot, "apps/platform-smoke/src/index.js"),
});
writePackageShim("@kanbien/product-kanbien-platform", {
  ".": join(runtimeRoot, "products/kanbien-platform/src/index.js"),
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
writePackageShim("@kanbien/platform-persistence", {
  ".": join(runtimeRoot, "platform/persistence/src/index.js"),
});
writePackageShim("@kanbien/platform-runtime", {
  ".": join(runtimeRoot, "platform/runtime/src/index.js"),
});
writePackageShim("@kanbien/platform-security", {
  ".": join(runtimeRoot, "platform/security/src/index.js"),
});
writePackageShim("@kanbien/platform-server", {
  ".": join(runtimeRoot, "platform/server/src/index.js"),
  "./main": join(runtimeRoot, "platform/server/src/main.js"),
});
writePackageShim("@kanbien/platform-workers", {
  ".": join(runtimeRoot, "platform/workers/src/index.js"),
  "./main": join(runtimeRoot, "platform/workers/src/main.js"),
});
writePackageShim("@kanbien/platform-adapter-aws-auth-cognito", {
  ".": join(runtimeRoot, "platform/adapters/aws/auth/cognito/src/index.js"),
});
writePackageShim("@kanbien/platform-adapter-aws-observability-cloudwatch", {
  ".": join(runtimeRoot, "platform/adapters/aws/observability/cloudwatch/src/index.js"),
});
writePackageShim("@kanbien/platform-adapter-aws-persistence-dynamodb", {
  ".": join(runtimeRoot, "platform/adapters/aws/persistence/dynamodb/src/index.js"),
});
writePackageShim("@kanbien/platform-adapter-aws-persistence-postgresql", {
  ".": join(runtimeRoot, "platform/adapters/aws/persistence/postgresql/src/index.js"),
});
writePackageShim("@kanbien/platform-adapter-aws-queue-sqs", {
  ".": join(runtimeRoot, "platform/adapters/aws/queue/sqs/src/index.js"),
});
writePackageShim("@kanbien/platform-adapter-aws-runtime-ecs-fargate", {
  ".": join(runtimeRoot, "platform/adapters/aws/runtime/ecs-fargate/src/index.js"),
});
writePackageShim("@kanbien/platform-adapter-aws-security-dynamodb-rate-limiter", {
  ".": join(runtimeRoot, "platform/adapters/aws/security/dynamodb-rate-limiter/src/index.js"),
});

console.log(`Prepared platform shell image runtime at ${runtimeRoot}`);
} catch {
  console.error(JSON.stringify({ scope: "platform-shell-runtime-preparation", verdict: "failed", code: "runtime-preparation-boundary-failed", phase: preparationPhase, ...preparationLocation, effect: "earlier-writes-possible" }));
  process.exitCode = 1;
}

function writePackageShim(packageName, exportsMap) {
  preparationLocation = { package: packageName };
  const packageRoot = join(runtimeRoot, "node_modules", ...packageName.split("/"));
  preparationPhase = "shim-directory";
  mkdirSync(packageRoot, { recursive: true });

  const packageExports = {};
  for (const [exportName, targetPath] of Object.entries(exportsMap)) {
    preparationLocation = { package: packageName, export: exportName };
    const shimPath = exportName === "."
      ? join(packageRoot, "index.js")
      : join(packageRoot, exportName.slice(2), "index.js");
    preparationPhase = "shim-directory";
    mkdirSync(path.dirname(shimPath), { recursive: true });
    preparationPhase = "shim-write";
    writeFileSync(shimPath, `module.exports = require(${JSON.stringify(relativeRequirePath(shimPath, targetPath))});\n`);
    packageExports[exportName] = exportName === "." ? "./index.js" : `./${exportName.slice(2)}/index.js`;
  }

  preparationPhase = "manifest-write";
  preparationLocation = { package: packageName };
  writeFileSync(
    join(packageRoot, "package.json"),
    `${JSON.stringify({ name: packageName, type: "commonjs", exports: packageExports }, null, 2)}\n`,
  );
}

function relativeRequirePath(fromFile, toFile) {
  const relativePath = path.relative(path.dirname(fromFile), toFile).replaceAll(path.sep, "/");
  return relativePath.startsWith(".") ? relativePath : `./${relativePath}`;
}
