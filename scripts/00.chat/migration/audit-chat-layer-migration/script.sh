#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.migration.audit-chat-layer-migration
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: migration
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Verify canonical chat-layer files and retired compatibility paths.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.migration-plan
#     path: .agentic/00.chat/migration-plan.md
#   effects:
#   - read-only

required_paths=(
  "package.json"
  ".agentic/00.chat/README.md"
  ".agentic/00.chat/migration-plan.md"
  ".agentic/00.chat/workflows/README.md"
  ".agentic/00.chat/workflows/chat-start.md"
  ".agentic/00.chat/workflows/chat-commit.md"
  ".agentic/00.chat/workflows/chat-refresh-from-main.md"
  ".agentic/00.chat/workflows/chat-promote-to-main.md"
  ".agentic/00.chat/workflows/chat-cleanup.md"
  ".agentic/00.chat/workflows/chat-reporting.md"
  ".agentic/00.chat/workflows/chat-upstream-reusable-lesson.md"
  ".agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md"
  ".agentic/00.chat/checklists/before-commit.md"
  ".agentic/00.chat/skills/session-summary.md"
)

retired_paths=(
  ".agentic/shared/workflows/chat-start-interview.md"
  ".agentic/shared/workflows/main-updated.md"
  ".agentic/shared/workflows/local-convergence.md"
  ".agentic/shared/checklists/before-commit.md"
  ".agentic/shared/workflows/default.md"
  ".agentic/01.harness/workflows/default.md"
)

failures=0

check_file() {
  local path="$1"
  local label="$2"

  if [ -f "$path" ]; then
    echo "OK: ${label}: ${path}"
  else
    echo "ERROR: missing ${label}: ${path}" >&2
    failures=$((failures + 1))
  fi
}

check_absent() {
  local path="$1"
  local label="$2"

  if [ -e "$path" ]; then
    echo "ERROR: retired ${label} still exists: ${path}" >&2
    failures=$((failures + 1))
  else
    echo "OK: retired ${label} absent: ${path}"
  fi
}

echo "Canonical chat layer files"
for path in "${required_paths[@]}"; do
  check_file "$path" "canonical file"
done

echo
echo "Retired compatibility paths"
for path in "${retired_paths[@]}"; do
  check_absent "$path" "path"
done

echo
echo "Retired compatibility references"
retired_matches="$(
  grep -RIlE \
    '\.agentic/shared/workflows/(chat-start-interview|main-updated|local-convergence|default)\.md|\.agentic/shared/checklists/before-commit\.md|\.agentic/01.harness/workflows/default\.md' \
    .agentic scripts docs 2>/dev/null \
    | grep -v -E '^\.agentic/00\.chat/migration-plan\.md$|^scripts/00\.chat/migration/audit-chat-layer-migration/script\.sh$' \
    || true
)"

if [ -z "$retired_matches" ]; then
  echo "OK: no retired compatibility references found."
else
  echo "Retired compatibility reference files:"
  printf '%s\n' "$retired_matches"
  failures=$((failures + 1))
fi

echo
echo "Retired aggregate summary policy references"
summary_matches="$(
  grep -RIl 'commitLogs/README.md' .agentic scripts docs 2>/dev/null \
    | grep -v -E '^\.agentic/00\.chat/migration-plan\.md$|^scripts/00\.chat/migration/audit-chat-layer-migration/script\.sh$' \
    || true
)"

if [ -z "$summary_matches" ]; then
  echo "OK: no commitLogs/README.md policy references found."
else
  echo "Policy reference files:"
  printf '%s\n' "$summary_matches"
fi

if [ "$failures" -gt 0 ]; then
  echo "Chat layer migration audit failed." >&2
  exit 1
fi

echo
echo "Chat layer migration audit completed."
