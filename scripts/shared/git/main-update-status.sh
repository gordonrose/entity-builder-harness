#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Report local branch ahead/behind state relative to a base branch.
#   domain: git
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

BASE_BRANCH="${1:-main}"

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  echo "ERROR: base branch does not exist: ${BASE_BRANCH}" >&2
  exit 1
fi

current_branch="$(git branch --show-current)"

if [ -z "$current_branch" ]; then
  echo "ERROR: current HEAD is detached." >&2
  exit 1
fi

echo "Base branch: ${BASE_BRANCH}"
echo "Current branch: ${current_branch}"

if git remote | grep -q .; then
  echo "Remote freshness: remotes configured; run git fetch --prune before relying on remote comparisons."
else
  echo "Remote freshness: no remotes configured; comparisons are local only."
fi

echo
printf '%-72s %8s %8s %s\n' "branch" "behind" "ahead" "state"

git branch --format='%(refname:short)' | while IFS= read -r branch; do
  if [ "$branch" = "$BASE_BRANCH" ]; then
    continue
  fi

  counts="$(git rev-list --left-right --count "${BASE_BRANCH}...${branch}")"
  behind="${counts%%	*}"
  ahead="${counts##*	}"

  if [ "$behind" = "0" ] && [ "$ahead" = "0" ]; then
    state="even"
  elif [ "$behind" = "0" ]; then
    state="ahead"
  elif [ "$ahead" = "0" ]; then
    state="behind"
  else
    state="diverged"
  fi

  printf '%-72s %8s %8s %s\n' "$branch" "$behind" "$ahead" "$state"
done
