// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: rag-rulebook.service.server
//   version: 1
//   status: active
//   layer: 02.rag-rulebook
//   domain: runtime
//   disciplines:
//     - agentic
//     - architecture
//   kind: script
//   purpose: Run the local RAG/rulebook HTTP service MSP skeleton.
//   portability:
//     class: reusable
//     targets:
//       - llm-workbench
//       - entity-builder
//       - design-system-builder
//   effects:
//     - read-only
//     - network
//   used_by:
//     - id: rag-rulebook.service.readme
//       path: .agentic/02.rag-rulebook/service/README.md
//     - id: rag-rulebook.script.run-local-service
//       path: scripts/02.rag-rulebook/run-local-service/script.sh
//     - id: rag-rulebook.script.run-local-service.smoke-test
//       path: scripts/02.rag-rulebook/run-local-service/smoke-test.sh

import { existsSync, readFileSync } from "node:fs";
import { spawn } from "node:child_process";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { queryLocalContext } from "./query-local-context.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(process.env.RAG_REPO_ROOT || path.join(__dirname, "../../.."));
for (const marker of ["package.json", ".agentic/02.rag-rulebook/service", "scripts/02.rag-rulebook"]) {
  if (!existsSync(path.join(rootDir, marker))) {
    throw new Error(`RAG repo root is missing required marker: ${marker}`);
  }
}
const packageJson = JSON.parse(readFileSync(path.join(rootDir, "package.json"), "utf8"));

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);
const ALLOWED_FORMATS = new Set(["full", "compact"]);
const MAX_REQUEST_TEXT_CHARS = 8000;
const MAX_FOCUSED_PATHS = 20;
const MAX_FOCUSED_PATH_CHARS = 240;
const MAX_SESSION_ID_CHARS = 160;
const MAX_SESSION_BRANCH_CHARS = 240;
const MAX_SESSION_WORKTREE_CHARS = 512;
const MAX_PACKET_ID_CHARS = 200;
const MAX_ROUTING_SUMMARY_CHARS = 500;
const SAFE_ID_PATTERN = /^[A-Za-z0-9._:@/-]*$/;
const SAFE_BRANCH_PATTERN = /^[A-Za-z0-9._/@-]*$/;
const SAFE_PACKET_ID_PATTERN = /^[A-Za-z0-9._:-]*$/;

function parseIntegerEnv(name, fallback, { min, max } = {}) {
  const value = Number.parseInt(process.env[name] || String(fallback), 10);
  if (!Number.isInteger(value) || (min !== undefined && value < min) || (max !== undefined && value > max)) {
    throw new Error(`${name} must be an integer${min !== undefined ? ` >= ${min}` : ""}${max !== undefined ? ` <= ${max}` : ""}`);
  }
  return value;
}

const config = {
  host: process.env.HOST || "127.0.0.1",
  port: parseIntegerEnv("PORT", 3000, { min: 1, max: 65535 }),
  rootDir,
  runtimeDir: path.resolve(rootDir, process.env.RAG_RUNTIME_DIR || ".cache/02.rag-rulebook"),
  serviceName: "rag-rulebook-service",
  serviceVersion: process.env.SERVICE_VERSION || packageJson.version || "0.0.0-local",
  commitSha: process.env.GITHUB_SHA || process.env.COMMIT_SHA || "local",
  queryTimeoutMs: parseIntegerEnv("RAG_QUERY_TIMEOUT_MS", 30000, { min: 1000, max: 120000 }),
  allowNonLoopback: process.env.RAG_ALLOW_NON_LOOPBACK === "1",
  authToken: process.env.RAG_SERVICE_TOKEN || "",
  startedAt: new Date().toISOString(),
};

function log(level, message, fields = {}) {
  const record = {
    level,
    message,
    service: config.serviceName,
    time: new Date().toISOString(),
    ...fields,
  };
  const stream = level === "error" ? process.stderr : process.stdout;
  stream.write(`${JSON.stringify(record)}\n`);
}

function sendJson(response, statusCode, body) {
  response.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  response.end(`${JSON.stringify(body)}\n`);
}

