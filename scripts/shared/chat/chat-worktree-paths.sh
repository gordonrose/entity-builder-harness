#!/usr/bin/env bash

# agentic-script:
#   owner: 00.chat
#   purpose: Provide canonical chat worktree path and metadata helper functions.
#   domain: worktree
#   portability: llm-workbench-required
#   used_by:
#     - scripts/shared/chat/ensure-chat-worktree.sh
#     - scripts/shared/git/verify-local-convergence.sh
#   effects: read-only

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

chat_worktree_root_for_repo() {
  local repo_root="$1"
  local repo_slug

  repo_slug="$(chat_worktree_safe_name "$(basename "$repo_root")")"
  printf '%s\n' "${AGENTIC_CHAT_WORKTREE_ROOT:-${TMPDIR:-/tmp}/agentic-chat-worktrees/${repo_slug}-$(chat_worktree_repo_key "$repo_root")}"
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
