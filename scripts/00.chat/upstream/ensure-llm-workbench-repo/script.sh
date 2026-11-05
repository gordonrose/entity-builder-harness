#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.upstream.ensure-llm-workbench-repo
#   version: 2
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: upstream
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Ensure the canonical local llm-workbench upstream repo exists.
#   portability:
#     class: source-only
#     targets: []
#   used_by:
#   - id: chat.script.upstream.ensure-llm-workbench-repo.readme
#     path: scripts/00.chat/upstream/ensure-llm-workbench-repo/README.md
#   - id: harness.standards.governed-script-permissions
#     path: .agentic/01.harness/standards/governed-script-permissions.md
#   - id: chat.workflows.chat-upstream-reusable-lesson
#     path: .agentic/00.chat/workflows/chat-upstream-reusable-lesson.md
#   effects:
#   - network
#   - writes-files

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
      echo "ERROR: unknown argument." >&2
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

  if ORIGIN_URL="$(git -C "$TARGET_PATH" config --get remote.origin.url 2>/dev/null)"; then
    :
  else
    status=$?
    if [ "$status" -eq 1 ]; then
      echo "ERROR: target repo has no configured origin." >&2
      exit 1
    fi
    echo "ERROR: upstream-origin-read-failed; effect=none." >&2
    exit 2
  fi
  if [ "$ORIGIN_URL" != "$REPO_URL" ]; then
    echo "ERROR: target repo has unexpected origin." >&2
    exit 1
  fi

  echo "llm-workbench already present: $TARGET_PATH"
  exit 0
fi

if [ "$DRY_RUN" = "yes" ]; then
  echo "Would clone $REPO_URL to $TARGET_PATH"
  exit 0
fi

if mkdir -p "${TARGET_PATH%/*}" 2>/dev/null; then :; else
  status=$?
  echo "ERROR: upstream-directory-creation-failed; effect=unknown; inspect before retry." >&2
  exit "$status"
fi
if git clone "$REPO_URL" "$TARGET_PATH" 2>/dev/null; then :; else
  status=$?
  echo "ERROR: upstream-clone-failed; effect=unknown; inspect before retry." >&2
  exit "$status"
fi
echo "Cloned llm-workbench: $TARGET_PATH"
