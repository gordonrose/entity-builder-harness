#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.query-local-context.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test querying a local RAG/rulebook runtime for a validated context packet.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.query-local-context
#       path: scripts/02.rag-rulebook/query-local-context/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

RUNTIME_DIR="$TMP_DIR/runtime"
PACKET_FILE="$TMP_DIR/context-packet.json"

bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir "$RUNTIME_DIR" \
  --pretty >/dev/null

bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "How do I update my harness so we can deploy it behind an MCP server?" \
  --session-layer 01.harness \
  --session-mode planning \
  --session-workflow .agentic/01.harness/workflows/change-harness.md \
  --focused-path .agentic/01.harness/workflows/change-harness.md \
  --pretty > "$PACKET_FILE"

python3 - "$PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert packet["schema"] == "rag-rulebook/context-packet/v1"
assert packet["routing"]["layer"] == "01.harness"
assert packet["routing"]["mode"] == "planning"
assert packet["routing"]["workflow"] == ".agentic/01.harness/workflows/change-harness.md"
assert packet["routing"]["status"] == "ready"
assert any(corpus["corpus_id"] == "corpus.02.rag-rulebook" for corpus in packet["matched_corpora"])
assert any("mcp.server.deployment.architecture" in chunk["chunk_id"] for chunk in packet["selected_chunks"])
assert packet["selector_trace"]["strategy_id"] == "retrieval-selector.v1.hybrid-deterministic-first"
assert packet["selector_trace"]["candidate_counts"]["selected"] == len(packet["selected_chunks"])
assert packet["confidence"]["overall"] > 0
assert packet["citations"]
PY

python3 - "$RUNTIME_DIR/manifest.json" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
manifest = json.loads(path.read_text(encoding="utf-8"))
manifest["fingerprints"]["inputs"]["recognition_sources"]["sha256"] = "0" * 64
path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "How do I update my harness so we can deploy it behind an MCP server?" \
  --session-layer 01.harness \
  --session-mode planning \
  --session-workflow .agentic/01.harness/workflows/change-harness.md \
  --focused-path .agentic/01.harness/workflows/change-harness.md \
  --pretty > "$TMP_DIR/stale-packet.json" 2> "$TMP_DIR/stale-query.err"; then
  echo "ERROR: stale local runtime unexpectedly queried successfully." >&2
  exit 1
fi

grep -q "RAG/rulebook runtime freshness: stale" "$TMP_DIR/stale-query.err" || {
  echo "ERROR: stale runtime failure did not explain stale runtime." >&2
  cat "$TMP_DIR/stale-query.err" >&2
  exit 1
}

echo "Local RAG/rulebook context query smoke test passed."
