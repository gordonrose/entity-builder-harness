#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Mirror explicit paths from the active worktree and stage them in an isolated chat worktree.
#   domain: git
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0009-allow-automatic-session-branch-commit-context.md
#     - scripts/shared/git/smoke-test-with-chat-branch.sh
#   effects: writes-files, stages-files

usage() {
  cat <<'EOF'
Usage:
  stage-active-worktree-paths.sh <path>...

Stages explicit paths in the current isolated worktree by mirroring them from
AGENTIC_ACTIVE_WORKTREE. Run through with-chat-branch.sh.
EOF
}

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

if [ -z "${AGENTIC_ACTIVE_WORKTREE:-}" ]; then
  echo "ERROR: AGENTIC_ACTIVE_WORKTREE is not set. Run through with-chat-branch.sh." >&2
  exit 1
fi

ACTIVE_WORKTREE="$(cd "$AGENTIC_ACTIVE_WORKTREE" && pwd -P)"
ISOLATED_WORKTREE="$(git rev-parse --show-toplevel)"
ISOLATED_WORKTREE="$(cd "$ISOLATED_WORKTREE" && pwd -P)"

if [ "$ACTIVE_WORKTREE" = "$ISOLATED_WORKTREE" ]; then
  echo "ERROR: active and isolated worktrees are the same path." >&2
  exit 1
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

mirror_path() {
  local path="$1"
  local source_path="$ACTIVE_WORKTREE/$path"
  local target_path="$ISOLATED_WORKTREE/$path"
  local target_parent

  validate_path "$path"

  if [ -e "$source_path" ] || [ -L "$source_path" ]; then
    target_parent="$(dirname "$target_path")"
    mkdir -p "$target_parent"

    if [ -d "$source_path" ] && [ ! -L "$source_path" ]; then
      rm -rf "$target_path"
      cp -a "$source_path" "$target_path"
    else
      rm -rf "$target_path"
      cp -a "$source_path" "$target_path"
    fi

    git add -A -- "$path"
  else
    git rm -r --ignore-unmatch -- "$path" >/dev/null
    git add -A -- "$path"
  fi
}

for path in "$@"; do
  mirror_path "$path"
done

echo "Staged active worktree paths in isolated worktree:"
printf '%s\n' "$@"
