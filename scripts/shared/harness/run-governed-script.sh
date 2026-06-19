#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Run only explicitly governed repository scripts with approval-sensitive routing.
#   domain: governance
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/harness/standards/governed-script-permissions.md
#     - .agentic/00.chat/workflows/chat-start.md
#   effects: read-only

usage() {
  cat <<'EOF'
Usage:
  run-governed-script.sh [--approved-action] <script> [args...]
  run-governed-script.sh --list

Runs only explicitly governed repository scripts.

Use --approved-action only after the current chat has explicit approval for the
action class governed by the active workflow.
EOF
}

APPROVED_ACTION="no"

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

case "$1" in
  --approved-action)
    APPROVED_ACTION="yes"
    shift
    ;;
  --list)
    cat <<'EOF'
always scripts/00.chat/migration/audit-chat-layer-migration/script.sh
always scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
always scripts/00.chat/reporting/generate-commit-log-summary/script.sh
always scripts/00.chat/reporting/report-chat-workspaces/script.sh
always scripts/00.chat/local-merge/list-active-chat-branches/script.sh
always scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh
always scripts/00.chat/main-refresh/check-chat-is-current-with-main/script.sh
always scripts/00.chat/session-log/check-commit-prerequisites/script.sh
always scripts/00.chat/session-log/check-commitlog-deletions/script.sh
always scripts/00.chat/worktree/check-write-location/script.sh
always scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh
always scripts/00.chat/worktree/dirty-worktree-check/script.sh
always scripts/00.chat/main-refresh/show-main-update-status/script.sh
always scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh
always scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh
always scripts/shared/harness/check-deterministic-process-drift.sh
always scripts/shared/harness/check-artifact-metadata-headers.sh
always scripts/shared/harness/check-governed-script-command-drift.sh
approved scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh
approved scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh
approved scripts/00.chat/startup/auto-start-missing-session/script.sh
approved scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh
approved scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh
approved scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
approved scripts/00.chat/session-log/record-chat-commit/script.sh
EOF
    exit 0
    ;;
  -h|--help)
    usage
    exit 0
    ;;
esac

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

SCRIPT_PATH="$1"
shift

case "$SCRIPT_PATH" in
  /*|*../*|../*|*"/.."|*".."|*"
"*) 
    echo "ERROR: refused non-repository script path: $SCRIPT_PATH" >&2
    exit 1
    ;;
  scripts/shared/*.sh|scripts/shared/*/*.sh|scripts/shared/chat/request-initialization/*.sh|\
  scripts/00.chat/migration/audit-chat-layer-migration/script.sh|\
  scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh|\
  scripts/00.chat/reporting/generate-commit-log-summary/script.sh|\
  scripts/00.chat/reporting/report-chat-workspaces/script.sh|\
  scripts/00.chat/local-merge/list-active-chat-branches/script.sh|\
  scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh|\
  scripts/00.chat/main-refresh/check-chat-is-current-with-main/script.sh|\
  scripts/00.chat/session-log/check-commit-prerequisites/script.sh|\
  scripts/00.chat/session-log/check-commitlog-deletions/script.sh|\
  scripts/00.chat/worktree/check-write-location/script.sh|\
  scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh|\
  scripts/00.chat/worktree/dirty-worktree-check/script.sh|\
  scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh|\
  scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh|\
  scripts/00.chat/main-refresh/show-main-update-status/script.sh|\
  scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh|\
  scripts/00.chat/startup/auto-start-missing-session/script.sh|\
  scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh|\
  scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh|\
  scripts/00.chat/session-log/record-chat-commit/script.sh|\
  scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh|\
  scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh)
    ;;
  *)
    echo "ERROR: refused script outside governed shared script paths: $SCRIPT_PATH" >&2
    exit 1
    ;;
esac

RUN_CLASS=""
case "$SCRIPT_PATH" in
  scripts/00.chat/migration/audit-chat-layer-migration/script.sh|\
  scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh|\
  scripts/00.chat/reporting/generate-commit-log-summary/script.sh|\
  scripts/00.chat/reporting/report-chat-workspaces/script.sh|\
  scripts/00.chat/local-merge/list-active-chat-branches/script.sh|\
  scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh|\
  scripts/00.chat/main-refresh/check-chat-is-current-with-main/script.sh|\
  scripts/shared/git/check-commit-prerequisites.sh|\
  scripts/00.chat/session-log/check-commit-prerequisites/script.sh|\
  scripts/shared/git/check-commitlog-deletions.sh|\
  scripts/00.chat/session-log/check-commitlog-deletions/script.sh|\
  scripts/shared/git/check-write-location.sh|\
  scripts/00.chat/worktree/check-write-location/script.sh|\
  scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh|\
  scripts/shared/git/dirty-worktree-check.sh|\
  scripts/00.chat/worktree/dirty-worktree-check/script.sh|\
  scripts/00.chat/main-refresh/show-main-update-status/script.sh|\
  scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh|\
  scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh|\
  scripts/shared/harness/check-deterministic-process-drift.sh|\
  scripts/shared/harness/check-artifact-metadata-headers.sh|\
  scripts/shared/harness/check-governed-script-command-drift.sh)
    RUN_CLASS="always"
    ;;
  scripts/shared/chat/rename-current-chat-log-folder.sh|\
  scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh|\
  scripts/shared/chat/ensure-llm-workbench-repo.sh|\
  scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh|\
  scripts/shared/chat/request-initialization/auto-start-missing-session.sh|\
  scripts/00.chat/startup/auto-start-missing-session/script.sh|\
  scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh|\
  scripts/shared/git/checkpoint-chat-session-log.sh|\
  scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh|\
  scripts/shared/git/prepare-chat-session-before-commit.sh|\
  scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh|\
  scripts/shared/git/record-chat-commit.sh|\
  scripts/00.chat/session-log/record-chat-commit/script.sh|\
  scripts/shared/git/stage-active-worktree-paths.sh)
    RUN_CLASS="approved"
    ;;
  *)
    echo "ERROR: script is not in the governed allowlist: $SCRIPT_PATH" >&2
    exit 1
    ;;
esac

if [ "$RUN_CLASS" = "approved" ] && [ "$APPROVED_ACTION" != "yes" ]; then
  echo "ERROR: approval-sensitive script requires --approved-action: $SCRIPT_PATH" >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "ERROR: governed script does not exist: $SCRIPT_PATH" >&2
  exit 1
fi

exec bash "$SCRIPT_PATH" "$@"
