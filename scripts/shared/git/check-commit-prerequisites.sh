#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../chat/session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

BRANCH="$(git branch --show-current)"
CHECKLIST=".agentic/00.chat/checklists/before-commit.md"
COMPAT_CHECKLIST=".agentic/shared/checklists/before-commit.md"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch: $BRANCH" >&2
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
  sed -n "/<!-- agentic-session/,/-->/s/^${key}: //p" "$LOG_FILE" | head -n 1
}

check_file() {
  local path="$1"
  local description="$2"

  if [ -f "$path" ]; then
    ok "$description exists: $path"
  else
    fail "$description is missing: $path"
  fi
}

collect_script_refs() {
  local file="$1"

  if [ ! -f "$file" ]; then
    return
  fi

  grep -Eo "scripts/[^ \`\"']+" "$file" || true
}

if [ ! -f "$LOG_FILE" ]; then
  fail "missing chat log: $LOG_FILE"
else
  ok "chat log exists: $LOG_FILE"
fi

WORKFLOW=""
if [ -f "$LOG_FILE" ]; then
  WORKFLOW="$(metadata_value "workflow")"
fi

if [ -z "${WORKFLOW// }" ]; then
  fail "session metadata is missing workflow"
else
  check_file "$WORKFLOW" "declared workflow"
fi

check_file "$CHECKLIST" "canonical before-commit checklist"
check_file "$COMPAT_CHECKLIST" "compatibility before-commit checklist"

SCRIPT_REFS=""
if [ -n "${WORKFLOW// }" ] && [ -f "$WORKFLOW" ]; then
  SCRIPT_REFS="$SCRIPT_REFS
$(collect_script_refs "$WORKFLOW")"
fi

if [ -f "$CHECKLIST" ]; then
  SCRIPT_REFS="$SCRIPT_REFS
$(collect_script_refs "$CHECKLIST")"
fi

if [ -f "$COMPAT_CHECKLIST" ]; then
  SCRIPT_REFS="$SCRIPT_REFS
$(collect_script_refs "$COMPAT_CHECKLIST")"
fi

while IFS= read -r script_path; do
  if [ -z "${script_path// }" ]; then
    continue
  fi
  check_file "$script_path" "referenced gate script"
done < <(printf '%s\n' "$SCRIPT_REFS" | sort -u)

if [ "$FAILURES" -gt 0 ]; then
  echo "Commit prerequisites are missing. Repair branch state before committing." >&2
  exit 1
fi

echo "Commit prerequisites are present."
