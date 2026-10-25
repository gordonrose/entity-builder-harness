#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.command.build-core-server-persistence-image.verify-runtime
//   version: 1
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: script
//   purpose: Resolve assembled persistence entrypoints and package imports before image qualification.
//   portability: { class: internal, targets: [] }
//   effects: [read-only]
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { runtimeEntrypoints, wrapperSource } from "./runtime-contract.mjs";
try {
  if (process.argv.length !== 4 || process.argv[2] !== "--compiled-root") throw new Error("payload-arguments-invalid");
  const root = resolve(process.argv[3]);
  const require = createRequire(join(root, "payload-check.cjs"));
  for (const [entry, exported] of Object.entries(runtimeEntrypoints)) {
    if (!existsSync(join(root, `${entry}.js`))) throw new Error("payload-wrapper-missing");
    const wrapper = readFileSync(join(root, `${entry}.js`), "utf8");
    if (wrapper !== wrapperSource(entry, exported)) throw new Error("payload-wrapper-mismatch");
    const program = require(join(root, "infra/04.deploy/03.product/entrypoints", `${entry}.js`));
    if (typeof program[exported] !== "function") throw new Error("payload-entrypoint-export-missing");
  }
  // Loading guarded source modules resolves imports without invoking main,
  // opening sockets or reading target credentials/configuration.
  const imports = JSON.parse(readFileSync(join(root, "runtime-payload.json"), "utf8")).required_imports;
  if (!Array.isArray(imports) || imports.length === 0 || imports.some((item) => typeof item !== "string" || !item.startsWith("@kanbien/"))) throw new Error("payload-import-unresolved");
  for (const specifier of imports) require(specifier);
  if (typeof require("pg").Pool !== "function") throw new Error("payload-driver-missing");
  console.log(JSON.stringify({ verdict: "passed", evidence_class: "local-runtime", code: "persistence-payload-imports-resolved" }));
} catch (error) {
  const safe = new Set(["payload-arguments-invalid", "payload-wrapper-missing", "payload-wrapper-mismatch", "payload-entrypoint-export-missing", "payload-driver-missing"]);
  console.error(JSON.stringify({ verdict: "failed", code: safe.has(error?.message) ? error.message : "payload-import-unresolved" }));
  process.exitCode = 1;
}
