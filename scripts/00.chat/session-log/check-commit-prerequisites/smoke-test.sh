#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.check-commit-prerequisites.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test commit prerequisite validation and missing-file failures.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.check-commit-prerequisites.readme
#     path: scripts/00.chat/session-log/check-commit-prerequisites/README.md
#   - id: chat.script.session-log.check-commit-prerequisites
#     path: scripts/00.chat/session-log/check-commit-prerequisites/script.sh
#   effects:
#   - writes-files
#   - branches
#   - commits
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
  "$REPO/scripts/00.chat/session-log/check-commit-prerequisites" \
  "$REPO/scripts/00.chat/session-log/read-current-chat-log" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/01.harness"

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/check-commit-prerequisites/script.sh" "$REPO/scripts/00.chat/session-log/check-commit-prerequisites/script.sh"
chmod +x "$REPO/scripts/00.chat/session-log/check-commit-prerequisites/script.sh"

cat > "$REPO/.agentic/00.chat/checklists/before-commit.md" <<'EOF'
# Before Commit

Run:

```bash
bash scripts/00.chat/session-log/check-commit-prerequisites/script.sh
```

Repositories may provide an optional extension hook at
`scripts/repo/commit-gates/script.sh`.
EOF

cat > "$REPO/.agentic/00.chat/workflows/chat-start.md" <<'EOF'
# Chat Start

Run:

```bash
bash scripts/00.chat/session-log/read-current-chat-log/script.sh
```

The executable startup scripts live under canonical `scripts/00.chat/`
capability folders.
EOF

printf '#!/usr/bin/env bash\n' > "$REPO/scripts/00.chat/session-log/read-current-chat-log/script.sh"

cat > "$REPO/commitLogs/2026/jun/19/2026-06-19-13-11-test/README.md" <<'EOF'
# Chat Session: test

<!-- agentic-session
id: 2026-06-19-13-11-test
task: test
branch: chat/2026-06-19-13-11-test
worktree:
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
status: ready
-->
EOF

git -C "$REPO" add .
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'
git -C "$REPO" switch --quiet -c chat/2026-06-19-13-11-test

if sed -n '/<!-- agentic-session/,/-->/p' "$REPO/commitLogs/2026/jun/19/2026-06-19-13-11-test/README.md" | grep -Eq '^(layer|mode|workflow): '; then
  fail "smoke fixture contains durable classification metadata"
fi

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/check-commit-prerequisites/script.sh \
  >"$TMP_ROOT/out"

grep -q 'Commit prerequisites are present.' "$TMP_ROOT/out" \
  || fail "commit prerequisites did not pass with prose directory reference"

grep -q 'optional referenced gate script is absent: scripts/repo/commit-gates/script.sh' "$TMP_ROOT/out" \
  || fail "optional repository extension hook was not treated as optional"

if grep -q 'scripts/00.chat/ is missing' "$TMP_ROOT/out"; then
  fail "directory prose reference was treated as a missing script"
fi

echo "commit prerequisites smoke test passed."
