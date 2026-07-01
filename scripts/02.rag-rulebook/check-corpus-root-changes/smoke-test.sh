#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-corpus-root-changes.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test governed corpus-root change detection.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.check-corpus-root-changes
#       path: scripts/02.rag-rulebook/check-corpus-root-changes/script.sh

TMP_DIR="$(mktemp -d)"
ORPHAN_SOURCE="docs/04.deploy/source-material/02.rag-rulebook/.corpus-root-change-smoke-source.md"
RETIREMENT_RECORD=".agentic/02.rag-rulebook/retirements/.corpus-root-change-smoke.yml"
cleanup() {
  rm -rf "$TMP_DIR"
  rm -f "$ORPHAN_SOURCE" "$RETIREMENT_RECORD"
}
trap cleanup EXIT

CURRENT_REPORT="$TMP_DIR/current.json"
DELETED_CHANGES="$TMP_DIR/deleted.tsv"
DELETED_REPORT="$TMP_DIR/deleted.json"
ADDED_SOURCE_CHANGES="$TMP_DIR/added-source.tsv"
ADDED_SOURCE_REPORT="$TMP_DIR/added-source.json"
RETIRED_SOURCE_PREFIX="docs/04.deploy/source-material/02.rag-rulebook/.corpus-root-change-retired"
RETIRED_SOURCE="$RETIRED_SOURCE_PREFIX.md"

bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh \
  --current \
  --json > "$CURRENT_REPORT"

python3 - "$CURRENT_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["schema"] == "rag-rulebook/corpus-root-change-check-report/v1"
assert report["ok"] is True, report
assert "counts" in report
PY

printf 'D\t%s\n' "$RETIRED_SOURCE" > "$DELETED_CHANGES"

if bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh \
  --changes-file "$DELETED_CHANGES" \
  --json > "$DELETED_REPORT"; then
  echo "ERROR: deleted governed path without retirement record unexpectedly passed." >&2
  exit 1
fi

python3 - "$DELETED_REPORT" "$RETIRED_SOURCE" <<'PY'
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
retirement_id: retirement.test.04.deploy.corpus-root-change-smoke
status: accepted
owner_layer: 04.deploy
corpus_id: corpus.04.deploy
retired_at_utc: "2026-06-27T00:00:00Z"
retired_artifacts:
  - path: $RETIRED_SOURCE
    kind: source-material
    path_state: removed
    previous_sha256: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
reason:
  - Temporary smoke-test deleted source.
reference_checks:
  checked_roots:
    - .agentic/02.rag-rulebook
    - docs/04.deploy
    - scripts/02.rag-rulebook
  remaining_references: []
validation:
  required_checks:
    - bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current
  checks_run:
    - command: bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current
      result: passed
  checks_pending: []
review:
  required: true
  decision: accept
  reviewer: smoke-test
  notes:
    - Accepted only for corpus-root change smoke coverage.
EOF

bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh \
  --changes-file "$DELETED_CHANGES" \
  --json > "$DELETED_REPORT"

python3 - "$DELETED_REPORT" "$RETIRED_SOURCE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
retired_source = sys.argv[2]
assert report["ok"] is True, report
assert retired_source in report["accepted_retirements"]
PY

rm -f "$RETIREMENT_RECORD"

cat > "$ORPHAN_SOURCE" <<'MARKDOWN'
# Corpus Root Change Smoke Source

This temporary source intentionally has no structured rule, derivation report,
or corpus gap outcome.
MARKDOWN
printf 'A\t%s\n' "$ORPHAN_SOURCE" > "$ADDED_SOURCE_CHANGES"

if bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh \
  --changes-file "$ADDED_SOURCE_CHANGES" \
  --json > "$ADDED_SOURCE_REPORT"; then
  echo "ERROR: added orphan source unexpectedly passed corpus-root change check." >&2
  exit 1
fi

python3 - "$ADDED_SOURCE_REPORT" "$ORPHAN_SOURCE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
source_path = sys.argv[2]
assert report["ok"] is False
assert any("source-material coverage" in error for error in report["errors"])
assert any(source_path in error for error in report["source_coverage"]["errors"])
PY

echo "Corpus-root change checker smoke test passed."
