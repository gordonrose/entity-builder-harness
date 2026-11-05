#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.upstream.check-llm-workbench-contract.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-11-05"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: validation
#   disciplines: [agentic, security]
#   kind: script
#   purpose: Prove contract pattern reads distinguish rejected content from unavailable observation.
#   portability: { class: source-only, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/00.chat/upstream/check-llm-workbench-contract/script.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
FIXTURE="$TMP_ROOT/repo"
# Only files that this read-only contract checker consumes.
for source in \
 .agentic/00.chat/workflows/chat-start.md \
 .agentic/00.chat/standards/llm-workbench-public-beta-contract.md \
 .agentic/00.chat/checklists/llm-workbench-public-beta.md \
 scripts/00.chat/startup/start-chat-session/script.sh \
 scripts/00.chat/session-log/record-chat-commit/script.sh \
 scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh \
 scripts/00.chat/metrics/estimate-chat-cost/script.js \
 scripts/00.chat/metrics/data/chat-pricing.json \
 scripts/00.chat/metrics/data/chat-pricing.schema.json \
 scripts/00.chat/command/dispatcher/script.sh \
 docs/00.chat/llm-workbench-acceptance-matrix.md \
 docs/00.chat/bootstrap/llm-workbench-template/root/docs/public-beta-contract.md.template \
 docs/00.chat/bootstrap/llm-workbench-template/root/README.md.template; do
  mkdir -p "$FIXTURE/$(dirname "$source")"
  cp "$ROOT/$source" "$FIXTURE/$source"
done
bash "$SCRIPT" --repo "$FIXTURE" > "$TMP_ROOT/out"
grep -q 'contract check passed' "$TMP_ROOT/out" || fail "ordinary contract did not pass"
export CONTRACT_REAL_GREP="$(command -v grep)"
mkdir -p "$TMP_ROOT/bin"
cat > "$TMP_ROOT/bin/grep" <<'SH'
#!/usr/bin/env bash
case "$CONTRACT_FAULT:$*" in
  required:*'"default_profile"'*|forbidden:*'classify-task'*|tree:*'-RIEq'*)
    echo CONTRACT_NATIVE_CANARY >&2; exit 99 ;;
esac
exec "$CONTRACT_REAL_GREP" "$@"
SH
chmod +x "$TMP_ROOT/bin/grep"
for fault in required forbidden tree; do
  status=0
  CONTRACT_FAULT="$fault" PATH="$TMP_ROOT/bin:$PATH" bash "$SCRIPT" --repo "$FIXTURE" > "$TMP_ROOT/out" 2>&1 || status=$?
  [ "$status" -eq 2 ] || fail "$fault status $status"
  grep -q 'workbench-contract-observation-unavailable' "$TMP_ROOT/out" || fail "$fault reason lost"
  if grep -Eq 'CONTRACT_NATIVE_CANARY|contract check passed|FAIL:' "$TMP_ROOT/out"; then fail "$fault misreported"; fi
done
printf '\nclassify-task\n' >> "$FIXTURE/.agentic/00.chat/workflows/chat-start.md"
status=0
bash "$SCRIPT" --repo "$FIXTURE" > "$TMP_ROOT/out" 2>&1 || status=$?
[ "$status" -eq 1 ] || fail "actual forbidden content must remain a rejection"
grep -q 'unexpected pattern' "$TMP_ROOT/out" || fail "actual rejection reason missing"
# The portability command's pattern guards are tested without building/installing
# a workbench for each injected read fault. Its complete caller runs once in the
# final disposable portability qualification.
sed '/^make_repo()/,$d' "$ROOT/scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh" \
  > "$TMP_ROOT/portability-guards.sh"
printf 'present\n' > "$TMP_ROOT/pattern"
for guard in require_grep reject_grep reject_tree_grep; do
  status=0
  CONTRACT_FAULT=forbidden PATH="$TMP_ROOT/bin:$PATH" bash -c \
    'source "$1"; "$2" classify-task "$3"' sh "$TMP_ROOT/portability-guards.sh" "$guard" "$TMP_ROOT/pattern" \
    > "$TMP_ROOT/guard.out" 2>&1 || status=$?
  [ "$status" -eq 2 ] || fail "$guard accepted failed pattern read"
  grep -q 'portability-observation-unavailable; stage=pattern-read' "$TMP_ROOT/guard.out" || fail "$guard reason missing"
  if grep -Eq 'CONTRACT_NATIVE_CANARY|FAIL:' "$TMP_ROOT/guard.out"; then fail "$guard misreported"; fi
done
bash -c 'source "$1"; require_grep present "$2"; reject_grep absent "$2"; reject_tree_grep absent "$2"' \
  sh "$TMP_ROOT/portability-guards.sh" "$TMP_ROOT/pattern"
echo "upstream contract diagnostic smoke test passed."
