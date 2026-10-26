#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-persistence-publication-qualification
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise the actual publication qualification shell and builder with controlled local boundaries to prove single execution and fail-stop ordering.
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

with tempfile.TemporaryDirectory(prefix='publication-qualification-') as directory:
    fixture = Path(directory)
    builder = fixture / module.BUILD
    builder.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / module.BUILD, builder)
    binaries = fixture / 'bin'
    binaries.mkdir()
    (binaries / 'git').write_text('#!/bin/bash\nprintf "%s\\n" "$QUAL_ROOT"\n')
    (binaries / 'bash').write_text('''#!/bin/bash
set -e
command_path="$1"
shift
printf '%s\\n' "$command_path" >> "$QUAL_CALLS"
if [[ "$command_path" == "$QUAL_FAIL" ]]; then exit 23; fi
if [[ "$command_path" == "$QUAL_BUILDER" ]]; then exec /bin/bash "$command_path" "$@"; fi
''')
    (binaries / 'python3').write_text('#!/bin/bash\nprintf "%s\\n" "$1" >> "$QUAL_CALLS"\n[[ "$1" != "$QUAL_FAIL" ]]\n')
    (binaries / 'docker').write_text('#!/bin/bash\nprintf "docker:%s\\n" "$1" >> "$QUAL_CALLS"\n')
    for binary in binaries.iterdir():
        binary.chmod(0o755)
    calls = fixture / 'calls'
    boundary = fixture / 'qualification-complete'
    environment = {**os.environ, 'PATH': str(binaries) + os.pathsep + os.environ['PATH'], 'QUAL_ROOT': str(fixture), 'QUAL_CALLS': str(calls), 'QUAL_BUILDER': module.BUILD}
    required = [command[1] for command in module.QUALIFICATION] + [
        'scripts/04.deploy/inventory-deploy-control/script.py',
        'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh',
        'scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh',
        'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh',
        'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh',
    ]
    for rejected in ('', *required):
        calls.write_text('')
        boundary.unlink(missing_ok=True)
        result = subprocess.run(['/bin/bash', '-e', '-c', step['run'] + '\ntouch qualification-complete\n'], cwd=fixture, env={**environment, 'QUAL_FAIL': rejected}, capture_output=True, text=True)
        executed = calls.read_text().splitlines()
        if not rejected:
            assert result.returncode == 0 and boundary.exists(), result.stderr
            assert all(executed.count(path) == 1 for path in required), executed
            assert executed.count('docker:build') == 1
        else:
            assert result.returncode != 0 and not boundary.exists(), rejected
            assert executed.count(rejected) == 1, executed
            if rejected not in (module.SMOKE, 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/capability-negative-test.py', 'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py'):
                assert module.SMOKE not in executed and 'docker:build' not in executed, executed
    with contextlib.chdir(fixture):
        assert module.qualification_route_valid(text)
        original = builder.read_text()
        first_gate = module.BUILDER_PREAMBLE[5]
        last_gate = module.BUILDER_PREAMBLE[-1]
        for change, altered in {
            'missing-gate': original.replace(first_gate, '# removed declaration gate'),
            'conditional-skip': original.replace(first_gate, 'if false; then\n' + first_gate).replace(last_gate, last_gate + '\nfi'),
            'uncalled-function': original.replace(first_gate, 'qualify() {\n' + first_gate).replace(last_gate, last_gate + '\n}'),
            'failure-suppressed': original.replace(first_gate, first_gate + ' || true'),
            'fail-stop-disabled': original.replace('set -euo pipefail', 'set +e'),
            'wrong-contract': original.replace('--scope-contract infra/', '--scope-contract other/'),
            'late-gate': original.replace(first_gate + '\n', '').replace(module.DOCKER_BOUNDARY, module.DOCKER_BOUNDARY + '\n' + first_gate),
            'missing-docker-boundary': original.replace(module.DOCKER_BOUNDARY, ''),
        }.items():
            builder.write_text(altered)
            assert not module.qualification_route_valid(text), change
        builder.write_text(original)
print('Publication qualification passed: actual workflow/builder route runs every declared command once; each required failure stops progression; conditional skips, altered arguments and inherited shell defaults fail closed; no provider or Docker engine invoked.')
