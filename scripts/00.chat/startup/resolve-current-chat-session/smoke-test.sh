#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.startup.resolve-current-chat-session.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: startup
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test startup resolution for missing and existing chat sessions.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.startup.resolve-current-chat-session.readme
#     path: scripts/00.chat/startup/resolve-current-chat-session/README.md
#   effects:
#   - writes-files
#   - branches
#   - worktrees
#   - commits

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/resolve-current-chat-session-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init --quiet --initial-branch=main

mkdir -p \
  "$REPO/scripts/00.chat/classification/classify-task" \
  "$REPO/scripts/00.chat/command/dispatcher" \
  "$REPO/scripts/00.chat/command/new" \
  "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/session-log/read-current-chat-log" \
  "$REPO/scripts/00.chat/startup/auto-start-missing-session" \
  "$REPO/scripts/00.chat/startup/resolve-current-chat-session" \
  "$REPO/scripts/00.chat/startup/start-chat-session" \
  "$REPO/scripts/00.chat/startup/start-new-chat" \
  "$REPO/scripts/00.chat/worktree/ensure-chat-worktree" \
  "$REPO/scripts/00.chat/worktree/open-window" \
  "$REPO/scripts/00.chat/worktree/paths"

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" "$REPO/scripts/00.chat/worktree/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/read-current-chat-log/script.sh" "$REPO/scripts/00.chat/session-log/read-current-chat-log/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/resolve-current-chat-session/script.sh" "$REPO/scripts/00.chat/startup/resolve-current-chat-session/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/auto-start-missing-session/script.sh" "$REPO/scripts/00.chat/startup/auto-start-missing-session/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/command/dispatcher/script.sh" "$REPO/scripts/00.chat/command/dispatcher/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/command/new/script.sh" "$REPO/scripts/00.chat/command/new/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/start-new-chat/script.sh" "$REPO/scripts/00.chat/startup/start-new-chat/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/start-chat-session/script.sh" "$REPO/scripts/00.chat/startup/start-chat-session/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/classification/classify-task/script.sh" "$REPO/scripts/00.chat/classification/classify-task/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/ensure-chat-worktree/script.sh" "$REPO/scripts/00.chat/worktree/ensure-chat-worktree/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/open-window/script.sh" "$REPO/scripts/00.chat/worktree/open-window/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"
chmod +x \
  "$REPO/scripts/00.chat/session-log/read-current-chat-log/script.sh" \
  "$REPO/scripts/00.chat/startup/resolve-current-chat-session/script.sh" \
  "$REPO/scripts/00.chat/startup/auto-start-missing-session/script.sh" \
  "$REPO/scripts/00.chat/command/dispatcher/script.sh" \
  "$REPO/scripts/00.chat/command/new/script.sh" \
  "$REPO/scripts/00.chat/startup/start-new-chat/script.sh" \
  "$REPO/scripts/00.chat/startup/start-chat-session/script.sh" \
  "$REPO/scripts/00.chat/classification/classify-task/script.sh" \
  "$REPO/scripts/00.chat/worktree/ensure-chat-worktree/script.sh" \
  "$REPO/scripts/00.chat/worktree/open-window/script.sh" \
  "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"

printf 'base\n' > "$REPO/README.md"
git -C "$REPO" add README.md scripts
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'

AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/worktrees" \
CHAT_CLEANUP_EMPTY_BRANCHES=skip \
CHAT_COPY_PROMPT=skip \
CHAT_OPEN_WORKTREE_WINDOW=skip \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/00.chat/startup/resolve-current-chat-session/script.sh "use the existing chat start process" \
    >"$TMP_ROOT/resolve-missing.out"

grep -q 'Created branch: chat/' "$TMP_ROOT/resolve-missing.out" \
  || fail "resolver did not auto-start a missing root-main session"
grep -q 'Task: use the existing chat start process' "$TMP_ROOT/resolve-missing.out" \
  || fail "resolver did not pass the opening prompt to auto-start"

chat_branch="$(git -C "$REPO" branch --format='%(refname:short)' | grep '^chat/' | head -n 1)"
worktree_path="$(
  git -C "$REPO" worktree list --porcelain \
    | awk -v branch="refs/heads/${chat_branch}" '
      /^worktree / { path = substr($0, 10) }
      /^branch / && substr($0, 8) == branch { print path }
    '
)"

if [ -z "$worktree_path" ]; then
  fail "resolver-created chat branch did not have a worktree"
fi

branch_count_before="$(git -C "$REPO" branch --format='%(refname:short)' | grep -c '^chat/')"

bash -c 'cd "$1" && shift && "$@"' sh "$worktree_path" \
  bash scripts/00.chat/startup/resolve-current-chat-session/script.sh "ignored because metadata exists" \
  >"$TMP_ROOT/resolve-existing.out"

grep -q '^task: use the existing chat start process$' "$TMP_ROOT/resolve-existing.out" \
  || fail "resolver did not return existing session metadata"
grep -q '^workflow: .agentic/00.chat/workflows/chat-start.md$' "$TMP_ROOT/resolve-existing.out" \
  || fail "resolver existing-session metadata did not include workflow"

branch_count_after="$(git -C "$REPO" branch --format='%(refname:short)' | grep -c '^chat/')"
if [ "$branch_count_after" != "$branch_count_before" ]; then
  fail "resolver created another chat branch despite existing metadata"
fi

echo "resolve current chat session smoke test passed."
