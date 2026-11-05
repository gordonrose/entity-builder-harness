#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.recovery.import-active-paths-to-chat-worktree.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: recovery
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test recovery import from an active worktree into a chat-owned worktree.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.recovery.import-active-paths-to-chat-worktree
#     path: scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh
#   effects:
#   - branches
#   - commits
#   - worktrees
#   - writes-files

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/import-active-paths-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

assert_file_equals() {
  local file="$1"
  local expected="$2"
  local actual

  actual="$(cat "$file")"
  if [ "$actual" != "$expected" ]; then
    fail "expected $file to contain '$expected', got '$actual'"
  fi
}

REPO="$TMP_ROOT/repo"
mkdir -p \
  "$REPO/scripts/00.chat/recovery/import-active-paths-to-chat-worktree" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/worktree/paths"

cp "$SOURCE_ROOT/scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh" \
  "$REPO/scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" \
  "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" \
  "$REPO/scripts/00.chat/worktree/paths/lib.sh"

git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"

mkdir -p "$REPO/docs"
printf 'base\n' > "$REPO/docs/kept.txt"
printf 'delete me\n' > "$REPO/docs/remove-me.txt"
git -C "$REPO" add \
  docs/kept.txt \
  docs/remove-me.txt \
  scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh \
  scripts/00.chat/session-log/paths/lib.sh \
  scripts/00.chat/worktree/paths/lib.sh
git -C "$REPO" commit -q -m "initial"

SESSION_ID="2026-06-19-21-00-import-smoke"
SESSION_BRANCH="chat/$SESSION_ID"
SESSION_DIR="$REPO/commitLogs/2026/jun/19/$SESSION_ID"
SESSION_LOG="$SESSION_DIR/README.md"
WORKTREE_ROOT="$TMP_ROOT/worktrees"
WORKTREE_PATH="$WORKTREE_ROOT/chat_${SESSION_ID}-$(printf '%s' "$SESSION_BRANCH" | cksum | awk '{print $1}')"

mkdir -p "$SESSION_DIR"
cat > "$SESSION_LOG" <<EOF
# Chat Session: import smoke

<!-- agentic-session
id: $SESSION_ID
task: import smoke
branch: $SESSION_BRANCH
worktree: $WORKTREE_PATH
layer: 00.chat
mode: implementation
workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-06-19T20:00:00Z
-->
EOF

git -C "$REPO" add "$SESSION_LOG"
git -C "$REPO" commit -q -m "add session log"
git -C "$REPO" branch "$SESSION_BRANCH"
git -C "$REPO" worktree add --quiet "$WORKTREE_PATH" "$SESSION_BRANCH"

printf 'changed in active\n' > "$REPO/docs/kept.txt"
rm "$REPO/docs/remove-me.txt"
mkdir -p "$REPO/docs/new-dir"
printf 'new file\n' > "$REPO/docs/new-dir/new.txt"

export REAL_GIT="$(command -v git)" REAL_MKDIR="$(command -v mkdir)" REAL_RM="$(command -v rm)" REAL_CP="$(command -v cp)"
export FAULT_MARKER="$TMP_ROOT/fault-attempts"
mkdir "$TMP_ROOT/fault-bin"
for command in git mkdir rm cp; do
  printf '#!/usr/bin/env bash\ncommand=%q\n' "$command" > "$TMP_ROOT/fault-bin/$command"
  cat >> "$TMP_ROOT/fault-bin/$command" <<'EOF'
args=("$@")
if [ "$command" = git ] && [ "${1:-}" = -C ]; then shift 2; fi
case "$FAULT:$command:${1:-}" in
  status:git:status|branch:git:branch|stage:git:add|delete:git:rm|prepare:mkdir:*|remove:rm:*|copy:cp:*)
    echo attempted >> "$FAULT_MARKER"
    echo private-recovery-canary@example.invalid >&2
    exit 71 ;;
esac
case "$command" in
  git) exec "$REAL_GIT" "${args[@]}" ;;
  mkdir) exec "$REAL_MKDIR" "${args[@]}" ;;
  rm) exec "$REAL_RM" "${args[@]}" ;;
  cp) exec "$REAL_CP" "${args[@]}" ;;
esac
EOF
  chmod +x "$TMP_ROOT/fault-bin/$command"
done
for stage in status branch prepare remove copy stage delete; do
  printf '' > "$FAULT_MARKER"
  selected=docs/kept.txt
  [ "$stage" != delete ] || selected=docs/remove-me.txt
  expected_status=71
  case "$stage" in status|branch) expected_status=2 ;; esac
  if failure="$(cd "$REPO" && PATH="$TMP_ROOT/fault-bin:$PATH" FAULT="$stage" \
    bash scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh \
    --session-log "$SESSION_LOG" --source-worktree "$REPO" -- "$selected" 2>&1)"; then
    fail "$stage failure reported successful recovery"
  else
    [ "$?" -eq "$expected_status" ] || fail "$stage lost failure status"
  fi
  [[ "$failure" == *recovery-*-failed* && "$failure" != *private-recovery-canary* && "$failure" != *Imported* ]] || fail "$stage safe reason lost"
  [ "$(wc -l < "$FAULT_MARKER")" -eq 1 ] || fail "failed operation replayed"
  case "$stage" in
    status|branch) assert_file_equals "$WORKTREE_PATH/docs/kept.txt" base ;;
    *) [[ "$failure" == *effect=unknown* ]] || fail "mutation effect was guessed" ;;
  esac
  # Restore only this disposable fixture's known original content after a
  # deliberately failed copy/stage; the real worktree is never involved.
  printf 'base\n' > "$WORKTREE_PATH/docs/kept.txt"
  [ -z "$(git -C "$WORKTREE_PATH" status --porcelain)" ] || fail "fixture restoration incomplete"
done

(
  cd "$REPO"
  AGENTIC_CHAT_WORKTREE_ROOT="$WORKTREE_ROOT" \
    bash scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh \
      --session-log "$SESSION_LOG" \
      --source-worktree "$REPO" \
      -- docs/kept.txt docs/remove-me.txt docs/new-dir
)

assert_file_equals "$WORKTREE_PATH/docs/kept.txt" "changed in active"
assert_file_equals "$WORKTREE_PATH/docs/new-dir/new.txt" "new file"

if [ -e "$WORKTREE_PATH/docs/remove-me.txt" ]; then
  fail "deleted active path still exists in chat-owned worktree"
fi

if ! git -C "$WORKTREE_PATH" diff --cached --name-only | grep -qx 'docs/kept.txt'; then
  fail "changed file was not staged"
fi

if ! git -C "$WORKTREE_PATH" diff --cached --name-only | grep -qx 'docs/remove-me.txt'; then
  fail "deleted file was not staged"
fi

if ! git -C "$WORKTREE_PATH" diff --cached --name-only | grep -qx 'docs/new-dir/new.txt'; then
  fail "new file was not staged"
fi

set +e
(
  cd "$REPO"
  bash scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh \
    --session-log "$SESSION_LOG" \
    --source-worktree "$REPO" \
    -- /absolute/path
) > "$TMP_ROOT/unsafe.out" 2> "$TMP_ROOT/unsafe.err"
UNSAFE_STATUS="$?"
set -e

if [ "$UNSAFE_STATUS" -eq 0 ]; then
  fail "unsafe absolute path was not rejected"
fi

if ! grep -q "path must be a repository-relative path" "$TMP_ROOT/unsafe.err"; then
  fail "unsafe path rejection message was not emitted"
fi

echo "import active paths recovery smoke test passed."
