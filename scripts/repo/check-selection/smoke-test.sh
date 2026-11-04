#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection.wrapper
#   version: 2
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-31"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Exercise focused change selection and declaration coverage with disposable synthetic scopes and no external operations.
#   portability: { class: source-only, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.command.check-selection
#     path: scripts/repo/check-selection/script.sh
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [ "$#" -eq 0 ]; then
  exec bash scripts/repo/check-selection/script.sh --aggregate-members check-selection-regression --execute-local --json
fi
if [ "$#" -ne 2 ] || [ "$1" != "--unit" ]; then
  echo "Usage: smoke-test.sh [--unit mechanics|repository-contracts|harness-lifecycle|harness-header|harness-index|chat-session|chat-local-merge|chat-main-refresh|chat-export|chat-commit-metrics]" >&2
  exit 2
fi
# Owner suites perform Git operations only in their self-created temporary roots.
# Literal dispatch preserves the old fixture-only execution boundary, not general
# permission to forward a command or mutate this repository.
case "$2" in
  mechanics|repository-contracts) exec python3 -B scripts/repo/check-selection/smoke-test.py --suite "$2" ;;
  harness-lifecycle) exec bash scripts/01.harness/artifact-metadata/update-lifecycle/smoke-test.sh ;;
  harness-header) exec bash scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh ;;
  harness-index) exec bash scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh ;;
  chat-session) exec bash scripts/00.chat/session-log/prepare-chat-session-before-commit/smoke-test.sh ;;
  chat-local-merge) exec bash scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/smoke-test.sh ;;
  chat-main-refresh) exec bash scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh ;;
  chat-export) exec bash scripts/00.chat/export/smoke-test.sh ;;
  chat-commit-metrics) exec bash scripts/00.chat/session-log/record-chat-commit/smoke-test.sh ;;
  *) echo "Unknown runner test unit" >&2; exit 2 ;;
esac
