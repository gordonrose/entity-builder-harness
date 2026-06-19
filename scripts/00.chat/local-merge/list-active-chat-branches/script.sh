#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: List active chat branches with session metadata and relation to local main.
#   domain: local-merge
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

# shellcheck source=../../session-log/paths/lib.sh
source "$REPO_ROOT/scripts/00.chat/session-log/paths/lib.sh"

BASE_BRANCH="${1:-main}"

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  echo "ERROR: base branch does not exist: ${BASE_BRANCH}" >&2
  exit 1
fi

current_branch="$(git branch --show-current)"
tmp_dir="$(mktemp -d)"

cleanup() {
  rm -rf "$tmp_dir"
}

trap cleanup EXIT

if [ -z "$current_branch" ]; then
  echo "ERROR: current HEAD is detached." >&2
  exit 1
fi

printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "branch" "relation" "behind" "ahead" "layer" "mode" "status" "task"

git branch --format='%(refname:short)' | while IFS= read -r branch; do
  case "$branch" in
    chat/*)
      ;;
    *)
      continue
      ;;
  esac

  session_id="${branch#chat/}"
  log_file="$(chat_log_file_for_session "$session_id")"
  branch_log_file="${tmp_dir}/$(printf '%s\n' "$session_id" | tr -c 'A-Za-z0-9._-' '_').README.md"

  if [ -f "$log_file" ]; then
    layer="$(chat_log_metadata_value "$log_file" "layer")"
    mode="$(chat_log_metadata_value "$log_file" "mode")"
    status="$(chat_log_metadata_value "$log_file" "status")"
    task="$(chat_log_metadata_value "$log_file" "task")"
  elif git cat-file -e "${branch}:commitLogs/${session_id}/README.md" 2>/dev/null; then
    git show "${branch}:commitLogs/${session_id}/README.md" > "$branch_log_file"
    layer="$(chat_log_metadata_value "$branch_log_file" "layer")"
    mode="$(chat_log_metadata_value "$branch_log_file" "mode")"
    status="$(chat_log_metadata_value "$branch_log_file" "status")"
    task="$(chat_log_metadata_value "$branch_log_file" "task")"
  else
    layer="missing-log"
    mode="missing-log"
    status="missing-log"
    task="missing session log: ${log_file}"
  fi

  counts="$(git rev-list --left-right --count "${BASE_BRANCH}...${branch}")"
  behind="${counts%%	*}"
  ahead="${counts##*	}"

  if [ "$behind" = "0" ] && [ "$ahead" = "0" ]; then
    relation="even"
  elif [ "$behind" = "0" ]; then
    relation="ahead"
  elif [ "$ahead" = "0" ]; then
    relation="behind"
  else
    relation="diverged"
  fi

  if [ "$branch" = "$current_branch" ]; then
    branch="${branch}*"
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$branch" "$relation" "$behind" "$ahead" \
    "${layer:-unknown}" "${mode:-unknown}" "${status:-unknown}" "${task:-}"
done
