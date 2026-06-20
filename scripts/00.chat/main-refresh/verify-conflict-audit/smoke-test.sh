#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test main-refresh conflict audit verification.
#   domain: main-refresh
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/main-refresh/verify-conflict-audit/script.sh
#   effects: temporary-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd -P)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/verify-main-refresh-conflict-audit-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.com
git -C "$REPO" config user.name "Test User"

mkdir -p \
  "$REPO/scripts/00.chat/main-refresh/verify-conflict-audit" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/commitLogs/2026/jun/20/test-session"

cp "$SOURCE_ROOT/scripts/00.chat/main-refresh/verify-conflict-audit/script.sh" "$REPO/scripts/00.chat/main-refresh/verify-conflict-audit/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"

SESSION_LOG="$REPO/commitLogs/2026/jun/20/test-session/README.md"
CONFLICT_PATH="docs/example-conflict.md"
cat > "$SESSION_LOG" <<'EOF'
# Chat Session: test

## Main Refresh Conflicts

- Path: `docs/example-conflict.md`
  Type: `ownership-migration-conflict`
  Mode: deterministic
  Reason: test
  Action: test
  Preflight branch: `agentic/preflight/chat-test/20000101000000`
  Preflight worktree: `/tmp/preflight`
  Files changed by resolution: docs/example-conflict.md
  Checks: test
EOF

git -C "$REPO" add scripts commitLogs
git -C "$REPO" commit -q -m base

(
  cd "$REPO"
  bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh \
    --session-log commitLogs/2026/jun/20/test-session/README.md \
    --path "$CONFLICT_PATH"
) >/dev/null

set +e
(
  cd "$REPO"
  bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh \
    --session-log commitLogs/2026/jun/20/test-session/README.md \
    --path missing/path.md
) > "$TMP_ROOT/missing.out" 2> "$TMP_ROOT/missing.err"
MISSING_STATUS="$?"
set -e

if [ "$MISSING_STATUS" -eq 0 ]; then
  fail "missing conflict audit path passed"
fi

if ! grep -q "conflict path missing from session audit" "$TMP_ROOT/missing.err"; then
  fail "missing path failure was not explained"
fi

echo "main refresh conflict audit verifier smoke test passed."
