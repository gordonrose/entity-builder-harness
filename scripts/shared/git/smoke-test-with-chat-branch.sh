#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test isolated chat branch command execution and guarded staging.
#   domain: git
#   portability: llm-workbench-validation
#   used_by:
#     - docs/harness/architecture/adrs/0009-allow-automatic-session-branch-commit-context.md
#     - scripts/shared/git/with-chat-branch.sh
#   effects: writes-files, branches, worktrees, commits

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/with-chat-branch-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

assert_file_equals() {
  local file="$1"
  local expected="$2"
  local actual

  actual="$(cat "$file")"
  if [ "$actual" != "$expected" ]; then
    fail "expected $file to contain '$expected', got '$actual'"
  fi
}

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO/scripts/shared/git" "$REPO/scripts/shared/chat" "$REPO/scripts/00.chat/session-log/paths"

cp "$SOURCE_ROOT/scripts/shared/git/with-chat-branch.sh" "$REPO/scripts/shared/git/with-chat-branch.sh"
cp "$SOURCE_ROOT/scripts/shared/git/stage-active-worktree-paths.sh" "$REPO/scripts/shared/git/stage-active-worktree-paths.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" "$REPO/scripts/shared/chat/session-log-paths.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"

git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"

printf 'base\n' > "$REPO/base.txt"
git -C "$REPO" add base.txt scripts/shared/git/with-chat-branch.sh scripts/shared/git/stage-active-worktree-paths.sh scripts/shared/chat/session-log-paths.sh scripts/00.chat/session-log/paths/lib.sh
git -C "$REPO" commit -q -m "initial"

SESSION_ID="2026-06-16-09-08-smoke"
SESSION_BRANCH="chat/$SESSION_ID"
SESSION_DIR="$REPO/commitLogs/2026/jun/16/$SESSION_ID"
SESSION_LOG="$SESSION_DIR/README.md"

git -C "$REPO" branch "$SESSION_BRANCH"
mkdir -p "$SESSION_DIR"
cat > "$SESSION_LOG" <<EOF
# Chat Session: smoke

<!-- agentic-session
id: $SESSION_ID
task: smoke
branch: $SESSION_BRANCH
layer: shared
mode: implementation
workflow: .agentic/shared/workflows/change-shared-process.md
status: ready
raised_at_utc: 2026-06-16T08:08:25Z
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
-->
EOF

git -C "$REPO" add "$SESSION_LOG"
git -C "$REPO" commit -q -m "add session log"

printf 'dirty active worktree\n' > "$REPO/active-dirty.txt"

OUT_DIR="$TMP_ROOT/out"
WORKTREE_ROOT="$TMP_ROOT/worktrees"
mkdir -p "$OUT_DIR"

(
  cd "$REPO"
  AGENTIC_CHAT_WORKTREE_ROOT="$WORKTREE_ROOT" \
    bash scripts/shared/git/with-chat-branch.sh "$SESSION_LOG" -- bash -c \
      'git branch --show-current > "$1/branch"; pwd > "$1/pwd"; printf "ran\n" > smoke-output.txt' \
      bash "$OUT_DIR"
)

assert_file_equals "$OUT_DIR/branch" "$SESSION_BRANCH"

ACTIVE_BRANCH="$(git -C "$REPO" branch --show-current)"
if [ "$ACTIVE_BRANCH" != "main" ]; then
  fail "active worktree switched to $ACTIVE_BRANCH"
fi

assert_file_equals "$REPO/active-dirty.txt" "dirty active worktree"

