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
  if [ -n "${PREFLIGHT_BRANCH:-}" ]; then
    git -C "$REPO" branch -D "$PREFLIGHT_BRANCH" >/dev/null 2>&1 || true
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
  bash scripts/shared/chat/generate-commit-log-summary.sh --output "$TMP_ROOT/base-summary.md" >/dev/null
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

if [ -z "$PREFLIGHT_BRANCH" ] || [ -z "$PREFLIGHT_WORKTREE" ]; then
  fail "preflight did not report branch and worktree"
fi

if ! printf '%s\n' "$PREFLIGHT_OUTPUT" | grep -q '^result=clean-merge$'; then
  fail "preflight did not report a clean merge"
fi

(
  cd "$REPO"
  bash scripts/shared/git/promote-preflight-refresh.sh "$PREFLIGHT_BRANCH" >/dev/null
)

if ! grep -q "main update" "$REPO/README.md"; then
  fail "promoted chat branch does not include main update"
fi

if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
  fail "repo is dirty after preflight promotion"
fi

echo "main refresh preflight smoke test passed."
