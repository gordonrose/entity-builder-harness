#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.check-governed-script-command-drift
#   version: 2
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-11-05"
#   layer: 01.harness
#   domain: governance
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Flag approval-sensitive governed script references that bypass the governed
#     runner.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.prepare-chat-session-before-commit
#     path: scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
#   - id: harness.standards.governed-script-permissions
#   effects:
#   - read-only

usage() {
  cat <<'EOF'
Usage:
  check-governed-script-command-drift.sh [--paths <path>...]

Flags active agent-facing artifacts that show approval-sensitive governed
scripts without routing through the governed runner.
EOF
}

PATH_ARGS=()
read_failed() { echo "ERROR: command-drift-$1-read-failed" >&2; return 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --paths)
      shift
      if [ $# -eq 0 ]; then
        echo "ERROR: --paths requires at least one path." >&2
        exit 2
      fi
      while [ $# -gt 0 ]; do
        PATH_ARGS+=("$1")
        shift
      done
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument" >&2
      usage >&2
      exit 2
      ;;
  esac
done

collect_default_paths() {
  {
    if [ -f AGENTS.md ]; then
      printf '%s\n' AGENTS.md
    fi
    if [ -d .agentic ]; then
      find .agentic -type f 2>/dev/null || { read_failed scan; return 2; }
    fi
    if [ -d docs/01.harness ]; then
      find docs/01.harness -type f 2>/dev/null || { read_failed scan; return 2; }
    fi
    if [ -d docs/03.product ]; then
      find docs/03.product -type f 2>/dev/null || { read_failed scan; return 2; }
    fi
    if [ -d docs/06.shared ]; then
      find docs/06.shared -type f 2>/dev/null || { read_failed scan; return 2; }
    fi
  } | sort -u 2>/dev/null
}

collect_paths_from_args() {
  local path

  for path in "${PATH_ARGS[@]}"; do
    if [ -d "$path" ]; then
      find "$path" -type f 2>/dev/null || { read_failed scan; return 2; }
    elif [ -f "$path" ]; then
      printf '%s\n' "$path"
    else
      echo "WARN: requested path does not exist, skipping" >&2
    fi
  done | sort -u 2>/dev/null
}

is_scannable_path() {
  local path="$1"

  case "$path" in
    AGENTS.md|.agentic/*.md|.agentic/**/*.md|docs/01.harness/*.md|docs/01.harness/**/*.md|docs/03.product/*.md|docs/03.product/**/*.md|docs/06.shared/*.md|docs/06.shared/**/*.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

APPROVED_SCRIPTS="$(bash scripts/01.harness/run-governed-script.sh --list \
  | awk '$1 == "approved" { print $2 }' 2>/dev/null)" || { read_failed classification; exit 2; }

if [ -z "${APPROVED_SCRIPTS// }" ]; then
  echo "ERROR: governed runner returned no approved scripts." >&2
  exit 1
fi

if [ "${#PATH_ARGS[@]}" -gt 0 ]; then
  PATHS="$(collect_paths_from_args)" || { read_failed paths; exit 2; }
else
  PATHS="$(collect_default_paths)" || { read_failed paths; exit 2; }
fi

FINDINGS=0

scan_file() {
  local path="$1"
  local script
  local line_no
  local text
  local previous_text=""
  local lines status

  is_scannable_path "$path" || return 0

  if lines="$(grep -n 'scripts/' "$path" 2>/dev/null)"; then
    :
  else
    status=$?
    [ "$status" -eq 1 ] || { read_failed content; return 2; }
  fi
  while IFS=: read -r line_no text; do
    [ -n "$line_no" ] || continue
    for script in $APPROVED_SCRIPTS; do
      case "$text" in
        *"$script"*)
          case "$text" in
            *"bash $script"*)
              ;;
            *)
              continue
              ;;
          esac
          case "$text" in
            *"bash scripts/01.harness/run-governed-script.sh --approved-action $script"*)
              ;;
            *)
              case "$path:$text" in
                scripts/shared/*:*"exec bash $script"*)
                  continue
                  ;;
              esac
              case "$previous_text" in
                *"bash scripts/01.harness/run-governed-script.sh --approved-action \\"*)
                  continue
                  ;;
              esac
              printf '%s:%s\n' "$path" "$line_no"
              printf '  Type: direct-approved-governed-script\n'
              printf '  Text: %s\n' "$text"
              printf '  Suggestion: Use bash scripts/01.harness/run-governed-script.sh --approved-action %s\n\n' "$script"
              FINDINGS=$((FINDINGS + 1))
              break
              ;;
          esac
          ;;
      esac
    done
    previous_text="$text"
  done <<< "$lines"
}

while IFS= read -r path; do
  [ -n "$path" ] || continue
  scan_file "$path"
done <<< "$PATHS"

if [ "$FINDINGS" -gt 0 ]; then
  echo "Governed script command drift found: $FINDINGS finding(s)." >&2
  exit 1
fi

echo "No governed script command drift found."
