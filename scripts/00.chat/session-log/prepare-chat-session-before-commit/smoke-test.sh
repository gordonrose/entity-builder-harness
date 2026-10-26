#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.prepare-chat-session-before-commit.smoke-test
#   version: 4
#   status: active
#   created_on: "2026-07-09"
#   updated_on: "2026-10-26"
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
  "$REPO/docs/00.chat/adrs" \
  "$REPO/docs/01.harness/adrs" \
  "$REPO/docs/02.rag-rulebook/adrs" \
  "$REPO/docs/aws/architecture/adrs" \
  "$REPO/scripts/00.chat/session-log/check-commit-prerequisites" \
  "$REPO/scripts/00.chat/session-log/check-commitlog-deletions" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/session-log/prepare-chat-session-before-commit" \
  "$REPO/scripts/00.chat/worktree/check-write-location" \
  "$REPO/scripts/01.harness/artifact-metadata/check-headers" \
  "$REPO/scripts/01.harness/artifact-metadata/generate-index" \
  "$REPO/scripts/01.harness/artifact-metadata/update-lifecycle" \
  "$REPO/scripts/repo/check-selection" \
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

cat > "$REPO/scripts/01.harness/artifact-metadata/update-lifecycle/script.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'lifecycle %s\n' "$*" >> preparation-order
printf '%s\n' '{"plans":[{"path":".agentic/task.md"}],"errors":[]}'
EOF
chmod +x "$REPO/scripts/01.harness/artifact-metadata/update-lifecycle/script.sh"

cat > "$REPO/scripts/01.harness/artifact-metadata/generate-index/script.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'index %s\n' "$*" >> preparation-order
printf '%s\n' '{"schema":"agentic-artifact-index/v1"}'
EOF
chmod +x "$REPO/scripts/01.harness/artifact-metadata/generate-index/script.sh"

cat > "$REPO/scripts/repo/check-selection/script.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'selector %s\n' "$*" >> preparation-order
printf '%s\n' '{"schema":"repo/check-selection-report/v1","verdict":"planned","checks":[]}'
EOF
chmod +x "$REPO/scripts/repo/check-selection/script.sh"

cat > "$REPO/scripts/01.harness/artifact-metadata/check-headers/script.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'headers %s\n' "$*" >> preparation-order
echo 'stub-ok'
EOF
chmod +x "$REPO/scripts/01.harness/artifact-metadata/check-headers/script.sh"

cat > "$REPO/.agentic/00.chat/checklists/before-commit.md" <<'EOF'
# Before Commit
EOF

cat > "$REPO/docs/00.chat/adrs/0001-first-decision.md" <<'EOF'
# ADR 0001: First Decision

## Status

Accepted.
EOF

cat > "$REPO/docs/02.rag-rulebook/adrs/0002-second-decision.md" <<'EOF'
# ADR 0002: Second Decision

## Status

Accepted.
EOF

cat > "$REPO/docs/aws/architecture/adrs/0001-aws-decision.md" <<'EOF'
# ADR 0001: AWS Decision

## Status

Accepted.
EOF

cat > "$REPO/docs/01.harness/adrs/0032-owner-aligned-decision.md" <<'EOF'
# ADR 0032: Owner Aligned Decision

## Status

Accepted.
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

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh \
  --before-verification --paths .agentic/task.md src/feature.ts \
  >"$TMP_ROOT/before-verification.out"

grep -q 'Verification preparation passed.' "$TMP_ROOT/before-verification.out" \
  || fail "before-verification mode did not pass"
expected_order=$'lifecycle --paths .agentic/task.md src/feature.ts --skip-non-artifacts --apply\nindex --paths .agentic/task.md --strict\nheaders --paths .agentic/task.md src/feature.ts\nselector --paths .agentic/task.md src/feature.ts --stage local --record-preparation --json'
if [[ "$(cat "$REPO/preparation-order")" != "$expected_order" ]]; then
  fail "before-verification did not complete lifecycle, structural, then selector preparation in order"
fi

rm "$REPO/scripts/repo/check-selection/script.sh"
: > "$REPO/preparation-order"
bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh \
  --before-verification --paths .agentic/task.md \
  >"$TMP_ROOT/portable-before-verification.out"
grep -q 'Repository selector is absent' "$TMP_ROOT/portable-before-verification.out" \
  || fail "before-verification did not preserve portable operation without a repository selector"
if [[ "$(cat "$REPO/preparation-order")" != $'lifecycle --paths .agentic/task.md --skip-non-artifacts --apply\nindex --paths .agentic/task.md --strict\nheaders --paths .agentic/task.md' ]]; then
  fail "portable preparation unexpectedly attempted repository selector work"
fi

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

- Decision: Accept multiple ADR paths.
  Rationale: Some chats create or rely on more than one durable architecture decision.

## Context Hygiene

- Summary: Noisy evidence was reduced to decisions, tests, and unresolved issues.
  Durable evidence: Session log and task commit carry forward the important state.

## ADR Disposition

ADR needed: yes
ADR paths:
- docs/00.chat/adrs/0001-first-decision.md
- docs/02.rag-rulebook/adrs/0002-second-decision.md
- docs/aws/architecture/adrs/0001-aws-decision.md
- docs/01.harness/adrs/0032-owner-aligned-decision.md
Reason: This smoke test covers multiple ADR paths in one session log.
EOF

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh \
  >"$TMP_ROOT/multi-adr.out"

grep -q 'Chat session is ready for commit:' "$TMP_ROOT/multi-adr.out" \
  || fail "prepare gate did not pass with multiple ADR paths"

echo "prepare chat session smoke test passed."
