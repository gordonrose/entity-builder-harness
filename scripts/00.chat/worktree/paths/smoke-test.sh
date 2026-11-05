#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.worktree.paths.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-10-04"
#   updated_on: "2026-11-05"
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
    "$repo/scripts/00.chat/worktree/dirty-worktree-check" \
    "$repo/scripts/00.chat/worktree/ensure-chat-worktree" \
    "$repo/scripts/00.chat/worktree/open-window" \
    "$repo/scripts/00.chat/worktree/paths"

  cp "$SOURCE_ROOT/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "$repo/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$repo/scripts/00.chat/session-log/paths/lib.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/startup/start-chat-session/script.sh" "$repo/scripts/00.chat/startup/start-chat-session/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/worktree/check-write-location/script.sh" "$repo/scripts/00.chat/worktree/check-write-location/script.sh"
  cp "$SOURCE_ROOT/scripts/00.chat/worktree/dirty-worktree-check/script.sh" "$repo/scripts/00.chat/worktree/dirty-worktree-check/script.sh"
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

repo="$TMP_ROOT/ensure-create/repo"
home_root="$TMP_ROOT/ensure-create-home"
init_repo "$repo"
session="2026-10-05-ensure-create"
branch="chat/$session"
git -C "$repo" branch "$branch"
expected_worktree="$(env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$home_root" bash -c 'cd "$1" && source scripts/00.chat/worktree/paths/lib.sh && chat_worktree_path_for_branch "$1" "$2"' sh "$repo" "$branch")"
session_log="$repo/commitLogs/2026/oct/05/$session/README.md"
mkdir -p "$(dirname "$session_log")"
cat > "$session_log" <<EOF
<!-- agentic-session
id: $session
branch: $branch
worktree: $expected_worktree
-->
EOF
ensure_result="$(env -u AGENTIC_CHAT_WORKTREE_ROOT HOME="$home_root" bash -c 'cd "$1" && bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$2"' sh "$repo" "$session_log" 2>"$TMP_ROOT/ensure-create.err")"
[ "$ensure_result" = "$expected_worktree" ] || fail "ensure did not preserve its stdout path contract after creating a worktree"
grep -Fqx "Created worktree: $expected_worktree" "$TMP_ROOT/ensure-create.err" \
  || fail "ensure did not report creating the worktree"
grep -Fqx "  cd $expected_worktree" "$TMP_ROOT/ensure-create.err" \
  || fail "ensure did not provide the command to enter the created worktree"
grep -Fqx "  (cd $expected_worktree && npm run chat -- open-window)" "$TMP_ROOT/ensure-create.err" \
  || fail "ensure did not provide the command to open the created worktree"

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
grep -Fqx 'ERROR: startup-operation-failed; stage=root-create; effect=unknown; inspect before retry.' "$TMP_ROOT/unwritable.out" || fail "unwritable destination lost its bounded stage and effect"
if grep -Fq "$blocked_root" "$TMP_ROOT/unwritable.out"; then
  fail "unwritable destination exposed native path text"
fi
if [ -n "$(git -C "$repo" branch --format='%(refname:short)' | grep '^chat/' || true)" ]; then
  fail "startup created a chat branch after persistent destination preflight failed"
fi

REAL_GIT="$(command -v git)"
REAL_AWK="$(command -v awk)"
export REAL_GIT REAL_AWK
mkdir -p "$TMP_ROOT/fault-bin"
cat > "$TMP_ROOT/fault-bin/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
original=("$@")
if [ "${1:-}" = -C ]; then shift 2; fi
case "${FAULT:-}:$1:${2:-}" in
  root:rev-parse:--show-toplevel|branch:branch:--show-current|reference:show-ref:--verify)
    echo "private-registration-canary@example.invalid" >&2
    exit 128 ;;
