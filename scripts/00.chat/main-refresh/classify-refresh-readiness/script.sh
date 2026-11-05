#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.main-refresh.classify-refresh-readiness
#   version: 1
#   status: active
#   created_on: "2026-06-17"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: main-refresh
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Classify whether the current chat worktree is ready to refresh from main.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-refresh-from-main
#     path: .agentic/00.chat/workflows/chat-refresh-from-main.md
#   - id: chat.script.main-refresh.rehearse-refresh-from-main
#     path: scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh
#   effects:
#   - read-only

usage() {
  cat <<'EOF'
Usage:
  script.sh [base-ref]

Classifies dirty worktree state before refreshing a chat branch from a base ref.
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

blocked() {
  echo "classification=unsupported-dirty"
  echo "recoverability=blocked"
  echo "reason=$1"
  exit 1
}

if git rev-parse --verify --quiet "${BASE_BRANCH}^{commit}" >/dev/null 2>&1; then
  :
else
  status=$?
  if [ "$status" -eq 1 ]; then
    blocked "refresh-base-unresolved"
  fi
  blocked "refresh-base-read-failed"
fi

# shellcheck source=../../session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

if ! BRANCH="$(git branch --show-current 2>/dev/null)"; then
  blocked "refresh-branch-read-failed"
fi

if [ -z "$BRANCH" ]; then
  echo "classification=unsupported-dirty"
  echo "recoverability=blocked"
  echo "reason=current HEAD is detached"
  exit 1
fi

SESSION_ID=""
LOG_FILE=""

if SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  if ! LOG_FILE="$(chat_log_file_for_session "$SESSION_ID" 2>/dev/null)"; then
    blocked "refresh-session-lookup-failed"
  fi
fi

if ! OBSERVATION_DIR="$(mktemp -d 2>/dev/null)"; then
  blocked "refresh-workspace-create-failed"
fi
STATUS_FILE="$OBSERVATION_DIR/status"
DIRTY_FILE="$OBSERVATION_DIR/dirty"
STAGED_FILE="$OBSERVATION_DIR/staged"
INCOMING_FILE="$OBSERVATION_DIR/incoming"
OVERLAP_FILE="$OBSERVATION_DIR/overlap"

cleanup() {
  rm -f "$STATUS_FILE" "$DIRTY_FILE" "$STAGED_FILE" "$INCOMING_FILE" "$OVERLAP_FILE"
  rmdir "$OBSERVATION_DIR"
}

trap cleanup EXIT

if ! { git status --porcelain > "$STATUS_FILE"; } 2>/dev/null; then
  blocked "refresh-status-read-failed"
fi

if [ ! -s "$STATUS_FILE" ]; then
  echo "classification=clean"
  echo "recoverability=normal-refresh"
  echo "reason=worktree is clean"
  exit 0
fi

if ! { awk '{ print substr($0, 4) }' "$STATUS_FILE" | sort -u > "$DIRTY_FILE"; } 2>/dev/null; then
  blocked "refresh-dirty-paths-read-failed"
fi
if ! { awk 'substr($0, 1, 1) != " " && substr($0, 1, 1) != "?" { print substr($0, 4) }' \
  "$STATUS_FILE" | sort -u > "$STAGED_FILE"; } 2>/dev/null; then
  blocked "refresh-staged-paths-read-failed"
fi
if ! { git diff --name-only "HEAD...${BASE_BRANCH}" | sort -u > "$INCOMING_FILE"; } 2>/dev/null; then
  blocked "refresh-incoming-paths-read-failed"
fi
if ! { comm -12 "$DIRTY_FILE" "$INCOMING_FILE" > "$OVERLAP_FILE"; } 2>/dev/null; then
  blocked "refresh-overlap-read-failed"
fi

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

only_allowed_paths="yes"
repo_work_paths=""
other_commitlog_paths=""

while IFS= read -r path; do
  if [ -z "$path" ]; then
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
  echo "classification=current-session-bookkeeping"
  echo "recoverability=checkpoint-or-preserve"
  echo "reason=dirty paths are limited to the current session log"
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
