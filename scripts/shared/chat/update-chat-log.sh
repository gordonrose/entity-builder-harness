#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

usage() {
  cat <<'EOF'
Usage:
  update-chat-log.sh question <asked-summary> <response-summary>
  update-chat-log.sh issue <issue-summary> <resolution-summary>
  update-chat-log.sh decision <decision-summary> <rationale-summary>
  update-chat-log.sh commit-summary <commit-or-message> <summary> [adr-impact]
  update-chat-log.sh adr-disposition needed <adr-path> <reason>
  update-chat-log.sh adr-disposition not-needed <reason>

Updates the current chat branch session log under commitLogs/<yyyy>/<mmm>/<dd>/<session>/README.md.
EOF
}

if [ $# -lt 1 ]; then
  usage >&2
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

TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

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

set_adr_disposition() {
  local needed="$1"
  local path="$2"
  local reason="$3"
  local tmp

  tmp="$(mktemp)"

  awk -v needed="$needed" -v path="$path" -v reason="$reason" '
    BEGIN {
      in_adr = 0
      saw_needed = 0
      saw_path = 0
      saw_reason = 0
    }
    $0 == "## ADR Disposition" {
      in_adr = 1
      print
      next
    }
    in_adr && /^## / {
      if (saw_needed == 0) {
        print "ADR needed: " needed
      }
      if (saw_path == 0) {
        print "ADR path: " path
      }
      if (saw_reason == 0) {
        print "Reason: " reason
      }
      in_adr = 0
    }
    in_adr && /^ADR needed:/ {
      print "ADR needed: " needed
      saw_needed = 1
      next
    }
    in_adr && /^ADR path:/ {
      print "ADR path: " path
      saw_path = 1
      next
    }
    in_adr && /^Reason:/ {
      print "Reason: " reason
      saw_reason = 1
      next
    }
    {
      print
    }
    END {
      if (in_adr == 1) {
        if (saw_needed == 0) {
          print "ADR needed: " needed
        }
        if (saw_path == 0) {
          print "ADR path: " path
        }
        if (saw_reason == 0) {
          print "Reason: " reason
        }
      }
    }
  ' "$LOG_FILE" > "$tmp"

  mv "$tmp" "$LOG_FILE"
}

COMMAND="$1"
shift

case "$COMMAND" in
  question)
    if [ $# -ne 2 ]; then
      usage >&2
      exit 2
    fi
    insert_section_entry "## Questions Asked" "- Asked: $1
  Response: $2"
    insert_section_entry "## Activity Log" "### ${TIMESTAMP} - Question

Asked: $1

Response: $2"
    ;;
  issue)
    if [ $# -ne 2 ]; then
      usage >&2
      exit 2
    fi
    insert_section_entry "## Issues Raised" "- Raised: $1
  Resolution: $2"
    insert_section_entry "## Activity Log" "### ${TIMESTAMP} - Issue

Raised: $1

Resolution: $2"
    ;;
  decision)
    if [ $# -ne 2 ]; then
      usage >&2
      exit 2
    fi
    insert_section_entry "## Decisions Made" "- Decision: $1
  Rationale: $2"
    insert_section_entry "## Activity Log" "### ${TIMESTAMP} - Decision

Decision: $1

Rationale: $2"
    ;;
  commit-summary)
    if [ $# -lt 2 ] || [ $# -gt 3 ]; then
      usage >&2
      exit 2
    fi
    ADR_IMPACT="${3:-covered by session ADR disposition}"
    insert_section_entry "## Commits" "- Commit: $1
  Summary: $2
  ADR impact: ${ADR_IMPACT}"
    insert_section_entry "## Activity Log" "### ${TIMESTAMP} - Commit summary

Commit: $1

Summary: $2

ADR impact: ${ADR_IMPACT}"
    ;;
  adr-disposition)
    if [ $# -lt 1 ]; then
      usage >&2
      exit 2
    fi
    case "$1" in
      needed)
        if [ $# -ne 3 ]; then
          usage >&2
          exit 2
        fi
        set_adr_disposition "yes" "$2" "$3"
        insert_section_entry "## Activity Log" "### ${TIMESTAMP} - ADR disposition

ADR needed: yes

ADR path: $2

Reason: $3"
        ;;
      not-needed)
        if [ $# -ne 2 ]; then
          usage >&2
          exit 2
        fi
        set_adr_disposition "no" "" "$2"
        insert_section_entry "## Activity Log" "### ${TIMESTAMP} - ADR disposition

ADR needed: no

Reason: $2"
        ;;
      *)
        usage >&2
        exit 2
        ;;
    esac
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
