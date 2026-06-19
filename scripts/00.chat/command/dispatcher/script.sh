#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Dispatch chat subcommands from canonical scripts/00.chat/command folders.
#   domain: command
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/commands/README.md
#     - scripts/00.chat/command/dispatcher/README.md
#     - scripts/chat/chat-command.sh
#     - scripts/00.chat/startup/auto-start-missing-session/script.sh
#   effects: branches, worktrees, writes-files, stages-files

COMMAND_DIR="scripts/00.chat/command"

usage() {
  cat <<EOF
Usage: chat-command.sh <command> [args...]

Commands:
EOF

  if [ -d "$COMMAND_DIR" ]; then
    find "$COMMAND_DIR" -mindepth 2 -maxdepth 2 -type f -path '*/script.sh' -perm -u+x \
      ! -path "$COMMAND_DIR/dispatcher/script.sh" \
      | sed -E 's#^scripts/00\.chat/command/([^/]+)/script\.sh$#  \1#' \
      | sort
  fi
}

if [ $# -eq 0 ]; then
  usage
  exit 0
fi

case "$1" in
  -h|--help|help|list)
    usage
    exit 0
    ;;
esac

COMMAND_NAME="$1"
shift

case "$COMMAND_NAME" in
  *[!a-zA-Z0-9_-]*|'')
    echo "ERROR: invalid chat command name: $COMMAND_NAME" >&2
    echo "Use letters, numbers, underscores, or hyphens." >&2
    exit 2
    ;;
esac

COMMAND_SCRIPT="${COMMAND_DIR}/${COMMAND_NAME}/script.sh"

if [ "$COMMAND_NAME" = "dispatcher" ]; then
  echo "ERROR: unknown chat command: $COMMAND_NAME" >&2
  usage >&2
  exit 2
fi

if [ ! -f "$COMMAND_SCRIPT" ]; then
  echo "ERROR: unknown chat command: $COMMAND_NAME" >&2
  usage >&2
  exit 2
fi

if [ ! -x "$COMMAND_SCRIPT" ]; then
  echo "ERROR: chat command is not executable: $COMMAND_SCRIPT" >&2
  exit 2
fi

exec "$COMMAND_SCRIPT" "$@"
