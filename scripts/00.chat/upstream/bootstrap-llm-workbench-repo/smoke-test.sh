#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.upstream.bootstrap-llm-workbench-repo.smoke-test
#   version: 2
#   status: active
#   created_on: "2026-06-20"
#   updated_on: "2026-10-20"
#   layer: 00.chat
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test the llm-workbench bootstrap dry-run planner.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.upstream.bootstrap-llm-workbench-repo.readme
#     path: scripts/00.chat/upstream/bootstrap-llm-workbench-repo/README.md
#   - id: chat.script.bootstrap.audit-chat-bootstrap-file-set
#     path: scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
#   effects:
#   - writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$SOURCE_ROOT/scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/llm-workbench-bootstrap-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

make_repo() {
  local repo="$1"
  mkdir -p "$repo"
  git -C "$repo" init --quiet --initial-branch=main
}

run_plan() {
  local repo="$1"
  local output="$2"
  bash "$SCRIPT" --target "$repo" --dry-run > "$output"
}

run_apply() {
  local repo="$1"
  local output="$2"
  bash "$SCRIPT" --target "$repo" --apply > "$output"
}

EMPTY_REPO="$TMP_ROOT/empty"
make_repo "$EMPTY_REPO"
run_plan "$EMPTY_REPO" "$TMP_ROOT/empty.out"
grep -q '^CREATE package.json$' "$TMP_ROOT/empty.out" || fail "empty repo did not plan package creation"
grep -q '^CREATE scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh$' "$TMP_ROOT/empty.out" || fail "empty repo did not plan upstream planner script"
if grep -q '^CREATE \.agentic/01\.harness/' "$TMP_ROOT/empty.out"; then
  fail "empty repo planned source-maintenance .agentic/01.harness files"
fi
if grep -Eq '^CREATE docs/00\.chat/public-chat-workbench-adrs\.md$|^CREATE docs/00\.chat/adrs/' "$TMP_ROOT/empty.out"; then
  fail "empty repo planned public ADR export files"
fi
grep -q '^conflicts: 0$' "$TMP_ROOT/empty.out" || fail "empty repo reported conflicts"
run_apply "$EMPTY_REPO" "$TMP_ROOT/empty-apply.out"
test -f "$EMPTY_REPO/AGENTS.md" || fail "apply did not create AGENTS.md"
test -f "$EMPTY_REPO/package.json" || fail "apply did not create package.json"
test -f "$EMPTY_REPO/scripts/01.harness/artifact-metadata/header_discovery.py" || fail "apply did not include shared header discovery"
test -f "$EMPTY_REPO/scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh" || fail "apply did not create planner script"
test ! -e "$EMPTY_REPO/.agentic/01.harness" || fail "apply created source-maintenance .agentic/01.harness"
test ! -e "$EMPTY_REPO/docs/00.chat/public-chat-workbench-adrs.md" || fail "apply created public ADR manifest"
test ! -e "$EMPTY_REPO/docs/00.chat/adrs" || fail "apply created ADR docs"
for source_only_path in \
  scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh \
  scripts/01.harness/artifact-metadata/generate-index/script.sh \
  scripts/01.harness/check-artifact-metadata-headers.sh \
  scripts/01.harness/check-artifact-path-migration.sh \
  scripts/01.harness/check-rule-test-taxonomy.sh \
  scripts/01.harness/plan-artifact-path-migration.sh \
  scripts/01.harness/smoke-test-artifact-path-migration.sh; do
  test ! -e "$EMPTY_REPO/$source_only_path" ||
    fail "apply created source-maintenance harness script: $source_only_path"
done
node -e "const p=require(process.argv[1]); if (p.name !== 'llm-workbench') process.exit(1); if (!p.scripts.chat) process.exit(1)" "$EMPTY_REPO/package.json" || fail "created package.json did not match template"

