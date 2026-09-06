#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.script.build-platform-shell-image.verify-runtime-payload
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - agentic
//   - sre
//   kind: script
//   purpose: Prove the compiled platform shell payload starts with its generated package shims rather than workspace TypeScript sources.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: package.script.platform-server-image-runtime-check
//     path: package.json

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, renameSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const runtimeRoot = join(repositoryRoot, ".cache", "platform-shell-image-build");
const entrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-server.main.js");
const workspacePackageScope = join(repositoryRoot, "node_modules", "@kanbien");
const hiddenWorkspaceRoot = mkdtempSync(join(tmpdir(), "platform-shell-runtime-payload-"));
const hiddenWorkspaceScope = join(hiddenWorkspaceRoot, "@kanbien");

const requiredPayloadFiles = [
  entrypoint,
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-auth-cognito", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-runtime-ecs-fargate", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-security-dynamodb-rate-limiter", "index.js"),
];

for (const filePath of requiredPayloadFiles) {
  if (!existsSync(filePath)) {
    throw new Error(`Platform shell runtime payload is incomplete: ${filePath}`);
  }
}

if (!existsSync(workspacePackageScope)) {
  throw new Error("Expected local workspace package links are unavailable for runtime-payload isolation.");
}

renameSync(workspacePackageScope, hiddenWorkspaceScope);

try {
  const result = spawnSync(process.execPath, [entrypoint], {
    cwd: repositoryRoot,
    env: {
      ...process.env,
      HOST: "127.0.0.1",
      PORT: "39455",
      PLATFORM_SERVER_EXIT_AFTER_START: "1",
      PLATFORM_DEPLOYMENT_EXPOSURE: "public",
      PLATFORM_AUTH_PROVIDER: "cognito",
      PLATFORM_AUTH_COGNITO_REGION: "eu-west-1",
      PLATFORM_AUTH_COGNITO_USER_POOL_ID: "eu-west-1_EQaXioA1n",
      PLATFORM_AUTH_COGNITO_APP_CLIENT_ID: "4n7kuqstbvb97ur3btbur8afjt",
      PLATFORM_AUTHZ_SCOPE_PERMISSIONS: '{"platform-shell/smoke.read":["platform-smoke.smoke:read"]}',
      PLATFORM_CORS_ALLOWLIST: "https://staging.platform.kanbien.com",
      PLATFORM_HEALTH_LIVEZ_EXPOSURE: "public",
      PLATFORM_HEALTH_READYZ_EXPOSURE: "authenticated",
      PLATFORM_RATE_LIMIT_PROVIDER: "dynamodb",
      PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "kanbien-staging-platform-shell-rate-limits",
      PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "eu-west-1",
      PLATFORM_RATE_LIMIT_LIMIT: "120",
      PLATFORM_RATE_LIMIT_WINDOW_MS: "60000",
      PLATFORM_TRUSTED_INGRESS_MODE: "alb-security-group-only",
      PLATFORM_SERVER_MAX_REQUEST_BODY_BYTES: "1048576",
      PLATFORM_SERVER_MAX_HEADER_BYTES: "16384",
      PLATFORM_SERVER_MAX_HEADERS_COUNT: "100",
      PLATFORM_SERVER_HEADERS_TIMEOUT_MS: "10000",
      PLATFORM_SERVER_REQUEST_TIMEOUT_MS: "30000",
      PLATFORM_SERVER_KEEP_ALIVE_TIMEOUT_MS: "5000",
      PLATFORM_SERVER_HANDLER_TIMEOUT_MS: "30000",
      PLATFORM_SERVER_SHUTDOWN_DRAIN_TIMEOUT_MS: "30000",
      PLATFORM_SERVER_MAX_CONCURRENT_REQUESTS: "100",
      PLATFORM_SERVER_MAX_REQUESTS_PER_SOCKET: "1000",
      PLATFORM_SMOKE_APP_NAME: "Kanbien Platform Smoke",
    },
    stdio: "inherit",
  });

  if (result.status !== 0) {
    throw new Error(`Compiled platform shell runtime failed with exit code ${String(result.status)}.`);
  }
} finally {
  renameSync(hiddenWorkspaceScope, workspacePackageScope);
  rmSync(hiddenWorkspaceRoot, { force: true, recursive: true });
}

console.log("Platform shell compiled runtime payload check passed.");
