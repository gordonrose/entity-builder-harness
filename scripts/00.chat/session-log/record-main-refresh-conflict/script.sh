#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Record main-refresh conflict classification and resolution in the current chat log.
#   domain: refresh
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#     - .agentic/00.chat/standards/main-refresh-conflict-types.md
#     - package.json scripts.chat:record-main-refresh-conflict
#   effects: writes-files

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

usage() {
  cat <<'EOF'
Usage:
  record-main-refresh-conflict.sh \
    --path <conflicted-path> \
    --type <conflict-type> \
    --reason <classification-reason> \
    --action <resolution-action> \
    --mode <deterministic|skill-assisted|manual|stopped> \
    --preflight-branch <branch> \
    --preflight-worktree <path> \
    [--files <changed-files-summary>] \
    [--checks <checks-summary>]

Records a main-refresh conflict classification and resolution audit entry in
the current chat session log.
EOF
}

CONFLICT_PATH=""
CONFLICT_TYPE=""
REASON=""
ACTION=""
MODE=""
PREFLIGHT_BRANCH=""
PREFLIGHT_WORKTREE=""
FILES="pending"
CHECKS="pending"

while [ $# -gt 0 ]; do
  case "$1" in
    --path)
      CONFLICT_PATH="${2:-}"
      shift 2
      ;;
    --type)
      CONFLICT_TYPE="${2:-}"
      shift 2
      ;;
    --reason)
      REASON="${2:-}"
      shift 2
      ;;
    --action)
      ACTION="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --preflight-branch)
      PREFLIGHT_BRANCH="${2:-}"
      shift 2
      ;;
    --preflight-worktree)
      PREFLIGHT_WORKTREE="${2:-}"
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

for required in CONFLICT_PATH CONFLICT_TYPE REASON ACTION MODE PREFLIGHT_BRANCH PREFLIGHT_WORKTREE; do
  if [ -z "${!required// }" ]; then
    echo "ERROR: missing required value: ${required}" >&2
    usage >&2
    exit 2
  fi
done

case "$MODE" in
  deterministic|skill-assisted|manual|stopped)
    ;;
  *)
    echo "ERROR: invalid mode: $MODE" >&2
    echo "Expected deterministic, skill-assisted, manual, or stopped." >&2
    exit 2
    ;;
esac

BRANCH="$(git branch --show-current)"

case "$BRANCH" in
  chat/*|agentic/preflight/*)
    ;;
  *)
    echo "ERROR: current branch is not a chat or preflight branch: $BRANCH" >&2
    exit 1
    ;;
esac

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH" 2>/dev/null)"; then
  if [ -z "${AGENTIC_SESSION_LOG:-}" ]; then
    echo "ERROR: could not infer chat session from branch. Set AGENTIC_SESSION_LOG." >&2
    exit 1
  fi
  LOG_FILE="$AGENTIC_SESSION_LOG"
else
  LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"
fi

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

ENTRY="- Path: \`${CONFLICT_PATH}\`
  Type: \`${CONFLICT_TYPE}\`
  Mode: ${MODE}
  Reason: ${REASON}
  Action: ${ACTION}
  Preflight branch: \`${PREFLIGHT_BRANCH}\`
  Preflight worktree: \`${PREFLIGHT_WORKTREE}\`
  Files changed by resolution: ${FILES}
  Checks: ${CHECKS}"

insert_section_entry "## Main Refresh Conflicts" "$ENTRY"
insert_section_entry "## Activity Log" "### ${TIMESTAMP} - Main refresh conflict recorded

Path: \`${CONFLICT_PATH}\`

Type: \`${CONFLICT_TYPE}\`

Mode: ${MODE}

Action: ${ACTION}"

echo "Recorded main refresh conflict: ${CONFLICT_PATH}"
