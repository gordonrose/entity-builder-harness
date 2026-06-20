#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Ensure the canonical local llm-workbench upstream repo exists.
#   domain: upstream
#   portability: source-only
#   used_by:
#     - scripts/00.chat/upstream/ensure-llm-workbench-repo/README.md
#     - .agentic/01.harness/standards/governed-script-permissions.md
#     - .agentic/00.chat/workflows/chat-upstream-reusable-lesson.md
#   effects: network, writes-files

usage() {
  cat <<'EOF'
Usage:
  ensure-llm-workbench-repo.sh [--dry-run]

Ensures the governed upstream workbench repository exists at the canonical local
path used by upstream reusable lesson workflows.
EOF
}

DRY_RUN="no"
REPO_URL="git@github.com:gordonrose/llm-workbench.git"
TARGET_PATH="/home/owner/projects/llm-workbench"

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -e "$TARGET_PATH" ]; then
  if [ ! -d "$TARGET_PATH/.git" ]; then
    echo "ERROR: target exists but is not a Git repository: $TARGET_PATH" >&2
    exit 1
  fi

  ORIGIN_URL="$(git -C "$TARGET_PATH" config --get remote.origin.url || true)"
  if [ "$ORIGIN_URL" != "$REPO_URL" ]; then
    echo "ERROR: target repo has unexpected origin: ${ORIGIN_URL:-<missing>}" >&2
    echo "Expected: $REPO_URL" >&2
    exit 1
  fi

  echo "llm-workbench already present: $TARGET_PATH"
  exit 0
fi

if [ "$DRY_RUN" = "yes" ]; then
  echo "Would clone $REPO_URL to $TARGET_PATH"
  exit 0
fi

mkdir -p "${TARGET_PATH%/*}"
git clone "$REPO_URL" "$TARGET_PATH"
echo "Cloned llm-workbench: $TARGET_PATH"
