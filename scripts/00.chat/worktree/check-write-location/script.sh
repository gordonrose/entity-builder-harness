#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.worktree.check-write-location
#   version: 2
#   status: active
#   layer: 00.chat
#   domain: worktree
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Enforce task writes from chat-owned worktrees instead of the root integration
#     worktree.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.worktree.check-write-location.readme
#     path: scripts/00.chat/worktree/check-write-location/README.md
#   effects:
#   - read-only
usage() {
  cat <<'EOF'
Usage:
  check-write-location.sh [--allow-root-maintenance]

Fails when task writes would run from the root integration worktree. Chat task
work must run from that chat branch's canonical chat-owned worktree.

Set AGENTIC_ALLOW_ROOT_WRITE=1 only for explicit root maintenance operations.
EOF
}

ALLOW_ROOT_MAINTENANCE="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --allow-root-maintenance)
      ALLOW_ROOT_MAINTENANCE="yes"
      shift
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
done

CALLER_ROOT="$(git rev-parse --show-toplevel)"
CALLER_ROOT="$(cd "$CALLER_ROOT" && pwd -P)"

# shellcheck source=../paths/lib.sh
source "$CALLER_ROOT/scripts/00.chat/worktree/paths/lib.sh"
# shellcheck source=../../session-log/paths/lib.sh
source "$CALLER_ROOT/scripts/00.chat/session-log/paths/lib.sh"

PRIMARY_PATH="$(chat_worktree_primary_path "$CALLER_ROOT")"
chat_worktree_load_config "$PRIMARY_PATH"
BRANCH="$(git -C "$CALLER_ROOT" branch --show-current)"

if [ "$CALLER_ROOT" = "$PRIMARY_PATH" ]; then
  if [ "${AGENTIC_ALLOW_ROOT_WRITE:-}" = "1" ] || [ "$ALLOW_ROOT_MAINTENANCE" = "yes" ]; then
    echo "root-maintenance-allowed"
    exit 0
  fi

  echo "ERROR: refusing task write in root integration worktree: $CALLER_ROOT" >&2
  echo "Use the chat-owned worktree for chat work." >&2
  exit 1
fi

case "$BRANCH" in
  chat/*) ;;
  *)
    echo "ERROR: current worktree is not on a chat branch: $BRANCH" >&2
    exit 1
    ;;
esac

set +e
EXPECTED_PATH="$(chat_worktree_registered_path_for_branch "$PRIMARY_PATH" "$BRANCH")"
registered_status=$?
set -e
if [ "$registered_status" -eq 1 ]; then
  echo "ERROR: no registered chat worktree exists for branch '$BRANCH'." >&2
  exit 1
elif [ "$registered_status" -ne 0 ]; then
  exit "$registered_status"
fi

if [ "$CALLER_ROOT" != "$EXPECTED_PATH" ]; then
  echo "ERROR: current chat branch is not in its registered chat worktree." >&2
  echo "Current:  $CALLER_ROOT" >&2
  echo "Expected: $EXPECTED_PATH" >&2
  exit 1
fi

SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"
SESSION_LOG="$CALLER_ROOT/$(chat_log_file_for_session "$SESSION_ID")"
if [ ! -f "$SESSION_LOG" ]; then
  echo "ERROR: missing session log for current chat branch: $SESSION_LOG" >&2
  exit 1
fi
if [ "$(chat_worktree_metadata_value "$SESSION_LOG" "branch")" != "$BRANCH" ]; then
  echo "ERROR: session log branch metadata does not match current branch: $SESSION_LOG" >&2
  exit 1
fi
RECORDED_WORKTREE="$(chat_worktree_metadata_value "$SESSION_LOG" "worktree")"
if ! RECORDED_WORKTREE="$(cd "$RECORDED_WORKTREE" 2>/dev/null && pwd -P)"; then
  echo "ERROR: session log records an unavailable worktree: $RECORDED_WORKTREE" >&2
  exit 1
fi
if [ "$RECORDED_WORKTREE" != "$CALLER_ROOT" ]; then
  echo "ERROR: session log worktree metadata does not match current worktree." >&2
  exit 1
fi

echo "chat-worktree"
