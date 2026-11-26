#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.smoke-test-artifact-path-migration
#   version: 4
#   status: active
#   created_on: "2026-06-20"
#   updated_on: "2026-11-26"
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
  "$REPO/.agentic/02.rag-rulebook/recognition-sources/generated" \
  "$REPO/.agentic/02.rag-rulebook/retirements/example" \
  "$REPO/.agentic/harness-renamed/plans/migration" \
  "$REPO/infra/04.deploy/03.product/targets/example/20-scopes/example/30-release-evidence/proof-receipts" \
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

  cat > .agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml <<'EOF'
historical_evidence_path: .agentic/01.harness
EOF

  cat > infra/04.deploy/03.product/targets/example/20-scopes/example/30-release-evidence/proof-receipts/accepted.json <<'EOF'
{"historical_source_path":".agentic/01.harness"}
EOF

  if bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/plan-missing.out" 2>"$TMP_ROOT/plan-missing.err"; then
    fail "checker allowed migration-plan old-path references without an explicit plan path"
  fi

  bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" \
    --plan .agentic/harness-renamed/plans/migration/example.md \
    .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/plan.out"
  grep -q '^plan_path=.agentic/harness-renamed/plans/migration/example.md$' "$TMP_ROOT/plan.out" || fail "checker did not report plan path"
  grep -q '^active_old_refs=none$' "$TMP_ROOT/plan.out" || fail "checker did not ignore explicit plan evidence"

  cat > infra/04.deploy/03.product/targets/example/20-scopes/example/30-release-evidence/current-accepted-release.yml <<'EOF'
current_source_path: .agentic/01.harness
EOF
  if bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" \
    --plan .agentic/harness-renamed/plans/migration/example.md \
    .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/current-release.out" 2>"$TMP_ROOT/current-release.err"; then
    fail "checker treated the active current-release pointer as historical evidence"
  fi
  grep -q '^infra/04.deploy/03.product/targets/example/20-scopes/example/30-release-evidence/current-accepted-release.yml:1$' "$TMP_ROOT/current-release.err" || fail "checker dropped current-release finding location"
  sed -i 's#\.agentic/01\.harness#\.agentic/harness-renamed#g' infra/04.deploy/03.product/targets/example/20-scopes/example/30-release-evidence/current-accepted-release.yml

  cat > scripts/01.harness/active-old-path.sh <<'EOF'
#!/usr/bin/env bash
echo .agentic/01.harness
EOF
  if bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" \
    --plan .agentic/harness-renamed/plans/migration/example.md \
    .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/active-script.out" 2>"$TMP_ROOT/active-script.err"; then
    fail "checker treated an active script reference as historical evidence"
  fi
  grep -q '^scripts/01.harness/active-old-path.sh:2$' "$TMP_ROOT/active-script.err" || fail "checker dropped active script finding location"
  sed -i 's#\.agentic/01\.harness#\.agentic/harness-renamed#g' scripts/01.harness/active-old-path.sh

  bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" \
    --plan .agentic/harness-renamed/plans/migration/example.md \
    .agentic/01.harness .agentic/harness-renamed >"$TMP_ROOT/historical.out"
  grep -q '^active_old_refs=none$' "$TMP_ROOT/historical.out" || fail "checker did not retain only historical evidence"

  # Cross a search batch, preserve literal punctuation/whitespace paths and
  # every matching line, and bound giant generated-line excerpts.
  for ((index=0; index<260; index++)); do
    printf 'unrelated\n' > "docs/neutral-$index.txt"
  done
  printf 'docs/a[1].md\ndocs/a[1].md and docs/a[1].md\ndocs/a11.md\n' > 'docs/zz file:12:literal.md'
  printf '%6000s docs/a[1].md\n' '' > 'docs/zz long.md'
  bash "$SOURCE_ROOT/scripts/01.harness/plan-artifact-path-migration.sh" 'docs/a[1].md' docs/renamed.md > "$TMP_ROOT/batch.out"
  grep -Fxq 'references=3' "$TMP_ROOT/batch.out" || fail "batch scanner changed literal matching-line counts"
  grep -Fxq 'docs/zz file:12:literal.md:2' "$TMP_ROOT/batch.out" || fail "batch scanner lost literal filename or line location"
  grep -q '\[excerpt truncated\]' "$TMP_ROOT/batch.out" || fail "planner did not mark a shortened source excerpt"
  [ "$(wc -c < "$TMP_ROOT/batch.out")" -lt 3000 ] || fail "planner retained an unbounded generated line"
  if bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" 'docs/a[1].md' docs/renamed.md > "$TMP_ROOT/batch-check.out" 2> "$TMP_ROOT/batch-check.err"; then
    fail "checker lost active references across a batch"
  fi
  grep -Fxq 'docs/zz file:12:literal.md:2' "$TMP_ROOT/batch-check.err" || fail "checker lost exact batch match location"
  grep -Fxq 'docs/zz long.md:1' "$TMP_ROOT/batch-check.err" || fail "checker omitted a giant matching line"
)

