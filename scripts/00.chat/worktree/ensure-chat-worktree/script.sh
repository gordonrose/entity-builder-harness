#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.worktree.ensure-chat-worktree
#   version: 3
#   status: active
#   created_on: "2026-06-16"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: worktree
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Create or verify the chat-owned worktree for a session branch.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   - id: chat.script.startup.start-chat-session
#     path: scripts/00.chat/startup/start-chat-session/script.sh
#   effects:
#   - worktrees
usage() {
  cat <<'EOF'
Usage:
  ensure-chat-worktree.sh <session-log>

Creates or verifies the canonical chat-owned worktree for the chat branch named
in a session log. The root worktree is an integration console; task work should
happen in the returned chat worktree path.
EOF
}

if [ $# -ne 1 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage >&2
  exit 2
fi

failed() { echo "ERROR: $1" >&2; exit 2; }
CALLER_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || failed "worktree-root-read-failed"
CALLER_ROOT="$(cd "$CALLER_ROOT" && pwd -P)" || failed "worktree-root-inaccessible"

# shellcheck source=../paths/lib.sh
source "$CALLER_ROOT/scripts/00.chat/worktree/paths/lib.sh"

REPO_ROOT="$(chat_worktree_repo_root "$CALLER_ROOT")"
chat_worktree_load_config "$REPO_ROOT"

SESSION_LOG="$1"
case "$SESSION_LOG" in
  /*) ;;
  *) SESSION_LOG="$CALLER_ROOT/$SESSION_LOG" ;;
esac

if [ ! -f "$SESSION_LOG" ]; then
  echo "ERROR: missing chat session log" >&2
  exit 1
fi

SESSION_ROOT="$(git -C "$(dirname "$SESSION_LOG")" rev-parse --show-toplevel 2>/dev/null)" || failed "worktree-session-root-read-failed"
if [ -z "${SESSION_ROOT// }" ]; then
  echo "ERROR: session log is outside a Git worktree" >&2
  exit 1
fi
SESSION_PRIMARY="$(chat_worktree_repo_root "$SESSION_ROOT")"
if [ "$SESSION_PRIMARY" != "$REPO_ROOT" ]; then
  echo "ERROR: session log belongs to a different repository" >&2
  exit 1
fi

BRANCH="$(chat_worktree_metadata_value "$SESSION_LOG" "branch")"
if [ -z "${BRANCH// }" ]; then
  echo "ERROR: session log is missing branch metadata" >&2
  exit 1
fi

case "$BRANCH" in
  chat/*) ;;
  *)
    echo "ERROR: session branch is not a chat branch" >&2
    exit 1
    ;;
esac

if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/${BRANCH}" 2>/dev/null; then
  :
else
  reference_status=$?
  [ "$reference_status" -eq 1 ] || failed "worktree-branch-reference-read-failed"
  echo "ERROR: session branch does not exist locally" >&2
  exit 1
fi

RECORDED_WORKTREE="$(chat_worktree_metadata_value "$SESSION_LOG" "worktree")"
if [ -z "${RECORDED_WORKTREE// }" ]; then
  echo "ERROR: session log is missing worktree metadata" >&2
  exit 1
fi
case "$RECORDED_WORKTREE" in
  /*) ;;
  *) RECORDED_WORKTREE="$(dirname "$SESSION_LOG")/$RECORDED_WORKTREE" ;;
esac

registered_status=0
CREATED_WORKTREE="no"
set +e
WORKTREE_PATH="$(chat_worktree_registered_path_for_branch "$REPO_ROOT" "$BRANCH")"
registered_status=$?
set -e

if [ "$registered_status" -eq 0 ]; then
  if [ "$WORKTREE_PATH" = "$REPO_ROOT" ]; then
    echo "ERROR: session branch is checked out in the root integration worktree" >&2
    exit 1
  fi
  if ! RECORDED_CANONICAL="$(cd "$RECORDED_WORKTREE" 2>/dev/null && pwd -P)"; then
    echo "ERROR: session log records an unavailable worktree" >&2
    exit 1
  fi
  if [ "$RECORDED_CANONICAL" != "$WORKTREE_PATH" ]; then
    echo "ERROR: registered worktree does not match session metadata." >&2
    exit 1
  fi
elif [ "$registered_status" -eq 1 ]; then
  WORKTREE_PATH="$(chat_worktree_path_for_branch "$REPO_ROOT" "$BRANCH")"
  if [ "$RECORDED_WORKTREE" != "$WORKTREE_PATH" ]; then
    echo "ERROR: session log records a worktree, but no matching worktree is registered." >&2
    echo "Refusing to create a different worktree for this existing session." >&2
    exit 1
  fi
  if [ -e "$WORKTREE_PATH" ]; then
    echo "ERROR: chat worktree destination exists but is not registered" >&2
    exit 1
  fi
  if ! mkdir -p "${WORKTREE_PATH%/*}" 2>/dev/null; then
    echo "ERROR: cannot create persistent chat worktree root" >&2
    exit 1
  fi
  if [ ! -w "${WORKTREE_PATH%/*}" ]; then
    echo "ERROR: persistent chat worktree root is not writable" >&2
    exit 1
  fi
  if git -C "$REPO_ROOT" worktree add --quiet "$WORKTREE_PATH" "$BRANCH" >/dev/null 2>&1; then
    :
  else
    creation_status=$?
    echo "ERROR: worktree-creation-failed; effect=unknown; inspect registration and destination before retrying" >&2
    exit "$creation_status"
  fi
  CREATED_WORKTREE="yes"
else
  exit "$registered_status"
fi

if ! git -C "$WORKTREE_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: registered chat worktree could not be verified as a Git worktree" >&2
  exit 1
fi
current_branch="$(git -C "$WORKTREE_PATH" branch --show-current 2>/dev/null)" || failed "worktree-created-branch-read-failed"
if [ "$current_branch" != "$BRANCH" ]; then
  echo "ERROR: chat worktree is not on the expected branch" >&2
  exit 1
fi

if [ "$CREATED_WORKTREE" = "yes" ]; then
  {
    echo "Created worktree: $WORKTREE_PATH"
    echo "Inspect the new worktree:"
    printf '  cd %q\n' "$WORKTREE_PATH"
    echo "Open it in a new VS Code window:"
    printf '  (cd %q && npm run chat -- open-window)\n' "$WORKTREE_PATH"
  } >&2
fi

printf '%s\n' "$WORKTREE_PATH"
