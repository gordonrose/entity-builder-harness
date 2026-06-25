#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.git.cleanup-empty-chat-branches.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: git
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test empty chat branch and session log cleanup safety.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-cleanup
#     path: .agentic/00.chat/workflows/chat-cleanup.md
#   - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
#     path: docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#   effects:
#   - branches
#   - commits
#   - destructive
#   - writes-files

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
 mkdir -p "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches" "$REPO/scripts/00.chat/session-log/paths"
cp "$SOURCE_ROOT/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"

git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"

printf 'base\n' > "$REPO/base.txt"
git -C "$REPO" add base.txt scripts/00.chat/git/cleanup-empty-chat-branches/script.sh scripts/00.chat/session-log/paths/lib.sh
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
  bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --apply
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
