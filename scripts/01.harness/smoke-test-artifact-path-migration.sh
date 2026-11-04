#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.smoke-test-artifact-path-migration
#   version: 1
#   status: active
#   created_on: "2026-06-20"
#   updated_on: "2026-10-31"
#   layer: 01.harness
#   domain: migration
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test artifact path migration planning and validation helpers.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: harness.workflows.migrate-artifact-paths
#     path: .agentic/01.harness/workflows/migrate-artifact-paths.md
#   - id: harness.script.plan-artifact-path-migration
#     path: scripts/01.harness/plan-artifact-path-migration.sh
#   - id: harness.script.check-artifact-path-migration
#     path: scripts/01.harness/check-artifact-path-migration.sh
#   effects:
#   - read-only
#   - writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q

mkdir -p \
  "$REPO/.agentic/01.harness/workflows" \
  "$REPO/.agentic/02.rag-rulebook/retirements/example" \
  "$REPO/.agentic/harness-renamed/plans/migration" \
  "$REPO/scripts/01.harness" \
  "$REPO/docs/00.chat/bootstrap" \
  "$REPO/commitLogs/2026/jun/20/example"

cat > "$REPO/AGENTS.md" <<'EOF'
Use .agentic/01.harness/workflows/change-harness.md. PRIVATE_MIGRATION_SOURCE_CANARY
EOF

cat > "$REPO/.agentic/01.harness/workflows/change-harness.md" <<'EOF'
Consult .agentic/01.harness/standards/example.md.
EOF

cat > "$REPO/.agentic/harness-renamed/plans/migration/example.md" <<'EOF'
Migrate .agentic/01.harness to .agentic/harness-renamed.
EOF

cat > "$REPO/scripts/01.harness/example.sh" <<'EOF'
#!/usr/bin/env bash
echo .agentic/01.harness
EOF

cat > "$REPO/docs/00.chat/bootstrap/example.md" <<'EOF'
Bootstrap .agentic/01.harness.
EOF

cat > "$REPO/commitLogs/2026/jun/20/example/README.md" <<'EOF'
workflow: .agentic/01.harness/workflows/change-harness.md
EOF

(
  cd "$REPO"
  PLAN_OUTPUT="$(bash "$SOURCE_ROOT/scripts/01.harness/plan-artifact-path-migration.sh" .agentic/01.harness .agentic/harness-renamed)"

  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^old_path=.agentic/01.harness$' || fail "plan missing old path"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[routing\]$' || fail "plan missing routing bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[workflow\]$' || fail "plan missing workflow bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[migration-plan\]$' || fail "plan missing migration-plan bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[script\]$' || fail "plan missing script bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[bootstrap\]$' || fail "plan missing bootstrap bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[session-history\]$' || fail "plan missing session-history bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^  Use .agentic/01.harness/workflows/change-harness.md. PRIVATE_MIGRATION_SOURCE_CANARY$' || fail "planner changed intentional matched source inventory"

  if bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/check.out" 2>"$TMP_ROOT/check.err"; then
    fail "checker allowed active old-path references without compatibility approval"
  fi

  grep -q 'active old-path references remain' "$TMP_ROOT/check.err" || fail "checker failure did not explain active references"
  grep -q '^AGENTS.md:1$' "$TMP_ROOT/check.err" || fail "checker dropped accepted finding location"
  if grep -q 'PRIVATE_MIGRATION_SOURCE_CANARY\|Use .agentic' "$TMP_ROOT/check.err"; then
    fail "checker disclosed matched source text"
  fi

  bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" --allow-active-old-path .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/allow.out"
  grep -q '^artifact_path_migration_check=ok$' "$TMP_ROOT/allow.out" || fail "checker did not pass with explicit compatibility approval"

  sed -i 's#\.agentic/01\.harness#\.agentic/harness-renamed#g' \
    AGENTS.md \
    .agentic/01.harness/workflows/change-harness.md \
    scripts/01.harness/example.sh \
    docs/00.chat/bootstrap/example.md

  cat > .agentic/02.rag-rulebook/retirements/example/retired-path.yml <<'EOF'
schema: rag-rulebook/retirement-record/v1
retired_artifacts:
  - path: .agentic/01.harness
EOF

  if bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/plan-missing.out" 2>"$TMP_ROOT/plan-missing.err"; then
    fail "checker allowed migration-plan old-path references without an explicit plan path"
  fi

  bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" \
    --plan .agentic/harness-renamed/plans/migration/example.md \
    .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/plan.out"
  grep -q '^plan_path=.agentic/harness-renamed/plans/migration/example.md$' "$TMP_ROOT/plan.out" || fail "checker did not report plan path"
  grep -q '^active_old_refs=none$' "$TMP_ROOT/plan.out" || fail "checker did not ignore explicit plan evidence"
)

