#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  dirty-worktree-check.sh [--allow-session-bookkeeping]

Checks whether the worktree is clean. With --allow-session-bookkeeping, changes
limited to the current chat session log and commitLogs/README.md are accepted.
EOF
}

ALLOW_SESSION_BOOKKEEPING="no"

if [ $# -gt 1 ]; then
  usage >&2
  exit 2
fi

if [ $# -eq 1 ]; then
  case "$1" in
    --allow-session-bookkeeping)
      ALLOW_SESSION_BOOKKEEPING="yes"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "clean"
  exit 0
fi

if [ "$ALLOW_SESSION_BOOKKEEPING" = "yes" ]; then
  # shellcheck source=../chat/session-log-paths.sh
  source "scripts/shared/chat/session-log-paths.sh"

  BRANCH="$(git branch --show-current)"

  if SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
    LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"
    SUMMARY_FILE="commitLogs/README.md"
    MIXED_FILES="$(
      {
        git diff --name-only
        git diff --cached --name-only
        git ls-files --others --exclude-standard
      } | awk \
        -v log_file="$LOG_FILE" \
        -v summary_file="$SUMMARY_FILE" \
        '$0 != "" && $0 != log_file && $0 != summary_file' \
        | sort -u
    )"

    if [ -z "${MIXED_FILES// }" ]; then
      echo "bookkeeping-only"
      exit 0
    fi
  fi
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "dirty"
  exit 1
fi

echo "clean"
