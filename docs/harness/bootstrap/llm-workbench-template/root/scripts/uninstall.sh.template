#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/uninstall.sh <target-git-repo>

Removes llm-workbench harness files from a target Git repository.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

TARGET_REPO="${1:-}"

if [ -z "$TARGET_REPO" ]; then
  usage >&2
  exit 2
fi

if [ ! -d "$TARGET_REPO/.git" ]; then
  echo "ERROR: target is not a Git repo: $TARGET_REPO" >&2
  exit 1
fi

rm -rf \
  "$TARGET_REPO/.agentic/00.chat" \
  "$TARGET_REPO/.agentic/shared" \
  "$TARGET_REPO/scripts/00.chat" \
  "$TARGET_REPO/scripts/shared/harness"

echo "Removed llm-workbench harness directories from: $TARGET_REPO"
echo "Review AGENTS.md and package.json manually before deleting them."
