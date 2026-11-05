#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.check-commit-prerequisites
#   version: 2
#   status: active
#   created_on: "2026-06-15"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Verify commit-boundary workflow, checklist, and referenced gate files exist.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.check-commit-prerequisites.readme
#     path: scripts/00.chat/session-log/check-commit-prerequisites/README.md
#   - id: chat.script.session-log.check-commit-prerequisites.smoke-test
#     path: scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh
#   effects:
#   - read-only

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

read_failed() { echo "ERROR: prerequisite-$1-read-failed" >&2; exit 2; }
BRANCH="$(git branch --show-current 2>/dev/null)" || read_failed branch
CHECKLIST=".agentic/00.chat/checklists/before-commit.md"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch" >&2
  exit 1
fi

LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"
FAILURES=0

fail() {
  echo "ERROR: $*" >&2
  FAILURES=$((FAILURES + 1))
}

ok() {
  echo "OK: $*"
}

metadata_value() {
  local key="$1"
  chat_log_metadata_value "$LOG_FILE" "$key"
}

check_file() {
  local path="$1"
  local description="$2"

  if [ -f "$path" ]; then
    ok "$description exists: $path"
  else
    fail "$description is missing"
  fi
}

collect_script_refs() {
  local file="$1"

  if [ ! -f "$file" ]; then
    return
  fi

  local status
  if grep -Eo "scripts/[^ \`\"']+\.sh" "$file" 2>/dev/null; then
    return 0
  else
    status=$?
    [ "$status" -eq 1 ] || read_failed script-references
  fi
}

is_optional_script_ref() {
  local path="$1"

  case "$path" in
    scripts/repo/commit-gates/script.sh)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if [ ! -f "$LOG_FILE" ]; then
  fail "missing chat log"
else
  ok "chat log exists: $LOG_FILE"
fi

WORKFLOW=""
if [ -f "$LOG_FILE" ]; then
  WORKFLOW="$(metadata_value "chat_lifecycle_workflow")"
  if [ -z "${WORKFLOW// }" ]; then
    WORKFLOW="$(metadata_value "workflow")"
  fi
fi

if [ -z "${WORKFLOW// }" ]; then
  fail "session metadata is missing chat_lifecycle_workflow"
else
  check_file "$WORKFLOW" "declared chat lifecycle workflow"
fi

check_file "$CHECKLIST" "canonical before-commit checklist"

SCRIPT_REFS=""
if [ -n "${WORKFLOW// }" ] && [ -f "$WORKFLOW" ]; then
  SCRIPT_REFS="$SCRIPT_REFS
$(collect_script_refs "$WORKFLOW")"
fi

if [ -f "$CHECKLIST" ]; then
  SCRIPT_REFS="$SCRIPT_REFS
$(collect_script_refs "$CHECKLIST")"
fi

sorted_refs="$(printf '%s\n' "$SCRIPT_REFS" | sort -u 2>/dev/null)" || read_failed reference-sort
while IFS= read -r script_path; do
  if [ -z "${script_path// }" ]; then
    continue
  fi
  if is_optional_script_ref "$script_path" && [ ! -f "$script_path" ]; then
    ok "optional referenced gate script is absent: $script_path"
    continue
  fi
  check_file "$script_path" "referenced gate script"
done <<< "$sorted_refs"

if [ "$FAILURES" -gt 0 ]; then
  echo "Commit prerequisites are missing. Repair branch state before committing." >&2
  exit 1
fi

echo "Commit prerequisites are present."
