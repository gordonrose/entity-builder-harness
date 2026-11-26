#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-persistence-publication-qualification
#   version: 4
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-11-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise both actual builders and the persistence publication shell with controlled boundaries to prove preserved arguments, single execution and fail-stop ordering.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.core-server-persistence-image-payload-fixture
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/payload-fixture-test.sh
import contextlib
import copy
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[5]
VERIFIER = ROOT / 'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/verify-workflow.py'
spec = importlib.util.spec_from_file_location('publication_contract', VERIFIER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
text = (ROOT / module.EXPECTED).read_text()
workflow = yaml.safe_load(text)
steps = workflow['jobs']['qualify-and-publish']['steps']
step = next(item for item in steps if item.get('name') == 'Qualify declarations and actual candidate payload')
with contextlib.chdir(ROOT):
    assert module.qualification_route_valid(text)
    for source in ('scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh',
                   'scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble.mjs', 'scripts/repo/workspace-build/declarations.mjs', 'scripts/repo/workspace-build/compile.mjs', 'scripts/repo/workspace-build/runtime-packages.mjs', 'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs', 'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/compile.mjs', 'infra/04.deploy/03.product/entrypoints/runnable-program-index.yml',
                   'scripts/04.deploy/lifecycle/40-package/prepare-runtime-dependencies/prepare.mjs',
                   'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-dependencies.mjs',
                   'infra/04.deploy/03.product/image/core-server-persistence/Dockerfile.dockerignore',
                   'infra/04.deploy/03.product/image/core-server-persistence/Dockerfile'):
        selected_input = ' --input ' + source
        assert selected_input in text
        assert not module.qualification_route_valid(text.replace(selected_input, '')), 'omitted assembly/context input must invalidate future qualification binding'
    for malformed in ('[]', '{jobs: []}', '{jobs: {qualify-and-publish: {steps: [null]}}}'):
        assert not module.qualification_route_valid(malformed)
    for change in ('missing-build', 'duplicate-build', 'ignored-failure', 'late-qualification'):
        broken = copy.deepcopy(workflow)
        entries = broken['jobs']['qualify-and-publish']['steps']
        qualification = next(item for item in entries if item.get('name') == step['name'])
        if change == 'missing-build':
            qualification['run'] = '\n'.join(line for line in qualification['run'].splitlines() if module.BUILD not in line)
        elif change == 'duplicate-build':
            qualification['run'] += '\nbash ' + module.BUILD + ' --tag kanbien-core-server-persistence:qualification\n'
        elif change == 'ignored-failure':
            qualification['continue-on-error'] = True
        else:
            entries.remove(qualification)
            entries.append(qualification)
        assert not module.qualification_route_valid(yaml.safe_dump(broken)), change
    for owner in ('workflow', 'job'):
        for defaults in ({'run': {'shell': 'bash {0}'}}, {'run': {'working-directory': '/tmp'}}, None, []):
            broken = copy.deepcopy(workflow)
            target = broken if owner == 'workflow' else broken['jobs']['qualify-and-publish']
            target['defaults'] = defaults
            assert not module.qualification_route_valid(yaml.safe_dump(broken)), (owner, defaults)

with tempfile.TemporaryDirectory(prefix='publication qualification-') as directory:
    fixture = Path(directory)
    builder = fixture / module.BUILD
    builder.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / module.BUILD, builder)
    operations = fixture / module.CANDIDATE_BUILD_OPERATIONS
    operations.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / module.CANDIDATE_BUILD_OPERATIONS, operations)
    helper = Path('scripts/04.deploy/shared/safe-command-diagnostics.sh')
    (fixture / helper).parent.mkdir(parents=True)
    shutil.copyfile(ROOT / helper, fixture / helper)
    binaries = fixture / 'bin'
    binaries.mkdir()
    (binaries / 'git').write_text('''#!/bin/bash
if [[ "$*" == 'rev-parse --show-toplevel' ]]; then printf '%s\\n' "$QUAL_ROOT"
elif [[ "$*" == 'rev-parse HEAD' ]]; then
  count=0; [[ ! -f "$QUAL_HEAD_COUNT" ]] || read -r count < "$QUAL_HEAD_COUNT"
  count=$((count+1)); printf '%s\\n' "$count" > "$QUAL_HEAD_COUNT"
  if [[ -n "${QUAL_BAD_SOURCE:-}" ]]; then printf '%s\\n' invalid-source
  elif [[ "$count" == 1 ]]; then printf '%040d\\n' 1; else printf '%040d\\n' 2; fi
elif [[ "$1" == status ]]; then printf '%s' "${QUAL_DIRTY:-}"
else exit 2; fi
''')
    (binaries / 'bash').write_text('''#!/bin/bash
set -e
command_path="$1"
shift
printf '%s\\n' "$command_path" >> "$QUAL_CALLS"
if [[ "$command_path" == scripts/repo/check-selection/script.sh ]]; then
  printf '%s\\0' "$@" > "$QUAL_PREPARATION_ARGS"
  if [[ "$command_path" == "$QUAL_FAIL" ]]; then
    printf '%s\\n' '{"verdict":"gap","findings":[{"code":"verification-task-context-invalid"}]}'
    exit 23
  fi
fi
if [[ "$command_path" == "$QUAL_FAIL" ]]; then exit 23; fi
if [[ "$command_path" == "$QUAL_BUILDER" ]]; then exec /bin/bash "$command_path" "$@"; fi
''')
    (binaries / 'npm').write_text('#!/bin/bash\nprintf "npm:%s\\n" "$*" >> "$QUAL_CALLS"\nif [[ "npm:$*" == "$QUAL_FAIL" ]]; then exit 23; fi\n')
    (binaries / 'python3').write_text('#!/bin/bash\n[[ "$1" != -B ]] || shift\nprintf "%s\\n" "$1" >> "$QUAL_CALLS"\n[[ "$1" != "$QUAL_FAIL" ]]\n')
    (binaries / 'docker').write_text('''#!/bin/bash
printf 'docker:%s\\n' "$1" >> "$QUAL_CALLS"
if [[ "docker:$1" == "$QUAL_FAIL" ]]; then printf 'build-provider-canary\\n' >&2; exit 23; fi
[[ "$1" != build ]] || printf '%s\\0' "$@" > "$QUAL_DOCKER_ARGS"
''')
    (binaries / 'timeout').write_text('#!/bin/bash\nprintf "timeout:%s\\n" "$1" >> "$QUAL_CALLS"\nshift\nexec "$@"\n')
    for binary in binaries.iterdir():
        binary.chmod(0o755)
    calls = fixture / 'calls'
    boundary = fixture / 'qualification-complete'
    head_count, docker_args = fixture / 'head-count', fixture / 'docker-args'
    environment = {**os.environ, 'PATH': str(binaries) + os.pathsep + os.environ['PATH'], 'QUAL_ROOT': str(fixture), 'QUAL_CALLS': str(calls), 'QUAL_BUILDER': module.BUILD, 'QUAL_HEAD_COUNT': str(head_count), 'QUAL_DOCKER_ARGS': str(docker_args)}
    required = [command[1] for command in module.QUALIFICATION] + [
        'scripts/04.deploy/inventory-deploy-control/script.py',
        'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh',
        'scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh',
        'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh',
        'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh',
        'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-diagnostics-check.sh',
        'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh',
    ]
    for rejected in ('', *required):
        calls.write_text('')
        head_count.unlink(missing_ok=True)
        boundary.unlink(missing_ok=True)
        result = subprocess.run(['/bin/bash', '-e', '-c', step['run'] + '\ntouch qualification-complete\n'], cwd=fixture, env={**environment, 'QUAL_FAIL': rejected}, capture_output=True, text=True)
        executed = calls.read_text().splitlines()
        if not rejected:
            assert result.returncode == 0 and boundary.exists(), result.stderr
            assert all(executed.count(path) == 1 for path in required), executed
            assert executed.count('docker:build') == 1
            assert docker_args.read_bytes().decode().split('\0')[:-1] == [
                'build', '--file', 'infra/04.deploy/03.product/image/core-server-persistence/Dockerfile',
                '--tag', 'kanbien-core-server-persistence:qualification', '--label', 'org.opencontainers.image.revision=' + '1'.zfill(40),
                '--label', 'org.opencontainers.image.source=entity-builder-harness', '--build-arg', 'SOURCE_COMMIT_SHA=' + '1'.zfill(40), str(fixture)]
            assert head_count.read_text().strip() == '1' and 'timeout:30' not in executed
        else:
            assert result.returncode != 0 and not boundary.exists(), rejected
            assert executed.count(rejected) == 1, executed
            if rejected not in (module.SMOKE, 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/capability-negative-test.py', 'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py'):
                assert module.SMOKE not in executed and 'docker:build' not in executed, executed
    with contextlib.chdir(fixture):
        assert module.qualification_route_valid(text)
        original = builder.read_text()
        first_gate = next(line for line in module.BUILDER_PREAMBLE if line.startswith('candidate_image_prechecks '))
        last_gate = module.BUILDER_PREAMBLE[-1]
        for change, altered in {
            'missing-gate': original.replace(first_gate, '# removed declaration gate'),
            'conditional-skip': original.replace(first_gate, 'if false; then\n' + first_gate).replace(last_gate, last_gate + '\nfi'),
            'uncalled-function': original.replace(first_gate, 'qualify() {\n' + first_gate).replace(last_gate, last_gate + '\n}'),
            'failure-suppressed': original.replace(first_gate, first_gate + ' || true'),
            'fail-stop-disabled': original.replace('set -euo pipefail', 'set +e'),
            'wrong-contract': original.replace('candidate_image_prechecks infra/', 'candidate_image_prechecks other/'),
            'late-gate': original.replace(first_gate + '\n', '').replace(module.DOCKER_BOUNDARY, module.DOCKER_BOUNDARY + '\n' + first_gate),
            'missing-docker-boundary': original.replace(module.DOCKER_BOUNDARY, ''),
            'second-source-read': original.replace('"$persistence_source" "$ROOT"', '"$(git rev-parse HEAD)" "$ROOT"'),
            'unbound-source': original.replace('"$persistence_source" "$persistence_source"', 'fixture-revision fixture-source'),
        }.items():
            builder.write_text(altered)
            assert not module.qualification_route_valid(text), change
        builder.write_text(original)
        original_operations = operations.read_text()
        for altered in (
            original_operations.replace('  bash scripts/04.deploy/lifecycle/00-target-alignment/', '  true # bash scripts/04.deploy/lifecycle/00-target-alignment/'),
            original_operations.replace('  "$@" scripts/04.deploy/inventory-deploy-control/script.py --delivery --check', '  if false; then\n    "$@" scripts/04.deploy/inventory-deploy-control/script.py --delivery --check\n  fi'),
            original_operations.replace('--scope-contract "$scope" --json', '--scope-contract "$scope" --json || true'),
            original_operations.replace('docker build "$@"', 'docker build'),
        ):
            operations.write_text(altered)
            assert not module.qualification_route_valid(text), 'shared operation bypass must invalidate the original workflow'
        operations.unlink()
        assert not module.qualification_route_valid(text), 'missing common helper cannot qualify'
        operations.write_text(original_operations)

    for rejected in ('docker:info', 'docker:build'):
        calls.write_text(''); head_count.unlink(missing_ok=True)
        result = subprocess.run(['/bin/bash', str(builder)], cwd=fixture, env={**environment, 'QUAL_FAIL': rejected}, capture_output=True, text=True)
        assert result.returncode != 0 and calls.read_text().splitlines()[-1] == rejected
        if rejected == 'docker:build':
            assert result.returncode == 23 and 'DIAGNOSTIC_CODE=PERSISTENCE_IMAGE_BUILD_FAILED' in result.stderr
            assert 'build-provider-canary' not in result.stderr and 'Built local' not in result.stdout

    # Exercise the actual feature caller too, with independent argv/order
    # expectations. These doubles never start Docker or observe a provider.
    feature_path = 'scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/script.sh'
    feature = fixture / feature_path
    feature.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / feature_path, feature)
    shared = [
        'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh',
        'scripts/04.deploy/inventory-deploy-control/script.py',
        'scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh',
        'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh',
    ]
    preparation_args = fixture / 'preparation-args'
    environment['QUAL_PREPARATION_ARGS'] = str(preparation_args)
    feature_checks = shared + ['scripts/repo/check-selection/script.sh']
    for rejected in ('', *feature_checks, 'docker:info', 'docker:build'):
        calls.write_text(''); head_count.unlink(missing_ok=True); docker_args.unlink(missing_ok=True)
        result = subprocess.run(['/bin/bash', str(feature), '--tag', 'kanbien-entity-smoke:fixture'], cwd=fixture,
                                env={**environment, 'QUAL_FAIL': rejected}, capture_output=True, text=True)
        executed = calls.read_text().splitlines()
        if not rejected:
            assert result.returncode == 0, result.stderr
            assert executed == feature_checks + ['timeout:30', 'docker:info', 'docker:build'], executed
            assert preparation_args.read_bytes().decode().split('\0')[:-1] == [
                '--checks', 'diagnostic-catalog-readers', 'entity-smoke-runtime', 'entity-smoke-composition', '--task-paths',
                'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml',
                '--record-preparation', '--execute-local', '--json']
            assert head_count.read_text().strip() == '1'
            assert result.stdout.strip() == 'ENTITY_SMOKE_LOCAL_IMAGE_BUILT_NOT_QUALIFIED'
            assert docker_args.read_bytes().decode().split('\0')[:-1] == [
                'build', '--load', '--platform', 'linux/amd64', '--provenance=false', '--file',
                'infra/04.deploy/03.product/image/entity-smoke/Dockerfile', '--tag', 'kanbien-entity-smoke:fixture',
                '--label', 'org.opencontainers.image.revision=' + '1'.zfill(40), '--label', 'org.opencontainers.image.source=entity-builder-harness',
                '--build-arg', 'SOURCE_COMMIT_SHA=' + '1'.zfill(40), str(fixture)]
        else:
            assert result.returncode != 0 and executed[-1] == rejected, (rejected, executed)
            assert not docker_args.exists() and 'BUILT_NOT_QUALIFIED' not in result.stdout
            if rejected == 'scripts/repo/check-selection/script.sh':
                assert result.returncode == 23
                assert result.stdout.strip() == '{"verdict":"gap","findings":[{"code":"verification-task-context-invalid"}]}'
                assert result.stderr == ''
            if rejected == 'docker:build':
                assert 'DIAGNOSTIC_CODE=ENTITY_SMOKE_IMAGE_BUILD_FAILED' in result.stderr and 'build-provider-canary' not in result.stderr
    for args, extra, code in (
        (['--tag', 'other:fixture'], {}, 'ENTITY_SMOKE_IMAGE_ARGUMENTS_INVALID'),
        ([], {'QUAL_DIRTY': ' M source.ts'}, 'ENTITY_SMOKE_IMAGE_COMMITTED_SOURCE_REQUIRED'),
        ([], {'QUAL_BAD_SOURCE': 'yes'}, 'ENTITY_SMOKE_IMAGE_SOURCE_INVALID'),
    ):
        calls.write_text('')
        result = subprocess.run(['/bin/bash', str(feature), *args], cwd=fixture, env={**environment, 'QUAL_FAIL': '', **extra}, capture_output=True, text=True)
        assert result.returncode != 0 and result.stderr.strip() == code and calls.read_text() == ''

    calls.write_text('')
    renamed = '''set -euo pipefail
source scripts/04.deploy/shared/safe-command-diagnostics.sh
source scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh
candidate_image_prechecks fixtures/renamed/declaration.yml fixtures/renamed/scopes RENAMED_PROGRAM_INVALID 'Fixture program.' 'Inspect fixture.' python3
candidate_image_build RENAMED_BUILD_FAILED 'Fixture build.' 'Inspect fixture.' fixtures/renamed/Dockerfile 'renamed:fixture' fixture-revision fixture-source "$QUAL_ROOT" --load
'''
    result = subprocess.run(['/bin/bash', '-c', renamed], cwd=fixture, env={**environment, 'QUAL_FAIL': ''}, capture_output=True, text=True)
    assert result.returncode == 0 and calls.read_text().splitlines() == shared + ['docker:build'], result.stderr
    assert docker_args.read_bytes().decode().split('\0')[:-1] == ['build', '--load', '--file', 'fixtures/renamed/Dockerfile', '--tag', 'renamed:fixture', '--label', 'org.opencontainers.image.revision=fixture-revision', '--label', 'org.opencontainers.image.source=entity-builder-harness', '--build-arg', 'SOURCE_COMMIT_SHA=fixture-source', str(fixture)]
print('Publication qualification passed: both actual builders retain ordered gates, source policy, diagnostic status and exact Docker arguments; renamed controlled binding uses the same operations; omitted or substituted helpers fail closed; no provider or Docker engine invoked.')
