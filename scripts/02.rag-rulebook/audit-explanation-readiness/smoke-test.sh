#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.audit-explanation-readiness.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the explanation readiness audit for current and weak-source states.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.audit-explanation-readiness
#       path: scripts/02.rag-rulebook/audit-explanation-readiness/script.sh

TMP_DIR="$(mktemp -d)"
WEAK_SOURCE="docs/04.deploy/source-material/02.rag-rulebook/.explanation-readiness-smoke-test.md"
trap 'rm -rf "$TMP_DIR"; rm -f "$WEAK_SOURCE"' EXIT

CURRENT_REPORT="$TMP_DIR/current.json"
WEAK_REPORT="$TMP_DIR/weak.json"

bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh \
  --current \
  --json > "$CURRENT_REPORT"

python3 - "$CURRENT_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert report["schema"] == "rag-rulebook/explanation-readiness-audit/v1"
assert report["ok"] is True
assert report["counts"]["sources"] >= 8
assert report["counts"]["source_explanation_chunks"] > 0
paths = {item["path"]: item for item in report["sources"]}
platform = paths["docs/harness/architecture/source-material/platform-runtime-enterprise-obligations-v1.md"]
assert platform["readiness_status"] == "ready"
assert platform["chunked"] is True
assert platform["source_explanation_chunk_count"] > 0
assert platform["execution_authority_status"] == "has-execution-authority"
assert "platform.runtime-shell-surfaces-are-explicit" in platform["execution_rule_ids"]
PY

cat > "$WEAK_SOURCE" <<'MARKDOWN'
<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.source-material.explanation-readiness-smoke-test
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
kind: source-material
purpose: Temporary weak explanation readiness smoke-test source.
-->
# Overview

This temporary source has enough words to become a chunk, but only one generic
heading. The audit should report it as weak for human explanation instead of
confusing that with an unchunked source.
MARKDOWN

bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh \
  --current \
  --json > "$WEAK_REPORT"

python3 - "$WEAK_REPORT" "$WEAK_SOURCE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
source_path = sys.argv[2]

source = next(item for item in report["sources"] if item["path"] == source_path)
assert source["chunked"] is True
assert source["readiness_status"] == "gap:weak-explanation"
assert source["recommended_repair_source"] == "source-material"
assert "single-section-outline" in source["weak_or_missing_heading_issues"]
assert any(issue.startswith("weak-heading-title:") for issue in source["weak_or_missing_heading_issues"])
assert any(gap["path"] == source_path and gap["readiness_status"] == "gap:weak-explanation" for gap in report["gaps"])
PY

echo "RAG/rulebook explanation readiness audit smoke test passed."
