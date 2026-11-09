import { equal } from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { verifyRuntimeRunner } from "../../../../../../../../packages/core/tests/test-infrastructure/helpers/runtime-runner-fixture";

verifyRuntimeRunner("platform/adapters/aws/observability/cloudwatch");
runnerDispatchProof();

function runnerDispatchProof(): void {
  const runner = resolve("platform/adapters/aws/observability/cloudwatch/tests/run-runtime-tests.mjs");
  const root = mkdtempSync(join(tmpdir(), "kanbien-metric-lifecycle-dispatch-"));
  const directory = join(root, "platform/adapters/aws/observability/cloudwatch/tests"); mkdirSync(directory, { recursive: true });
  try {
    writeFileSync(join(directory, "cloudwatch-otel-adapter-runtime.test.ts"), "export {};\n");
    writeFileSync(join(directory, "cloudwatch-otel-lifecycle-runtime.test.ts"), "export {};\n");
    for (const [first, second, status, output] of [[0, 0, 0, "first\nsecond\n"], [7, 0, 7, "first\n"], [0, 9, 9, "first\nsecond\n"]] as const) {
      writeFileSync(join(directory, "cloudwatch-otel-adapter-runtime.test.js"), `console.log("first"); process.exitCode = ${first};\n`);
      writeFileSync(join(directory, "cloudwatch-otel-lifecycle-runtime.test.js"), `console.log("second"); process.exitCode = ${second};\n`);
      const child = spawnSync(process.execPath, [runner], {
        cwd: root, env: { ...process.env, KANBIEN_CLOUDWATCH_OTEL_RUNTIME_ROOT: root }, encoding: "utf8",
      });
      equal(child.status, status); equal(child.stdout, output); equal(child.stderr, "");
    }
  } finally { rmSync(root, { recursive: true, force: true }); }
}
