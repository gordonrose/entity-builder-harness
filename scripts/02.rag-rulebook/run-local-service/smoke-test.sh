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
  status=$?
  if [ "$status" -ne 0 ] && [ -f "$LOG_FILE" ]; then
    echo "RAG/rulebook service log:" >&2
    cat "$LOG_FILE" >&2
  fi
  if [ -n "${SERVICE_PID:-}" ] && kill -0 "$SERVICE_PID" 2>/dev/null; then
    kill "$SERVICE_PID" 2>/dev/null || true
    wait "$SERVICE_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_DIR"
  exit "$status"
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
        id: "service-smoke-session",
        branch: "chat/service-smoke-session",
        worktree: "/tmp/service-smoke-session",
        latestContextPacketId: "packet.selector-fixture.previous",
        latestContextPacketRoutingSummary: "previous prompt used 02.rag-rulebook discovery context",
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
  if (packet.routing.scope !== "prompt") {
    throw new Error(`unexpected routing scope: ${packet.routing.scope}`);
  }
  if (packet.routing.layer !== "02.rag-rulebook" || packet.routing.mode !== "planning" || packet.routing.workflow !== ".agentic/02.rag-rulebook/workflows/default.md") {
    throw new Error(`prompt-first query should resolve from prompt context: ${JSON.stringify(packet.routing)}`);
  }
  if (packet.request.previous_packet_id !== "packet.selector-fixture.previous") {
    throw new Error("previous packet continuity was not preserved");
  }

  const maliciousHintQuery = await fetch(`${base}/context/query`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      requestText: "Explain the product platform rules for this prompt.",
      session: {
        id: "service-smoke-session",
        branch: "chat/service-smoke-session",
        worktree: "/tmp/service-smoke-session",
        layer: "04.deploy",
        mode: "execution",
        workflow: ".agentic/aws/workflows/execute-approved-aws-change.md",
      },
      focusedPaths: ["docs/harness/architecture/rules/layers/platform.yml"],
      maxChunks: 6,
      format: "full",
    }),
  });
  if (maliciousHintQuery.status !== 200) {
    throw new Error(`malicious-hint query failed with status ${maliciousHintQuery.status}: ${await maliciousHintQuery.text()}`);
  }
  const maliciousHintPacket = await maliciousHintQuery.json();
  const matchedCorpusIds = maliciousHintPacket.matched_corpora.map((corpus) => corpus.corpus_id);
  if (
    maliciousHintPacket.routing.layer !== "03.product" ||
    maliciousHintPacket.routing.mode !== "discovery" ||
    maliciousHintPacket.routing.workflow !== ".agentic/product/workflows/default.md" ||
    maliciousHintPacket.intent.layer !== "03.product" ||
    maliciousHintPacket.intent.mode !== "discovery" ||
    maliciousHintPacket.intent.workflow !== ".agentic/product/workflows/default.md"
  ) {
    throw new Error(`prompt routing did not stay product-scoped under hostile session hint: ${JSON.stringify(maliciousHintPacket.routing)}`);
  }
  if (maliciousHintPacket.provenance.session_context.legacy_routing_hint.trusted !== false) {
    throw new Error("HTTP session routing hints must remain untrusted");
  }
  if (!matchedCorpusIds.includes("corpus.03.product.platform")) {
    throw new Error(`prompt evidence did not select product platform corpus: ${matchedCorpusIds.join(", ")}`);
  }
  if (matchedCorpusIds.includes("corpus.04.deploy")) {
    throw new Error(`untrusted deploy hint leaked into matched corpora: ${matchedCorpusIds.join(", ")}`);
  }

  const invalidWorktree = await fetch(`${base}/context/query`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      requestText: "Explain prompt context",
      session: {
        worktree: "relative/worktree",
      },
      noFocusedPaths: true,
      maxChunks: 6,
      format: "compact",
    }),
  });
  if (invalidWorktree.status !== 400) {
    throw new Error(`invalid worktree should return 400, got ${invalidWorktree.status}`);
  }

  const invalidSummary = await fetch(`${base}/context/query`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      requestText: "Explain prompt context",
      previousRoutingSummary: "bad\u0001summary",
      noFocusedPaths: true,
      maxChunks: 6,
      format: "compact",
    }),
  });
  if (invalidSummary.status !== 400) {
    throw new Error(`invalid continuity summary should return 400, got ${invalidSummary.status}`);
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
NODE

echo "RAG/rulebook local service smoke test passed."
