// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.entity-smoke.prepare-runtime
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Assemble only the isolated feature program exports and safe generated package wrappers.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: infra.04-deploy.entity-smoke.image.dockerfile
//     path: infra/04.deploy/03.product/image/entity-smoke/Dockerfile

import { existsSync, mkdirSync, readFileSync, writeFileSync, copyFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const repository = fileURLToPath(new URL("../../../../../", import.meta.url));
let phase = "arguments", writes = false, location = {};
try {
  const args = process.argv.slice(2);
  if (args.length < 2 || args[0] !== "--compiled-root" || !args[1] || args.slice(2).some(arg => arg !== "--dry-run")) throw new Error("arguments");
  const compiled = resolve(args[1]), dry = args.includes("--dry-run");
  const entrypoints = {
    "kanbien-entity-smoke.main": ["runEntitySmokeMain", "startup"],
    "kanbien-entity-smoke-migration.main": ["runEntitySmokeMigration", "migration"],
    "kanbien-entity-smoke-administration.main": ["runEntitySmokeAdministration", "administration"],
    "kanbien-entity-smoke-verifier.main": ["runEntitySmokeVerifier", "verification"],
    "kanbien-entity-smoke-database-proof.main": ["runEntitySmokeDatabaseProof", "verification"],
  };
  const packages = {
    "@kanbien/core": Object.fromEntries(Object.entries(JSON.parse(readFileSync(join(repository, "packages/core/package.json"), "utf8")).exports).map(([name, target]) => {
      if (typeof target !== "string" || !/^\.\/src\/[A-Za-z0-9_./-]+\.(?:ts|json)$/.test(target) || target.split("/").includes("..")) throw new Error("manifest");
      return [name, join("packages/core", target.slice(2)).replace(/\.ts$/, ".js")];
    })),
    "@kanbien/app-entity-smoke": { ".": "apps/entity-smoke/src/index.js" },
    ...Object.fromEntries(["config", "contracts", "health", "observability", "persistence", "runtime", "security"].map(name => ["@kanbien/platform-" + name, { ".": "platform/" + name + "/src/index.js" }])),
    "@kanbien/platform-server": { ".": "platform/server/src/index.js", "./main": "platform/server/src/main.js" },
    "@kanbien/platform-adapter-aws-persistence-postgresql": { ".": "platform/adapters/aws/persistence/postgresql/src/index.js" },
  };
  phase = "compiled-entrypoint";
  for (const entry of Object.keys(entrypoints)) {
    location = { entrypoint: entry };
    if (!existsSync(join(compiled, "infra/04.deploy/03.product/entrypoints", entry + ".js"))) throw new Error("missing");
  }
  phase = "compiled-export";
  for (const [name, entries] of Object.entries(packages)) for (const [exportName, target] of Object.entries(entries)) {
    location = { package: name, export: exportName };
    if (!existsSync(join(target.endsWith(".json") ? repository : compiled, target))) throw new Error("missing");
  }
  if (!dry) {
    for (const [name, entries] of Object.entries(packages)) {
      const directory = join(compiled, "node_modules", name), exports = {};
      for (const [key, target] of Object.entries(entries)) {
        location = { package: name, export: key };
        const output = key === "." ? "index.js" : key.slice(2) + (target.endsWith(".json") ? "" : "/index.js");
        const destination = join(directory, output);
        phase = "shim-directory"; writes = true; mkdirSync(dirname(destination), { recursive: true });
        if (target.endsWith(".json")) { phase = "asset-copy"; copyFileSync(join(repository, target), destination); }
        else {
          phase = "shim-write";
          const path = relative(dirname(destination), join(compiled, target)).replaceAll("\\", "/");
          writeFileSync(destination, "module.exports = require(" + JSON.stringify(path.startsWith(".") ? path : "./" + path) + ");\n");
        }
        exports[key] = "./" + output;
      }
      phase = "manifest-write"; location = { package: name };
      writeFileSync(join(directory, "package.json"), JSON.stringify({ name, type: "commonjs", exports }) + "\n");
    }
    for (const [entry, [exported, operation]] of Object.entries(entrypoints)) {
      phase = "wrapper-write"; location = { entrypoint: entry };
      const target = "./infra/04.deploy/03.product/entrypoints/" + entry + ".js";
      writeFileSync(join(compiled, entry + ".js"), "const entry = require(" + JSON.stringify(target) + ");\nmodule.exports = entry;\nif (require.main === module) void entry." + exported + "().catch(cause => { require('./infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js').reportEntitySmokeFailure(" + JSON.stringify(operation) + ", 'unknown', cause); process.exitCode = 1; });\n");
    }
    phase = "payload-manifest-write"; location = {};
    writeFileSync(join(compiled, "entity-smoke-payload.json"), JSON.stringify({ required_imports: Object.entries(packages).flatMap(([name, entries]) => Object.keys(entries).map(key => name + (key === "." ? "" : key.slice(1)))) }) + "\n");
  }
  console.log(JSON.stringify({ scope: "entity-smoke-runtime-preparation", verdict: dry ? "planned" : "prepared" }));
} catch {
  console.error(JSON.stringify({ scope: "entity-smoke-runtime-preparation", verdict: "failed", code: "runtime-preparation-boundary-failed", phase, ...location, effect: writes ? "earlier-writes-possible" : "writes-not-started" }));
  process.exitCode = 1;
}

