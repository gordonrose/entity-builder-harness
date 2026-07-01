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
TEMP_RULE="docs/02.rag-rulebook/rules/concerns/.derived-rule-projection-apply-smoke.yml"
TEMP_REPORT=".agentic/02.rag-rulebook/derivation-reports/02.rag-rulebook/.derived-rule-projection-apply-smoke.yml"
trap 'rm -rf "$TMP_DIR"; rm -f "$TEMP_RULE" "$TEMP_REPORT"' EXIT

CURRENT_REPORT="$TMP_DIR/current.json"
MISSING_RULE_MANIFEST="$TMP_DIR/missing-rule.yml"
MISSING_RULE_REPORT="$TMP_DIR/missing-rule.json"
APPLY_MANIFEST="$TMP_DIR/apply.yml"
APPLY_REPORT="$TMP_DIR/apply.json"

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

cp docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml "$TEMP_RULE"

cat > "$TEMP_REPORT" <<'YAML'
schema: rag-rulebook/source-to-rule-derivation-report/v1
report_id: derivation.02.rag-rulebook.smoke.derived-rule-projection-apply
status: needs-review
source_change:
  change_type: created
  approved_source_state: approved
  changed_paths:
    - docs/02.rag-rulebook/source-material/mcp-server-deployment-architecture.md
  summary: Smoke report for provenance-only apply testing.
target:
  corpus_id: corpus.02.rag-rulebook
  owner_layer: 02.rag-rulebook
  expected_rule_paths:
    - docs/02.rag-rulebook/rules/concerns/.derived-rule-projection-apply-smoke.yml
  affected_rule_paths:
    - docs/02.rag-rulebook/rules/concerns/.derived-rule-projection-apply-smoke.yml
semantic_review:
  source_claims:
    - claim_id: smoke-claim
      summary: Smoke source claim.
      evidence_path: docs/02.rag-rulebook/source-material/mcp-server-deployment-architecture.md
  conflicts:
    status: none-found
    items: []
  drift:
    status: none-found
    items: []
  ownership:
    status: ok
    notes: []
proposed_updates:
  rules:
    - docs/02.rag-rulebook/rules/concerns/.derived-rule-projection-apply-smoke.yml
downstream_effects:
  index_required: false
  chunks_required: false
  selector_evaluation_required: false
  publish_required: false
validation:
  required_checks: []
  checks_run: []
  checks_pending: []
review:
  required: true
  decision: pending
YAML

python3 - "$TEMP_RULE" "$APPLY_MANIFEST" "$TEMP_REPORT" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

rule_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
report_path = sys.argv[3]

rule = yaml.safe_load(rule_path.read_text(encoding="utf-8"))
rule["source_derivation"]["source_material"][0]["sha256"] = "0" * 64
rule_path.write_text(yaml.safe_dump(rule, sort_keys=False), encoding="utf-8")

manifest = yaml.safe_load(Path(".agentic/02.rag-rulebook/source-projections/v1.yml").read_text(encoding="utf-8"))
manifest["projection_sets"].append(
    {
        "id": "projection.02.rag-rulebook.smoke.derived-rule-projection-apply",
        "status": "active",
        "projection_mode": "manual-reviewed",
        "source_material": [
            {
                "path": "docs/02.rag-rulebook/source-material/mcp-server-deployment-architecture.md",
                "role": "primary",
            }
        ],
        "target": {
            "corpus_id": "corpus.02.rag-rulebook",
            "owner_layer": "02.rag-rulebook",
        },
        "expected_rule_paths": [
            "docs/02.rag-rulebook/rules/concerns/.derived-rule-projection-apply-smoke.yml"
        ],
        "derivation_reports": [report_path],
        "corpus_gap_paths": [],
        "expected_selector_evaluations": [],
        "required_checks": [],
    }
)
manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
PY

bash scripts/02.rag-rulebook/generate-derived-rules/script.sh \
  --current \
  --manifest "$APPLY_MANIFEST" \
  --apply-provenance \
  --generated-at-utc "2026-06-27T00:00:00Z" \
  --json > "$APPLY_REPORT"

python3 - "$APPLY_REPORT" "$TEMP_RULE" "$TEMP_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rule = yaml.safe_load(Path(sys.argv[2]).read_text(encoding="utf-8"))
report_path = sys.argv[3]

assert report["ok"] is True, report["errors"]
assert report["mode"] == "apply-provenance"
assert report["counts"]["writes"] == 1
assert report["writes"][0]["changed"] is True
assert rule["source_derivation"]["generated_at_utc"] == "2026-06-27T00:00:00Z"
assert rule["source_derivation"]["derivation_report"] == report_path
assert rule["source_derivation"]["source_material"][0]["sha256"] != "0" * 64
PY

echo "Derived rule projection planner smoke test passed."
