#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Create or verify the chat-owned worktree for a session branch.
#   domain: worktree
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-start.md
#     - scripts/shared/chat/request-initialization/start-chat-session.sh
#   effects: worktrees

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

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

# shellcheck source=chat-worktree-paths.sh
source "$REPO_ROOT/scripts/shared/chat/chat-worktree-paths.sh"

SESSION_LOG="$1"
case "$SESSION_LOG" in
  /*) ;;
  *) SESSION_LOG="$REPO_ROOT/$SESSION_LOG" ;;
esac

if [ ! -f "$SESSION_LOG" ]; then
  echo "ERROR: missing chat session log: $SESSION_LOG" >&2
  exit 1
fi

BRANCH="$(chat_worktree_metadata_value "$SESSION_LOG" "branch")"
if [ -z "${BRANCH// }" ]; then
  echo "ERROR: session log is missing branch metadata: $SESSION_LOG" >&2
  exit 1
fi

case "$BRANCH" in
  chat/*) ;;
  *)
    echo "ERROR: session branch is not a chat branch: $BRANCH" >&2
    exit 1
    ;;
esac

if ! git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  echo "ERROR: session branch does not exist locally: $BRANCH" >&2
  exit 1
fi

WORKTREE_PATH="$(chat_worktree_path_for_branch "$REPO_ROOT" "$BRANCH")"
WORKTREE_ROOT="${WORKTREE_PATH%/*}"
PRIMARY_PATH="$(chat_worktree_primary_path)"
PRIMARY_PATH="$(cd "$PRIMARY_PATH" && pwd -P)"

branch_worktrees="$(
  git -C "$REPO_ROOT" worktree list --porcelain \
    | awk -v branch="refs/heads/${BRANCH}" '
      /^worktree / { path = substr($0, 10) }
      /^branch / && substr($0, 8) == branch { print path }
    '
)"

while IFS= read -r branch_worktree; do
  if [ -z "${branch_worktree// }" ]; then
    continue
  fi

  branch_worktree="$(cd "$branch_worktree" && pwd -P)"

  if [ "$branch_worktree" = "$WORKTREE_PATH" ]; then
    continue
  fi

  if [ "$branch_worktree" = "$PRIMARY_PATH" ]; then
    echo "ERROR: session branch is checked out in the root integration worktree:" >&2
    echo "$branch_worktree" >&2
    echo "Switch the root worktree away from the chat branch before creating the chat-owned worktree." >&2
    exit 1
  fi

  echo "ERROR: session branch is already checked out in another worktree:" >&2
  echo "$branch_worktree" >&2
  echo "Expected chat-owned worktree:" >&2
  echo "$WORKTREE_PATH" >&2
  exit 1
done <<< "$branch_worktrees"

if [ -e "$WORKTREE_PATH" ]; then
  if ! git -C "$WORKTREE_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: chat worktree path exists but is not a git worktree: $WORKTREE_PATH" >&2
    exit 1
  fi

  current_branch="$(git -C "$WORKTREE_PATH" branch --show-current)"
  if [ "$current_branch" != "$BRANCH" ]; then
    echo "ERROR: chat worktree is on '$current_branch', expected '$BRANCH': $WORKTREE_PATH" >&2
    exit 1
  fi
else
  mkdir -p "$WORKTREE_ROOT"
  git -C "$REPO_ROOT" worktree add --quiet "$WORKTREE_PATH" "$BRANCH"
fi

printf '%s\n' "$WORKTREE_PATH"
