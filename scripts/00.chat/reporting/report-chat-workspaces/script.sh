#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.reporting.report-chat-workspaces
#   version: 3
#   status: active
#   created_on: "2026-06-16"
#   updated_on: "2026-11-05"
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
read_failed() { echo "ERROR: workspace-report-$1-read-failed" >&2; exit 2; }
observe() { local stage="$1"; shift; "$@" 2>/dev/null || read_failed "$stage"; }

CALLER_ROOT="$(observe root git rev-parse --show-toplevel)"
CALLER_ROOT="$(cd "$CALLER_ROOT" 2>/dev/null && pwd -P)" || read_failed root

# shellcheck source=../../worktree/paths/lib.sh
source "$CALLER_ROOT/scripts/00.chat/worktree/paths/lib.sh"
# shellcheck source=../../session-log/paths/lib.sh
source "$CALLER_ROOT/scripts/00.chat/session-log/paths/lib.sh"

REPO_ROOT="$(chat_worktree_repo_root "$CALLER_ROOT")"
chat_worktree_load_config "$REPO_ROOT"

if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/${BASE_BRANCH}" 2>/dev/null; then
  :
else
  reference_status=$?
  [ "$reference_status" -eq 1 ] || read_failed base-reference
  echo "ERROR: base branch does not exist" >&2
  exit 1
fi

printf 'Base branch: %s\n' "$BASE_BRANCH"
printf '%-64s %-8s %-8s %-8s %-10s %s\n' "branch" "ahead" "behind" "status" "log-head" "worktree"

branches="$(observe branch-list git -C "$REPO_ROOT" branch --format='%(refname:short)')"
while IFS= read -r branch; do
  case "$branch" in
    chat/*) ;;
    *) continue ;;
  esac

  session_id="${branch#chat/}"
  log_file="$(chat_log_file_for_session "$session_id")"
  branch_head="$(observe branch-head git -C "$REPO_ROOT" rev-parse --short "$branch")"
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

  ahead="$(observe comparison git -C "$REPO_ROOT" rev-list --count "${BASE_BRANCH}..${branch}")"
  behind="$(observe comparison git -C "$REPO_ROOT" rev-list --count "${branch}..${BASE_BRANCH}")"
  worktree_path="$(chat_worktree_path_for_existing_or_new_branch "$REPO_ROOT" "$branch")"
  status="absent"

  if [ -d "$worktree_path" ]; then
    git -C "$worktree_path" rev-parse --is-inside-work-tree >/dev/null 2>&1 || read_failed worktree-verification
    worktree_status="$(observe status git -C "$worktree_path" status --porcelain)"
    if [ -z "$worktree_status" ]; then
      status="clean"
    else
      status="dirty"
    fi
  fi

  printf '%-64s %-8s %-8s %-8s %-10s %s\n' "$branch" "$ahead" "$behind" "$status" "$log_head_state" "$worktree_path"
done <<< "$branches"
