#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.smoke-test-governed-script-runner
#   version: 2
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-11-26"
#   layer: 01.harness
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test governed script runner allowlist and approval behavior.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: harness.standards.governed-script-permissions
#     path: .agentic/01.harness/standards/governed-script-permissions.md
#   - id: harness.script.run-governed-script
#     path: scripts/01.harness/run-governed-script.sh
#   effects:
#   - commits
#   - writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/governed-script-runner.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

REPO="$TMP_ROOT/repo"
mkdir -p \
  "$REPO/scripts/00.chat/session-log/rename-current-chat-log-folder" \
  "$REPO/scripts/00.chat/session-log/prepare-chat-session-before-commit" \
  "$REPO/scripts/00.chat/session-log/record-chat-commit" \
  "$REPO/scripts/00.chat/session-log/checkpoint-chat-session-log" \
  "$REPO/scripts/00.chat/startup/auto-start-missing-session" \
  "$REPO/scripts/00.chat/startup/resolve-current-chat-session" \
  "$REPO/scripts/00.chat/upstream/ensure-llm-workbench-repo" \
  "$REPO/scripts/00.chat/worktree/check-write-location" \
  "$REPO/scripts/02.rag-rulebook/run-local-service" \
  "$REPO/scripts/01.harness" \
  "$REPO/scripts/local"

cp "$SOURCE_ROOT/scripts/01.harness/run-governed-script.sh" \
  "$REPO/scripts/01.harness/run-governed-script.sh"
for dependency in scripts/01.harness/artifact-metadata/header_discovery.py .agentic/01.harness/artifact-metadata/taxonomy.yml; do
  mkdir -p "$REPO/${dependency%/*}"
  cp "$SOURCE_ROOT/$dependency" "$REPO/$dependency"
done

make_fixture() {
  local path="$1"
  local label="$2"
  local effects="${3:-read-only}"
  local style="${4:-block}"
  local effect

  mkdir -p "$REPO/${path%/*}"
  {
    printf '#!/usr/bin/env bash\n'
    printf 'set -euo pipefail\n'
    printf '\n'
    printf '# agentic-artifact:\n'
    printf '#   schema: agentic-artifact/v2\n'
    printf '#   id: smoke.fixture.%s\n' "$(printf '%s' "$label" | tr -c '[:alnum:]' '-')"
    printf '#   version: 1\n'
    printf '#   status: active\n'
    printf '#   layer: 00.chat\n'
    printf '#   domain: smoke-test\n'
    printf '#   disciplines:\n'
    printf '#   - agentic\n'
    printf '#   kind: script\n'
    printf '#   purpose: Fixture script for governed runner smoke tests.\n'
    if [ "$style" = inline ]; then
      printf '#   effects: [%s]\n' "${effects// /, }"
    else
      printf '#   effects:\n'
      for effect in $effects; do printf '#   - %s\n' "$effect"; done
    fi
    printf '#   portability: {class: source-only, targets: [aws-mutation]}\n'
    printf '#   unrelated:\n#   - destructive\n'
    printf '\n'
    printf 'echo "%s:$*"\n' "$label"
  } > "$REPO/$path"
}

