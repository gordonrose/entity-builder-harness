#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Report changed-path overlap between active worktree changes and chat branches.
#   domain: local-merge
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

tmp_dir="$(mktemp -d)"

cleanup() {
  rm -rf "$tmp_dir"
}

trap cleanup EXIT

labels_file="${tmp_dir}/labels"
current_branch="$(git branch --show-current)"

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

  git diff --name-only "${BASE_BRANCH}...${branch}" | sort -u > "$path_file"

  if [ -s "$path_file" ]; then
    printf '%s\t%s\n' "$label" "$path_file" >> "$labels_file"
  fi
}

write_worktree_paths() {
  local label="worktree:${current_branch}"
  local path_file="${tmp_dir}/$(safe_name "$label").paths"

  {
    git diff --name-only
    git diff --cached --name-only
    git ls-files --others --exclude-standard
  } | sort -u > "$path_file"

  if [ -s "$path_file" ]; then
    printf '%s\t%s\n' "$label" "$path_file" >> "$labels_file"
  fi
}

: > "$labels_file"

git branch --format='%(refname:short)' | while IFS= read -r branch; do
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

for left_index in $(seq 1 "$line_count"); do
  left_line="$(sed -n "${left_index}p" "$labels_file")"
  left_label="${left_line%%	*}"
  left_file="${left_line#*	}"

  right_start=$((left_index + 1))
  if [ "$right_start" -gt "$line_count" ]; then
    continue
  fi

  for right_index in $(seq "$right_start" "$line_count"); do
    right_line="$(sed -n "${right_index}p" "$labels_file")"
    right_label="${right_line%%	*}"
    right_file="${right_line#*	}"
    overlap_file="${tmp_dir}/overlap-${left_index}-${right_index}"

    comm -12 "$left_file" "$right_file" > "$overlap_file"

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
