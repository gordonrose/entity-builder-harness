#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.prepare-chat-session-before-commit.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test chat session readiness checks before task commits.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.prepare-chat-session-before-commit.readme
#     path: scripts/00.chat/session-log/prepare-chat-session-before-commit/README.md
#   effects:
#   - writes-files
#   - branches
#   - commits
fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/prepare-chat-session-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
SESSION_ID="2026-07-08-22-34-prepare-context-hygiene"
LOG_DIR="$REPO/commitLogs/2026/jul/08/$SESSION_ID"
LOG_FILE="$LOG_DIR/README.md"

mkdir -p \
  "$REPO/.agentic/00.chat/checklists" \
  "$REPO/scripts/00.chat/session-log/check-commit-prerequisites" \
  "$REPO/scripts/00.chat/session-log/check-commitlog-deletions" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/session-log/prepare-chat-session-before-commit" \
  "$REPO/scripts/00.chat/worktree/check-write-location" \
  "$REPO/scripts/01.harness/artifact-metadata/check-headers" \
  "$LOG_DIR"

git -C "$REPO" init --quiet --initial-branch=main

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh" "$REPO/scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh"
chmod +x "$REPO/scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh"

for stub in \
  "$REPO/scripts/00.chat/worktree/check-write-location/script.sh" \
  "$REPO/scripts/00.chat/session-log/check-commit-prerequisites/script.sh" \
  "$REPO/scripts/00.chat/session-log/check-commitlog-deletions/script.sh" \
  "$REPO/scripts/01.harness/check-deterministic-process-drift.sh" \
  "$REPO/scripts/01.harness/check-governed-script-command-drift.sh" \
  "$REPO/scripts/01.harness/artifact-metadata/check-headers/script.sh"; do
  cat > "$stub" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "stub-ok"
EOF
  chmod +x "$stub"
done

cat > "$REPO/.agentic/00.chat/checklists/before-commit.md" <<'EOF'
# Before Commit
EOF

cat > "$LOG_FILE" <<EOF
# Chat Session: prepare context hygiene smoke

<!-- agentic-session
id: $SESSION_ID
task: test prepare context hygiene
branch: chat/$SESSION_ID
worktree:
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
-->

## Initial Intent

test prepare context hygiene

## Decisions Made

- Decision: Require context hygiene.
  Rationale: Preserve durable carry-forward instead of raw noise.

## ADR Disposition

ADR needed: no
ADR path:
Reason: Session-log gate behavior only; no durable architecture decision.
EOF

git -C "$REPO" add .
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'
git -C "$REPO" switch --quiet -c "chat/$SESSION_ID"

set +e
bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh \
  >"$TMP_ROOT/missing.out" 2>"$TMP_ROOT/missing.err"
missing_status=$?
set -e

if [ "$missing_status" -eq 0 ]; then
  fail "prepare gate passed without context hygiene"
fi

grep -q 'Context hygiene summary is still missing' "$TMP_ROOT/missing.err" \
  || fail "prepare gate did not report missing context hygiene"

cat >> "$LOG_FILE" <<'EOF'

## Context Hygiene

- Summary: Noisy evidence was reduced to decisions, tests, and unresolved issues.
  Durable evidence: Session log and task commit carry forward the important state.
EOF

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh \
  >"$TMP_ROOT/passing.out"

grep -q 'Chat session is ready for commit:' "$TMP_ROOT/passing.out" \
  || fail "prepare gate did not pass with context hygiene"

echo "prepare chat session smoke test passed."
