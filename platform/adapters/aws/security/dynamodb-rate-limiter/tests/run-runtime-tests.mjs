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

const result = spawnSync(
  process.execPath,
  [".cache/platform-adapter-aws-security-dynamodb-rate-limiter-runtime/platform/adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-runtime.test.js"],
  { stdio: "inherit" },
);

process.exitCode = result.status ?? 1;