make_fixture "scripts/shared/git/check-write-location.sh" "retired-check"
make_fixture "scripts/00.chat/worktree/check-write-location/script.sh" "canonical-check"
make_fixture "scripts/shared/chat/ensure-llm-workbench-repo.sh" "retired-workbench" "writes-files"
make_fixture "scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh" "canonical-workbench" "writes-files"
make_fixture "scripts/shared/chat/request-initialization/auto-start-missing-session.sh" "retired-auto-start" "writes-files"
make_fixture "scripts/00.chat/startup/auto-start-missing-session/script.sh" "canonical-auto-start" "writes-files"
make_fixture "scripts/00.chat/startup/resolve-current-chat-session/script.sh" "canonical-resolve-session" "writes-files"
make_fixture "scripts/shared/chat/rename-current-chat-log-folder.sh" "retired-rename" "writes-files"
make_fixture "scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh" "canonical-approved-action" "writes-files"
make_fixture "scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh" "canonical-prepare" "writes-files"
make_fixture "scripts/00.chat/session-log/record-chat-commit/script.sh" "canonical-record" "writes-files commits"
make_fixture "scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh" "canonical-checkpoint" "writes-files"
make_fixture "scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "dangerous-helper" "branches destructive writes-files"
make_fixture "scripts/01.harness/check-deterministic-process-drift.sh" "allowed-harness"
make_fixture "scripts/02.rag-rulebook/run-local-service/smoke-test.sh" "canonical-rag-smoke" "writes-files network"
make_fixture "scripts/local/not-governed.sh" "local-script"
for style in block inline; do
  for effect in destructive aws-mutation push history-rewrite overwrites cloud database network-extra; do
    make_fixture "scripts/01.harness/blocked-$style-$effect.sh" "blocked-$style-$effect" "read-only $effect" "$style"
  done
  for effect in writes-files stages-files commits branches worktrees network; do
    make_fixture "scripts/01.harness/approved-$style-$effect.sh" "approved-$style-$effect" "read-only $effect" "$style"
  done
  make_fixture "scripts/01.harness/read-only-$style.sh" "read-only-$style" read-only "$style"
done
make_fixture "scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh" "refresh" "branches destructive worktrees writes-files"

git -C "$REPO" init --quiet
git -C "$REPO" add scripts
git -C "$REPO" \
  -c user.name="Smoke Test" \
  -c user.email="smoke@example.invalid" \
  commit --quiet -m "fixture"

cd "$REPO"

if bash scripts/01.harness/run-governed-script.sh scripts/shared/git/check-write-location.sh arg1 >"$TMP_ROOT/check-retired.out" 2>&1; then
  fail "retired check-write-location helper was still accepted"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh scripts/00.chat/worktree/check-write-location/script.sh arg1)"
if [ "$OUT" != "canonical-check:arg1" ]; then
  fail "canonical allowed check did not run through the governed runner: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/shared/chat/ensure-llm-workbench-repo.sh --dry-run >"$TMP_ROOT/workbench-missing.out" 2>&1; then
  fail "workbench clone helper ran without --approved-action"
fi

if bash scripts/01.harness/run-governed-script.sh --approved-action scripts/shared/chat/ensure-llm-workbench-repo.sh --dry-run >"$TMP_ROOT/workbench-retired.out" 2>&1; then
  fail "retired workbench helper was still accepted"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh --dry-run)"
if [ "$OUT" != "canonical-workbench:--dry-run" ]; then
  fail "canonical workbench helper did not run through the governed runner: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/shared/chat/request-initialization/auto-start-missing-session.sh "new chat" >"$TMP_ROOT/auto-start-missing.out" 2>&1; then
  fail "auto-start helper ran without --approved-action"
fi

if bash scripts/01.harness/run-governed-script.sh --approved-action scripts/shared/chat/request-initialization/auto-start-missing-session.sh "new chat" >"$TMP_ROOT/auto-start-retired.out" 2>&1; then
  fail "retired auto-start helper was still accepted"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/auto-start-missing-session/script.sh "new chat")"
if [ "$OUT" != "canonical-auto-start:new chat" ]; then
  fail "canonical auto-start helper did not run with --approved-action: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/00.chat/startup/resolve-current-chat-session/script.sh "new chat" >"$TMP_ROOT/resolve-missing.out" 2>&1; then
  fail "startup resolver ran without --approved-action"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/resolve-current-chat-session/script.sh "new chat")"
if [ "$OUT" != "canonical-resolve-session:new chat" ]; then
  fail "startup resolver did not run with --approved-action: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/shared/chat/rename-current-chat-log-folder.sh test >"$TMP_ROOT/approved-missing.out" 2>&1; then
  fail "approval-sensitive script ran without --approved-action"
fi

if bash scripts/01.harness/run-governed-script.sh --approved-action scripts/shared/chat/rename-current-chat-log-folder.sh test >"$TMP_ROOT/rename-retired.out" 2>&1; then
  fail "retired rename helper was still accepted"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh test)"
