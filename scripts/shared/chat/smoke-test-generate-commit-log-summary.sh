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
estimated_tokens: 100 tokens
-->
EOF

(
  cd "$REPO"
  bash scripts/shared/chat/generate-commit-log-summary.sh >/dev/null
  bash scripts/shared/chat/generate-commit-log-summary.sh --check >/dev/null
  bash scripts/shared/chat/generate-commit-log-summary.sh --print > "$TMP_ROOT/printed.md"
)

if ! cmp -s "$REPO/commitLogs/README.md" "$TMP_ROOT/printed.md"; then
  fail "--print output did not match written summary"
fi

printf '\nmanual drift\n' >> "$REPO/commitLogs/README.md"

set +e
(
  cd "$REPO"
  bash scripts/shared/chat/generate-commit-log-summary.sh --check
) >/dev/null 2>"$TMP_ROOT/check.err"
CHECK_STATUS="$?"
set -e

if [ "$CHECK_STATUS" -eq 0 ]; then
  fail "--check allowed a drifted summary"
fi

if ! grep -q "is not up to date" "$TMP_ROOT/check.err"; then
  fail "--check did not explain drift"
fi

echo "commit log summary smoke test passed."
