#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.prepare-chat-session-before-commit
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Run commit-boundary gates and session-log readiness checks before task commits.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.prepare-chat-session-before-commit.readme
#     path: scripts/00.chat/session-log/prepare-chat-session-before-commit/README.md
#   effects:
#   - read-only

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

bash scripts/00.chat/worktree/check-write-location/script.sh
bash scripts/00.chat/session-log/check-commit-prerequisites/script.sh
bash scripts/00.chat/session-log/check-commitlog-deletions/script.sh
bash scripts/01.harness/check-deterministic-process-drift.sh --staged
bash scripts/01.harness/artifact-metadata/check-headers/script.sh --staged-added
bash scripts/01.harness/check-governed-script-command-drift.sh

REPO_COMMIT_GATES_SCRIPT="${CHAT_REPO_COMMIT_GATES_SCRIPT:-scripts/repo/commit-gates/script.sh}"

if [ -n "${REPO_COMMIT_GATES_SCRIPT//[[:space:]]/}" ] && [ -e "$REPO_COMMIT_GATES_SCRIPT" ]; then
  case "$REPO_COMMIT_GATES_SCRIPT" in
    /*|../*|*/../*|*/..|..|-*|*$'\n'*|*$'\r'*)
      echo "ERROR: refused non-repository commit extension hook: $REPO_COMMIT_GATES_SCRIPT" >&2
      exit 1
      ;;
  esac

  if [ ! -x "$REPO_COMMIT_GATES_SCRIPT" ]; then
    echo "ERROR: repository commit extension hook is not executable: $REPO_COMMIT_GATES_SCRIPT" >&2
    exit 1
  fi

  bash "$REPO_COMMIT_GATES_SCRIPT"
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
