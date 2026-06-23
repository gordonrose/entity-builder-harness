#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Inventory references before moving, renaming, retiring, or removing repository artifact paths.
#   domain: migration
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/01.harness/workflows/migrate-artifact-paths.md
#     - .agentic/01.harness/standards/artifact-path-migrations.md
#   effects: read-only

usage() {
  cat <<'EOF'
Usage:
  plan-artifact-path-migration.sh <old-path> <new-path>

Reports old-path references by migration bucket so a path move can separate
active compatibility risk from historical session history.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ $# -ne 2 ]; then
  usage >&2
  exit 2
fi

OLD_PATH="$1"
NEW_PATH="$2"

case "$OLD_PATH:$NEW_PATH" in
  *"
"*|*":")
    echo "ERROR: paths must be non-empty single-line values." >&2
    exit 2
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

bucket_for_path() {
  case "$1" in
    AGENTS.md|CLAUDE.md|.agentic/routing-policy.yaml|scripts/00.chat/classification/*)
      printf '%s\n' "routing"
      ;;
    .agentic/*)
      printf '%s\n' "workflow"
      ;;
    docs/00.chat/*|scripts/00.chat/bootstrap/*|scripts/00.chat/upstream/*)
      printf '%s\n' "bootstrap"
      ;;
    scripts/*)
      printf '%s\n' "script"
      ;;
    docs/harness/architecture/adrs/*|docs/harness/architecture/*)
      printf '%s\n' "architecture"
      ;;
    commitLogs/*)
      printf '%s\n' "session-history"
      ;;
    *)
      printf '%s\n' "other"
      ;;
  esac
}

all_files() {
  {
    git ls-files
    git ls-files --others --exclude-standard
  } | sort -u
}

matching_refs() {
  local needle="$1"
  local file

  while IFS= read -r file; do
    [ -f "$file" ] || continue
    case "$file" in
      .git/*)
        continue
        ;;
    esac
    grep -nF "$needle" "$file" 2>/dev/null | while IFS=: read -r line_no text; do
      printf '%s\t%s\t%s\n' "$(bucket_for_path "$file")" "$file:$line_no" "$text"
    done
  done < <(all_files)
}

print_refs_for() {
  local label="$1"
  local needle="$2"
  local refs
  local bucket

  refs="$(matching_refs "$needle" || true)"
  printf '%s\n' "$label"
  printf 'path=%s\n' "$needle"

  if [ -z "$refs" ]; then
    printf 'references=0\n'
    return 0
  fi

  printf 'references=%s\n' "$(printf '%s\n' "$refs" | wc -l | tr -d ' ')"
  for bucket in routing workflow script bootstrap architecture session-history other; do
    if printf '%s\n' "$refs" | awk -F '\t' -v bucket="$bucket" '$1 == bucket { found = 1 } END { exit found ? 0 : 1 }'; then
      printf '\n[%s]\n' "$bucket"
      printf '%s\n' "$refs" | awk -F '\t' -v bucket="$bucket" '$1 == bucket { print $2 "\n  " $3 }'
    fi
  done
}

old_exists="no"
new_exists="no"
[ -e "$OLD_PATH" ] && old_exists="yes"
[ -e "$NEW_PATH" ] && new_exists="yes"

printf 'Artifact path migration plan\n'
printf 'old_path=%s\n' "$OLD_PATH"
printf 'new_path=%s\n' "$NEW_PATH"
printf 'old_exists=%s\n' "$old_exists"
printf 'new_exists=%s\n' "$new_exists"
printf '\n'

print_refs_for "Old path references" "$OLD_PATH"
printf '\n'
print_refs_for "New path references" "$NEW_PATH"
printf '\n'
printf 'Compatibility guidance\n'
printf -- '- active old-path references require alias, wrapper, pointer, or reference updates\n'
printf -- '- session-history references may remain as audit history\n'
printf -- '- layer namespace renames should also plan the matching scripts/ owner path\n'
