#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.bootstrap.audit-chat-bootstrap-file-set
#   version: 2
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: bootstrap
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Audit the portable chat bootstrap script and support-file set.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.bootstrap-chat-workbench-repo
#     path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   - id: shared.standard.upstream-repo-bootstrap
#     path: .agentic/shared/standards/upstream-repo-bootstrap.md
#   - id: harness.script.run-governed-script
#     path: scripts/01.harness/run-governed-script.sh
#   effects:
#   - read-only

usage() {
  cat <<'EOF'
Usage:
  audit-chat-bootstrap-file-set.sh

Reports the script and support-file dependency set for the portable chat
harness bootstrap.

The audit starts from package chat commands, chat workflows, shared process
artifacts used by chat startup/commit/promotion, and the governed script runner.
It then follows script references to produce a required script set and candidate
unreferenced scripts.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

read_failed() {
  echo "ERROR: bootstrap-audit-observation-unavailable; stage=$1." >&2
  exit 2
}
observe() {
  local stage="$1"; shift
  "$@" 2>/dev/null || read_failed "$stage"
}
matches() {
  local status
  if grep "$@" 2>/dev/null; then return 0; else status=$?; fi
  [ "$status" -eq 1 ] && return 1
  read_failed content-match
}
optional_matches() {
  if matches "$@"; then :; fi
}
REPO_ROOT="$(observe repository-root git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/chat-bootstrap-audit.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

SEEDS="$TMP_DIR/seeds.txt"
SEEN="$TMP_DIR/seen.txt"
QUEUE="$TMP_DIR/queue.txt"
NEXT_QUEUE="$TMP_DIR/next-queue.txt"
SCRIPT_REFS="$TMP_DIR/script-refs.txt"
MISSING="$TMP_DIR/missing.txt"
ALL_SCRIPTS="$TMP_DIR/all-scripts.txt"
REQUIRED="$TMP_DIR/required.txt"
UNREFERENCED="$TMP_DIR/unreferenced.txt"
VALIDATION="$TMP_DIR/validation.txt"
COMPATIBILITY="$TMP_DIR/compatibility.txt"
UNCLASSIFIED="$TMP_DIR/unclassified.txt"

: > "$SEEDS"
: > "$SEEN"
: > "$QUEUE"
: > "$SCRIPT_REFS"
: > "$MISSING"

add_if_exists() {
  local path="$1"

  if [ -e "$path" ]; then
    printf '%s\n' "$path" >> "$SEEDS"
  fi
}

add_tree_if_exists() {
  local path="$1"

  if [ -d "$path" ]; then
    observe seed-tree find "$path" -type f >> "$SEEDS"
  fi
}

add_if_exists "AGENTS.md"
add_tree_if_exists ".agentic/00.chat"
add_tree_if_exists ".agentic/shared/standards"
add_tree_if_exists ".agentic/shared/workflows"
add_if_exists "package.json"
add_if_exists "scripts/01.harness/run-governed-script.sh"
add_if_exists "scripts/01.harness/check-deterministic-process-drift.sh"
add_tree_if_exists "scripts/01.harness/artifact-metadata"
add_if_exists "scripts/01.harness/check-artifact-metadata-headers.sh"
add_if_exists "scripts/01.harness/check-governed-script-command-drift.sh"
add_if_exists "scripts/01.harness/plan-artifact-path-migration.sh"
add_if_exists "scripts/01.harness/check-artifact-path-migration.sh"

observe seed-sort sort -u "$SEEDS" > "$QUEUE"

extract_script_refs() {
  local path="$1"
  local dir

  optional_matches -Eo 'scripts/[A-Za-z0-9._/-]+\.(sh|js|mjs|cjs|tsv|json)' "$path" \
    | optional_matches -E '^scripts/(00\.chat|01\.harness|chat|harness|shared)/' || return $?

  case "$path" in
    scripts/*)
      dir="$(dirname "$path")"
      optional_matches -Eo 'SCRIPT_DIR/[A-Za-z0-9._/-]+\.(sh|js|mjs|cjs|tsv|json)' "$path" \
        | observe reference-transform sed "s#^SCRIPT_DIR/#${dir}/#" || return $?
      optional_matches -Eo 'dirname "\$0"\)/[A-Za-z0-9._/-]+\.(sh|js|mjs|cjs|tsv|json)' "$path" \
        | observe reference-transform sed "s#^dirname \"\\\$0\")/#${dir}/#" || return $?
      ;;
  esac
}

while [ -s "$QUEUE" ]; do
  : > "$NEXT_QUEUE"

  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if matches -Fxq -- "$path" "$SEEN"; then continue; fi
    printf '%s\n' "$path" >> "$SEEN"

    if [ ! -f "$path" ]; then
      printf '%s\n' "$path" >> "$MISSING"
      continue
    fi

    refs="$(extract_script_refs "$path")" || exit $?
    while IFS= read -r ref; do
      [ -n "$ref" ] || continue
      printf '%s\n' "$ref" >> "$SCRIPT_REFS"
      if [ -f "$ref" ]; then
        case "$ref" in
          scripts/*)
            if ! matches -Fxq -- "$ref" "$SEEN"; then
              printf '%s\n' "$ref" >> "$NEXT_QUEUE"
            fi
            ;;
        esac
      else
        printf '%s\n' "$ref" >> "$MISSING"
      fi
    done <<< "$refs"
  done < "$QUEUE"

  observe queue-sort sort -u "$NEXT_QUEUE" > "$QUEUE"
done

observe script-tree find scripts -type f \
  \( -name '*.sh' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.tsv' -o -name '*.json' \) \
  | observe script-sort sort -u > "$ALL_SCRIPTS"

{
  optional_matches '^scripts/' "$SEEN"
  observe reference-sort sort -u "$SCRIPT_REFS"
} | observe required-sort sort -u > "$REQUIRED"

observe candidate-comparison comm -23 "$ALL_SCRIPTS" "$REQUIRED" > "$UNREFERENCED"
while IFS= read -r path; do
  [ -n "$path" ] || continue
  if matches -Eq '^([#[:space:]]*|[[:space:]]*//[[:space:]]*)portability: .*compatibility' "$path"; then
    printf '%s\n' "$path"
  fi
done < "$UNREFERENCED" > "$COMPATIBILITY"
{
  optional_matches -E '/smoke-test-[^/]+\.sh$|/smoke-test\.sh$|/with-chat-branch\.sh$' "$UNREFERENCED"
  cat "$COMPATIBILITY"
} | observe validation-sort sort -u > "$VALIDATION"
observe classification-comparison comm -23 "$UNREFERENCED" "$VALIDATION" > "$UNCLASSIFIED"

echo "Chat bootstrap script file set audit"
echo
echo "Seed surfaces scanned:"
echo "- AGENTS.md"
echo "- .agentic/00.chat/"
echo "- .agentic/shared/standards/"
echo "- .agentic/shared/workflows/"
echo "- package.json chat scripts"
echo "- governed runner and deterministic harness checks"
echo
echo "Required scripts and support files:"
cat "$REQUIRED"
echo
echo "Validation and compatibility candidates:"
if [ -s "$VALIDATION" ]; then
  cat "$VALIDATION"
else
  echo "(none)"
fi
echo
echo "Unclassified candidates:"
if [ -s "$UNCLASSIFIED" ]; then
  cat "$UNCLASSIFIED"
else
  echo "(none)"
fi

if [ -s "$MISSING" ]; then
  echo
  echo "Missing referenced scripts:" >&2
  sort -u "$MISSING" >&2
  exit 1
fi

echo
echo "Audit completed."
