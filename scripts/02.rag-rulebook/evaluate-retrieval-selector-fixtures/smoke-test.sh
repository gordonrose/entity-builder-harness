#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.evaluate-retrieval-selector-fixtures.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the retrieval selector evaluation fixture runner.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.evaluate-retrieval-selector-fixtures
#       path: scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT_FILE="$TMP_DIR/retrieval-selector-evaluations.json"

bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh \
  --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/exact-rag-rulebook-workflow.yml \
  --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/prompt-session-conflict.yml \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["counts"]["fixtures"] == 2
assert report["counts"]["failed"] == 0
fixture_ids = {item["fixture_id"] for item in report["fixtures"]}
assert "retrieval-selector.v1.exact-rag-rulebook-workflow" in fixture_ids
assert "retrieval-selector.v1.prompt-session-conflict" in fixture_ids
PY

echo "Retrieval selector evaluation fixtures smoke test passed."
