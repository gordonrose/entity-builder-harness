#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.smoke-test-deterministic-process-drift
#   version: 1
#   status: active
#   created_on: "2026-11-05"
#   updated_on: "2026-11-05"
#   layer: 01.harness
#   domain: validation
#   disciplines: [agentic, security]
#   kind: script
#   purpose: Prove unavailable scans cannot be reported as no deterministic process drift.
#   portability: { class: source-only, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/01.harness/check-deterministic-process-drift.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
mkdir -p "$TMP_ROOT/repo/.agentic" "$TMP_ROOT/bin"
printf 'Ordinary prose.\n' > "$TMP_ROOT/repo/AGENTS.md"
printf 'Ordinary prose.\n' > "$TMP_ROOT/repo/.agentic/example.md"
export DRIFT_REAL_AWK="$(command -v awk)" DRIFT_REAL_FIND="$(command -v find)" DRIFT_REAL_SORT="$(command -v sort)"
cat > "$TMP_ROOT/bin/git" <<'SH'
#!/usr/bin/env bash
case "$DRIFT_FAULT:$*" in
  paths:'diff --cached --name-only'*|commit-paths:diff-tree*|diff:'diff --cached -U0'*|commit-diff:show*)
    echo DRIFT_NATIVE_CANARY >&2; exit 99 ;;
esac
case "$*" in
  'diff --cached --name-only'*|diff-tree*) echo AGENTS.md ;;
  'rev-parse --verify'*) echo fixture-commit ;;
  *) printf '@@ -0,0 +1 @@\n+Ordinary prose.\n' ;;
esac
SH
for tool in awk find sort; do
  cat > "$TMP_ROOT/bin/$tool" <<'SH'
#!/usr/bin/env bash
tool="$(basename "$0")"
if [ "$DRIFT_FAULT" = "$tool" ]; then echo DRIFT_NATIVE_CANARY >&2; exit 99; fi
case "$tool" in
  awk) exec "$DRIFT_REAL_AWK" "$@" ;;
  find) exec "$DRIFT_REAL_FIND" "$@" ;;
  sort) exec "$DRIFT_REAL_SORT" "$@" ;;
esac
SH
done
chmod +x "$TMP_ROOT/bin/"*
(cd "$TMP_ROOT/repo"; bash "$SCRIPT" --all) > "$TMP_ROOT/out"
grep -q '^No deterministic process drift found.' "$TMP_ROOT/out" || fail "normal empty findings"
for fault in paths commit-paths diff commit-diff awk find sort; do
  args=(--all)
  case "$fault" in
    paths|diff) args=(--staged) ;;
    commit-paths|commit-diff) args=(--commit fixture) ;;
  esac
  status=0
  (cd "$TMP_ROOT/repo"; TMPDIR="$TMP_ROOT" DRIFT_FAULT="$fault" PATH="$TMP_ROOT/bin:$PATH" \
    bash "$SCRIPT" "${args[@]}") > "$TMP_ROOT/out" 2>&1 || status=$?
  [ "$status" -eq 2 ] || fail "$fault status $status"
  grep -q 'deterministic-process-observation-unavailable' "$TMP_ROOT/out" || fail "$fault reason missing"
  if grep -Eq 'DRIFT_NATIVE_CANARY|No deterministic|process drift found' "$TMP_ROOT/out"; then fail "$fault misreported"; fi
done
printf 'Verify that the file exists.\n' > "$TMP_ROOT/repo/AGENTS.md"
status=0
(cd "$TMP_ROOT/repo"; bash "$SCRIPT" --paths AGENTS.md) > "$TMP_ROOT/out" 2>&1 || status=$?
[ "$status" -eq 1 ] || fail "actual drift status"
grep -q 'Type: scriptable-check' "$TMP_ROOT/out" || fail "actual finding lost"
echo "deterministic process diagnostic smoke test passed."
