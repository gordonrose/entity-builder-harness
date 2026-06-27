#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-retirement-records.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the RAG/rulebook retirement-record validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.validate-retirement-records
#       path: scripts/02.rag-rulebook/validate-retirement-records/script.sh

TMP_DIR="$(mktemp -d)"
REFERENCE_FILE=".agentic/02.rag-rulebook/.retirement-smoke-active-reference.md"
cleanup() {
  rm -rf "$TMP_DIR"
  rm -f "$REFERENCE_FILE"
}
trap cleanup EXIT

REPORT_FILE="$TMP_DIR/current.json"
VALID_RECORD="$TMP_DIR/valid-retirement.yml"
BROKEN_NO_HASH="$TMP_DIR/broken-no-hash.yml"
BROKEN_PENDING_ACCEPTED="$TMP_DIR/broken-pending-accepted.yml"
BROKEN_MISSING_REPLACEMENT="$TMP_DIR/broken-missing-replacement.yml"
BROKEN_REMAINING_REFERENCE="$TMP_DIR/broken-remaining-reference.yml"
BROKEN_DISCOVERED_REFERENCE="$TMP_DIR/broken-discovered-reference.yml"
RETIRED_PATH_PREFIX="docs/04.deploy/source-material/02.rag-rulebook/old-mcp-server"
RETIRED_PATH="$RETIRED_PATH_PREFIX-deployment.md"

bash scripts/02.rag-rulebook/validate-retirement-records/script.sh \
  --current \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["schema"] == "rag-rulebook/retirement-record-validation-report/v1"
assert "counts" in report
PY

cat > "$VALID_RECORD" <<EOF
schema: rag-rulebook/retirement-record/v1
retirement_id: retirement.test.04.deploy.old-mcp-source
status: accepted
owner_layer: 04.deploy
corpus_id: corpus.04.deploy
retired_at_utc: "2026-06-27T00:00:00Z"
retired_artifacts:
  - path: $RETIRED_PATH
    kind: source-material
    path_state: removed
    previous_sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    replacement_paths:
      - docs/04.deploy/source-material/02.rag-rulebook/mcp-server-deployment.md
reason:
  - The old source was merged into the current MCP server deployment source.
reference_checks:
  checked_roots:
    - .agentic/02.rag-rulebook
    - docs/04.deploy
    - scripts/02.rag-rulebook
  remaining_references: []
validation:
  required_checks:
    - bash scripts/02.rag-rulebook/validate-retirement-records/script.sh --current
  checks_run:
    - command: bash scripts/02.rag-rulebook/validate-retirement-records/script.sh --current
      result: passed
  checks_pending: []
review:
  required: true
  decision: accept
  reviewer: smoke-test
  notes:
    - Accepted for validator smoke coverage.
EOF

bash scripts/02.rag-rulebook/validate-retirement-records/script.sh \
  --record "$VALID_RECORD" >/dev/null

python3 - "$VALID_RECORD" "$BROKEN_NO_HASH" "$BROKEN_PENDING_ACCEPTED" "$BROKEN_MISSING_REPLACEMENT" "$BROKEN_REMAINING_REFERENCE" "$BROKEN_DISCOVERED_REFERENCE" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

valid_path = Path(sys.argv[1])

no_hash = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
no_hash["retired_artifacts"][0].pop("previous_sha256", None)
Path(sys.argv[2]).write_text(yaml.safe_dump(no_hash, sort_keys=False), encoding="utf-8")

pending = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
pending["review"]["decision"] = "pending"
Path(sys.argv[3]).write_text(yaml.safe_dump(pending, sort_keys=False), encoding="utf-8")

missing_replacement = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
missing_replacement["retired_artifacts"][0]["path_state"] = "renamed"
missing_replacement["retired_artifacts"][0]["replacement_paths"] = ["docs/04.deploy/source-material/missing.md"]
Path(sys.argv[4]).write_text(yaml.safe_dump(missing_replacement, sort_keys=False), encoding="utf-8")

remaining_reference = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
remaining_reference["reference_checks"]["remaining_references"] = ["docs/04.deploy/rules/old.yml"]
Path(sys.argv[5]).write_text(yaml.safe_dump(remaining_reference, sort_keys=False), encoding="utf-8")

discovered_reference = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
Path(sys.argv[6]).write_text(yaml.safe_dump(discovered_reference, sort_keys=False), encoding="utf-8")
PY

for broken in \
  "$BROKEN_NO_HASH" \
  "$BROKEN_PENDING_ACCEPTED" \
  "$BROKEN_MISSING_REPLACEMENT" \
  "$BROKEN_REMAINING_REFERENCE"; do
  if bash scripts/02.rag-rulebook/validate-retirement-records/script.sh \
    --record "$broken" >/dev/null 2>&1; then
    echo "ERROR: retirement-record validator accepted broken record: $broken" >&2
    exit 1
  fi
done

cat > "$REFERENCE_FILE" <<EOF
Temporary smoke-test active reference to $RETIRED_PATH.
EOF

if bash scripts/02.rag-rulebook/validate-retirement-records/script.sh \
  --record "$BROKEN_DISCOVERED_REFERENCE" >/dev/null 2>&1; then
  echo "ERROR: retirement-record validator accepted an undisclosed active reference" >&2
  exit 1
fi

echo "Retirement-record validator smoke test passed."
