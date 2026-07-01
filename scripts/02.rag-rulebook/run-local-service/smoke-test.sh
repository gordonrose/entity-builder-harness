#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.run-local-service.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the local RAG/rulebook HTTP service MSP skeleton.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#     - network
#   used_by:
#     - id: rag-rulebook.script.run-local-service
#       path: scripts/02.rag-rulebook/run-local-service/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

TMP_DIR="$(mktemp -d)"
RUNTIME_DIR="$TMP_DIR/runtime"
PORT="${RAG_SERVICE_SMOKE_PORT:-39451}"
LOG_FILE="$TMP_DIR/service.log"

cleanup() {
  if [ -n "${SERVICE_PID:-}" ] && kill -0 "$SERVICE_PID" 2>/dev/null; then
    kill "$SERVICE_PID" 2>/dev/null || true
    wait "$SERVICE_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir "$RUNTIME_DIR" \
  --pretty >/dev/null

HOST=127.0.0.1 PORT="$PORT" RAG_RUNTIME_DIR="$RUNTIME_DIR" \
  node .agentic/02.rag-rulebook/service/server.mjs >"$LOG_FILE" 2>&1 &
SERVICE_PID="$!"

node - "$PORT" <<'NODE'
const port = process.argv[2];
const base = `http://127.0.0.1:${port}`;

async function waitForHealth() {
  const deadline = Date.now() + 10000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${base}/health`);
      if (response.status === 200) {
        const body = await response.json();
        if (body.status === "ready") return;
      }
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw lastError || new Error("service did not become healthy");
}

async function main() {
  await waitForHealth();

  const version = await fetch(`${base}/version`).then((response) => response.json());
  if (version.service !== "rag-rulebook-service") {
    throw new Error("unexpected service version response");
  }

  const query = await fetch(`${base}/context/query`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      requestText: "Explain how the RAG rulebook service should answer a planning question.",
      session: {
        layer: "02.rag-rulebook",
        mode: "discovery",
        workflow: ".agentic/02.rag-rulebook/workflows/default.md",
      },
      noFocusedPaths: true,
      maxChunks: 6,
      format: "compact",
    }),
  });

  if (query.status !== 200) {
    throw new Error(`query failed with status ${query.status}: ${await query.text()}`);
  }
  const packet = await query.json();
  if (packet.schema !== "rag-rulebook/context-packet-compact/v1") {
    throw new Error(`unexpected packet schema: ${packet.schema}`);
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
NODE

echo "RAG/rulebook local service smoke test passed."
