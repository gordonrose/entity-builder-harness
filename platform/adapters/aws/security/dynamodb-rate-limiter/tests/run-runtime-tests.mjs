import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { resolve, join } from "node:path";

const root = resolve(".cache/platform-adapter-aws-security-dynamodb-rate-limiter-runtime");
for (const [name, source] of [["@kanbien/core", "packages/core"], ["@kanbien/platform-security", "platform/security"]]) {
  const directory = join(root, "node_modules", ...name.split("/"));
  mkdirSync(directory, { recursive: true });
  const manifest = JSON.parse(readFileSync(`${source}/package.json`, "utf8"));
  const exports = {};
  for (const [entry, target] of Object.entries(manifest.exports)) {
    const file = entry === "." ? "index.cjs" : `${entry.slice(2)}.cjs`;
    exports[entry] = `./${file}`;
    writeFileSync(join(directory, file), `module.exports = require(${JSON.stringify(join(root, source, target.replace(/\.ts$/, ".js")))});\n`);
  }
  writeFileSync(join(directory, "package.json"), JSON.stringify({ name, type: "commonjs", exports }));
}

const result = spawnSync(
  process.execPath,
  [".cache/platform-adapter-aws-security-dynamodb-rate-limiter-runtime/platform/adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-runtime.test.js"],
  { stdio: "inherit" },
);

process.exitCode = result.status ?? 1;
