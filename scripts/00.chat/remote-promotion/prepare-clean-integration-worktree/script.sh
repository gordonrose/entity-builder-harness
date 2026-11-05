#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.remote-promotion.prepare-clean-integration-worktree
#   version: 2
#   status: active
#   created_on: "2026-09-27"
#   updated_on: "2026-11-05"
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
    echo "ERROR: source must be a chat branch." >&2
    exit 1
    ;;
esac

CREATED=no
read_failed() {
  echo "ERROR: integration-preparation-observation-unavailable; stage=$1; worktree-created=$CREATED." >&2
  exit 2
}
observe() {
  local stage="$1"; shift
  "$@" 2>/dev/null || read_failed "$stage"
}
matches() {
  local stage="$1" status; shift
  if "$@" 2>/dev/null; then return 0; else status=$?; fi
  [ "$status" -eq 1 ] && return 1
  read_failed "$stage"
}
REPO_ROOT="$(observe repository-root git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"
BASE_REF="refs/remotes/${REMOTE_NAME}/${BASE_BRANCH}"

if ! matches source-reference git show-ref --verify --quiet "refs/heads/${SOURCE_BRANCH}"; then
  echo "ERROR: source branch does not exist locally." >&2
  exit 1
fi

if ! matches base-reference git show-ref --verify --quiet "$BASE_REF"; then
  echo "ERROR: remote base is absent; fetch first." >&2
  exit 1
fi

if ! matches ancestry git merge-base --is-ancestor "$BASE_REF" "$SOURCE_BRANCH"; then
  echo "ERROR: source is not a fast-forward candidate from the remote base." >&2
  exit 1
fi

SOURCE_COMMIT="$(observe source-commit git rev-parse "$SOURCE_BRANCH")"
SAFE_SOURCE="$(printf '%s' "$SOURCE_BRANCH" | sed 's#[^A-Za-z0-9._-]#_#g')"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
INTEGRATION_BRANCH="agentic/remote-promotion/${SAFE_SOURCE}-${STAMP}"
PROMOTION_ROOT="${TMPDIR:-/tmp}/agentic-remote-promotions"
INTEGRATION_WORKTREE="${PROMOTION_ROOT}/${SAFE_SOURCE}-${STAMP}-$$"

if matches integration-reference git show-ref --verify --quiet "refs/heads/${INTEGRATION_BRANCH}"; then
  echo "ERROR: generated integration branch already exists." >&2
  exit 1
fi

if [ -e "$INTEGRATION_WORKTREE" ]; then
  echo "ERROR: generated integration worktree path already exists." >&2
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

apply_command() {
  local stage="$1" status; shift
  if "$@" 2>/dev/null; then return 0; else status=$?; fi
  echo "ERROR: integration-preparation-failed; stage=$stage; effect=unknown; inspect before retry." >&2
  exit "$status"
}
apply_command directory-create mkdir -p "$PROMOTION_ROOT"
apply_command worktree-create git worktree add -b "$INTEGRATION_BRANCH" "$INTEGRATION_WORKTREE" "$SOURCE_COMMIT"
CREATED=yes

WORKTREE_STATUS="$(observe created-status git -C "$INTEGRATION_WORKTREE" status --porcelain)"
if [ -n "$WORKTREE_STATUS" ]; then
  echo "ERROR: created integration worktree is unexpectedly dirty." >&2
  exit 1
fi

CREATED_HEAD="$(observe created-head git -C "$INTEGRATION_WORKTREE" rev-parse HEAD)"
if [ "$CREATED_HEAD" != "$SOURCE_COMMIT" ]; then
  echo "ERROR: integration worktree does not point at the verified source commit." >&2
  exit 1
fi

echo "result=prepared"
