#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.main-refresh.check-chat-is-current-with-main
#   version: 1
#   status: active
#   created_on: "2026-06-16"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: main-refresh
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Check whether a chat branch is current with the local base branch.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: harness.architecture.adr.0011-use-chat-owned-worktrees-for-local-convergence
#   - id: harness.script.run-governed-script
#     path: scripts/01.harness/run-governed-script.sh
#   effects:
#   - read-only

usage() {
  cat <<'EOF'
Usage:
  script.sh [--base <branch>] [--require-fresh] [<branch>]

Reports whether a chat branch includes the latest local base branch. With
--require-fresh, exits non-zero when the branch is behind or diverged.
EOF
}

BASE_BRANCH="main"
REQUIRE_FRESH="no"
TARGET_BRANCH=""

while [ $# -gt 0 ]; do
  case "$1" in
    --base)
      if [ $# -lt 2 ]; then
        usage >&2
        exit 2
      fi
      BASE_BRANCH="$2"
      shift 2
      ;;
    --require-fresh)
      REQUIRE_FRESH="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [ -n "$TARGET_BRANCH" ]; then
        usage >&2
        exit 2
      fi
      TARGET_BRANCH="$1"
      shift
      ;;
  esac
done

failed() {
  echo "ERROR: $1" >&2
  exit 1
}

if [ -z "$TARGET_BRANCH" ]; then
  if ! TARGET_BRANCH="$(git branch --show-current 2>/dev/null)"; then
    failed "freshness-branch-read-failed"
  fi
fi

if [ -z "$TARGET_BRANCH" ]; then
  echo "ERROR: target branch is empty or HEAD is detached." >&2
  exit 1
fi

case "$TARGET_BRANCH" in
  chat/*) ;;
  *)
    echo "ERROR: target branch is not a chat branch." >&2
    exit 1
    ;;
esac

check_ref() {
  local ref="$1" subject="$2" status
  if git show-ref --verify --quiet "$ref" 2>/dev/null; then
    return
  else
    status=$?
    if [ "$status" -eq 1 ]; then
      failed "freshness-${subject}-missing"
    fi
    failed "freshness-${subject}-read-failed"
  fi
}
check_ref "refs/heads/${BASE_BRANCH}" "base"
check_ref "refs/heads/${TARGET_BRANCH}" "target"

if ! ahead="$(git rev-list --count "${BASE_BRANCH}..${TARGET_BRANCH}" 2>/dev/null)"; then
  failed "freshness-ahead-read-failed"
fi
if ! behind="$(git rev-list --count "${TARGET_BRANCH}..${BASE_BRANCH}" 2>/dev/null)"; then
  failed "freshness-behind-read-failed"
fi

echo "Base branch: $BASE_BRANCH"
echo "Chat branch: $TARGET_BRANCH"
echo "Ahead of base: $ahead"
echo "Behind base: $behind"

if [ "$behind" = "0" ]; then
  if [ "$ahead" = "0" ]; then
    echo "Freshness: even"
  else
    echo "Freshness: fresh-ahead"
  fi
  exit 0
fi

if [ "$ahead" = "0" ]; then
  echo "Freshness: behind"
else
  echo "Freshness: diverged"
fi

if [ "$REQUIRE_FRESH" = "yes" ]; then
  exit 1
fi
