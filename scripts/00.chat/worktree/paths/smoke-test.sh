#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.worktree.paths.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: worktree
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Verify persistent chat worktree defaults and legacy registration handling.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.worktree.paths.lib
#     path: scripts/00.chat/worktree/paths/lib.sh
#   effects:
#   - branches
#   - worktrees
#   - writes-files

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/persistent-chat-worktree-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

copy_harness() {
  local repo="$1"

  mkdir -p \
    "$repo/scripts/00.chat/git/cleanup-empty-chat-branches" \
    "$repo/scripts/00.chat/session-log/paths" \
    "$repo/scripts/00.chat/startup/start-chat-session" \
    "$repo/scripts/00.chat/worktree/check-write-location" \
    "$repo/scripts/00.chat/worktree/ensure-chat-worktree" \
    "$repo/scripts/00.chat/worktree/open-window" \
    "$repo/scripts/00.chat/worktree/paths"

  cp "$SOURCE_ROOT/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "$repo/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$repo/scripts/00.chat/session-log/paths/lib.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/startup/start-chat-session/script.sh" "$repo/scripts/00.chat/startup/start-chat-session/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/worktree/check-write-location/script.sh" "$repo/scripts/00.chat/worktree/check-write-location/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/worktree/ensure-chat-worktree/script.sh" "$repo/scripts/00.chat/worktree/ensure-chat-worktree/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/worktree/open-window/script.sh" "$repo/scripts/00.chat/worktree/open-window/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" "$repo/scripts/00.chat/worktree/paths/lib.sh"
}

init_repo() {
  local repo="$1"

  mkdir -p "$repo"
  copy_harness "$repo"
  git -C "$repo" init -q -b main
  git -C "$repo" config user.name "Smoke Test"
  git -C "$repo" config user.email "smoke@example.invalid"
  printf 'base\n' > "$repo/README.md"
  git -C "$repo" add README.md scripts
  git -C "$repo" commit -q -m "base"
}

single_chat_branch() {
  git -C "$1" branch --format='%(refname:short)' | awk '/^chat\// { print; exit }'
}

registered_worktree() {
  local repo="$1"
  local branch="$2"

  git -C "$repo" worktree list --porcelain \
    | awk -v branch="refs/heads/${branch}" '
        /^worktree / { path = substr($0, 10) }
        /^branch / && substr($0, 8) == branch { print path }
      '
}

start_chat() {
  local repo="$1"
  local home_root="$2"
  local task="$3"

  env -u AGENTIC_CHAT_WORKTREE_ROOT \
    HOME="$home_root" \
    CHAT_CLEANUP_EMPTY_BRANCHES=skip \
    CHAT_COPY_PROMPT=skip \
    CHAT_OPEN_WORKTREE_WINDOW=skip \
    bash -c 'cd "$1" && bash scripts/00.chat/startup/start-chat-session/script.sh "$2"' sh "$repo" "$task"
}

repo="$TMP_ROOT/default/repo"
home_root="$TMP_ROOT/default-home"
init_repo "$repo"
start_chat "$repo" "$home_root" "persistent default"
branch="$(single_chat_branch "$repo")"
worktree="$(registered_worktree "$repo" "$branch")"
case "$worktree" in
  "$home_root/projects/.chat-worktrees/repo-"*/chat_*) ;;
  *) fail "default worktree is not under the persistent root: $worktree" ;;
esac
if printf '%s' "$worktree" | grep -q '^/tmp/agentic-chat-worktrees/'; then
  fail "default worktree still uses /tmp"
fi
session_log="$(find "$worktree/commitLogs" -name README.md -type f | head -n 1)"
ensure_result="$(env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$home_root" bash -c 'cd "$1" && bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$2"' sh "$repo" "$session_log")"
[ "$ensure_result" = "$worktree" ] || fail "ensure did not reuse the persistent worktree"
check_result="$(env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$home_root" bash -c 'cd "$1" && bash scripts/00.chat/worktree/check-write-location/script.sh' sh "$worktree")"
[ "$check_result" = "chat-worktree" ] || fail "write-location did not validate the persistent worktree"

repo="$TMP_ROOT/legacy/repo"
init_repo "$repo"
session="2026-10-05-legacy-tmp-worktree"
branch="chat/$session"
legacy_worktree="$TMP_ROOT/legacy-tmp/worktrees/chat_legacy"
git -C "$repo" branch "$branch"
git -C "$repo" worktree add -q "$legacy_worktree" "$branch"
legacy_log="$legacy_worktree/commitLogs/2026/oct/05/$session/README.md"
mkdir -p "$(dirname "$legacy_log")"
cat > "$legacy_log" <<EOF
<!-- agentic-session
id: $session
branch: $branch
worktree: $legacy_worktree
-->
EOF
printf 'preserve this uncommitted content\n' > "$legacy_worktree/uncommitted.txt"
ensure_result="$(env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$TMP_ROOT/legacy-home" bash -c 'cd "$1" && bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$2"' sh "$repo" "$legacy_log")"
[ "$ensure_result" = "$legacy_worktree" ] || fail "ensure did not reuse legacy /tmp worktree"
grep -qx 'preserve this uncommitted content' "$legacy_worktree/uncommitted.txt" || fail "legacy uncommitted content changed"
check_result="$(env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$TMP_ROOT/legacy-home" bash -c 'cd "$1" && bash scripts/00.chat/worktree/check-write-location/script.sh' sh "$legacy_worktree")"
[ "$check_result" = "chat-worktree" ] || fail "write-location rejected legacy registered worktree"

