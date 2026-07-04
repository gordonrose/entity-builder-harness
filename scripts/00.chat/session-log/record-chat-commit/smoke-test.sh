#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.record-chat-commit.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test chat commit recording metrics and transcript discovery.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.checklists.before-commit
#     path: .agentic/00.chat/checklists/before-commit.md
#   - id: chat.script.session-log.record-chat-commit.readme
#     path: scripts/00.chat/session-log/record-chat-commit/README.md
#   - id: chat.script.session-log.record-chat-commit
#     path: scripts/00.chat/session-log/record-chat-commit/script.sh
#   effects:
#   - writes-files
#   - branches
#   - commits
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

mkdir -p "$REPO/scripts/00.chat/transcript/discover-codex-session-log" \
  "$REPO/scripts/00.chat/metrics/estimate-chat-cost" \
  "$REPO/scripts/00.chat/metrics/data" \
  "$REPO/scripts/00.chat/session-log/record-chat-commit" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/${LOG_FILE%/README.md}"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/record-chat-commit/script.sh" \
  "$REPO/scripts/00.chat/session-log/record-chat-commit/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" \
  "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/transcript/discover-codex-session-log/script.sh" \
  "$REPO/scripts/00.chat/transcript/discover-codex-session-log/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/metrics/estimate-chat-cost/script.js" \
  "$REPO/scripts/00.chat/metrics/estimate-chat-cost/script.js"
cp "$SOURCE_ROOT/scripts/00.chat/metrics/data/chat-pricing.json" \
  "$REPO/scripts/00.chat/metrics/data/chat-pricing.json"
chmod +x "$REPO/scripts/00.chat/session-log/record-chat-commit/script.sh" \
  "$REPO/scripts/00.chat/transcript/discover-codex-session-log/script.sh"

cat > "$REPO/$LOG_FILE" <<EOF
# Chat Session: token metrics

<!-- agentic-session
id: ${SESSION_ID}
branch: ${BRANCH}
raised_at_utc: 2026-06-18T00:00:00Z
transcript_provider:
transcript_path:
transcript_bytes:
transcript_source:
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
  CHAT_TRANSCRIPT_METRICS_MODE=strict \
    bash scripts/00.chat/session-log/record-chat-commit/script.sh abc1234 "Test commit" "Missing token metric"
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
    bash scripts/00.chat/session-log/record-chat-commit/script.sh abc1234 "Test commit" "Portable unavailable token metric" >/dev/null
)

if grep -q '^estimated_tokens:' "$REPO/$LOG_FILE"; then
  fail "legacy estimated_tokens metadata remained after recording"
fi

if ! grep -q '^estimated_chat_tokens: unavailable; transcript source not supplied by chat$' "$REPO/$LOG_FILE"; then
  fail "portable missing transcript metric was not marked unavailable"
fi

if ! grep -q '^Estimated chat tokens: unavailable; transcript source not supplied by chat$' "$REPO/$LOG_FILE"; then
  fail "visible portable missing transcript metric was not marked unavailable"
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

(
  cd "$REPO"
  CODEX_HOME="$CODEX_HOME_FIXTURE" \
  CHAT_TRANSCRIPT_PROVIDER=codex \
    bash scripts/00.chat/session-log/record-chat-commit/script.sh cde4567 "Test commit 2" "Discovered Codex session metric" >/dev/null
)

if ! grep -q '^transcript_provider: codex$' "$REPO/$LOG_FILE"; then
  fail "discovered Codex provider was not recorded"
fi

if ! grep -q "^transcript_path: ${CODEX_SESSION_LOG}$" "$REPO/$LOG_FILE"; then
  fail "discovered Codex transcript path was not recorded"
fi

if ! grep -q "^estimated_chat_tokens: ${CODEX_SESSION_TOKENS} estimated from chat transcript bytes (${CODEX_SESSION_BYTES} bytes; source: codex path: ${CODEX_SESSION_LOG})$" "$REPO/$LOG_FILE"; then
  fail "discovered Codex session byte metric was not recorded"
fi

if ! grep -q '^estimated_chat_cost: unavailable; no pricing profile selected$' "$REPO/$LOG_FILE"; then
  fail "Codex transcript without explicit pricing profile did not leave cost unavailable"
fi

if ! grep -q '^estimated_chat_cost_basis: unavailable; set CHAT_COST_PROFILE or CHAT_COST_PRICING_FILE$' "$REPO/$LOG_FILE"; then
  fail "Codex transcript without explicit pricing profile did not explain unavailable cost basis"
fi

if grep -q '^estimated_chat_cost_basis: profile=.*openai' "$REPO/$LOG_FILE"; then
  fail "default Codex transcript cost used an OpenAI pricing profile"
fi

(
  cd "$REPO"
  CHAT_TRANSCRIPT_PROVIDER=manual \
  CHAT_TRANSCRIPT_BYTES=4096 \
  CHAT_TRANSCRIPT_SOURCE="smoke transcript fixture" \
  CHAT_COST_PROFILE=openai-chat-latest-standard-conservative-output \
    bash scripts/00.chat/session-log/record-chat-commit/script.sh def5678 "Test commit 3" "Transcript byte token metric" >/dev/null
)

if ! grep -q '^estimated_chat_tokens: 1024 estimated from chat transcript bytes (4096 bytes; source: smoke transcript fixture)$' "$REPO/$LOG_FILE"; then
  fail "transcript-byte chat token metric was not recorded"
fi

if ! grep -q '^transcript_provider: manual$' "$REPO/$LOG_FILE"; then
  fail "manual transcript provider was not recorded"
fi

if ! grep -q '^estimated_chat_cost: USD 0.0307 estimated from estimated_chat_tokens$' "$REPO/$LOG_FILE"; then
  fail "explicit OpenAI chat cost profile did not record transcript-byte cost"
fi

if ! grep -q '^estimated_chat_cost_basis: profile=openai-chat-latest-standard-conservative-output; model=chat-latest;' "$REPO/$LOG_FILE"; then
  fail "explicit OpenAI chat cost profile was not recorded in the cost basis"
fi

if grep -q 'estimated from session log' "$REPO/$LOG_FILE"; then
  fail "session log size was used as a token source"
fi

echo "record chat commit metrics smoke test passed."
