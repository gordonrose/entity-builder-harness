#!/usr/bin/env bash
set -euo pipefail

BRANCH="$(git branch --show-current)"
CHECKLIST=".agentic/shared/checklists/before-commit.md"

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

  sed -n -E 's/.*bash +(scripts\/[^ `"'\'']+).*/\1/p' "$file"
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

check_file "$CHECKLIST" "before-commit checklist"

SCRIPT_REFS=""
if [ -n "${WORKFLOW// }" ] && [ -f "$WORKFLOW" ]; then
  SCRIPT_REFS="$SCRIPT_REFS
$(collect_script_refs "$WORKFLOW")"
fi

if [ -f "$CHECKLIST" ]; then
  SCRIPT_REFS="$SCRIPT_REFS
$(collect_script_refs "$CHECKLIST")"
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
