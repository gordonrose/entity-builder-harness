#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/record-chat-commit-metrics-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
SESSION_ID="2026-06-18-00-00-token-metrics"
BRANCH="chat/${SESSION_ID}"
LOG_FILE="commitLogs/2026/jun/18/${SESSION_ID}/README.md"

mkdir -p "$REPO/scripts/shared/git" "$REPO/scripts/shared/chat" "$REPO/${LOG_FILE%/README.md}"
cp "$SOURCE_ROOT/scripts/shared/git/record-chat-commit.sh" \
  "$REPO/scripts/shared/git/record-chat-commit.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" \
  "$REPO/scripts/shared/chat/session-log-paths.sh"

cat > "$REPO/$LOG_FILE" <<EOF
# Chat Session: token metrics

<!-- agentic-session
id: ${SESSION_ID}
branch: ${BRANCH}
raised_at_utc: 2026-06-18T00:00:00Z
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_tokens:
-->

## Commits

- None recorded yet.

## Activity Log

- None recorded yet.

## Session Metrics

Raised at UTC: 2026-06-18T00:00:00Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated tokens:
EOF

(
  cd "$REPO"
  git init -q
  git config user.name "Smoke Test"
  git config user.email "smoke@example.invalid"
  git add .
  git commit -q -m "initial"
  git checkout -q -b "$BRANCH"
)

set +e
(
  cd "$REPO"
  bash scripts/shared/git/record-chat-commit.sh abc1234 "Test commit" "Missing token metric"
) >/dev/null 2>"$TMP_ROOT/missing-metrics.err"
MISSING_STATUS="$?"
set -e

if [ "$MISSING_STATUS" -eq 0 ]; then
  fail "recording succeeded without chat transcript metrics"
fi

if ! grep -q "missing chat transcript metrics" "$TMP_ROOT/missing-metrics.err"; then
  fail "missing metrics failure was not explained"
fi

(
  cd "$REPO"
  ALLOW_MISSING_CHAT_TRANSCRIPT_METRICS=yes \
    bash scripts/shared/git/record-chat-commit.sh abc1234 "Test commit" "Legacy token metric escape" >/dev/null
)

if grep -q '^estimated_tokens:' "$REPO/$LOG_FILE"; then
  fail "legacy estimated_tokens metadata remained after recording"
fi

if ! grep -q '^estimated_chat_tokens: unavailable; transcript source not supplied by chat$' "$REPO/$LOG_FILE"; then
  fail "legacy chat token metric escape was not marked unavailable"
fi

if ! grep -q '^Estimated chat tokens: unavailable; transcript source not supplied by chat$' "$REPO/$LOG_FILE"; then
  fail "visible legacy chat token metric escape was not marked unavailable"
fi

(
  cd "$REPO"
  CHAT_TRANSCRIPT_BYTES=4096 \
  CHAT_TRANSCRIPT_SOURCE="smoke transcript fixture" \
    bash scripts/shared/git/record-chat-commit.sh def5678 "Test commit 2" "Transcript byte token metric" >/dev/null
)

if ! grep -q '^estimated_chat_tokens: 1024 estimated from chat transcript bytes (4096 bytes; source: smoke transcript fixture)$' "$REPO/$LOG_FILE"; then
  fail "transcript-byte chat token metric was not recorded"
fi

if grep -q 'estimated from session log' "$REPO/$LOG_FILE"; then
  fail "session log size was used as a token source"
fi

echo "record chat commit metrics smoke test passed."
