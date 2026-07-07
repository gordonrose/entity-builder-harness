#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.query-context.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#     - sre
#   kind: script
#   purpose: Smoke test the RAG-owned hosted/local context provider boundary without exposing secrets.
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
#     - id: rag-rulebook.script.query-context
#       path: scripts/02.rag-rulebook/query-context/script.sh

TMP_DIR="$(mktemp -d)"
SERVER_PID=""
trap 'if [ -n "$SERVER_PID" ]; then kill "$SERVER_PID" 2>/dev/null || true; fi; rm -rf "$TMP_DIR"' EXIT

TOKEN="query-context-smoke-token"
PORT_FILE="$TMP_DIR/port"
SERVER_ERR="$TMP_DIR/server.err"
SERVER_SCRIPT="$TMP_DIR/fake-hosted-rag.cjs"

cat > "$SERVER_SCRIPT" <<'NODE'
const fs = require("fs");
const http = require("http");

const [portFile, expectedToken] = process.argv.slice(2);

const server = http.createServer((request, response) => {
  if (request.method !== "POST" || request.url !== "/context/query") {
    response.writeHead(404, { "content-type": "application/json" });
    response.end(JSON.stringify({ error: { code: "not_found" } }));
    return;
  }
  let raw = "";
  request.setEncoding("utf8");
  request.on("data", (chunk) => {
    raw += chunk;
  });
  request.on("end", () => {
    if (request.headers.authorization !== `Bearer ${expectedToken}`) {
      response.writeHead(401, { "content-type": "application/json" });
      response.end(JSON.stringify({ error: { code: "unauthorized", message: "authorization required" } }));
      return;
    }
    const body = JSON.parse(raw || "{}");
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({
      schema: body.format === "full" ? "rag-rulebook/context-packet/v1" : "rag-rulebook/context-packet-compact/v1",
      packet_id: "packet.query-context.smoke",
      request: {
        raw_text: body.requestText,
        focused_paths: body.focusedPaths || []
      },
      routing: {
        status: "ready",
        layer: "02.rag-rulebook",
        mode: "discovery"
      },
      selected_chunks: [
        {
          rank: 1,
          chunk_id: "chunk.query-context.smoke",
          corpus_id: "corpus.02.rag-rulebook",
          artifact_id: "artifact.hosted-context-provider-contract",
          content: "Hosted context provider smoke response."
        }
      ],
      citations: [],
      gaps: []
    }));
  });
});

server.listen(0, "127.0.0.1", () => {
  fs.writeFileSync(portFile, String(server.address().port));
});
NODE
node "$SERVER_SCRIPT" "$PORT_FILE" "$TOKEN" 2> "$SERVER_ERR" &
SERVER_PID="$!"

for _ in $(seq 1 50); do
  if [ -s "$PORT_FILE" ]; then
    break
  fi
  sleep 0.1
done
if [ ! -s "$PORT_FILE" ]; then
  echo "ERROR: fake hosted RAG server did not start." >&2
  cat "$SERVER_ERR" >&2
  exit 1
fi
BASE_URL="http://127.0.0.1:$(cat "$PORT_FILE")"

GOOD_CONFIG="$TMP_DIR/good.rag.env"
MISSING_AUTH_CONFIG="$TMP_DIR/missing-auth.rag.env"
BAD_AUTH_CONFIG="$TMP_DIR/bad-auth.rag.env"
AUTO_BLOCKED_CONFIG="$TMP_DIR/auto-blocked.rag.env"
BAD_PERM_CONFIG="$TMP_DIR/bad-perm.rag.env"

cat > "$GOOD_CONFIG" <<EOF
RAG_RULEBOOK_PROVIDER=hosted
RAG_RULEBOOK_BASE_URL=$BASE_URL
RAG_RULEBOOK_AUTH_MODE=bearer
RAG_RULEBOOK_TOKEN=$TOKEN
EOF
chmod 600 "$GOOD_CONFIG"

cat > "$MISSING_AUTH_CONFIG" <<EOF
RAG_RULEBOOK_PROVIDER=hosted
RAG_RULEBOOK_BASE_URL=$BASE_URL
RAG_RULEBOOK_AUTH_MODE=bearer
EOF
chmod 600 "$MISSING_AUTH_CONFIG"

cat > "$BAD_AUTH_CONFIG" <<EOF
RAG_RULEBOOK_PROVIDER=hosted
RAG_RULEBOOK_BASE_URL=$BASE_URL
RAG_RULEBOOK_AUTH_MODE=bearer
RAG_RULEBOOK_TOKEN=wrong-token-value
EOF
chmod 600 "$BAD_AUTH_CONFIG"

cat > "$AUTO_BLOCKED_CONFIG" <<EOF
RAG_RULEBOOK_PROVIDER=auto
RAG_RULEBOOK_BASE_URL=$BASE_URL
RAG_RULEBOOK_AUTH_MODE=bearer
EOF
chmod 600 "$AUTO_BLOCKED_CONFIG"

