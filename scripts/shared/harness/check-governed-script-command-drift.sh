#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Flag approval-sensitive governed script references that bypass the governed runner.
#   domain: governance
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
#     - .agentic/harness/standards/governed-script-permissions.md
#   effects: read-only

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
    [ -f AGENTS.md ] && printf '%s\n' AGENTS.md
    [ -d .agentic ] && find .agentic -type f
    [ -d docs/harness ] && find docs/harness -type f
    [ -d scripts/shared/chat/commands ] && find scripts/shared/chat/commands -type f
    [ -d scripts/shared/chat/request-initialization ] && find scripts/shared/chat/request-initialization -maxdepth 1 -type f
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
    scripts/shared/chat/commands/*.sh|scripts/shared/chat/request-initialization/*.sh)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

APPROVED_SCRIPTS="$(bash scripts/shared/harness/run-governed-script.sh --list \
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
            *"bash scripts/shared/harness/run-governed-script.sh --approved-action $script"*)
              ;;
            *)
              case "$path:$text" in
                scripts/shared/*:*"exec bash $script"*)
                  continue
                  ;;
              esac
              case "$previous_text" in
                *"bash scripts/shared/harness/run-governed-script.sh --approved-action \\"*)
                  continue
                  ;;
              esac
              printf '%s:%s\n' "$path" "$line_no"
              case "$text" in
                *"bash $script"*)
                  printf '  Type: direct-approved-governed-script\n'
                  ;;
                *)
                  printf '  Type: unrouted-approved-governed-script-reference\n'
                  ;;
              esac
              printf '  Text: %s\n' "$text"
              printf '  Suggestion: Use bash scripts/shared/harness/run-governed-script.sh --approved-action %s\n\n' "$script"
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