esac
set -- "${original[@]}"
case "${FAULT:-}:$1:${2:-}" in
  dirty-status:status:*|dirty-unstaged:diff:--name-only|dirty-staged:diff:--cached|dirty-untracked:ls-files:*)
    echo "private-registration-canary@example.invalid" >&2
    exit 128 ;;
esac
if [ "${3:-}" = worktree ] && [ "${4:-}" = list ]; then
  count="$(<"$READ_COUNT")"
  count=$((count + 1))
  printf '%s\n' "$count" > "$READ_COUNT"
  if [ "$count" -eq "$FAIL_READ" ]; then
    echo "private-registration-canary@example.invalid" >&2
    exit 128
  fi
fi
if [ "${3:-}" = worktree ] && [ "${4:-}" = add ]; then
  echo mutation-attempted > "$MUTATION_MARKER"
  echo "private-registration-canary@example.invalid" >&2
  exit 99
fi
exec "$REAL_GIT" "$@"
EOF
chmod +x "$TMP_ROOT/fault-bin/git"
cat > "$TMP_ROOT/fault-bin/awk" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [ "${FAULT:-}" = metadata ] && [ "${2:-}" = key=branch ]; then
  "$REAL_AWK" "$@"
  echo "private-registration-canary@example.invalid" >&2
  exit 2
fi
exec "$REAL_AWK" "$@"
EOF
cat > "$TMP_ROOT/fault-bin/code" <<'EOF'
#!/usr/bin/env bash
echo opened > "$WINDOW_MARKER"
echo "private-registration-canary@example.invalid" >&2
exit 23
EOF
chmod +x "$TMP_ROOT/fault-bin/awk" "$TMP_ROOT/fault-bin/code"
for failed_read in 1 3; do
  printf '0\n' > "$TMP_ROOT/read-count"
  if fault_output="$(PATH="$TMP_ROOT/fault-bin:$PATH" READ_COUNT="$TMP_ROOT/read-count" FAIL_READ="$failed_read" MUTATION_MARKER="$TMP_ROOT/mutation" \
    bash -c 'cd "$1" && bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$2"' sh "$TMP_ROOT/legacy/repo" "$legacy_log" 2>&1)"; then
    fail "ensure accepted failed worktree enumeration $failed_read"
  fi
  [[ "$fault_output" == *worktree-registration-read-failed* ]] || fail "worktree read failure reason lost"
  [[ "$fault_output" != *private-registration-canary* ]] || fail "worktree native output leaked"
  [ ! -e "$TMP_ROOT/mutation" ] || fail "worktree read failure permitted creation"
done

# True absence remains different from a failed enumeration.
if absence_output="$(bash -c 'source "$1"; chat_worktree_registered_path_for_branch "$2" chat/nonexistent' sh \
  "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" "$TMP_ROOT/legacy/repo" 2>&1)"; then
  fail "unregistered branch unexpectedly found"
else
  [ "$?" -eq 1 ] || fail "honest absence no longer returns 1"
fi
[ -z "$absence_output" ] || fail "honest absence emitted an error"

for stage in status unstaged staged untracked; do
  if fault_output="$(cd "$legacy_worktree" && PATH="$TMP_ROOT/fault-bin:$PATH" FAULT="dirty-$stage" \
    bash scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping 2>&1)"; then
    fail "failed $stage observation reported a clean worktree"
  else
    [ "$?" -eq 2 ] || fail "failed $stage observation lost its unavailable exit status"
  fi
  [[ "$fault_output" == *"worktree-$stage-read-failed"* ]] || fail "$stage read reason lost"
  [[ "$fault_output" != *private-registration-canary* ]] || fail "native $stage failure leaked"
  [[ "$fault_output" != *clean* && "$fault_output" != *bookkeeping-only* ]] || fail "failed $stage read became an accepted state"
done

