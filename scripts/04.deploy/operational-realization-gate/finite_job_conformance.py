"""Exercise the shared finite-job runner with inert, independently bound fixtures."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.finite-job-conformance
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify exact local finite execution and refusal paths without qualifying any product task.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.smoke-test-platform-shell-image
#     path: scripts/04.deploy/smoke-test-platform-shell-image/script.sh

from datetime import datetime, timezone
import json
import re
from pathlib import Path
import sys
import tempfile

DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import container_engine
import container_profiles
import finite_job_contracts as contracts
import local_container
import release_compiler as release
from local_build_sandbox import canonical, digest

FIXTURES = 'scripts/04.deploy/operational-realization-gate/fixtures/finite-jobs/'
CASES = (
    ('success', 'completed', None), ('stderr-success', 'completed', None),
    ('nonzero', 'failed', 'exit-nonzero'), ('missing', 'failed', 'terminal-invalid'),
    ('malformed', 'failed', 'terminal-invalid'), ('wrong-run', 'failed', 'terminal-invalid'),
    ('wrong-profile', 'failed', 'terminal-invalid'), ('duplicate', 'failed', 'terminal-invalid'),
    ('extra-field', 'failed', 'terminal-invalid'), ('timeout', 'timed-out', 'deadline-exceeded'),
    ('excessive-output', 'failed', 'output-limit'),
)
BLOCKED = dict(authorized=False, release_eligibility='blocked', operation_authorization='blocked',
               qualification_verdict='blocked', source_closure='blocked')


def fail(code):
    raise release.ReleaseFailure('finite-job-conformance-' + code)


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def snapshot(root):
    paths = [FIXTURES + 'Dockerfile', FIXTURES + 'jobs/task.cjs',
             'scripts/04.deploy/operational-realization-gate/finite_job_conformance.py',
             'scripts/04.deploy/operational-realization-gate/finite_job_contracts.py',
             'infra/04.deploy/contracts/release-control/v1/finite-job-profile.schema.yml',
             'infra/04.deploy/contracts/release-control/v1/finite-job-result.schema.yml']
    files = {name: local_container.read(root, name) for name in paths}
    executing = {
        paths[2]: (DIRECTORY, 'finite_job_conformance.py'),
        paths[3]: (Path(contracts.__file__).resolve().parent, 'finite_job_contracts.py'),
        paths[4]: (contracts.build_contracts.SCHEMA_DIR, 'finite-job-profile.schema.yml'),
        paths[5]: (contracts.build_contracts.SCHEMA_DIR, 'finite-job-result.schema.yml'),
    }
    # A different source checkout cannot label the implementation that executes here.
    for name, (directory, relative) in executing.items():
        if files[name] != local_container.read(directory, relative):
            fail('source-changed')
    rows = [{'path': key, 'digest': digest(value)} for key, value in sorted(files.items())]
    rows.append({'path': 'existing-container-implementation', 'digest': local_container.implementation_digest(root)})
    return files, digest(canonical(rows))


def profile(case, image_id, files):
    return contracts.validate_profile({
        'schema': 'finite-job-profile/v1', 'id': 'fixture-' + case,
        'artifact': {'image_id': image_id, 'payload_digest': digest(canonical(files))},
        'execution': {'entrypoint': ['/nodejs/bin/node'], 'command': ['jobs/task.cjs', case], 'working_dir': '/app'},
        'limits': {'timeout_seconds': 2 if case == 'timeout' else 15, 'output_bytes': 4096},
        'completion': {'protocol': 'finite-job-terminal/v1', 'required_checks': ['fixture-calculation']},
    })


def validate_result(result, *, image_id, files, revision, inventory_digest, lock, recipe_digest, repository_head):
    release.bounded_json(result)
    fields = {'schema', 'scope', 'verdict', 'started_at', 'completed_at', 'repository_head', 'runner_digest',
              'artifact', 'payload_files', 'engine', 'product_profile_inventory_digest', 'product_profile_updates',
              'cases', 'result_digest'} | set(BLOCKED)
    if (not isinstance(result, dict) or set(result) != fields or result['schema'] != 'finite-job-conformance-result/v1'
            or result['scope'] != 'inert-fixture-conformance' or result['verdict'] != 'passed'
            or any(result[key] != value or type(result[key]) is not type(value) for key, value in BLOCKED.items())
            or result['runner_digest'] != revision or result['payload_files'] != files
            or result['product_profile_inventory_digest'] != inventory_digest or result['product_profile_updates'] != []):
        fail('result-invalid')
    if (type(result['repository_head']) is not str or not re.fullmatch(r'[0-9a-f]{40}', result['repository_head'])
            or result['repository_head'] != repository_head or type(result['engine']) is not dict
            or set(result['engine']) != {'client', 'server'}
            or any(type(value) is not str or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', value)
                   for value in result['engine'].values())):
        fail('metadata-invalid')
    try:
        dates = [datetime.strptime(result[key], '%Y-%m-%dT%H:%M:%SZ') for key in ('started_at', 'completed_at')]
        if (dates[1] < dates[0] or any(dates[index].strftime('%Y-%m-%dT%H:%M:%SZ') != result[key]
                for index, key in enumerate(('started_at', 'completed_at')))):
            fail('metadata-invalid')
    except (TypeError, ValueError):
        fail('metadata-invalid')
    wanted = {'image_id': image_id, 'payload_digest': digest(canonical(files)),
              'runtime_image': lock['runtime_image'], 'runtime_config_digest': lock['runtime_config_digest'],
              'recipe_digest': recipe_digest}
    if result['artifact'] != wanted or type(result['cases']) is not list or len(result['cases']) != len(CASES):
        fail('artifact-or-case-binding-invalid')
    attempts = set()
    for row, (case, outcome, code) in zip(result['cases'], CASES):
        if (not isinstance(row, dict) or set(row) != {'case', 'expected_outcome', 'expected_failure_code', 'conformance_verdict', 'execution'}
                or row['case'] != case or row['expected_outcome'] != outcome or row['expected_failure_code'] != code
                or row['conformance_verdict'] != 'passed'):
            fail('case-binding-invalid')
        execution = row['execution']
        contracts.validate_result(execution, profile(case, image_id, files), execution['run_id'])
        if (execution['outcome'] != outcome or execution['failure_code'] != code
                or not execution['cleanup_verified'] or execution['run_id'] in attempts):
            fail('case-execution-invalid')
        attempts.add(execution['run_id'])
    if result['result_digest'] != digest(canonical({key: value for key, value in result.items() if key != 'result_digest'})):
        fail('result-digest-invalid')
    return result


def run(root, scratch):
    root = Path(root).resolve(strict=True)
    scratch = local_container.checked_scratch(root, scratch)
    source, revision = snapshot(root)
    lock = local_container.load_lock(root)
    head = local_container.repository_head(root)
    profiles = container_profiles.discover(root)
    inventory_digest = digest(canonical(profiles))
    started = now()
    task = source[FIXTURES + 'jobs/task.cjs']
    files = [{'path': 'jobs/task.cjs', 'digest': digest(task), 'bytes': len(task)}]
    recipe_digest = digest(source[FIXTURES + 'Dockerfile'])
    with tempfile.TemporaryDirectory(prefix='finite-job-conformance-', dir=scratch) as temporary:
        work = Path(temporary)
        executor = container_engine.Engine(work)
        engine = executor.version()
        local_container.check_base(executor.base_identity(lock['runtime_image']), lock)
        context = work / 'context'; (context / 'jobs').mkdir(parents=True)
        (context / 'jobs/task.cjs').write_bytes(task)
        (context / 'Dockerfile').write_bytes(source[FIXTURES + 'Dockerfile'])
        image_id = executor.build_job_fixture(context, context / 'Dockerfile', lock['runtime_image'], head)
        cases = []
        for case, outcome, code in CASES:
            execution = executor.run_job(profile(case, image_id, files), files)
            contracts.validate_result(execution, profile(case, image_id, files), execution['run_id'])
            if (execution['outcome'] != outcome or execution['failure_code'] != code or not execution['cleanup_verified']):
                fail('case-execution-invalid')
            cases.append({'case': case, 'expected_outcome': outcome, 'expected_failure_code': code,
                          'conformance_verdict': 'passed', 'execution': execution})
        if ((context / 'jobs/task.cjs').read_bytes() != task
                or (context / 'Dockerfile').read_bytes() != source[FIXTURES + 'Dockerfile']
                or snapshot(root) != (source, revision) or local_container.load_lock(root) != lock
                or local_container.repository_head(root) != head or container_profiles.discover(root) != profiles):
            fail('source-changed')
        result = {'schema': 'finite-job-conformance-result/v1', 'scope': 'inert-fixture-conformance',
                  'verdict': 'passed', **BLOCKED, 'started_at': started, 'completed_at': now(),
                  'repository_head': head, 'runner_digest': revision,
                  'artifact': {'image_id': image_id, 'payload_digest': digest(canonical(files)),
                               'runtime_image': lock['runtime_image'], 'runtime_config_digest': lock['runtime_config_digest'],
                               'recipe_digest': recipe_digest}, 'payload_files': files, 'engine': engine,
                  'product_profile_inventory_digest': inventory_digest, 'product_profile_updates': [], 'cases': cases}
        result['result_digest'] = digest(canonical(result))
        return validate_result(result, image_id=image_id, files=files, revision=revision,
                               inventory_digest=inventory_digest, lock=lock, recipe_digest=recipe_digest, repository_head=head)


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        flags = [value.split('=', 1)[0] for value in argv if value.startswith('--')]
        if len(flags) != len(set(flags)):
            fail('arguments-invalid')
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument('--source-root', required=True)
        parser.add_argument('--scratch-root', required=True)
        args = parser.parse_args(argv)
        if not args.source_root.strip() or not args.scratch_root.strip():
            fail('arguments-invalid')
        result = run(args.source_root, args.scratch_root)
        print(json.dumps(result, sort_keys=True, separators=(',', ':')))
        return 0
    except (release.ReleaseFailure, container_engine.EngineFailure) as error:
        code = error.code if error.code in {'finite-job-conformance-arguments-invalid', 'finite-job-conformance-case-execution-invalid',
            'finite-job-conformance-source-changed', 'finite-job-conformance-result-invalid'} else 'finite-job-conformance-failed'
    except Exception:
        code = 'finite-job-conformance-failed'
    print(json.dumps({'schema': 'finite-job-conformance-error/v1', 'verdict': 'failed', **BLOCKED,
                      'findings': [{'code': code}]}, sort_keys=True, separators=(',', ':')))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
