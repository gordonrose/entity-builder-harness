#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/install.sh <target-git-repo>

Copies the llm-workbench harness into a target Git repository.
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

SOURCE_REPO="$(cd "$(dirname "$0")/.." && pwd)"

copy_path() {
  local source="$1"
  local target="$2"

  mkdir -p "$(dirname "$target")"
  cp -R "$source" "$target"
}

copy_path "$SOURCE_REPO/AGENTS.md" "$TARGET_REPO/AGENTS.md"
copy_path "$SOURCE_REPO/package.json" "$TARGET_REPO/package.json"
copy_path "$SOURCE_REPO/.agentic/00.chat" "$TARGET_REPO/.agentic/00.chat"
copy_path "$SOURCE_REPO/.agentic/shared" "$TARGET_REPO/.agentic/shared"
copy_path "$SOURCE_REPO/scripts/00.chat" "$TARGET_REPO/scripts/00.chat"
copy_path "$SOURCE_REPO/scripts/shared/harness" "$TARGET_REPO/scripts/shared/harness"

echo "Installed llm-workbench harness into: $TARGET_REPO"
echo "Next: cd \"$TARGET_REPO\" && npm run chat:list"
