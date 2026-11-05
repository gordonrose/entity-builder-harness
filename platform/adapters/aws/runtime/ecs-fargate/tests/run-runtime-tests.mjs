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

const result = spawnSync(
  process.execPath,
  [join(runtimeRoot, "platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-runtime.test.js")],
  { stdio: "inherit" },
);

process.exitCode = result.status ?? 1;
