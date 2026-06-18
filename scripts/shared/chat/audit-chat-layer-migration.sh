#!/usr/bin/env bash
set -euo pipefail

required_paths=(
  ".agentic/00.chat/README.md"
  ".agentic/00.chat/migration-plan.md"
  ".agentic/00.chat/workflows/README.md"
  ".agentic/00.chat/workflows/chat-start.md"
  ".agentic/00.chat/workflows/chat-commit.md"
  ".agentic/00.chat/workflows/chat-refresh-from-main.md"
  ".agentic/00.chat/workflows/chat-promote-to-main.md"
  ".agentic/00.chat/workflows/chat-cleanup.md"
  ".agentic/00.chat/workflows/chat-reporting.md"
  ".agentic/00.chat/checklists/before-commit.md"
  ".agentic/00.chat/skills/session-summary.md"
)

compatibility_paths=(
  ".agentic/shared/workflows/chat-start-interview.md"
  ".agentic/shared/workflows/main-updated.md"
  ".agentic/shared/workflows/local-convergence.md"
  ".agentic/shared/checklists/before-commit.md"
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

echo "Canonical chat layer files"
for path in "${required_paths[@]}"; do
  check_file "$path" "canonical file"
done

echo
echo "Compatibility files"
for path in "${compatibility_paths[@]}"; do
  check_file "$path" "compatibility file"
done

echo
echo "Legacy shared workflow references"
legacy_matches="$(
  grep -RIlE \
    '\.agentic/shared/workflows/(chat-start-interview|main-updated|local-convergence)\.md|\.agentic/shared/checklists/before-commit\.md' \
    .agentic scripts docs 2>/dev/null \
    | grep -v -E '^\.agentic/00\.chat/migration-plan\.md$|^scripts/shared/chat/audit-chat-layer-migration\.sh$' \
    || true
)"

if [ -z "$legacy_matches" ]; then
  echo "OK: no legacy shared chat workflow references found."
else
  echo "Legacy reference files:"
  printf '%s\n' "$legacy_matches"
fi

echo
echo "Retired aggregate summary policy references"
summary_matches="$(
  grep -RIl 'commitLogs/README.md' .agentic scripts docs 2>/dev/null \
    | grep -v -E '^\.agentic/00\.chat/migration-plan\.md$|^scripts/shared/chat/audit-chat-layer-migration\.sh$' \
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
