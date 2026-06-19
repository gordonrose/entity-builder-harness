#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: shared-git
#   purpose: Run commit-boundary commands in an isolated worktree for a chat branch.
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0009-allow-automatic-session-branch-commit-context.md
#     - scripts/shared/git/smoke-test-with-chat-branch.sh
#   effects: worktrees, writes-files

usage() {
  cat <<'EOF'
Usage:
  with-chat-branch.sh --session-log <path> -- <command> [args...]
  with-chat-branch.sh <session-log> -- <command> [args...]
  with-chat-branch.sh -- <command> [args...]

Runs a commit-boundary command inside a deterministic isolated worktree for the
local chat/* branch recorded in a chat session log. The active worktree is not
switched, staged, cleaned, or otherwise modified by this helper.

Environment:
  AGENTIC_SESSION_LOG          Default session log path.
  AGENTIC_CHAT_WORKTREE_ROOT   Override reusable worktree root.
EOF
}

SESSION_LOG="${AGENTIC_SESSION_LOG:-}"
SESSION_LOG_FROM_ARGS="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --session-log)
      if [ $# -lt 2 ]; then
        usage >&2
        exit 2
      fi
      SESSION_LOG="$2"
      SESSION_LOG_FROM_ARGS="yes"
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
      if [ "$SESSION_LOG_FROM_ARGS" = "no" ]; then
        SESSION_LOG="$1"
        SESSION_LOG_FROM_ARGS="yes"
        shift
      else
        usage >&2
        exit 2
      fi
      ;;
  esac
done

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

# shellcheck source=../chat/session-log-paths.sh
source "$REPO_ROOT/scripts/shared/chat/session-log-paths.sh"

if [ -z "${SESSION_LOG// }" ]; then
  CURRENT_BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"
  if ! SESSION_ID="$(chat_session_id_from_branch "$CURRENT_BRANCH")"; then
    echo "ERROR: no session log provided and current branch is not a chat branch: $CURRENT_BRANCH" >&2
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

TARGET_BRANCH="$(
  sed -n '/<!-- agentic-session/,/-->/s/^branch: //p' "$SESSION_LOG" | head -n 1
)"

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

if ! git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/${TARGET_BRANCH}"; then
  echo "ERROR: session branch does not exist locally: $TARGET_BRANCH" >&2
  exit 1
fi

deny_direct_command() {
  local command_name="$1"
  local git_subcommand="${2:-}"
  local branch_flag="${3:-}"

  if [ "$command_name" != "git" ]; then
    return 0
  fi

  case "$git_subcommand" in
    push|merge|rebase|reset|checkout|switch|restore|clean|cherry-pick|revert)
      echo "ERROR: with-chat-branch.sh does not authorize git $git_subcommand." >&2
      exit 1
      ;;
    worktree)
      echo "ERROR: with-chat-branch.sh does not authorize nested git worktree operations." >&2
      exit 1
      ;;
    branch)
      case "$branch_flag" in
        -d|-D|--delete|-m|-M|--move|-f|--force)
          echo "ERROR: with-chat-branch.sh does not authorize branch deletion, moving, or forcing." >&2
          exit 1
          ;;
      esac
      ;;
  esac
}

deny_direct_command "$@"

repo_key() {
  printf '%s' "$REPO_ROOT" | cksum | awk '{print $1}'
}

safe_name() {
  printf '%s' "$1" | sed 's#[^A-Za-z0-9._-]#_#g'
}

absolute_git_common_dir() {
  git -C "$1" rev-parse --path-format=absolute --git-common-dir
}

worktree_branch_for_path() {
  git -C "$1" symbolic-ref --quiet --short HEAD 2>/dev/null || true
}

REPO_SLUG="$(safe_name "$(basename "$REPO_ROOT")")"
BRANCH_SLUG="$(safe_name "$TARGET_BRANCH")"
BRANCH_KEY="$(printf '%s' "$TARGET_BRANCH" | cksum | awk '{print $1}')"
WORKTREE_ROOT="${AGENTIC_CHAT_WORKTREE_ROOT:-${TMPDIR:-/tmp}/agentic-chat-worktrees/${REPO_SLUG}-$(repo_key)}"
WORKTREE_PATH="${WORKTREE_ROOT}/${BRANCH_SLUG}-${BRANCH_KEY}"

MAIN_COMMON_DIR="$(absolute_git_common_dir "$REPO_ROOT")"

branch_worktrees="$(
  git -C "$REPO_ROOT" worktree list --porcelain \
    | awk -v branch="refs/heads/${TARGET_BRANCH}" '
      /^worktree / { path = substr($0, 10) }
      /^branch / && substr($0, 8) == branch { print path }
    '
)"

ADD_FORCE_ARGS=()

while IFS= read -r branch_worktree; do
  if [ -z "${branch_worktree// }" ]; then
    continue
  fi

  branch_worktree="$(cd "$branch_worktree" && pwd -P)"

  case "$branch_worktree" in
    "$WORKTREE_PATH")
      ;;
    "$REPO_ROOT")
      ADD_FORCE_ARGS=(--force)
      ;;
    *)
      echo "ERROR: session branch is already checked out outside the active and isolated worktrees:" >&2
      echo "$branch_worktree" >&2
      echo "Expected isolated path:" >&2
      echo "$WORKTREE_PATH" >&2
      exit 1
      ;;
  esac
done <<< "$branch_worktrees"

if [ -e "$WORKTREE_PATH" ]; then
  if ! git -C "$WORKTREE_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: isolated worktree path exists but is not a git worktree: $WORKTREE_PATH" >&2
    exit 1
  fi

  WORKTREE_PATH="$(cd "$WORKTREE_PATH" && pwd -P)"
  WORKTREE_COMMON_DIR="$(absolute_git_common_dir "$WORKTREE_PATH")"
  if [ "$WORKTREE_COMMON_DIR" != "$MAIN_COMMON_DIR" ]; then
    echo "ERROR: isolated worktree path belongs to a different repository: $WORKTREE_PATH" >&2
    exit 1
  fi

  WORKTREE_BRANCH="$(worktree_branch_for_path "$WORKTREE_PATH")"
  if [ "$WORKTREE_BRANCH" != "$TARGET_BRANCH" ]; then
    echo "ERROR: isolated worktree is on '$WORKTREE_BRANCH', expected '$TARGET_BRANCH': $WORKTREE_PATH" >&2
    exit 1
  fi
else
  mkdir -p "$WORKTREE_ROOT"
  if ! git -C "$REPO_ROOT" worktree add "${ADD_FORCE_ARGS[@]}" --quiet "$WORKTREE_PATH" "$TARGET_BRANCH"; then
    echo "ERROR: could not create isolated worktree: $WORKTREE_PATH" >&2
    exit 1
  fi
fi

export AGENTIC_SESSION_LOG="$SESSION_LOG"
export AGENTIC_ACTIVE_WORKTREE="$REPO_ROOT"
export AGENTIC_CHAT_WORKTREE_PATH="$WORKTREE_PATH"

cd "$WORKTREE_PATH"
"$@"
