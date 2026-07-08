import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcRoot = path.join(packageRoot, "src");

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

for (const moduleName of expectedModules) {
  const modulePath = path.join(srcRoot, moduleName, "index.ts");
  const details = await stat(modulePath);
  assert.equal(details.isFile(), true, `${moduleName} must expose index.ts`);
}

const sourceFiles = (await walk(srcRoot)).filter((file) => file.endsWith(".ts"));
assert.ok(sourceFiles.length > expectedModules.length, "core should expose module files");

const forbiddenImport = /from\s+["'](?:\.\.\/)*(?:apps|platform|infra)\//;
const forbiddenRuntimeWords = /\b(?:S3|Kafka|Redis|Fastify|Prisma|DynamoDB|CloudWatch)\b/;

for (const file of sourceFiles) {
  const relative = path.relative(packageRoot, file);
  const text = await readFile(file, "utf8");
  assert.equal(forbiddenImport.test(text), false, `${relative} must not import app, platform, or infra code`);
  assert.equal(forbiddenRuntimeWords.test(text), false, `${relative} must not define runtime provider implementation details`);
}

console.log(`packages/core boundary check passed for ${sourceFiles.length} source file(s).`);
