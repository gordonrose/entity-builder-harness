#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-recognition-candidates.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the recognition-candidate validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.validate-recognition-candidates
#       path: scripts/02.rag-rulebook/validate-recognition-candidates/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT_FILE="$TMP_DIR/current.json"
VALID_CANDIDATE="$TMP_DIR/valid-candidate.yml"
BROKEN_NO_SENTENCE="$TMP_DIR/broken-no-sentence.yml"
BROKEN_NO_CONFIDENCE="$TMP_DIR/broken-no-confidence.yml"
BROKEN_STATUS_DECISION="$TMP_DIR/broken-status-decision.yml"
BROKEN_ACCEPTED_MISSING_COVERAGE="$TMP_DIR/broken-accepted-missing-coverage.yml"
BROKEN_COVERED_MISSING_STAGE="$TMP_DIR/broken-covered-missing-stage.yml"
BROKEN_DIRECTORY_STATUS_DIR="$TMP_DIR/accepted"
BROKEN_DIRECTORY_STATUS="$BROKEN_DIRECTORY_STATUS_DIR/wrong-status.yml"

bash scripts/02.rag-rulebook/validate-recognition-candidates/script.sh \
  --current \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["schema"] == "rag-rulebook/recognition-candidate/v1"
assert report["counts"]["candidates"] >= 1
PY

cat > "$VALID_CANDIDATE" <<'EOF'
schema: rag-rulebook/recognition-candidate/v1
candidate_id: recognition-candidate.test.domain-noun.mcp-server
status: needs-review
observed:
  term: MCP server
  sentence: How do I deploy behind an MCP server?
  source: chat-prompt
  layer: 01.harness
  mode: planning
  workflow: .agentic/01.harness/workflows/change-harness.md
suggested:
  source_id: recognition.curated.domain-nouns
  category: domain-noun
  canonical_id: domain.service.mcp-server
  confidence_weight: 0.8
  target_source_path: .agentic/02.rag-rulebook/recognition-sources/curated/domain-nouns.yml
coverage:
  required: true
  status: missing
  gap_id: gap.selector-fixture.missing-corpus.mcp-server
  needed_corpus_ids:
    - corpus.01.harness
    - corpus.04.deploy
  needed_topic: MCP server deployment architecture for harness services.
  suggested_resolution: Add governed corpus source material before accepting this term into curated domain-noun recognition.
  stages:
    source_material:
      status: missing
      evidence_paths: []
    structured_rulebook:
      status: missing
      evidence_paths: []
    indexed_chunks:
      status: missing
      evidence_paths: []
    selector_evaluation:
      status: missing
      evidence_paths: []
reason:
  - Important unmatched service architecture term.
review:
  required: true
  decision: pending
  reviewer_notes: ""
EOF

bash scripts/02.rag-rulebook/validate-recognition-candidates/script.sh \
  --candidate "$VALID_CANDIDATE" >/dev/null

python3 - "$VALID_CANDIDATE" "$BROKEN_NO_SENTENCE" "$BROKEN_NO_CONFIDENCE" "$BROKEN_STATUS_DECISION" "$BROKEN_ACCEPTED_MISSING_COVERAGE" "$BROKEN_COVERED_MISSING_STAGE" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

valid_path = Path(sys.argv[1])

no_sentence = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
no_sentence["observed"].pop("sentence", None)
Path(sys.argv[2]).write_text(yaml.safe_dump(no_sentence, sort_keys=False), encoding="utf-8")

no_confidence = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
no_confidence["suggested"].pop("confidence_weight", None)
Path(sys.argv[3]).write_text(yaml.safe_dump(no_confidence, sort_keys=False), encoding="utf-8")

status_decision = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
status_decision["status"] = "accepted"
status_decision["review"]["decision"] = "pending"
Path(sys.argv[4]).write_text(yaml.safe_dump(status_decision, sort_keys=False), encoding="utf-8")

accepted_missing_coverage = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
accepted_missing_coverage["status"] = "accepted"
accepted_missing_coverage["review"]["decision"] = "accept"
accepted_missing_coverage["review"]["accepted_source_path"] = ".agentic/02.rag-rulebook/recognition-candidates/README.md"
accepted_missing_coverage["review"]["accepted_fixture_path"] = ".agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/intent-form-planning-mcp-server.yml"
Path(sys.argv[5]).write_text(yaml.safe_dump(accepted_missing_coverage, sort_keys=False), encoding="utf-8")

covered_missing_stage = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
covered_missing_stage["coverage"]["status"] = "covered"
Path(sys.argv[6]).write_text(yaml.safe_dump(covered_missing_stage, sort_keys=False), encoding="utf-8")
PY

mkdir -p "$BROKEN_DIRECTORY_STATUS_DIR"
cp "$VALID_CANDIDATE" "$BROKEN_DIRECTORY_STATUS"

for broken in \
  "$BROKEN_NO_SENTENCE" \
  "$BROKEN_NO_CONFIDENCE" \
  "$BROKEN_STATUS_DECISION" \
  "$BROKEN_ACCEPTED_MISSING_COVERAGE" \
  "$BROKEN_COVERED_MISSING_STAGE" \
  "$BROKEN_DIRECTORY_STATUS"; do
  if bash scripts/02.rag-rulebook/validate-recognition-candidates/script.sh \
    --candidate "$broken" >/dev/null 2>&1; then
    echo "ERROR: recognition-candidate validator accepted broken candidate: $broken" >&2
    exit 1
  fi
done

echo "Recognition-candidate validator smoke test passed."
