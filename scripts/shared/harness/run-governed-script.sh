#!/usr/bin/env bash
set -euo pipefail

ALLOWLIST_FILE=".agentic/harness/data/governed-script-allowlist.txt"

usage() {
  cat <<'EOF'
Usage:
  run-governed-script.sh --list
  run-governed-script.sh <repo-relative-script> [args...]

Runs only scripts listed in .agentic/harness/data/governed-script-allowlist.txt.
The wrapper must be invoked from a repository worktree.
EOF
}

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [ ! -f "$ALLOWLIST_FILE" ]; then
  echo "ERROR: missing governed script allowlist: $ALLOWLIST_FILE" >&2
  exit 1
fi

if [ "$1" = "--list" ]; then
  sed -n '/^[^#[:space:]]/p' "$ALLOWLIST_FILE"
  exit 0
fi

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  usage
  exit 0
fi

SCRIPT_PATH="$1"
shift

case "$SCRIPT_PATH" in
  /*|*../*|../*|*//*)
    echo "ERROR: governed script path must be a normalized repo-relative path: $SCRIPT_PATH" >&2
    exit 1
    ;;
esac

if ! grep -Fxq "$SCRIPT_PATH" "$ALLOWLIST_FILE"; then
  echo "ERROR: script is not on the governed allowlist: $SCRIPT_PATH" >&2
  echo "Allowed scripts:" >&2
  sed -n 's/^/  /;/^[^#[:space:]]/p' "$ALLOWLIST_FILE" >&2
  exit 1
fi

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "ERROR: governed script does not exist: $SCRIPT_PATH" >&2
  exit 1
fi

exec bash "$SCRIPT_PATH" "$@"
