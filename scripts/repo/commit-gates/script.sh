#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.script.commit-gates
#   version: 3
#   status: active
#   created_on: "2026-07-04"
#   updated_on: "2026-10-25"
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
#   - writes-files
#   used_by:
#   - id: chat.script.session-log.prepare-chat-session-before-commit
#     path: scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
#   - id: repo.script.commit-gates.readme
#     path: scripts/repo/commit-gates/README.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# Portable chat preparation already enforces deterministic process drift,
# staged headers and governed command drift. Keep those checks at their owner.
# The repository extension adds inventory coverage and focused implementation
# verification once, and a required missing command is a failure.
for required in scripts/01.harness/artifact-metadata/generate-index/script.sh scripts/repo/check-selection/script.sh; do
  if [ ! -f "$required" ]; then
    echo "ERROR: required repository gate is missing: $required" >&2
    exit 1
  fi
done
bash scripts/01.harness/artifact-metadata/generate-index/script.sh --all --strict --check-coverage > /dev/null
bash scripts/repo/check-selection/script.sh --staged --execute-local --json

echo "Repository commit extension gates passed."
