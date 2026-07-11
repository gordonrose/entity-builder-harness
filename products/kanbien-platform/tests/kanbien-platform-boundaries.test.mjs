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
const allowedSourceImportPattern = /^@kanbien\/app-platform-smoke$/;
const forbiddenTargetWords = /\b(?:AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|COGNITO_USER_POOL_ID|ECS_CLUSTER|arn:|https:\/\/|accountId|region)\b/;

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
    `${relative} relative import must stay inside products/kanbien-platform, found ${specifier}`,
  );
}

const packageJson = JSON.parse(await readFile(packageJsonPath, "utf8"));
assert.equal(packageJson.name, "@kanbien/product-kanbien-platform");
assert.equal(packageJson.exports?.["."], "./src/index.ts", "root package export must point to src/index.ts");
assert.equal(packageJson.dependencies?.["@kanbien/app-platform-smoke"], "0.0.0", "product must depend on public app package");
assert.equal(packageJson.dependencies?.["@kanbien/platform-server"], undefined, "product production dependencies must not include platform/server");
assert.equal(packageJson.dependencies?.["@kanbien/platform-workers"], undefined, "product production dependencies must not include platform/workers");

const sourceFiles = (await walk(srcRoot)).filter((file) => file.endsWith(".ts"));
assert.ok(sourceFiles.length > 0, "products/kanbien-platform should expose source files");

for (const file of sourceFiles) {
  const relative = path.relative(repositoryRoot, file);
  const text = await readFile(file, "utf8");

  for (const pattern of importSpecifierPatterns) {
    for (const match of text.matchAll(pattern)) {
      const specifier = match[1];

      if (specifier.startsWith(".")) {
        assertInsidePackage(specifier, path.resolve(path.dirname(file), specifier), relative);
        continue;
      }

      assert.ok(
        allowedSourceImportPattern.test(specifier),
        `${relative} may only import public app package roots, found ${specifier}`,
      );
      assert.equal(specifier.includes("/src/"), false, `${relative} must not import app internals, found ${specifier}`);
    }
  }

  assert.equal(forbiddenTargetWords.test(text), false, `${relative} must not include deployment target values`);
}

console.log(`products/kanbien-platform boundary check passed for ${sourceFiles.length} source file(s).`);
