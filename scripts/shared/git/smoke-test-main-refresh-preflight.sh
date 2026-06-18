#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/main-refresh-preflight-smoke.XXXXXX")"

cleanup() {
  if [ -n "${PREFLIGHT_WORKTREE:-}" ] && [ -d "$PREFLIGHT_WORKTREE" ]; then
    git -C "$REPO" worktree remove -f "$PREFLIGHT_WORKTREE" >/dev/null 2>&1 || true
  fi
  if [ -n "${DIRTY_PREFLIGHT_WORKTREE:-}" ] && [ -d "$DIRTY_PREFLIGHT_WORKTREE" ]; then
    git -C "$REPO" worktree remove -f "$DIRTY_PREFLIGHT_WORKTREE" >/dev/null 2>&1 || true
  fi
  if [ -n "${PREFLIGHT_BRANCH:-}" ]; then
    git -C "$REPO" branch -D "$PREFLIGHT_BRANCH" >/dev/null 2>&1 || true
  fi
  if [ -n "${DIRTY_PREFLIGHT_BRANCH:-}" ]; then
    git -C "$REPO" branch -D "$DIRTY_PREFLIGHT_BRANCH" >/dev/null 2>&1 || true
  fi
  if [ -n "${STALE_PREFLIGHT_WORKTREE:-}" ] && [ -d "$STALE_PREFLIGHT_WORKTREE" ]; then
    git -C "$REPO" worktree remove -f "$STALE_PREFLIGHT_WORKTREE" >/dev/null 2>&1 || true
  fi
  if [ -n "${UNIQUE_PREFLIGHT_WORKTREE:-}" ] && [ -d "$UNIQUE_PREFLIGHT_WORKTREE" ]; then
    git -C "$REPO" worktree remove -f "$UNIQUE_PREFLIGHT_WORKTREE" >/dev/null 2>&1 || true
  fi
  if [ -n "${STALE_PREFLIGHT_BRANCH:-}" ]; then
    git -C "$REPO" branch -D "$STALE_PREFLIGHT_BRANCH" >/dev/null 2>&1 || true
  fi
  if [ -n "${UNIQUE_PREFLIGHT_BRANCH:-}" ]; then
    git -C "$REPO" branch -D "$UNIQUE_PREFLIGHT_BRANCH" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
SESSION_ID="2026-06-17-00-01-preflight-chat"
SESSION_LOG="commitLogs/2026/jun/17/${SESSION_ID}/README.md"

mkdir -p \
  "$REPO/scripts/shared/chat" \
  "$REPO/scripts/shared/git" \
  "$REPO/$(dirname "$SESSION_LOG")"

cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" \
  "$REPO/scripts/shared/chat/session-log-paths.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/generate-commit-log-summary.sh" \
  "$REPO/scripts/shared/chat/generate-commit-log-summary.sh"
cp "$SOURCE_ROOT/scripts/shared/git/classify-main-refresh-dirty-state.sh" \
  "$REPO/scripts/shared/git/classify-main-refresh-dirty-state.sh"
cp "$SOURCE_ROOT/scripts/shared/git/preflight-main-refresh.sh" \
  "$REPO/scripts/shared/git/preflight-main-refresh.sh"
cp "$SOURCE_ROOT/scripts/shared/git/promote-preflight-refresh.sh" \
  "$REPO/scripts/shared/git/promote-preflight-refresh.sh"

git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"

cat > "$REPO/README.md" <<'EOF'
base
EOF

cat > "$REPO/$SESSION_LOG" <<EOF
# Chat Session: ${SESSION_ID}

<!-- agentic-session
id: ${SESSION_ID}
chat_duration: 10s
estimated_tokens: 50 tokens
-->
EOF

(
  cd "$REPO"
  bash scripts/shared/chat/generate-commit-log-summary.sh >/dev/null
)

git -C "$REPO" add .
git -C "$REPO" commit -q -m "base"
git -C "$REPO" switch -q -c "chat/${SESSION_ID}"

git -C "$REPO" switch -q main
printf 'main update\n' >> "$REPO/README.md"
git -C "$REPO" add README.md
git -C "$REPO" commit -q -m "update main"
git -C "$REPO" switch -q "chat/${SESSION_ID}"

PREFLIGHT_OUTPUT="$(
  cd "$REPO"
  TMPDIR="$TMP_ROOT" bash scripts/shared/git/preflight-main-refresh.sh
)"

PREFLIGHT_BRANCH="$(printf '%s\n' "$PREFLIGHT_OUTPUT" | sed -n 's/^preflight_branch=//p')"
PREFLIGHT_WORKTREE="$(printf '%s\n' "$PREFLIGHT_OUTPUT" | sed -n 's/^preflight_worktree=//p')"
PREFLIGHT_HEAD="$(printf '%s\n' "$PREFLIGHT_OUTPUT" | sed -n 's/^preflight_head=//p')"

if [ -z "$PREFLIGHT_BRANCH" ] || [ -z "$PREFLIGHT_WORKTREE" ] || [ -z "$PREFLIGHT_HEAD" ]; then
  fail "preflight did not report branch, worktree, and head"
fi

if ! printf '%s\n' "$PREFLIGHT_OUTPUT" | grep -q '^result=clean-merge$'; then
  fail "preflight did not report a clean merge"
fi

printf 'dirty preflight residue\n' >> "$PREFLIGHT_WORKTREE/preflight-note.txt"

