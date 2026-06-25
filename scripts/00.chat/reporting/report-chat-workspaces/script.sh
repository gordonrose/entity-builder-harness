#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.reporting.report-chat-workspaces
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: reporting
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Report chat branches, log head state, and worktree status.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-cleanup
#     path: .agentic/00.chat/workflows/chat-cleanup.md
#   - id: chat.workflows.chat-promote-to-main
#     path: .agentic/00.chat/workflows/chat-promote-to-main.md
#   effects:
#   - read-only

BASE_BRANCH="${1:-main}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

# shellcheck source=../../worktree/paths/lib.sh
source "$REPO_ROOT/scripts/00.chat/worktree/paths/lib.sh"
# shellcheck source=../../session-log/paths/lib.sh
source "$REPO_ROOT/scripts/00.chat/session-log/paths/lib.sh"

if ! git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  echo "ERROR: base branch does not exist: $BASE_BRANCH" >&2
  exit 1
fi

printf 'Base branch: %s\n' "$BASE_BRANCH"
printf '%-64s %-8s %-8s %-8s %-10s %s\n' "branch" "ahead" "behind" "status" "log-head" "worktree"

git -C "$REPO_ROOT" branch --format='%(refname:short)' | while IFS= read -r branch; do
  case "$branch" in
    chat/*) ;;
    *) continue ;;
  esac

  session_id="${branch#chat/}"
  log_file="$(chat_log_file_for_session "$session_id")"
  branch_head="$(git -C "$REPO_ROOT" rev-parse --short "$branch")"
  recorded_head=""
  log_head_state="missing"

  if [ -f "$log_file" ]; then
    recorded_head="$(chat_worktree_metadata_value "$log_file" "latest_commit_sha")"
    if [ -z "${recorded_head// }" ]; then
      log_head_state="unrecorded"
    elif [ "${recorded_head:0:7}" = "$branch_head" ]; then
      log_head_state="matches"
    else
      log_head_state="differs"
    fi
  fi

  ahead="$(git -C "$REPO_ROOT" rev-list --count "${BASE_BRANCH}..${branch}")"
  behind="$(git -C "$REPO_ROOT" rev-list --count "${branch}..${BASE_BRANCH}")"
  worktree_path="$(chat_worktree_path_for_branch "$REPO_ROOT" "$branch")"
  status="absent"

  if [ -d "$worktree_path/.git" ] || git -C "$worktree_path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if [ -z "$(git -C "$worktree_path" status --porcelain)" ]; then
      status="clean"
    else
      status="dirty"
    fi
  fi

  printf '%-64s %-8s %-8s %-8s %-10s %s\n' "$branch" "$ahead" "$behind" "$status" "$log_head_state" "$worktree_path"
done
