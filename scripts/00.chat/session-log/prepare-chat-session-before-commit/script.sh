#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Run commit-boundary gates and session-log readiness checks before task commits.
#   domain: session-log
#   portability: llm-workbench-required
#   used_by:
#     - scripts/shared/git/prepare-chat-session-before-commit.sh
#     - scripts/00.chat/session-log/prepare-chat-session-before-commit/README.md
#   effects: read-only

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

bash scripts/shared/git/check-write-location.sh
bash scripts/shared/git/check-commit-prerequisites.sh
bash scripts/shared/git/check-commitlog-deletions.sh
bash scripts/shared/harness/check-deterministic-process-drift.sh --staged
bash scripts/shared/harness/check-artifact-metadata-headers.sh --staged-added
bash scripts/shared/harness/check-governed-script-command-drift.sh

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

FAILURES=0

fail() {
  echo "ERROR: $*" >&2
  FAILURES=$((FAILURES + 1))
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
  echo "Chat session is not ready for commit." >&2
  exit 1
fi

echo "Chat session is ready for commit: $LOG_FILE"
