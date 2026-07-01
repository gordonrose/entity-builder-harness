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
RETIREMENT_RECORD=".agentic/02.rag-rulebook/retirements/.source-projection-smoke-test.yml"
trap 'rm -rf "$TMP_DIR"; rm -f "$RETIREMENT_RECORD"' EXIT

VALID_REPORT="$TMP_DIR/valid-report.json"
MISSING_SOURCE_MANIFEST="$TMP_DIR/missing-source.yml"
MISSING_RULE_MANIFEST="$TMP_DIR/missing-rule.yml"
RETIRED_SET_MANIFEST="$TMP_DIR/retired-set.yml"
MISSING_SOURCE_REPORT="$TMP_DIR/missing-source-report.json"
MISSING_RULE_REPORT="$TMP_DIR/missing-rule-report.json"
RETIRED_SET_REPORT="$TMP_DIR/retired-set-report.json"
RETIRED_SOURCE_PREFIX="docs/04.deploy/source-material/02.rag-rulebook/.source-projection-retired"
RETIRED_SOURCE="$RETIRED_SOURCE_PREFIX.md"

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

python3 - "$RETIRED_SET_MANIFEST" "$RETIRED_SOURCE" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

source = Path(".agentic/02.rag-rulebook/source-projections/v1.yml")
data = yaml.safe_load(source.read_text(encoding="utf-8"))
data["projection_sets"].append(
    {
        "id": "projection.04.deploy.source-projection-smoke-retired",
        "status": "retired",
        "projection_mode": "manual-reviewed",
        "source_material": [
            {
                "path": sys.argv[2],
                "role": "primary",
            }
        ],
        "target": {
            "corpus_id": "corpus.04.deploy",
            "owner_layer": "04.deploy",
        },
        "expected_rule_paths": [],
        "derivation_reports": [],
        "corpus_gap_paths": [],
        "expected_selector_evaluations": [],
        "required_checks": [
            "bash scripts/02.rag-rulebook/check-source-projections/script.sh --current",
        ],
    }
)
Path(sys.argv[1]).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/check-source-projections/script.sh \
  --current \
  --manifest "$RETIRED_SET_MANIFEST" \
  --json > "$RETIRED_SET_REPORT"; then
  echo "ERROR: retired projection set without retirement record unexpectedly passed." >&2
  exit 1
fi

python3 - "$RETIRED_SET_REPORT" "$RETIRED_SOURCE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
retired_source = sys.argv[2]

assert report["ok"] is False
assert any(retired_source in error and "lacks accepted retirement record" in error for error in report["errors"])
PY

cat > "$RETIREMENT_RECORD" <<EOF
schema: rag-rulebook/retirement-record/v1
retirement_id: retirement.test.04.deploy.source-projection-smoke
status: accepted
owner_layer: 04.deploy
corpus_id: corpus.04.deploy
retired_at_utc: "2026-06-27T00:00:00Z"
retired_artifacts:
  - path: $RETIRED_SOURCE
    kind: source-material
    path_state: removed
    previous_sha256: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
reason:
  - Temporary smoke-test retired projection source.
reference_checks:
  checked_roots:
    - .agentic/02.rag-rulebook
    - docs/04.deploy
    - scripts/02.rag-rulebook
  remaining_references: []
validation:
  required_checks:
    - bash scripts/02.rag-rulebook/check-source-projections/script.sh --current
  checks_run:
    - command: bash scripts/02.rag-rulebook/check-source-projections/script.sh --current
      result: passed
  checks_pending: []
review:
  required: true
  decision: accept
  reviewer: smoke-test
  notes:
    - Accepted only for source projection smoke coverage.
EOF

bash scripts/02.rag-rulebook/check-source-projections/script.sh \
  --current \
  --manifest "$RETIRED_SET_MANIFEST" \
  --json > "$RETIRED_SET_REPORT"

python3 - "$RETIRED_SET_REPORT" "$RETIRED_SOURCE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
retired_source = sys.argv[2]

assert report["ok"] is True, report
assert retired_source in report["accepted_retirements"]
PY

echo "Source projection checker smoke test passed."
