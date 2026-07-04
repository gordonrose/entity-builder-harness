#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.record-knowledge-disposition
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: session-log
#   disciplines:
#   - agentic
#   - architecture
#   kind: script
#   purpose: Record the RAG/rulebook knowledge disposition for knowledge-bearing code changes.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   effects:
#   - writes-files
#   used_by:
#   - id: rag-rulebook.script.check-code-change-knowledge-coverage
#     path: scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh
#   - id: rag-rulebook.script.record-knowledge-disposition.readme
#     path: scripts/02.rag-rulebook/record-knowledge-disposition/README.md

usage() {
  cat <<'EOF'
Usage:
  record-knowledge-disposition/script.sh covered <reason> <evidence-path>...
  record-knowledge-disposition/script.sh no-impact <reason>
  record-knowledge-disposition/script.sh deferred-with-gap <reason> <corpus-gap-path>...
EOF
}

if [ $# -lt 2 ]; then
  usage >&2
  exit 2
fi

STATUS="$1"
REASON="$2"
shift 2

case "$STATUS" in
  covered)
    if [ $# -lt 1 ]; then
      echo "ERROR: covered requires at least one evidence path." >&2
      exit 2
    fi
    ;;
  no-impact)
    if [ $# -ne 0 ]; then
      echo "ERROR: no-impact does not accept evidence or gap paths." >&2
      exit 2
    fi
    ;;
  deferred-with-gap)
    if [ $# -lt 1 ]; then
      echo "ERROR: deferred-with-gap requires at least one corpus gap path." >&2
      exit 2
    fi
    ;;
  *)
    echo "ERROR: unsupported RAG knowledge disposition status: $STATUS" >&2
    usage >&2
    exit 2
    ;;
esac

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# shellcheck source=../../00.chat/session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

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

TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
ENTRY_FILE="$(mktemp)"
TMP_FILE="$(mktemp)"

cleanup() {
  rm -f "$ENTRY_FILE" "$TMP_FILE"
}

trap cleanup EXIT

{
  echo "## RAG Knowledge Disposition"
  echo
  echo "Status: $STATUS"
  echo "Reason: $REASON"
  echo "Evidence:"
  if [ "$STATUS" = "covered" ]; then
    for path in "$@"; do
      echo "- $path"
    done
  else
    echo "- None."
  fi
  echo "Corpus gaps:"
  if [ "$STATUS" = "deferred-with-gap" ]; then
    for path in "$@"; do
      echo "- $path"
    done
  else
    echo "- None."
  fi
} > "$ENTRY_FILE"

awk -v entry_path="$ENTRY_FILE" '
  BEGIN {
    while ((getline line < entry_path) > 0) {
      entry = entry (entry == "" ? "" : "\n") line
    }
    close(entry_path)
  }
  $0 == "## RAG Knowledge Disposition" {
    if (inserted == 0) {
      print entry
      inserted = 1
    }
    skip = 1
    next
  }
  skip && /^## / {
    skip = 0
  }
  !skip {
    print
  }
  END {
    if (inserted == 0) {
      print ""
      print entry
    }
  }
' "$LOG_FILE" > "$TMP_FILE"
mv "$TMP_FILE" "$LOG_FILE"

bash scripts/00.chat/session-log/update-chat-log/script.sh decision \
  "Record RAG knowledge disposition: $STATUS" \
  "$REASON"

echo "Recorded RAG knowledge disposition in $LOG_FILE"
