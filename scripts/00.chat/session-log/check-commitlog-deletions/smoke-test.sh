#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.check-commitlog-deletions.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test commit log deletion protection for recorded work.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: harness.architecture.adr.0010-protect-commit-logs-with-recorded-work
#   - id: chat.script.session-log.check-commitlog-deletions.readme
#     path: scripts/00.chat/session-log/check-commitlog-deletions/README.md
#   - id: chat.script.session-log.check-commitlog-deletions
#     path: scripts/00.chat/session-log/check-commitlog-deletions/script.sh
#   effects:
#   - writes-files
#   - commits
SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/commitlog-deletions-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO/scripts/00.chat/session-log/check-commitlog-deletions"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/check-commitlog-deletions/script.sh" "$REPO/scripts/00.chat/session-log/check-commitlog-deletions/script.sh"
chmod +x "$REPO/scripts/00.chat/session-log/check-commitlog-deletions/script.sh"

git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"

COMMITTED_LOG="$REPO/commitLogs/2026/jun/16/committed/README.md"
EMPTY_LOG="$REPO/commitLogs/2026/jun/16/empty/README.md"
RETAINED_LOG="$REPO/commitLogs/2026/jun/16/retained/README.md"

mkdir -p "$(dirname "$COMMITTED_LOG")" "$(dirname "$EMPTY_LOG")" "$(dirname "$RETAINED_LOG")"

cat > "$COMMITTED_LOG" <<'EOF'
# Chat Session: committed

<!-- agentic-session
latest_commit_sha: abc1234
-->

## Commits

- Commit: `abc1234`
EOF

cat > "$EMPTY_LOG" <<'EOF'
# Chat Session: empty

## Commits

TBD
EOF

cat > "$RETAINED_LOG" <<'EOF'
# Chat Session: retained

retain: yes

## Commits

TBD
EOF

git -C "$REPO" add .
git -C "$REPO" commit -q -m "add logs"

git -C "$REPO" rm -q "$COMMITTED_LOG" "$EMPTY_LOG" "$RETAINED_LOG"

set +e
(
  cd "$REPO"
  bash scripts/00.chat/session-log/check-commitlog-deletions/script.sh
) > "$TMP_ROOT/protected.out" 2> "$TMP_ROOT/protected.err"
PROTECTED_STATUS="$?"
set -e

if [ "$PROTECTED_STATUS" -eq 0 ]; then
  fail "protected commit log deletions were allowed"
fi

if ! grep -q "cannot delete commit log with recorded commits" "$TMP_ROOT/protected.err"; then
  fail "recorded commit deletion was not reported"
fi

if ! grep -q "cannot delete commit log marked for retention" "$TMP_ROOT/protected.err"; then
  fail "retained commit log deletion was not reported"
fi

git -C "$REPO" restore --staged --worktree -- "$COMMITTED_LOG" "$RETAINED_LOG"

(
  cd "$REPO"
  bash scripts/00.chat/session-log/check-commitlog-deletions/script.sh
) > "$TMP_ROOT/empty-only.out" 2> "$TMP_ROOT/empty-only.err"

if ! grep -q "Commit log deletion gate passed" "$TMP_ROOT/empty-only.out"; then
  fail "empty-only deletion did not pass"
fi

echo "commitlog deletion smoke test passed."
