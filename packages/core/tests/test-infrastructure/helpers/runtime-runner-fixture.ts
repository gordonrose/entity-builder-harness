import { deepEqual, equal, match, notEqual } from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";

export function verifyRuntimeRunner(owner: string, expectedFailureExitCode = 7): void {
  const runner = resolve(owner, "tests/run-runtime-tests.mjs");
  function configurationValue(file: string, key: "outDir" | "rootDir"): string {
    const configuration = JSON.parse(readFileSync(file, "utf8")) as { extends?: string; compilerOptions?: { outDir?: string; rootDir?: string } };
    const value = configuration.compilerOptions?.[key];
    if (value !== undefined) return resolve(dirname(file), value);
    if (configuration.extends === undefined) throw new Error("Missing runtime fixture configuration: " + key);
    return configurationValue(resolve(dirname(file), configuration.extends), key);
  }
  const configuration = resolve(owner, "tsconfig.runtime-test.json");
  const outputRoot = relative(process.cwd(), configurationValue(configuration, "outDir"));
  const relativeTests = relative(configurationValue(configuration, "rootDir"), resolve(owner, "tests"));


  function fixture(check: (root: string, source: (name: string, compiled?: string) => void, compiled: (name: string, body: string) => void) => void): void {
    const root = mkdtempSync(join(tmpdir(), "core-test-runner-"));
    const sourceRoot = join(root, owner, "tests");
    const compiledRoot = join(root, outputRoot, relativeTests);
    const write = (file: string, body: string) => {
      mkdirSync(dirname(file), { recursive: true });
      writeFileSync(file, body);
    };
    const compiled = (name: string, body: string) => write(join(compiledRoot, name), body);
    const source = (name: string, body?: string) => {
      write(join(sourceRoot, name), "export {};\n");
      if (body !== undefined) compiled(name.replace(/\.ts$/, ".js"), body);
    };
    try {
      mkdirSync(sourceRoot, { recursive: true });
      mkdirSync(compiledRoot, { recursive: true });
      check(root, source, compiled);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  }

  function run(root: string) {
    return spawnSync(process.execPath, [runner], { cwd: root, encoding: "utf8", timeout: 10_000, env: { ...process.env, KANBIEN_CLOUDWATCH_OTEL_RUNTIME_ROOT: join(root, outputRoot) } });
  }

  fixture((root, source, compiled) => {
    source("z-runtime.test.ts", 'console.log("last");');
    source("shared/time/unit/first-runtime.test.ts", 'console.log("nested");');
    source("first-runtime.test.ts", 'console.log("flat");');
    source("shared/time/type-level/time-types.test.ts", "process.exit(91);");
    compiled("stale-runtime.test.js", "process.exit(92);");
    compiled("shared/time/unit/retired-runtime.test.js", "process.exit(93);");

    const actual = run(root);

    equal(actual.status, 0, "flat and nested source-backed cases execute successfully");
    deepEqual(actual.stdout.trim().split(/\r?\n/), ["flat", "nested", "last"],
      "discovery is deterministic, runs each case once, handles duplicate basenames and excludes type-only/stale output");
  });

  fixture((root, source) => {
    source("first-runtime.test.ts", 'console.log("must not run");');
    source("shared/time/unit/missing-runtime.test.ts");

    const actual = run(root);

    notEqual(actual.status, 0, "missing nested compilation fails the runner");
    match(actual.stderr, /Compiled (?:Core )?runtime test unavailable: .*missing-runtime\.test\.js/);
    equal(actual.stdout, "", "missing compilation is detected before other cases execute");
  });

  fixture((root, source) => {
    source("shared/time/unit/a-runtime.test.ts", 'console.log("failed case"); process.exit(7);');
    source("z-runtime.test.ts", 'console.log("must not run");');

    const actual = run(root);

    equal(actual.status, expectedFailureExitCode, "a nested child failure retains the owner's nonzero status");
    equal(actual.stdout.trim(), "failed case", "the runner stops after a failed case");
  });

  fixture((root, source, compiled) => {
    source("shared/time/type-level/time-types.test.ts", "process.exit(91);");
    compiled("retired-runtime.test.js", "process.exit(92);");

    const actual = run(root);

    notEqual(actual.status, 0, "type-only and stale output cannot conceal zero runtime cases");
    match(actual.stderr, /No (?:packages\/core )?runtime tests found/);
    equal(actual.stdout, "", "no compiled-only file executes");
  });

  fixture((root, source) => {
    source("actual-runtime.test.ts", 'console.log("must not run");');
    symlinkSync("actual-runtime.test.ts", join(root, owner, "tests/alias-runtime.test.ts"));

    const actual = run(root);

    notEqual(actual.status, 0, "ambiguous symlink discovery fails rather than silently omitting or duplicating a case");
    match(actual.stderr, /(?:Core test|Runtime test) discovery does not support symlinks/);
    equal(actual.stdout, "", "invalid discovery fails before case execution");
  });

  console.log(owner + " test-runner unit regressions passed.");
}
