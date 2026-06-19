#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test local-main merge readiness verifier classifications.
#   domain: local-merge
#   portability: llm-workbench-validation
#   used_by:
#     - .agentic/00.chat/workflows/chat-promote-to-main.md
#     - scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh
#   effects: writes-files, branches, worktrees, commits

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/local-convergence-verifier-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

copy_verifier_scripts() {
  local repo="$1"

  mkdir -p "$repo/scripts/shared/git" "$repo/scripts/shared/chat" "$repo/scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main" "$repo/scripts/00.chat/session-log/paths" "$repo/scripts/00.chat/worktree/paths"
  cp "$SOURCE_ROOT/scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh" "$repo/scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" "$repo/scripts/00.chat/worktree/paths/lib.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$repo/scripts/00.chat/session-log/paths/lib.sh"
}

init_repo() {
  local name="$1"
  local repo="$TMP_ROOT/$name/repo"

  mkdir -p "$repo"
  copy_verifier_scripts "$repo"

  git -C "$repo" init -q -b main
  git -C "$repo" config user.name "Smoke Test"
  git -C "$repo" config user.email "smoke@example.invalid"

  printf 'base\n' > "$repo/base.txt"
  git -C "$repo" add base.txt scripts
  git -C "$repo" commit -q -m "initial"

  printf '%s\n' "$repo"
}

canonical_worktree_path() {
  local repo="$1"
  local branch="$2"

  (
    cd "$repo"
    # shellcheck source=../worktree/paths/lib.sh
    source scripts/00.chat/worktree/paths/lib.sh
    chat_worktree_path_for_branch "$repo" "$branch"
  )
}

write_session_log() {
  local repo="$1"
  local session="$2"
  local branch="$3"
  local worktree="$4"
  local latest_sha="$5"
  local log_path="$repo/commitLogs/2026/jun/16/$session/README.md"

  mkdir -p "$(dirname "$log_path")"
  cat > "$log_path" <<EOF
# Chat Session: $session

<!-- agentic-session
id: $session
task: smoke test local convergence
branch: $branch
worktree: $worktree
layer: shared
mode: implementation
workflow: .agentic/shared/workflows/change-shared-process.md
status: ready
latest_commit_sha: $latest_sha
-->

## Commits

- Commit: \`$latest_sha\`
EOF
}

create_chat_branch_with_log() {
  local repo="$1"
  local session="$2"
  local latest_sha="${3:-}"
  local branch="chat/$session"
  local worktree
  local task_sha

  worktree="$(canonical_worktree_path "$repo" "$branch")"

  git -C "$repo" switch -q -c "$branch"
  printf 'work\n' > "$repo/work-$session.txt"
  git -C "$repo" add "work-$session.txt"
  git -C "$repo" commit -q -m "task work"
  task_sha="$(git -C "$repo" rev-parse HEAD)"

  if [ -z "$latest_sha" ]; then
    latest_sha="$task_sha"
  fi

  write_session_log "$repo" "$session" "$branch" "$worktree" "$latest_sha"
  git -C "$repo" add "commitLogs/2026/jun/16/$session/README.md"
  git -C "$repo" commit -q -m "record session log"
  git -C "$repo" switch -q main
  mkdir -p "${worktree%/*}"
  git -C "$repo" worktree add -q "$worktree" "$branch"
}

run_expect_state() {
  local repo="$1"
  local branch="$2"
  local state="$3"
  local should_succeed="$4"
  local out="$TMP_ROOT/output"
  local err="$TMP_ROOT/error"

  if [ "$should_succeed" = "yes" ]; then
    (
      cd "$repo"
      bash scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh "$branch"
    ) > "$out" 2> "$err" || {
      cat "$out" >&2
      cat "$err" >&2
      fail "expected verifier success for $state"
    }
  else
    if (
      cd "$repo"
      bash scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh "$branch"
    ) > "$out" 2> "$err"; then
      cat "$out" >&2
      fail "expected verifier failure for $state"
    fi
  fi

  if ! grep -q "State: $state" "$out"; then
    cat "$out" >&2
    cat "$err" >&2
    fail "expected state $state"
  fi
}

repo="$(init_repo eligible)"
session="2026-06-16-22-32-eligible"
branch="chat/$session"
create_chat_branch_with_log "$repo" "$session"
run_expect_state "$repo" "$branch" "eligible" "yes"

repo="$(init_repo renamed-log)"
session="2026-06-16-22-32-renamed-log"
branch="chat/$session"
create_chat_branch_with_log "$repo" "$session"
worktree="$(canonical_worktree_path "$repo" "$branch")"
git -C "$worktree" mv \
  "commitLogs/2026/jun/16/$session" \
  "commitLogs/2026/jun/16/2026-06-16-22-32-short-log-name"
git -C "$worktree" commit -q -m "rename session log folder"
run_expect_state "$repo" "$branch" "eligible" "yes"

repo="$(init_repo behind)"
session="2026-06-16-22-33-behind"
branch="chat/$session"
worktree="$(canonical_worktree_path "$repo" "$branch")"
write_session_log "$repo" "$session" "$branch" "$worktree" "$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" add "commitLogs/2026/jun/16/$session/README.md"
git -C "$repo" commit -q -m "record shared session log"
git -C "$repo" branch "$branch"
printf 'main update\n' > "$repo/main-update.txt"
git -C "$repo" add main-update.txt
git -C "$repo" commit -q -m "main update"
mkdir -p "${worktree%/*}"
git -C "$repo" worktree add -q "$worktree" "$branch"
run_expect_state "$repo" "$branch" "blocked-behind" "no"

repo="$(init_repo diverged)"
session="2026-06-16-22-34-diverged"
branch="chat/$session"
create_chat_branch_with_log "$repo" "$session"
printf 'main update\n' > "$repo/main-update.txt"
git -C "$repo" add main-update.txt
git -C "$repo" commit -q -m "main update"
run_expect_state "$repo" "$branch" "blocked-diverged" "no"

repo="$(init_repo dirty-chat)"
session="2026-06-16-22-35-dirty-chat"
branch="chat/$session"
create_chat_branch_with_log "$repo" "$session"
worktree="$(canonical_worktree_path "$repo" "$branch")"
printf 'dirty\n' > "$worktree/dirty.txt"
run_expect_state "$repo" "$branch" "blocked-dirty-chat-worktree" "no"

repo="$(init_repo missing-log)"
session="2026-06-16-22-36-missing-log"
branch="chat/$session"
git -C "$repo" branch "$branch"
run_expect_state "$repo" "$branch" "blocked-missing-log" "no"

repo="$(init_repo missing-worktree)"
session="2026-06-16-22-37-missing-worktree"
branch="chat/$session"
create_chat_branch_with_log "$repo" "$session"
worktree="$(canonical_worktree_path "$repo" "$branch")"
git -C "$repo" worktree remove "$worktree" >/dev/null
run_expect_state "$repo" "$branch" "blocked-missing-worktree" "no"

repo="$(init_repo log-mismatch)"
session="2026-06-16-22-38-log-mismatch"
branch="chat/$session"
create_chat_branch_with_log "$repo" "$session" "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
run_expect_state "$repo" "$branch" "blocked-log-head-mismatch" "no"

echo "local merge readiness verifier smoke test passed."
