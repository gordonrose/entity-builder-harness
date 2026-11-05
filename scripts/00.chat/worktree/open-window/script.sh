#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.worktree.open-window
#   version: 2
#   status: active
#   created_on: "2026-06-20"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: worktree
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Open a VS Code window for a chat-owned worktree.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.startup.start-chat-session
#     path: scripts/00.chat/startup/start-chat-session/script.sh
#   - id: chat.script.command.open-window
#     path: scripts/00.chat/command/open-window/script.sh
#   effects:
#   - read-only
usage() {
  cat <<'EOF'
Usage: open-window [worktree-path|session-log]

Opens the current chat worktree in a new VS Code window. If an argument is
provided, it may be a verified chat-owned worktree path or a session-log
README.md path.
EOF
}

# shellcheck source=../../session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

target="${1:-}"

if [ "${target:-}" = "-h" ] || [ "${target:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -gt 1 ]; then
  usage >&2
  exit 2
fi

resolve_current_worktree() {
  local branch session_id log_file worktree

  branch="$(git branch --show-current 2>/dev/null)" || { echo "ERROR: window-branch-read-failed" >&2; return 2; }
  if ! session_id="$(chat_session_id_from_branch "$branch")"; then
    echo "ERROR: current branch is not a chat branch" >&2
    echo "Pass a chat worktree path or session log path when running from the root worktree." >&2
    return 1
  fi

  log_file="$(chat_log_file_for_session "$session_id")" || return "$?"
  if [ ! -f "$log_file" ]; then
    echo "ERROR: missing chat log" >&2
    return 1
  fi

  worktree="$(chat_log_metadata_value "$log_file" "worktree")" || return "$?"
  if [ -z "${worktree// }" ]; then
    echo "ERROR: session log is missing worktree metadata" >&2
    return 1
  fi

  printf '%s\n' "$worktree"
}

normalize_shell_path() {
  local path_value="$1"

  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$path_value" 2>/dev/null && return 0
  fi

  printf '%s\n' "${path_value//\\//}"
}

canonical_dir() {
  local dir="$1"

  dir="$(normalize_shell_path "$dir")"
  cd "$dir" 2>/dev/null && pwd -P
}

resolve_target() {
  local candidate="$1"
  local candidate_path

  if [ -z "${candidate// }" ]; then
    resolve_current_worktree
    return
  fi

  candidate_path="$(normalize_shell_path "$candidate")"
  if [ -f "$candidate_path" ]; then
    chat_log_metadata_value "$candidate_path" "worktree"
    return
  fi

  printf '%s\n' "$candidate"
}

verify_chat_owned_worktree() {
  local candidate_path="$1"
  local target_root target_branch target_session_id log_file declared_branch declared_worktree declared_path declared_root

  candidate_path="$(normalize_shell_path "$candidate_path")"

  if [ ! -d "$candidate_path" ]; then
    echo "ERROR: chat worktree path does not exist" >&2
    return 1
  fi

  if ! git -C "$candidate_path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: path could not be verified as a git worktree" >&2
    return 1
  fi

  target_root="$(git -C "$candidate_path" rev-parse --show-toplevel 2>/dev/null)" || { echo "ERROR: window-root-read-failed" >&2; return 2; }
  target_root="$(canonical_dir "$target_root")" || { echo "ERROR: window-root-inaccessible" >&2; return 2; }
  target_branch="$(git -C "$target_root" branch --show-current 2>/dev/null)" || { echo "ERROR: window-target-branch-read-failed" >&2; return 2; }

  if ! target_session_id="$(chat_session_id_from_branch "$target_branch")"; then
    echo "ERROR: refusing to open non-chat worktree branch" >&2
    echo "Use the chat open-window command from a chat branch or pass a chat-owned worktree/session log." >&2
    return 1
  fi

  log_file="$(chat_log_file_for_session "$target_session_id")" || return "$?"
  log_file="$target_root/$log_file"
  if [ ! -f "$log_file" ]; then
    echo "ERROR: missing session log for chat worktree" >&2
    return 1
  fi

  declared_branch="$(chat_log_metadata_value "$log_file" "branch")" || return "$?"
  if [ "$declared_branch" != "$target_branch" ]; then
    echo "ERROR: session log branch does not match target worktree." >&2
    return 1
  fi

  declared_worktree="$(chat_log_metadata_value "$log_file" "worktree")" || return "$?"
  if [ -z "${declared_worktree// }" ]; then
    echo "ERROR: session log is missing worktree metadata" >&2
    return 1
  fi

  declared_path="$(normalize_shell_path "$declared_worktree")"
  if [ ! -d "$declared_path" ]; then
    echo "ERROR: declared chat worktree does not exist" >&2
    return 1
  fi

  declared_root="$(canonical_dir "$declared_path")" || { echo "ERROR: window-declared-worktree-inaccessible" >&2; return 2; }
  if [ "$declared_root" != "$target_root" ]; then
    echo "ERROR: refusing to open path that is not the declared chat-owned worktree." >&2
    return 1
  fi

  printf '%s\n' "$target_root"
}

WORKTREE_PATH="$(resolve_target "$target")"

if [ -z "${WORKTREE_PATH// }" ]; then
  echo "ERROR: could not resolve chat worktree path." >&2
  exit 1
fi

WORKTREE_PATH="$(verify_chat_owned_worktree "$WORKTREE_PATH")"

case "${CHAT_OPEN_WORKTREE_WINDOW:-open}" in
  open|"")
    ;;
  0|false|no|skip)
    echo "Skipping VS Code window open: $WORKTREE_PATH"
    exit 0
    ;;
  *)
    echo "ERROR: invalid CHAT_OPEN_WORKTREE_WINDOW value" >&2
    echo "Use open, skip, 0, false, or no." >&2
    exit 2
    ;;
esac

if ! command -v code >/dev/null 2>&1; then
  echo "WARNING: VS Code CLI 'code' not found; cannot open chat worktree window" >&2
  exit 0
fi

if code --new-window "$WORKTREE_PATH" >/dev/null 2>&1; then
  echo "Opened VS Code window: $WORKTREE_PATH"
else
  echo "WARNING: VS Code CLI failed to open chat worktree window; opening outcome is unconfirmed" >&2
fi