# Exercise the actual commands with only disposable Git/grep/sort ports replaced.
# Successful planner source inventory above is intentional data, not a failure stream.
FAKE_BIN="$TMP_ROOT/bin"
mkdir -p "$FAKE_BIN"
MIGRATION_REAL_GIT="$(command -v git)"
MIGRATION_REAL_GREP="$(command -v grep)"
MIGRATION_REAL_SORT="$(command -v sort)"
export MIGRATION_REAL_GIT MIGRATION_REAL_GREP MIGRATION_REAL_SORT

cat > "$FAKE_BIN/git" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$MIGRATION_GIT_CALLS"
if [ "$*" = 'rev-parse --show-toplevel' ]; then
  case "$MIGRATION_MODE" in
    root-native) echo 'PRIVATE_MIGRATION_NATIVE_CANARY' >&2; exit 71 ;;
    root-access) printf '%s\n' "$MIGRATION_MISSING_ROOT"; exit 0 ;;
  esac
fi
if [ "$1" = ls-files ]; then
  case "$MIGRATION_MODE:$#" in
    tracked-native:1|untracked-native:3)
      printf '%s\n' AGENTS.md
      echo 'PRIVATE_MIGRATION_NATIVE_CANARY' >&2
      exit 73
      ;;
    empty:*) exit 0 ;;
  esac
fi
exec "$MIGRATION_REAL_GIT" "$@"
EOF
cat > "$FAKE_BIN/grep" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$MIGRATION_GREP_CALLS"
if [ "$MIGRATION_MODE" = read-native ] ||
   { [ "$MIGRATION_MODE" = new-read-native ] && [ "$2" = .agentic/harness-renamed ]; }; then
  printf '%s\n' '1:PRIVATE_MIGRATION_NATIVE_CANARY'
  echo 'PRIVATE_MIGRATION_NATIVE_CANARY' >&2
  exit 2
fi
exec "$MIGRATION_REAL_GREP" "$@"
EOF
cat > "$FAKE_BIN/sort" <<'EOF'
#!/usr/bin/env bash
if [ "$MIGRATION_MODE" = sort-native ]; then
  # Consume the enumeration before rejecting its reduction; no provider calls.
  while IFS= read -r line; do :; done
  echo 'PRIVATE_MIGRATION_NATIVE_CANARY' >&2
  exit 74
fi
exec "$MIGRATION_REAL_SORT" "$@"
EOF
chmod +x "$FAKE_BIN/git" "$FAKE_BIN/grep" "$FAKE_BIN/sort"

migration_command() {
  local script="$1" mode="$2"
  shift 2
  : > "$TMP_ROOT/git.calls"
  : > "$TMP_ROOT/grep.calls"
  (
    cd "$REPO"
    PATH="$FAKE_BIN:$PATH" \
      MIGRATION_MODE="$mode" \
      MIGRATION_GIT_CALLS="$TMP_ROOT/git.calls" \
      MIGRATION_GREP_CALLS="$TMP_ROOT/grep.calls" \
      MIGRATION_MISSING_ROOT="$TMP_ROOT/PRIVATE_MIGRATION_NATIVE_CANARY" \
      bash "$SOURCE_ROOT/scripts/01.harness/$script" "$@"
  ) > "$TMP_ROOT/command.out" 2> "$TMP_ROOT/command.err"
}

assert_failure() {
  local script="$1" mode="$2" expected_status="$3" concern="$4" status
  shift 4
  if migration_command "$script" "$mode" "$@"; then
    fail "migration command accepted an unavailable observation"
  else
    status=$?
  fi
  [ "$status" -eq "$expected_status" ] || fail "migration command changed expected failure status"
  grep -Fxq "ERROR: $concern" "$TMP_ROOT/command.err" || fail "migration command lost exact owned concern"
  if grep -q 'PRIVATE_MIGRATION_NATIVE_CANARY\|PRIVATE_MIGRATION_REJECTED_CANARY' "$TMP_ROOT/command.out" "$TMP_ROOT/command.err"; then
    fail "migration command disclosed native or rejected evidence"
  fi
  if grep -q 'active_old_refs=none\|references=0\|artifact_path_migration_check=ok' "$TMP_ROOT/command.out"; then
    fail "unavailable migration observation became absence or success"
  fi
}

