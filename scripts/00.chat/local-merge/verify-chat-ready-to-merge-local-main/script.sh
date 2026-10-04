#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.local-merge.verify-chat-ready-to-merge-local-main
#   version: 2
#   status: active
#   layer: 00.chat
#   domain: local-merge
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Verify whether a completed chat branch is ready to merge into local main.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-promote-to-main
#     path: .agentic/00.chat/workflows/chat-promote-to-main.md
#   - id: harness.architecture.adr.0011-use-chat-owned-worktrees-for-local-convergence
#   effects:
#   - read-only

usage() {
  cat <<'EOF'
Usage:
  script.sh [--base <branch>] [--remote-main <remote>] <chat-branch>

Read-only gate for merging a completed chat branch into local main.
Classifies deterministic blocked states and exits non-zero unless the branch is
eligible for explicit, user-approved local merge.

With --remote-main, verifies the same recorded source evidence against a
freshly fetched <remote>/<base> reference. This mode is for a clean,
fast-forward-only remote promotion when the local integration console has
unrelated work and must remain untouched.
EOF
}

BASE_BRANCH="main"
REMOTE_NAME=""
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
    --remote-main)
      if [ $# -lt 2 ]; then
        usage >&2
        exit 2
      fi
      REMOTE_NAME="$2"
      shift 2
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

if [ -z "$TARGET_BRANCH" ]; then
  usage >&2
  exit 2
fi

CALLER_ROOT="$(git rev-parse --show-toplevel)"
CALLER_ROOT="$(cd "$CALLER_ROOT" && pwd -P)"

# shellcheck source=../../worktree/paths/lib.sh
source "$CALLER_ROOT/scripts/00.chat/worktree/paths/lib.sh"
# shellcheck source=../../session-log/paths/lib.sh
source "$CALLER_ROOT/scripts/00.chat/session-log/paths/lib.sh"

PRIMARY_PATH="$(chat_worktree_primary_path)"
PRIMARY_PATH="$(cd "$PRIMARY_PATH" && pwd -P)"
chat_worktree_load_config "$PRIMARY_PATH"

if [ -n "$REMOTE_NAME" ]; then
  REPO_ROOT="$PRIMARY_PATH"
  BASE_REF="refs/remotes/${REMOTE_NAME}/${BASE_BRANCH}"
else
  REPO_ROOT="$CALLER_ROOT"
  BASE_REF="refs/heads/${BASE_BRANCH}"
fi

tmp_dir="$(mktemp -d)"

cleanup() {
  rm -rf "$tmp_dir"
}

trap cleanup EXIT

block() {
  local state="$1"
  local condition="$2"
  local action="$3"

  echo "State: $state"
  echo "Branch: $TARGET_BRANCH"
  echo "Blocking condition: $condition"
  echo "Required action: $action"
  exit 1
}

info() {
  printf '%s: %s\n' "$1" "$2"
}

find_worktree_log_by_metadata() {
  local grouped_parent="$1"
  local candidate

  if [ ! -d "$REPO_ROOT/$grouped_parent" ]; then
    return 1
  fi

  while IFS= read -r candidate; do
    if [ "$(chat_log_metadata_value "$REPO_ROOT/$candidate" "id")" = "$SESSION_ID" ] \
      || [ "$(chat_log_metadata_value "$REPO_ROOT/$candidate" "branch")" = "$TARGET_BRANCH" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done < <(find "$REPO_ROOT/$grouped_parent" -mindepth 2 -maxdepth 2 -type f -name README.md \
    | sed "s#^$REPO_ROOT/##" \
    | sort)

  return 1
}

find_branch_log_by_metadata() {
  local grouped_parent="$1"
  local candidate tmp_log

  while IFS= read -r candidate; do
    tmp_log="${tmp_dir}/candidate-log.md"
    git -C "$REPO_ROOT" show "${TARGET_BRANCH}:${candidate}" > "$tmp_log"
    if [ "$(chat_log_metadata_value "$tmp_log" "id")" = "$SESSION_ID" ] \
      || [ "$(chat_log_metadata_value "$tmp_log" "branch")" = "$TARGET_BRANCH" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done < <(git -C "$REPO_ROOT" ls-tree -r --name-only "$TARGET_BRANCH" -- "$grouped_parent" \
    | awk '/\/README\.md$/ { print }' \
    | sort)

  return 1
}

case "$TARGET_BRANCH" in
  chat/*) ;;
  *)
    block "blocked-invalid-branch" \
      "target is not a chat branch" \
      "Choose a local chat/* branch."
    ;;
esac

if ! git -C "$REPO_ROOT" show-ref --verify --quiet "$BASE_REF"; then
  if [ -n "$REMOTE_NAME" ]; then
    block "blocked-missing-remote-base" \
      "remote tracking reference does not exist: ${REMOTE_NAME}/${BASE_BRANCH}" \
      "Fetch the named remote before remote promotion verification."
  fi

  block "blocked-missing-base" \
    "base branch does not exist: $BASE_BRANCH" \
    "Create or select the local base branch before convergence."
fi

if ! git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/${TARGET_BRANCH}"; then
  block "blocked-missing-branch" \
    "target branch does not exist locally" \
    "Create or fetch the chat branch before convergence."
fi

if [ -z "$REMOTE_NAME" ] && [ "$REPO_ROOT" != "$PRIMARY_PATH" ]; then
    block "blocked-not-root-integration-worktree" \
    "verification is not running from the root integration worktree" \
    "Run local merge verification from the root integration worktree."
fi

if [ -z "$REMOTE_NAME" ]; then
  current_branch="$(git -C "$REPO_ROOT" branch --show-current)"
  if [ "$current_branch" != "$BASE_BRANCH" ]; then
    block "blocked-root-not-main" \
      "root integration worktree is on '$current_branch', expected '$BASE_BRANCH'" \
      "Switch the root integration worktree to $BASE_BRANCH before convergence."
  fi

  if [ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]; then
    block "blocked-dirty-root" \
      "root integration worktree is dirty" \
      "Clean or explicitly resolve root worktree changes before convergence."
  fi
fi

SESSION_ID="${TARGET_BRANCH#chat/}"
GROUPED_DIR="$(chat_log_grouped_dir_for_session "$SESSION_ID")"
GROUPED_PARENT="${GROUPED_DIR%/*}"
GROUPED_LOG="${GROUPED_DIR}/README.md"
FLAT_LOG="commitLogs/${SESSION_ID}/README.md"
LOG_FILE="${tmp_dir}/session-log.md"
LOG_SOURCE=""
LOG_PATH=""
metadata_log_path=""

if git -C "$REPO_ROOT" cat-file -e "${TARGET_BRANCH}:${GROUPED_LOG}" 2>/dev/null; then
  git -C "$REPO_ROOT" show "${TARGET_BRANCH}:${GROUPED_LOG}" > "$LOG_FILE"
  LOG_SOURCE="branch"
  LOG_PATH="$GROUPED_LOG"
elif git -C "$REPO_ROOT" cat-file -e "${TARGET_BRANCH}:${FLAT_LOG}" 2>/dev/null; then
  git -C "$REPO_ROOT" show "${TARGET_BRANCH}:${FLAT_LOG}" > "$LOG_FILE"
  LOG_SOURCE="branch"
  LOG_PATH="$FLAT_LOG"
elif metadata_log_path="$(find_branch_log_by_metadata "$GROUPED_PARENT")"; then
  git -C "$REPO_ROOT" show "${TARGET_BRANCH}:${metadata_log_path}" > "$LOG_FILE"
  LOG_SOURCE="branch"
  LOG_PATH="$metadata_log_path"
elif [ -f "$REPO_ROOT/$GROUPED_LOG" ]; then
  cp "$REPO_ROOT/$GROUPED_LOG" "$LOG_FILE"
  LOG_SOURCE="worktree"
  LOG_PATH="$GROUPED_LOG"
elif [ -f "$REPO_ROOT/$FLAT_LOG" ]; then
  cp "$REPO_ROOT/$FLAT_LOG" "$LOG_FILE"
  LOG_SOURCE="worktree"
  LOG_PATH="$FLAT_LOG"
elif metadata_log_path="$(find_worktree_log_by_metadata "$GROUPED_PARENT")"; then
  cp "$REPO_ROOT/$metadata_log_path" "$LOG_FILE"
  LOG_SOURCE="worktree"
  LOG_PATH="$metadata_log_path"
else
  block "blocked-missing-log" \
    "session log is missing from root $BASE_BRANCH and target branch" \
    "Restore or create the chat session log before convergence."
fi

metadata_branch="$(chat_log_metadata_value "$LOG_FILE" "branch")"
metadata_worktree="$(chat_log_metadata_value "$LOG_FILE" "worktree")"
metadata_latest_sha="$(chat_log_metadata_value "$LOG_FILE" "latest_commit_sha")"

if [ "$metadata_branch" != "$TARGET_BRANCH" ]; then
  block "blocked-invalid-metadata" \
    "session log branch metadata is '$metadata_branch', expected '$TARGET_BRANCH'" \
    "Fix the session log metadata before convergence."
fi

set +e
WORKTREE_PATH="$(chat_worktree_registered_path_for_branch "$REPO_ROOT" "$TARGET_BRANCH")"
registered_status=$?
set -e

if [ "$registered_status" -eq 1 ]; then
  WORKTREE_PATH="$metadata_worktree"
elif [ "$registered_status" -ne 0 ]; then
  exit "$registered_status"
fi

if [ "$metadata_worktree" != "$WORKTREE_PATH" ]; then
  block "blocked-invalid-metadata" \
    "session log worktree metadata is '$metadata_worktree', expected '$WORKTREE_PATH'" \
    "Fix the session log worktree metadata before convergence."
fi

branch_worktrees="$(
  git -C "$REPO_ROOT" worktree list --porcelain \
    | awk -v branch="refs/heads/${TARGET_BRANCH}" '
      /^worktree / { path = substr($0, 10) }
      /^branch / && substr($0, 8) == branch { print path }
    '
)"

found_canonical_worktree="no"
while IFS= read -r branch_worktree; do
  if [ -z "${branch_worktree// }" ]; then
    continue
  fi

  branch_worktree="$(cd "$branch_worktree" && pwd -P)"
  if [ "$branch_worktree" = "$PRIMARY_PATH" ]; then
    block "blocked-branch-in-root-worktree" \
      "target chat branch is checked out in the root integration worktree" \
      "Switch root back to $BASE_BRANCH before convergence."
  fi

  if [ "$branch_worktree" != "$WORKTREE_PATH" ]; then
    block "blocked-wrong-worktree" \
      "target chat branch is checked out in '$branch_worktree', expected '$WORKTREE_PATH'" \
      "Move or recreate the chat-owned worktree before convergence."
  fi

  found_canonical_worktree="yes"
done <<< "$branch_worktrees"

if [ "$found_canonical_worktree" != "yes" ]; then
  block "blocked-missing-worktree" \
    "canonical chat-owned worktree is missing" \
    "Run ensure-chat-worktree after session log verification, then rerun convergence verification."
fi

if ! git -C "$WORKTREE_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  block "blocked-missing-worktree" \
    "canonical chat-owned worktree path is not a git worktree" \
    "Recreate the chat-owned worktree before convergence."
fi

worktree_branch="$(git -C "$WORKTREE_PATH" branch --show-current)"
if [ "$worktree_branch" != "$TARGET_BRANCH" ]; then
  block "blocked-wrong-worktree" \
    "chat worktree is on '$worktree_branch', expected '$TARGET_BRANCH'" \
    "Check out the target chat branch in its canonical worktree."
fi

if [ -n "$(git -C "$WORKTREE_PATH" status --porcelain)" ]; then
  block "blocked-dirty-chat-worktree" \
    "chat-owned worktree is dirty" \
    "Commit, inspect, preserve, or explicitly discard chat work before convergence."
fi

ahead="$(git -C "$REPO_ROOT" rev-list --count "${BASE_REF}..${TARGET_BRANCH}")"
behind="$(git -C "$REPO_ROOT" rev-list --count "${TARGET_BRANCH}..${BASE_REF}")"

if [ "$behind" != "0" ] && [ "$ahead" != "0" ]; then
  block "blocked-diverged" \
    "chat branch and $BASE_BRANCH both have unique commits" \
    "Use the governed refresh path before convergence."
fi

if [ "$behind" != "0" ]; then
  block "blocked-behind" \
    "chat branch is behind $BASE_BRANCH" \
    "Merge $BASE_BRANCH into the chat branch from the chat-owned worktree before convergence."
fi

if [ "$ahead" = "0" ]; then
  block "blocked-even" \
    "chat branch has no commits beyond $BASE_BRANCH" \
    "Do not merge; use cleanup or reporting flow instead."
fi

if [ -z "${metadata_latest_sha// }" ]; then
  block "blocked-unrecorded-commit" \
    "session log does not record latest_commit_sha" \
    "Record the latest task commit, or explain the no-task-commit case before convergence."
fi

if ! git -C "$REPO_ROOT" cat-file -e "${metadata_latest_sha}^{commit}" 2>/dev/null; then
  block "blocked-log-head-mismatch" \
    "recorded latest_commit_sha does not resolve to a commit: $metadata_latest_sha" \
    "Fix the session log commit evidence before convergence."
fi

if ! git -C "$REPO_ROOT" merge-base --is-ancestor "$metadata_latest_sha" "$TARGET_BRANCH"; then
  block "blocked-log-head-mismatch" \
    "recorded latest_commit_sha is not contained in the chat branch" \
    "Record a commit that is present on the target chat branch before convergence."
fi

if [ -n "$REMOTE_NAME" ]; then
  echo "State: eligible-remote-promotion"
  info "Remote base" "${REMOTE_NAME}/${BASE_BRANCH}"
else
  echo "State: eligible"
  info "Base branch" "$BASE_BRANCH"
fi
info "Branch" "$TARGET_BRANCH"
info "Ahead of base" "$ahead"
info "Behind base" "$behind"
info "Session log source" "$LOG_SOURCE"
info "Session log path" "$LOG_PATH"
info "Chat worktree" "$WORKTREE_PATH"
info "Recorded latest task commit" "$metadata_latest_sha"
if [ -n "$REMOTE_NAME" ]; then
  echo "Next step: after explicit push approval, prepare a clean remote-promotion worktree and push without force."
else
  echo "Next step: ask for explicit approval, then merge from the root integration worktree."
fi