ISOLATED_PWD="$(cat "$OUT_DIR/pwd")"
case "$ISOLATED_PWD" in
  "$WORKTREE_ROOT"/*) ;;
  *) fail "command did not run under isolated worktree root: $ISOLATED_PWD" ;;
esac

if [ ! -f "$ISOLATED_PWD/smoke-output.txt" ]; then
  fail "wrapped command did not write inside isolated worktree"
fi

(
  cd "$REPO"
  AGENTIC_CHAT_WORKTREE_ROOT="$WORKTREE_ROOT" \
    bash scripts/shared/git/with-chat-branch.sh "$SESSION_LOG" -- \
      bash scripts/shared/git/stage-active-worktree-paths.sh active-dirty.txt
)

if ! git -C "$ISOLATED_PWD" diff --cached --name-only | grep -qx 'active-dirty.txt'; then
  fail "active-dirty.txt was not staged in isolated worktree"
fi

assert_file_equals "$ISOLATED_PWD/active-dirty.txt" "dirty active worktree"

set +e
(
  cd "$REPO"
  AGENTIC_CHAT_WORKTREE_ROOT="$WORKTREE_ROOT" \
    bash scripts/shared/git/with-chat-branch.sh "$SESSION_LOG" -- git push
) > "$OUT_DIR/denied.out" 2> "$OUT_DIR/denied.err"
DENIED_STATUS="$?"
set -e

if [ "$DENIED_STATUS" -eq 0 ]; then
  fail "direct git push was not denied"
fi

if ! grep -q "does not authorize git push" "$OUT_DIR/denied.err"; then
  fail "direct git push denial message was not emitted"
fi

CHECKED_OUT_SESSION_ID="2026-06-16-09-08-checked-out-smoke"
CHECKED_OUT_BRANCH="chat/$CHECKED_OUT_SESSION_ID"
CHECKED_OUT_DIR="$REPO/commitLogs/2026/jun/16/$CHECKED_OUT_SESSION_ID"
CHECKED_OUT_LOG="$CHECKED_OUT_DIR/README.md"

git -C "$REPO" branch "$CHECKED_OUT_BRANCH"
mkdir -p "$CHECKED_OUT_DIR"
cat > "$CHECKED_OUT_LOG" <<EOF
# Chat Session: checked out smoke

<!-- agentic-session
id: $CHECKED_OUT_SESSION_ID
task: checked out smoke
branch: $CHECKED_OUT_BRANCH
layer: shared
mode: implementation
workflow: .agentic/shared/workflows/change-shared-process.md
status: ready
raised_at_utc: 2026-06-16T08:08:25Z
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
-->
EOF

git -C "$REPO" switch -q "$CHECKED_OUT_BRANCH"

(
  cd "$REPO"
  AGENTIC_CHAT_WORKTREE_ROOT="$WORKTREE_ROOT" \
    bash scripts/shared/git/with-chat-branch.sh "$CHECKED_OUT_LOG" -- bash -c \
      'git branch --show-current > "$1/checked-out-branch"; pwd > "$1/checked-out-pwd"' \
      bash "$OUT_DIR"
)

assert_file_equals "$OUT_DIR/checked-out-branch" "$CHECKED_OUT_BRANCH"
assert_file_equals "$REPO/active-dirty.txt" "dirty active worktree"

EXTERNAL_SESSION_ID="2026-06-16-09-08-external-smoke"
EXTERNAL_BRANCH="chat/$EXTERNAL_SESSION_ID"
EXTERNAL_DIR="$REPO/commitLogs/2026/jun/16/$EXTERNAL_SESSION_ID"
EXTERNAL_LOG="$EXTERNAL_DIR/README.md"
EXTERNAL_WORKTREE="$TMP_ROOT/external-worktree"

git -C "$REPO" switch -q main
git -C "$REPO" branch "$EXTERNAL_BRANCH"
mkdir -p "$EXTERNAL_DIR"
cat > "$EXTERNAL_LOG" <<EOF
# Chat Session: external smoke

<!-- agentic-session
id: $EXTERNAL_SESSION_ID
task: external smoke
branch: $EXTERNAL_BRANCH
layer: shared
mode: implementation
workflow: .agentic/shared/workflows/change-shared-process.md
status: ready
raised_at_utc: 2026-06-16T08:08:25Z
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
-->
EOF

git -C "$REPO" worktree add --quiet "$EXTERNAL_WORKTREE" "$EXTERNAL_BRANCH"

set +e
(
  cd "$REPO"
  AGENTIC_CHAT_WORKTREE_ROOT="$WORKTREE_ROOT" \
    bash scripts/shared/git/with-chat-branch.sh "$EXTERNAL_LOG" -- git status --short
) > "$OUT_DIR/external.out" 2> "$OUT_DIR/external.err"
EXTERNAL_STATUS="$?"
set -e

if [ "$EXTERNAL_STATUS" -eq 0 ]; then
  fail "branch checked out in an external worktree was not rejected"
fi

if ! grep -q "already checked out outside the active and isolated worktrees" "$OUT_DIR/external.err"; then
  fail "external worktree rejection message was not emitted"
fi

echo "with-chat-branch smoke test passed."
