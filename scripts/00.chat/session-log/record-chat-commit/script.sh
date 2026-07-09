#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.record-chat-commit
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Record a task commit and chat metrics in the current session log.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.record-chat-commit.readme
#     path: scripts/00.chat/session-log/record-chat-commit/README.md
#   - id: chat.script.session-log.record-chat-commit.smoke-test
#     path: scripts/00.chat/session-log/record-chat-commit/smoke-test.sh
#   effects:
#   - writes-files

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

usage() {
  cat <<'EOF'
Usage:
  record-chat-commit.sh <sha> <message> <summary> [adr-impact]

Records a commit in the current chat session log and updates rolling latest
commit session metrics.

The script estimates chat tokens from CHAT_TRANSCRIPT_BYTES when supplied.
Otherwise it uses neutral transcript_path metadata. Codex transcript discovery
is available when CHAT_TRANSCRIPT_PROVIDER=codex or LLM_WORKBENCH_TRANSCRIPT_PROVIDER=codex.

The script estimates chat cost from the resulting estimated chat-token count
when a pricing profile is available.
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
  local entry_tmp

  tmp="$(mktemp)"
  entry_tmp="$(mktemp)"
  printf '%s\n' "$entry" > "$entry_tmp"

  if awk -v section="$section" -v entry_path="$entry_tmp" '
    BEGIN {
      in_section = 0
      inserted = 0
      found = 0
      entry = ""
      while ((getline line < entry_path) > 0) {
        entry = entry (entry == "" ? "" : "\n") line
      }
      close(entry_path)
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
  ' "$LOG_FILE" > "$tmp"; then
    mv "$tmp" "$LOG_FILE"
  else
    rm -f "$tmp"
    rm -f "$entry_tmp"
    return 1
  fi

  rm -f "$entry_tmp"
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

TRANSCRIPT_PROVIDER="${CHAT_TRANSCRIPT_PROVIDER:-${TRANSCRIPT_PROVIDER:-$(metadata_value "transcript_provider")}}"
TRANSCRIPT_PATH="${CHAT_TRANSCRIPT_PATH:-${TRANSCRIPT_PATH:-$(metadata_value "transcript_path")}}"
TRANSCRIPT_BYTES="${CHAT_TRANSCRIPT_BYTES:-${TRANSCRIPT_BYTES:-$(metadata_value "transcript_bytes")}}"
TRANSCRIPT_SOURCE="${CHAT_TRANSCRIPT_SOURCE:-${TRANSCRIPT_SOURCE:-$(metadata_value "transcript_source")}}"
TRANSCRIPT_METRICS_MODE="${CHAT_TRANSCRIPT_METRICS_MODE:-portable}"

if [ -n "${CODEX_SESSION_LOG_PATH:-}" ]; then
  TRANSCRIPT_PROVIDER="${TRANSCRIPT_PROVIDER:-codex}"
  TRANSCRIPT_PATH="$CODEX_SESSION_LOG_PATH"
fi

case "${TRANSCRIPT_PROVIDER:-${LLM_WORKBENCH_TRANSCRIPT_PROVIDER:-}}" in
  codex)
    if [ -z "${TRANSCRIPT_PATH// }" ]; then
      TRANSCRIPT_PATH="$(bash scripts/00.chat/transcript/discover-codex-session-log/script.sh "$SESSION_ID" "$LOG_FILE" 2>/dev/null || true)"
    fi
    if [ -n "${TRANSCRIPT_PATH// }" ]; then
      TRANSCRIPT_PROVIDER="codex"
    fi
    ;;
esac

if [ -z "${TRANSCRIPT_BYTES:-}" ] && [ -n "${TRANSCRIPT_PATH// }" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  TRANSCRIPT_BYTES="$(wc -c < "$TRANSCRIPT_PATH" | tr -d ' ')"
  TRANSCRIPT_SOURCE="${TRANSCRIPT_SOURCE:-${TRANSCRIPT_PROVIDER:-transcript} path: ${TRANSCRIPT_PATH}}"
fi

if [ -n "${TRANSCRIPT_BYTES:-}" ]; then
  case "$TRANSCRIPT_BYTES" in
    ''|*[!0-9]*)
      echo "ERROR: CHAT_TRANSCRIPT_BYTES must be a non-negative integer." >&2
      exit 1
      ;;
  esac

  TRANSCRIPT_PROVIDER="${TRANSCRIPT_PROVIDER:-manual}"
  TRANSCRIPT_SOURCE="${TRANSCRIPT_SOURCE:-chat-supplied transcript byte count}"
  CHAT_TOKEN_ESTIMATE="$(( (TRANSCRIPT_BYTES + 3) / 4 )) estimated from chat transcript bytes (${TRANSCRIPT_BYTES} bytes; source: ${TRANSCRIPT_SOURCE})"
elif [ -n "${ESTIMATED_CHAT_TOKENS:-}" ]; then
  CHAT_TOKEN_ESTIMATE="$ESTIMATED_CHAT_TOKENS"
elif [ "$TRANSCRIPT_METRICS_MODE" = "strict" ] && [ "${ALLOW_MISSING_CHAT_TRANSCRIPT_METRICS:-}" != "yes" ]; then
  echo "ERROR: missing chat transcript metrics." >&2
  echo "Set CHAT_TRANSCRIPT_BYTES, CHAT_TRANSCRIPT_PATH, ESTIMATED_CHAT_TOKENS, or use portable transcript metrics mode." >&2
  exit 1
else
  CHAT_TOKEN_ESTIMATE="unavailable; transcript source not supplied by chat"
fi

CHAT_COST_ESTIMATE="unavailable; estimated chat tokens are unavailable"
CHAT_COST_BASIS="unavailable; estimated chat tokens are unavailable"

if [[ "$CHAT_TOKEN_ESTIMATE" =~ ^([0-9]+)[[:space:]] ]]; then
  CHAT_TOKEN_COUNT="${BASH_REMATCH[1]}"
  CHAT_COST_OUTPUT="$(node scripts/00.chat/metrics/estimate-chat-cost/script.js "$CHAT_TOKEN_COUNT")"
  CHAT_COST_ESTIMATE="$(printf '%s\n' "$CHAT_COST_OUTPUT" | sed -n 's/^estimated_chat_cost: //p' | head -n 1)"
  CHAT_COST_BASIS="$(printf '%s\n' "$CHAT_COST_OUTPUT" | sed -n 's/^estimated_chat_cost_basis: //p' | head -n 1)"
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
  -v transcript_provider="$TRANSCRIPT_PROVIDER" \
  -v transcript_path="$TRANSCRIPT_PATH" \
  -v transcript_bytes="$TRANSCRIPT_BYTES" \
  -v transcript_source="$TRANSCRIPT_SOURCE" \
  -v duration="$CHAT_DURATION" \
  -v chat_tokens="$CHAT_TOKEN_ESTIMATE" \
  -v chat_cost="$CHAT_COST_ESTIMATE" \
  -v chat_cost_basis="$CHAT_COST_BASIS" '
    BEGIN {
      in_meta = 0
      wrote_transcript_provider = 0
      wrote_transcript_path = 0
      wrote_transcript_bytes = 0
      wrote_transcript_source = 0
      wrote_chat_cost = 0
      wrote_chat_cost_basis = 0
    }
    /^<!-- agentic-session/ {
      in_meta = 1
      print
      next
    }
    in_meta && /^transcript_provider:/ {
      print "transcript_provider: " transcript_provider
      wrote_transcript_provider = 1
      next
    }
    in_meta && /^transcript_path:/ {
      print "transcript_path: " transcript_path
      wrote_transcript_path = 1
      next
    }
    in_meta && /^transcript_bytes:/ {
      print "transcript_bytes: " transcript_bytes
      wrote_transcript_bytes = 1
      next
    }
    in_meta && /^transcript_source:/ {
      print "transcript_source: " transcript_source
      wrote_transcript_source = 1
      next
    }
    in_meta && /^codex_session_log_path:/ {
      next
    }
    in_meta && /^-->/ {
      if (wrote_transcript_provider == 0) {
        print "transcript_provider: " transcript_provider
        wrote_transcript_provider = 1
      }
      if (wrote_transcript_path == 0) {
        print "transcript_path: " transcript_path
        wrote_transcript_path = 1
      }
      if (wrote_transcript_bytes == 0) {
        print "transcript_bytes: " transcript_bytes
        wrote_transcript_bytes = 1
      }
      if (wrote_transcript_source == 0) {
        print "transcript_source: " transcript_source
        wrote_transcript_source = 1
      }
      if (wrote_chat_cost == 0) {
        print "estimated_chat_cost: " chat_cost
        wrote_chat_cost = 1
      }
      if (wrote_chat_cost_basis == 0) {
        print "estimated_chat_cost_basis: " chat_cost_basis
        wrote_chat_cost_basis = 1
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
    /^estimated_chat_cost:/ {
      print "estimated_chat_cost: " chat_cost
      wrote_chat_cost = 1
      next
    }
    /^estimated_chat_cost_basis:/ {
      print "estimated_chat_cost_basis: " chat_cost_basis
      wrote_chat_cost_basis = 1
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
      print "Estimated chat cost: " chat_cost
      print "Estimated chat cost basis: " chat_cost_basis
      next
    }
    /^Estimated chat cost:/ {
      next
    }
    /^Estimated chat cost basis:/ {
      next
    }
    {
      print
    }
  ' "$LOG_FILE" > "$tmp"

mv "$tmp" "$LOG_FILE"

echo "Recorded chat commit: $COMMIT_SHA"
echo "If continuing this chat into another phase after checkpointing session-log bookkeeping, run /compact."
