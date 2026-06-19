#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: shared-git
#   purpose: Check whether a chat branch includes the latest local base branch.
#   portability: llm-workbench-required
#   used_by:
#     - docs/harness/architecture/adrs/0011-use-chat-owned-worktrees-for-local-convergence.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

usage() {
  cat <<'EOF'
Usage:
  check-chat-branch-freshness.sh [--base <branch>] [--require-fresh] [<branch>]

Reports whether a chat branch includes the latest local base branch. With
--require-fresh, exits non-zero when the branch is behind or diverged.
EOF
}

BASE_BRANCH="main"
REQUIRE_FRESH="no"
TARGET_BRANCH=""

while [ $# -gt 0 ]; do
  case "$1" in
    --base)
      if [ $# -lt 2 ]; then
        usage >&2
        exit 2
      fi
      BASE_BRANCH="$2"
      shift 2
      ;;
    --require-fresh)
      REQUIRE_FRESH="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [ -n "$TARGET_BRANCH" ]; then
        usage >&2
        exit 2
      fi
      TARGET_BRANCH="$1"
      shift
      ;;
  esac
done

if [ -z "$TARGET_BRANCH" ]; then
  TARGET_BRANCH="$(git branch --show-current)"
fi

if [ -z "$TARGET_BRANCH" ]; then
  echo "ERROR: target branch is empty or HEAD is detached." >&2
  exit 1
fi

case "$TARGET_BRANCH" in
  chat/*) ;;
  *)
    echo "ERROR: target branch is not a chat branch: $TARGET_BRANCH" >&2
    exit 1
    ;;
esac

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  echo "ERROR: base branch does not exist: $BASE_BRANCH" >&2
  exit 1
fi

if ! git show-ref --verify --quiet "refs/heads/${TARGET_BRANCH}"; then
  echo "ERROR: target branch does not exist: $TARGET_BRANCH" >&2
  exit 1
fi

ahead="$(git rev-list --count "${BASE_BRANCH}..${TARGET_BRANCH}")"
behind="$(git rev-list --count "${TARGET_BRANCH}..${BASE_BRANCH}")"

echo "Base branch: $BASE_BRANCH"
echo "Chat branch: $TARGET_BRANCH"
echo "Ahead of base: $ahead"
echo "Behind base: $behind"

if [ "$behind" = "0" ]; then
  if [ "$ahead" = "0" ]; then
    echo "Freshness: even"
  else
    echo "Freshness: fresh-ahead"
  fi
  exit 0
fi

if [ "$ahead" = "0" ]; then
  echo "Freshness: behind"
else
  echo "Freshness: diverged"
fi

if [ "$REQUIRE_FRESH" = "yes" ]; then
  exit 1
fi
