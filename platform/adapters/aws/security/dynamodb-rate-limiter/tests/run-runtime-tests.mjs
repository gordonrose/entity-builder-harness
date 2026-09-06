import { spawnSync } from "node:child_process";

const result = spawnSync(
  process.execPath,
  [".cache/platform-adapter-aws-security-dynamodb-rate-limiter-runtime/platform/adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-runtime.test.js"],
  { stdio: "inherit" },
);

process.exitCode = result.status ?? 1;
