#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.run-governed-script
#   version: 2
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-11-05"
#   layer: 01.harness
#   domain: governance
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Run only explicitly governed repository scripts with approval-sensitive routing.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: harness.standards.governed-script-permissions
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   effects:
#   - read-only

usage() {
  cat <<'EOF'
Usage:
  run-governed-script.sh [--approved-action] <script> [args...]
  run-governed-script.sh --list

Runs only explicitly governed repository scripts.

Use --approved-action only after the current chat has explicit approval for the
action class governed by the active workflow.
EOF
}

read_failed() { echo "ERROR: governed-$1-read-failed" >&2; return 2; }
reject_script() {
  if [ "${LIST_MODE:-no}" != yes ]; then echo "ERROR: $1" >&2; fi
}
has_artifact_header() {
  local header status
  header="$(sed -n '1,80p' "$1" 2>/dev/null)" || { read_failed header; return 2; }
  if grep -Fq "agentic-artifact:" <<< "$header" 2>/dev/null; then return 0; else status=$?; fi
  [ "$status" -ne 1 ] || return 1
  read_failed header
}

metadata_has_line() {
  local path="$1"
  local value="$2"
  local header status

  header="$(sed -n '1,140p' "$path" 2>/dev/null)" || { read_failed effects; return 2; }
  if grep -Eq "^[#[:space:]]*-[[:space:]]*$value[[:space:]]*$" <<< "$header" 2>/dev/null; then return 0; else status=$?; fi
  [ "$status" -ne 1 ] || return 1
  read_failed effects
}

has_never_persistent_effect() {
  local path="$1"

  case "$path" in
    scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh)
      return 1
      ;;
  esac

  local effect status
  for effect in destructive push history-rewrite overwrites cloud database; do
    if metadata_has_line "$path" "$effect"; then return 0; else status=$?; fi
    [ "$status" -eq 1 ] || return "$status"
  done
  return 1
}

classify_script() {
  local path="$1" status effect read_only=no

  case "$path" in
    */lib.sh)
      reject_script "governed library files must not be invoked directly"
      return 1
      ;;
  esac

  case "$path" in
    scripts/[0-9][0-9].*/*.sh|scripts/[0-9][0-9].*/*/script.sh|scripts/[0-9][0-9].*/*/smoke-test.sh|\
    scripts/[0-9][0-9].*/*/*/script.sh|scripts/[0-9][0-9].*/*/*/smoke-test.sh)
      ;;
    scripts/shared/*.sh|scripts/shared/*/*.sh)
      reject_script "retired shared script path must not be invoked directly"
      return 1
      ;;
    *)
      reject_script "refused script outside canonical governed script paths"
      return 1
      ;;
  esac

  if [ ! -f "$path" ]; then
    reject_script "governed script does not exist"
    return 1
  fi

  if has_artifact_header "$path"; then
    :
  else
    status=$?
    [ "$status" -eq 1 ] || return "$status"
    reject_script "script is missing governed agentic-artifact metadata"
    return 1
  fi

  if has_never_persistent_effect "$path"; then
    reject_script "script has effects that are never persistent-auto-approved"
    return 1
  else
    status=$?
    [ "$status" -eq 1 ] || return "$status"
  fi

  if metadata_has_line "$path" read-only; then
    read_only=yes
  else
    status=$?
    [ "$status" -eq 1 ] || return "$status"
  fi
  if [ "$read_only" = yes ]; then
    for effect in writes-files commits network; do
      if metadata_has_line "$path" "$effect"; then
        read_only=no
        break
      else
        status=$?
        [ "$status" -eq 1 ] || return "$status"
      fi
    done
    if [ "$read_only" = yes ]; then printf '%s\n' always; return 0; fi
  fi

  printf '%s\n' "approved"
}

APPROVED_ACTION="no"

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

case "$1" in
  --approved-action)
    APPROVED_ACTION="yes"
    shift
    ;;
  --list)
    REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { read_failed root; exit 2; }
    cd "$REPO_ROOT"
    scripts="$(git ls-files 'scripts/*.sh' 'scripts/*/*.sh' 'scripts/*/*/*.sh' 'scripts/*/*/*/*.sh' 2>/dev/null)" || { read_failed inventory; exit 2; }
      while IFS= read -r script_path; do
        [ -n "$script_path" ] || continue
        if run_class="$(LIST_MODE=yes classify_script "$script_path")"; then
          printf '%s %s\n' "$run_class" "$script_path"
        else
          status=$?
          [ "$status" -eq 1 ] || exit "$status"
        fi
      done <<< "$scripts"
    exit 0
    ;;
  -h|--help)
    usage
    exit 0
    ;;
esac

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

SCRIPT_PATH="$1"
shift

case "$SCRIPT_PATH" in
  /*|*../*|../*|*"/.."|*".."|*"
"*)
    echo "ERROR: refused non-repository script path" >&2
    exit 1
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { read_failed root; exit 2; }
cd "$REPO_ROOT"

RUN_CLASS="$(classify_script "$SCRIPT_PATH")"

if [ "$RUN_CLASS" = "approved" ] && [ "$APPROVED_ACTION" != "yes" ]; then
  echo "ERROR: approval-sensitive script requires --approved-action" >&2
  exit 1
fi

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "ERROR: governed script does not exist" >&2
  exit 1
fi

exec bash "$SCRIPT_PATH" "$@"
