#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.remote-promotion.prepare-clean-integration-worktree
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: remote-promotion
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Create an isolated, clean integration worktree for a verified fast-forward remote promotion.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-promote-to-remote-main
#     path: .agentic/00.chat/workflows/chat-promote-to-remote-main.md
#   effects:
#   - branches
#   - worktrees
#   - writes-files

usage() {
  cat <<'EOF'
Usage: script.sh [--remote <name>] [--base <branch>] [--dry-run] <chat-branch>

Creates an isolated local branch and worktree at the exact chat-branch commit.
It only proceeds when that commit is already a descendant of the fetched remote
base. It does not fetch, merge, push, rewrite history, alter local main, or
clean any existing worktree.
EOF
}

REMOTE_NAME="origin"
BASE_BRANCH="main"
DRY_RUN="no"
SOURCE_BRANCH=""

while [ $# -gt 0 ]; do
  case "$1" in
    --remote)
      [ $# -ge 2 ] || { usage >&2; exit 2; }
      REMOTE_NAME="$2"
      shift 2
      ;;
    --base)
      [ $# -ge 2 ] || { usage >&2; exit 2; }
      BASE_BRANCH="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      [ -z "$SOURCE_BRANCH" ] || { usage >&2; exit 2; }
      SOURCE_BRANCH="$1"
      shift
      ;;
  esac
done

[ -n "$SOURCE_BRANCH" ] || { usage >&2; exit 2; }

case "$SOURCE_BRANCH" in
  chat/*) ;;
  *)
    echo "ERROR: source must be a chat branch: $SOURCE_BRANCH" >&2
    exit 1
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"
BASE_REF="refs/remotes/${REMOTE_NAME}/${BASE_BRANCH}"

if ! git show-ref --verify --quiet "refs/heads/${SOURCE_BRANCH}"; then
  echo "ERROR: source branch does not exist locally: $SOURCE_BRANCH" >&2
  exit 1
fi

if ! git show-ref --verify --quiet "$BASE_REF"; then
  echo "ERROR: remote base is absent: ${REMOTE_NAME}/${BASE_BRANCH}; fetch first." >&2
  exit 1
fi

if ! git merge-base --is-ancestor "$BASE_REF" "$SOURCE_BRANCH"; then
  echo "ERROR: source is not a fast-forward candidate from ${REMOTE_NAME}/${BASE_BRANCH}." >&2
  exit 1
fi

SOURCE_COMMIT="$(git rev-parse "$SOURCE_BRANCH")"
SAFE_SOURCE="$(printf '%s' "$SOURCE_BRANCH" | sed 's#[^A-Za-z0-9._-]#_#g')"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
INTEGRATION_BRANCH="agentic/remote-promotion/${SAFE_SOURCE}-${STAMP}"
PROMOTION_ROOT="${TMPDIR:-/tmp}/agentic-remote-promotions"
INTEGRATION_WORKTREE="${PROMOTION_ROOT}/${SAFE_SOURCE}-${STAMP}-$$"

if git show-ref --verify --quiet "refs/heads/${INTEGRATION_BRANCH}"; then
  echo "ERROR: generated integration branch already exists: $INTEGRATION_BRANCH" >&2
  exit 1
fi

if [ -e "$INTEGRATION_WORKTREE" ]; then
  echo "ERROR: generated integration worktree path already exists: $INTEGRATION_WORKTREE" >&2
  exit 1
fi

printf 'remote=%s\n' "$REMOTE_NAME"
printf 'base_ref=%s\n' "${REMOTE_NAME}/${BASE_BRANCH}"
printf 'source_branch=%s\n' "$SOURCE_BRANCH"
printf 'source_commit=%s\n' "$SOURCE_COMMIT"
printf 'integration_branch=%s\n' "$INTEGRATION_BRANCH"
printf 'integration_worktree=%s\n' "$INTEGRATION_WORKTREE"

if [ "$DRY_RUN" = "yes" ]; then
  echo "result=dry-run"
  exit 0
fi

mkdir -p "$PROMOTION_ROOT"
git worktree add -b "$INTEGRATION_BRANCH" "$INTEGRATION_WORKTREE" "$SOURCE_COMMIT"

if [ -n "$(git -C "$INTEGRATION_WORKTREE" status --porcelain)" ]; then
  echo "ERROR: created integration worktree is unexpectedly dirty: $INTEGRATION_WORKTREE" >&2
  exit 1
fi

if [ "$(git -C "$INTEGRATION_WORKTREE" rev-parse HEAD)" != "$SOURCE_COMMIT" ]; then
  echo "ERROR: integration worktree does not point at the verified source commit." >&2
  exit 1
fi

echo "result=prepared"
