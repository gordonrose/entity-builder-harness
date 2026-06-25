#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.worktree.check-write-location
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: worktree
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Enforce task writes from chat-owned worktrees instead of the root integration
#     worktree.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.worktree.check-write-location.readme
#     path: scripts/00.chat/worktree/check-write-location/README.md
#   effects:
#   - read-only
usage() {
  cat <<'EOF'
Usage:
  check-write-location.sh [--allow-root-maintenance]

Fails when task writes would run from the root integration worktree. Chat task
work must run from that chat branch's canonical chat-owned worktree.

Set AGENTIC_ALLOW_ROOT_WRITE=1 only for explicit root maintenance operations.
EOF
}

ALLOW_ROOT_MAINTENANCE="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --allow-root-maintenance)
      ALLOW_ROOT_MAINTENANCE="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

# shellcheck source=../paths/lib.sh
source "$REPO_ROOT/scripts/00.chat/worktree/paths/lib.sh"

PRIMARY_PATH="$(chat_worktree_primary_path)"
PRIMARY_PATH="$(cd "$PRIMARY_PATH" && pwd -P)"
BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"

if [ "$REPO_ROOT" = "$PRIMARY_PATH" ]; then
  if [ "${AGENTIC_ALLOW_ROOT_WRITE:-}" = "1" ] || [ "$ALLOW_ROOT_MAINTENANCE" = "yes" ]; then
    echo "root-maintenance-allowed"
    exit 0
  fi

  echo "ERROR: refusing task write in root integration worktree: $REPO_ROOT" >&2
  echo "Use the chat-owned worktree for chat work." >&2
  exit 1
fi

case "$BRANCH" in
  chat/*) ;;
  *)
    echo "ERROR: current worktree is not on a chat branch: $BRANCH" >&2
    exit 1
    ;;
esac

EXPECTED_PATH="$(chat_worktree_path_for_branch "$PRIMARY_PATH" "$BRANCH")"
EXPECTED_PATH="$(cd "$EXPECTED_PATH" 2>/dev/null && pwd -P || printf '%s\n' "$EXPECTED_PATH")"

if [ "$REPO_ROOT" != "$EXPECTED_PATH" ]; then
  echo "ERROR: current chat branch is not in its canonical chat worktree." >&2
  echo "Current:  $REPO_ROOT" >&2
  echo "Expected: $EXPECTED_PATH" >&2
  exit 1
fi

echo "chat-worktree"
