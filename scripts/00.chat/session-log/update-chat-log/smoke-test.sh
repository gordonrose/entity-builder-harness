#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.update-chat-log.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-07-09"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test structured chat log updates.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.update-chat-log.readme
#     path: scripts/00.chat/session-log/update-chat-log/README.md
#   effects:
#   - writes-files
#   - branches
#   - commits
fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/update-chat-log-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
SESSION_ID="2026-07-08-22-33-test-context-hygiene"
LOG_DIR="$REPO/commitLogs/2026/jul/08/$SESSION_ID"
LOG_FILE="$LOG_DIR/README.md"

mkdir -p \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/session-log/update-chat-log" \
  "$LOG_DIR"

git -C "$REPO" init --quiet --initial-branch=main

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/update-chat-log/script.sh" "$REPO/scripts/00.chat/session-log/update-chat-log/script.sh"
chmod +x "$REPO/scripts/00.chat/session-log/update-chat-log/script.sh"

cat > "$LOG_FILE" <<EOF
# Chat Session: context hygiene smoke

<!-- agentic-session
id: $SESSION_ID
task: test context hygiene
branch: chat/$SESSION_ID
worktree:
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
-->

## Initial Intent

test context hygiene

## Context Hygiene

- None recorded yet.

## ADR Disposition

ADR needed: unknown
ADR path:
Reason:

## Activity Log

- None recorded yet.
EOF

git -C "$REPO" add .
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'
git -C "$REPO" switch --quiet -c "chat/$SESSION_ID"

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/update-chat-log/script.sh context-hygiene \
    "Noisy tool output was reduced to decisions and test outcomes." \
    "Durable evidence lives in the task commit and session log." \
  >"$TMP_ROOT/update.out"

if grep -q -- '- None recorded yet.' "$LOG_FILE"; then
  fail "context hygiene placeholder remained after update"
fi

grep -q '^- Summary: Noisy tool output was reduced to decisions and test outcomes\.$' "$LOG_FILE" \
  || fail "context hygiene summary was not recorded"

grep -q '^  Durable evidence: Durable evidence lives in the task commit and session log\.$' "$LOG_FILE" \
  || fail "context hygiene durable evidence was not recorded"

grep -q '^### .* - Context hygiene$' "$LOG_FILE" \
  || fail "context hygiene activity entry was not recorded"

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/update-chat-log/script.sh adr-disposition not-needed \
    "The smoke update does not make an architectural decision." \
  >"$TMP_ROOT/adr-disposition.out"

grep -qx 'ADR path:' "$LOG_FILE" \
  || fail "not-needed ADR disposition left whitespace in the empty ADR path"

git -C "$REPO" diff --check \
  || fail "ADR disposition introduced whitespace errors"

for consumer in record-sub-agent-activity record-main-refresh-conflict; do
  mkdir -p "$REPO/scripts/00.chat/session-log/$consumer"
  cp "$SOURCE_ROOT/scripts/00.chat/session-log/$consumer/script.sh" "$REPO/scripts/00.chat/session-log/$consumer/script.sh"
done
export WRITER_REAL_GIT="$(command -v git)" WRITER_REAL_AWK="$(command -v awk)" WRITER_REAL_MV="$(command -v mv)"
mkdir -p "$TMP_ROOT/bin"
cat > "$TMP_ROOT/bin/git" <<'SH'
#!/usr/bin/env bash
if [ "$WRITER_FAULT:$*" = 'branch:branch --show-current' ]; then echo WRITER_NATIVE_CANARY >&2; exit 99; fi
exec "$WRITER_REAL_GIT" "$@"
SH
cat > "$TMP_ROOT/bin/awk" <<'SH'
#!/usr/bin/env bash
args=()
for arg in "$@"; do
  case "$arg" in
    entry_path=*)
      if [ "$WRITER_FAULT" = entry ]; then arg='entry_path=/no-such-WRITER_NATIVE_CANARY'; fi ;;
  esac
  args+=("$arg")
done
exec "$WRITER_REAL_AWK" "${args[@]}"
SH
cat > "$TMP_ROOT/bin/mv" <<'SH'
#!/usr/bin/env bash
if [ "$WRITER_FAULT" = replacement ]; then echo WRITER_NATIVE_CANARY >&2; exit 77; fi
exec "$WRITER_REAL_MV" "$@"
SH
chmod +x "$TMP_ROOT/bin/"*
for consumer in update-chat-log record-sub-agent-activity record-main-refresh-conflict; do
  case "$consumer" in
    update-chat-log) args=(question "question" "answer") ;;
    record-sub-agent-activity) args=(--mode sub-agent --status completed --agent fixture --scope tests --summary done) ;;
    record-main-refresh-conflict) args=(--path example.ts --type fixture --reason fixture --action retained --mode manual --preflight-branch fixture --preflight-worktree fixture) ;;
  esac
  (cd "$REPO"; bash "scripts/00.chat/session-log/$consumer/script.sh" "${args[@]}") > "$TMP_ROOT/ordinary.out"
  cp "$LOG_FILE" "$TMP_ROOT/before"
  for fault in branch entry replacement; do
    status=0
    (cd "$REPO"; WRITER_FAULT="$fault" PATH="$TMP_ROOT/bin:$PATH" \
      bash "scripts/00.chat/session-log/$consumer/script.sh" "${args[@]}") > "$TMP_ROOT/fault.out" 2>&1 || status=$?
    expected=2; stage=entry-construction
    case "$fault" in
      branch) stage=session-log-branch-read-failed ;;
      replacement) stage=replacement; expected=77 ;;
    esac
    [ "$status" -eq "$expected" ] || fail "$consumer/$fault status $status"
    grep -q "$stage" "$TMP_ROOT/fault.out" || fail "$consumer/$fault lost reason"
    if grep -q WRITER_NATIVE_CANARY "$TMP_ROOT/fault.out"; then fail "$consumer/$fault leaked"; fi
    cmp "$LOG_FILE" "$TMP_ROOT/before" || fail "$consumer/$fault changed log"
  done
done

echo "update chat log smoke test passed."
