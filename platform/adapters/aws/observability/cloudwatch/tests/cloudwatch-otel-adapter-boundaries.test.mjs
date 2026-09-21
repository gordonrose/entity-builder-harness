import assert from "node:assert/strict"; // Fail deterministically when the adapter crosses an architectural boundary.
import { readdir, readFile, stat } from "node:fs/promises"; // Inspect the adapter source tree without executing its runtime code.
import path from "node:path"; // Construct repository-relative paths safely.
import { fileURLToPath } from "node:url"; // Resolve this ES module's own directory reliably.

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."); // Locate the adapter package root from this test file.
const srcRoot = path.join(packageRoot, "src"); // Locate the adapter implementation source directory.
const packageJsonPath = path.join(packageRoot, "package.json"); // Locate the package contract metadata.
const repositoryRoot = path.resolve(packageRoot, "../../../../.."); // Locate the repository root for readable test diagnostics.
const allowedSourceImportPattern = /^(?:@opentelemetry\/(?:api|exporter-metrics-otlp-proto|resources|sdk-metrics)|@kanbien\/core\/monitoring)$/; // Permit only Core monitoring and OTel SDK imports inside this provider adapter.

const packageJson = JSON.parse(await readFile(packageJsonPath, "utf8")); // Read the adapter package metadata once.
assert.equal(packageJson.name, "@kanbien/platform-adapter-aws-observability-cloudwatch"); // Prove the public package identity matches the adapter path.
assert.equal(packageJson.dependencies?.["@kanbien/core"], "0.0.0"); // Prove the adapter depends on the provider-neutral Core contract.
assert.ok(packageJson.dependencies?.["@opentelemetry/sdk-metrics"]); // Prove a real OTel metrics SDK backs the adapter rather than an invented format.
assert.ok(packageJson.dependencies?.["@opentelemetry/exporter-metrics-otlp-proto"]); // Prove a real OTLP metric exporter backs the adapter.

const sourceFiles = (await walk(srcRoot)).filter((file) => file.endsWith(".ts")); // Collect every TypeScript source file for boundary inspection.
assert.ok(sourceFiles.length > 0, "CloudWatch OTel adapter should expose source files"); // Ensure an empty package cannot pass the boundary test.

for (const file of sourceFiles) { // Check every implementation file individually.
  const relative = path.relative(repositoryRoot, file); // Produce a readable repository-relative failure path.
  const text = await readFile(file, "utf8"); // Read source as text so imports and forbidden layers can be checked.
  assert.equal(/(?:^|\/)(?:apps|infra)(?:\/|$)/m.test(text), false, relative + " must not import app or infra layers"); // Keep provider adapter code independent of applications and CloudFormation.
  for (const match of text.matchAll(/\bimport\s+(?:type\s+)?(?:[^"'()]*?\s+from\s+)?["']([^"']+)["']/g)) { // Inspect each static ES module import.
    assert.ok(allowedSourceImportPattern.test(match[1]), relative + " has disallowed import " + match[1]); // Reject cross-layer, provider-client, or app imports not owned by this adapter.
  }
}

console.log("CloudWatch OTel adapter boundary check passed for " + sourceFiles.length + " source file(s)."); // Make successful standalone execution clear in governed check output.

async function walk(dir) { // Recursively enumerate adapter source files without shelling out.
  const entries = await readdir(dir); // Read direct entries in the current source directory.
  const files = []; // Collect nested file paths in traversal order.
  for (const entry of entries) { // Inspect each directory entry.
    const fullPath = path.join(dir, entry); // Form the absolute path for metadata lookup.
    const details = await stat(fullPath); // Determine whether this entry is a directory or file.
    if (details.isDirectory()) { // Recurse into nested source directories.
      files.push(...await walk(fullPath)); // Add all nested files to the final list.
    } else { // Retain ordinary files for the caller's filter.
      files.push(fullPath); // Add this source file path.
    }
  }
  return files; // Return the complete recursive source file list.
}
