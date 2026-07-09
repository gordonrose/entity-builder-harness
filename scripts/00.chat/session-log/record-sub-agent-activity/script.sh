#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.record-sub-agent-activity
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Record sub-agent or direct-fallback work in the current chat log.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.record-sub-agent-activity.readme
#     path: scripts/00.chat/session-log/record-sub-agent-activity/README.md
#   - id: chat.script.session-log.record-sub-agent-activity.smoke-test
#     path: scripts/00.chat/session-log/record-sub-agent-activity/smoke-test.sh
#   effects:
#   - writes-files

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

usage() {
  cat <<'EOF'
Usage:
  record-sub-agent-activity.sh \
    --mode <sub-agent|direct-fallback> \
    --status <completed|blocked|failed|partial> \
    --agent <label> \
    --scope <work-scope> \
    --summary <summary> \
    [--files <files-summary>] \
    [--checks <checks-summary>] \
    [--git-actions <git-actions-summary>] \
    [--blockers <blockers-summary>] \
    [--next-step <next-step-summary>]

Records delegated or direct-fallback work in the current chat session log.
EOF
}

MODE=""
STATUS=""
AGENT=""
SCOPE=""
SUMMARY=""
FILES="none"
CHECKS="not run"
GIT_ACTIONS="none"
BLOCKERS="none"
NEXT_STEP="none"

while [ $# -gt 0 ]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --status)
      STATUS="${2:-}"
      shift 2
      ;;
    --agent)
      AGENT="${2:-}"
      shift 2
      ;;
    --scope)
      SCOPE="${2:-}"
      shift 2
      ;;
    --summary)
      SUMMARY="${2:-}"
      shift 2
      ;;
    --files)
      FILES="${2:-}"
      shift 2
      ;;
    --checks)
      CHECKS="${2:-}"
      shift 2
      ;;
    --git-actions)
      GIT_ACTIONS="${2:-}"
      shift 2
      ;;
    --blockers)
      BLOCKERS="${2:-}"
      shift 2
      ;;
    --next-step)
      NEXT_STEP="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

for required in MODE STATUS AGENT SCOPE SUMMARY; do
  if [ -z "${!required// }" ]; then
    echo "ERROR: missing required value: ${required}" >&2
    usage >&2
    exit 2
  fi
done

case "$MODE" in
  sub-agent|direct-fallback)
    ;;
  *)
    echo "ERROR: invalid mode: $MODE" >&2
    echo "Expected sub-agent or direct-fallback." >&2
    exit 2
    ;;
esac

case "$STATUS" in
  completed|blocked|failed|partial)
    ;;
  *)
    echo "ERROR: invalid status: $STATUS" >&2
    echo "Expected completed, blocked, failed, or partial." >&2
    exit 2
    ;;
esac

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
FALLBACK_USED="no"

if [ "$MODE" = "direct-fallback" ]; then
  FALLBACK_USED="yes"
fi

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

ENTRY="### ${TIMESTAMP} - ${AGENT}

Status: ${STATUS}
Delegation mode: ${MODE}
Fallback used: ${FALLBACK_USED}
Scope: ${SCOPE}
Files touched: ${FILES}
Checks run: ${CHECKS}
Git actions: ${GIT_ACTIONS}
Blockers: ${BLOCKERS}
Next step: ${NEXT_STEP}
Summary: ${SUMMARY}"

insert_section_entry "## Sub-Agent Activity" "$ENTRY"
insert_section_entry "## Activity Log" "### ${TIMESTAMP} - Sub-agent activity recorded

Agent: ${AGENT}

Status: ${STATUS}

Delegation mode: ${MODE}

Fallback used: ${FALLBACK_USED}

Scope: ${SCOPE}"

echo "Recorded sub-agent activity: ${AGENT} (${MODE}, ${STATUS})"
