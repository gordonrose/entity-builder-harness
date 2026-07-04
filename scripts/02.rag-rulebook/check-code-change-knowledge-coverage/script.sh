#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-code-change-knowledge-coverage
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#   - agentic
#   - architecture
#   kind: script
#   purpose: Require RAG knowledge disposition for knowledge-bearing code changes.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   effects:
#   - read-only
#   used_by:
#   - id: rag-rulebook.script.commit-gates
#     path: scripts/02.rag-rulebook/commit-gates/script.sh
#   - id: rag-rulebook.script.check-code-change-knowledge-coverage.readme
#     path: scripts/02.rag-rulebook/check-code-change-knowledge-coverage/README.md

MODE=""
JSON="no"

usage() {
  cat <<'EOF'
Usage:
  check-code-change-knowledge-coverage/script.sh --staged [--json]
  check-code-change-knowledge-coverage/script.sh --current [--json]

Requires the current chat log to record a RAG Knowledge Disposition when
knowledge-bearing code paths changed.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --staged|--current)
      if [ -n "$MODE" ]; then
        usage >&2
        exit 2
      fi
      MODE="${1#--}"
      shift
      ;;
    --json)
      JSON="yes"
      shift
      ;;
    -h|--help)
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

if [ -z "$MODE" ]; then
  usage >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

month_name() {
  case "$1" in
    01) printf 'jan\n' ;;
    02) printf 'feb\n' ;;
    03) printf 'mar\n' ;;
    04) printf 'apr\n' ;;
    05) printf 'may\n' ;;
    06) printf 'jun\n' ;;
    07) printf 'jul\n' ;;
    08) printf 'aug\n' ;;
    09) printf 'sep\n' ;;
    10) printf 'oct\n' ;;
    11) printf 'nov\n' ;;
    12) printf 'dec\n' ;;
    *) return 1 ;;
  esac
}

log_file_for_session() {
  local session_id="$1"
  local year month day month log

  year="${session_id:0:4}"
  month="${session_id:5:2}"
  day="${session_id:8:2}"
  month="$(month_name "$month")"
  log="commitLogs/${year}/${month}/${day}/${session_id}/README.md"

  if [ -f "$log" ]; then
    printf '%s\n' "$log"
    return 0
  fi

  find "commitLogs/${year}/${month}/${day}" -mindepth 2 -maxdepth 2 -type f -name README.md 2>/dev/null \
    | while IFS= read -r candidate; do
        if sed -n '/<!-- agentic-session/,/-->/p' "$candidate" | grep -Eq "^(id: ${session_id}|branch: chat/${session_id})$"; then
          printf '%s\n' "$candidate"
          return 0
        fi
      done \
    | head -n 1
}

changed_paths() {
  if [ "$MODE" = "staged" ]; then
    git diff --cached --name-only
    return
  fi

  {
    git diff --name-only HEAD
    git ls-files --others --exclude-standard
  } | sort -u
}

is_knowledge_bearing_path() {
  case "$1" in
    packages/core/*|platform/*|infra/*|.github/workflows/*)
      return 0
      ;;
    apps/*/app.mount.ts|apps/*/app.manifest.ts)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

knowledge_paths="$(
  changed_paths \
    | while IFS= read -r path; do
        if [ -n "$path" ] && is_knowledge_bearing_path "$path"; then
          printf '%s\n' "$path"
        fi
      done \
    | sort -u
)"

if [ -z "${knowledge_paths// }" ]; then
  if [ "$JSON" = "yes" ]; then
    printf '{"status":"no-impact","knowledge_bearing_paths":[]}\n'
  else
    echo "No knowledge-bearing code changes detected."
  fi
  exit 0
fi

branch="$(git branch --show-current)"
case "$branch" in
  chat/*) session_id="${branch#chat/}" ;;
  *)
    echo "ERROR: current branch is not a chat branch: $branch" >&2
    exit 1
    ;;
esac

log_file="$(log_file_for_session "$session_id")"
if [ -z "${log_file// }" ] || [ ! -f "$log_file" ]; then
  echo "ERROR: missing chat session log for RAG knowledge disposition: $session_id" >&2
  exit 1
fi

section="$(
  awk '
    $0 == "## RAG Knowledge Disposition" { in_section = 1; next }
    in_section && /^## / { exit }
    in_section { print }
  ' "$log_file"
)"

status="$(printf '%s\n' "$section" | sed -n 's/^Status: //p' | head -n 1)"
reason="$(printf '%s\n' "$section" | sed -n 's/^Reason: //p' | head -n 1)"
evidence_count="$(printf '%s\n' "$section" | awk '
  /^Evidence:/ { in_evidence = 1; next }
  /^Corpus gaps:/ { in_evidence = 0 }
  in_evidence && /^- / { count++ }
  END { print count + 0 }
')"
gap_count="$(printf '%s\n' "$section" | awk '
  /^Corpus gaps:/ { in_gaps = 1; next }
  in_gaps && /^- / { count++ }
  END { print count + 0 }
')"

case "$status" in
  covered)
    if [ "$evidence_count" -eq 0 ]; then
      echo "ERROR: RAG Knowledge Disposition status covered requires at least one evidence path." >&2
      exit 1
    fi
    ;;
  no-impact)
    if [ -z "${reason// }" ]; then
      echo "ERROR: RAG Knowledge Disposition status no-impact requires a reason." >&2
      exit 1
    fi
    ;;
  deferred-with-gap)
    if [ "$gap_count" -eq 0 ]; then
      echo "ERROR: RAG Knowledge Disposition status deferred-with-gap requires at least one corpus gap path." >&2
      exit 1
    fi
    ;;
  "")
    echo "ERROR: knowledge-bearing code changes require ## RAG Knowledge Disposition in $log_file" >&2
    printf '%s\n' "$knowledge_paths" >&2
    exit 1
    ;;
  *)
    echo "ERROR: unsupported RAG Knowledge Disposition status: $status" >&2
    exit 1
    ;;
esac

if [ "$JSON" = "yes" ]; then
  python3 - "$status" "$log_file" "$knowledge_paths" <<'PY'
import json
import sys

status, log_file, paths = sys.argv[1:]
print(json.dumps({
    "status": status,
    "log_file": log_file,
    "knowledge_bearing_paths": [path for path in paths.splitlines() if path],
}, sort_keys=True))
PY
else
  echo "RAG knowledge disposition is recorded: $status"
fi
