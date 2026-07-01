#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.report-recognition-candidates.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the recognition-candidate review report helper.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.report-recognition-candidates
#       path: scripts/02.rag-rulebook/report-recognition-candidates/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT_FILE="$TMP_DIR/report.json"
TEXT_REPORT="$TMP_DIR/report.txt"

bash scripts/02.rag-rulebook/report-recognition-candidates/script.sh \
  --current \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["schema"] == "rag-rulebook/recognition-candidate-review-report/v1"
assert report["counts"]["candidates"] >= 1

mcp = None
for candidate in report["candidates"]:
    if candidate["term"] == "MCP server":
        mcp = candidate
        break
assert mcp is not None, report
assert mcp["status"] == "deferred"
assert mcp["lifecycle_directory"] == "deferred"
assert mcp["coverage_status"] == "covered"
action_ids = {action["action_id"] for action in mcp["allowed_next_actions"]}
assert "keep-deferred" in action_ids
assert "add-evidence" in action_ids
assert "accept" in action_ids
assert "reject" in action_ids
assert "merge" in action_ids
assert "add-corpus-coverage" not in action_ids
assert "human reviewer before curated-source mutation" in mcp["review_needs"]
PY

bash scripts/02.rag-rulebook/report-recognition-candidates/script.sh \
  --current > "$TEXT_REPORT"

if ! grep -q "Recognition candidate review report" "$TEXT_REPORT"; then
  echo "ERROR: text report missing title" >&2
  exit 1
fi

if ! grep -q "MCP server" "$TEXT_REPORT"; then
  echo "ERROR: text report missing MCP server candidate" >&2
  exit 1
fi

echo "Recognition-candidate review report smoke test passed."
