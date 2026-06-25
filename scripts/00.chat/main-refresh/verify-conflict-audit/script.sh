#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.main-refresh.verify-conflict-audit
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: main-refresh
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Verify main-refresh conflict paths are recorded in the chat session log.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-refresh-from-main
#     path: .agentic/00.chat/workflows/chat-refresh-from-main.md
#   - id: chat.standards.main-refresh-conflict-types
#     path: .agentic/00.chat/standards/main-refresh-conflict-types.md
#   effects:
#   - read-only

# shellcheck source=../../session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

usage() {
  cat <<'EOF'
Usage:
  script.sh [--session-log <path>] [--path <conflict-path>]... [--paths-file <file>]

Verifies that each conflict path has a matching `- Path: `<path>`` entry under
the chat session log's `## Main Refresh Conflicts` section.

If no paths are supplied, unresolved conflict paths are read from the Git index.
For resolved preflight conflicts, pass the captured paths explicitly.
EOF
}

SESSION_LOG=""
PATHS_FILE=""
PATHS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --session-log)
      SESSION_LOG="${2:-}"
      shift 2
      ;;
    --path)
      PATHS+=("${2:-}")
      shift 2
      ;;
    --paths-file)
      PATHS_FILE="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: not inside a Git worktree." >&2
  exit 1
fi

if [ -n "$PATHS_FILE" ]; then
  if [ ! -f "$PATHS_FILE" ]; then
    echo "ERROR: missing paths file: $PATHS_FILE" >&2
    exit 1
  fi

  while IFS= read -r path; do
    [ -z "$path" ] && continue
    PATHS+=("$path")
  done < "$PATHS_FILE"
fi

if [ "${#PATHS[@]}" -eq 0 ]; then
  while IFS= read -r path; do
    [ -z "$path" ] && continue
    PATHS+=("$path")
  done < <(git diff --name-only --diff-filter=U)
fi

if [ -z "$SESSION_LOG" ]; then
  BRANCH="$(git branch --show-current)"
  if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH" 2>/dev/null)"; then
    if [ -n "${AGENTIC_SESSION_LOG:-}" ]; then
      SESSION_LOG="$AGENTIC_SESSION_LOG"
    else
      echo "ERROR: could not infer chat session from branch. Use --session-log." >&2
      exit 1
    fi
  else
    SESSION_LOG="$(chat_log_file_for_session "$SESSION_ID")"
  fi
fi

if [ ! -f "$SESSION_LOG" ]; then
  echo "ERROR: missing session log: $SESSION_LOG" >&2
  exit 1
fi

if [ "${#PATHS[@]}" -eq 0 ]; then
  echo "No conflict paths supplied or unresolved in the Git index."
  echo "For resolved preflight conflicts, rerun with --path or --paths-file."
  exit 0
fi

AUDIT_PATHS="$(
  awk '
    $0 == "## Main Refresh Conflicts" { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section && /^- Path: `/ {
      line = $0
      sub(/^- Path: `/, "", line)
      sub(/`$/, "", line)
      print line
    }
  ' "$SESSION_LOG"
)"

FAILED=0

for path in "${PATHS[@]}"; do
  if [ -z "$path" ]; then
    continue
  fi

  if printf '%s\n' "$AUDIT_PATHS" | grep -Fxq "$path"; then
    echo "OK: conflict path recorded: $path"
  else
    echo "ERROR: conflict path missing from session audit: $path" >&2
    FAILED=1
  fi
done

if [ "$FAILED" -ne 0 ]; then
  exit 1
fi

echo "Main refresh conflict audit verified."
