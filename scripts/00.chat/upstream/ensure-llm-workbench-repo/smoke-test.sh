#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.upstream.ensure-llm-workbench-repo.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-11-05"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: validation
#   disciplines: [agentic, security]
#   kind: script
#   purpose: Prove upstream lookup failure reporting using a relocated disposable target and command doubles.
#   portability: { class: source-only, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
TARGET="$TMP_ROOT/upstream"
SCRIPT="$TMP_ROOT/ensure.sh"
# Relocate only the canonical fixture path. Never execute against real upstream.
sed "s#^TARGET_PATH=.*#TARGET_PATH=\"$TARGET\"#" \
  "$ROOT/scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh" > "$SCRIPT"
mkdir -p "$TARGET/.git" "$TMP_ROOT/bin"
cat > "$TMP_ROOT/bin/git" <<'SH'
#!/usr/bin/env bash
if [ "$1" = clone ]; then
  echo "UPSTREAM_NATIVE_CANARY" >&2
  exit 77
fi
case "$UPSTREAM_CASE" in
  valid) echo 'git@github.com:gordonrose/llm-workbench.git' ;;
  missing) exit 1 ;;
  wrong) echo 'https://UPSTREAM_ORIGIN_CANARY@example.invalid/private' ;;
  failed) echo 'git@github.com:gordonrose/llm-workbench.git'; echo UPSTREAM_NATIVE_CANARY >&2; exit 99 ;;
esac
SH
chmod +x "$TMP_ROOT/bin/git"
for scenario in valid missing wrong failed; do
  status=0
  UPSTREAM_CASE="$scenario" PATH="$TMP_ROOT/bin:$PATH" bash "$SCRIPT" --dry-run > "$TMP_ROOT/out" 2>&1 || status=$?
  case "$scenario" in
    valid) expected=0; message='already present' ;;
    missing) expected=1; message='no configured origin' ;;
    wrong) expected=1; message='unexpected origin' ;;
    failed) expected=2; message='upstream-origin-read-failed' ;;
  esac
  [ "$status" -eq "$expected" ] || fail "$scenario status $status"
  grep -q "$message" "$TMP_ROOT/out" || fail "$scenario lost reason"
  if grep -Eq 'UPSTREAM_NATIVE_CANARY|UPSTREAM_ORIGIN_CANARY' "$TMP_ROOT/out"; then fail "$scenario leaked"; fi
done
rmdir "$TARGET/.git" "$TARGET"
PATH="$TMP_ROOT/bin:$PATH" bash "$SCRIPT" --dry-run > "$TMP_ROOT/out"
grep -q '^Would clone ' "$TMP_ROOT/out" || fail 'missing target dry run'
status=0
PATH="$TMP_ROOT/bin:$PATH" bash "$SCRIPT" > "$TMP_ROOT/out" 2>&1 || status=$?
[ "$status" -eq 77 ] || fail "clone status lost"
grep -q 'upstream-clone-failed; effect=unknown' "$TMP_ROOT/out" || fail "clone uncertainty lost"
if grep -Eq 'UPSTREAM_NATIVE_CANARY|Cloned llm' "$TMP_ROOT/out"; then fail "clone leaked or succeeded"; fi
echo "upstream ensure diagnostic smoke test passed."
