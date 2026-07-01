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

GENERATED_ARTIFACTS="$TMP_DIR/artifacts.yml"
GENERATED_ROUTING="$TMP_DIR/routing.yml"
PRINTED_ARTIFACTS="$TMP_DIR/printed-artifacts.yml"
PRINTED_ROUTING="$TMP_DIR/printed-routing.yml"

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source artifacts \
  --output "$GENERATED_ARTIFACTS" >/dev/null

bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
  --source "$GENERATED_ARTIFACTS" >/dev/null

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source routing \
  --output "$GENERATED_ROUTING" >/dev/null

bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
  --source "$GENERATED_ROUTING" >/dev/null

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source artifacts \
  --print > "$PRINTED_ARTIFACTS"

cmp "$GENERATED_ARTIFACTS" "$PRINTED_ARTIFACTS" >/dev/null || {
  echo "ERROR: artifact --output and --print produced different recognition sources" >&2
  exit 1
}

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source routing \
  --print > "$PRINTED_ROUTING"

cmp "$GENERATED_ROUTING" "$PRINTED_ROUTING" >/dev/null || {
  echo "ERROR: routing --output and --print produced different recognition sources" >&2
  exit 1
}

python3 - "$GENERATED_ARTIFACTS" "$GENERATED_ROUTING" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

artifacts = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
routing = yaml.safe_load(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert artifacts["schema"] == "rag-rulebook/recognition-source/v1"
assert artifacts["source_id"] == "recognition.generated.artifacts"
assert artifacts["generation_mode"] == "generated"
artifact_terms = {term["term"]: term for term in artifacts["terms"]}
assert "rag-rulebook.schema.recognition-source" in artifact_terms
assert ".agentic/02.rag-rulebook/schemas/recognition-source.schema.yml" in artifact_terms
assert "recognition-source.schema.yml" in artifact_terms
assert artifacts["generation_summary"]["term_count"] == len(artifacts["terms"])
assert len(artifacts["terms"]) > 100

assert routing["schema"] == "rag-rulebook/recognition-source/v1"
assert routing["source_id"] == "recognition.generated.routing"
assert routing["generation_mode"] == "generated"
routing_terms = {term["term"]: term for term in routing["terms"]}
assert "02.rag-rulebook" in routing_terms
assert "corpus.02.rag-rulebook" in routing_terms
assert "implementation" in routing_terms
assert ".agentic/02.rag-rulebook/workflows/default.md" in routing_terms
assert routing["generation_summary"]["term_count"] == len(routing["terms"])
assert len(routing["terms"]) > 20
PY

if [ -f ".agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml" ]; then
  bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check >/dev/null
fi

echo "Recognition-source generator smoke test passed."
