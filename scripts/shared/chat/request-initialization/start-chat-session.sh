#!/usr/bin/env bash
set -euo pipefail

AGENTIC_ENV_FILE=".agentic/env.local"

# shellcheck source=../session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"
# shellcheck source=../../chat-worktree-paths.sh
source "scripts/shared/chat/chat-worktree-paths.sh"

CHAT_CLEANUP_EMPTY_BRANCHES_WAS_SET="no"
CHAT_CLEANUP_EMPTY_BRANCHES_SHELL_VALUE="${CHAT_CLEANUP_EMPTY_BRANCHES:-}"

if [ "${CHAT_CLEANUP_EMPTY_BRANCHES+x}" = "x" ]; then
  CHAT_CLEANUP_EMPTY_BRANCHES_WAS_SET="yes"
fi

if [ -f "$AGENTIC_ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$AGENTIC_ENV_FILE"
  set +a
fi

if [ "$CHAT_CLEANUP_EMPTY_BRANCHES_WAS_SET" = "yes" ]; then
  CHAT_CLEANUP_EMPTY_BRANCHES="$CHAT_CLEANUP_EMPTY_BRANCHES_SHELL_VALUE"
fi

if [ $# -gt 0 ]; then
  QUESTION="$*"
else
  read -r -p "Short task summary: " QUESTION
fi

if [ -z "${QUESTION// }" ] || [ "$QUESTION" = "new chat" ]; then
  echo "ERROR: Provide a meaningful task summary."
  echo "Example: add tenant auth guard"
  exit 1
fi

STAMP="$(date +"%Y-%m-%d-%H-%M")"
RAISED_AT_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

SLUG="$(echo "$QUESTION" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g' \
  | sed -E 's/^-+|-+$//g' \
  | cut -c1-60)"

BRANCH="chat/${STAMP}-${SLUG}"
LOG_DIR="$(chat_log_grouped_dir_for_session "${STAMP}-${SLUG}")"
LOG_FILE="${LOG_DIR}/README.md"
REPO_ROOT="$(chat_worktree_repo_root)"
WORKTREE_PATH="$(chat_worktree_path_for_branch "$REPO_ROOT" "$BRANCH")"
BASE_BRANCH="main"

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  BASE_BRANCH="$(git branch --show-current)"
fi

if [ -z "${BASE_BRANCH// }" ]; then
  echo "ERROR: could not determine a base branch for the chat branch." >&2
  exit 1
fi

CLASSIFICATION="$(bash scripts/shared/chat/request-initialization/classify-task.sh "$QUESTION" || true)"
LAYER="$(printf '%s\n' "$CLASSIFICATION" | sed -n 's/^Layer: //p')"
MODE="$(printf '%s\n' "$CLASSIFICATION" | sed -n 's/^Mode: //p')"
WORKFLOW="$(printf '%s\n' "$CLASSIFICATION" | sed -n 's/^Workflow: //p')"

LAYER="${LAYER:-unknown}"
MODE="${MODE:-unknown}"
WORKFLOW="${WORKFLOW:-unknown}"

if [ -n "$(git status --porcelain)" ]; then
  WORKTREE_STATUS="dirty"
else
  WORKTREE_STATUS="clean"
fi

git status --short

git branch "$BRANCH" "$BASE_BRANCH"
mkdir -p "${WORKTREE_PATH%/*}"
git worktree add --quiet "$WORKTREE_PATH" "$BRANCH"

mkdir -p "$WORKTREE_PATH/$LOG_DIR"

cat > "$WORKTREE_PATH/$LOG_FILE" <<EOF
# Chat Session: ${STAMP} ${SLUG}

<!-- agentic-session
id: ${STAMP}-${SLUG}
task: ${QUESTION}
branch: ${BRANCH}
worktree: ${WORKTREE_PATH}
layer: ${LAYER}
mode: ${MODE}
workflow: ${WORKFLOW}
status: ready
raised_at_utc: ${RAISED_AT_UTC}
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_tokens:
-->

## Initial Intent

${QUESTION}

## Branch

\`${BRANCH}\`

## Worktree

\`${WORKTREE_PATH}\`

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- None recorded yet.

## Activity Log

### ${RAISED_AT_UTC} - Session started

Initial intent: ${QUESTION}

## Commits

- None recorded yet.

## ADR Disposition

ADR needed: unknown
ADR path:
Reason:

## Session Metrics

Raised at UTC: ${RAISED_AT_UTC}
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated tokens:

## Notes

- None recorded yet.
EOF

echo "Created branch: $BRANCH"
echo "Created log: $LOG_FILE"
echo "Created worktree: $WORKTREE_PATH"

FIRST_PROMPT="Task: ${QUESTION}
Session log: ${LOG_FILE}
Chat worktree: ${WORKTREE_PATH}
Layer: ${LAYER}
Mode: ${MODE}
Workflow: ${WORKFLOW}
Bootstrap worktree status: ${WORKTREE_STATUS}

If Bootstrap worktree status is dirty, reply exactly:
Blocked: dirty worktree. Confirm proceed? Layer: ${LAYER}. Mode: ${MODE}. Workflow: ${WORKFLOW}

Do not read workflows before that response.
Do not run git status before that response.
Do not run dirty-worktree-check before that response.

Default mode: read-only.

Do not create, edit, move, delete, stage, commit, format, or patch files unless I explicitly give permission in the current chat.
Until then, inspect and propose only.

When write permission is granted, run task commands from the chat worktree above, not from the root integration worktree.
Before writing, run:
bash scripts/shared/git/check-write-location.sh

For approved commit-boundary operations, use this chat-owned worktree. Do not write task changes directly in the root integration worktree.

After write permission is granted, rename this chat's commitLog folder to a concise summary with:
bash scripts/shared/chat/rename-current-chat-log-folder.sh \"<short-summary>\"

Do not commit without my explicit approval."

if [ "${CHAT_COPY_PROMPT:-copy}" = "skip" ]; then
  echo
  echo "Paste this into Codex / Claude / Mistral:"
  echo "$FIRST_PROMPT"
elif command -v clip.exe >/dev/null 2>&1; then
  printf '%s' "$FIRST_PROMPT" | clip.exe
  echo "Copied first agent prompt to clipboard."
elif command -v xclip >/dev/null 2>&1; then
  printf '%s' "$FIRST_PROMPT" | xclip -selection clipboard
  echo "Copied first agent prompt to clipboard."
else
  echo
  echo "Paste this into Codex / Claude / Mistral:"
  echo "$FIRST_PROMPT"
fi

case "${CHAT_CLEANUP_EMPTY_BRANCHES:-apply}" in
  apply)
    echo "Cleaning up empty chat branches..."
    bash scripts/shared/git/cleanup-empty-chat-branches.sh --apply
    ;;
  dry-run)
    echo "Previewing empty chat branch cleanup..."
    bash scripts/shared/git/cleanup-empty-chat-branches.sh --dry-run
    ;;
  0|false|no|skip)
    echo "Skipping empty chat branch cleanup."
    ;;
  *)
    echo "ERROR: invalid CHAT_CLEANUP_EMPTY_BRANCHES value: ${CHAT_CLEANUP_EMPTY_BRANCHES}" >&2
    echo "Use apply, dry-run, skip, 0, false, or no." >&2
    exit 2
    ;;
esac

(cd "$WORKTREE_PATH" && bash scripts/shared/chat/generate-commit-log-summary.sh >/dev/null)
git -C "$WORKTREE_PATH" add "$LOG_FILE" commitLogs/README.md
