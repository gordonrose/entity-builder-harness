#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test commit prerequisite validation and missing-file failures.
#   domain: git
#   portability: llm-workbench-validation
#   used_by:
#     - .agentic/00.chat/checklists/before-commit.md
#     - scripts/shared/git/check-commit-prerequisites.sh
#   effects: writes-files, branches, commits

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/commit-prerequisites-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init --quiet --initial-branch=main

mkdir -p \
  "$REPO/.agentic/00.chat/checklists" \
  "$REPO/.agentic/00.chat/workflows" \
  "$REPO/commitLogs/2026/jun/19/2026-06-19-13-11-test" \
  "$REPO/scripts/shared/chat" \
  "$REPO/scripts/shared/git" \
  "$REPO/scripts/shared/harness"

cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" "$REPO/scripts/shared/chat/session-log-paths.sh"
cp "$SOURCE_ROOT/scripts/shared/git/check-commit-prerequisites.sh" "$REPO/scripts/shared/git/check-commit-prerequisites.sh"
chmod +x "$REPO/scripts/shared/git/check-commit-prerequisites.sh"

cat > "$REPO/.agentic/00.chat/checklists/before-commit.md" <<'EOF'
# Before Commit

Run:

```bash
bash scripts/shared/git/check-commit-prerequisites.sh
```
EOF

cat > "$REPO/.agentic/00.chat/workflows/chat-start.md" <<'EOF'
# Chat Start

Run:

```bash
bash scripts/shared/chat/request-initialization/read-current-chat-log.sh
```

The executable startup scripts still live under `scripts/shared/chat/` for
compatibility.
EOF

mkdir -p "$REPO/scripts/shared/chat/request-initialization"
printf '#!/usr/bin/env bash\n' > "$REPO/scripts/shared/chat/request-initialization/read-current-chat-log.sh"

cat > "$REPO/commitLogs/2026/jun/19/2026-06-19-13-11-test/README.md" <<'EOF'
# Chat Session: test

<!-- agentic-session
id: 2026-06-19-13-11-test
task: test
branch: chat/2026-06-19-13-11-test
worktree:
layer: chat
mode: implementation
workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
-->
EOF

git -C "$REPO" add .
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'
git -C "$REPO" switch --quiet -c chat/2026-06-19-13-11-test

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/shared/git/check-commit-prerequisites.sh \
  >"$TMP_ROOT/out"

grep -q 'Commit prerequisites are present.' "$TMP_ROOT/out" \
  || fail "commit prerequisites did not pass with prose directory reference"

if grep -q 'scripts/shared/chat/ is missing' "$TMP_ROOT/out"; then
  fail "directory prose reference was treated as a missing script"
fi

echo "commit prerequisites smoke test passed."
