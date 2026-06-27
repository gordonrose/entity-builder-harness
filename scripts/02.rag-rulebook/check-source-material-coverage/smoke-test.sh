#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-source-material-coverage.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test source-material coverage validation for current and orphan source states.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.check-source-material-coverage
#       path: scripts/02.rag-rulebook/check-source-material-coverage/script.sh

TMP_DIR="$(mktemp -d)"
ORPHAN_SOURCE="docs/04.deploy/source-material/02.rag-rulebook/.source-material-coverage-smoke-test.md"
trap 'rm -rf "$TMP_DIR"; rm -f "$ORPHAN_SOURCE"' EXIT

CURRENT_REPORT="$TMP_DIR/current.json"
ORPHAN_REPORT="$TMP_DIR/orphan.json"

bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh \
  --current \
  --json > "$CURRENT_REPORT"

python3 - "$CURRENT_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert report["schema"] == "rag-rulebook/source-material-coverage-report/v1"
assert report["ok"] is True
assert report["counts"]["sources"] >= 2
paths = {item["path"] for item in report["sources"]}
assert "docs/02.rag-rulebook/source-material/mcp-server-deployment-architecture.md" in paths
assert "docs/04.deploy/source-material/02.rag-rulebook/mcp-server-deployment.md" in paths
PY

cat > "$ORPHAN_SOURCE" <<'MARKDOWN'
# Source Material Coverage Smoke Test

This temporary file intentionally has no structured rule, derivation report, or
corpus gap outcome. The coverage checker must fail while it exists.
MARKDOWN

if bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh \
  --current \
  --json > "$ORPHAN_REPORT"; then
  echo "ERROR: orphan source material unexpectedly passed coverage check." >&2
  exit 1
fi

python3 - "$ORPHAN_REPORT" "$ORPHAN_SOURCE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
source_path = sys.argv[2]

assert report["ok"] is False
assert any(source_path in error for error in report["errors"])
source = next(item for item in report["sources"] if item["path"] == source_path)
assert source["outcomes"]["structured_rules"] == []
assert source["outcomes"]["derivation_reports"] == []
assert source["outcomes"]["corpus_gaps"] == []
PY

rm -f "$ORPHAN_SOURCE"

echo "RAG/rulebook source material coverage smoke test passed."
