#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.main-refresh.verify-conflict-audit.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-20"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: main-refresh
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test main-refresh conflict audit verification.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.main-refresh.verify-conflict-audit
#     path: scripts/00.chat/main-refresh/verify-conflict-audit/script.sh
#   effects:
#   - writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd -P)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/verify-main-refresh-conflict-audit-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.com
git -C "$REPO" config user.name "Test User"

mkdir -p \
  "$REPO/scripts/00.chat/main-refresh/verify-conflict-audit" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/commitLogs/2026/jun/20/test-session"

cp "$SOURCE_ROOT/scripts/00.chat/main-refresh/verify-conflict-audit/script.sh" "$REPO/scripts/00.chat/main-refresh/verify-conflict-audit/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"

SESSION_LOG="$REPO/commitLogs/2026/jun/20/test-session/README.md"
CONFLICT_PATH="docs/example-conflict.md"
cat > "$SESSION_LOG" <<'EOF'
# Chat Session: test

## Main Refresh Conflicts

- Path: `docs/example-conflict.md`
  Type: `ownership-migration-conflict`
  Mode: deterministic
  Reason: test
  Action: test
  Preflight branch: `agentic/preflight/chat-test/20000101000000`
  Preflight worktree: `/tmp/preflight`
  Files changed by resolution: docs/example-conflict.md
  Checks: test
EOF

git -C "$REPO" add scripts commitLogs
git -C "$REPO" commit -q -m base

(
  cd "$REPO"
  bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh \
    --session-log commitLogs/2026/jun/20/test-session/README.md \
    --path "$CONFLICT_PATH"
) >/dev/null

set +e
(
  cd "$REPO"
  bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh \
    --session-log commitLogs/2026/jun/20/test-session/README.md \
    --path missing/path.md
) > "$TMP_ROOT/missing.out" 2> "$TMP_ROOT/missing.err"
MISSING_STATUS="$?"
set -e

if [ "$MISSING_STATUS" -eq 0 ]; then
  fail "missing conflict audit path passed"
fi

if ! grep -q "conflict path missing from session audit" "$TMP_ROOT/missing.err"; then
  fail "missing path failure was not explained"
fi

# Failed observations must not become an empty index or a missing audit entry.
export REAL_GIT="$(command -v git)" REAL_AWK="$(command -v awk)" REAL_GREP="$(command -v grep)" REAL_CAT="$(command -v cat)"
mkdir "$TMP_ROOT/fault-bin"
for command in git awk grep cat; do
  printf '#!/usr/bin/env bash\ncommand=%q\n' "$command" > "$TMP_ROOT/fault-bin/$command"
  cat >> "$TMP_ROOT/fault-bin/$command" <<'EOF'
case "$FAULT:$command:${1:-}" in
  index:git:diff|branch:git:branch|audit:awk:*|match:grep:*|paths:cat:*)
    echo private-audit-canary@example.invalid >&2
    exit 2 ;;
esac
case "$command" in
  git) exec "$REAL_GIT" "$@" ;;
  awk) exec "$REAL_AWK" "$@" ;;
  grep) exec "$REAL_GREP" "$@" ;;
  cat) exec "$REAL_CAT" "$@" ;;
esac
EOF
  chmod +x "$TMP_ROOT/fault-bin/$command"
done
printf '%s\n' "$CONFLICT_PATH" > "$TMP_ROOT/paths"
for stage in index branch audit match paths; do
  args=(--session-log "$SESSION_LOG" --path "$CONFLICT_PATH")
  case "$stage" in
    index) args=(--session-log "$SESSION_LOG"); expected=conflict-index-read-failed ;;
    branch) args=(--path "$CONFLICT_PATH"); expected=conflict-branch-read-failed ;;
    audit) expected=conflict-audit-read-failed ;;
    match) expected=conflict-audit-match-failed ;;
    paths) args=(--session-log "$SESSION_LOG" --paths-file "$TMP_ROOT/paths"); expected=conflict-paths-file-read-failed ;;
  esac
  if output="$(cd "$REPO" && PATH="$TMP_ROOT/fault-bin:$PATH" FAULT="$stage" \
    bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh "${args[@]}" 2>&1)"; then
    fail "$stage read failure was accepted"
  else
    [ "$?" -eq 2 ] || fail "$stage unavailable status lost"
  fi
  [[ "$output" == *"$expected"* ]] || fail "$stage precise reason lost"
  [[ "$output" != *private-audit-canary* && "$output" != *verified* && "$output" != *missing\ from* ]] || fail "$stage unsafe or misleading report"
done

# A leading '-' is a literal path, never a grep option; ordinary absence is 1.
if output="$(cd "$REPO" && bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh \
  --session-log "$SESSION_LOG" --path --private-path-canary 2>&1)"; then
  fail "absent literal path accepted"
else
  [ "$?" -eq 1 ] || fail "literal path interpreted as an option"
fi
[[ "$output" != *private-path-canary* ]] || fail "rejected path leaked"

echo "main refresh conflict audit verifier smoke test passed."