node - "$EMPTY_REPO" <<'NODE'
const fs = require('fs');
const path = require('path');
const today = new Date().toISOString().slice(0, 10);
for (const name of ['scripts/install.sh', 'scripts/uninstall.sh', '.github/workflows/portability.yml']) {
  const file = path.join(process.argv[2], name);
  const text = fs.readFileSync(file, 'utf8');
  for (const expected of ['schema: agentic-artifact/v3', `created_on: "${today}"`, `updated_on: "${today}"`]) {
    if (!text.includes(expected)) throw new Error(`${name} missing ${expected}`);
  }
  if (text.includes('{{ARTIFACT_')) throw new Error(`${name} contains an unrendered lifecycle placeholder`);
  fs.writeFileSync(file, text.replace(`created_on: "${today}"`, 'created_on: "2001-01-01"')
    .replace(`updated_on: "${today}"`, 'updated_on: "2001-01-02"'));
}
NODE
# Copied canonical files can have existing conflicts after portability
# sanitization; template lifecycle idempotence is independent of those.
run_plan "$EMPTY_REPO" "$TMP_ROOT/repeated.out" || :
grep -q '^SAME scripts/install.sh$' "$TMP_ROOT/repeated.out" || fail "repeat plan changed install lifecycle dates"
grep -q '^SAME scripts/uninstall.sh$' "$TMP_ROOT/repeated.out" || fail "repeat plan changed uninstall lifecycle dates"
grep -q '^SAME .github/workflows/portability.yml$' "$TMP_ROOT/repeated.out" || fail "repeat plan changed CI lifecycle dates"
grep -q '^#   updated_on: "2001-01-02"$' "$EMPTY_REPO/scripts/install.sh" || fail "dry run rewrote target dates"
printf '\n# target customization\n' >> "$EMPTY_REPO/scripts/install.sh"
if run_apply "$EMPTY_REPO" "$TMP_ROOT/template-conflict.out"; then
  fail "customized generated script did not conflict"
fi
grep -q '^CONFLICT scripts/install.sh$' "$TMP_ROOT/template-conflict.out" || fail "template conflict was not reported"
grep -q '^# target customization$' "$EMPTY_REPO/scripts/install.sh" || fail "conflicting apply overwrote customization"

# A copied v3 header changed by portability sanitization keeps its creation
# evidence while receiving the date of the actual metadata edit.
LIFECYCLE_SOURCE="$TMP_ROOT/lifecycle-source"
LIFECYCLE_TARGET="$TMP_ROOT/lifecycle-target"
make_repo "$LIFECYCLE_SOURCE"
make_repo "$LIFECYCLE_TARGET"
LIFECYCLE_TEMPLATES="$LIFECYCLE_SOURCE/docs/00.chat/bootstrap/llm-workbench-template/root"
mkdir -p "$LIFECYCLE_TEMPLATES" "$LIFECYCLE_SOURCE/.agentic/00.chat"
printf '{"name":"lifecycle-fixture","scripts":{}}\n' > "$LIFECYCLE_TEMPLATES/package.json.template"
cat > "$LIFECYCLE_SOURCE/.agentic/00.chat/lifecycle.md" <<'EOF'
<!-- agentic-artifact:
schema: agentic-artifact/v3
id: test.bootstrap.lifecycle
version: 1
status: active
created_on: "2001-01-01"
updated_on: "2001-01-02"
used_by:
- id: test.absent
  path: .agentic/01.harness/absent.md
-->
# Lifecycle fixture
EOF
(
  cd "$LIFECYCLE_SOURCE"
  run_apply "$LIFECYCLE_TARGET" "$TMP_ROOT/lifecycle.out"
)
node - "$LIFECYCLE_TARGET/.agentic/00.chat/lifecycle.md" <<'NODE'
const fs = require('fs');
const text = fs.readFileSync(process.argv[2], 'utf8');
const today = new Date().toISOString().slice(0, 10);
if (!text.includes('created_on: "2001-01-01"')) throw new Error('sanitizer reset creation date');
if (!text.includes(`updated_on: "${today}"`)) throw new Error('sanitizer did not stamp update date');
if (text.includes('path: .agentic/01.harness/absent.md')) throw new Error('sanitizer retained missing path');
NODE