if [ "$OUT" != "canonical-approved-action:test" ]; then
  fail "canonical approval-sensitive script did not run with --approved-action: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/02.rag-rulebook/run-local-service/smoke-test.sh >"$TMP_ROOT/rag-smoke-missing.out" 2>&1; then
  fail "RAG service smoke test ran without --approved-action"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/run-local-service/smoke-test.sh)"
if [ "$OUT" != "canonical-rag-smoke:" ]; then
  fail "canonical RAG service smoke test did not run through the governed runner: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --apply >"$TMP_ROOT/dangerous.out" 2>&1; then
  fail "dangerous helper was allowed"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/local/not-governed.sh >"$TMP_ROOT/local.out" 2>&1; then
  fail "non-shared local script was allowed"
fi

if bash scripts/01.harness/run-governed-script.sh ../scripts/shared/git/check-write-location.sh >"$TMP_ROOT/traversal.out" 2>&1; then
  fail "parent traversal path was allowed"
fi

if bash scripts/01.harness/run-governed-script.sh /bin/echo >"$TMP_ROOT/absolute.out" 2>&1; then
  fail "absolute command path was allowed"
fi

LIST="$(bash scripts/01.harness/run-governed-script.sh --list)"
for style in block inline; do
  for effect in destructive aws-mutation push history-rewrite overwrites cloud database network-extra; do
    path="scripts/01.harness/blocked-$style-$effect.sh"
    [[ "$LIST" != *"$path"* ]] || fail "listed forbidden $style/$effect"
    if bash scripts/01.harness/run-governed-script.sh --approved-action "$path" >"$TMP_ROOT/blocked.out" 2>&1; then
      fail "explicit approval bypassed forbidden $style/$effect"
    fi
    [[ "$(<"$TMP_ROOT/blocked.out")" != *"blocked-$style-$effect:"* ]] || fail "rejected child executed"
  done
  for effect in writes-files stages-files commits branches worktrees network; do
    path="scripts/01.harness/approved-$style-$effect.sh"
    [[ "$LIST" == *"approved $path"* ]] || fail "lost mixed read-only/$style/$effect classification"
    if bash scripts/01.harness/run-governed-script.sh "$path" >"$TMP_ROOT/approved.out" 2>&1; then
      fail "mixed $style/$effect ran without approval"
    fi
    OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action "$path")"
    [ "$OUT" = "approved-$style-$effect:" ] || fail "approved $style/$effect did not execute"
  done
  OUT="$(bash scripts/01.harness/run-governed-script.sh "scripts/01.harness/read-only-$style.sh")"
  [ "$OUT" = "read-only-$style:" ] || fail "unrelated lists altered $style read-only approval"
done
[[ "$LIST" == *"approved scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh"* ]] || fail "lost governed refresh exception"
OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh)"
[ "$OUT" = refresh: ] || fail "approved refresh did not execute"

# A later invocation must read changed effects, not reuse a previous decision.
make_fixture "scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh" "refresh" "destructive aws-mutation" inline
if bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh >"$TMP_ROOT/changed.out" 2>&1; then
  fail "reused stale permission metadata"
fi
for declaration in 'effects: []' 'effects: read-only' 'effects: [read-only, {invalid: shape}]' 'effects: [read-only' 'effects: [read-only]\n#   effects: [writes-files]' 'unrelated: [read-only]'; do
  printf '# agentic-artifact:\n#   kind: script\n#   %b\n\necho invalid-child-executed\n' "$declaration" > scripts/01.harness/invalid.sh
  if output="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/invalid.sh 2>&1)"; then
    fail "invalid effects were accepted"
  else
    [ "$?" -eq 1 ] || fail "invalid effects lost policy rejection"
  fi
  [[ "$output" == *"metadata or effects are missing, invalid or unknown"* && "$output" != *invalid-child-executed* ]] || fail "invalid metadata executed or lost reason"
