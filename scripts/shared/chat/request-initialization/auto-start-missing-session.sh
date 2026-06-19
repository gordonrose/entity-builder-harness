#!/usr/bin/env bash
set -euo pipefail

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

exec bash scripts/shared/chat/chat-command.sh new "$PROMPT"
