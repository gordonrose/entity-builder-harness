#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.read-current-chat-log.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test current chat metadata reads and recorded-session reuse guard.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.read-current-chat-log.readme
#     path: scripts/00.chat/session-log/read-current-chat-log/README.md
#   - id: chat.script.session-log.read-current-chat-log
#     path: scripts/00.chat/session-log/read-current-chat-log/script.sh
#   effects:
#   - writes-files
#   - branches
#   - commits
fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/read-current-chat-log-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init --quiet --initial-branch=main

mkdir -p \
  "$REPO/scripts/00.chat/session-log/read-current-chat-log" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/commitLogs/2026/jun/23/2026-06-23-18-00-empty-session" \
  "$REPO/commitLogs/2026/jun/23/2026-06-23-18-05-recorded-session"

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/read-current-chat-log/script.sh" "$REPO/scripts/00.chat/session-log/read-current-chat-log/script.sh"
chmod +x "$REPO/scripts/00.chat/session-log/read-current-chat-log/script.sh"

cat > "$REPO/commitLogs/2026/jun/23/2026-06-23-18-00-empty-session/README.md" <<'EOF'
# Chat Session: empty

<!-- agentic-session
id: 2026-06-23-18-00-empty-session
task: empty
branch: chat/2026-06-23-18-00-empty-session
worktree:
layer: harness
mode: implementation
workflow: .agentic/01.harness/workflows/change-harness.md
status: ready
latest_commit_sha:
-->
EOF

cat > "$REPO/commitLogs/2026/jun/23/2026-06-23-18-05-recorded-session/README.md" <<'EOF'
# Chat Session: recorded

<!-- agentic-session
id: 2026-06-23-18-05-recorded-session
task: recorded
branch: chat/2026-06-23-18-05-recorded-session
worktree:
layer: harness
mode: implementation
workflow: .agentic/01.harness/workflows/change-harness.md
status: ready
latest_commit_sha: abc1234
-->
EOF

git -C "$REPO" add .
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'

git -C "$REPO" switch --quiet -c chat/2026-06-23-18-00-empty-session
bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/read-current-chat-log/script.sh \
  >"$TMP_ROOT/empty.out"

grep -q '^layer: harness$' "$TMP_ROOT/empty.out" \
  || fail "empty session metadata was not printed"

git -C "$REPO" switch --quiet main
git -C "$REPO" switch --quiet -c chat/2026-06-23-18-05-recorded-session

if bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/read-current-chat-log/script.sh \
  >"$TMP_ROOT/recorded.out" 2>&1; then
  fail "recorded session metadata printed without explicit approval"
fi

grep -q '^ERROR: recorded-session-approval-required$' "$TMP_ROOT/recorded.out" \
  || fail "recorded session did not require explicit approval"

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/read-current-chat-log/script.sh --allow-recorded-session \
  >"$TMP_ROOT/recorded-allowed.out"

grep -q '^latest_commit_sha: abc1234$' "$TMP_ROOT/recorded-allowed.out" \
  || fail "approved recorded session metadata was not printed"

echo "read-current-chat-log smoke test passed."
