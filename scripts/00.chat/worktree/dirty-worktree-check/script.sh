#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.worktree.dirty-worktree-check
#   version: 1
#   status: active
#   created_on: "2026-06-15"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: worktree
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Check worktree cleanliness with optional current-session bookkeeping tolerance.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.worktree.dirty-worktree-check.readme
#     path: scripts/00.chat/worktree/dirty-worktree-check/README.md
#   effects:
#   - read-only
usage() {
  cat <<'EOF'
Usage:
  dirty-worktree-check.sh [--allow-session-bookkeeping]

Checks whether the worktree is clean. With --allow-session-bookkeeping, changes
limited to the current chat session log are accepted.
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

failed() {
  echo "ERROR: $1" >&2
  exit 2
}

if ! STATUS="$(git status --porcelain 2>/dev/null)"; then
  failed "worktree-status-read-failed"
fi
if [[ -z "$STATUS" ]]; then
  echo "clean"
  exit 0
fi

if [ "$ALLOW_SESSION_BOOKKEEPING" = "yes" ]; then
  # shellcheck source=../../session-log/paths/lib.sh
  source "scripts/00.chat/session-log/paths/lib.sh"

  if ! BRANCH="$(git branch --show-current 2>/dev/null)"; then
    failed "worktree-branch-read-failed"
  fi

  if SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
    LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"
    if ! UNSTAGED="$(git diff --name-only 2>/dev/null)"; then
      failed "worktree-unstaged-read-failed"
    fi
    if ! STAGED="$(git diff --cached --name-only 2>/dev/null)"; then
      failed "worktree-staged-read-failed"
    fi
    if ! UNTRACKED="$(git ls-files --others --exclude-standard 2>/dev/null)"; then
      failed "worktree-untracked-read-failed"
    fi
    if ! MIXED_FILES="$(
      { printf '%s\n' "$UNSTAGED" "$STAGED" "$UNTRACKED" | awk \
        -v log_file="$LOG_FILE" \
        '$0 != "" && $0 != log_file' \
        | sort -u; } 2>/dev/null
    )"; then
      failed "worktree-path-selection-failed"
    fi

    if [ -z "${MIXED_FILES// }" ]; then
      echo "bookkeeping-only"
      exit 0
    fi
  fi
fi

if ! STATUS="$(git status --porcelain 2>/dev/null)"; then
  failed "worktree-status-read-failed"
fi
if [[ -n "$STATUS" ]]; then
  echo "dirty"
  exit 1
fi

echo "clean"
