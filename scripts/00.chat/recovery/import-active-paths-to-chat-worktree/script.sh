#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Import explicit paths from an active worktree into a session's chat-owned worktree.
#   domain: recovery
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/recovery/import-active-paths-to-chat-worktree/README.md
#     - scripts/shared/git/stage-active-worktree-paths.sh
#   effects: writes-files, stages-files

usage() {
  cat <<'EOF'
Usage:
  script.sh --session-log <path> [--source-worktree <path>] -- <path>...

Imports explicit repository-relative paths from the source worktree into the
chat-owned worktree recorded in a session log, then stages those paths in the
chat-owned worktree.

This is recovery tooling for edits made in the wrong worktree. Normal chat task
work should happen directly in the chat-owned worktree.
EOF
}

SESSION_LOG="${AGENTIC_SESSION_LOG:-}"
SOURCE_WORKTREE="${AGENTIC_ACTIVE_WORKTREE:-}"

while [ $# -gt 0 ]; do
  case "$1" in
    --session-log)
      if [ $# -lt 2 ]; then
        usage >&2
        exit 2
      fi
      SESSION_LOG="$2"
      shift 2
      ;;
    --source-worktree)
      if [ $# -lt 2 ]; then
        usage >&2
        exit 2
      fi
      SOURCE_WORKTREE="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

validate_path() {
  local path="$1"

  if [ -z "${path// }" ]; then
    echo "ERROR: empty path is not allowed." >&2
    exit 1
  fi

  case "$path" in
    /*|../*|*/../*|*/..|.)
      echo "ERROR: path must be a repository-relative path without '..': $path" >&2
      exit 1
      ;;
  esac
}

for path in "$@"; do
  validate_path "$path"
done

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

# shellcheck source=../../worktree/paths/lib.sh
source "$REPO_ROOT/scripts/00.chat/worktree/paths/lib.sh"
# shellcheck source=../../session-log/paths/lib.sh
source "$REPO_ROOT/scripts/00.chat/session-log/paths/lib.sh"

if [ -z "${SOURCE_WORKTREE// }" ]; then
  SOURCE_WORKTREE="$REPO_ROOT"
fi

SOURCE_WORKTREE="$(cd "$SOURCE_WORKTREE" && pwd -P)"

if [ -z "${SESSION_LOG// }" ]; then
  CURRENT_BRANCH="$(git -C "$SOURCE_WORKTREE" branch --show-current)"
  if ! SESSION_ID="$(chat_session_id_from_branch "$CURRENT_BRANCH")"; then
    echo "ERROR: --session-log is required when the source worktree is not on a chat branch." >&2
    exit 1
  fi
  SESSION_LOG="$(chat_log_file_for_session "$SESSION_ID")"
fi

case "$SESSION_LOG" in
  /*) ;;
  *) SESSION_LOG="$REPO_ROOT/$SESSION_LOG" ;;
esac

if [ ! -f "$SESSION_LOG" ]; then
  echo "ERROR: missing chat session log: $SESSION_LOG" >&2
  exit 1
fi

TARGET_BRANCH="$(chat_worktree_metadata_value "$SESSION_LOG" "branch")"
if [ -z "${TARGET_BRANCH// }" ]; then
  echo "ERROR: session log is missing branch metadata: $SESSION_LOG" >&2
  exit 1
fi

case "$TARGET_BRANCH" in
  chat/*) ;;
  *)
    echo "ERROR: session branch is not a chat branch: $TARGET_BRANCH" >&2
    exit 1
    ;;
esac

TARGET_WORKTREE="$(chat_worktree_metadata_value "$SESSION_LOG" "worktree")"
if [ -z "${TARGET_WORKTREE// }" ]; then
  TARGET_WORKTREE="$(chat_worktree_path_for_branch "$REPO_ROOT" "$TARGET_BRANCH")"
fi

case "$TARGET_WORKTREE" in
  /*) ;;
  *) TARGET_WORKTREE="$REPO_ROOT/$TARGET_WORKTREE" ;;
esac

if [ ! -d "$TARGET_WORKTREE" ]; then
  echo "ERROR: chat-owned worktree is missing: $TARGET_WORKTREE" >&2
  echo "Run scripts/00.chat/worktree/ensure-chat-worktree/script.sh first." >&2
  exit 1
fi

TARGET_WORKTREE="$(cd "$TARGET_WORKTREE" && pwd -P)"

if [ "$SOURCE_WORKTREE" = "$TARGET_WORKTREE" ]; then
  echo "ERROR: source worktree and chat-owned worktree are the same path." >&2
  echo "Normal task work should be staged directly in the chat-owned worktree." >&2
  exit 1
fi

if ! git -C "$TARGET_WORKTREE" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: chat-owned worktree path is not a git worktree: $TARGET_WORKTREE" >&2
  exit 1
fi

TARGET_CURRENT_BRANCH="$(git -C "$TARGET_WORKTREE" branch --show-current)"
if [ "$TARGET_CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
  echo "ERROR: chat-owned worktree is on '$TARGET_CURRENT_BRANCH', expected '$TARGET_BRANCH': $TARGET_WORKTREE" >&2
  exit 1
fi

if [ -n "$(git -C "$TARGET_WORKTREE" status --porcelain)" ]; then
  echo "ERROR: chat-owned worktree is dirty; refusing to import over existing work." >&2
  echo "Commit, checkpoint, or inspect the target worktree before recovery import." >&2
  exit 1
fi

import_path() {
  local path="$1"
  local source_path="$SOURCE_WORKTREE/$path"
  local target_path="$TARGET_WORKTREE/$path"
  local target_parent

  if [ -e "$source_path" ] || [ -L "$source_path" ]; then
    target_parent="$(dirname "$target_path")"
    mkdir -p "$target_parent"
    rm -rf "$target_path"
    cp -a "$source_path" "$target_path"
    git -C "$TARGET_WORKTREE" add -A -- "$path"
  else
    git -C "$TARGET_WORKTREE" rm -r --ignore-unmatch -- "$path" >/dev/null 2>&1 || true
  fi
}

for path in "$@"; do
  import_path "$path"
done

echo "Imported active worktree paths into chat-owned worktree:"
printf '%s\n' "$@"
echo "Target worktree: $TARGET_WORKTREE"
