#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.main-refresh.rehearse-refresh-from-main
#   version: 1
#   status: active
#   created_on: "2026-06-17"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: main-refresh
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Rehearse refreshing a chat branch from main in a temporary worktree.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-refresh-from-main
#     path: .agentic/00.chat/workflows/chat-refresh-from-main.md
#   - id: chat.script.main-refresh.rehearse-refresh-from-main.smoke-test
#     path: scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh
#   effects:
#   - branches
#   - commits
#   - worktrees

usage() {
  cat <<'EOF'
Usage:
  script.sh [base-ref]

Creates a temporary worktree and branch from the current chat branch, then
attempts to merge the base ref there. The active chat worktree is left
untouched. If the merge succeeds, the preflight branch contains the merge
commit and can be applied with apply-rehearsed-refresh.
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

if git rev-parse --verify --quiet "${BASE_BRANCH}^{commit}" >/dev/null 2>&1; then
  :
else
  status=$?
  if [ "$status" -eq 1 ]; then
    echo "ERROR: refresh-base-unresolved" >&2
  else
    echo "ERROR: refresh-base-read-failed" >&2
  fi
  exit 1
fi

if READINESS="$(bash scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh "$BASE_BRANCH" 2>/dev/null)"; then
  READINESS_STATUS=0
else
  READINESS_STATUS=$?
fi
CLASSIFICATION=""
READINESS_FAILURE="refresh-readiness-check-failed"
while IFS= read -r line; do
  case "$line" in
    classification=clean|classification=current-session-bookkeeping|classification=repo-work|classification=unsupported-dirty)
      CLASSIFICATION="${line#classification=}" ;;
    reason=refresh-base-unresolved|reason=refresh-base-read-failed|reason=refresh-branch-read-failed|reason=refresh-session-lookup-failed|reason=refresh-workspace-create-failed|reason=refresh-status-read-failed|reason=refresh-dirty-paths-read-failed|reason=refresh-staged-paths-read-failed|reason=refresh-incoming-paths-read-failed|reason=refresh-overlap-read-failed)
      READINESS_FAILURE="${line#reason=}" ;;
  esac
done <<< "$READINESS"
if [ "$READINESS_STATUS" -ne 0 ]; then
  echo "ERROR: $READINESS_FAILURE" >&2
  exit 1
fi
if [ -z "$CLASSIFICATION" ]; then
  echo "ERROR: refresh-readiness-result-invalid" >&2
  exit 1
fi

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
RAW_SAFE_BRANCH="$(printf '%s' "$CURRENT_BRANCH" | tr -c 'A-Za-z0-9._-' '-')"
SAFE_BRANCH_PREFIX="$(printf '%s' "$RAW_SAFE_BRANCH" | cut -c1-48 | sed -E 's/[-.]+$//')"
if [ -z "${SAFE_BRANCH_PREFIX// }" ]; then
  SAFE_BRANCH_PREFIX="chat"
fi
SAFE_BRANCH="${SAFE_BRANCH_PREFIX}-$(git rev-parse --short=12 HEAD)"
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
echo "Apply with:"
echo "  bash scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh ${PREFLIGHT_BRANCH}"
