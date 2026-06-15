#!/usr/bin/env bash
set -euo pipefail

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

FAILURES=0

fail() {
  echo "ERROR: $*" >&2
  FAILURES=$((FAILURES + 1))
}

metadata_value() {
  local key="$1"
  sed -n "/<!-- agentic-session/,/-->/s/^${key}: //p" "$LOG_FILE" | head -n 1
}

section_has_recorded_entry() {
  local section="$1"

  awk -v section="$section" '
    $0 == section {
      in_section = 1
      next
    }
    in_section && /^## / {
      exit
    }
    in_section && $0 != "" && $0 != "- None recorded yet." {
      found = 1
    }
    END {
      exit found ? 0 : 1
    }
  ' "$LOG_FILE"
}

field_value() {
  local label="$1"
  sed -n "s/^${label}: //p" "$LOG_FILE" | tail -n 1
}

require_section_entry() {
  local section="$1"
  local description="$2"

  if ! section_has_recorded_entry "$section"; then
    fail "$description is still missing in $LOG_FILE"
  fi
}

require_section_entry "## Initial Intent" "Initial intent"
require_section_entry "## Decisions Made" "Decisions made summary"
require_section_entry "## ADR Disposition" "ADR disposition"

ADR_NEEDED="$(field_value "ADR needed")"
ADR_PATH="$(field_value "ADR path")"
ADR_REASON="$(field_value "Reason")"

case "$ADR_NEEDED" in
  yes)
    if [ -z "${ADR_PATH// }" ]; then
      fail "ADR needed is yes, but ADR path is empty"
    elif [[ "$ADR_PATH" != docs/harness/architecture/adrs/*.md ]]; then
      fail "ADR path must be under docs/harness/architecture/adrs/: $ADR_PATH"
    elif [ ! -f "$ADR_PATH" ]; then
      fail "ADR path does not exist: $ADR_PATH"
    fi

    if [ -z "${ADR_REASON// }" ]; then
      fail "ADR needed is yes, but reason is empty"
    fi
    ;;
  no)
    if [ -z "${ADR_REASON// }" ]; then
      fail "ADR needed is no, but reason is empty"
    fi
    ;;
  *)
    fail "ADR needed must be yes or no, got: ${ADR_NEEDED:-missing}"
    ;;
esac

if [ "$FAILURES" -gt 0 ]; then
  echo "Chat session finalization failed." >&2
  exit 1
fi

FINALIZED_AT_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
RAISED_AT_UTC="$(metadata_value "raised_at_utc")"
CHAT_DURATION="unknown"

if [ -n "${RAISED_AT_UTC// }" ]; then
  if RAISED_SECONDS="$(date -u -d "$RAISED_AT_UTC" +"%s" 2>/dev/null)" &&
     FINAL_SECONDS="$(date -u -d "$FINALIZED_AT_UTC" +"%s" 2>/dev/null)"; then
    DURATION_SECONDS=$((FINAL_SECONDS - RAISED_SECONDS))
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

tmp="$(mktemp)"

awk \
  -v finalized_at="$FINALIZED_AT_UTC" \
  -v duration="$CHAT_DURATION" \
  -v tokens="$TOKEN_ESTIMATE" '
    /^final_commit_at_utc:/ {
      print "final_commit_at_utc: " finalized_at
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
      print "Final commit at UTC: " finalized_at
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

echo "Chat session finalized: $LOG_FILE"
