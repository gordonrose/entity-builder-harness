#!/usr/bin/env bash

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.worktree.paths.lib
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: worktree
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Provide canonical chat worktree path and metadata helper functions.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.reporting.report-chat-workspaces
#     path: scripts/00.chat/reporting/report-chat-workspaces/script.sh
#   - id: chat.script.startup.start-chat-session
#     path: scripts/00.chat/startup/start-chat-session/script.sh
#   - id: chat.script.worktree.ensure-chat-worktree
#     path: scripts/00.chat/worktree/ensure-chat-worktree/script.sh
#   effects:
#   - read-only
chat_worktree_repo_root() {
  local repo_root

  repo_root="$(git rev-parse --show-toplevel)"
  cd "$repo_root" && pwd -P
}

chat_worktree_repo_key() {
  local repo_root="$1"

  printf '%s' "$repo_root" | cksum | awk '{print $1}'
}

chat_worktree_safe_name() {
  printf '%s' "$1" | sed 's#[^A-Za-z0-9._-]#_#g'
}

chat_worktree_shell_path() {
  local path_value="$1"

  if command -v cygpath >/dev/null 2>&1; then
    cygpath -m "$path_value" 2>/dev/null && return 0
  fi

  printf '%s\n' "${path_value//\\//}"
}

chat_worktree_root_for_repo() {
  local repo_root="$1"
  local repo_slug root_path

  repo_slug="$(chat_worktree_safe_name "$(basename "$repo_root")")"
  root_path="${AGENTIC_CHAT_WORKTREE_ROOT:-${TMPDIR:-/tmp}/agentic-chat-worktrees/${repo_slug}-$(chat_worktree_repo_key "$repo_root")}"
  chat_worktree_shell_path "$root_path"
}

chat_worktree_path_for_branch() {
  local repo_root="$1"
  local branch="$2"
  local branch_slug branch_key

  branch_slug="$(chat_worktree_safe_name "$branch")"
  branch_key="$(printf '%s' "$branch" | cksum | awk '{print $1}')"
  printf '%s/%s-%s\n' "$(chat_worktree_root_for_repo "$repo_root")" "$branch_slug" "$branch_key"
}

chat_worktree_primary_path() {
  git worktree list --porcelain | sed -n '1s/^worktree //p'
}

chat_worktree_metadata_value() {
  local log_file="$1"
  local key="$2"

  sed -n "/<!-- agentic-session/,/-->/s/^${key}: //p" "$log_file" | head -n 1
}