done
case "$LIST" in
  *"always scripts/00.chat/worktree/check-write-location/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical always entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical workbench entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/00.chat/startup/resolve-current-chat-session/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical startup resolver entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/00.chat/startup/auto-start-missing-session/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical auto-start entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical approved entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/02.rag-rulebook/run-local-service/smoke-test.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical RAG smoke test entry"
    ;;
esac

case "$LIST" in
  *"scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"*)
    fail "--list output included never-persistent destructive helper"
    ;;
esac

export REAL_GIT="$(command -v git)" REAL_PYTHON="$(command -v python3)"
mkdir "$TMP_ROOT/fault-bin"
for command in git python3; do
  printf '#!/usr/bin/env bash\ncommand=%q\n' "$command" > "$TMP_ROOT/fault-bin/$command"
  cat >> "$TMP_ROOT/fault-bin/$command" <<'EOF'
fault=no
if [ "$command" = python3 ] && [ -n "${READ_COUNTER:-}" ]; then
  printf '%s\n' "${3:-}" >> "$READ_COUNTER"
fi
case "$FAULT:$command:${1:-}" in
  root:git:rev-parse|inventory:git:ls-files|metadata:python3:-B)
    fault=yes ;;
esac
if [ "$fault" = yes ]; then
  echo private-governance-canary@example.invalid >&2
  exit 77
fi
case "$command" in
  git) exec "$REAL_GIT" "$@" ;;
  python3) exec "$REAL_PYTHON" "$@" ;;
esac
EOF
  chmod +x "$TMP_ROOT/fault-bin/$command"
done
for mode in run list; do
  for stage in root inventory metadata; do
    [ "$mode:$stage" != run:inventory ] || continue
    args=(scripts/00.chat/worktree/check-write-location/script.sh)
    [ "$mode" != list ] || args=(--list)
    if failure="$(PATH="$TMP_ROOT/fault-bin:$PATH" FAULT="$stage" bash scripts/01.harness/run-governed-script.sh "${args[@]}" 2>&1)"; then
      fail "$mode accepted failed $stage observation"
    else
      [ "$?" -eq 2 ] || fail "$mode $stage read failure became policy rejection"
    fi
    expected="$stage"
    [[ "$failure" == *"governed-$expected-read-failed"* && "$failure" != *private-governance-canary* && "$failure" != *canonical-check:* ]] || fail "$mode lost exact read reason or executed child"
  done
done

PATH="$TMP_ROOT/fault-bin:$PATH" FAULT=none READ_COUNTER="$TMP_ROOT/reads" \
  bash scripts/01.harness/run-governed-script.sh scripts/00.chat/worktree/check-write-location/script.sh > "$TMP_ROOT/count.out"
[[ "$(<"$TMP_ROOT/reads")" == scripts/00.chat/worktree/check-write-location/script.sh ]] || fail "permission classification parsed metadata more than once"

taxonomy=.agentic/01.harness/artifact-metadata/taxonomy.yml
portable_taxonomy=scripts/01.harness/artifact-metadata/taxonomy.yml
mv "$taxonomy" "$portable_taxonomy"
OUT="$(bash scripts/01.harness/run-governed-script.sh scripts/00.chat/worktree/check-write-location/script.sh)"
[ "$OUT" = canonical-check: ] || fail "portable taxonomy could not classify the same script"
mv "$portable_taxonomy" "$TMP_ROOT/taxonomy.yml"
for availability in missing unsupported; do
  if [ "$availability" = unsupported ]; then
    sed 's/#   version: 2/#   version: 999/' "$TMP_ROOT/taxonomy.yml" > "$portable_taxonomy"
  fi
  if output="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/worktree/check-write-location/script.sh 2>&1)"; then
    fail "$availability taxonomy permitted execution"
  else
    [ "$?" -eq 2 ] || fail "$availability taxonomy lost observation-failure status"
  fi
  [[ "$output" == *governed-metadata-read-failed* && "$output" != *canonical-check:* ]] || fail "$availability taxonomy executed child or lost reason"
done

echo "governed script runner smoke test passed"
