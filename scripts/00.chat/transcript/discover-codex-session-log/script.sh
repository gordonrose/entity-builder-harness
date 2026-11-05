#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.transcript.discover-codex-session-log
#   version: 1
#   status: active
#   created_on: "2026-06-18"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: transcript
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Find the Codex JSONL transcript for a chat session.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.transcript.register-codex-session-log
#     path: scripts/00.chat/transcript/register-codex-session-log/script.sh
#   - id: chat.script.session-log.record-chat-commit
#     path: scripts/00.chat/session-log/record-chat-commit/script.sh
#   effects:
#   - read-only

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
  echo "ERROR: transcript-home-absent" >&2
  exit 1
fi

if ! TMP_DISCOVERY="$(mktemp -d 2>/dev/null)"; then
  echo "ERROR: transcript-workspace-failed" >&2
  exit 3
fi
TMP_MATCHES="$TMP_DISCOVERY/matches"
trap 'rm -rf "$TMP_DISCOVERY"' EXIT
: > "$TMP_MATCHES"

append_match() {
  local file="$1"
  local mtime

  if ! mtime="$(stat -c '%Y' "$file" 2>/dev/null)"; then
    if ! mtime="$(stat -f '%m' "$file" 2>/dev/null)"; then
      echo "ERROR: transcript-stat-failed" >&2
      return 3
    fi
  fi

  if [ -z "${mtime// }" ]; then
    echo "ERROR: transcript-stat-failed" >&2
    return 3
  fi

  printf '%s\t%s\n' "$mtime" "$file" >> "$TMP_MATCHES"
}

matches_file() {
  local file="$1" status
  local -a patterns=(-e "$SESSION_ID" -e "chat/${SESSION_ID}")
  [ -z "${SESSION_LOG_PATH// }" ] || patterns+=(-e "$SESSION_LOG_PATH")
  # Do not use -q: grep may otherwise hide an I/O error after an early match.
  if grep -F "${patterns[@]}" "$file" >/dev/null 2>/dev/null; then return 0; else status=$?; fi
  if [ "$status" -ne 1 ]; then
    echo "ERROR: transcript-read-failed" >&2
    return 3
  fi

  return 1
}

for root in "$CODEX_HOME_DIR/sessions" "$CODEX_HOME_DIR/archived_sessions"; do
  if [ ! -d "$root" ]; then
    continue
  fi

  if ! find "$root" -type f -name '*.jsonl' -print0 > "$TMP_DISCOVERY/files" 2>/dev/null; then
    echo "ERROR: transcript-scan-failed" >&2
    exit 3
  fi
  while IFS= read -r -d '' file; do
    if matches_file "$file"; then
      append_match "$file"
    else
      status=$?
      [ "$status" -eq 1 ] || exit "$status"
    fi
  done < "$TMP_DISCOVERY/files"
done

if [ ! -s "$TMP_MATCHES" ]; then
  echo "ERROR: transcript-match-absent" >&2
  exit 1
fi

if ! sort -rn "$TMP_MATCHES" > "$TMP_DISCOVERY/sorted" 2>/dev/null; then
  echo "ERROR: transcript-selection-failed" >&2
  exit 3
fi
IFS=$'\t' read -r selected_mtime selected_path < "$TMP_DISCOVERY/sorted"
printf '%s\n' "$selected_path"