# Historical fields must not exempt current instructions in the same documents.
MIGRATION_SOURCE_ROOT="$SOURCE_ROOT" MIGRATION_FIXTURE_ROOT="$REPO" python3 -B - <<'PY'
import os
from pathlib import Path
import subprocess

root = Path(os.environ['MIGRATION_FIXTURE_ROOT'])
scripts = Path(os.environ['MIGRATION_SOURCE_ROOT']) / 'scripts/01.harness'
old, new = 'example/old/', 'example/new/'
def header(kind, layer, markdown=True):
    fields = f'schema: agentic-artifact/v3\ncreated_on: "2026-01-01"\nkind: {kind}\nlayer: {layer}\n'
    return '<!-- agentic-artifact:\n' + fields + '-->\n' if markdown else '# agentic-artifact:\n' + ''.join('#   ' + line + '\n' for line in fields.splitlines())
course = header('guide', '05.education') + 'The frozen inventory is recorded in this frozen course inventory.\n<!-- course-file: example/old/a.sh -->\n<!-- course-source-sha256: before=absent after=' + 'a' * 64 + ' -->\n- [ ] [example/old/a.sh](example/new/a.sh) — modified; before `aaaaaaaaaaaa`, snapshot `bbbbbbbbbbbb`.\n'
derivation = header('derivation-report', '02.rag-rulebook', False) + '''schema: rag-rulebook/source-to-rule-derivation-report/v1
semantic_review:
  source_claims:
    - evidence_path: example/old/a.sh
validation:
  required_checks: ['bash example/old/a.sh']
  checks_run:
    - command: bash example/old/a.sh
      result: passed
  checks_pending: []
'''
review = header('review-record', '02.rag-rulebook', False) + 'schema: rag-rulebook/okf-source-material-review/v1\nstatus: accepted\nsource_material:\n  sha256: ' + 'a' * 64 + '\niterations:\n  - reviewer_assessments:\n      - evidence: [example/old/a.sh]\n'
plan = header('plan', '06.shared') + 'Historical task paths (completed work; not current instructions):\n\n```text\nexample/old/a.sh\n```\n'
documents = {
    'docs/education/history.md': course,
    '.agentic/02.rag-rulebook/derivation-reports/example/2026-01-01-record.yml': derivation,
    '.agentic/02.rag-rulebook/source-material-reviews/example/2026-01-01-record.yml': review,
    '.agentic/shared/plans/implementation/history.md': plan,
}
for name, content in documents.items():
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
def run(script, env=None, needle=old):
    return subprocess.run(['bash', str(scripts / script), needle, new], cwd=root, text=True, capture_output=True, env=env)
accepted = run('check-artifact-path-migration.sh')
assert accepted.returncode == 0 and 'active_old_refs=none' in accepted.stdout, accepted.stderr
inventory = run('plan-artifact-path-migration.sh')
assert inventory.returncode == 0 and 'references=7' in inventory.stdout and '[session-history]' in inventory.stdout, inventory.stdout + inventory.stderr
old_inventory = inventory.stdout.split('New path references', 1)[0]
assert '[workflow]' not in old_inventory and '[other]' not in old_inventory, old_inventory
for name, content in documents.items():
    for line, value in enumerate(content.splitlines(), 1):
        if old in value:
            assert f'{name}:{line}\n' in inventory.stdout, (name, line)
education, derivation_path, review_path, plan_path = documents
rejections = [
    (education, course + 'Run bash example/old/a.sh\n'),
    (education, course + '[Current script](example/old/a.sh)\n'),
    (education, course.replace('(example/new/a.sh)', '(example/old/a.sh)')),
    (education, course.replace('course-source-sha256:', 'unverified-source:')),
    (education, course.replace('05.education', '01.harness')),
    (education, course.replace('kind: guide', 'kind: guide\nkind: guide')),
    (education, course.replace('<!-- course-file:', '```bash\n<!-- course-file:').replace(' -->\n- [ ]', ' -->\n```\n- [ ]')),
    (education, course.replace('<!-- course-file:', '~~~~\n```bash\n<!-- course-file:')),
    (derivation_path, derivation.replace('result: passed', 'result: failed')),
    (derivation_path, derivation.replace('checks_pending: []', 'checks_pending: [awaiting-proof]')),
    (derivation_path, derivation + 'current_command: bash example/old/a.sh\n'),
    (derivation_path, derivation.replace('evidence_path: example/old/a.sh', '{evidence_path: example/old/a.sh, current_command: example/old/a.sh}')),
    (derivation_path, derivation.replace('source-to-rule-derivation-report/v1', 'unknown/v1')),
    (derivation_path, derivation.replace('result: passed', 'result: passed\n      result: passed')),
    (derivation_path, derivation + 'unknown: [unterminated\n'),
    (derivation_path, derivation.replace('evidence_path: example/old/a.sh', 'evidence_path: &old example/old/a.sh') + 'current_command: *old\n'),
    (review_path, review.replace('status: accepted', 'status: pending')),
    (review_path, review.replace('a' * 64, 'unverified')),
    (plan_path, plan.replace('Historical task paths (completed work; not current instructions):', 'Task paths for parent review:')),
    (plan_path, plan.replace('example/old/a.sh', 'bash example/old/a.sh')),
    (plan_path, plan + 'Run bash example/old/a.sh\n'),
]
for name, content in rejections:
    (root / name).write_text(content)
    rejected = run('check-artifact-path-migration.sh')
    assert rejected.returncode == 1 and 'active old-path references remain' in rejected.stderr, (name, rejected.stdout, rejected.stderr)
    (root / name).write_text(documents[name])
