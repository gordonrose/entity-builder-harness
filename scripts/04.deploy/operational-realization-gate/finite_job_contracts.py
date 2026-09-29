"""Closed finite-execution observations without business-effect or release authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.finite-job-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind exact finite commands and bounded terminal observations while blocking semantic and release authority claims.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.container-engine
#     path: scripts/04.deploy/operational-realization-gate/container_engine.py

from copy import deepcopy
import json
import re

import build_contracts
import release_compiler as release

ReleaseFailure = release.ReleaseFailure

SCHEMAS = ('finite-job-profile', 'finite-job-result')
SETTINGS = {
    'network': 'none', 'read_only': True, 'user': '65532:65532',
    'capabilities': 'none', 'no_new_privileges': True, 'memory_bytes': 536870912,
    'cpus': 1, 'pids_limit': 128, 'tmpfs_bytes': 16777216,
    'published_ports': [], 'host_mounts': [], 'restart': 'no', 'ipc': 'none',
    'environment_keys': ['RELEASE_CONTROL_PROFILE_DIGEST', 'RELEASE_CONTROL_RUN_ID'],
}
FAILURE_CODES = frozenset({
    'engine-unavailable', 'image-mismatch', 'payload-mismatch', 'command-mismatch',
    'isolation-mismatch', 'start-failed', 'exit-nonzero', 'oom-killed',
    'terminal-invalid', 'output-limit', 'deadline-exceeded', 'interrupted',
    'cleanup-failed', 'observation-unavailable',
})
OBSERVATION_FIELDS = frozenset({
    'outcome', 'failure_code', 'exit_code', 'oom_killed', 'terminal_digest',
    'checks', 'cleanup_verified', 'elapsed_ms',
})
RUN_ID = re.compile(r'[0-9a-f]{32}')


def fail(code):
    raise release.ReleaseFailure('finite-job-' + code)


def digest(document):
    return release.digest_document(document)


def schema_digests():
    return {name + '/v1': digest(release.load_document(
        build_contracts.SCHEMA_DIR / (name + '.schema.yml'), 'finite-job-schema-unreadable'))
        for name in SCHEMAS}


def validate_profile(profile):
    build_contracts.validate_schema('finite-job-profile', profile)
    path = profile['execution']['command'][0]
    if path.startswith('-') or any(part in {'', '.', '..'} for part in path.split('/')):
        fail('command-invalid')
    return profile


def profile_digest(profile):
    validate_profile(profile)
    return digest({'profile': profile, 'schema_digests': schema_digests()})


def _run_id(run_id):
    if type(run_id) is not str or not RUN_ID.fullmatch(run_id):
        fail('run-id-invalid')


def _expected_checks(profile):
    return [{'id': identifier, 'verdict': 'passed'}
            for identifier in profile['completion']['required_checks']]


def _terminal(profile, run_id, checks):
    validate_profile(profile)
    _run_id(run_id)
    if checks != _expected_checks(profile):
        fail('terminal-invalid')
    return {'schema': 'finite-job-terminal/v1', 'run_id': run_id,
            'profile_digest': profile_digest(profile), 'outcome': 'completed',
            'checks': deepcopy(checks)}


def terminal_digest(profile, run_id, checks):
    """Hash the accepted canonical envelope, never raw stdout or secret text."""
    return digest(_terminal(profile, run_id, checks))


def evaluate_terminal(raw, profile, run_id):
    """Accept exactly one closed fresh terminal envelope, independent of exit status."""
    validate_profile(profile)
    _run_id(run_id)
    if type(raw) is not bytes:
        fail('terminal-invalid')
    if len(raw) > profile['limits']['output_bytes']:
        fail('output-limit')

    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                fail('terminal-invalid')
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=lambda ignored: fail('terminal-invalid'))
        release.bounded_json(value, max_nodes=256)
    except (ValueError, UnicodeError, RecursionError, release.ReleaseFailure):
        fail('terminal-invalid')
    expected = _terminal(profile, run_id, _expected_checks(profile))
    if type(value) is not dict or value != expected:
        fail('terminal-invalid')
    return deepcopy(expected['checks'])


def make_result(profile, run_id, observation):
    """Build a safe result from observations made by the bounded local adapter."""
    validate_profile(profile)
    _run_id(run_id)
    if type(observation) is not dict or set(observation) != OBSERVATION_FIELDS:
        fail('observation-invalid')
    result = {
        'schema': 'finite-job-result/v1', 'scope': 'local-finite-execution',
        'authorized': False, 'release_eligibility': 'blocked',
        'operation_authorization': 'blocked', 'qualification_verdict': 'blocked',
        'source_closure': 'blocked', 'semantic_verdict': 'unverified',
        'profile': deepcopy(profile), 'profile_digest': profile_digest(profile),
        'schema_digests': schema_digests(), 'run_id': run_id,
        'settings': deepcopy(SETTINGS), **deepcopy(observation),
    }
    result['result_digest'] = digest(result)
    return validate_result(result, profile, run_id)


def validate_result(result, expected_profile, expected_run_id):
    """Fresh expected bindings are mandatory; this is not a saved-result admission API."""
    validate_profile(expected_profile)
    _run_id(expected_run_id)
    build_contracts.validate_schema('finite-job-result', result)
    if result['result_digest'] != digest({key: value for key, value in result.items()
                                         if key != 'result_digest'}):
        fail('result-digest-invalid')
    if (result['profile'] != expected_profile or result['run_id'] != expected_run_id
            or result['schema_digests'] != schema_digests()
            or result['profile_digest'] != profile_digest(expected_profile)):
        fail('result-binding-invalid')
    outcome, code = result['outcome'], result['failure_code']
    if outcome == 'completed':
        if (code is not None or result['exit_code'] != 0 or result['oom_killed'] is not False
                or result['cleanup_verified'] is not True
                or result['checks'] != _expected_checks(expected_profile)
                or result['terminal_digest'] != terminal_digest(expected_profile, expected_run_id, result['checks'])):
            fail('completion-invalid')
    else:
        if code not in FAILURE_CODES or result['checks'] or result['terminal_digest'] is not None:
            fail('failure-invalid')
        if (outcome == 'timed-out') != (code == 'deadline-exceeded'):
            fail('failure-invalid')
        if (outcome == 'interrupted') != (code == 'interrupted'):
            fail('failure-invalid')
        if (outcome == 'unknown') != (code in {'engine-unavailable', 'observation-unavailable', 'cleanup-failed'}):
            fail('failure-invalid')
        if result['cleanup_verified'] is False and code != 'cleanup-failed':
            fail('cleanup-invalid')
        if code == 'cleanup-failed' and result['cleanup_verified'] is not False:
            fail('cleanup-invalid')
        if code == 'exit-nonzero' and (result['exit_code'] is None or result['exit_code'] == 0):
            fail('failure-invalid')
        if code == 'oom-killed' and result['oom_killed'] is not True:
            fail('failure-invalid')
    return result
