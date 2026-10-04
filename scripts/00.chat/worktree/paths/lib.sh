#!/usr/bin/env bash

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.worktree.paths.lib
#   version: 2
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
chat_worktree_primary_path() {
  local repo_path="${1:-.}" primary_path

  primary_path="$(git -C "$repo_path" worktree list --porcelain | sed -n '1s/^worktree //p')"
  if [ -z "${primary_path// }" ]; then
    echo "ERROR: could not determine the primary worktree for: $repo_path" >&2
    return 1
  fi

  cd "$primary_path" && pwd -P
}

chat_worktree_repo_root() {
  chat_worktree_primary_path "${1:-.}"
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

chat_worktree_load_config() {
  local repo_root="$1"
  local env_file="$repo_root/.agentic/env.local"
  local supplied_override="no"
  local saved_override=""

  if [ "${AGENTIC_CHAT_WORKTREE_ROOT+x}" = "x" ]; then
    supplied_override="yes"
    saved_override="$AGENTIC_CHAT_WORKTREE_ROOT"
  fi

  if [ -f "$env_file" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  fi

  if [ "$supplied_override" = "yes" ]; then
    export AGENTIC_CHAT_WORKTREE_ROOT="$saved_override"
  fi
}

chat_worktree_root_for_repo() {
  local repo_root="$1"
  local repo_slug root_path

  repo_slug="$(chat_worktree_safe_name "$(basename "$repo_root")")"
  if [ -n "${AGENTIC_CHAT_WORKTREE_ROOT:-}" ]; then
    root_path="$AGENTIC_CHAT_WORKTREE_ROOT"
  else
    if [ -z "${HOME:-}" ]; then
      echo "ERROR: HOME is required to select the persistent chat worktree root." >&2
      return 1
    fi
    root_path="$HOME/projects/.chat-worktrees/${repo_slug}-$(chat_worktree_repo_key "$repo_root")"
  fi

  case "$root_path" in
    /*) ;;
    *)
      echo "ERROR: AGENTIC_CHAT_WORKTREE_ROOT must be an absolute path: $root_path" >&2
      return 1
      ;;
  esac

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

chat_worktree_registered_path_for_branch() {
  local repo_root="$1"
  local branch="$2"
  local path found_path="" found_count=0

  while IFS= read -r path; do
    [ -z "${path// }" ] && continue
    found_path="$path"
    found_count=$((found_count + 1))
  done < <(
    git -C "$repo_root" worktree list --porcelain \
      | awk -v branch="refs/heads/${branch}" '
          /^worktree / { path = substr($0, 10) }
          /^branch / && substr($0, 8) == branch { print path }
        '
  )

  if [ "$found_count" -eq 0 ]; then
    return 1
  fi

  if [ "$found_count" -ne 1 ]; then
    echo "ERROR: ambiguous registered worktrees for chat branch '$branch' in $repo_root." >&2
    return 2
  fi

  if [ ! -d "$found_path" ]; then
    echo "ERROR: registered chat worktree is unavailable: $found_path" >&2
    return 2
  fi

  cd "$found_path" && pwd -P
}

chat_worktree_path_for_existing_or_new_branch() {
  local repo_root="$1"
  local branch="$2"
  local status
  local registered_path

  set +e
  registered_path="$(chat_worktree_registered_path_for_branch "$repo_root" "$branch")"
  status=$?
  set -e

  case "$status" in
    0) printf '%s\n' "$registered_path" ;;
    1) chat_worktree_path_for_branch "$repo_root" "$branch" ;;
    *) return "$status" ;;
  esac
}

chat_worktree_metadata_value() {
  local log_file="$1"
  local key="$2"

  sed -n "/<!-- agentic-session/,/-->/s/^${key}: //p" "$log_file" | head -n 1
}
