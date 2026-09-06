import { spawnSync } from "node:child_process";

const result = spawnSync(
  process.execPath,
  [".cache/platform-adapter-aws-runtime-ecs-fargate-runtime/platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-runtime.test.js"],
  { stdio: "inherit" },
);

process.exitCode = result.status ?? 1;
