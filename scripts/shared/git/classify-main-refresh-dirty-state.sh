#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  classify-main-refresh-dirty-state.sh [base-branch]

Classifies dirty worktree state before refreshing a chat branch from main.
The classifier reports state only; workflows decide what actions are allowed.
EOF
}

BASE_BRANCH="${1:-main}"

if [ $# -gt 1 ]; then
  usage >&2
  exit 2
fi

case "$BASE_BRANCH" in
  -h|--help)
    usage
    exit 0
    ;;
esac

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  echo "classification=unsupported-dirty"
  echo "recoverability=blocked"
  echo "reason=base branch does not exist: ${BASE_BRANCH}"
  exit 1
fi

# shellcheck source=../chat/session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

BRANCH="$(git branch --show-current)"

if [ -z "$BRANCH" ]; then
  echo "classification=unsupported-dirty"
  echo "recoverability=blocked"
  echo "reason=current HEAD is detached"
  exit 1
fi

SESSION_ID=""
LOG_FILE=""

if SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"
fi

SUMMARY_FILE="commitLogs/README.md"
STATUS_FILE="$(mktemp)"
DIRTY_FILE="$(mktemp)"
STAGED_FILE="$(mktemp)"
INCOMING_FILE="$(mktemp)"
OVERLAP_FILE="$(mktemp)"

cleanup() {
  rm -f "$STATUS_FILE" "$DIRTY_FILE" "$STAGED_FILE" "$INCOMING_FILE" "$OVERLAP_FILE"
}

trap cleanup EXIT

git status --porcelain > "$STATUS_FILE"

if [ ! -s "$STATUS_FILE" ]; then
  echo "classification=clean"
  echo "recoverability=normal-refresh"
  echo "reason=worktree is clean"
  exit 0
fi

awk '{ print substr($0, 4) }' "$STATUS_FILE" | sort -u > "$DIRTY_FILE"
awk 'substr($0, 1, 1) != " " && substr($0, 1, 1) != "?" { print substr($0, 4) }' \
  "$STATUS_FILE" | sort -u > "$STAGED_FILE"
git diff --name-only "HEAD...${BASE_BRANCH}" | sort -u > "$INCOMING_FILE"
comm -12 "$DIRTY_FILE" "$INCOMING_FILE" > "$OVERLAP_FILE"

emit_common() {
  echo "branch=${BRANCH}"
  echo "base_branch=${BASE_BRANCH}"
  if [ -n "$SESSION_ID" ]; then
    echo "session_id=${SESSION_ID}"
    echo "session_log=${LOG_FILE}"
  else
    echo "session_id="
    echo "session_log="
  fi
  echo "dirty_paths<<EOF"
  cat "$DIRTY_FILE"
  echo "EOF"
  echo "staged_paths<<EOF"
  cat "$STAGED_FILE"
  echo "EOF"
  echo "incoming_overlap_paths<<EOF"
  cat "$OVERLAP_FILE"
  echo "EOF"
}

path_count() {
  wc -l < "$1" | tr -d ' '
}

only_allowed_paths="yes"
repo_work_paths=""
other_commitlog_paths=""

while IFS= read -r path; do
  if [ -z "$path" ]; then
    continue
  fi

  if [ "$path" = "$SUMMARY_FILE" ]; then
    continue
  fi

  if [ -n "$LOG_FILE" ] && [ "$path" = "$LOG_FILE" ]; then
    continue
  fi

  only_allowed_paths="no"

  case "$path" in
    commitLogs/*/README.md)
      other_commitlog_paths="${other_commitlog_paths}${path}
"
      ;;
    *)
      repo_work_paths="${repo_work_paths}${path}
"
      ;;
  esac
done < "$DIRTY_FILE"

if [ "$only_allowed_paths" = "yes" ]; then
  dirty_count="$(path_count "$DIRTY_FILE")"

  if [ "$dirty_count" = "1" ] && grep -qx "$SUMMARY_FILE" "$DIRTY_FILE"; then
    if bash scripts/shared/chat/generate-commit-log-summary.sh --check >/dev/null 2>&1; then
      echo "classification=generated-commitlog-summary"
      echo "recoverability=recoverable-with-restore-regenerate"
      echo "reason=only generated aggregate commit log summary is dirty and it matches generator output"
      emit_common
      exit 0
    fi

    echo "classification=unsupported-dirty"
    echo "recoverability=blocked"
    echo "reason=aggregate commit log summary is dirty but does not match generator output"
    emit_common
    exit 0
  fi

  echo "classification=current-session-bookkeeping"
  echo "recoverability=checkpoint-or-preserve"
  echo "reason=dirty paths are limited to the current session log and aggregate commit log summary"
  emit_common
  exit 0
fi

if [ -n "${repo_work_paths// }" ]; then
  echo "classification=repo-work"
  echo "recoverability=checkpoint-required"
  echo "reason=dirty paths include normal repository work"
  emit_common
  exit 0
fi

echo "classification=unsupported-dirty"
echo "recoverability=blocked"
echo "reason=dirty paths are outside governed main-refresh recovery categories"
emit_common
