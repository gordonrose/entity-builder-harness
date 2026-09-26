import assert from "node:assert/strict";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcRoot = path.join(packageRoot, "src");
const packageJsonPath = path.join(packageRoot, "package.json");
const repositoryRoot = path.resolve(packageRoot, "../../../../..");
const allowedSourceImportPattern = /^(?:node:crypto|pg|@kanbien\/core(?:\/[^"']+)?|@kanbien\/platform-persistence|\.\.?\/[^"']+)$/;

async function walk(dir) {
  const entries = await readdir(dir);
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry);
    const details = await stat(fullPath);
    if (details.isDirectory()) files.push(...await walk(fullPath));
    else files.push(fullPath);
  }
  return files;
}

const packageJson = JSON.parse(await readFile(packageJsonPath, "utf8"));
assert.equal(packageJson.name, "@kanbien/platform-adapter-aws-persistence-postgresql");
assert.equal(packageJson.dependencies?.pg, "^8.23.0");
assert.equal(packageJson.dependencies?.["@kanbien/platform-persistence"], "0.0.0");

const sourceFiles = (await walk(srcRoot)).filter((file) => file.endsWith(".ts"));
assert.ok(sourceFiles.length >= 10, "PostgreSQL persistence adapter should expose semantic source modules");

for (const file of sourceFiles) {
  const relative = path.relative(repositoryRoot, file);
  const text = await readFile(file, "utf8");
  assert.equal(/(?:^|\/)(?:apps|infra)(?:\/|$)/m.test(text), false, relative + " must not import app or infra layers");
  for (const match of text.matchAll(/\bimport\s+(?:type\s+)?(?:[^"'()]*?\s+from\s+)?["']([^"']+)["']/g)) {
    assert.ok(allowedSourceImportPattern.test(match[1]), relative + " has disallowed import " + match[1]);
  }
}

console.log("PostgreSQL persistence adapter boundary check passed for " + sourceFiles.length + " source file(s).");
