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
COMPACT_PACKET_FILE="$TMP_DIR/context-packet.compact.json"
PROMPT_FIRST_PACKET_FILE="$TMP_DIR/context-packet.prompt-first.json"
SIDE_EFFECT_PACKET_FILE="$TMP_DIR/context-packet.side-effect.json"
MALICIOUS_HINT_PACKET_FILE="$TMP_DIR/context-packet.malicious-hint.json"
ROUTE_COHERENCE_PACKET_FILE="$TMP_DIR/context-packet.route-coherence.json"

bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir "$RUNTIME_DIR" \
  --pretty >/dev/null

bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "How do I update my harness so we can deploy it behind an MCP server?" \
  --session-id chat-trusted-session \
  --session-branch chat/trusted-session \
  --session-worktree /tmp/chat-trusted-session \
  --session-layer 01.harness \
  --session-mode planning \
  --session-workflow .agentic/01.harness/workflows/change-harness.md \
  --trust-session-routing \
  --focused-path .agentic/01.harness/workflows/change-harness.md \
  --pretty > "$PACKET_FILE"

bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "How do I update my harness so we can deploy it behind an MCP server?" \
  --session-id chat-trusted-session \
  --session-branch chat/trusted-session \
  --session-worktree /tmp/chat-trusted-session \
  --session-layer 01.harness \
  --session-mode planning \
  --session-workflow .agentic/01.harness/workflows/change-harness.md \
  --trust-session-routing \
  --focused-path .agentic/01.harness/workflows/change-harness.md \
  --format compact \
  --pretty > "$COMPACT_PACKET_FILE"

bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "Explain the corpus.03.product.platform rules using the exact product platform corpus." \
  --session-id chat-test-session \
  --session-branch chat/test-session \
  --session-worktree /tmp/chat-test-session \
  --previous-packet-id packet.selector-fixture.previous \
  --previous-routing-summary "previous prompt used 02.rag-rulebook planning context" \
  --focused-path docs/harness/architecture/rules/layers/platform.yml \
  --pretty > "$PROMPT_FIRST_PACKET_FILE"

bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "Explain the product platform rules for this prompt." \
  --session-id chat-test-session \
  --session-branch chat/test-session \
  --session-worktree /tmp/chat-test-session \
  --session-layer 04.deploy \
  --session-mode execution \
  --session-workflow .agentic/aws/workflows/execute-approved-aws-change.md \
  --focused-path docs/harness/architecture/rules/layers/platform.yml \
  --pretty > "$MALICIOUS_HINT_PACKET_FILE"

bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "Explain corpus.03.product.platform for this prompt." \
  --focused-path .agentic/02.rag-rulebook/workflows/default.md \
  --pretty > "$ROUTE_COHERENCE_PACKET_FILE"

bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "Commit this" \
  --no-focused-paths \
  --pretty > "$SIDE_EFFECT_PACKET_FILE"

python3 - "$PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert packet["schema"] == "rag-rulebook/context-packet/v1"
assert packet["routing"]["layer"] == "01.harness"
assert packet["routing"]["mode"] == "discovery"
assert packet["routing"]["workflow"] == ".agentic/01.harness/workflows/change-harness.md"
assert packet["routing"]["status"] == "ready"
assert any(corpus["corpus_id"] == "corpus.02.rag-rulebook" for corpus in packet["matched_corpora"])
assert any("mcp.server.deployment.architecture" in chunk["chunk_id"] for chunk in packet["selected_chunks"])
assert packet["selector_trace"]["strategy_id"] == "retrieval-selector.v1.hybrid-deterministic-first"
assert packet["selector_trace"]["candidate_counts"]["selected"] == len(packet["selected_chunks"])
assert packet["confidence"]["overall"] > 0
assert packet["citations"]
PY

python3 - "$PACKET_FILE" "$COMPACT_PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

full_path = Path(sys.argv[1])
compact_path = Path(sys.argv[2])
full_packet = json.loads(full_path.read_text(encoding="utf-8"))
compact_packet = json.loads(compact_path.read_text(encoding="utf-8"))
assert compact_packet["schema"] == "rag-rulebook/context-packet-compact/v1"
assert compact_packet["source_schema"] == full_packet["schema"]
assert compact_packet["packet_id"] == full_packet["packet_id"]
assert compact_packet["request"]["raw_text"] == full_packet["request"]["raw_text"]
assert "recognition_source_matches" not in compact_packet["request"]
assert len(compact_packet["selected_chunks"]) == len(full_packet["selected_chunks"])
assert compact_packet["selected_chunks"][0]["content"]
assert compact_packet["citations"]
assert compact_packet["debug"]["full_packet_available_with"] == "--format full"
assert compact_packet["debug"]["selector_strategy_id"] == full_packet["selector_trace"]["strategy_id"]
assert compact_packet["packet_summary"]["selected_chunk_count"] == len(full_packet["selected_chunks"])
assert compact_path.stat().st_size < full_path.stat().st_size
PY

