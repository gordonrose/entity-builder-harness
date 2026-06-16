#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

usage() {
  cat <<'EOF'
Usage: rename-current-chat-log-folder.sh <short-summary>

Renames the current chat session log folder to a shorter summary while keeping
the branch name and session metadata stable.
EOF
}

if [ $# -lt 1 ]; then
  usage >&2
  exit 2
fi

SUMMARY="$*"

if [ -z "${SUMMARY// }" ]; then
  echo "ERROR: provide a non-empty summary." >&2
  exit 2
fi

BRANCH="$(git branch --show-current)"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch: $BRANCH" >&2
  exit 1
fi

LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE" >&2
  exit 1
fi

STAMP="${SESSION_ID:0:16}"
SLUG="$(printf '%s' "$SUMMARY" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g' \
  | sed -E 's/^-+|-+$//g' \
  | cut -c1-40)"

if [ -z "$SLUG" ]; then
  echo "ERROR: summary must contain at least one ASCII letter or number." >&2
  exit 2
fi

CURRENT_DIR="${LOG_FILE%/README.md}"
PARENT_DIR="${CURRENT_DIR%/*}"
TARGET_DIR="${PARENT_DIR}/${STAMP}-${SLUG}"
TARGET_FILE="${TARGET_DIR}/README.md"

if [ "$CURRENT_DIR" = "$TARGET_DIR" ]; then
  echo "Chat log folder already matches: $CURRENT_DIR"
  exit 0
fi

if [ -e "$TARGET_DIR" ]; then
  echo "ERROR: target commit log folder already exists: $TARGET_DIR" >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  && git ls-files --error-unmatch "$LOG_FILE" >/dev/null 2>&1; then
  git mv "$CURRENT_DIR" "$TARGET_DIR"
else
  mv "$CURRENT_DIR" "$TARGET_DIR"
fi

tmp="$(mktemp)"
awk -v stamp="$STAMP" -v slug="$SLUG" '
  NR == 1 && /^# Chat Session:/ {
    print "# Chat Session: " stamp " " slug
    next
  }
  { print }
' "$TARGET_FILE" > "$tmp"
mv "$tmp" "$TARGET_FILE"

bash scripts/shared/chat/generate-commit-log-summary.sh >/dev/null

echo "Renamed chat log folder:"
echo "  from: $CURRENT_DIR"
echo "  to:   $TARGET_DIR"
