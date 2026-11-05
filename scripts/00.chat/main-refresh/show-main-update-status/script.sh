#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.main-refresh.show-main-update-status
#   version: 1
#   status: active
#   created_on: "2026-06-16"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: main-refresh
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Show whether local chat branches are ahead of or behind the base branch.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-refresh-from-main
#     path: .agentic/00.chat/workflows/chat-refresh-from-main.md
#   - id: harness.script.run-governed-script
#     path: scripts/01.harness/run-governed-script.sh
#   effects:
#   - read-only

BASE_BRANCH="${1:-main}"

failed() {
  echo "ERROR: $1" >&2
  exit 1
}

if git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}" 2>/dev/null; then
  :
else
  status=$?
  if [ "$status" -eq 1 ]; then
    failed "refresh-status-base-missing"
  fi
  failed "refresh-status-base-read-failed"
fi

if ! current_branch="$(git branch --show-current 2>/dev/null)"; then
  failed "refresh-status-branch-read-failed"
fi

if [ -z "$current_branch" ]; then
  echo "ERROR: current HEAD is detached." >&2
  exit 1
fi

if ! remotes="$(git remote 2>/dev/null)"; then
  failed "refresh-status-remotes-read-failed"
fi
if ! branches="$(git branch --format='%(refname:short)' 2>/dev/null)"; then
  failed "refresh-status-branches-read-failed"
fi

echo "Base branch: ${BASE_BRANCH}"
echo "Current branch: ${current_branch}"

if [ -n "$remotes" ]; then
  echo "Remote freshness: remotes configured; run git fetch --prune before relying on remote comparisons."
else
  echo "Remote freshness: no remotes configured; comparisons are local only."
fi

echo
printf '%-72s %8s %8s %s\n' "branch" "behind" "ahead" "state"

while IFS= read -r branch; do
  if [ -z "$branch" ]; then
    continue
  fi
  if [ "$branch" = "$BASE_BRANCH" ]; then
    continue
  fi

  if ! counts="$(git rev-list --left-right --count "${BASE_BRANCH}...${branch}" 2>/dev/null)"; then
    failed "refresh-status-comparison-read-failed"
  fi
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
done <<< "$branches"
