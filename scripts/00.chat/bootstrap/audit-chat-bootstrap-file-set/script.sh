#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Audit the portable chat bootstrap script and support-file set.
#   domain: bootstrap
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#     - .agentic/shared/standards/upstream-repo-bootstrap.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

usage() {
  cat <<'EOF'
Usage:
  audit-chat-bootstrap-file-set.sh

Reports the script and support-file dependency set for the portable chat
harness bootstrap.

The audit starts from public chat commands, chat workflows, shared process
artifacts used by chat startup/commit/promotion, and the governed script
runner. It then follows script references to produce a required script set and
candidate unreferenced scripts.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
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
    find "$path" -type f >> "$SEEDS"
  fi
}

add_if_exists "AGENTS.md"
add_tree_if_exists ".agentic/00.chat"
add_tree_if_exists ".agentic/shared/checklists"
add_tree_if_exists ".agentic/shared/gates"
add_tree_if_exists ".agentic/shared/standards"
add_tree_if_exists ".agentic/shared/workflows"
add_tree_if_exists "scripts/chat"
add_if_exists "scripts/shared/harness/run-governed-script.sh"
add_if_exists "scripts/shared/harness/check-deterministic-process-drift.sh"
add_if_exists "scripts/shared/harness/check-governed-script-command-drift.sh"

sort -u "$SEEDS" > "$QUEUE"

extract_script_refs() {
  local path="$1"
  local dir

  grep -Eo 'scripts/[A-Za-z0-9._/-]+\.(sh|js|mjs|cjs|tsv|json)' "$path" 2>/dev/null \
    | grep -E '^scripts/(00\.chat|chat|harness|shared)/' || true

  case "$path" in
    scripts/*)
      dir="$(dirname "$path")"
      grep -Eo 'SCRIPT_DIR/[A-Za-z0-9._/-]+\.(sh|js|mjs|cjs|tsv|json)' "$path" 2>/dev/null \
        | sed "s#^SCRIPT_DIR/#${dir}/#" || true
      grep -Eo 'dirname "\$0"\)/[A-Za-z0-9._/-]+\.(sh|js|mjs|cjs|tsv|json)' "$path" 2>/dev/null \
        | sed "s#^dirname \"\\\$0\")/#${dir}/#" || true
      ;;
  esac
}

while [ -s "$QUEUE" ]; do
  : > "$NEXT_QUEUE"

  while IFS= read -r path; do
    [ -n "$path" ] || continue
    grep -Fxq "$path" "$SEEN" && continue
    printf '%s\n' "$path" >> "$SEEN"

    if [ ! -f "$path" ]; then
      printf '%s\n' "$path" >> "$MISSING"
      continue
    fi

    while IFS= read -r ref; do
      [ -n "$ref" ] || continue
      printf '%s\n' "$ref" >> "$SCRIPT_REFS"
      if [ -f "$ref" ]; then
        case "$ref" in
          scripts/*)
            if ! grep -Fxq "$ref" "$SEEN"; then
              printf '%s\n' "$ref" >> "$NEXT_QUEUE"
            fi
            ;;
        esac
      else
        printf '%s\n' "$ref" >> "$MISSING"
      fi
    done < <(extract_script_refs "$path")
  done < "$QUEUE"

  sort -u "$NEXT_QUEUE" > "$QUEUE"
done

find scripts -type f \
  \( -name '*.sh' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.tsv' -o -name '*.json' \) \
  | sort -u > "$ALL_SCRIPTS"

{
  grep '^scripts/' "$SEEN" || true
  sort -u "$SCRIPT_REFS"
} | sort -u > "$REQUIRED"

comm -23 "$ALL_SCRIPTS" "$REQUIRED" > "$UNREFERENCED"
while IFS= read -r path; do
  [ -n "$path" ] || continue
  if grep -Eq '^[#[:space:]]*portability: .*compatibility' "$path"; then
    printf '%s\n' "$path"
  fi
done < "$UNREFERENCED" > "$COMPATIBILITY"
{
  grep -E '/smoke-test-[^/]+\.sh$|/smoke-test\.sh$|/with-chat-branch\.sh$' "$UNREFERENCED" || true
  cat "$COMPATIBILITY"
} | sort -u > "$VALIDATION"
comm -23 "$UNREFERENCED" "$VALIDATION" > "$UNCLASSIFIED"

echo "Chat bootstrap script file set audit"
echo
echo "Seed surfaces scanned:"
echo "- AGENTS.md"
echo "- .agentic/00.chat/"
echo "- .agentic/shared/checklists/"
echo "- .agentic/shared/gates/"
echo "- .agentic/shared/standards/"
echo "- .agentic/shared/workflows/"
echo "- scripts/chat/"
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