python3 - "$PROMPT_FIRST_PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert packet["schema"] == "rag-rulebook/context-packet/v1"
assert packet["routing"]["scope"] == "prompt"
assert packet["routing"]["layer"] == "03.product"
assert packet["routing"]["mode"] == "discovery"
assert packet["routing"]["workflow"] == ".agentic/product/workflows/default.md"
assert packet["routing"]["previous_packet_id"] == "packet.selector-fixture.previous"
assert packet["request"]["previous_packet_id"] == "packet.selector-fixture.previous"
assert packet["provenance"]["session_context"]["session_id"] == "chat-test-session"
assert packet["provenance"]["session_context"]["branch"] == "chat/test-session"
assert packet["provenance"]["session_context"]["worktree"] == "/tmp/chat-test-session"
assert packet["provenance"]["session_context"]["legacy_routing_hint"]["layer"] == "unknown"
assert "corpus.unknown" not in [corpus["corpus_id"] for corpus in packet["matched_corpora"]]
assert any(corpus["corpus_id"] == "corpus.03.product.platform" for corpus in packet["matched_corpora"])
assert packet["routing"]["status"] == "ready"
PY

python3 - "$MALICIOUS_HINT_PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
matched_corpora = [corpus["corpus_id"] for corpus in packet["matched_corpora"]]
assert packet["routing"]["scope"] == "prompt"
assert packet["routing"]["layer"] == "03.product"
assert packet["routing"]["mode"] == "discovery"
assert packet["routing"]["workflow"] == ".agentic/product/workflows/default.md"
assert packet["intent"]["layer"] == "03.product"
assert packet["intent"]["mode"] == "discovery"
assert packet["intent"]["workflow"] == ".agentic/product/workflows/default.md"
assert packet["provenance"]["session_context"]["legacy_routing_hint"]["layer"] == "04.deploy"
assert packet["provenance"]["session_context"]["legacy_routing_hint"]["trusted"] is False
assert "corpus.03.product.platform" in matched_corpora
assert "corpus.04.deploy" not in matched_corpora
PY

python3 - "$ROUTE_COHERENCE_PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert packet["routing"]["scope"] == "prompt"
assert packet["routing"]["layer"] == "03.product"
assert packet["routing"]["mode"] == "discovery"
assert packet["routing"]["workflow"] == ".agentic/product/workflows/default.md"
assert packet["intent"]["layer"] == "03.product"
assert packet["intent"]["workflow"] == ".agentic/product/workflows/default.md"
PY

python3 - "$SIDE_EFFECT_PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert packet["action_authorization"]["side_effect_class"] == "git"
assert packet["action_authorization"]["execution_allowed"] is False
assert packet["routing"]["status"] == "blocked"
assert "gap.selector-fixture.missing-session-ownership-for-side-effect" in packet["action_authorization"]["blocking_gap_ids"]
assert packet["provenance"]["session_context"]["verification_status"] == "unverified"
PY

if bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "Explain prompt context" \
  --session-worktree relative/worktree \
  --no-focused-paths \
  --pretty > "$TMP_DIR/invalid-worktree.json" 2> "$TMP_DIR/invalid-worktree.err"; then
  echo "ERROR: invalid relative worktree unexpectedly succeeded." >&2
  exit 1
fi

grep -q "session-worktree must be an absolute path" "$TMP_DIR/invalid-worktree.err" || {
  echo "ERROR: invalid worktree failure did not explain the path constraint." >&2
  cat "$TMP_DIR/invalid-worktree.err" >&2
  exit 1
}

if bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --request-text "Explain prompt context" \
  --session-layer 01.harness \
  --session-mode planning \
  --session-workflow .agentic/01.harness/workflows/change-harness.md \
  --trust-session-routing \
  --no-focused-paths \
  --pretty > "$TMP_DIR/trust-without-proof.json" 2> "$TMP_DIR/trust-without-proof.err"; then
  echo "ERROR: trusted routing without lifecycle proof unexpectedly succeeded." >&2
  exit 1
fi

grep -q -- "--trust-session-routing requires governed lifecycle proof fields" "$TMP_DIR/trust-without-proof.err" || {
  echo "ERROR: trusted routing failure did not explain required lifecycle proof." >&2
  cat "$TMP_DIR/trust-without-proof.err" >&2
  exit 1
}

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
