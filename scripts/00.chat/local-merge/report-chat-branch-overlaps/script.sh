#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.local-merge.report-chat-branch-overlaps
#   version: 2
#   status: active
#   created_on: "2026-06-16"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: local-merge
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Report changed-path overlap between active worktree changes and chat branches.
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

read_failed() { echo "ERROR: branch-overlap-read-failed; stage=$1." >&2; exit 2; }
observe() { local stage="$1"; shift; "$@" 2>/dev/null || read_failed "$stage"; }
if git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}" 2>/dev/null; then :; else
  status=$?
  [ "$status" -eq 1 ] || read_failed base-reference
  echo "ERROR: base branch does not exist." >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"

cleanup() {
  rm -rf "$tmp_dir"
}

trap cleanup EXIT

labels_file="${tmp_dir}/labels"
current_branch="$(observe current-branch git branch --show-current)"

if [ -z "$current_branch" ]; then
  echo "ERROR: current HEAD is detached." >&2
  exit 1
fi

safe_name() {
  printf '%s\n' "$1" | tr -c 'A-Za-z0-9._-' '_'
}

write_branch_paths() {
  local label="$1"
  local branch="$2"
  local path_file="${tmp_dir}/$(safe_name "$label").paths"

  observe branch-paths git diff --name-only "${BASE_BRANCH}...${branch}" | observe path-sort sort -u > "$path_file"

  if [ -s "$path_file" ]; then
    printf '%s\t%s\n' "$label" "$path_file" >> "$labels_file"
  fi
}

write_worktree_paths() {
  local label="worktree:${current_branch}"
  local path_file="${tmp_dir}/$(safe_name "$label").paths"

  {
    observe worktree-paths git diff --name-only
    observe staged-paths git diff --cached --name-only
    observe untracked-paths git ls-files --others --exclude-standard
  } | observe path-sort sort -u > "$path_file"

  if [ -s "$path_file" ]; then
    printf '%s\t%s\n' "$label" "$path_file" >> "$labels_file"
  fi
}

: > "$labels_file"

observe branch-list git branch --format='%(refname:short)' | while IFS= read -r branch; do
  case "$branch" in
    chat/*)
      write_branch_paths "$branch" "$branch"
      ;;
  esac
done

write_worktree_paths

if [ ! -s "$labels_file" ]; then
  echo "No branch-only or worktree path changes found relative to ${BASE_BRANCH}."
  exit 0
fi

echo "Base branch: ${BASE_BRANCH}"
echo "Current branch: ${current_branch}"
echo
echo "Changed path sets:"
while IFS="$(printf '\t')" read -r label path_file; do
  count="$(wc -l < "$path_file" | tr -d ' ')"
  printf '%5s  %s\n' "$count" "$label"
done < "$labels_file"

echo
echo "Overlaps:"

overlap_count=0
line_count="$(wc -l < "$labels_file" | tr -d ' ')"

for ((left_index=1; left_index<=line_count; left_index++)); do
  left_line="$(observe label-read sed -n "${left_index}p" "$labels_file")"
  left_label="${left_line%%	*}"
  left_file="${left_line#*	}"

  right_start=$((left_index + 1))
  if [ "$right_start" -gt "$line_count" ]; then
    continue
  fi

  for ((right_index=right_start; right_index<=line_count; right_index++)); do
    right_line="$(observe label-read sed -n "${right_index}p" "$labels_file")"
    right_label="${right_line%%	*}"
    right_file="${right_line#*	}"
    overlap_file="${tmp_dir}/overlap-${left_index}-${right_index}"

    observe path-comparison comm -12 "$left_file" "$right_file" > "$overlap_file"

    if [ -s "$overlap_file" ]; then
      overlap_count=$((overlap_count + 1))
      overlap_paths="$(wc -l < "$overlap_file" | tr -d ' ')"
      printf '\n%s <-> %s (%s paths)\n' "$left_label" "$right_label" "$overlap_paths"
      sed 's/^/  /' "$overlap_file"
    fi
  done
done

if [ "$overlap_count" -eq 0 ]; then
  echo "No overlapping changed paths found."
fi