cat > "$BAD_PERM_CONFIG" <<EOF
RAG_RULEBOOK_PROVIDER=hosted
RAG_RULEBOOK_BASE_URL=$BASE_URL
RAG_RULEBOOK_AUTH_MODE=bearer
RAG_RULEBOOK_TOKEN=$TOKEN
EOF
chmod 644 "$BAD_PERM_CONFIG"

SUCCESS_JSON="$TMP_DIR/success.json"
SUCCESS_ERR="$TMP_DIR/success.err"
if ! bash scripts/02.rag-rulebook/query-context/script.sh \
  --config "$GOOD_CONFIG" \
  --provider hosted \
  --request-text "Smoke test the hosted context provider contract." \
  --focused-path docs/02.rag-rulebook/rules/concerns/hosted-context-provider-contract.yml \
  --format compact \
  --pretty > "$SUCCESS_JSON" 2> "$SUCCESS_ERR"; then
  echo "ERROR: hosted provider success case failed." >&2
  cat "$SUCCESS_ERR" >&2
  exit 1
fi

python3 - "$SUCCESS_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert packet["schema"] == "rag-rulebook/context-packet-compact/v1"
assert packet["routing"]["status"] == "ready"
assert packet["selected_chunks"][0]["corpus_id"] == "corpus.02.rag-rulebook"
assert packet["request"]["focused_paths"] == [
    "docs/02.rag-rulebook/rules/concerns/hosted-context-provider-contract.yml"
]
PY

if grep -R "$TOKEN" "$SUCCESS_JSON" "$SUCCESS_ERR" >/dev/null; then
  echo "ERROR: hosted success leaked the bearer token." >&2
  exit 1
fi

if bash scripts/02.rag-rulebook/query-context/script.sh \
  --config "$MISSING_AUTH_CONFIG" \
  --provider hosted \
  --request-text "Missing token should fail closed." \
  > "$TMP_DIR/missing-auth.out" 2> "$TMP_DIR/missing-auth.err"; then
  echo "ERROR: hosted provider without auth unexpectedly succeeded." >&2
  exit 1
fi
grep -q "gap.rag-rulebook.hosted-context-provider-auth-missing" "$TMP_DIR/missing-auth.err" || {
  echo "ERROR: missing auth failure did not emit the expected gap." >&2
  cat "$TMP_DIR/missing-auth.err" >&2
  exit 1
}

if bash scripts/02.rag-rulebook/query-context/script.sh \
  --config "$BAD_AUTH_CONFIG" \
  --provider hosted \
  --request-text "Rejected token should fail closed." \
  > "$TMP_DIR/bad-auth.out" 2> "$TMP_DIR/bad-auth.err"; then
  echo "ERROR: hosted provider with rejected auth unexpectedly succeeded." >&2
  exit 1
fi
grep -q "gap.rag-rulebook.hosted-context-provider-auth-rejected" "$TMP_DIR/bad-auth.err" || {
  echo "ERROR: rejected auth failure did not emit the expected gap." >&2
  cat "$TMP_DIR/bad-auth.err" >&2
  exit 1
}
if grep -R "wrong-token-value" "$TMP_DIR/bad-auth.out" "$TMP_DIR/bad-auth.err" >/dev/null; then
  echo "ERROR: rejected auth leaked the bearer token." >&2
  exit 1
fi

if bash scripts/02.rag-rulebook/query-context/script.sh \
  --config "$AUTO_BLOCKED_CONFIG" \
  --provider auto \
  --request-text "Auto mode without governed fallback should fail." \
  > "$TMP_DIR/auto-blocked.out" 2> "$TMP_DIR/auto-blocked.err"; then
  echo "ERROR: auto provider without auth/fallback unexpectedly succeeded." >&2
  exit 1
fi
grep -q "gap.rag-rulebook.hosted-context-provider-local-fallback-blocked" "$TMP_DIR/auto-blocked.err" || {
  echo "ERROR: blocked fallback did not emit the expected gap." >&2
  cat "$TMP_DIR/auto-blocked.err" >&2
  exit 1
}

if bash scripts/02.rag-rulebook/query-context/script.sh \
  --config "$BAD_PERM_CONFIG" \
  --provider hosted \
  --request-text "Readable config should fail." \
  > "$TMP_DIR/bad-perm.out" 2> "$TMP_DIR/bad-perm.err"; then
  echo "ERROR: group/world-readable config unexpectedly succeeded." >&2
  exit 1
fi
grep -q "group/other-readable" "$TMP_DIR/bad-perm.err" || {
  echo "ERROR: bad permission failure did not explain the config mode issue." >&2
  cat "$TMP_DIR/bad-perm.err" >&2
  exit 1
}

echo "RAG/rulebook context provider smoke test passed."
