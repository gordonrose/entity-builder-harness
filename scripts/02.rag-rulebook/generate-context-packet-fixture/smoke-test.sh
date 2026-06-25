#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-context-packet-fixture.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: context-packets
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the read-only context-packet fixture generator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.generate-context-packet-fixture
#       path: scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CHUNKS_FILE="$TMP_DIR/rulebook-chunks.json"
PACKET_FILE="$TMP_DIR/context-packet-fixture.json"
REPORT_FILE="$TMP_DIR/context-packet-report.json"
CURRENT_PACKET_FILE="$TMP_DIR/current-context-packet-fixture.json"

bash scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh --generate-current --pretty > "$CHUNKS_FILE"

bash scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh \
  --chunks "$CHUNKS_FILE" \
  --request-text "Add governed validation checks for a product app route." \
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
assert packet["intent"]["source"] == "deterministic"
assert len(packet["selected_chunks"]) >= 3
assert len(packet["selected_chunks"]) <= 5
assert {chunk["content_kind"] for chunk in packet["selected_chunks"]}.intersection({"required-check"})
assert packet["required_checks"]
assert packet["forbidden_actions"]
assert packet["stop_conditions"]
assert packet["citations"]
assert packet["budgets"]["selected_context_tokens"] == sum(
    chunk["token_estimate"] for chunk in packet["selected_chunks"]
)
assert report["ok"], report
assert report["counts"]["selected_chunks"] == len(packet["selected_chunks"])
PY

bash scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh \
  --generate-current \
  --max-chunks 3 > "$CURRENT_PACKET_FILE"

python3 - "$CURRENT_PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert packet["schema"] == "rag-rulebook/context-packet/v1"
assert len(packet["selected_chunks"]) == 3
PY

echo "Context packet fixture generator smoke test passed."
