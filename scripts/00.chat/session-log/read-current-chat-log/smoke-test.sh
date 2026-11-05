#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.read-current-chat-log.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-23"
#   updated_on: "2026-11-05"
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
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
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
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
latest_context_packet_id: packet.selector-fixture.previous
latest_context_packet_routing_summary: previous prompt routed to 02.rag-rulebook discovery
latest_context_packet_at_utc: 2026-06-23T18:05:00Z
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

grep -q '^chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md$' "$TMP_ROOT/empty.out" \
  || fail "empty session lifecycle metadata was not printed"

grep -q '^latest_context_packet_id:$' "$TMP_ROOT/empty.out" \
  || fail "empty session context packet field was not printed"

if grep -Eq '^(layer|mode|workflow): ' "$TMP_ROOT/empty.out"; then
  fail "empty session printed durable classification metadata"
fi

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

# Force metadata lookup rather than the exact historical path.
mv "$REPO/commitLogs/2026/jun/23/2026-06-23-18-05-recorded-session" "$REPO/commitLogs/2026/jun/23/renamed"
mkdir -p "$TMP_ROOT/bin"
for command in find awk; do
  printf '#!/usr/bin/env bash\necho PRIVATE_LOOKUP_CANARY >&2\nexit 70\n' > "$TMP_ROOT/bin/$command"
  chmod +x "$TMP_ROOT/bin/$command"
  if (cd "$REPO" && PATH="$TMP_ROOT/bin:$PATH" bash scripts/00.chat/session-log/read-current-chat-log/script.sh --allow-recorded-session) > "$TMP_ROOT/lookup-failure.out" 2>&1; then
    fail "failed lookup was accepted"
  fi
  expected='ERROR: session-directory-read-failed'
  [ "$command" != awk ] || expected='ERROR: session-metadata-read-failed'
  test "$(cat "$TMP_ROOT/lookup-failure.out")" = "$expected" || fail "lookup failed without precise safe outcome"
  rm "$TMP_ROOT/bin/$command"
done
(cd "$REPO" && bash scripts/00.chat/session-log/read-current-chat-log/script.sh --allow-recorded-session) > "$TMP_ROOT/renamed.out"
grep -q '^latest_commit_sha: abc1234$' "$TMP_ROOT/renamed.out" || fail "renamed lookup regressed"
cp -R "$REPO/commitLogs/2026/jun/23/renamed" "$REPO/commitLogs/2026/jun/23/duplicate"
if (cd "$REPO" && bash scripts/00.chat/session-log/read-current-chat-log/script.sh --allow-recorded-session) > "$TMP_ROOT/ambiguous.out" 2>&1; then
  fail "ambiguous lookup was accepted"
fi
test "$(cat "$TMP_ROOT/ambiguous.out")" = 'ERROR: session-log-ambiguous' || fail "ambiguous lookup became absence"
echo "read-current-chat-log smoke test passed."
