import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { inspectIndex, inspectModuleDependencies } from "../../../scripts/repo/module-structure/check.mjs";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcRoot = path.join(packageRoot, "src");
const packageJsonPath = path.join(packageRoot, "package.json");

const expectedModules = [
  "audit",
  "authn",
  "authz",
  "config",
  "diagnostics",
  "events",
  "files",
  "i18n",
  "logging",
  "localization",
  "monitoring",
  "persistence",
  "queues",
  "security",
  "shared",
  "tenancy",
  "validation",
];

function assertSameValues(actual, expected, label) {
  assert.deepEqual([...actual].sort(), [...expected].sort(), `${label} must match`);
}

async function walk(dir) {
  const entries = await readdir(dir);
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry);
    const details = await stat(fullPath);
    if (details.isDirectory()) {
      files.push(...await walk(fullPath));
    } else {
      files.push(fullPath);
    }
  }
  return files;
}

const packageJson = JSON.parse(await readFile(packageJsonPath, "utf8"));
const exportEntries = Object.entries(packageJson.exports ?? {});
const assetEntries = exportEntries.filter(([, target]) => typeof target === "string" && target.endsWith(".json"));
assertSameValues(assetEntries.map(([key]) => key), ["./config/diagnostics.v1.json"], "public JSON assets");
for (const [key, target] of assetEntries) {
  assert.equal(target, "./src/config/contract/reporting/diagnostics.v1.json", `${key} must name its module-owned generated asset`);
  assert.equal((await stat(path.join(packageRoot, target))).isFile(), true);
  const asset = JSON.parse(await readFile(path.join(packageRoot, target), "utf8"));
  assert.equal(asset.schema, "core/diagnostic-catalog-export/v1");
  assert.equal(asset.catalog.owner, "core.config");
}
const exportedModules = exportEntries.filter(([, target]) => typeof target !== "string" || !target.endsWith(".json"))
  .filter(([key]) => key !== ".")
  .map(([key]) => {
    assert.ok(key.startsWith("./"), `package export ${key} must be a subpath export`);
    return key.slice(2);
  });

assert.equal(packageJson.exports?.["."], "./src/index.ts", "root package export must point to src/index.ts");
assertSameValues(exportedModules, expectedModules, "package export module list");

const actualModules = (await readdir(srcRoot, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);
assertSameValues(actualModules, expectedModules, "source module directory list");

for (const moduleName of expectedModules) {
  const modulePath = path.join(srcRoot, moduleName, "index.ts");
  const details = await stat(modulePath);
  assert.equal(details.isFile(), true, `${moduleName} must expose index.ts`);

  assert.equal(
    packageJson.exports[`./${moduleName}`],
    `./src/${moduleName}/index.ts`,
    `${moduleName} package export must point to its module index`,
  );
}

const sourceFiles = (await walk(srcRoot)).filter((file) => file.endsWith(".ts"));
assert.ok(sourceFiles.length > expectedModules.length, "core should expose module files");

assert.deepEqual(
  inspectIndex("packages/core/src/config/index.ts", await readFile(path.join(srcRoot, "config/index.ts"), "utf8")).findings,
  [],
  "config public index must only expose implementation owned by dedicated files",
);

const importSpecifierPatterns = [
  /\bimport\s+(?:type\s+)?(?:[^"'()]*?\s+from\s+)?["']([^"']+)["']/g,
  /\bexport\s+(?:type\s+)?[^"']*?\s+from\s+["']([^"']+)["']/g,
  /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g,
];
const coreSources = new Map(await Promise.all(sourceFiles.map(async file => [
  `packages/core/${path.relative(packageRoot, file).split(path.sep).join('/')}`,
  await readFile(file, 'utf8'),
])));
assert.deepEqual(inspectModuleDependencies(coreSources).findings, [], 'adopted Core modules must keep contract/capability dependencies acyclic and public');
const forbiddenRuntimeWords = /\b(?:S3|Kafka|Redis|Fastify|Prisma|DynamoDB|CloudWatch)\b/;

for (const file of sourceFiles) {
  const relative = path.relative(packageRoot, file);
  const text = await readFile(file, "utf8");

  for (const pattern of importSpecifierPatterns) {
    for (const match of text.matchAll(pattern)) {
      const specifier = match[1];
      assert.ok(specifier.startsWith("."), `${relative} must use only relative imports, found ${specifier}`);
    }
  }

  assert.equal(forbiddenRuntimeWords.test(text), false, `${relative} must not define runtime provider implementation details`);
}

console.log(`packages/core boundary check passed for ${sourceFiles.length} source file(s).`);
