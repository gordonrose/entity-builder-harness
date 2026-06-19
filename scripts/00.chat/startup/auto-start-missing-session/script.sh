#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Convert an opening prompt into a governed chat session when metadata is missing.
#   domain: startup
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/commands/README.md
#     - scripts/00.chat/startup/auto-start-missing-session/README.md
#   effects: branches, worktrees, writes-files, stages-files

OPENING_PROMPT="${*:-}"

trimmed_prompt() {
  printf '%s' "$OPENING_PROMPT" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//'
}

PROMPT="$(trimmed_prompt)"
PROMPT_LOWER="$(printf '%s' "$PROMPT" | tr '[:upper:]' '[:lower:]')"

if [ -z "${PROMPT// }" ]; then
  echo "ERROR: opening prompt is required." >&2
  exit 2
fi

case "$PROMPT_LOWER" in
  "new")
    echo "What should the new chat be about?"
    exit 2
    ;;
  ignore\ chat\ start*)
    echo "Skipping chat auto-start because the opening prompt begins with 'ignore chat start'."
    exit 0
    ;;
esac

exec bash scripts/00.chat/command/dispatcher/script.sh new "$PROMPT"