snapshot_name = 'docs/04.deploy/plans/verification-diagnostics-timeout-inventory.tsv'
snapshot = root / snapshot_name
snapshot.parent.mkdir(parents=True, exist_ok=True)
snapshot_needle = 'scripts/04.deploy/'
counterfeit = ('category\tpath_or_id\tdetails\ncurrent\t' + snapshot_needle + 'active.sh\trun now\n').encode()
snapshot.write_bytes(counterfeit)
rejected = run('check-artifact-path-migration.sh', needle=snapshot_needle)
assert rejected.returncode == 1 and snapshot_name + ':2' in rejected.stderr, rejected.stderr
# Source-only audit data is not shipped in portable harness exports.
original_snapshot = scripts.parents[1] / snapshot_name
if original_snapshot.is_file():
    original = original_snapshot.read_bytes()
    snapshot.write_bytes(original)
    accepted = run('check-artifact-path-migration.sh', needle=snapshot_needle)
    assert accepted.returncode == 0 and 'active_old_refs=none' in accepted.stdout, accepted.stderr
    inventory = run('plan-artifact-path-migration.sh', needle=snapshot_needle)
    snapshot_inventory = inventory.stdout.split('New path references', 1)[0]
    assert inventory.returncode == 0 and '[session-history]' in snapshot_inventory and '[other]' not in snapshot_inventory, inventory.stdout + inventory.stderr
    for number, line in enumerate(original.decode().splitlines(), 1):
        if snapshot_needle in line:
            assert f'{snapshot_name}:{number}\n' in inventory.stdout, number
    for altered in (original + counterfeit, original.replace(b'registered-check', b'current-command', 1)):
        snapshot.write_bytes(altered)
        rejected = run('check-artifact-path-migration.sh', needle=snapshot_needle)
        assert rejected.returncode == 1 and snapshot_name + ':' in rejected.stderr, rejected.stderr
    snapshot.unlink()
    lookalike = snapshot.with_name('current-inventory.tsv')
    lookalike.write_bytes(original)
    rejected = run('check-artifact-path-migration.sh', needle=snapshot_needle)
    assert rejected.returncode == 1 and 'current-inventory.tsv:' in rejected.stderr, rejected.stderr
    lookalike.unlink()
    print('OK: exact frozen audit snapshot retained with all planner line locations; changed, appended and lookalike snapshots rejected.')
else:
    snapshot.unlink()
    print('OK: counterfeit audit snapshot rejected; original source-only snapshot is not present in this export.')
bin_dir = root.parent / 'history-bin'
bin_dir.mkdir()
port = bin_dir / 'python3'
port.write_text('#!/bin/sh\necho PRIVATE_HISTORY_NATIVE_CANARY >&2\nexit 77\n')
port.chmod(0o755)
for script in ('check-artifact-path-migration.sh', 'plan-artifact-path-migration.sh'):
    unavailable = run(script, dict(os.environ, PATH=str(bin_dir) + ':' + os.environ['PATH']))
    assert unavailable.returncode == 1 and unavailable.stderr == 'ERROR: artifact-path-migration-history-observation-unavailable\n', unavailable.stderr
    assert 'PRIVATE_HISTORY_NATIVE_CANARY' not in unavailable.stdout
    assert 'active_old_refs=none' not in unavailable.stdout and 'references=0' not in unavailable.stdout
print('OK: seven exact historical references retained; twenty-one active/malformed variants rejected; parser failures observed safely.')
PY

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
   { [ "$MIGRATION_MODE" = matched-read-native ] && [ "$1" = -nF ]; } ||
   { [ "$MIGRATION_MODE" = new-read-native ] && [ "$3" = .agentic/harness-renamed ]; }; then
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
  [ "$(wc -l < "$TMP_ROOT/grep.calls")" -eq 1 ] || fail "read failure did not stop at first attempted batch"
  grep -q '^-lF -- .agentic/01.harness ' "$TMP_ROOT/grep.calls" || fail "batch scan changed literal query"

  assert_failure "$script" matched-read-native 1 artifact-path-migration-reference-read-unavailable .agentic/01.harness .agentic/harness-renamed
  [ "$(< "$TMP_ROOT/git.calls")" = "$EXPECTED_ENUMERATION" ] || fail "matched-file failure changed enumeration calls"
  [ "$(wc -l < "$TMP_ROOT/grep.calls")" -eq 2 ] || fail "matched-file failure did not stop after first full read"
  grep -q '^-nF -- .agentic/01.harness ' "$TMP_ROOT/grep.calls" || fail "positive candidate skipped its full read"

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