EXPECTED_ENUMERATION=$'rev-parse --show-toplevel\nls-files\nls-files --others --exclude-standard'
read -r EXPECTED_FIRST_FILE < <(
  {
    "$MIGRATION_REAL_GIT" -C "$REPO" ls-files
    "$MIGRATION_REAL_GIT" -C "$REPO" ls-files --others --exclude-standard
  } | "$MIGRATION_REAL_SORT" -u
)
for script in check-artifact-path-migration.sh plan-artifact-path-migration.sh; do
  assert_failure "$script" root-native 71 artifact-path-migration-repository-observation-unavailable .agentic/01.harness .agentic/harness-renamed
  [ "$(< "$TMP_ROOT/git.calls")" = 'rev-parse --show-toplevel' ] || fail "repository failure changed Git calls"

  assert_failure "$script" root-access 1 artifact-path-migration-repository-access-unavailable .agentic/01.harness .agentic/harness-renamed
  [ "$(< "$TMP_ROOT/git.calls")" = 'rev-parse --show-toplevel' ] || fail "repository access failure added Git calls"

  for mode in tracked-native untracked-native sort-native; do
    assert_failure "$script" "$mode" 1 artifact-path-migration-enumeration-unavailable .agentic/01.harness .agentic/harness-renamed
    [ "$(< "$TMP_ROOT/git.calls")" = "$EXPECTED_ENUMERATION" ] || fail "enumeration failure changed Git call order/count"
    [ ! -s "$TMP_ROOT/grep.calls" ] || fail "enumeration failure entered file reads"
  done

  assert_failure "$script" read-native 1 artifact-path-migration-reference-read-unavailable .agentic/01.harness .agentic/harness-renamed
  [ "$(< "$TMP_ROOT/git.calls")" = "$EXPECTED_ENUMERATION" ] || fail "read failure changed Git call order/count"
  [ "$(< "$TMP_ROOT/grep.calls")" = "-nF .agentic/01.harness $EXPECTED_FIRST_FILE" ] || fail "read failure did not stop at first attempted file"

  migration_command "$script" normal .agentic/no-existing-reference .agentic/no-new-reference || fail "legitimate grep no-match became failure"
  [ ! -s "$TMP_ROOT/command.err" ] || fail "no-match emitted failure diagnostics"
  if [ "$script" = check-artifact-path-migration.sh ]; then
    grep -Fxq 'active_old_refs=none' "$TMP_ROOT/command.out" || fail "checker lost known no-match"
    [ "$(< "$TMP_ROOT/git.calls")" = "$EXPECTED_ENUMERATION" ] || fail "checker added enumeration calls"
  else
    [ "$(grep -c '^references=0$' "$TMP_ROOT/command.out")" -eq 2 ] || fail "planner lost known no-match inventory"
    [ "$(< "$TMP_ROOT/git.calls")" = "$EXPECTED_ENUMERATION"$'\nls-files\nls-files --others --exclude-standard' ] || fail "planner changed two-query enumeration calls"
  fi

  migration_command "$script" empty .agentic/no-existing-reference .agentic/no-new-reference || fail "empty successful enumeration became unavailable"
  [ ! -s "$TMP_ROOT/grep.calls" ] || fail "empty enumeration invented a file read"
  [ ! -s "$TMP_ROOT/command.err" ] || fail "empty enumeration emitted diagnostics"
done

assert_failure check-artifact-path-migration.sh normal 2 artifact-path-migration-plan-not-file \
  --plan "$TMP_ROOT/PRIVATE_MIGRATION_REJECTED_CANARY" .agentic/01.harness .agentic/harness-renamed
[ "$(< "$TMP_ROOT/git.calls")" = 'rev-parse --show-toplevel' ] || fail "rejected plan changed first-guard call order"

# A failed new-path query cannot erase the already completed old-path inventory.
assert_failure plan-artifact-path-migration.sh new-read-native 1 artifact-path-migration-reference-read-unavailable \
  .agentic/01.harness .agentic/harness-renamed
grep -Fxq 'Old path references' "$TMP_ROOT/command.out" || fail "later failure erased completed inventory"
grep -q '^references=[1-9]' "$TMP_ROOT/command.out" || fail "later failure erased known old-path references"
[ "$(< "$TMP_ROOT/git.calls")" = "$EXPECTED_ENUMERATION"$'\nls-files\nls-files --others --exclude-standard' ] || fail "new-query failure changed Git calls"

echo "OK: artifact path migration helpers smoke test passed."
