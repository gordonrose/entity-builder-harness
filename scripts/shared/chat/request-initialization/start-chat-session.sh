#!/usr/bin/env bash
set -euo pipefail

AGENTIC_ENV_FILE=".agentic/env.local"

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

SLUG="$(echo "$QUESTION" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g' \
  | sed -E 's/^-+|-+$//g' \
  | cut -c1-60)"

BRANCH="chat/${STAMP}-${SLUG}"
LOG_DIR="commitLogs/${STAMP}-${SLUG}"
LOG_FILE="${LOG_DIR}/README.md"

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

git switch -c "$BRANCH"

mkdir -p "$LOG_DIR"

cat > "$LOG_FILE" <<EOF
# Chat Session: ${STAMP} ${SLUG}

<!-- agentic-session
id: ${STAMP}-${SLUG}
task: ${QUESTION}
branch: ${BRANCH}
layer: ${LAYER}
mode: ${MODE}
workflow: ${WORKFLOW}
status: ready
-->

## First user request

${QUESTION}

## Branch

\`${BRANCH}\`

## Session log

- Session started.
- Branch created.
- Commit log initialized.

## Intended work

TBD

## Commits

TBD

## Decisions / risks

TBD
EOF

git add "$LOG_FILE"

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

echo "Created branch: $BRANCH"
echo "Created log: $LOG_FILE"

FIRST_PROMPT="Task: ${QUESTION}
Session log: ${LOG_FILE}
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

Do not commit without my explicit approval."

if command -v clip.exe >/dev/null 2>&1; then
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
