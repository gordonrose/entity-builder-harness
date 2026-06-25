#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-rulebook-index.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: indexing
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the read-only rulebook index validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.validate-rulebook-index
#       path: scripts/02.rag-rulebook/validate-rulebook-index/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INDEX_FILE="$TMP_DIR/rulebook-index.json"
REPORT_FILE="$TMP_DIR/rulebook-index-validation.json"
BROKEN_INDEX_FILE="$TMP_DIR/broken-rulebook-index.json"

bash scripts/02.rag-rulebook/generate-rulebook-index/script.sh --pretty > "$INDEX_FILE"
bash scripts/02.rag-rulebook/validate-rulebook-index/script.sh --index "$INDEX_FILE" --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["counts"]["corpus_packages"] >= 10
assert report["counts"]["artifacts"] >= 26
assert report["counts"]["rules"] > 0
assert report["counts"]["graph_edges"] > 0
PY

python3 - "$INDEX_FILE" "$BROKEN_INDEX_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
data = json.loads(source.read_text(encoding="utf-8"))
data["graph_edges"][0]["to_ref"] = "missing.ref"
target.write_text(json.dumps(data), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/validate-rulebook-index/script.sh --index "$BROKEN_INDEX_FILE" >/dev/null 2>&1; then
  echo "ERROR: validator accepted a broken graph edge" >&2
  exit 1
fi

echo "Rulebook index validator smoke test passed."
