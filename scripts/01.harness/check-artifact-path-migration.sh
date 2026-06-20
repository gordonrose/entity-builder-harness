#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Validate that a path migration does not leave unapproved active old-path references.
#   domain: migration
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/01.harness/workflows/migrate-artifact-paths.md
#     - .agentic/01.harness/standards/artifact-path-migrations.md
#   effects: read-only

usage() {
  cat <<'EOF'
Usage:
  check-artifact-path-migration.sh [--allow-active-old-path] <old-path> <new-path>

Fails when active files still reference <old-path> unless compatibility for the
old path has been explicitly approved with --allow-active-old-path.
EOF
}

ALLOW_ACTIVE_OLD_PATH="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --allow-active-old-path)
      ALLOW_ACTIVE_OLD_PATH="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

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

all_files() {
  {
    git ls-files
    git ls-files --others --exclude-standard
  } | sort -u
}

is_historical_path() {
  case "$1" in
    commitLogs/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

active_old_refs() {
  local file

  while IFS= read -r file; do
    [ -f "$file" ] || continue
    is_historical_path "$file" && continue
    grep -nF "$OLD_PATH" "$file" 2>/dev/null | while IFS=: read -r line_no text; do
      printf '%s:%s\n  %s\n' "$file" "$line_no" "$text"
    done
  done < <(all_files)
}

ACTIVE_REFS="$(active_old_refs || true)"

if [ -n "$ACTIVE_REFS" ] && [ "$ALLOW_ACTIVE_OLD_PATH" != "yes" ]; then
  echo "ERROR: active old-path references remain: $OLD_PATH" >&2
  printf '%s\n' "$ACTIVE_REFS" >&2
  echo "Update active references or rerun with --allow-active-old-path after approving an alias, wrapper, or pointer." >&2
  exit 1
fi

if [ -e "$NEW_PATH" ]; then
  new_exists="yes"
else
  new_exists="no"
fi

if [ -n "$ACTIVE_REFS" ]; then
  active_old_refs="present"
else
  active_old_refs="none"
fi

printf 'artifact_path_migration_check=ok\n'
printf 'old_path=%s\n' "$OLD_PATH"
printf 'new_path=%s\n' "$NEW_PATH"
printf 'new_exists=%s\n' "$new_exists"
printf 'active_old_refs=%s\n' "$active_old_refs"
