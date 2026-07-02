#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.run-governed-script
#   version: 1
#   status: active
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
#     path: .agentic/01.harness/standards/governed-script-permissions.md
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

has_artifact_header() {
  sed -n '1,80p' "$1" | grep -Fq "agentic-artifact:"
}

metadata_has_line() {
  local path="$1"
  local value="$2"

  sed -n '1,140p' "$path" | grep -Eq "^[#[:space:]]*-[[:space:]]*$value[[:space:]]*$"
}

has_never_persistent_effect() {
  local path="$1"

  case "$path" in
    scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh)
      return 1
      ;;
  esac

  metadata_has_line "$path" "destructive" ||
    metadata_has_line "$path" "push" ||
    metadata_has_line "$path" "history-rewrite" ||
    metadata_has_line "$path" "overwrites" ||
    metadata_has_line "$path" "cloud" ||
    metadata_has_line "$path" "database"
}

classify_script() {
  local path="$1"

  case "$path" in
    */lib.sh)
      echo "ERROR: governed library files must not be invoked directly: $path" >&2
      return 1
      ;;
  esac

  case "$path" in
    scripts/[0-9][0-9].*/*.sh|scripts/[0-9][0-9].*/*/script.sh|scripts/[0-9][0-9].*/*/smoke-test.sh|\
    scripts/[0-9][0-9].*/*/*/script.sh|scripts/[0-9][0-9].*/*/*/smoke-test.sh)
      ;;
    scripts/shared/*.sh|scripts/shared/*/*.sh)
      echo "ERROR: retired shared script path must not be invoked directly: $path" >&2
      return 1
      ;;
    *)
      echo "ERROR: refused script outside canonical governed script paths: $path" >&2
      return 1
      ;;
  esac

  if [ ! -f "$path" ]; then
    echo "ERROR: governed script does not exist: $path" >&2
    return 1
  fi

  if ! has_artifact_header "$path"; then
    echo "ERROR: script is missing governed agentic-artifact metadata: $path" >&2
    return 1
  fi

  if has_never_persistent_effect "$path"; then
    echo "ERROR: script has effects that are never persistent-auto-approved: $path" >&2
    return 1
  fi

  if metadata_has_line "$path" "read-only" &&
    ! metadata_has_line "$path" "writes-files" &&
    ! metadata_has_line "$path" "commits" &&
    ! metadata_has_line "$path" "network"; then
    printf '%s\n' "always"
    return 0
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
    REPO_ROOT="$(git rev-parse --show-toplevel)"
    cd "$REPO_ROOT"
    git ls-files 'scripts/*.sh' 'scripts/*/*.sh' 'scripts/*/*/*.sh' 'scripts/*/*/*/*.sh' |
      while IFS= read -r script_path; do
        run_class="$(classify_script "$script_path" 2>/dev/null || true)"
        if [ -n "$run_class" ]; then
          printf '%s %s\n' "$run_class" "$script_path"
        fi
      done
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
    echo "ERROR: refused non-repository script path: $SCRIPT_PATH" >&2
    exit 1
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

RUN_CLASS="$(classify_script "$SCRIPT_PATH")"

if [ "$RUN_CLASS" = "approved" ] && [ "$APPROVED_ACTION" != "yes" ]; then
  echo "ERROR: approval-sensitive script requires --approved-action: $SCRIPT_PATH" >&2
  exit 1
fi

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "ERROR: governed script does not exist: $SCRIPT_PATH" >&2
  exit 1
fi

exec bash "$SCRIPT_PATH" "$@"
