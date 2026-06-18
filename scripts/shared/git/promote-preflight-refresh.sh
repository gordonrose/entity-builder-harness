#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  promote-preflight-refresh.sh <preflight-branch>

Fast-forwards the current chat branch to a tested preflight refresh branch,
then removes the temporary preflight worktree and deletes the preflight branch.
The current worktree and preflight worktree must both be clean.
EOF
}

if [ $# -ne 1 ]; then
  usage >&2
  exit 2
fi

PREFLIGHT_BRANCH="$1"

case "$PREFLIGHT_BRANCH" in
  agentic/preflight/*/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9])
    ;;
  *)
    echo "ERROR: refusing non-preflight branch: ${PREFLIGHT_BRANCH}" >&2
    echo "Expected branch created by preflight-main-refresh.sh." >&2
    exit 1
    ;;
esac

if ! git show-ref --verify --quiet "refs/heads/${PREFLIGHT_BRANCH}"; then
  echo "ERROR: preflight branch does not exist: ${PREFLIGHT_BRANCH}" >&2
  exit 1
fi

preflight_worktrees_for_branch() {
  local branch="$1"

  git worktree list --porcelain \
    | awk -v branch="refs/heads/${branch}" '
      /^worktree / { path = substr($0, 10) }
      /^branch / && substr($0, 8) == branch { print path }
    '
}

worktree_count() {
  awk 'NF { count += 1 } END { print count + 0 }'
}

cleanup_stale_preflight_siblings() {
  local promoted_branch="$1"
  local prefix="${promoted_branch%/*}/"
  local sibling sibling_worktrees sibling_worktree_count sibling_worktree

  while IFS= read -r sibling; do
    if [ -z "$sibling" ] || [ "$sibling" = "$promoted_branch" ]; then
      continue
    fi

    case "$sibling" in
      "$prefix"*)
        ;;
      *)
        continue
        ;;
    esac

    if ! git merge-base --is-ancestor "$sibling" HEAD; then
      echo "stale_preflight_skipped=${sibling} reason=unique-commits-not-in-promoted-head"
      continue
    fi

    sibling_worktrees="$(preflight_worktrees_for_branch "$sibling")"
    sibling_worktree_count="$(printf '%s\n' "$sibling_worktrees" | worktree_count)"

    if [ "$sibling_worktree_count" -gt 1 ]; then
      echo "stale_preflight_skipped=${sibling} reason=multiple-worktrees"
      continue
    fi

    if [ "$sibling_worktree_count" = "1" ]; then
      sibling_worktree="$(printf '%s\n' "$sibling_worktrees" | awk 'NF { print; exit }')"
      sibling_worktree="$(cd "$sibling_worktree" && pwd -P)"

      if [ "$sibling_worktree" = "$CURRENT_WORKTREE" ]; then
        echo "stale_preflight_skipped=${sibling} reason=active-worktree"
        continue
      fi

      if [ -n "$(git -C "$sibling_worktree" status --porcelain)" ]; then
        echo "stale_preflight_skipped=${sibling} reason=dirty-worktree"
        continue
      fi

      git worktree remove "$sibling_worktree"
      echo "stale_preflight_removed=${sibling} worktree=${sibling_worktree}"
    else
      echo "stale_preflight_removed=${sibling} worktree="
    fi

    git branch -d "$sibling" >/dev/null
  done < <(git branch --format='%(refname:short)')
}

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

PREFLIGHT_HEAD="$(git rev-parse "$PREFLIGHT_BRANCH")"

if ! git merge-base --is-ancestor HEAD "$PREFLIGHT_BRANCH"; then
  echo "ERROR: preflight branch does not descend from current HEAD." >&2
  echo "Current branch may have moved since preflight." >&2
  exit 1
fi

PREFLIGHT_WORKTREES="$(preflight_worktrees_for_branch "$PREFLIGHT_BRANCH")"

PREFLIGHT_WORKTREE_COUNT="$(printf '%s\n' "$PREFLIGHT_WORKTREES" | worktree_count)"

if [ "$PREFLIGHT_WORKTREE_COUNT" != "1" ]; then
  echo "ERROR: expected exactly one preflight worktree for ${PREFLIGHT_BRANCH}; found ${PREFLIGHT_WORKTREE_COUNT}." >&2
  exit 1
fi

PREFLIGHT_WORKTREE="$(printf '%s\n' "$PREFLIGHT_WORKTREES" | awk 'NF { print; exit }')"
CURRENT_WORKTREE="$(pwd -P)"
PREFLIGHT_WORKTREE="$(cd "$PREFLIGHT_WORKTREE" && pwd -P)"

if [ "$PREFLIGHT_WORKTREE" = "$CURRENT_WORKTREE" ]; then
  echo "ERROR: refusing to remove the active chat worktree as preflight cleanup." >&2
  exit 1
fi

if [ -n "$(git -C "$PREFLIGHT_WORKTREE" status --porcelain)" ]; then
  echo "ERROR: refusing to clean dirty preflight worktree: ${PREFLIGHT_WORKTREE}" >&2
  git -C "$PREFLIGHT_WORKTREE" status --short >&2
  exit 1
fi

git merge --ff-only "$PREFLIGHT_BRANCH"

PROMOTED_COMMIT="$(git rev-parse HEAD)"

if [ "$PROMOTED_COMMIT" != "$PREFLIGHT_HEAD" ]; then
  echo "ERROR: promotion ended at ${PROMOTED_COMMIT}, expected ${PREFLIGHT_HEAD}." >&2
  exit 1
fi

git worktree remove "$PREFLIGHT_WORKTREE"
git branch -d "$PREFLIGHT_BRANCH" >/dev/null
cleanup_stale_preflight_siblings "$PREFLIGHT_BRANCH"

echo "Promoted preflight refresh:"
echo "current_branch=${CURRENT_BRANCH}"
echo "preflight_branch=${PREFLIGHT_BRANCH}"
echo "preflight_worktree=${PREFLIGHT_WORKTREE}"
echo "promoted_commit=${PROMOTED_COMMIT}"
echo "cleanup_result=removed-worktree-and-deleted-branch"
