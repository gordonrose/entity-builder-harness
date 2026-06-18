#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../chat/session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

usage() {
  cat <<'EOF'
Usage:
  record-chat-commit.sh <sha> <message> <summary> [adr-impact]

Records a commit in the current chat session log and updates rolling latest
commit session metrics.

The script estimates chat tokens from CHAT_TRANSCRIPT_BYTES when supplied.
Otherwise it uses codex_session_log_path metadata, or discovers the matching
Codex JSONL session log and counts its bytes.
EOF
}

if [ $# -lt 3 ] || [ $# -gt 4 ]; then
  usage >&2
  exit 2
fi

COMMIT_SHA="$1"
COMMIT_MESSAGE="$2"
COMMIT_SUMMARY="$3"
ADR_IMPACT="${4:-covered by session ADR disposition}"

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

COMMIT_AT_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

metadata_value() {
  local key="$1"
  sed -n "/<!-- agentic-session/,/-->/s/^${key}: //p" "$LOG_FILE" | head -n 1
}

format_duration_seconds() {
  local total_seconds="$1"
  local days hours minutes seconds

  days=$((total_seconds / 86400))
  hours=$(((total_seconds % 86400) / 3600))
  minutes=$(((total_seconds % 3600) / 60))
  seconds=$((total_seconds % 60))

  printf '%ss (%02d:%02d:%02d:%02d)\n' \
    "$total_seconds" "$days" "$hours" "$minutes" "$seconds"
}

insert_section_entry() {
  local section="$1"
  local entry="$2"
  local tmp

  tmp="$(mktemp)"

  awk -v section="$section" -v entry="$entry" '
    BEGIN {
      in_section = 0
      inserted = 0
      found = 0
    }
    $0 == section {
      found = 1
      in_section = 1
      print
      next
    }
    in_section && /^## / && inserted == 0 {
      print ""
      print entry
      print ""
      inserted = 1
      in_section = 0
    }
    in_section && $0 == "- None recorded yet." {
      next
    }
    {
      print
    }
    END {
      if (found == 0) {
        print ""
        print section
        print ""
        print entry
      } else if (in_section == 1 && inserted == 0) {
        print ""
        print entry
      }
    }
  ' "$LOG_FILE" > "$tmp"

  mv "$tmp" "$LOG_FILE"
}

RAISED_AT_UTC="$(metadata_value "raised_at_utc")"
CHAT_DURATION="unknown"

if [ -n "${RAISED_AT_UTC// }" ]; then
  if RAISED_SECONDS="$(date -u -d "$RAISED_AT_UTC" +"%s" 2>/dev/null)" &&
     COMMIT_SECONDS="$(date -u -d "$COMMIT_AT_UTC" +"%s" 2>/dev/null)"; then
    DURATION_SECONDS=$((COMMIT_SECONDS - RAISED_SECONDS))
    if [ "$DURATION_SECONDS" -ge 0 ]; then
      CHAT_DURATION="$(format_duration_seconds "$DURATION_SECONDS")"
    fi
  fi
fi

CODEX_SESSION_LOG_PATH="${CODEX_SESSION_LOG_PATH:-$(metadata_value "codex_session_log_path")}"

if [ -z "${CHAT_TRANSCRIPT_BYTES:-}" ]; then
  if [ -z "${CODEX_SESSION_LOG_PATH// }" ]; then
    CODEX_SESSION_LOG_PATH="$(bash scripts/shared/chat/discover-codex-session-log.sh "$SESSION_ID" "$LOG_FILE" 2>/dev/null || true)"
  fi

  if [ -n "${CODEX_SESSION_LOG_PATH// }" ] && [ -f "$CODEX_SESSION_LOG_PATH" ]; then
    CHAT_TRANSCRIPT_BYTES="$(wc -c < "$CODEX_SESSION_LOG_PATH" | tr -d ' ')"
    CHAT_TRANSCRIPT_SOURCE="${CHAT_TRANSCRIPT_SOURCE:-Codex session log: ${CODEX_SESSION_LOG_PATH}}"
  fi
fi

