#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-persistence-image-payload-fixture
#   version: 2
#   status: draft
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove missing imports, driver, wrappers and compiled exports fail before image construction.
#   portability: { class: internal, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: deploy.command.smoke-test-core-server-persistence-image.readme
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/README.md
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT
bash scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/build.sh --out-dir "$TEMPORARY_DIRECTORY"
node scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs --compiled-root "$TEMPORARY_DIRECTORY"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/verify-runtime.mjs --compiled-root "$TEMPORARY_DIRECTORY"
node - "$TEMPORARY_DIRECTORY" "$ROOT" <<'NODE'
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const [compiled, root] = process.argv.slice(2);
const validator = path.join(root, 'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/verify-runtime.mjs');
function rejects(mutate, undo, nodePath = path.join(root, 'node_modules')) {
  mutate();
  try {
    const result = spawnSync(process.execPath, [validator, '--compiled-root', compiled], {encoding:'utf8', env: {...process.env, NODE_PATH:nodePath}});
    assert.equal(result.status, 1, 'broken payload must fail before image construction');
    assert.equal(JSON.parse(result.stderr).verdict, 'failed');
  } finally { undo(); }
}
const wrapper = path.join(compiled, 'kanbien-core-server-persistence.main.js');
const wrapperContent = fs.readFileSync(wrapper);
rejects(() => fs.unlinkSync(wrapper), () => fs.writeFileSync(wrapper, wrapperContent));
rejects(() => fs.writeFileSync(wrapper, "// " + wrapperContent.toString().replaceAll("\n", " ")), () => fs.writeFileSync(wrapper, wrapperContent));
const manifest = path.join(compiled, 'node_modules/@kanbien/core/package.json');
const manifestContent = fs.readFileSync(manifest);
rejects(() => { const m=JSON.parse(manifestContent); delete m.exports['./diagnostics']; fs.writeFileSync(manifest, JSON.stringify(m)); }, () => fs.writeFileSync(manifest, manifestContent));
rejects(() => {}, () => {}, path.join(compiled, 'absent-external-dependencies'));
const entry = path.join(compiled, 'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.js');
const entryContent = fs.readFileSync(entry);
rejects(() => fs.writeFileSync(entry, 'module.exports = {};'), () => fs.writeFileSync(entry, entryContent));
fs.unlinkSync(path.join(compiled, 'packages/core/src/diagnostics/index.js'));
const prepared = spawnSync(process.execPath, [path.join(root, 'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs'), '--compiled-root', compiled], {encoding:'utf8'});
assert.equal(prepared.status, 1, 'missing compiled export must fail preparation');
console.log('Persistence payload regression passed (6 broken-payload cases; no container or target access).');
NODE
python3 - "$ROOT" "$TEMPORARY_DIRECTORY" <<'PY'
import json, os, shutil, subprocess, sys
from pathlib import Path
root, temporary = map(Path, sys.argv[1:])
fixture = temporary / 'stage-fixture'
coverage = Path('scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage')
(fixture / coverage).mkdir(parents=True)
for name in ('script.sh', 'script.py'):
    shutil.copyfile(root / coverage / name, fixture / coverage / name)
