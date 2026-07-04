#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.startup.start-chat-session
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: startup
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Create chat branch, session log, prompt, and chat-owned worktree.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.startup.start-new-chat
#     path: scripts/00.chat/startup/start-new-chat/script.sh
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   effects:
#   - branches
#   - worktrees
#   - writes-files
#   - stages-files
AGENTIC_ENV_FILE=".agentic/env.local"

# shellcheck source=../../session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"
# shellcheck source=../../worktree/paths/lib.sh
source "scripts/00.chat/worktree/paths/lib.sh"

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

OUTPUT_FORMAT="text"

case "${1:-}" in
  --json)
    OUTPUT_FORMAT="json"
    shift
    ;;
esac

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
CHAT_LIFECYCLE_WORKFLOW=".agentic/00.chat/workflows/chat-start.md"

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  BASE_BRANCH="$(git branch --show-current)"
fi

if [ -z "${BASE_BRANCH// }" ]; then
  echo "ERROR: could not determine a base branch for the chat branch." >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  WORKTREE_STATUS="dirty"
else
  WORKTREE_STATUS="clean"
fi

if [ "$OUTPUT_FORMAT" = "text" ]; then
  git status --short
fi

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
chat_lifecycle_workflow: ${CHAT_LIFECYCLE_WORKFLOW}
status: ready
raised_at_utc: ${RAISED_AT_UTC}
transcript_provider:
transcript_path:
transcript_bytes:
transcript_source:
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

${QUESTION}

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

## Main Refresh Conflicts

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
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.
EOF

if [ "$OUTPUT_FORMAT" = "text" ]; then
  echo "Created branch: $BRANCH"
  echo "Created log: $LOG_FILE"
  echo "Created worktree: $WORKTREE_PATH"
fi

if [ "$OUTPUT_FORMAT" = "text" ]; then
  CHAT_OPEN_WORKTREE_WINDOW="${CHAT_OPEN_WORKTREE_WINDOW:-skip}" \
    bash scripts/00.chat/worktree/open-window/script.sh "$WORKTREE_PATH"
fi

FIRST_PROMPT="Task: ${QUESTION}
Session log: ${LOG_FILE}
Chat worktree: ${WORKTREE_PATH}
Chat lifecycle workflow: ${CHAT_LIFECYCLE_WORKFLOW}
Latest context packet id:
Latest context packet routing summary:
Bootstrap worktree status: ${WORKTREE_STATUS}

If Bootstrap worktree status is dirty, reply exactly:
Blocked: dirty worktree. Confirm proceed?

Before that response, do not read workflows or run git status/dirty checks.

Governed startup bootstrap has already created this chat branch, worktree, and session log.
Default mode after startup bootstrap: read-only until I grant write permission in this chat.
For task writes or commit-boundary work, use the chat worktree above and follow the current workflow gates.
For prompt-level routing, use the current user request, this repo's assistant instructions, and any repo-provided context router if one exists. Do not assign the whole chat a durable layer, mode, or workflow.
Do not commit without my explicit approval."

emit_json_packet() {
  node - \
    "$QUESTION" \
    "$LOG_FILE" \
    "$WORKTREE_PATH" \
    "$CHAT_LIFECYCLE_WORKFLOW" \
    "$WORKTREE_STATUS" \
    "$FIRST_PROMPT" <<'NODE'
const [
  task,
  sessionLog,
  chatWorktree,
  chatLifecycleWorkflow,
  bootstrapWorktreeStatus,
  firstPrompt
] = process.argv.slice(2);

const packet = {
  schema: 'llm-workbench/startup-packet/v1',
  task,
  session_log: sessionLog,
  chat_worktree: chatWorktree,
  chat_lifecycle_workflow: chatLifecycleWorkflow,
  latest_context_packet_id: '',
  latest_context_packet_routing_summary: '',
  bootstrap_worktree_status: bootstrapWorktreeStatus,
  first_prompt: firstPrompt
};

process.stdout.write(`${JSON.stringify(packet, null, 2)}\n`);
NODE
}

print_first_prompt() {
  echo
  echo "Paste this into Codex / Claude / Mistral:"
  echo "$FIRST_PROMPT"
}

copy_first_prompt_with_retry() {
  local label="$1"
  shift

  local attempt=1
  while [ "$attempt" -le 2 ]; do
    if printf '%s' "$FIRST_PROMPT" | "$@"; then
      echo "Copied first agent prompt to clipboard."
      return 0
    fi

    if [ "$attempt" -lt 2 ]; then
      echo "Clipboard copy via ${label} failed; retrying..." >&2
      sleep 1
    fi

    attempt=$((attempt + 1))
  done

  echo "WARNING: Clipboard copy via ${label} failed; printing prompt instead." >&2
  return 1
}

if [ "$OUTPUT_FORMAT" = "json" ]; then
  git -C "$WORKTREE_PATH" add "$LOG_FILE"
  emit_json_packet
  exit 0
fi

if [ "${CHAT_COPY_PROMPT:-copy}" = "skip" ]; then
  print_first_prompt
elif command -v clip.exe >/dev/null 2>&1; then
  copy_first_prompt_with_retry "clip.exe" clip.exe || print_first_prompt
elif command -v pbcopy >/dev/null 2>&1; then
  copy_first_prompt_with_retry "pbcopy" pbcopy || print_first_prompt
elif command -v xclip >/dev/null 2>&1; then
  copy_first_prompt_with_retry "xclip" xclip -selection clipboard || print_first_prompt
else
  print_first_prompt
fi

case "${CHAT_CLEANUP_EMPTY_BRANCHES:-apply}" in
  apply)
    echo "Cleaning up empty chat branches..."
    bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --apply
    ;;
  dry-run)
    echo "Previewing empty chat branch cleanup..."
    bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --dry-run
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

git -C "$WORKTREE_PATH" add "$LOG_FILE"
