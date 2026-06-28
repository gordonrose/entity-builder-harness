#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-retrieval-selector-fixture.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the read-only retrieval selector fixture generator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.generate-retrieval-selector-fixture
#       path: scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CHUNKS_FILE="$TMP_DIR/rulebook-chunks.json"
INDEX_FILE="$TMP_DIR/rulebook-index.json"
COMPILED_POLICY_FILE="$TMP_DIR/compiled-retrieval-policy.json"
PACKET_FILE="$TMP_DIR/retrieval-selector-fixture.json"
REPORT_FILE="$TMP_DIR/retrieval-selector-report.json"
CURRENT_PACKET_FILE="$TMP_DIR/current-retrieval-selector-fixture.json"

bash scripts/02.rag-rulebook/generate-rulebook-index/script.sh --pretty > "$INDEX_FILE"
bash scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh --index "$INDEX_FILE" --pretty > "$CHUNKS_FILE"
bash scripts/02.rag-rulebook/compile-retrieval-policy/script.sh \
  --current \
  --index "$INDEX_FILE" \
  --output "$COMPILED_POLICY_FILE" \
  --pretty

bash scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh \
  --chunks "$CHUNKS_FILE" \
  --compiled-policy "$COMPILED_POLICY_FILE" \
  --request-text "Build the RAG rulebook retrieval selector fixture using routing recognition sources." \
  --session-layer 02.rag-rulebook \
  --session-mode implementation \
  --session-workflow .agentic/02.rag-rulebook/workflows/default.md \
  --focused-path .agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml \
  --focused-path .agentic/02.rag-rulebook/recognition-sources/generated/routing.yml \
  --pretty > "$PACKET_FILE"

bash scripts/02.rag-rulebook/validate-context-packet/script.sh \
  --packet "$PACKET_FILE" \
  --chunks "$CHUNKS_FILE" \
  --json > "$REPORT_FILE"

python3 - "$PACKET_FILE" "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
report = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert packet["schema"] == "rag-rulebook/context-packet/v1"
assert packet["routing"]["status"] == "ready"
assert packet["routing"]["layer"] == "02.rag-rulebook"
assert packet["routing"]["classification_source"] == "request-context-plus-recognition-sources"
assert packet["intent"]["source"] == "mixed"
assert packet["provenance"]["compiled_policy"]["schema"] == "rag-rulebook/compiled-retrieval-policy/v1"
assert packet["provenance"]["compiled_policy"]["compiled_policy_id"].startswith("compiled.retrieval-policy.retrieval-selector.v1.")
assert packet["provenance"]["policy_pack"]["policy_pack_id"] == "retrieval-selector.v1"
assert packet["provenance"]["recognition_sources"]["matched_terms"] > 0
assert packet["provenance"]["retrieval_order"][0] == "load compiled retrieval policy"
assert packet["selector_trace"]["strategy_id"] == "retrieval-selector.v1.hybrid-deterministic-first"
assert [stage["stage_id"] for stage in packet["selector_trace"]["stages"]][-1] == "final-ranking"
assert packet["request"]["recognition_source_matches"]
assert any(match["source_id"] == "recognition.generated.routing" for match in packet["request"]["recognition_source_matches"])
assert len(packet["selected_chunks"]) >= 3
assert len(packet["selected_chunks"]) <= 6
assert packet["required_checks"]
assert packet["forbidden_actions"]
assert packet["stop_conditions"]
assert packet["citations"]
assert report["ok"], report
PY

bash scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh \
  --generate-current \
  --compiled-policy "$COMPILED_POLICY_FILE" \
  --max-chunks 3 > "$CURRENT_PACKET_FILE"

python3 - "$CURRENT_PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert packet["schema"] == "rag-rulebook/context-packet/v1"
assert len(packet["selected_chunks"]) == 3
assert packet["provenance"]["retrieval_order"][0] == "load compiled retrieval policy"
assert packet["selector_trace"]["candidate_counts"]["selected"] == 3
PY

echo "Retrieval selector fixture generator smoke test passed."
