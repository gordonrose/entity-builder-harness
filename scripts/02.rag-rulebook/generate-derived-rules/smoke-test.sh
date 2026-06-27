#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-derived-rules.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the derived rule projection planner.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.generate-derived-rules
#       path: scripts/02.rag-rulebook/generate-derived-rules/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CURRENT_REPORT="$TMP_DIR/current.json"
MISSING_RULE_MANIFEST="$TMP_DIR/missing-rule.yml"
MISSING_RULE_REPORT="$TMP_DIR/missing-rule.json"

bash scripts/02.rag-rulebook/generate-derived-rules/script.sh \
  --current \
  --check \
  --json > "$CURRENT_REPORT"

python3 - "$CURRENT_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["schema"] == "rag-rulebook/derived-rule-projection-plan/v1"
assert report["ok"] is True
assert report["mode"] == "check"
assert report["counts"]["projection_sets"] >= 2
assert report["counts"]["stale_or_incomplete"] == 0
assert all(item["actions"] == ["none"] for item in report["projection_sets"])
assert any(
    source["sha256"]
    for item in report["projection_sets"]
    for source in item["source_material"]
)
assert any(
    rule["provenance_template"]["source_material"]
    for item in report["projection_sets"]
    for rule in item["expected_rule_paths"]
)
PY

python3 - "$MISSING_RULE_MANIFEST" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

source = Path(".agentic/02.rag-rulebook/source-projections/v1.yml")
data = yaml.safe_load(source.read_text(encoding="utf-8"))
data["projection_sets"][0]["expected_rule_paths"].append(
    "docs/02.rag-rulebook/rules/concerns/derived-rule-projection-smoke-missing.yml"
)
Path(sys.argv[1]).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/generate-derived-rules/script.sh \
  --current \
  --manifest "$MISSING_RULE_MANIFEST" \
  --check \
  --json > "$MISSING_RULE_REPORT"; then
  echo "ERROR: missing derived rule unexpectedly passed projection planning." >&2
  exit 1
fi

python3 - "$MISSING_RULE_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert report["counts"]["stale_or_incomplete"] >= 1
assert any(
    rule["action"] == "create-derived-rule"
    for item in report["projection_sets"]
    for rule in item["expected_rule_paths"]
)
PY

echo "Derived rule projection planner smoke test passed."

