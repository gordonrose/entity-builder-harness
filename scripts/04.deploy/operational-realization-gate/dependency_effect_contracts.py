"""Closed local dependency evidence; no provider or release authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.dependency-effect-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind actual packaged command effects to fresh isolated dependencies and independent observations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.dependency-effects
#     path: scripts/04.deploy/operational-realization-gate/dependency_effects.py

import json
import re
from copy import deepcopy

import build_contracts
import release_compiler as release

SCHEMAS = ('dependency-effect-profile', 'dependency-effect-result')
BLOCKED = dict(authorized=False, release_eligibility='blocked', operation_authorization='blocked',
               qualification_verdict='blocked', source_closure='blocked')
PREFIX = '.cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/'
COMMANDS = {name: [PREFIX + 'kanbien-platform-postgresql-' + name + '.main.js']
            for name in ('bootstrap', 'migration')}
CASES = (
    ('bootstrap-binding-invalid', 'bootstrap', 'failed', ['empty-before', 'empty-after']),
    ('bootstrap-untrusted-ca', 'bootstrap', 'failed', ['empty-before', 'empty-after']),
    ('bootstrap-bad-password', 'bootstrap', 'failed', ['empty-before', 'empty-after']),
    ('bootstrap', 'bootstrap', 'succeeded', ['empty-before', 'roles-and-schema']),
    ('bootstrap-repeat', 'bootstrap', 'succeeded', ['roles-and-schema', 'state-unchanged']),
    ('migration-denied', 'migration', 'failed', ['roles-and-schema', 'no-tables']),
    ('migration', 'migration', 'succeeded', ['no-tables', 'manifest-and-grants']),
    ('migration-repeat', 'migration', 'succeeded', ['manifest-and-grants', 'state-unchanged']),
    ('migration-checksum-mismatch', 'migration', 'failed', ['corrupt-checksum-present', 'state-unchanged']),
)
ASSERTIONS = ['tls-session-observed', 'runtime-ddl-denied', 'runtime-dml-transaction',
              'final-manifest-and-grants', 'network-cleanup', 'container-cleanup',
              'missing-select-detected', 'missing-insert-detected', 'missing-update-detected', 'missing-delete-detected']
DIGEST = re.compile(r'sha256:[a-f0-9]{64}\Z')


def fail(code):
    raise release.ReleaseFailure('dependency-effect-' + code)


def digest(value):
    return release.digest_document(value)


def schema_digests():
    return {name + '/v1': digest(release.load_document(build_contracts.SCHEMA_DIR / (name + '.schema.yml'),
                                                     'dependency-effect-schema-unreadable')) for name in SCHEMAS}


def validate_lock(value):
    keys = {'schema', 'image', 'config_digest', 'engine_version', 'platform', 'source'}
    if (type(value) is not dict or set(value) != keys or value['schema'] != 'dependency-image-lock/v1'
            or value['engine_version'] != '17.11' or value['platform'] != 'linux/amd64'
            or type(value['image']) is not str or not re.fullmatch(r'docker\.io/library/postgres@sha256:[a-f0-9]{64}', value['image'])
            or type(value['config_digest']) is not str or not DIGEST.fullmatch(value['config_digest'])
            or type(value['source']) is not str or not re.fullmatch(r'https://github\.com/docker-library/postgres/tree/[a-f0-9]{40}/17/bookworm', value['source'])):
        fail('dependency-lock-invalid')
    return value


def validate_expectations(value):
    if (type(value) is not dict or set(value) != {'schema', 'engine_version', 'migration_checksums', 'tables', 'columns', 'constraints'}
            or value['schema'] != 'dependency-effect-expectations/v1' or value['engine_version'] != '17.11'
            or value['tables'] != ['platform_migration_history', 'platform_outbox', 'platform_processing',
                                   'platform_record_change', 'platform_smoke_work_item']
            or type(value['migration_checksums']) is not dict
            or set(value['migration_checksums']) != {'v0001_platform_persistence', 'v0002_platform_smoke_work_item'}
            or any(type(v) is not str or not re.fullmatch(r'[a-f0-9]{64}', v) for v in value['migration_checksums'].values())):
        fail('expectations-invalid')
    if (type(value['columns']) is not list or not value['columns'] or type(value['constraints']) is not list or not value['constraints']
            or any(type(row) is not dict or set(row) != {'table', 'position', 'name', 'type', 'nullable', 'default'} for row in value['columns'])
            or any(type(row) is not dict or set(row) != {'table', 'kind', 'definition'} for row in value['constraints'])):
        fail('expectations-invalid')
    return value


def validate_profile(value):
    build_contracts.validate_schema('dependency-effect-profile', value)
    if value['commands'] != COMMANDS or value['schema_digests'] != schema_digests():
        fail('profile-invalid')
    return value


def terminal(raw, task, expected, *, failure_category=None):
    """The existing product terminal is only execution evidence; psql proves effects."""
    if task not in COMMANDS or expected not in {'succeeded', 'failed'} or type(raw) is not bytes or len(raw) > 4096:
        fail('terminal-invalid')
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                fail('terminal-invalid')
            result[key] = value
        return result
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=lambda _: fail('terminal-invalid'))
    except (ValueError, UnicodeError, RecursionError):
        fail('terminal-invalid')
    fields = value.get('fields') if type(value) is dict else None
    if (type(value) is not dict or set(value) != {'level', 'message', 'fields'}
            or value['level'] != ('info' if expected == 'succeeded' else 'error')
            or value['message'] != 'kanbien-platform.relational-smoke.' + task + '_completed'
            or type(fields) is not dict or fields.get('outcome') != expected
            or set(fields) not in ({'outcome'}, {'outcome', 'failure_category'})):
        fail('terminal-invalid')
    if 'failure_category' in fields:
        if (task != 'bootstrap' or expected != 'failed' or type(fields['failure_category']) is not str
                or fields['failure_category'] not in {'bootstrap-input-validation-failure',
                    'bootstrap-database-authentication-failure', 'bootstrap-database-authorization-failure',
                    'bootstrap-database-connectivity-failure', 'bootstrap-database-tls-failure',
                    'bootstrap-certificate-authority-unavailable', 'bootstrap-password-quotation-failure',
                    'bootstrap-role-provisioning-failure', 'bootstrap-database-grant-failure',
                    'bootstrap-schema-provisioning-failure', 'bootstrap-schema-grant-failure',
                    'bootstrap-workload-failure-unclassified'}):
            fail('terminal-invalid')
    if failure_category is not None and fields.get('failure_category') != failure_category:
        fail('terminal-category-mismatch')
    return digest(value)


def validate_result(value, expected_profile, expected_run_id):
    validate_profile(expected_profile)
    build_contracts.validate_schema('dependency-effect-result', value)
    if (value['profile'] != expected_profile or value['profile_digest'] != digest(expected_profile)
            or value['run_id'] != expected_run_id or type(expected_run_id) is not str
            or not re.fullmatch(r'[a-f0-9]{32}', expected_run_id)
            or any(type(value[k]) is not type(v) or value[k] != v for k, v in BLOCKED.items())
            or value['assertions'] != [{'id': a, 'verdict': 'passed'} for a in ASSERTIONS]):
        fail('result-binding-invalid')
    attempts = set()
    for observed, (name, task, outcome, assertions) in zip(value['cases'], CASES):
        if (observed['case'] != name or observed['task'] != task or observed['outcome'] != outcome
                or observed['exit_code'] != (0 if outcome == 'succeeded' else 1)
                or observed['assertions'] != [{'id': a, 'verdict': 'passed'} for a in assertions]
                or observed['attempt_id'] in attempts):
            fail('case-binding-invalid')
        attempts.add(observed['attempt_id'])
        if 'state-unchanged' in assertions and observed['before_digest'] != observed['after_digest']:
            fail('effect-mismatch')
    if value['result_digest'] != digest({k: v for k, v in value.items() if k != 'result_digest'}):
        fail('result-digest-invalid')
    return value


def make_result(profile, run_id, cases, certificate_digest, engine):
    result = {'schema': 'dependency-effect-result/v1', 'scope': 'local-packaged-postgresql-effects',
              'verdict': 'passed', **BLOCKED, 'profile': deepcopy(profile), 'profile_digest': digest(profile),
              'run_id': run_id, 'certificate_digest': certificate_digest, 'engine': engine,
              'cases': deepcopy(cases), 'assertions': [{'id': a, 'verdict': 'passed'} for a in ASSERTIONS],
              'cleanup_verified': True, 'pending_tasks': ['relay', 'worker', 'restore-verify']}
    result['result_digest'] = digest(result)
    return validate_result(result, profile, run_id)
