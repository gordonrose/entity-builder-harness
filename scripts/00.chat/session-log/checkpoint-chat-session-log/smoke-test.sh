#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.checkpoint-diagnostics-smoke-test
#   version: 1
#   status: active
#   created_on: "2026-11-05"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: validation
#   disciplines: [agentic, security]
#   kind: script
#   purpose: Prove checkpoint, rename and transcript-registration failure preservation in disposable repositories.
#   portability: { class: source-only, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q -b chat/2026-11-05-00-00-maintenance
git -C "$REPO" config user.name Fixture
git -C "$REPO" config user.email fixture@example.invalid
for source in session-log/paths/lib.sh session-log/checkpoint-chat-session-log/script.sh \
  session-log/rename-current-chat-log-folder/script.sh transcript/register-codex-session-log/script.sh; do
  mkdir -p "$REPO/scripts/00.chat/$(dirname "$source")"
  cp "$ROOT/scripts/00.chat/$source" "$REPO/scripts/00.chat/$source"
done
LOG="commitLogs/2026/nov/05/2026-11-05-00-00-maintenance/README.md"
mkdir -p "$REPO/$(dirname "$LOG")" "$REPO/scripts/00.chat/transcript/discover-codex-session-log"
cat > "$REPO/$LOG" <<'EOF'
# Chat Session: fixture
<!-- agentic-session
id: 2026-11-05-00-00-maintenance
branch: chat/2026-11-05-00-00-maintenance
transcript_provider:
transcript_path:
-->
EOF
export MAINT_TRANSCRIPT="$REPO/transcript.jsonl"
printf '{}\n' > "$MAINT_TRANSCRIPT"
cat > "$REPO/scripts/00.chat/transcript/discover-codex-session-log/script.sh" <<'SH'
#!/usr/bin/env bash
if [ "${MAINT_FAULT:-}" = discovery ]; then echo 'ERROR: fixture-discovery-unavailable' >&2; exit 23; fi
printf '%s\n' "$MAINT_TRANSCRIPT"
SH
git -C "$REPO" add .
git -C "$REPO" commit -qm baseline
(cd "$REPO"; bash scripts/00.chat/transcript/register-codex-session-log/script.sh) > "$TMP_ROOT/registered.out"
grep -q 'transcript_provider: codex' "$REPO/$LOG" || fail "registration lost provider"
git -C "$REPO" add .
git -C "$REPO" commit -qm registered
(cd "$REPO"; bash scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh --dry-run) > "$TMP_ROOT/clean.out"
grep -q 'No session bookkeeping changes' "$TMP_ROOT/clean.out" || fail "clean checkpoint changed"
export MAINT_REAL_GIT="$(command -v git)" MAINT_REAL_AWK="$(command -v awk)" MAINT_REAL_MV="$(command -v mv)"
mkdir -p "$TMP_ROOT/bin"
cat > "$TMP_ROOT/bin/git" <<'SH'
#!/usr/bin/env bash
case "$MAINT_FAULT:$*" in
  branch:'branch --show-current'|tracked:ls-files\ --\ commitLogs/*|diff:'diff --quiet '*)
    echo MAINT_NATIVE_CANARY >&2; exit 99 ;;
  stage-log:'add -- '*|commit-log:commit*|tracked-move:mv*)
    echo MAINT_NATIVE_CANARY >&2; exit 77 ;;
esac
exec "$MAINT_REAL_GIT" "$@"
SH
cat > "$TMP_ROOT/bin/awk" <<'SH'
#!/usr/bin/env bash
if [ "$MAINT_FAULT" = construction ] && [[ "$*" == *transcript_provider=codex* ]]; then echo MAINT_NATIVE_CANARY >&2; exit 77; fi
exec "$MAINT_REAL_AWK" "$@"
SH
cat > "$TMP_ROOT/bin/mv" <<'SH'
#!/usr/bin/env bash
if [ "$MAINT_FAULT" = replacement ]; then echo MAINT_NATIVE_CANARY >&2; exit 77; fi
exec "$MAINT_REAL_MV" "$@"
SH
chmod +x "$TMP_ROOT/bin/"*
for consumer in session-log/checkpoint-chat-session-log session-log/rename-current-chat-log-folder transcript/register-codex-session-log; do
  args=(); faults=branch
  case "$consumer" in
    *checkpoint*) args=(--dry-run); faults='branch tracked diff' ;;
    *rename*) args=(renamed); faults='branch tracked tracked-move' ;;
    *register*) faults='branch discovery construction replacement' ;;
  esac
  for fault in $faults; do
    status=0
    (cd "$REPO"; MAINT_FAULT="$fault" PATH="$TMP_ROOT/bin:$PATH" \
      bash "scripts/00.chat/$consumer/script.sh" "${args[@]}") > "$TMP_ROOT/fault.out" 2>&1 || status=$?
    expected=2
    case "$fault" in discovery) expected=23 ;; construction|replacement|tracked-move) expected=77 ;; esac
    [ "$status" -eq "$expected" ] || fail "$consumer/$fault status $status"
    grep -Eq 'read-failed|observation-unavailable|operation-failed|construction-failed|replacement-failed|fixture-discovery-unavailable' "$TMP_ROOT/fault.out" || fail "$consumer/$fault reason"
    if grep -Eq 'MAINT_NATIVE_CANARY|Checkpointed|Renamed chat|Registered Codex' "$TMP_ROOT/fault.out"; then fail "$consumer/$fault leaked or succeeded"; fi
  done
done
printf '\nBookkeeping update.\n' >> "$REPO/$LOG"
(cd "$REPO"; bash scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh --dry-run) > "$TMP_ROOT/dirty.out"
grep -q 'Would checkpoint' "$TMP_ROOT/dirty.out" || fail "dirty log was not recognized"
for fault in stage-log commit-log; do
  status=0
  (cd "$REPO"; MAINT_FAULT="$fault" PATH="$TMP_ROOT/bin:$PATH" \
    bash scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh) > "$TMP_ROOT/fault.out" 2>&1 || status=$?
  [ "$status" -eq 77 ] || fail "$fault exit status"
  grep -q "stage=$fault; effect=unknown" "$TMP_ROOT/fault.out" || fail "$fault uncertainty"
  if grep -Eq 'MAINT_NATIVE_CANARY|Checkpointed' "$TMP_ROOT/fault.out"; then fail "$fault leaked or succeeded"; fi
done
(cd "$REPO"; bash scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh renamed) > "$TMP_ROOT/rename.out"
test -f "$REPO/commitLogs/2026/nov/05/2026-11-05-00-00-renamed/README.md" || fail "ordinary rename lost"
echo "session maintenance diagnostic smoke test passed."