async function readJsonBody(request, limitBytes = 128 * 1024) {
  const contentType = String(request.headers["content-type"] || "").toLowerCase();
  if (!contentType.startsWith("application/json")) {
    const error = new Error("content-type must be application/json");
    error.statusCode = 415;
    error.publicMessage = "content-type must be application/json";
    error.publicCode = "unsupported_media_type";
    throw error;
  }

  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > limitBytes) {
      const error = new Error("request body is too large");
      error.statusCode = 413;
      error.publicMessage = "request body is too large";
      error.publicCode = "request_body_too_large";
      throw error;
    }
    chunks.push(chunk);
  }
  if (chunks.length === 0) {
    return {};
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch (error) {
    error.statusCode = 400;
    error.publicMessage = "request body must be valid JSON";
    error.publicCode = "invalid_json";
    throw error;
  }
}

function badRequest(code, message) {
  const error = new Error(message);
  error.statusCode = 400;
  error.publicCode = code;
  error.publicMessage = message;
  return error;
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function runtimeStatus(runtimeDir) {
  const requiredFiles = [
    "manifest.json",
    "rulebook-chunks.json",
    "compiled-retrieval-policy.json",
  ];
  const files = requiredFiles.map((file) => ({
    file,
    present: existsSync(path.join(runtimeDir, file)),
  }));
  return {
    ready: files.every((file) => file.present),
    files,
  };
}

function checkRuntimeFreshness(runtimeDir) {
  return new Promise((resolve) => {
    const child = spawn(
      "bash",
      [
        "scripts/02.rag-rulebook/check-runtime-freshness/script.sh",
        "--runtime-dir",
        runtimeDir,
        "--json",
      ],
      {
        cwd: config.rootDir,
        env: process.env,
        stdio: ["ignore", "pipe", "pipe"],
      },
    );

    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      resolve({
        fresh: false,
        status: "timeout",
        error: "runtime freshness check timed out",
      });
    }, Math.min(config.queryTimeoutMs, 10000));

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", () => {
      clearTimeout(timer);
      resolve({
        fresh: false,
        status: "error",
        error: "runtime freshness check failed to start",
      });
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        resolve({
          fresh: false,
          status: "stale",
          error: stderr.trim() || "runtime freshness check failed",
        });
        return;
      }
      try {
        const report = JSON.parse(stdout);
        resolve({
          fresh: Boolean(report.ok),
          status: report.ok ? "fresh" : "stale",
          counts: report.counts || {},
        });
      } catch {
        resolve({
          fresh: false,
          status: "invalid-report",
          error: "runtime freshness check returned invalid JSON",
        });
      }
    });
  });
}

function stringFromBody(body, camelName, snakeName, fallback) {
  const value = body[camelName] ?? body[snakeName];
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function stringFromSession(body, camelName, snakeName, fallback = "") {
  const session = isPlainObject(body.session) ? body.session : {};
  return stringFromBody(session, camelName, snakeName, fallback);
}

function focusedPathsFromBody(body) {
  const value = body.focusedPaths ?? body.focused_paths;
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item) => typeof item === "string" && item.trim()).map((item) => item.trim());
}

function parseMaxChunks(body) {
  const value = Number.parseInt(String(body.maxChunks ?? body.max_chunks ?? "6"), 10);
  if (!Number.isInteger(value) || value < 3 || value > 12) {
    throw badRequest("invalid_max_chunks", "maxChunks or max_chunks must be an integer between 3 and 12.");
  }
  return value;
}

function validateFocusedPaths(paths) {
  if (paths.length > MAX_FOCUSED_PATHS) {
    throw badRequest("too_many_focused_paths", `focusedPaths may contain at most ${MAX_FOCUSED_PATHS} paths.`);
  }
  for (const focusedPath of paths) {
    if (focusedPath.length > MAX_FOCUSED_PATH_CHARS || focusedPath.includes("\0")) {
      throw badRequest("invalid_focused_path", "focusedPaths entries must be non-empty safe relative paths.");
    }
    if (path.isAbsolute(focusedPath) || focusedPath.split(/[\\/]/).includes("..")) {
      throw badRequest("invalid_focused_path", "focusedPaths entries must be repository-relative paths.");
    }
  }
}

function hasControlChars(value) {
  return /[\u0000-\u001f\u007f]/u.test(value);
}

function validateOptionalString(value, { fieldName, maxLength, pattern } = {}) {
  if (!value) return "";
  if (value.length > maxLength || hasControlChars(value)) {
    throw badRequest("invalid_session_context", `${fieldName} is too long or contains control characters.`);
  }
  if (pattern && !pattern.test(value)) {
    throw badRequest("invalid_session_context", `${fieldName} contains unsupported characters.`);
  }
  return value;
}

