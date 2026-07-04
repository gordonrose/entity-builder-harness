#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: repo.script.commit-gates
#   version: 1
#   status: active
#   layer: 06.shared
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Run repository-specific commit-boundary checks behind a portable chat hook.
#   portability:
#     class: source-only
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: chat.script.session-log.prepare-chat-session-before-commit
#     path: scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
#   - id: repo.script.commit-gates.readme
#     path: scripts/repo/commit-gates/README.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

run_if_executable() {
  local path="$1"
  shift

  if [ -x "$path" ]; then
    bash "$path" "$@"
  fi
}

require_executable() {
  local path="$1"

  if [ ! -x "$path" ]; then
    echo "ERROR: required repository commit gate is missing or not executable: $path" >&2
    exit 1
  fi
}

run_if_executable "scripts/01.harness/check-deterministic-process-drift.sh" --staged
run_if_executable "scripts/01.harness/artifact-metadata/check-headers/script.sh" --staged-added
run_if_executable "scripts/01.harness/check-governed-script-command-drift.sh"

if [ -d ".agentic/02.rag-rulebook" ]; then
  require_executable "scripts/02.rag-rulebook/commit-gates/script.sh"
  bash scripts/02.rag-rulebook/commit-gates/script.sh
fi

echo "Repository commit extension gates passed."
