#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.smoke-test-governed-script-command-drift
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test governed script command drift detection.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: harness.standards.governed-script-permissions
#     path: .agentic/01.harness/standards/governed-script-permissions.md
#   - id: harness.script.check-governed-script-command-drift
#     path: scripts/01.harness/check-governed-script-command-drift.sh
#   effects:
#   - commits
#   - writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/governed-script-command-drift.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

REPO="$TMP_ROOT/repo"
mkdir -p \
  "$REPO/.agentic/00.chat/checklists" \
  "$REPO/.agentic/00.chat/workflows" \
  "$REPO/docs/harness/architecture/adrs" \
  "$REPO/scripts/01.harness"

cp "$SOURCE_ROOT/scripts/01.harness/run-governed-script.sh" \
  "$REPO/scripts/01.harness/run-governed-script.sh"
cp "$SOURCE_ROOT/scripts/01.harness/check-governed-script-command-drift.sh" \
  "$REPO/scripts/01.harness/check-governed-script-command-drift.sh"

git -C "$REPO" init --quiet
cd "$REPO"

cat > .agentic/00.chat/checklists/bad.md <<'EOF'
# Bad

```bash
bash scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh
```
EOF

if bash scripts/01.harness/check-governed-script-command-drift.sh \
    --paths .agentic/00.chat/checklists/bad.md \
    > "$TMP_ROOT/bad.out" 2>&1; then
  fail "direct approval-sensitive command was not flagged"
fi

grep -q 'direct-approved-governed-script' "$TMP_ROOT/bad.out" \
  || fail "drift finding did not include expected type"

cat > .agentic/00.chat/checklists/good.md <<'EOF'
# Good

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh
```
EOF

bash scripts/01.harness/check-governed-script-command-drift.sh \
  --paths .agentic/00.chat/checklists/good.md \
  > "$TMP_ROOT/good.out"

cat > .agentic/00.chat/workflows/prose.md <<'EOF'
# Prose

The checkpoint helper lives at scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh.
EOF

if bash scripts/01.harness/check-governed-script-command-drift.sh \
    --paths .agentic/00.chat/workflows/prose.md \
    > "$TMP_ROOT/prose.out" 2>&1; then
  fail "bare approval-sensitive script reference was not flagged"
fi

grep -q 'unrouted-approved-governed-script-reference' "$TMP_ROOT/prose.out" \
  || fail "bare script finding did not include expected type"

cat > .agentic/00.chat/workflows/basename-prose.md <<'EOF'
# Basename prose

The checkpoint-chat-session-log.sh helper is approval-sensitive.
EOF

bash scripts/01.harness/check-governed-script-command-drift.sh \
  --paths .agentic/00.chat/workflows/basename-prose.md \
  > "$TMP_ROOT/basename-prose.out"

cat > docs/harness/architecture/adrs/0001-example.md <<'EOF'
# Historical ADR

```bash
bash scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh
```
EOF

bash scripts/01.harness/check-governed-script-command-drift.sh \
  --paths docs/harness/architecture/adrs/0001-example.md \
  > "$TMP_ROOT/adr.out"

echo "governed script command drift smoke test passed"
