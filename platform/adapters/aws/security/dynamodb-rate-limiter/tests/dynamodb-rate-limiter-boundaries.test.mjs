import assert from "node:assert/strict";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcRoot = path.join(packageRoot, "src");
const packageJsonPath = path.join(packageRoot, "package.json");
const repositoryRoot = path.resolve(packageRoot, "../../../../..");
const allowedSourceImportPattern = /^(?:node:crypto|@aws-sdk\/client-dynamodb|@kanbien\/(?:core|platform-security))$/;

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
assert.equal(packageJson.name, "@kanbien/platform-adapter-aws-security-dynamodb-rate-limiter");
assert.equal(packageJson.dependencies?.["@aws-sdk/client-dynamodb"], "^3.1127.0");
assert.equal(packageJson.dependencies?.["@kanbien/platform-security"], "0.0.0");

const sourceFiles = (await walk(srcRoot)).filter((file) => file.endsWith(".ts"));
assert.ok(sourceFiles.length > 0, "DynamoDB rate-limit adapter should expose source files");

for (const file of sourceFiles) {
  const relative = path.relative(repositoryRoot, file);
  const text = await readFile(file, "utf8");
  assert.equal(/(?:^|\/)(?:apps|infra)(?:\/|$)/m.test(text), false, relative + " must not import app or infra layers");
  for (const match of text.matchAll(/\bimport\s+(?:type\s+)?(?:[^"'()]*?\s+from\s+)?["']([^"']+)["']/g)) {
    assert.ok(allowedSourceImportPattern.test(match[1]), relative + " has disallowed import " + match[1]);
  }
}

console.log("DynamoDB rate-limit adapter boundary check passed for " + sourceFiles.length + " source file(s).");
