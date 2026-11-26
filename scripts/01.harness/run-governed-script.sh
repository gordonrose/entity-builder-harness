#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.run-governed-script
#   version: 3
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-11-26"
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
has_effect() {
  local value="$1" declared
  for declared in "${script_effects[@]}"; do
    [[ "$declared" == "$value" ]] && return 0
  done
  return 1
}

has_never_persistent_effect() {
  local path="$1"
  has_effect aws-mutation && return 0
  if has_effect destructive && [ "$path" != scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh ]; then
    return 0
  fi
  return 1
}

classify_script() {
  local path="$1" status effects_text
  local -a script_effects=()

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

  # The shared parser distinguishes the actual header from examples and gives
  # inline/block YAML one meaning. Read again on every invocation; no cache.
  if effects_text="$(python3 -B - "$path" 2>/dev/null <<'PY'
import sys
from pathlib import Path
try:
    sys.path.insert(0, 'scripts/01.harness/artifact-metadata')
    from header_discovery import HeaderError, parse_header_text, script_effects
    import yaml
except ImportError:
    sys.exit(2)
try:
    source = Path(sys.argv[1]).read_text(encoding='utf-8')
    allowed = script_effects()
except (OSError, UnicodeError, ValueError, KeyError, TypeError, yaml.YAMLError):
    sys.exit(2)
try:
    metadata = parse_header_text(source).get('agentic-artifact', {})
    effects = metadata.get('effects')
    if metadata.get('kind') != 'script' or not isinstance(effects, list) or not effects or any(
        not isinstance(effect, str) or effect not in allowed for effect in effects
    ):
        sys.exit(1)
except HeaderError:
    sys.exit(1)
print('\n'.join(effects))
PY
)"; then
    mapfile -t script_effects <<< "$effects_text"
  else
    status=$?
    if [ "$status" -eq 1 ]; then
      reject_script "script metadata or effects are missing, invalid or unknown"
      return 1
    fi
    read_failed metadata
    return 2
  fi
  if has_never_persistent_effect "$path"; then
    reject_script "script has effects that are never persistent-auto-approved"
    return 1
  else
    status=$?
    [ "$status" -eq 1 ] || return "$status"
  fi

  if [ "${#script_effects[@]}" -eq 1 ] && has_effect read-only; then
    printf '%s\n' always
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
