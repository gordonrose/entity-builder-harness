#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Dispatch chat subcommands from scripts/shared/chat/commands.
#   domain: command
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/commands/README.md
#     - scripts/00.chat/command/dispatcher/README.md
#     - scripts/chat/chat-command.sh
#     - scripts/shared/chat/request-initialization/auto-start-missing-session.sh
#   effects: branches, worktrees, writes-files, stages-files

COMMAND_DIR="scripts/shared/chat/commands"

usage() {
  cat <<EOF
Usage: chat-command.sh <command> [args...]

Commands:
EOF

  if [ -d "$COMMAND_DIR" ]; then
    find "$COMMAND_DIR" -maxdepth 1 -type f -name '*.sh' -perm -u+x \
      | sed -E 's#^.*/([^/]+)\.sh$#  \1#' \
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

COMMAND_SCRIPT="${COMMAND_DIR}/${COMMAND_NAME}.sh"

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
