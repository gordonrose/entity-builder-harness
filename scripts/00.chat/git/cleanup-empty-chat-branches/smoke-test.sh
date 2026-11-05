#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.git.cleanup-empty-chat-branches.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-16"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: git
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test empty chat branch and session log cleanup safety.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-cleanup
#     path: .agentic/00.chat/workflows/chat-cleanup.md
#   - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
#   effects:
#   - branches
#   - commits
#   - destructive
#   - writes-files

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/cleanup-empty-chat-branches-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

REPO="$TMP_ROOT/repo"
 mkdir -p "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches" "$REPO/scripts/00.chat/session-log/paths"
cp "$SOURCE_ROOT/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"

git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"

printf 'base\n' > "$REPO/base.txt"
git -C "$REPO" add base.txt scripts/00.chat/git/cleanup-empty-chat-branches/script.sh scripts/00.chat/session-log/paths/lib.sh
git -C "$REPO" commit -q -m "initial"

COMMITTED_SESSION="2026-06-16-07-18-committed-log"
COMMITTED_BRANCH="chat/$COMMITTED_SESSION"
COMMITTED_LOG="$REPO/commitLogs/2026/jun/16/$COMMITTED_SESSION/README.md"

git -C "$REPO" switch -q -c "$COMMITTED_BRANCH"
printf 'work\n' > "$REPO/work.txt"
git -C "$REPO" add work.txt
git -C "$REPO" commit -q -m "committed chat work"
COMMITTED_SHA="$(git -C "$REPO" rev-parse --short HEAD)"

git -C "$REPO" switch -q main
git -C "$REPO" merge -q --ff-only "$COMMITTED_BRANCH"

mkdir -p "$(dirname "$COMMITTED_LOG")"
cat > "$COMMITTED_LOG" <<EOF
# Chat Session: committed log

<!-- agentic-session
id: $COMMITTED_SESSION
branch: $COMMITTED_BRANCH
latest_commit_sha: $COMMITTED_SHA
-->

## Commits

- Commit: \`$COMMITTED_SHA\`
EOF

EMPTY_SESSION="2026-06-16-07-19-empty-log"
EMPTY_BRANCH="chat/$EMPTY_SESSION"
EMPTY_LOG="$REPO/commitLogs/2026/jun/16/$EMPTY_SESSION/README.md"

git -C "$REPO" branch "$EMPTY_BRANCH"
mkdir -p "$(dirname "$EMPTY_LOG")"
cat > "$EMPTY_LOG" <<EOF
# Chat Session: empty log

<!-- agentic-session
id: $EMPTY_SESSION
branch: $EMPTY_BRANCH
latest_commit_sha:
-->

## Commits

- None recorded yet.
EOF

git -C "$REPO" add "$COMMITTED_LOG" "$EMPTY_LOG"
git -C "$REPO" commit -q -m "add chat logs"

export REAL_GIT="$(command -v git)" REAL_AWK="$(command -v awk)" REAL_SED="$(command -v sed)" REAL_GREP="$(command -v grep)"
mkdir "$TMP_ROOT/fault-bin"
for command in git awk sed grep; do
  printf '#!/usr/bin/env bash\ncommand=%q\n' "$command" > "$TMP_ROOT/fault-bin/$command"
  cat >> "$TMP_ROOT/fault-bin/$command" <<'EOF'
case "$FAULT:$command:${1:-}" in
  branch:git:branch|reference:git:show-ref|base-resolution:git:rev-parse|worktrees:git:worktree|comparison:git:rev-list|metadata:sed:*|match:grep:*)
    echo private-cleanup-canary@example.invalid >&2
    exit 74 ;;
esac
if [ "$FAULT" = enumeration ] && [ "$command" = git ] && [ "${1:-}" = branch ] && [ "${2:-}" != --show-current ]; then
  echo private-cleanup-canary@example.invalid >&2
  exit 74
fi
if [ "$FAULT" = retention ] && [ "$command" = grep ] && [ "${1:-}" = -Eiq ]; then
  echo private-cleanup-canary@example.invalid >&2
  exit 74
fi
if [ "$FAULT" = commit ] && [ "$command" = sed ] && [[ "${2:-}" == *latest_commit_sha* ]]; then
  echo private-cleanup-canary@example.invalid >&2
  exit 74
fi
if [ "$FAULT" = delete ] && [ "$command" = git ] && [ "${1:-}" = branch ] && [ "${2:-}" = -D ]; then
  echo private-cleanup-canary@example.invalid >&2
  exit 74
fi
case "$command" in
  git) exec "$REAL_GIT" "$@" ;;
  awk) exec "$REAL_AWK" "$@" ;;
  sed) exec "$REAL_SED" "$@" ;;
  grep) exec "$REAL_GREP" "$@" ;;
esac
EOF
  chmod +x "$TMP_ROOT/fault-bin/$command"
done
for stage in branch reference worktrees comparison metadata match enumeration retention commit delete; do
  mode=--dry-run
  expected=2
  if [ "$stage" = delete ]; then mode=--apply; expected=74; fi
  if failure="$(cd "$REPO" && PATH="$TMP_ROOT/fault-bin:$PATH" FAULT="$stage" \
    bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh "$mode" 2>&1)"; then
    fail "$stage failure was accepted as complete cleanup"
  else
    [ "$?" -eq "$expected" ] || fail "$stage failure status lost: $failure"
  fi
  [[ "$failure" == *cleanup-*-failed* && "$failure" != *private-cleanup-canary* && "$failure" != *Empty\ chat\ branches\ found* ]] || fail "$stage safe failure lost"
  git -C "$REPO" show-ref --verify --quiet "refs/heads/$COMMITTED_BRANCH" || fail "failed observation/mutation removed branch"
  [ -f "$COMMITTED_LOG" ] && [ -f "$EMPTY_LOG" ] || fail "failed observation removed a log"
done

status=0
( cd "$REPO"; PATH="$TMP_ROOT/fault-bin:$PATH" FAULT=base-resolution \
  bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --dry-run ) > "$TMP_ROOT/base-resolution.out" 2>&1 || status=$?
[ "$status" -eq 1 ] || fail "base resolution lost refusal status"
grep -Fxq 'ERROR: base branch could not be resolved' "$TMP_ROOT/base-resolution.out" || fail "base resolution reason missing"
if grep -Eq 'private-cleanup-canary|Empty chat branches found' "$TMP_ROOT/base-resolution.out"; then
  fail "base resolution leaked or claimed success"
fi
(
  cd "$REPO"
  bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --apply
) > "$TMP_ROOT/cleanup.out" 2> "$TMP_ROOT/cleanup.err"

if git -C "$REPO" show-ref --verify --quiet "refs/heads/$COMMITTED_BRANCH"; then
  fail "merged committed branch was not deleted"
fi

if [ ! -f "$COMMITTED_LOG" ]; then
  fail "commit log with recorded commit was deleted"
fi

if git -C "$REPO" show-ref --verify --quiet "refs/heads/$EMPTY_BRANCH"; then
  fail "empty branch was not deleted"
fi

if [ -e "$EMPTY_LOG" ]; then
  fail "empty unsaved commit log was not deleted"
fi

if ! grep -q "Kept matching log (recorded commits)" "$TMP_ROOT/cleanup.out"; then
  fail "cleanup did not report keeping the committed log"
fi

if ! grep -q "Deleted matching log" "$TMP_ROOT/cleanup.out"; then
  fail "cleanup did not report deleting the empty log"
fi

echo "cleanup empty chat branches smoke test passed."
