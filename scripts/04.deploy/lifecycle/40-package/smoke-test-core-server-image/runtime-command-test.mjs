#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-image-runtime-command
//   version: 1
//   status: draft
//   created_on: "2026-10-20"
//   updated_on: "2026-10-20"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: script
//   purpose: Prove the exact generated core-server image command remains listening and serves its safe local operations.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - network
//   - writes-files
//   used_by:
//   - id: deploy.test.core-server-image-payload-fixture
//     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/payload-fixture-test.sh

import { spawn } from "node:child_process";
import { createServer } from "node:net";
import { resolve } from "node:path";

const [compiledRoot] = process.argv.slice(2);
if (typeof compiledRoot !== "string" || compiledRoot.length === 0) {
  throw new Error("Usage: runtime-command-test.mjs <compiled-payload-directory>");
}

const port = await reservePort();
const sourceCommitSha = "runtime-command-proof-2026.10.20";
const child = spawn(process.execPath, ["kanbien-core-server.main.js"], {
  cwd: resolve(compiledRoot),
  env: {
    ...process.env,
    HOST: "127.0.0.1",
    PORT: String(port),
    PLATFORM_SOURCE_COMMIT_SHA: sourceCommitSha,
  },
  stdio: "ignore",
});

try {
  await waitFor("/livez", (response, body) => response.status === 200 && body.status === "live");
  await waitFor("/readyz", (response, body) => response.status === 200 && body.status === "ready");
  await waitFor(
    "/internal/release-verification",
    (response, body) => response.status === 200 && body?.release?.sourceCommitSha === sourceCommitSha,
  );
  if (child.exitCode !== null || child.signalCode !== null) {
    throw new Error("Generated core-server command exited before safe operations were served.");
  }
} finally {
  child.kill("SIGTERM");
  await waitForExit(child);
}

console.log("Core-server generated runtime command proof passed.");

async function reservePort() {
  const server = createServer();
  await new Promise((resolveListen, rejectListen) => {
    server.once("error", rejectListen);
    server.listen(0, "127.0.0.1", resolveListen);
  });
  const address = server.address();
  if (address === null || typeof address === "string") {
    server.close();
    throw new Error("Could not reserve a local test port.");
  }
  await new Promise((resolveClose, rejectClose) => server.close((error) => error ? rejectClose(error) : resolveClose()));
  return address.port;
}

async function waitFor(path, accept) {
  const deadline = Date.now() + 20000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}${path}`);
      const body = await response.json();
      if (accept(response, body)) return;
      lastError = new Error("Generated command returned an unexpected safe response.");
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 100));
  }
  throw lastError || new Error("Generated core-server command did not become reachable.");
}

async function waitForExit(process) {
  if (process.exitCode !== null || process.signalCode !== null) return;
  await Promise.race([
    new Promise((resolveExit) => process.once("exit", resolveExit)),
    new Promise((_, rejectTimeout) => setTimeout(() => rejectTimeout(new Error("Generated core-server command did not stop.")), 5000)),
  ]);
}
