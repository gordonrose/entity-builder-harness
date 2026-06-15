#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  record-chat-commit.sh <sha> <message> <summary> [adr-impact]

Records a commit in the current chat session log and updates rolling latest
commit session metrics.
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

case "$BRANCH" in
  chat/*)
    SESSION_ID="${BRANCH#chat/}"
    ;;
  *)
    echo "ERROR: current branch is not a chat branch: $BRANCH" >&2
    exit 1
    ;;
esac

LOG_FILE="commitLogs/${SESSION_ID}/README.md"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE" >&2
  exit 1
fi

COMMIT_AT_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

metadata_value() {
  local key="$1"
  sed -n "/<!-- agentic-session/,/-->/s/^${key}: //p" "$LOG_FILE" | head -n 1
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
      CHAT_DURATION="${DURATION_SECONDS}s"
    fi
  fi
fi

if [ -n "${ESTIMATED_TOKENS:-}" ]; then
  TOKEN_ESTIMATE="$ESTIMATED_TOKENS"
else
  CHAR_COUNT="$(wc -c < "$LOG_FILE" | tr -d ' ')"
  TOKEN_ESTIMATE="$(( (CHAR_COUNT + 3) / 4 )) estimated from session log"
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
  -v duration="$CHAT_DURATION" \
  -v tokens="$TOKEN_ESTIMATE" '
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
      print "estimated_tokens: " tokens
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
      print "Estimated tokens: " tokens
      next
    }
    {
      print
    }
  ' "$LOG_FILE" > "$tmp"

mv "$tmp" "$LOG_FILE"

echo "Recorded chat commit: $COMMIT_SHA"
