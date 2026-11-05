import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcRoot = path.join(packageRoot, "src");
const packageJsonPath = path.join(packageRoot, "package.json");
const repositoryRoot = path.resolve(packageRoot, "../../../../..");
const allowedSourceImportPattern = /^(?:@aws-sdk\/client-dynamodb|@kanbien\/core(?:\/[^"']+)?|@kanbien\/platform-persistence|\.\.?\/[^"']+)$/;

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
assert.equal(packageJson.name, "@kanbien/platform-adapter-aws-persistence-dynamodb");
assert.equal(packageJson.dependencies?.["@aws-sdk/client-dynamodb"], "^3.1127.0");
assert.equal(packageJson.dependencies?.["@kanbien/platform-persistence"], "0.0.0");

assert.deepEqual(Object.keys(packageJson.exports), ["."], "the supported package entry remains the root");
assert.equal(existsSync(path.join(srcRoot, "configuration.ts")), false, "retired sibling configuration bridge must not return");
const sourceFiles = (await walk(srcRoot)).filter((file) => file.endsWith(".ts"));
assert.ok(sourceFiles.length >= 7, "DynamoDB persistence adapter should expose semantic source modules");

for (const file of sourceFiles) {
  const relative = path.relative(repositoryRoot, file);
  const text = await readFile(file, "utf8");
  assert.equal(/(?:^|\/)(?:apps|infra)(?:\/|$)/m.test(text), false, relative + " must not import app or infra layers");
  for (const reference of text.matchAll(/\bfrom\s+["'](\.\.?\/[^"']+)["']/g)) {
    const target = path.resolve(path.dirname(file), reference[1]);
    assert.ok(existsSync(`${target}.ts`) || existsSync(path.join(target, "index.ts")), relative + " has unresolved source import/export " + reference[1]);
  }
  for (const match of text.matchAll(/\bimport\s+(?:type\s+)?(?:[^"'()]*?\s+from\s+)?["']([^"']+)["']/g)) {
    assert.ok(allowedSourceImportPattern.test(match[1]), relative + " has disallowed import " + match[1]);
  }
}

console.log("DynamoDB persistence adapter boundary check passed for " + sourceFiles.length + " source file(s).");