function validateSessionWorktree(value) {
  if (!value) return "";
  validateOptionalString(value, {
    fieldName: "session worktree",
    maxLength: MAX_SESSION_WORKTREE_CHARS,
  });
  if (!path.isAbsolute(value) || value.split(/[\\/]/).includes("..")) {
    throw badRequest("invalid_session_context", "session worktree must be an absolute path without parent traversal.");
  }
  return value;
}

function validateSessionContextFields(fields) {
  return {
    sessionId: validateOptionalString(fields.sessionId, {
      fieldName: "session id",
      maxLength: MAX_SESSION_ID_CHARS,
      pattern: SAFE_ID_PATTERN,
    }),
    sessionBranch: validateOptionalString(fields.sessionBranch, {
      fieldName: "session branch",
      maxLength: MAX_SESSION_BRANCH_CHARS,
      pattern: SAFE_BRANCH_PATTERN,
    }),
    sessionWorktree: validateSessionWorktree(fields.sessionWorktree),
    sessionLayer: validateOptionalString(fields.sessionLayer, {
      fieldName: "session layer",
      maxLength: 80,
      pattern: SAFE_ID_PATTERN,
    }),
    sessionMode: validateOptionalString(fields.sessionMode, {
      fieldName: "session mode",
      maxLength: 80,
      pattern: SAFE_ID_PATTERN,
    }),
    sessionWorkflow: validateOptionalString(fields.sessionWorkflow, {
      fieldName: "session workflow",
      maxLength: 300,
      pattern: SAFE_BRANCH_PATTERN,
    }),
    previousPacketId: validateOptionalString(fields.previousPacketId, {
      fieldName: "previous packet id",
      maxLength: MAX_PACKET_ID_CHARS,
      pattern: SAFE_PACKET_ID_PATTERN,
    }),
    previousRoutingSummary: validateOptionalString(fields.previousRoutingSummary, {
      fieldName: "previous routing summary",
      maxLength: MAX_ROUTING_SUMMARY_CHARS,
    }),
  };
}

function validateContextQueryBody(body) {
  if (!isPlainObject(body)) {
    throw badRequest("invalid_request_body", "request body must be a JSON object.");
  }
  const requestText = stringFromBody(body, "requestText", "request_text", "");
  if (!requestText) {
    throw badRequest("missing_request_text", "requestText or request_text is required.");
  }
  if (requestText.length > MAX_REQUEST_TEXT_CHARS) {
    throw badRequest("request_text_too_long", `requestText may contain at most ${MAX_REQUEST_TEXT_CHARS} characters.`);
  }

  const focusedPaths = focusedPathsFromBody(body);
  validateFocusedPaths(focusedPaths);

  const format = stringFromBody(body, "format", "format", "compact");
  if (!ALLOWED_FORMATS.has(format)) {
    throw badRequest("invalid_format", "format must be full or compact.");
  }

  return {
    requestText,
    focusedPaths,
    maxChunks: parseMaxChunks(body),
    format,
  };
}

function checkAuthorization(request, routePath) {
  if (!config.authToken || routePath !== "/context/query") {
    return;
  }
  const expected = `Bearer ${config.authToken}`;
  if (request.headers.authorization !== expected) {
    const error = new Error("authorization required");
    error.statusCode = 401;
    error.publicCode = "unauthorized";
    error.publicMessage = "authorization required";
    throw error;
  }
}

async function handleHealth() {
  const runtime = runtimeStatus(config.runtimeDir);
  const freshness = runtime.ready
    ? await checkRuntimeFreshness(config.runtimeDir)
    : { fresh: false, status: "missing-runtime" };
  const ready = runtime.ready && freshness.fresh;
  return {
    statusCode: ready ? 200 : 503,
    body: {
      status: ready ? "ready" : "not-ready",
      service: config.serviceName,
      runtime,
      freshness,
    },
  };
}

async function handleVersion() {
  return {
    body: {
      service: config.serviceName,
      version: config.serviceVersion,
      commit: config.commitSha,
      started_at: config.startedAt,
      runtime: runtimeStatus(config.runtimeDir),
    },
  };
}

