#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-derivation-reports.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the source-to-rule derivation report validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.validate-derivation-reports
#       path: scripts/02.rag-rulebook/validate-derivation-reports/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT_FILE="$TMP_DIR/current.json"
VALID_REPORT="$TMP_DIR/valid-report.yml"
BROKEN_NO_CLAIMS="$TMP_DIR/broken-no-claims.yml"
BROKEN_CONFLICT_ITEMS="$TMP_DIR/broken-conflict-items.yml"
BROKEN_MISSING_SOURCE="$TMP_DIR/broken-missing-source.yml"
BROKEN_STATUS_DECISION="$TMP_DIR/broken-status-decision.yml"

bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh \
  --current \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["schema"] == "rag-rulebook/source-to-rule-derivation-report/v1"
assert report["counts"]["reports"] >= 1
PY

cat > "$VALID_REPORT" <<'EOF'
schema: rag-rulebook/source-to-rule-derivation-report/v1
report_id: derivation.test.04.deploy.mcp-server
status: needs-review
source_change:
  change_type: created
  approved_source_state: approved
  changed_paths:
    - docs/04.deploy/source-material/02.rag-rulebook/mcp-server-deployment.md
  summary: Test source-to-rule derivation report.
target:
  corpus_id: corpus.04.deploy
  owner_layer: 04.deploy
  deploy_track: 02.rag-rulebook
  expected_rule_paths:
    - docs/04.deploy/rules/02.rag-rulebook/mcp-server-deployment.yml
  affected_rule_paths:
    - docs/04.deploy/rules/02.rag-rulebook/mcp-server-deployment.yml
  affected_rulesets: []
  affected_evaluations:
    - .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/intent-form-planning-mcp-server.yml
  affected_corpus_gaps:
    - .agentic/02.rag-rulebook/corpus-gaps/04.deploy/mcp-server-deployment.yml
semantic_review:
  source_claims:
    - claim_id: local.rag.first
      summary: Local RAG must work before hosted RAG deployment is executable.
      evidence_path: docs/04.deploy/source-material/02.rag-rulebook/mcp-server-deployment.md
  conflicts:
    status: none-found
    search_scope:
      - docs/04.deploy/rules/
    items: []
  drift:
    status: expected
    items:
      - artifact: scripts/02.rag-rulebook/generate-rulebook-index/script.sh
        issue: Deploy corpus is not indexed yet.
        required_resolution: Add corpus root support.
  ownership:
    status: ok
    notes:
      - Deploy corpus owns deploy rules.
proposed_updates:
  rules:
    - docs/04.deploy/rules/02.rag-rulebook/mcp-server-deployment.yml
  rule_packs: []
  recognition_sources: []
  recognition_candidates:
    - .agentic/02.rag-rulebook/recognition-candidates/deferred/2026-06-26-mcp-server.yml
  corpus_gaps:
    - .agentic/02.rag-rulebook/corpus-gaps/04.deploy/mcp-server-deployment.yml
  evaluations: []
  notes:
    - Test report.
downstream_effects:
  index_required: true
  chunks_required: true
  selector_evaluation_required: true
  publish_required: false
  stale_artifacts:
    - generated rulebook index
validation:
  required_checks:
    - bash scripts/02.rag-rulebook/commit-gates/script.sh
  checks_run:
    - command: bash scripts/02.rag-rulebook/commit-gates/script.sh
      result: passed
  checks_pending:
    - Add selector proof.
review:
  required: true
  decision: pending
  notes:
    - Pending review.
EOF

bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh \
  --report "$VALID_REPORT" >/dev/null

python3 - "$VALID_REPORT" "$BROKEN_NO_CLAIMS" "$BROKEN_CONFLICT_ITEMS" "$BROKEN_MISSING_SOURCE" "$BROKEN_STATUS_DECISION" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

valid_path = Path(sys.argv[1])

no_claims = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
no_claims["semantic_review"]["source_claims"] = []
Path(sys.argv[2]).write_text(yaml.safe_dump(no_claims, sort_keys=False), encoding="utf-8")

conflict_items = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
conflict_items["semantic_review"]["conflicts"]["items"] = [{"issue": "should not exist"}]
Path(sys.argv[3]).write_text(yaml.safe_dump(conflict_items, sort_keys=False), encoding="utf-8")

missing_source = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
missing_source["source_change"]["changed_paths"] = ["docs/04.deploy/source-material/missing.md"]
Path(sys.argv[4]).write_text(yaml.safe_dump(missing_source, sort_keys=False), encoding="utf-8")

status_decision = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
status_decision["status"] = "accepted"
status_decision["review"]["decision"] = "pending"
Path(sys.argv[5]).write_text(yaml.safe_dump(status_decision, sort_keys=False), encoding="utf-8")
PY

for broken in \
  "$BROKEN_NO_CLAIMS" \
  "$BROKEN_CONFLICT_ITEMS" \
  "$BROKEN_MISSING_SOURCE" \
  "$BROKEN_STATUS_DECISION"; do
  if bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh \
    --report "$broken" >/dev/null 2>&1; then
    echo "ERROR: derivation-report validator accepted broken report: $broken" >&2
    exit 1
  fi
done

echo "Derivation-report validator smoke test passed."
