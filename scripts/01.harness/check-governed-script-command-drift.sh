#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.check-governed-script-command-drift
#   version: 1
#   status: active
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
#     path: .agentic/01.harness/standards/governed-script-permissions.md
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
      echo "ERROR: unknown argument: $1" >&2
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
      find .agentic -type f
    fi
    if [ -d docs/harness ]; then
      find docs/harness -type f
    fi
  } | sort -u
}

collect_paths_from_args() {
  local path

  for path in "${PATH_ARGS[@]}"; do
    if [ -d "$path" ]; then
      find "$path" -type f
    elif [ -f "$path" ]; then
      printf '%s\n' "$path"
    else
      echo "WARN: path does not exist, skipping: $path" >&2
    fi
  done | sort -u
}

is_scannable_path() {
  local path="$1"

  case "$path" in
    docs/harness/architecture/adrs/*.md)
      return 1
      ;;
    AGENTS.md|.agentic/*.md|.agentic/**/*.md|docs/harness/*.md|docs/harness/**/*.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

APPROVED_SCRIPTS="$(bash scripts/01.harness/run-governed-script.sh --list \
  | awk '$1 == "approved" { print $2 }')"

if [ -z "${APPROVED_SCRIPTS// }" ]; then
  echo "ERROR: governed runner returned no approved scripts." >&2
  exit 1
fi

if [ "${#PATH_ARGS[@]}" -gt 0 ]; then
  PATHS="$(collect_paths_from_args)"
else
  PATHS="$(collect_default_paths)"
fi

FINDINGS=0

scan_file() {
  local path="$1"
  local script
  local line_no
  local text
  local previous_text=""

  is_scannable_path "$path" || return 0

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
              case "$path:$script" in
                .agentic/00.chat/*:scripts/00.chat/*)
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
  done < <(grep -n 'scripts/' "$path" || true)
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
