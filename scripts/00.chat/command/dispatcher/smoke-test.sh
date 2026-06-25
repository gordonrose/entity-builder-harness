#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.command.dispatcher.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test the chat command dispatcher and chat subcommands.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.commands.readme
#     path: .agentic/00.chat/commands/README.md
#   - id: chat.workflows.bootstrap-chat-workbench-repo
#     path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   - id: chat.script.command.dispatcher.readme
#     path: scripts/00.chat/command/dispatcher/README.md
#   effects:
#   - branches
#   - worktrees
#   - writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/chat-command-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init --quiet --initial-branch=main

mkdir -p \
  "$REPO/scripts/00.chat/closeout/build-closeout-prompt" \
  "$REPO/scripts/00.chat/command/close" \
  "$REPO/scripts/00.chat/command/dispatcher" \
  "$REPO/scripts/00.chat/command/new" \
  "$REPO/scripts/00.chat/command/open-window" \
  "$REPO/scripts/00.chat/classification/classify-task" \
  "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/startup/auto-start-missing-session" \
  "$REPO/scripts/00.chat/startup/start-chat-session" \
  "$REPO/scripts/00.chat/startup/start-new-chat" \
  "$REPO/scripts/00.chat/worktree/ensure-chat-worktree" \
  "$REPO/scripts/00.chat/worktree/open-window" \
  "$REPO/scripts/00.chat/worktree/paths"

cp "$SOURCE_ROOT/scripts/00.chat/command/dispatcher/script.sh" "$REPO/scripts/00.chat/command/dispatcher/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/command/new/script.sh" "$REPO/scripts/00.chat/command/new/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/command/close/script.sh" "$REPO/scripts/00.chat/command/close/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/command/open-window/script.sh" "$REPO/scripts/00.chat/command/open-window/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" "$REPO/scripts/00.chat/worktree/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/ensure-chat-worktree/script.sh" "$REPO/scripts/00.chat/worktree/ensure-chat-worktree/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/open-window/script.sh" "$REPO/scripts/00.chat/worktree/open-window/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/start-chat-session/script.sh" "$REPO/scripts/00.chat/startup/start-chat-session/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/start-new-chat/script.sh" "$REPO/scripts/00.chat/startup/start-new-chat/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/closeout/build-closeout-prompt/script.sh" "$REPO/scripts/00.chat/closeout/build-closeout-prompt/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/classification/classify-task/script.sh" "$REPO/scripts/00.chat/classification/classify-task/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/auto-start-missing-session/script.sh" "$REPO/scripts/00.chat/startup/auto-start-missing-session/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"
chmod +x "$REPO/scripts/00.chat/closeout/build-closeout-prompt/script.sh" "$REPO/scripts/00.chat/command/dispatcher/script.sh" "$REPO/scripts/00.chat/command/new/script.sh" "$REPO/scripts/00.chat/command/close/script.sh" "$REPO/scripts/00.chat/command/open-window/script.sh" "$REPO/scripts/00.chat/classification/classify-task/script.sh" "$REPO/scripts/00.chat/startup/auto-start-missing-session/script.sh" "$REPO/scripts/00.chat/startup/start-chat-session/script.sh" "$REPO/scripts/00.chat/startup/start-new-chat/script.sh" "$REPO/scripts/00.chat/worktree/ensure-chat-worktree/script.sh" "$REPO/scripts/00.chat/worktree/open-window/script.sh" "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"

printf 'base\n' > "$REPO/README.md"
git -C "$REPO" add README.md scripts
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'

CHAT_COPY_PROMPT=skip \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/00.chat/command/dispatcher/script.sh list \
    >"$TMP_ROOT/list.out"

grep -q '^  new$' "$TMP_ROOT/list.out" || fail "new command was not listed"
grep -q '^  close$' "$TMP_ROOT/list.out" || fail "close command was not listed"
grep -q '^  open-window$' "$TMP_ROOT/list.out" || fail "open-window command was not listed"

AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/worktrees" \
CHAT_CLEANUP_EMPTY_BRANCHES=skip \
CHAT_COPY_PROMPT=skip \
CHAT_OPEN_WORKTREE_WINDOW=skip \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/00.chat/command/dispatcher/script.sh new "test command-created session" \
    >"$TMP_ROOT/new.out"

grep -q 'Created branch: chat/' "$TMP_ROOT/new.out" || fail "new command did not create a chat branch"
grep -q 'Paste this into Codex / Claude / Mistral:' "$TMP_ROOT/new.out" || fail "new command did not print first prompt"

AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/worktrees" \
CHAT_CLEANUP_EMPTY_BRANCHES=skip \
CHAT_COPY_PROMPT=skip \
CHAT_OPEN_WORKTREE_WINDOW=skip \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/00.chat/startup/auto-start-missing-session/script.sh "test opening prompt session" \
    >"$TMP_ROOT/auto-start.out"

grep -q 'Created branch: chat/' "$TMP_ROOT/auto-start.out" || fail "auto-start did not create a chat branch"
grep -q 'Task: test opening prompt session' "$TMP_ROOT/auto-start.out" || fail "auto-start did not use opening prompt as task"

if CHAT_COPY_PROMPT=skip \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/00.chat/startup/auto-start-missing-session/script.sh new \
    >"$TMP_ROOT/bare-new.out"; then
  fail "bare new auto-start unexpectedly succeeded"
fi

grep -Fxq 'What should the new chat be about?' "$TMP_ROOT/bare-new.out" || fail "bare new did not ask for a task summary"

chat_branch="$(git -C "$REPO" branch --format='%(refname:short)' | grep '^chat/' | head -n 1)"
worktree_path="$(
  git -C "$REPO" worktree list --porcelain \
    | awk -v branch="refs/heads/${chat_branch}" '
      /^worktree / { path = substr($0, 10) }
      /^branch / && substr($0, 8) == branch { print path }
    '
)"

if [ -z "$worktree_path" ]; then
  fail "new command did not create a chat worktree"
fi

FAKE_BIN="$TMP_ROOT/fake-bin"
mkdir -p "$FAKE_BIN"
cat > "$FAKE_BIN/code" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" > "$CODE_ARGS_FILE"
EOF
chmod +x "$FAKE_BIN/code"

CODE_ARGS_FILE="$TMP_ROOT/code-args.out" \
PATH="$FAKE_BIN:$PATH" \
  bash -c 'cd "$1" && shift && "$@"' sh "$worktree_path" \
    bash scripts/00.chat/command/dispatcher/script.sh open window \
    >"$TMP_ROOT/open-window.out"

grep -q "Opened VS Code window: $worktree_path" "$TMP_ROOT/open-window.out" \
  || fail "open window command did not report opened worktree"
grep -Fxq -- "--new-window $worktree_path" "$TMP_ROOT/code-args.out" \
  || fail "open window command did not call code with the chat worktree"

CHAT_COPY_PROMPT=skip \
  bash -c 'cd "$1" && shift && "$@"' sh "$worktree_path" \
    bash scripts/00.chat/command/dispatcher/script.sh close \
    >"$TMP_ROOT/close.out"

grep -q 'Workflow: .agentic/00.chat/workflows/chat-promote-to-main.md' "$TMP_ROOT/close.out" \
  || fail "close command did not route to promote workflow"
grep -q 'Ask for explicit approval before creating any task commit.' "$TMP_ROOT/close.out" \
  || fail "close command did not preserve commit approval boundary"
grep -q 'Do not push to origin unless I explicitly approve a separate push.' "$TMP_ROOT/close.out" \
  || fail "close command did not preserve push approval boundary"

echo "chat command smoke test passed."
