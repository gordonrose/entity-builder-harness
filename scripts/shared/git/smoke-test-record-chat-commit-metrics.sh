#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test chat commit recording metrics and transcript discovery.
#   domain: git
#   portability: llm-workbench-validation
#   used_by:
#     - .agentic/00.chat/checklists/before-commit.md
#     - scripts/shared/git/record-chat-commit.sh
#   effects: writes-files, branches, commits

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

mkdir -p "$REPO/scripts/shared/git" "$REPO/scripts/shared/chat" \
  "$REPO/.agentic/harness/data" "$REPO/${LOG_FILE%/README.md}"
cp "$SOURCE_ROOT/scripts/shared/git/record-chat-commit.sh" \
  "$REPO/scripts/shared/git/record-chat-commit.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" \
  "$REPO/scripts/shared/chat/session-log-paths.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/discover-codex-session-log.sh" \
  "$REPO/scripts/shared/chat/discover-codex-session-log.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/estimate-chat-cost.js" \
  "$REPO/scripts/shared/chat/estimate-chat-cost.js"
cp "$SOURCE_ROOT/.agentic/harness/data/openai-chat-pricing.json" \
  "$REPO/.agentic/harness/data/openai-chat-pricing.json"

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
estimated_chat_cost:
estimated_chat_cost_basis:
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
Estimated chat cost:
Estimated chat cost basis:
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
  CODEX_HOME="$TMP_ROOT/empty-codex" \
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
  CODEX_HOME="$TMP_ROOT/empty-codex" \
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

if ! grep -q '^estimated_chat_cost: unavailable; estimated chat tokens are unavailable$' "$REPO/$LOG_FILE"; then
  fail "missing-token escape did not mark estimated chat cost unavailable"
fi

CODEX_HOME_FIXTURE="$TMP_ROOT/codex-home"
CODEX_SESSION_LOG="$CODEX_HOME_FIXTURE/sessions/2026/06/18/rollout-test.jsonl"
mkdir -p "${CODEX_SESSION_LOG%/*}"
cat > "$CODEX_SESSION_LOG" <<EOF
{"type":"message","payload":"${SESSION_ID}"}
{"type":"message","payload":"${BRANCH}"}
{"type":"message","payload":"${LOG_FILE}"}
EOF
CODEX_SESSION_BYTES="$(wc -c < "$CODEX_SESSION_LOG" | tr -d ' ')"
CODEX_SESSION_TOKENS="$(( (CODEX_SESSION_BYTES + 3) / 4 ))"
CODEX_SESSION_COST="$(node -e "const cost=(${CODEX_SESSION_TOKENS}/1000000)*30; console.log(cost > 0 && cost < 1 ? cost.toFixed(4) : cost.toFixed(2));")"

(
  cd "$REPO"
  CODEX_HOME="$CODEX_HOME_FIXTURE" \
    bash scripts/shared/git/record-chat-commit.sh cde4567 "Test commit 2" "Discovered Codex session metric" >/dev/null
)

if ! grep -q "^codex_session_log_path: ${CODEX_SESSION_LOG}$" "$REPO/$LOG_FILE"; then
  fail "discovered Codex session log path was not recorded"
fi

if ! grep -q "^estimated_chat_tokens: ${CODEX_SESSION_TOKENS} estimated from chat transcript bytes (${CODEX_SESSION_BYTES} bytes; source: Codex session log: ${CODEX_SESSION_LOG})$" "$REPO/$LOG_FILE"; then
  fail "discovered Codex session byte metric was not recorded"
fi

if ! grep -q "^estimated_chat_cost: USD ${CODEX_SESSION_COST} estimated from estimated_chat_tokens$" "$REPO/$LOG_FILE"; then
  fail "discovered Codex session cost metric was not recorded"
fi

if ! grep -q '^estimated_chat_cost_basis: profile=chat-latest-standard-conservative-output; model=chat-latest;' "$REPO/$LOG_FILE"; then
  fail "chat cost basis did not use the default ChatGPT pricing profile"
fi

(
  cd "$REPO"
  CHAT_TRANSCRIPT_BYTES=4096 \
  CHAT_TRANSCRIPT_SOURCE="smoke transcript fixture" \
    bash scripts/shared/git/record-chat-commit.sh def5678 "Test commit 3" "Transcript byte token metric" >/dev/null
)

if ! grep -q '^estimated_chat_tokens: 1024 estimated from chat transcript bytes (4096 bytes; source: smoke transcript fixture)$' "$REPO/$LOG_FILE"; then
  fail "transcript-byte chat token metric was not recorded"
fi

if ! grep -q '^estimated_chat_cost: USD 0.0307 estimated from estimated_chat_tokens$' "$REPO/$LOG_FILE"; then
  fail "transcript-byte chat cost metric was not recorded"
fi

if grep -q 'estimated from session log' "$REPO/$LOG_FILE"; then
  fail "session log size was used as a token source"
fi

echo "record chat commit metrics smoke test passed."
