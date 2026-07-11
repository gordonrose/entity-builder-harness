import assert from "node:assert/strict";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcRoot = path.join(packageRoot, "src");
const packageJsonPath = path.join(packageRoot, "package.json");
const repositoryRoot = path.resolve(packageRoot, "../..");

const importSpecifierPatterns = [
  /\bimport\s+(?:type\s+)?(?:[^"'()]*?\s+from\s+)?["']([^"']+)["']/g,
  /\bexport\s+(?:type\s+)?[^"']*?\s+from\s+["']([^"']+)["']/g,
  /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g,
];
const allowedSourceImportPattern = /^(?:@kanbien\/(?:core(?:\/[a-z][a-z0-9-]*)?|platform-contracts))$/;
const forbiddenLayerImportPattern = /(?:^|\/)(?:platform\/(?:server|workers|runtime|testing|security)|products|infra)(?:\/|$)/;
const forbiddenProviderWords = /\b(?:Cognito|DynamoDB|Lambda|Fargate|CloudWatch|S3|Kafka|Redis|Prisma)\b/;

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

function assertInsidePackage(specifier, resolvedPath, relative) {
  const relativeToPackage = path.relative(packageRoot, resolvedPath);
  assert.equal(
    relativeToPackage.startsWith("..") || path.isAbsolute(relativeToPackage),
    false,
    `${relative} relative import must stay inside apps/platform-smoke, found ${specifier}`,
  );
}

const packageJson = JSON.parse(await readFile(packageJsonPath, "utf8"));
assert.equal(packageJson.name, "@kanbien/app-platform-smoke");
assert.equal(packageJson.exports?.["."], "./src/index.ts", "root package export must point to src/index.ts");
assert.equal(packageJson.dependencies?.["@kanbien/platform-contracts"], "0.0.0", "app must depend on platform/contracts");
assert.equal(packageJson.dependencies?.["@kanbien/platform-server"], undefined, "app production dependencies must not include platform/server");
assert.equal(packageJson.dependencies?.["@kanbien/platform-workers"], undefined, "app production dependencies must not include platform/workers");
assert.equal(packageJson.dependencies?.["@kanbien/platform-testing"], undefined, "app production dependencies must not include platform/testing");

const sourceFiles = (await walk(srcRoot)).filter((file) => file.endsWith(".ts"));
assert.ok(sourceFiles.length > 0, "apps/platform-smoke should expose source files");

for (const file of sourceFiles) {
  const relative = path.relative(repositoryRoot, file);
  const text = await readFile(file, "utf8");

  for (const pattern of importSpecifierPatterns) {
    for (const match of text.matchAll(pattern)) {
      const specifier = match[1];
      assert.equal(forbiddenLayerImportPattern.test(specifier), false, `${relative} must not import runtime internals or products, found ${specifier}`);

      if (specifier.startsWith(".")) {
        assertInsidePackage(specifier, path.resolve(path.dirname(file), specifier), relative);
        continue;
      }

      assert.ok(
        allowedSourceImportPattern.test(specifier),
        `${relative} may only import core contracts and platform/contracts, found ${specifier}`,
      );
    }
  }

  assert.equal(forbiddenProviderWords.test(text), false, `${relative} must not define cloud provider implementation details`);
}

console.log(`apps/platform-smoke boundary check passed for ${sourceFiles.length} source file(s).`);