set +e
DIRTY_PROMOTE_OUTPUT="$({
  cd "$REPO"
  bash scripts/shared/git/promote-preflight-refresh.sh "$PREFLIGHT_BRANCH"
} 2> "$TMP_ROOT/dirty-promote.err")"
DIRTY_PROMOTE_STATUS="$?"
set -e

if [ "$DIRTY_PROMOTE_STATUS" -eq 0 ]; then
  fail "promotion succeeded with dirty preflight worktree"
fi

if ! grep -q "refusing to clean dirty preflight worktree" "$TMP_ROOT/dirty-promote.err"; then
  fail "dirty preflight worktree failure was not explained"
fi

if [ "$(git -C "$REPO" rev-parse HEAD)" = "$PREFLIGHT_HEAD" ]; then
  fail "dirty cleanup failure still promoted chat branch"
fi

rm -f "$PREFLIGHT_WORKTREE/preflight-note.txt"

PREFLIGHT_PREFIX="${PREFLIGHT_BRANCH%/*}"
STALE_PREFLIGHT_BRANCH="${PREFLIGHT_PREFIX}/20000101000000"
STALE_PREFLIGHT_WORKTREE="$TMP_ROOT/stale-preflight-worktree"
git -C "$REPO" branch "$STALE_PREFLIGHT_BRANCH" HEAD
git -C "$REPO" worktree add --quiet "$STALE_PREFLIGHT_WORKTREE" "$STALE_PREFLIGHT_BRANCH"

UNIQUE_PREFLIGHT_BRANCH="${PREFLIGHT_PREFIX}/20000101000001"
UNIQUE_PREFLIGHT_WORKTREE="$TMP_ROOT/unique-preflight-worktree"
git -C "$REPO" branch "$UNIQUE_PREFLIGHT_BRANCH" HEAD
git -C "$REPO" worktree add --quiet "$UNIQUE_PREFLIGHT_WORKTREE" "$UNIQUE_PREFLIGHT_BRANCH"
printf 'unique stale preflight\n' >> "$UNIQUE_PREFLIGHT_WORKTREE/unique.txt"
git -C "$UNIQUE_PREFLIGHT_WORKTREE" add unique.txt
git -C "$UNIQUE_PREFLIGHT_WORKTREE" commit -q -m "unique stale preflight work"

PROMOTE_OUTPUT="$(
  cd "$REPO"
  bash scripts/shared/git/promote-preflight-refresh.sh "$PREFLIGHT_BRANCH"
)"

if ! grep -q "main update" "$REPO/README.md"; then
  fail "promoted chat branch does not include main update"
fi

if [ "$(git -C "$REPO" rev-parse HEAD)" != "$PREFLIGHT_HEAD" ]; then
  fail "promoted chat branch does not point at preflight head"
fi

if git -C "$REPO" show-ref --verify --quiet "refs/heads/${PREFLIGHT_BRANCH}"; then
  fail "preflight branch still exists after successful promotion"
fi

if git -C "$REPO" worktree list --porcelain | grep -Fqx "worktree ${PREFLIGHT_WORKTREE}"; then
  fail "preflight worktree still exists after successful promotion"
fi

if ! printf '%s\n' "$PROMOTE_OUTPUT" | grep -q '^cleanup_result=removed-worktree-and-deleted-branch$'; then
  fail "promotion did not report cleanup result"
fi

if git -C "$REPO" show-ref --verify --quiet "refs/heads/${STALE_PREFLIGHT_BRANCH}"; then
  fail "ancestor stale preflight branch still exists after promotion"
fi

if git -C "$REPO" worktree list --porcelain | grep -Fqx "worktree ${STALE_PREFLIGHT_WORKTREE}"; then
  fail "ancestor stale preflight worktree still exists after promotion"
fi

if ! printf '%s\n' "$PROMOTE_OUTPUT" | grep -q "^stale_preflight_removed=${STALE_PREFLIGHT_BRANCH} "; then
  fail "promotion did not report stale preflight removal"
fi

if ! git -C "$REPO" show-ref --verify --quiet "refs/heads/${UNIQUE_PREFLIGHT_BRANCH}"; then
  fail "unique stale preflight branch was deleted"
fi

if ! git -C "$REPO" worktree list --porcelain | grep -Fqx "worktree ${UNIQUE_PREFLIGHT_WORKTREE}"; then
  fail "unique stale preflight worktree was removed"
fi

if ! printf '%s\n' "$PROMOTE_OUTPUT" | grep -q "^stale_preflight_skipped=${UNIQUE_PREFLIGHT_BRANCH} reason=unique-commits-not-in-promoted-head$"; then
  fail "promotion did not report unique stale preflight skip"
fi

DIRTY_PREFLIGHT_BRANCH="topic/not-preflight"
git -C "$REPO" branch "$DIRTY_PREFLIGHT_BRANCH" HEAD
set +e
(
  cd "$REPO"
  bash scripts/shared/git/promote-preflight-refresh.sh "$DIRTY_PREFLIGHT_BRANCH"
) > "$TMP_ROOT/non-preflight.out" 2> "$TMP_ROOT/non-preflight.err"
NON_PREFLIGHT_STATUS="$?"
set -e

if [ "$NON_PREFLIGHT_STATUS" -eq 0 ]; then
  fail "promotion accepted a non-preflight branch"
fi

if ! grep -q "refusing non-preflight branch" "$TMP_ROOT/non-preflight.err"; then
  fail "non-preflight branch failure was not explained"
fi

if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
  fail "repo is dirty after preflight promotion"
fi

echo "main refresh preflight smoke test passed."