for capability in check-write-location ensure-chat-worktree open-window; do
  for stage in root branch metadata; do
    # ensure reads the current branch only after validating its metadata;
    # all of these faults precede creation or editor invocation.
    printf '0\n' > "$TMP_ROOT/read-count"
    args=()
    [ "$capability" != ensure-chat-worktree ] || args=("$legacy_log")
    if fault_output="$(cd "$legacy_worktree" && PATH="$TMP_ROOT/fault-bin:$PATH" FAULT="$stage" \
      READ_COUNT="$TMP_ROOT/read-count" FAIL_READ=0 MUTATION_MARKER="$TMP_ROOT/mutation" \
      WINDOW_MARKER="$TMP_ROOT/window" bash "scripts/00.chat/worktree/$capability/script.sh" "${args[@]}" 2>&1)"; then
      fail "$capability accepted failed $stage read"
    else
      [ "$?" -eq 2 ] || fail "$capability did not distinguish an unavailable $stage observation"
    fi
    [[ "$fault_output" == *read-failed* ]] || fail "$capability lost $stage read failure"
    [[ "$fault_output" != *private-registration-canary* ]] || fail "$capability leaked native $stage text"
    [[ "$fault_output" != *does\ not\ match* && "$fault_output" != *not\ a\ chat\ branch* ]] || fail "$capability misdiagnosed failed $stage read"
    [ ! -e "$TMP_ROOT/mutation" ] || fail "read failure permitted creation"
    [ ! -e "$TMP_ROOT/window" ] || fail "read failure permitted window launch"
  done
done

if fault_output="$(cd "$legacy_worktree" && PATH="$TMP_ROOT/fault-bin:$PATH" FAULT=reference \
  READ_COUNT="$TMP_ROOT/read-count" FAIL_READ=0 \
  bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$legacy_log" 2>&1)"; then
  fail "failed reference read was accepted"
else
  [ "$?" -eq 2 ] || fail "reference failure became branch absence"
fi
[[ "$fault_output" == *worktree-branch-reference-read-failed* && "$fault_output" != *private-registration-canary* ]] || fail "reference failure lost safe reason"

# Window launch is deliberately optional: failure is a safe warning, not success.
window_output="$(cd "$legacy_worktree" && PATH="$TMP_ROOT/fault-bin:$PATH" WINDOW_MARKER="$TMP_ROOT/window" \
  bash scripts/00.chat/worktree/open-window/script.sh 2>&1)"
[[ "$window_output" == *outcome\ is\ unconfirmed* && "$window_output" != *private-registration-canary* && "$window_output" != *Opened* ]] || fail "optional launch failure misreported"
[ -f "$TMP_ROOT/window" ] || fail "editor double was not invoked"

repo="$TMP_ROOT/create-failure/repo"
init_repo "$repo"
branch="chat/2026-11-05-create-failure"
git -C "$repo" branch "$branch"
planned="$(AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/create-failure-worktrees" bash -c \
  'source "$1"; chat_worktree_path_for_branch "$2" "$3"' sh \
  "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" "$repo" "$branch")"
creation_log="$repo/session.md"
printf '<!-- agentic-session\nbranch: %s\nworktree: %s\n-->\n' "$branch" "$planned" > "$creation_log"
printf '0\n' > "$TMP_ROOT/read-count"
if creation_output="$(cd "$repo" && AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/create-failure-worktrees" \
  PATH="$TMP_ROOT/fault-bin:$PATH" READ_COUNT="$TMP_ROOT/read-count" FAIL_READ=0 \
  MUTATION_MARKER="$TMP_ROOT/mutation" bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$creation_log" 2>&1)"; then
  fail "failed creation reported success"
else
  [ "$?" -eq 99 ] || fail "creation failure lost original exit status"
fi
[[ "$creation_output" == *worktree-creation-failed* && "$creation_output" == *effect=unknown* \
  && "$creation_output" != *private-registration-canary* ]] || fail "creation failure lost safe effect/phase"
[ -f "$TMP_ROOT/mutation" ] || fail "creation double was not exercised"
[ ! -d "$planned" ] || fail "creation fault fixture changed the intended target"

echo "persistent chat worktree smoke test passed."
