#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.closeout.build-closeout-prompt
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: closeout
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Build and copy or print the governed chat closeout prompt.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.commands.readme
#     path: .agentic/00.chat/commands/README.md
#   - id: chat.script.command.dispatcher
#     path: scripts/00.chat/command/dispatcher/script.sh
#   effects:
#   - read-only

# shellcheck source=../../session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

print_prompt() {
  echo
  echo "Paste this into Codex / Claude / Mistral:"
  echo "$CLOSE_PROMPT"
}

copy_prompt_with_retry() {
  local label="$1"
  shift

  local attempt=1
  while [ "$attempt" -le 2 ]; do
    if printf '%s' "$CLOSE_PROMPT" | "$@"; then
      echo "Copied closeout prompt to clipboard."
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

BRANCH="$(git branch --show-current)"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch: $BRANCH" >&2
  exit 1
fi

LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE" >&2
  exit 1
fi

TASK="$(chat_log_metadata_value "$LOG_FILE" "task")"
WORKTREE="$(chat_log_metadata_value "$LOG_FILE" "worktree")"
LAYER="$(chat_log_metadata_value "$LOG_FILE" "layer")"
MODE="$(chat_log_metadata_value "$LOG_FILE" "mode")"

WORKTREE="${WORKTREE:-$(pwd)}"
LAYER="${LAYER:-chat}"
MODE="${MODE:-implementation}"

CLOSE_PROMPT="Task: close this chat by committing approved work if needed and merging the chat branch to local main
Session log: ${LOG_FILE}
Chat branch: ${BRANCH}
Chat worktree: ${WORKTREE}
Original task: ${TASK}
Layer: chat
Mode: implementation
Workflow: .agentic/00.chat/workflows/chat-promote-to-main.md

Default mode: read-only until I grant each required approval.

Use the current session log as the first source of truth.
For implementation, file-edit, test, or git-action work, delegate to a sub-agent when the assistant runtime supports it. If no sub-agent capability is available, continue directly as direct-fallback and say that fallback was used.
The supervising agent keeps responsibility for approval boundaries, write location, final review, and the final response.
After delegated or direct-fallback work, record it with:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/record-sub-agent-activity/script.sh --mode <sub-agent|direct-fallback> --status <completed|blocked|failed> --agent <label> --scope <scope> --summary <summary> --files <files> --checks <checks> --git-actions <git-actions> --blockers <blockers> --next-step <next-step>
If there is uncommitted task work, follow .agentic/00.chat/workflows/chat-commit.md and .agentic/00.chat/checklists/before-commit.md.
Ask for explicit approval before creating any task commit.
After any task commit, record it with:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/record-chat-commit/script.sh <sha> <message> <summary> [adr-impact]
Before committing task work, record context hygiene with:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/update-chat-log/script.sh context-hygiene <summary> <durable-evidence>
After task commit recording and any narrow session-log checkpoint, run /compact before continuing the same chat into another implementation phase.

Then follow .agentic/00.chat/workflows/chat-promote-to-main.md for local convergence.
Run the required gates and verification before merging.
Ask for explicit approval before merging into local main.
Do not push to origin unless I explicitly approve a separate push.
Return a summary covering delegation mode, fallback use, files changed, checks run, git actions, blockers, and next step.

If governance is missing or state is ambiguous, stop and explain the gap."

case "${CHAT_COPY_PROMPT:-copy}" in
  skip)
    print_prompt
    ;;
  copy)
    if command -v clip.exe >/dev/null 2>&1; then
      copy_prompt_with_retry "clip.exe" clip.exe || print_prompt
    elif command -v xclip >/dev/null 2>&1; then
      copy_prompt_with_retry "xclip" xclip -selection clipboard || print_prompt
    else
      print_prompt
    fi
    ;;
  *)
    echo "ERROR: invalid CHAT_COPY_PROMPT value: ${CHAT_COPY_PROMPT}" >&2
    echo "Use copy or skip." >&2
    exit 2
    ;;
esac
