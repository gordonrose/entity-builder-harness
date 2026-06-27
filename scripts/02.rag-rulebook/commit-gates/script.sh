#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.commit-gates
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Run RAG/rulebook layer commit-boundary validation when the layer is present.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: chat.script.session-log.prepare-chat-session-before-commit
#       path: scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
#     - id: rag-rulebook.script.commit-gates.readme
#       path: scripts/02.rag-rulebook/commit-gates/README.md
#     - id: rag-rulebook.script.commit-gates.smoke-test
#       path: scripts/02.rag-rulebook/commit-gates/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

LAYER_DIR=".agentic/02.rag-rulebook"

if [ ! -d "$LAYER_DIR" ]; then
  echo "RAG/rulebook layer absent; skipping RAG/rulebook commit gates."
  exit 0
fi

require_executable() {
  local path="$1"

  if [ ! -x "$path" ]; then
    echo "ERROR: required RAG/rulebook gate is missing or not executable: $path" >&2
    exit 1
  fi
}

require_executable "scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh"
bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh --current --json >/dev/null
echo "RAG/rulebook retrieval policy pack is valid."

require_executable "scripts/02.rag-rulebook/validate-yaml-syntax/script.sh"
bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh
echo "RAG/rulebook governed YAML syntax is valid."

if [ -d "$LAYER_DIR/recognition-sources" ]; then
  require_executable "scripts/02.rag-rulebook/validate-recognition-sources/script.sh"
  bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current
  echo "RAG/rulebook recognition sources are valid."
fi

if [ -d "$LAYER_DIR/recognition-candidates" ]; then
  require_executable "scripts/02.rag-rulebook/validate-recognition-candidates/script.sh"
  bash scripts/02.rag-rulebook/validate-recognition-candidates/script.sh --current
  echo "RAG/rulebook recognition candidates are valid."
fi

if [ -d "$LAYER_DIR/derivation-reports" ]; then
  require_executable "scripts/02.rag-rulebook/validate-derivation-reports/script.sh"
  bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --current
  echo "RAG/rulebook source derivation reports are valid."
fi

if [ -d "$LAYER_DIR/recognition-sources/generated" ]; then
  require_executable "scripts/02.rag-rulebook/generate-recognition-sources/script.sh"
  bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check
  echo "RAG/rulebook generated recognition sources are current."
fi

require_executable "scripts/02.rag-rulebook/generate-retrieval-selector-fixture/smoke-test.sh"
bash scripts/02.rag-rulebook/generate-retrieval-selector-fixture/smoke-test.sh >/dev/null
echo "RAG/rulebook retrieval selector fixture is valid."

require_executable "scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/smoke-test.sh"
bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/smoke-test.sh >/dev/null
echo "RAG/rulebook retrieval selector evaluations passed."

require_executable "scripts/02.rag-rulebook/build-local-runtime/smoke-test.sh"
bash scripts/02.rag-rulebook/build-local-runtime/smoke-test.sh >/dev/null
echo "RAG/rulebook local runtime build smoke passed."

require_executable "scripts/02.rag-rulebook/check-runtime-freshness/smoke-test.sh"
bash scripts/02.rag-rulebook/check-runtime-freshness/smoke-test.sh >/dev/null
echo "RAG/rulebook local runtime freshness smoke passed."

require_executable "scripts/02.rag-rulebook/query-local-context/smoke-test.sh"
bash scripts/02.rag-rulebook/query-local-context/smoke-test.sh >/dev/null
echo "RAG/rulebook local context query smoke passed."

echo "RAG/rulebook commit gates passed."
