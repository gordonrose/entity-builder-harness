#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  promote-preflight-refresh.sh <preflight-branch>

Fast-forwards the current chat branch to a tested preflight refresh branch.
The current worktree must be clean and the preflight branch must descend from
the current HEAD.
EOF
}

if [ $# -ne 1 ]; then
  usage >&2
  exit 2
fi

PREFLIGHT_BRANCH="$1"

if ! git show-ref --verify --quiet "refs/heads/${PREFLIGHT_BRANCH}"; then
  echo "ERROR: preflight branch does not exist: ${PREFLIGHT_BRANCH}" >&2
  exit 1
fi

CURRENT_BRANCH="$(git branch --show-current)"

case "$CURRENT_BRANCH" in
  chat/*)
    ;;
  *)
    echo "ERROR: current branch is not a chat branch: ${CURRENT_BRANCH}" >&2
    exit 1
    ;;
esac

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: refusing to promote into a dirty chat worktree." >&2
  git status --short >&2
  exit 1
fi

if ! git merge-base --is-ancestor HEAD "$PREFLIGHT_BRANCH"; then
  echo "ERROR: preflight branch does not descend from current HEAD." >&2
  echo "Current branch may have moved since preflight." >&2
  exit 1
fi

git merge --ff-only "$PREFLIGHT_BRANCH"

echo "Promoted preflight refresh:"
echo "Current branch: ${CURRENT_BRANCH}"
echo "Preflight branch: ${PREFLIGHT_BRANCH}"
