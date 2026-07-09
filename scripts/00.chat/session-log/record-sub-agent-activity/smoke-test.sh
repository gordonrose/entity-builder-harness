#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.record-sub-agent-activity.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test sub-agent activity recording in chat session logs.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.record-sub-agent-activity
#     path: scripts/00.chat/session-log/record-sub-agent-activity/script.sh
#   - id: chat.script.session-log.record-sub-agent-activity.readme
#     path: scripts/00.chat/session-log/record-sub-agent-activity/README.md
#   effects:
#   - writes-files
#   - branches
#   - commits
fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/record-sub-agent-activity-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
SESSION_ID="2026-07-08-20-00-sub-agent-activity"
BRANCH="chat/${SESSION_ID}"
LOG_FILE="commitLogs/2026/jul/08/${SESSION_ID}/README.md"

mkdir -p \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/session-log/record-sub-agent-activity" \
  "$REPO/${LOG_FILE%/README.md}"

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" \
  "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/record-sub-agent-activity/script.sh" \
  "$REPO/scripts/00.chat/session-log/record-sub-agent-activity/script.sh"
chmod +x "$REPO/scripts/00.chat/session-log/record-sub-agent-activity/script.sh"

cat > "$REPO/$LOG_FILE" <<EOF
# Chat Session: sub-agent activity

<!-- agentic-session
id: ${SESSION_ID}
branch: ${BRANCH}
raised_at_utc: 2026-07-08T20:00:00Z
-->

## Sub-Agent Activity

- None recorded yet.

## Activity Log

- None recorded yet.
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

(
  cd "$REPO"
  bash scripts/00.chat/session-log/record-sub-agent-activity/script.sh \
    --mode sub-agent \
    --status completed \
    --agent "implementation sub-agent" \
    --scope "prompt delegation wording" \
    --summary "Updated generated prompts to request delegated implementation work." \
    --files "scripts/00.chat/startup/start-chat-session/script.sh" \
    --checks "startup smoke test" \
    --git-actions "none" \
    --blockers "none" \
    --next-step "run full portability checks" >/dev/null
)

if grep -q -- '- None recorded yet.' "$REPO/$LOG_FILE"; then
  fail "placeholder remained after recording sub-agent activity"
fi

if ! grep -q '^Delegation mode: sub-agent$' "$REPO/$LOG_FILE"; then
  fail "sub-agent delegation mode was not recorded"
fi

if ! grep -q '^Fallback used: no$' "$REPO/$LOG_FILE"; then
  fail "sub-agent fallback flag was not recorded as no"
fi

(
  cd "$REPO"
  bash scripts/00.chat/session-log/record-sub-agent-activity/script.sh \
    --mode direct-fallback \
    --status completed \
    --agent "supervising agent" \
    --scope "git closeout checks" \
    --summary "No sub-agent capability was available, so the supervising agent ran the checks directly." \
    --git-actions "checked status only" >/dev/null
)

if ! grep -q '^Delegation mode: direct-fallback$' "$REPO/$LOG_FILE"; then
  fail "direct fallback mode was not recorded"
fi

if ! grep -q '^Fallback used: yes$' "$REPO/$LOG_FILE"; then
  fail "direct fallback flag was not recorded as yes"
fi

if ! grep -q 'Sub-agent activity recorded' "$REPO/$LOG_FILE"; then
  fail "activity log did not receive a timeline entry"
fi

set +e
(
  cd "$REPO"
  bash scripts/00.chat/session-log/record-sub-agent-activity/script.sh \
    --mode unsupported \
    --status completed \
    --agent "bad" \
    --scope "bad" \
    --summary "bad"
) >/dev/null 2>"$TMP_ROOT/invalid-mode.err"
INVALID_STATUS="$?"
set -e

if [ "$INVALID_STATUS" -eq 0 ]; then
  fail "invalid mode unexpectedly succeeded"
fi

if ! grep -q 'invalid mode' "$TMP_ROOT/invalid-mode.err"; then
  fail "invalid mode failure was not explained"
fi

echo "record sub-agent activity smoke test passed."
