#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-recognition-sources.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test deterministic recognition-source generation.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.generate-recognition-sources
#       path: scripts/02.rag-rulebook/generate-recognition-sources/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

GENERATED="$TMP_DIR/artifacts.yml"
PRINTED="$TMP_DIR/printed.yml"

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --output "$GENERATED" >/dev/null

bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
  --source "$GENERATED" >/dev/null

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --print > "$PRINTED"

cmp "$GENERATED" "$PRINTED" >/dev/null || {
  echo "ERROR: --output and --print produced different recognition sources" >&2
  exit 1
}

python3 - "$GENERATED" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

source = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert source["schema"] == "rag-rulebook/recognition-source/v1"
assert source["source_id"] == "recognition.generated.artifacts"
assert source["generation_mode"] == "generated"
terms = {term["term"]: term for term in source["terms"]}
assert "rag-rulebook.schema.recognition-source" in terms
assert ".agentic/02.rag-rulebook/schemas/recognition-source.schema.yml" in terms
assert "recognition-source.schema.yml" in terms
assert source["generation_summary"]["term_count"] == len(source["terms"])
assert len(source["terms"]) > 100
PY

if [ -f ".agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml" ]; then
  bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check >/dev/null
fi

echo "Recognition-source generator smoke test passed."
