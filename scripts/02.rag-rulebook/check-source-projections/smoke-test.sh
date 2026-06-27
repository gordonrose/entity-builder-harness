#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-source-projections.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the source projection checker.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.check-source-projections
#       path: scripts/02.rag-rulebook/check-source-projections/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

VALID_REPORT="$TMP_DIR/valid-report.json"
MISSING_SOURCE_MANIFEST="$TMP_DIR/missing-source.yml"
MISSING_RULE_MANIFEST="$TMP_DIR/missing-rule.yml"
MISSING_SOURCE_REPORT="$TMP_DIR/missing-source-report.json"
MISSING_RULE_REPORT="$TMP_DIR/missing-rule-report.json"

bash scripts/02.rag-rulebook/check-source-projections/script.sh \
  --current \
  --json > "$VALID_REPORT"

python3 - "$VALID_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["schema"] == "rag-rulebook/source-projection-check-report/v1"
assert report["ok"] is True
assert report["counts"]["active_projection_sets"] >= 2
assert report["counts"]["current_source_material_files"] >= 2
assert report["counts"]["declared_rule_paths"] >= 5
PY

python3 - "$MISSING_SOURCE_MANIFEST" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

source = Path(".agentic/02.rag-rulebook/source-projections/v1.yml")
data = yaml.safe_load(source.read_text(encoding="utf-8"))
data["projection_sets"] = data["projection_sets"][1:]
Path(sys.argv[1]).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/check-source-projections/script.sh \
  --current \
  --manifest "$MISSING_SOURCE_MANIFEST" \
  --json > "$MISSING_SOURCE_REPORT"; then
  echo "ERROR: manifest with undeclared source unexpectedly passed." >&2
  exit 1
fi

python3 - "$MISSING_SOURCE_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert any("not declared in active projection manifest" in error for error in report["errors"])
PY

python3 - "$MISSING_RULE_MANIFEST" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

source = Path(".agentic/02.rag-rulebook/source-projections/v1.yml")
data = yaml.safe_load(source.read_text(encoding="utf-8"))
data["projection_sets"][0]["expected_rule_paths"].append(
    "docs/02.rag-rulebook/rules/concerns/source-projection-smoke-missing.yml"
)
Path(sys.argv[1]).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/check-source-projections/script.sh \
  --current \
  --manifest "$MISSING_RULE_MANIFEST" \
  --json > "$MISSING_RULE_REPORT"; then
  echo "ERROR: manifest with missing derived rule unexpectedly passed." >&2
  exit 1
fi

python3 - "$MISSING_RULE_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert any("expected_rule_paths does not exist" in error for error in report["errors"])
PY

echo "Source projection checker smoke test passed."

