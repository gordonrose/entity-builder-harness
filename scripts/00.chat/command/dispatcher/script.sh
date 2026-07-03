#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.command.dispatcher
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: command
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Dispatch chat subcommands from canonical scripts/00.chat/command folders.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.commands.readme
#     path: .agentic/00.chat/commands/README.md
#   - id: chat.script.command.dispatcher.readme
#     path: scripts/00.chat/command/dispatcher/README.md
#   - id: chat.script.startup.auto-start-missing-session
#     path: scripts/00.chat/startup/auto-start-missing-session/script.sh
#   effects:
#   - branches
#   - stages-files
#   - worktrees
#   - writes-files

COMMAND_DIR="scripts/00.chat/command"

usage() {
  cat <<EOF
Usage: npm run chat -- <command> [args...]

Commands:
EOF

  if [ -d "$COMMAND_DIR" ]; then
    find "$COMMAND_DIR" -mindepth 2 -maxdepth 2 -type f -path '*/script.sh' \
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

if [ "$COMMAND_NAME" = "open" ] && [ "${1:-}" = "window" ]; then
  COMMAND_NAME="open-window"
  shift
fi

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

exec bash "$COMMAND_SCRIPT" "$@"
