#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.bootstrap.diagnostic-smoke-test
#   version: 1
#   status: active
#   created_on: "2026-11-05"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: validation
#   disciplines: [agentic, security]
#   kind: script
#   purpose: Prove audit scan failure is distinct from an empty or valid audit.
#   portability: { class: source-only, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
mkdir -p "$TMP_ROOT/repo/"{.agentic,scripts,docs} "$TMP_ROOT/bin"
printf 'scripts/00.chat/example/script.sh\n' > "$TMP_ROOT/repo/AGENTS.md"
mkdir -p "$TMP_ROOT/repo/scripts/00.chat/example"
printf '#!/bin/bash\n' > "$TMP_ROOT/repo/scripts/00.chat/example/script.sh"

export AUDIT_FIXTURE="$TMP_ROOT/repo"
export AUDIT_REAL_GREP="$(command -v grep)" AUDIT_REAL_FIND="$(command -v find)"
cat > "$TMP_ROOT/bin/git" <<'SH'
#!/usr/bin/env bash
printf '%s\n' "$AUDIT_FIXTURE"
SH
cat > "$TMP_ROOT/bin/grep" <<'SH'
#!/usr/bin/env bash
if [ "$AUDIT_FAULT" = grep ]; then echo AUDIT_NATIVE_CANARY >&2; exit 99; fi
exec "$AUDIT_REAL_GREP" "$@"
SH
cat > "$TMP_ROOT/bin/find" <<'SH'
#!/usr/bin/env bash
if [ "$AUDIT_FAULT" = find ]; then echo AUDIT_NATIVE_CANARY >&2; exit 99; fi
exec "$AUDIT_REAL_FIND" "$@"
SH
chmod +x "$TMP_ROOT/bin/"*
(cd "$TMP_ROOT/repo"; AUDIT_FAULT=none PATH="$TMP_ROOT/bin:$PATH" bash "$SCRIPT") > "$TMP_ROOT/out" 2>&1
grep -q 'completed' "$TMP_ROOT/out" || fail "ordinary audit did not complete"
for fault in grep find; do

  status=0
  (cd "$TMP_ROOT/repo"; AUDIT_FAULT="$fault" PATH="$TMP_ROOT/bin:$PATH" bash "$SCRIPT") > "$TMP_ROOT/out" 2>&1 || status=$?
  [ "$status" -eq 2 ] || fail "$fault status $status"
  grep -q 'bootstrap-audit-observation-unavailable' "$TMP_ROOT/out" || fail "$fault reason missing"

  if grep -Eq 'AUDIT_NATIVE_CANARY|completed|no retired compatibility references' "$TMP_ROOT/out"; then fail "$fault misreported"; fi
done
printf 'scripts/00.chat/missing/script.sh\n' >> "$TMP_ROOT/repo/AGENTS.md"
status=0
(cd "$TMP_ROOT/repo"; AUDIT_FAULT=none PATH="$TMP_ROOT/bin:$PATH" bash "$SCRIPT") > "$TMP_ROOT/out" 2>&1 || status=$?
[ "$status" -eq 1 ] || fail "actual missing reference status"
grep -q 'Missing referenced scripts' "$TMP_ROOT/out" || fail "missing reference reason"
echo "bootstrap audit diagnostic smoke test passed."