async function handleContextQuery({ body }) {
  const validated = validateContextQueryBody(body);
  const sessionContext = validateSessionContextFields({
    sessionId: stringFromBody(body, "sessionId", "session_id", stringFromSession(body, "id", "id")),
    sessionBranch: stringFromBody(body, "sessionBranch", "session_branch", stringFromSession(body, "branch", "branch")),
    sessionWorktree: stringFromBody(body, "sessionWorktree", "session_worktree", stringFromSession(body, "worktree", "worktree")),
    sessionLayer: stringFromBody(body, "sessionLayer", "session_layer", stringFromSession(body, "layer", "layer")),
    sessionMode: stringFromBody(body, "sessionMode", "session_mode", stringFromSession(body, "mode", "mode")),
    sessionWorkflow: stringFromBody(
      body,
      "sessionWorkflow",
      "session_workflow",
      stringFromSession(body, "workflow", "workflow"),
    ),
    previousPacketId: stringFromBody(
      body,
      "previousPacketId",
      "previous_packet_id",
      stringFromSession(body, "latestContextPacketId", "latest_context_packet_id"),
    ),
    previousRoutingSummary: stringFromBody(
      body,
      "previousRoutingSummary",
      "previous_routing_summary",
      stringFromSession(body, "latestContextPacketRoutingSummary", "latest_context_packet_routing_summary"),
    ),
  });

  const result = await queryLocalContext({
    rootDir: config.rootDir,
    runtimeDir: config.runtimeDir,
    requestText: validated.requestText,
    ...sessionContext,
    focusedPaths: validated.focusedPaths,
    noFocusedPaths: Boolean(body.noFocusedPaths ?? body.no_focused_paths ?? validated.focusedPaths.length === 0),
    maxChunks: validated.maxChunks,
    format: validated.format,
    timeoutMs: config.queryTimeoutMs,
  });

  return {
    statusCode: 200,
    body: result,
  };
}

function createRouter() {
  const routes = new Map([
    ["GET /health", handleHealth],
    ["GET /version", handleVersion],
    ["POST /context/query", handleContextQuery],
  ]);
  return {
    match: (method, routePath) => routes.get(`${method.toUpperCase()} ${routePath}`),
  };
}

const router = createRouter();

const server = http.createServer(async (request, response) => {
  const requestStartedAt = Date.now();
  const url = new URL(request.url || "/", `http://${request.headers.host || "localhost"}`);
  const handler = router.match(request.method || "GET", url.pathname);

  if (!handler) {
    sendJson(response, 404, {
      error: {
        code: "not_found",
        message: "route not found",
      },
    });
    return;
  }

  try {
    checkAuthorization(request, url.pathname);
    const body = request.method === "POST" ? await readJsonBody(request) : {};
    const result = await handler({ request, body, query: Object.fromEntries(url.searchParams.entries()) });
    sendJson(response, result.statusCode || 200, result.body || {});
    log("info", "request handled", {
      method: request.method,
      path: url.pathname,
      statusCode: result.statusCode || 200,
      durationMs: Date.now() - requestStartedAt,
    });
  } catch (error) {
    const statusCode = error.statusCode || 500;
    sendJson(response, statusCode, {
      error: {
        code: error.publicCode || (statusCode >= 500 ? "internal_error" : "bad_request"),
        message: error.publicMessage || (statusCode >= 500 ? "request failed" : error.message || "request failed"),
      },
    });
    log("error", "request failed", {
      method: request.method,
      path: url.pathname,
      statusCode,
      durationMs: Date.now() - requestStartedAt,
      error: error.stack || String(error),
    });
  }
});

function shutdown(signal) {
  log("info", "shutdown requested", { signal });
  server.close((error) => {
    if (error) {
      log("error", "shutdown failed", { error: error.stack || String(error) });
      process.exit(1);
    }
    log("info", "shutdown complete");
    process.exit(0);
  });
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

if (!LOOPBACK_HOSTS.has(config.host) && !config.allowNonLoopback) {
  throw new Error("non-loopback binds require RAG_ALLOW_NON_LOOPBACK=1 and RAG_SERVICE_TOKEN");
}

if (!LOOPBACK_HOSTS.has(config.host) && !config.authToken) {
  throw new Error("non-loopback binds require RAG_SERVICE_TOKEN");
}

server.listen(config.port, config.host, () => {
  log("info", "service started", {
    host: config.host,
    port: config.port,
    runtimeReady: runtimeStatus(config.runtimeDir).ready,
    authRequired: Boolean(config.authToken),
  });
});
