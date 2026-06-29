// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: rag-rulebook.service.query-local-context
//   version: 1
//   status: active
//   layer: 02.rag-rulebook
//   domain: runtime
//   disciplines:
//     - agentic
//     - architecture
//   kind: script
//   purpose: Adapt the local context-packet query script for the RAG/rulebook HTTP service.
//   portability:
//     class: reusable
//     targets:
//       - llm-workbench
//       - entity-builder
//       - design-system-builder
//   effects:
//     - read-only
//   used_by:
//     - id: rag-rulebook.service.server
//       path: .agentic/02.rag-rulebook/service/server.mjs

import { spawn } from "node:child_process";

function commandArgs(input) {
  const args = [
    "scripts/02.rag-rulebook/query-local-context/script.sh",
    "--runtime-dir",
    input.runtimeDir,
    "--request-text",
    input.requestText,
    "--session-layer",
    input.sessionLayer,
    "--session-mode",
    input.sessionMode,
    "--session-workflow",
    input.sessionWorkflow,
    "--max-chunks",
    String(input.maxChunks),
    "--format",
    input.format,
    "--pretty",
  ];

  if (input.noFocusedPaths) {
    args.push("--no-focused-paths");
  } else {
    for (const focusedPath of input.focusedPaths) {
      args.push("--focused-path", focusedPath);
    }
  }

  return args;
}

function parseOutput(stdout) {
  try {
    return JSON.parse(stdout);
  } catch (error) {
    error.publicMessage = "context query returned invalid JSON";
    throw error;
  }
}

export function queryLocalContext(input) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const child = spawn("bash", commandArgs(input), {
      cwd: input.rootDir,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    let killTimer;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill("SIGTERM");
      const error = new Error("context query timed out");
      error.statusCode = 504;
      error.publicCode = "context_query_timeout";
      error.publicMessage = "context query timed out";
      killTimer = setTimeout(() => {
        child.kill("SIGKILL");
      }, 2000);
      reject(error);
    }, input.timeoutMs);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });

    child.on("error", (error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      clearTimeout(killTimer);
      error.statusCode = 500;
      error.publicCode = "context_query_start_failed";
      error.publicMessage = "context query failed to start";
      reject(error);
    });

    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      clearTimeout(killTimer);
      if (code !== 0) {
        const error = new Error(stderr.trim() || `context query failed with exit code ${code}`);
        error.statusCode = stderr.includes("runtime") ? 409 : 502;
        error.publicCode = error.statusCode === 409 ? "runtime_not_fresh" : "context_query_failed";
        error.publicMessage = error.statusCode === 409
          ? "runtime cache is stale or missing"
          : "context query failed";
        reject(error);
        return;
      }
      resolve(parseOutput(stdout));
    });
  });
}
