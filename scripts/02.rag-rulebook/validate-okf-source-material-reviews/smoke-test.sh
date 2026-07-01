#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-okf-source-material-reviews.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#     - sre
#   kind: script
#   purpose: Smoke test the OKF source-material review validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.validate-okf-source-material-reviews
#       path: scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

REPORT_FILE="$TMP_DIR/current.json"
VALID_RECORD="$TMP_DIR/valid-review.yml"
BROKEN_SCORE="$TMP_DIR/broken-score.yml"
BROKEN_MISSING_ROLE="$TMP_DIR/broken-missing-role.yml"
SOURCE_PATH="docs/04.deploy/source-material/02.rag-rulebook/github-actions-to-ecs-fargate.md"
SOURCE_HASH="$(sha256sum "$SOURCE_PATH" | awk '{print $1}')"

bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh \
  --current \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["schema"] == "rag-rulebook/okf-source-material-review-validation-report/v1"
assert report["counts"]["records"] >= 1
PY

python3 - "$VALID_RECORD" "$SOURCE_PATH" "$SOURCE_HASH" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

record_path, source_path, source_hash = sys.argv[1:4]
roles = ["architect", "agentic-engineer", "secops-engineer", "senior-sre"]
reviewer_assessments = []
for role in roles:
    reviewer_assessments.append({
        "role": role,
        "overall_score": 9.6,
        "decision": "pass",
        "blocking_gaps": [],
        "dimension_scores": {
            "coverage": 9.6,
            "necessity": 9.6,
            "production_grade_gaps": 9.6,
            "execution_variables": 9.6,
            "human_readability": 9.6,
            "machine_readability": 9.6,
            "cost_optimization": 9.6,
            "security": 9.6,
            "performance": 9.6,
            "token_optimization": 9.6,
        },
        "recommendations": [],
    })

record = {
    "schema": "rag-rulebook/okf-source-material-review/v1",
    "review_id": "review.smoke.04-deploy.valid-source",
    "status": "accepted",
    "source_material": {
        "path": source_path,
        "corpus_id": "corpus.04.deploy",
        "vertical": "smoke-test",
        "source_state": "accepted",
        "sha256": source_hash,
        "target_rule_paths": [],
    },
    "threshold": {
        "passing_score": 9.5,
        "required_roles": roles,
        "pass_rule": "every required reviewer score must be greater than 9.5 and no blocking gaps may remain",
    },
    "iterations": [{
        "iteration": 1,
        "source_revision_summary": "Smoke test accepted source review.",
        "reviewer_assessments": reviewer_assessments,
        "cross_review_summary": {
            "agreement": ["accepted"],
            "disagreement": [],
            "unresolved_blockers": [],
        },
        "recommendation_handling": {
            "applied": [],
            "rejected": [],
        },
        "rerun_required": False,
    }],
    "final_decision": {
        "status": "accepted",
        "summary": "Accepted for smoke test.",
        "accepted_source_sha256": source_hash,
        "accepted_at_utc": "2026-06-29T00:00:00Z",
        "required_before_derivation": [],
    },
}
Path(record_path).write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
PY

bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh \
  --record "$VALID_RECORD" >/dev/null

python3 - "$VALID_RECORD" "$BROKEN_SCORE" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

valid, broken = map(Path, sys.argv[1:3])
record = yaml.safe_load(valid.read_text(encoding="utf-8"))
record["iterations"][0]["reviewer_assessments"][0]["overall_score"] = 9.5
broken.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh \
  --record "$BROKEN_SCORE" >/dev/null 2>&1; then
  echo "ERROR: validator accepted a score at the threshold." >&2
  exit 1
fi

python3 - "$VALID_RECORD" "$BROKEN_MISSING_ROLE" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

valid, broken = map(Path, sys.argv[1:3])
record = yaml.safe_load(valid.read_text(encoding="utf-8"))
record["threshold"]["required_roles"] = ["architect", "agentic-engineer", "senior-sre"]
record["iterations"][0]["reviewer_assessments"] = [
    assessment
    for assessment in record["iterations"][0]["reviewer_assessments"]
    if assessment["role"] != "secops-engineer"
]
broken.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh \
  --record "$BROKEN_MISSING_ROLE" >/dev/null 2>&1; then
  echo "ERROR: validator accepted a review record without SecOps." >&2
  exit 1
fi

echo "OKF source-material review validator smoke test passed."
