#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/chat-worktree-session-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init --quiet --initial-branch=main

mkdir -p \
  "$REPO/scripts/shared/chat/request-initialization" \
  "$REPO/scripts/shared/git"

cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" "$REPO/scripts/shared/chat/session-log-paths.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/chat-worktree-paths.sh" "$REPO/scripts/shared/chat/chat-worktree-paths.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/ensure-chat-worktree.sh" "$REPO/scripts/shared/chat/ensure-chat-worktree.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/request-initialization/classify-task.sh" "$REPO/scripts/shared/chat/request-initialization/classify-task.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/request-initialization/start-chat-session.sh" "$REPO/scripts/shared/chat/request-initialization/start-chat-session.sh"
cp "$SOURCE_ROOT/scripts/shared/git/cleanup-empty-chat-branches.sh" "$REPO/scripts/shared/git/cleanup-empty-chat-branches.sh"
chmod +x "$REPO"/scripts/shared/chat/*.sh "$REPO"/scripts/shared/chat/request-initialization/*.sh "$REPO"/scripts/shared/git/*.sh

printf 'base\n' > "$REPO/README.md"
git -C "$REPO" add README.md scripts
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'

AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/worktrees" \
CHAT_CLEANUP_EMPTY_BRANCHES=skip \
CHAT_COPY_PROMPT=skip \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/shared/chat/request-initialization/start-chat-session.sh "test chat worktree session" \
    >/tmp/chat-worktree-session.out

root_branch="$(git -C "$REPO" branch --show-current)"
if [ "$root_branch" != "main" ]; then
  fail "root branch changed to $root_branch"
fi

chat_branch="$(git -C "$REPO" branch --format='%(refname:short)' | grep '^chat/' | head -n 1)"
if [ -z "$chat_branch" ]; then
  fail "chat branch was not created"
fi

worktree_path="$(
  git -C "$REPO" worktree list --porcelain \
    | awk -v branch="refs/heads/${chat_branch}" '
      /^worktree / { path = substr($0, 10) }
      /^branch / && substr($0, 8) == branch { print path }
    '
)"

if [ -z "$worktree_path" ] || [ "$worktree_path" = "$REPO" ]; then
  fail "chat branch does not have a separate worktree"
fi

if [ -n "$(git -C "$REPO" diff --cached --name-only)" ]; then
  fail "root worktree has staged changes"
fi

if ! git -C "$worktree_path" diff --cached --name-only | grep -q '^commitLogs/'; then
  fail "chat worktree did not stage the session log"
fi

session_log="$(git -C "$worktree_path" diff --cached --name-only | grep '^commitLogs/.*/README.md$' | head -n 1)"
if [ -z "$session_log" ]; then
  fail "could not find staged session log"
fi

layer="$(sed -n '/<!-- agentic-session/,/-->/s/^layer: //p' "$worktree_path/$session_log" | head -n 1)"
workflow="$(sed -n '/<!-- agentic-session/,/-->/s/^workflow: //p' "$worktree_path/$session_log" | head -n 1)"

if [ "$layer" != "chat" ]; then
  fail "chat startup did not classify the session as chat layer: ${layer:-missing}"
fi

if [ "$workflow" != ".agentic/00.chat/workflows/chat-start.md" ]; then
  fail "chat startup did not use the 00.chat workflow: ${workflow:-missing}"
fi

FAKE_BIN="$TMP_ROOT/fake-bin"
mkdir -p "$FAKE_BIN"
cat > "$FAKE_BIN/clip.exe" <<'EOF'
#!/usr/bin/env bash
cat >/dev/null
exit 1
EOF
chmod +x "$FAKE_BIN/clip.exe"

AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/worktrees" \
CHAT_CLEANUP_EMPTY_BRANCHES=skip \
CHAT_COPY_PROMPT=copy \
PATH="$FAKE_BIN:$PATH" \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/shared/chat/request-initialization/start-chat-session.sh "test clipboard fallback session" \
    >"$TMP_ROOT/chat-worktree-session-clipboard.out" 2>&1

if ! grep -q 'WARNING: Clipboard copy via clip.exe failed; printing prompt instead.' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "clipboard failure did not warn before falling back"
fi

if ! grep -q 'Paste this into Codex / Claude / Mistral:' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "clipboard failure did not print the first prompt"
fi

echo "chat worktree session smoke test passed."
