#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Test-refresh a chat branch from main in a temporary preflight worktree.
#   domain: git
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#     - scripts/shared/git/smoke-test-main-refresh-preflight.sh
#   effects: branches, worktrees, commits

usage() {
  cat <<'EOF'
Usage:
  preflight-main-refresh.sh [base-branch]

Creates a temporary worktree and branch from the current chat branch, then
attempts to merge the base branch there. The active chat worktree is left
untouched. If the merge succeeds, the preflight branch contains the merge
commit and can be promoted with promote-preflight-refresh.sh.
EOF
}

BASE_BRANCH="${1:-main}"

if [ $# -gt 1 ]; then
  usage >&2
  exit 2
fi

case "$BASE_BRANCH" in
  -h|--help)
    usage
    exit 0
    ;;
esac

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  echo "ERROR: base branch does not exist: ${BASE_BRANCH}" >&2
  exit 1
fi

CLASSIFICATION="$(bash scripts/shared/git/classify-main-refresh-dirty-state.sh "$BASE_BRANCH" | sed -n 's/^classification=//p' | head -n 1)"

if [ "$CLASSIFICATION" != "clean" ]; then
  echo "ERROR: preflight requires a clean chat worktree." >&2
  echo "Classifier reported: ${CLASSIFICATION}" >&2
  echo "Checkpoint or recover dirty state before preflighting main refresh." >&2
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

CURRENT_HEAD="$(git rev-parse HEAD)"
SAFE_BRANCH="$(printf '%s' "$CURRENT_BRANCH" | tr -c 'A-Za-z0-9._-' '-')"
STAMP="$(date -u +%Y%m%d%H%M%S)"
PREFLIGHT_BRANCH="agentic/preflight/${SAFE_BRANCH}/${STAMP}"
PREFLIGHT_ROOT="${TMPDIR:-/tmp}/agentic-main-refresh-preflight"
PREFLIGHT_WORKTREE="${PREFLIGHT_ROOT}/${SAFE_BRANCH}-${STAMP}"
MERGE_OUT="${PREFLIGHT_ROOT}/${SAFE_BRANCH}-${STAMP}.merge.out"
MERGE_ERR="${PREFLIGHT_ROOT}/${SAFE_BRANCH}-${STAMP}.merge.err"

mkdir -p "$PREFLIGHT_ROOT"

git branch "$PREFLIGHT_BRANCH" "$CURRENT_HEAD"
git worktree add -q "$PREFLIGHT_WORKTREE" "$PREFLIGHT_BRANCH"

set +e
git -C "$PREFLIGHT_WORKTREE" merge --no-ff --no-edit "$BASE_BRANCH" \
  > "$MERGE_OUT" 2> "$MERGE_ERR"
MERGE_STATUS="$?"
set -e

echo "preflight_branch=${PREFLIGHT_BRANCH}"
echo "preflight_worktree=${PREFLIGHT_WORKTREE}"
echo "source_branch=${CURRENT_BRANCH}"
echo "source_head=${CURRENT_HEAD}"
echo "base_branch=${BASE_BRANCH}"

if [ "$MERGE_STATUS" -ne 0 ]; then
  echo "result=conflict-or-failed"
  echo "conflict_paths<<EOF"
  git -C "$PREFLIGHT_WORKTREE" diff --name-only --diff-filter=U | sort -u
  echo "EOF"
  echo "Merge output:"
  sed 's/^/  /' "$MERGE_ERR"
  exit 1
fi

echo "result=clean-merge"
echo "preflight_head=$(git -C "$PREFLIGHT_WORKTREE" rev-parse HEAD)"
echo "Promote with:"
echo "  bash scripts/shared/git/promote-preflight-refresh.sh ${PREFLIGHT_BRANCH}"