repo="$TMP_ROOT/override/repo"
init_repo "$repo"
mkdir -p "$repo/.agentic"
override_root="$TMP_ROOT/override root with spaces"
printf 'AGENTIC_CHAT_WORKTREE_ROOT="%s"\n' "$override_root" > "$repo/.agentic/env.local"
start_chat "$repo" "$TMP_ROOT/override-home" "override with spaces"
branch="$(single_chat_branch "$repo")"
worktree="$(registered_worktree "$repo" "$branch")"
case "$worktree" in "$override_root"/*) ;; *) fail "env.local override with spaces was ignored: $worktree" ;; esac
session_log="$(find "$worktree/commitLogs" -name README.md -type f | head -n 1)"
ensure_result="$(env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$TMP_ROOT/override-home" bash -c 'cd "$1" && bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$2"' sh "$repo" "$session_log")"
[ "$ensure_result" = "$worktree" ] || fail "fresh-shell ensure did not load env.local override"
check_result="$(env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$TMP_ROOT/override-home" bash -c 'cd "$1" && bash scripts/00.chat/worktree/check-write-location/script.sh' sh "$worktree")"
[ "$check_result" = "chat-worktree" ] || fail "fresh-shell write-location did not load env.local override"

repo_one="$TMP_ROOT/twins/one/same"
repo_two="$TMP_ROOT/twins/two/same"
home_root="$TMP_ROOT/twins-home"
init_repo "$repo_one"
init_repo "$repo_two"
start_chat "$repo_one" "$home_root" "same name one"
start_chat "$repo_two" "$home_root" "same name two"
worktree_one="$(registered_worktree "$repo_one" "$(single_chat_branch "$repo_one")")"
worktree_two="$(registered_worktree "$repo_two" "$(single_chat_branch "$repo_two")")"
[ "$worktree_one" != "$worktree_two" ] || fail "repositories with the same name share a worktree path"

wrong_repo="$TMP_ROOT/wrong-repository/repo"
init_repo "$wrong_repo"
if env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$TMP_ROOT/wrong-home" bash -c 'cd "$1" && bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$2"' sh "$wrong_repo" "$legacy_log" >"$TMP_ROOT/wrong-repo.out" 2>&1; then
  fail "ensure accepted a session log from another repository"
fi
grep -q 'belongs to a different repository' "$TMP_ROOT/wrong-repo.out" || fail "wrong repository failure was unclear"

repo="$TMP_ROOT/wrong-branch/repo"
init_repo "$repo"
branch_a="chat/2026-10-05-wrong-branch-a"
branch_b="chat/2026-10-05-wrong-branch-b"
worktree_a="$TMP_ROOT/wrong-branch-a"
worktree_b="$TMP_ROOT/wrong-branch-b"
git -C "$repo" branch "$branch_a"
git -C "$repo" branch "$branch_b"
git -C "$repo" worktree add -q "$worktree_a" "$branch_a"
git -C "$repo" worktree add -q "$worktree_b" "$branch_b"
wrong_branch_log="$repo/wrong-branch-session.md"
cat > "$wrong_branch_log" <<EOF
<!-- agentic-session
id: 2026-10-05-wrong-branch-b
branch: $branch_b
worktree: $worktree_a
-->
EOF
if env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$TMP_ROOT/wrong-branch-home" bash -c 'cd "$1" && bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$2"' sh "$repo" "$wrong_branch_log" >"$TMP_ROOT/wrong-branch.out" 2>&1; then
  fail "ensure accepted mismatched branch worktree metadata"
fi
grep -q 'does not match session metadata' "$TMP_ROOT/wrong-branch.out" || fail "wrong branch failure was unclear"

repo="$TMP_ROOT/unwritable/repo"
init_repo "$repo"
blocked_root="$TMP_ROOT/not-a-directory"
printf 'not a directory\n' > "$blocked_root"
if AGENTIC_CHAT_WORKTREE_ROOT="$blocked_root" HOME="$TMP_ROOT/unwritable-home" CHAT_CLEANUP_EMPTY_BRANCHES=skip CHAT_COPY_PROMPT=skip CHAT_OPEN_WORKTREE_WINDOW=skip bash -c 'cd "$1" && bash scripts/00.chat/startup/start-chat-session/script.sh "unwritable destination"' sh "$repo" >"$TMP_ROOT/unwritable.out" 2>&1; then
  fail "startup accepted an unusable persistent destination"
fi
grep -q 'cannot create persistent chat worktree root' "$TMP_ROOT/unwritable.out" || fail "unwritable destination failure was unclear"
if [ -n "$(git -C "$repo" branch --format='%(refname:short)' | grep '^chat/' || true)" ]; then
  fail "startup created a chat branch after persistent destination preflight failed"
fi

echo "persistent chat worktree smoke test passed."
