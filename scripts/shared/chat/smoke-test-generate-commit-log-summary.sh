#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/commit-log-summary-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO/scripts/shared/chat" "$REPO/commitLogs/2026/jun/17/test-chat"
cp "$SOURCE_ROOT/scripts/shared/chat/generate-commit-log-summary.sh" \
  "$REPO/scripts/shared/chat/generate-commit-log-summary.sh"

cat > "$REPO/commitLogs/2026/jun/17/test-chat/README.md" <<'EOF'
# Chat Session: test-chat

<!-- agentic-session
id: test-chat
chat_duration: 42s
estimated_chat_tokens: 100 tokens
-->
EOF

(
  cd "$REPO"
  bash scripts/shared/chat/generate-commit-log-summary.sh > "$TMP_ROOT/printed.md"
  bash scripts/shared/chat/generate-commit-log-summary.sh --output "$TMP_ROOT/written.md" >/dev/null
)

if ! cmp -s "$TMP_ROOT/written.md" "$TMP_ROOT/printed.md"; then
  fail "printed output did not match explicit output file"
fi

set +e
(
  cd "$REPO"
  bash scripts/shared/chat/generate-commit-log-summary.sh --output commitLogs/README.md
) >/dev/null 2>"$TMP_ROOT/blocked.err"
BLOCKED_STATUS="$?"
set -e

if [ "$BLOCKED_STATUS" -eq 0 ]; then
  fail "script allowed writing commitLogs/README.md"
fi

if ! grep -q "not maintained" "$TMP_ROOT/blocked.err"; then
  fail "script did not explain retired aggregate path"
fi

if ! grep -q "Estimated Chat Tokens" "$TMP_ROOT/printed.md"; then
  fail "summary did not use estimated chat token heading"
fi

echo "commit log summary smoke test passed."
