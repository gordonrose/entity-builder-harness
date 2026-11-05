#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection.wrapper
#   version: 3
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-11-05"
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
  echo "Usage: smoke-test.sh [--unit <registered-unit>]" >&2
  echo "Supported units are the literal branches below, registered in checks.yml." >&2
  exit 2
fi
# Owner suites perform Git operations only in their self-created temporary roots.
# Literal dispatch preserves the old fixture-only execution boundary, not general
# permission to forward a command or mutate this repository.
case "$2" in
  chat-startup) exec bash scripts/00.chat/startup/start-chat-session/smoke-test.sh ;;
  chat-log-writers) exec bash scripts/00.chat/session-log/update-chat-log/smoke-test.sh ;;
  chat-log-maintenance) exec bash scripts/00.chat/session-log/checkpoint-chat-session-log/smoke-test.sh ;;
  chat-summary) exec bash scripts/00.chat/reporting/generate-commit-log-summary/smoke-test.sh ;;
  chat-upstream-portability) exec bash scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh ;;
  harness-governed-runner) exec bash scripts/01.harness/smoke-test-governed-script-runner.sh ;;
  harness-command-drift) exec bash scripts/01.harness/smoke-test-governed-script-command-drift.sh ;;
  harness-process-drift) exec bash scripts/01.harness/smoke-test-deterministic-process-drift.sh ;;
  chat-bootstrap-audit) exec bash scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/smoke-test.sh ;;
  chat-migration-audit) exec bash scripts/00.chat/migration/audit-chat-layer-migration/smoke-test.sh ;;
  chat-upstream-ensure) exec bash scripts/00.chat/upstream/ensure-llm-workbench-repo/smoke-test.sh ;;
  chat-upstream-contract) exec bash scripts/00.chat/upstream/check-llm-workbench-contract/smoke-test.sh ;;
  chat-upstream-bootstrap) exec bash scripts/00.chat/upstream/bootstrap-llm-workbench-repo/smoke-test.sh ;;
  chat-integration-preparation) exec bash scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/smoke-test.sh ;;
  chat-cleanup) exec bash scripts/00.chat/git/cleanup-empty-chat-branches/smoke-test.sh ;;
  chat-prerequisites) exec bash scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh ;;
  chat-conflict-audit) exec bash scripts/00.chat/main-refresh/verify-conflict-audit/smoke-test.sh ;;
  chat-recovery) exec bash scripts/00.chat/recovery/import-active-paths-to-chat-worktree/smoke-test.sh ;;
  chat-session-reader) exec bash scripts/00.chat/session-log/read-current-chat-log/smoke-test.sh ;;
  chat-session-resolution) exec bash scripts/00.chat/startup/resolve-current-chat-session/smoke-test.sh ;;
  chat-worktree-paths) exec bash scripts/00.chat/worktree/paths/smoke-test.sh ;;
  chat-command-dispatch) exec bash scripts/00.chat/command/dispatcher/smoke-test.sh ;;
  chat-refresh-readiness) exec bash scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh ;;
  chat-conflict-classification) exec bash scripts/00.chat/main-refresh/classify-conflict/smoke-test.sh ;;
  chat-log-deletion) exec bash scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh ;;
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
