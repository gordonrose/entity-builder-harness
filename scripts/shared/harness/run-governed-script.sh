#!/usr/bin/env bash
set -euo pipefail

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
always scripts/shared/chat/audit-chat-layer-migration.sh
always scripts/shared/chat/generate-commit-log-summary.sh
always scripts/shared/chat/report-chat-workspaces.sh
always scripts/shared/git/active-chat-branches.sh
always scripts/shared/git/branch-overlap-report.sh
always scripts/shared/git/check-chat-branch-freshness.sh
always scripts/shared/git/check-commit-prerequisites.sh
always scripts/shared/git/check-commitlog-deletions.sh
always scripts/shared/git/check-write-location.sh
always scripts/shared/git/classify-main-refresh-dirty-state.sh
always scripts/shared/git/dirty-worktree-check.sh
always scripts/shared/git/main-update-status.sh
always scripts/shared/git/verify-local-convergence.sh
always scripts/shared/harness/check-deterministic-process-drift.sh
always scripts/shared/harness/check-governed-script-command-drift.sh
approved scripts/shared/chat/rename-current-chat-log-folder.sh
approved scripts/shared/chat/ensure-llm-workbench-repo.sh
approved scripts/shared/chat/request-initialization/auto-start-missing-session.sh
approved scripts/shared/git/checkpoint-chat-session-log.sh
approved scripts/shared/git/prepare-chat-session-before-commit.sh
approved scripts/shared/git/record-chat-commit.sh
approved scripts/shared/git/stage-active-worktree-paths.sh
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
  scripts/shared/*.sh|scripts/shared/*/*.sh|scripts/shared/chat/request-initialization/*.sh)
    ;;
  *)
    echo "ERROR: refused script outside governed shared script paths: $SCRIPT_PATH" >&2
    exit 1
    ;;
esac

RUN_CLASS=""
case "$SCRIPT_PATH" in
  scripts/shared/chat/audit-chat-layer-migration.sh|\
  scripts/shared/chat/generate-commit-log-summary.sh|\
  scripts/shared/chat/report-chat-workspaces.sh|\
  scripts/shared/git/active-chat-branches.sh|\
  scripts/shared/git/branch-overlap-report.sh|\
  scripts/shared/git/check-chat-branch-freshness.sh|\
  scripts/shared/git/check-commit-prerequisites.sh|\
  scripts/shared/git/check-commitlog-deletions.sh|\
  scripts/shared/git/check-write-location.sh|\
  scripts/shared/git/classify-main-refresh-dirty-state.sh|\
  scripts/shared/git/dirty-worktree-check.sh|\
  scripts/shared/git/main-update-status.sh|\
  scripts/shared/git/verify-local-convergence.sh|\
  scripts/shared/harness/check-deterministic-process-drift.sh|\
  scripts/shared/harness/check-governed-script-command-drift.sh)
    RUN_CLASS="always"
    ;;
  scripts/shared/chat/rename-current-chat-log-folder.sh|\
  scripts/shared/chat/ensure-llm-workbench-repo.sh|\
  scripts/shared/chat/request-initialization/auto-start-missing-session.sh|\
  scripts/shared/git/checkpoint-chat-session-log.sh|\
  scripts/shared/git/prepare-chat-session-before-commit.sh|\
  scripts/shared/git/record-chat-commit.sh|\
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
