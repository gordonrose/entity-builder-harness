#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test empty chat branch and session log cleanup safety.
#   domain: git
#   portability: llm-workbench-validation
#   used_by:
#     - .agentic/00.chat/workflows/chat-cleanup.md
#     - scripts/shared/git/cleanup-empty-chat-branches.sh
#   effects: writes-files, branches, commits, destructive

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/cleanup-empty-chat-branches-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO/scripts/shared/git" "$REPO/scripts/shared/chat"
cp "$SOURCE_ROOT/scripts/shared/git/cleanup-empty-chat-branches.sh" "$REPO/scripts/shared/git/cleanup-empty-chat-branches.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" "$REPO/scripts/shared/chat/session-log-paths.sh"

git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"

printf 'base\n' > "$REPO/base.txt"
git -C "$REPO" add base.txt scripts/shared/git/cleanup-empty-chat-branches.sh scripts/shared/chat/session-log-paths.sh
git -C "$REPO" commit -q -m "initial"

COMMITTED_SESSION="2026-06-16-07-18-committed-log"
COMMITTED_BRANCH="chat/$COMMITTED_SESSION"
COMMITTED_LOG="$REPO/commitLogs/2026/jun/16/$COMMITTED_SESSION/README.md"

git -C "$REPO" switch -q -c "$COMMITTED_BRANCH"
printf 'work\n' > "$REPO/work.txt"
git -C "$REPO" add work.txt
git -C "$REPO" commit -q -m "committed chat work"
COMMITTED_SHA="$(git -C "$REPO" rev-parse --short HEAD)"

git -C "$REPO" switch -q main
git -C "$REPO" merge -q --ff-only "$COMMITTED_BRANCH"

mkdir -p "$(dirname "$COMMITTED_LOG")"
cat > "$COMMITTED_LOG" <<EOF
# Chat Session: committed log

<!-- agentic-session
id: $COMMITTED_SESSION
branch: $COMMITTED_BRANCH
latest_commit_sha: $COMMITTED_SHA
-->

## Commits

- Commit: \`$COMMITTED_SHA\`
EOF

EMPTY_SESSION="2026-06-16-07-19-empty-log"
EMPTY_BRANCH="chat/$EMPTY_SESSION"
EMPTY_LOG="$REPO/commitLogs/2026/jun/16/$EMPTY_SESSION/README.md"

git -C "$REPO" branch "$EMPTY_BRANCH"
mkdir -p "$(dirname "$EMPTY_LOG")"
cat > "$EMPTY_LOG" <<EOF
# Chat Session: empty log

<!-- agentic-session
id: $EMPTY_SESSION
branch: $EMPTY_BRANCH
latest_commit_sha:
-->

## Commits

- None recorded yet.
EOF

git -C "$REPO" add "$COMMITTED_LOG" "$EMPTY_LOG"
git -C "$REPO" commit -q -m "add chat logs"

(
  cd "$REPO"
  bash scripts/shared/git/cleanup-empty-chat-branches.sh --apply
) > "$TMP_ROOT/cleanup.out" 2> "$TMP_ROOT/cleanup.err"

if git -C "$REPO" show-ref --verify --quiet "refs/heads/$COMMITTED_BRANCH"; then
  fail "merged committed branch was not deleted"
fi

if [ ! -f "$COMMITTED_LOG" ]; then
  fail "commit log with recorded commit was deleted"
fi

if git -C "$REPO" show-ref --verify --quiet "refs/heads/$EMPTY_BRANCH"; then
  fail "empty branch was not deleted"
fi

if [ -e "$EMPTY_LOG" ]; then
  fail "empty unsaved commit log was not deleted"
fi

if ! grep -q "Kept matching log (recorded commits)" "$TMP_ROOT/cleanup.out"; then
  fail "cleanup did not report keeping the committed log"
fi

if ! grep -q "Deleted matching log" "$TMP_ROOT/cleanup.out"; then
  fail "cleanup did not report deleting the empty log"
fi

echo "cleanup empty chat branches smoke test passed."
