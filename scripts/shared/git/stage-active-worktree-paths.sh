#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Superseded compatibility wrapper for recovery import into a chat-owned worktree.
#   domain: legacy-compatibility
#   portability: llm-workbench-compatibility
#   status: superseded-by scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh
#   used_by:
#     - docs/harness/architecture/adrs/0009-allow-automatic-session-branch-commit-context.md
#     - scripts/shared/git/smoke-test-with-chat-branch.sh
#   effects: writes-files, stages-files

usage() {
  cat <<'EOF'
Usage:
  stage-active-worktree-paths.sh <path>...

Compatibility wrapper for:
  scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh

Imports explicit paths from AGENTIC_ACTIVE_WORKTREE into the chat-owned
worktree for AGENTIC_SESSION_LOG, then stages those paths there.
EOF
}

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

if [ -z "${AGENTIC_ACTIVE_WORKTREE:-}" ]; then
  echo "ERROR: AGENTIC_ACTIVE_WORKTREE is not set. Run through with-chat-branch.sh." >&2
  exit 1
fi

if [ -z "${AGENTIC_SESSION_LOG:-}" ]; then
  echo "ERROR: AGENTIC_SESSION_LOG is not set. Run through with-chat-branch.sh or call the canonical recovery script with --session-log." >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

exec bash "$REPO_ROOT/scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh" \
  --session-log "$AGENTIC_SESSION_LOG" \
  --source-worktree "$AGENTIC_ACTIVE_WORKTREE" \
  -- "$@"