contract = fixture / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml'
contract.parent.mkdir(parents=True)
contract.write_text('schema: deploy/target-scope-contract/v1\nscope: core-server-persistence\n')
binaries = fixture / 'bin'
binaries.mkdir()
(binaries / 'git').write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$COVERAGE_FIXTURE_ROOT"\n')
(binaries / 'docker').write_text('#!/usr/bin/env bash\ntouch "$COVERAGE_DOCKER_MARKER"\nexit 77\n')
for binary in binaries.iterdir(): binary.chmod(0o755)
marker = fixture / 'docker-was-called'
result = subprocess.run(['bash', str(root / 'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh')], cwd=fixture, env={**os.environ, 'PATH': str(binaries) + os.pathsep + os.environ['PATH'], 'COVERAGE_FIXTURE_ROOT': str(fixture), 'COVERAGE_DOCKER_MARKER': str(marker)}, capture_output=True, text=True)
assert result.returncode != 0, 'missing declaration coverage must stop construction'
report = json.loads(result.stdout)
assert 'change-impact-declaration-missing' in {item['code'] for item in report['findings']}, report
assert not marker.exists(), 'Docker must not be called after a declaration gap'
print('Persistence package stage regression passed (declaration gap blocks before Docker).')
# Isolate the next required stage with the real generic inventory/health checks.
# Coverage itself was exercised above; this stub lets us prove corrupt health
# cannot reach composition or Docker even when the requirement chain is covered.
(fixture / coverage / 'script.sh').write_text('#!/usr/bin/env bash\nprintf \'%s\\n\' \'{"verdict":"covered"}\'\n')
capabilities = (
    'scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery',
    'scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration',
    'scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration',
    'scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping',
    'scripts/04.deploy/lifecycle/60-run/validate-acceptance-route',
    'scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration',
    'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/validate-accepted-release',
    'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/validate-accepted-release',
    'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence',
    'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore',
)
for capability in capabilities:
    destination = fixture / capability; destination.mkdir(parents=True, exist_ok=True)
    for name in ('script.sh', 'script.py'):
        source = root / capability / name
        if source.is_file(): shutil.copy2(source, destination / name)
scopes = Path('infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes')
shutil.copytree(root / scopes, fixture / scopes, dirs_exist_ok=True)
# Active and historical scopes retain their real acceptance routes. Include
# their offline validators, schemas and receipt helpers rather than removing
# acceptance from the copied declarations or bypassing record validation.
schemas = Path('.agentic/04.deploy/60-run/schemas')
shutil.copytree(root / schemas, fixture / schemas, dirs_exist_ok=True)
provider = Path('scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence')
for name in ('proof-receipts.py', 'ecs-task-evidence.py'):
    shutil.copy2(root / provider / name, fixture / provider / name)
import yaml
original = contract.read_text()
invalid = yaml.safe_load(original); invalid['health_recovery'] = {}
contract.write_text(yaml.safe_dump(invalid, sort_keys=False))
for command in (
    'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh',
    'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh',
):
    destination = fixture / command; destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text('#!/usr/bin/env bash\ntouch "$COVERAGE_LATER_MARKER"\n')
later = fixture / 'later-stage-was-called'
environment = {**os.environ, 'PATH': str(binaries) + os.pathsep + os.environ['PATH'], 'COVERAGE_FIXTURE_ROOT': str(fixture), 'COVERAGE_DOCKER_MARKER': str(marker), 'COVERAGE_LATER_MARKER': str(later)}
helper = fixture / 'scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py'
helper_bytes = helper.read_bytes()
for damaged in (None, b'def invalid syntax\n'):
    if damaged is None: helper.unlink()
    else: helper.write_bytes(damaged)
    result = subprocess.run(['bash', str(root / 'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh')], cwd=fixture, env=environment, capture_output=True, text=True)
    reports = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    assert result.returncode != 0 and any('scope-lifecycle-acceptance-route-helper-unavailable' in {item['code'] for item in report.get('findings', [])} for report in reports), result.stdout + result.stderr
    assert 'Traceback' not in result.stderr and not marker.exists() and not later.exists(), 'missing/unloadable acceptance helper must report a gap before later stages'
helper.write_bytes(helper_bytes)
print('Persistence package stage regression passed (missing or unloadable acceptance helper returns structured gap).')
result = subprocess.run(['bash', str(root / 'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh')], cwd=fixture, env=environment, capture_output=True, text=True)
assert result.returncode != 0, 'corrupt health must stop image construction'
reports = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
assert any('active-scope-health-recovery-invalid' in {item['code'] for item in report.get('findings', [])} for report in reports), result.stdout + result.stderr
assert not marker.exists() and not later.exists(), 'invalid health must stop before compilation or Docker'
contract.write_text(original)
result = subprocess.run(['bash', str(root / 'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh')], cwd=fixture, env=environment, capture_output=True, text=True)
assert marker.exists() and later.exists(), 'valid declaration must allow the next stage and Docker availability check'
assert result.returncode != 0, 'the fake Docker boundary must never build an image'
print('Persistence package stage regression passed (corrupt health blocks before composition/Docker; repaired declaration advances).')
PY

python3 -B "$ROOT/scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/qualification-route-test.py"
