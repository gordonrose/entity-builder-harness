#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.report-artifact-retrieval-profile-coverage.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the artifact retrieval-profile coverage report helper.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.report-artifact-retrieval-profile-coverage
#       path: scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INDEX_FILE="$TMP_DIR/artifact-index.json"
REPORT_FILE="$TMP_DIR/report.json"
TEXT_REPORT="$TMP_DIR/report.txt"

bash scripts/01.harness/artifact-metadata/generate-index/script.sh \
  --all \
  --pretty \
  --strict > "$INDEX_FILE"

bash scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/script.sh \
  --index "$INDEX_FILE" \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["schema"] == "rag-rulebook/artifact-retrieval-profile-coverage-report/v1"
assert report["counts"]["artifacts"] >= 689
assert report["counts"]["coverage"].get("strong", 0) >= 1
assert report["counts"]["coverage"].get("partial", 0) == 0
assert report["counts"]["coverage"].get("weak", 0) == 0
assert report["counts"]["repair_sources"].get("generator-rule", 0) == 0

records = {record["artifact_id"]: record for record in report["records"]}
script = records.get("rag-rulebook.script.report-artifact-retrieval-profile-coverage")
assert script is not None, records.keys()
assert script["coverage"] == "strong"
assert "artifact.script" in script["specific_roles"]
assert "script.report" in script["specific_roles"]
assert script["produces"], script
assert script["consumes"], script
PY

bash scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/script.sh \
  --index "$INDEX_FILE" > "$TEXT_REPORT"

if ! grep -q "Artifact retrieval profile coverage report" "$TEXT_REPORT"; then
  echo "ERROR: text report missing title" >&2
  exit 1
fi

if ! grep -q "Coverage:" "$TEXT_REPORT"; then
  echo "ERROR: text report missing coverage section" >&2
  exit 1
fi

echo "Artifact retrieval-profile coverage report smoke test passed."