if [ -n "${CHAT_TRANSCRIPT_BYTES:-}" ]; then
  case "$CHAT_TRANSCRIPT_BYTES" in
    ''|*[!0-9]*)
      echo "ERROR: CHAT_TRANSCRIPT_BYTES must be a non-negative integer." >&2
      exit 1
      ;;
  esac

  CHAT_TRANSCRIPT_SOURCE="${CHAT_TRANSCRIPT_SOURCE:-chat-supplied transcript byte count}"
  CHAT_TOKEN_ESTIMATE="$(( (CHAT_TRANSCRIPT_BYTES + 3) / 4 )) estimated from chat transcript bytes (${CHAT_TRANSCRIPT_BYTES} bytes; source: ${CHAT_TRANSCRIPT_SOURCE})"
elif [ -n "${ESTIMATED_CHAT_TOKENS:-}" ]; then
  CHAT_TOKEN_ESTIMATE="$ESTIMATED_CHAT_TOKENS"
elif [ "${ALLOW_MISSING_CHAT_TRANSCRIPT_METRICS:-}" = "yes" ]; then
  CHAT_TOKEN_ESTIMATE="unavailable; transcript source not supplied by chat"
else
  echo "ERROR: missing chat transcript metrics." >&2
  echo "Set CHAT_TRANSCRIPT_BYTES, record codex_session_log_path, or ensure the Codex session log is discoverable." >&2
  echo "Use ALLOW_MISSING_CHAT_TRANSCRIPT_METRICS=yes only for explicit legacy or recovery cases." >&2
  exit 1
fi

insert_section_entry "## Commits" "- Commit: \`${COMMIT_SHA}\`
  Time UTC: ${COMMIT_AT_UTC}
  Message: ${COMMIT_MESSAGE}
  Summary: ${COMMIT_SUMMARY}
  ADR impact: ${ADR_IMPACT}"

insert_section_entry "## Activity Log" "### ${COMMIT_AT_UTC} - Commit recorded

Commit: \`${COMMIT_SHA}\`

Message: ${COMMIT_MESSAGE}

Summary: ${COMMIT_SUMMARY}

ADR impact: ${ADR_IMPACT}"

tmp="$(mktemp)"

awk \
  -v latest_at="$COMMIT_AT_UTC" \
  -v latest_sha="$COMMIT_SHA" \
  -v codex_path="$CODEX_SESSION_LOG_PATH" \
  -v duration="$CHAT_DURATION" \
  -v chat_tokens="$CHAT_TOKEN_ESTIMATE" '
    BEGIN {
      in_meta = 0
      wrote_codex_path = (codex_path == "")
    }
    /^<!-- agentic-session/ {
      in_meta = 1
      print
      next
    }
    in_meta && /^codex_session_log_path:/ {
      if (codex_path != "") {
        print "codex_session_log_path: " codex_path
      } else {
        print
      }
      wrote_codex_path = 1
      next
    }
    in_meta && /^-->/ {
      if (wrote_codex_path == 0) {
        print "codex_session_log_path: " codex_path
        wrote_codex_path = 1
      }
      in_meta = 0
      print
      next
    }
    /^final_commit_at_utc:/ {
      print "latest_commit_at_utc: " latest_at
      print "latest_commit_sha: " latest_sha
      next
    }
    /^latest_commit_at_utc:/ {
      print "latest_commit_at_utc: " latest_at
      next
    }
    /^latest_commit_sha:/ {
      print "latest_commit_sha: " latest_sha
      next
    }
    /^chat_duration:/ {
      print "chat_duration: " duration
      next
    }
    /^estimated_tokens:/ {
      print "estimated_chat_tokens: " chat_tokens
      next
    }
    /^estimated_chat_tokens:/ {
      print "estimated_chat_tokens: " chat_tokens
      next
    }
    /^Final commit at UTC:/ {
      print "Latest commit at UTC: " latest_at
      print "Latest commit SHA: " latest_sha
      next
    }
    /^Latest commit at UTC:/ {
      print "Latest commit at UTC: " latest_at
      next
    }
    /^Latest commit SHA:/ {
      print "Latest commit SHA: " latest_sha
      next
    }
    /^Chat duration:/ {
      print "Chat duration: " duration
      next
    }
    /^Estimated tokens:/ {
      print "Estimated chat tokens: " chat_tokens
      next
    }
    /^Estimated chat tokens:/ {
      print "Estimated chat tokens: " chat_tokens
      next
    }
    {
      print
    }
  ' "$LOG_FILE" > "$tmp"

mv "$tmp" "$LOG_FILE"

echo "Recorded chat commit: $COMMIT_SHA"
