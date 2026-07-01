#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-source-to-rule-work-order.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the source-to-rule work-order generator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.generate-source-to-rule-work-order
#       path: scripts/02.rag-rulebook/generate-source-to-rule-work-order/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT="$TMP_DIR/work-order.json"
FILTERED="$TMP_DIR/filtered.json"

bash scripts/02.rag-rulebook/generate-source-to-rule-work-order/script.sh --current --json > "$REPORT"
bash scripts/02.rag-rulebook/generate-source-to-rule-work-order/script.sh \
  --current \
  --projection-id projection.02.rag-rulebook.mcp-server-deployment-architecture \
  --json > "$FILTERED"

python3 - "$REPORT" "$FILTERED" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
filtered = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert report["schema"] == "rag-rulebook/source-to-rule-work-order/v1"
assert report["ok"] is True
assert report["counts"]["projection_sets"] >= 1
assert report["work_orders"]

for order in report["work_orders"]:
    assert order["id"]
    assert order["target"]["corpus_id"].startswith("corpus.")
    assert order["source_material"]
    assert order["expected_rule_paths"]
    assert order["derivation_reports"]
    assert order["work_actions"]
    assert order["derivation_instructions"]
    for source in order["source_material"]:
        assert source["path"]
        assert source["exists"] is True
        assert source["sha256"]
        assert isinstance(source["outline"], list)

assert filtered["counts"]["projection_sets"] == 1
only = filtered["work_orders"][0]
assert only["id"] == "projection.02.rag-rulebook.mcp-server-deployment-architecture"
assert only["target"]["corpus_id"] == "corpus.02.rag-rulebook"

print("Source-to-rule work-order smoke assertions passed.")
PY

echo "Source-to-rule work-order smoke test passed."