PACKAGE_REPO="$TMP_ROOT/package"
make_repo "$PACKAGE_REPO"
cat > "$PACKAGE_REPO/package.json" <<'JSON'
{
  "name": "existing-target",
  "scripts": {
    "build": "echo build"
  },
  "dependencies": {
    "left-pad": "1.3.0"
  }
}
JSON
run_plan "$PACKAGE_REPO" "$TMP_ROOT/package.out"
grep -q '^PACKAGE_ADD_SCRIPT chat ' "$TMP_ROOT/package.out" || fail "existing package did not plan chat script add"
grep -q '^PACKAGE_PRESERVE_SCRIPT build echo build$' "$TMP_ROOT/package.out" || fail "existing package did not preserve unrelated script"
grep -q '^conflicts: 0$' "$TMP_ROOT/package.out" || fail "existing package reported conflicts"
run_apply "$PACKAGE_REPO" "$TMP_ROOT/package-apply.out"
node -e "const p=require(process.argv[1]); if (p.name !== 'existing-target') process.exit(1); if (p.scripts.build !== 'echo build') process.exit(1); if (!p.scripts['chat:new']) process.exit(1); if (!p.dependencies['left-pad']) process.exit(1)" "$PACKAGE_REPO/package.json" || fail "package merge did not preserve existing data and add chat scripts"

PRESERVE_REPO="$TMP_ROOT/preserve"
make_repo "$PRESERVE_REPO"
mkdir -p "$PRESERVE_REPO/scripts/shared/custom"
printf '#!/usr/bin/env bash\n' > "$PRESERVE_REPO/scripts/shared/custom/tool.sh"
run_plan "$PRESERVE_REPO" "$TMP_ROOT/preserve.out"
grep -q '^PRESERVE scripts/shared/custom/tool.sh$' "$TMP_ROOT/preserve.out" || fail "target-owned shared script was not preserved"
grep -q '^conflicts: 0$' "$TMP_ROOT/preserve.out" || fail "preserve repo reported conflicts"
run_apply "$PRESERVE_REPO" "$TMP_ROOT/preserve-apply.out"
test -f "$PRESERVE_REPO/scripts/shared/custom/tool.sh" || fail "apply removed target-owned shared script"
test -f "$PRESERVE_REPO/scripts/01.harness/run-governed-script.sh" || fail "apply did not create shared harness script"
test -f "$PRESERVE_REPO/scripts/01.harness/check-deterministic-process-drift.sh" || fail "apply did not create deterministic drift check"
test ! -e "$PRESERVE_REPO/scripts/01.harness/plan-artifact-path-migration.sh" || fail "apply created source-maintenance harness script"

CONFLICT_REPO="$TMP_ROOT/conflict"
make_repo "$CONFLICT_REPO"
cat > "$CONFLICT_REPO/package.json" <<'JSON'
{
  "name": "conflict-target",
  "scripts": {
    "chat:new": "echo not-the-workbench"
  }
}
JSON
if run_plan "$CONFLICT_REPO" "$TMP_ROOT/conflict.out"; then
  fail "conflicting package script did not fail dry-run"
fi
grep -q '^PACKAGE_CONFLICT_SCRIPT chat:new ' "$TMP_ROOT/conflict.out" || fail "conflicting package script was not reported"
grep -q '^package_conflicts: yes$' "$TMP_ROOT/conflict.out" || fail "package conflict summary missing"
if run_apply "$CONFLICT_REPO" "$TMP_ROOT/conflict-apply.out"; then
  fail "conflicting package script did not fail apply"
fi
test ! -e "$CONFLICT_REPO/AGENTS.md" || fail "conflicting apply wrote files before refusing"

echo "llm-workbench bootstrap planner/apply smoke test passed."
