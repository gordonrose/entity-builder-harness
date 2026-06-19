#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Find the Codex JSONL transcript for a chat session.
#   portability: llm-workbench-required
#   used_by:
#     - scripts/shared/chat/register-codex-session-log.sh
#     - scripts/shared/git/record-chat-commit.sh
#   effects: read-only

usage() {
  cat <<'EOF'
Usage:
  discover-codex-session-log.sh <session-id> [session-log-path]

Finds the Codex JSONL session log that contains the chat session id, branch, or
session log path. Prints the newest matching path.
EOF
}

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  usage >&2
  exit 2
fi

SESSION_ID="$1"
SESSION_LOG_PATH="${2:-}"
CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"

if [ -z "${SESSION_ID// }" ]; then
  echo "ERROR: session id is required." >&2
  exit 2
fi

if [ ! -d "$CODEX_HOME_DIR" ]; then
  echo "ERROR: Codex home directory does not exist: $CODEX_HOME_DIR" >&2
  exit 1
fi

TMP_MATCHES="$(mktemp)"
trap 'rm -f "$TMP_MATCHES"' EXIT

append_match() {
  local file="$1"
  local mtime

  if ! mtime="$(stat -c '%Y' "$file" 2>/dev/null)"; then
    return
  fi

  printf '%s\t%s\n' "$mtime" "$file" >> "$TMP_MATCHES"
}

matches_file() {
  local file="$1"

  grep -Fq "$SESSION_ID" "$file" && return 0
  grep -Fq "chat/${SESSION_ID}" "$file" && return 0

  if [ -n "${SESSION_LOG_PATH// }" ]; then
    grep -Fq "$SESSION_LOG_PATH" "$file" && return 0
  fi

  return 1
}

for root in "$CODEX_HOME_DIR/sessions" "$CODEX_HOME_DIR/archived_sessions"; do
  if [ ! -d "$root" ]; then
    continue
  fi

  while IFS= read -r -d '' file; do
    if matches_file "$file"; then
      append_match "$file"
    fi
  done < <(find "$root" -type f -name '*.jsonl' -print0)
done

if [ ! -s "$TMP_MATCHES" ]; then
  echo "ERROR: no Codex session log matched session: $SESSION_ID" >&2
  exit 1
fi

sort -rn "$TMP_MATCHES" | head -n 1 | cut -f2-
