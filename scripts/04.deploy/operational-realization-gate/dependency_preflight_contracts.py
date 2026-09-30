"""Distinct bounded local prerequisite evidence; never task completion or authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.dependency-preflight-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind read-only packaged database preflight observations separately from task effects.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.dependency-effects
#     path: scripts/04.deploy/operational-realization-gate/dependency_effects.py

import json
from copy import deepcopy
from jsonschema import Draft202012Validator
import dependency_effect_contracts as effects

SCHEMAS = ('dependency-preflight-result', 'relational-task-preflight')
COMMANDS = {task: [effects.PREFIX + 'kanbien-platform-postgresql-' + task + '.main.js', '--preflight']
            for task in ('bootstrap', 'migration', 'relay', 'worker')}
CASES = (
    ('bootstrap-ready', 'bootstrap', 'passed', 'before-bootstrap'),
    ('bootstrap-denied-identity', 'bootstrap', 'failed', 'before-bootstrap'),
    ('migration-ready', 'migration', 'passed', 'after-bootstrap'),
    ('migration-denied-identity', 'migration', 'failed', 'after-bootstrap'),
    ('relay-ready', 'relay', 'passed', 'after-migration'),
    ('worker-ready', 'worker', 'passed', 'after-migration'),
    ('relay-denied-select', 'relay', 'failed', 'after-revoke-select'),
    ('worker-denied-delete', 'worker', 'failed', 'after-revoke-delete'),
)
TABLES = ('platform_outbox', 'platform_processing', 'platform_record_change', 'platform_smoke_work_item')
ASSERTIONS = ['selected-schema-and-grants-unchanged', 'selected-data-empty-unchanged']


def load_schema(name):
    if name not in SCHEMAS: effects.fail('preflight-schema-unsupported')
    schema = effects.release.load_document(effects.build_contracts.SCHEMA_DIR / (name + '.schema.yml'),
                                          'dependency-preflight-schema-unreadable')
    if (schema.get('$schema') != 'https://json-schema.org/draft/2020-12/schema'
            or schema.get('$id') != 'urn:release-control:' + name + ':v1'
            or schema.get('type') != 'object'
            or schema.get('properties', {}).get('schema') != {'const': name + '/v1'}):
        effects.fail('preflight-schema-invalid')
    pending = [schema]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if any(key in item for key in ('$ref', '$dynamicRef', '$recursiveRef')):
                effects.fail('preflight-schema-invalid')
            if item.get('type') == 'object' or 'properties' in item:
                fields, required = item.get('properties'), item.get('required')
                if (item.get('type') != 'object' or item.get('additionalProperties') is not False
                        or type(fields) is not dict or type(required) is not list
                        or any(type(key) is not str for key in required)
                        or len(set(required)) != len(required) or set(required) != set(fields)):
                    effects.fail('preflight-schema-invalid')
            pending.extend(item.values())
        elif isinstance(item, list): pending.extend(item)
    try: Draft202012Validator.check_schema(schema)
    except Exception: effects.fail('preflight-schema-invalid')
    return schema


def validate_shape(name, value):
    effects.release.bounded_json(value)
    if next(Draft202012Validator(load_schema(name)).iter_errors(value), None):
        effects.fail('preflight-document-invalid')


def schema_digests():
    return {name + '/v1': effects.digest(load_schema(name)) for name in SCHEMAS}


def terminal(raw, task, verdict):
    if task not in COMMANDS or verdict not in {'passed', 'failed'} or type(raw) is not bytes or len(raw) > 4096:
        effects.fail('preflight-terminal-invalid')
    def pairs(rows):
        value = {}
        for key, item in rows:
            if key in value: effects.fail('preflight-terminal-invalid')
            value[key] = item
        return value
    def invalid(_): effects.fail('preflight-terminal-invalid')
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError):
        effects.fail('preflight-terminal-invalid')
    wanted = {'schema': 'relational-task-preflight/v1', 'scope': 'read-only-database-prerequisites',
              'operation': task, 'verdict': verdict, 'authorized': False}
    if value != wanted or type(value.get('authorized')) is not bool:
        effects.fail('preflight-terminal-invalid')
    validate_shape('relational-task-preflight', value)
    return effects.digest(value)


def check_unchanged(before, after):
    if (type(before) is not dict or set(before) != {'state', 'row_counts'} or before != after
            or type(before['state']) is not dict or type(before['row_counts']) is not dict
            or set(before['row_counts']) not in (set(), set(TABLES))
            or any(type(count) is not int or count != 0 for count in before['row_counts'].values())):
        effects.fail('preflight-independent-state-mismatch')
    return effects.digest(before)


def observe(engine, image_id, case):
    selected = next((row for row in CASES if row[0] == case), None)
    if selected is None: effects.fail('preflight-case-invalid')
    name, task, verdict, phase = selected
    before = engine.preflight_snapshot()
    execution = engine.run_preflight(image_id, task, name, verdict)
    after = engine.preflight_snapshot()
    state_digest = check_unchanged(before, after)
    return {'case': name, 'operation': task, 'verdict': verdict, 'phase': phase, **execution,
            'before_digest': state_digest, 'after_digest': state_digest,
            'observed_row_counts': deepcopy(before['row_counts']),
            'assertions': [{'id': item, 'verdict': 'passed'} for item in ASSERTIONS]}


def validate_result(value, effect_result):
    effects.validate_result(effect_result, effect_result['profile'], effect_result['run_id'])
    validate_shape('dependency-preflight-result', value)
    if (value['effect_result_digest'] != effect_result['result_digest']
            or value['profile_digest'] != effect_result['profile_digest']
            or value['run_id'] != effect_result['run_id']
            or value['artifact'] != effect_result['profile']['artifact']
            or value['certificate_digest'] != effect_result['certificate_digest']
            or value['runner_digest'] != effect_result['profile']['runner_digest']
            or value['schema_digests'] != schema_digests() or value['commands'] != COMMANDS):
        effects.fail('preflight-result-binding-invalid')
    attempts = {row['attempt_id'] for row in effect_result['cases']}
    for row, (name, task, verdict, phase) in zip(value['cases'], CASES):
        expected_terminal = {'schema': 'relational-task-preflight/v1', 'scope': 'read-only-database-prerequisites',
                             'operation': task, 'verdict': verdict, 'authorized': False}
        counts = {} if phase in {'before-bootstrap', 'after-bootstrap'} else {name: 0 for name in TABLES}
        if (row['case'] != name or row['operation'] != task or row['verdict'] != verdict or row['phase'] != phase
                or row['exit_code'] != (0 if verdict == 'passed' else 1) or type(row['exit_code']) is not int
                or row['terminal_digest'] != effects.digest(expected_terminal)
                or row['before_digest'] != row['after_digest'] or row['attempt_id'] in attempts
                or row['observed_row_counts'] != counts
                or any(type(count) is not int for count in row['observed_row_counts'].values())
                or row['assertions'] != [{'id': item, 'verdict': 'passed'} for item in ASSERTIONS]):
            effects.fail('preflight-result-case-invalid')
        attempts.add(row['attempt_id'])
    if effects.digest({key: item for key, item in value.items() if key != 'result_digest'}) != value['result_digest']:
        effects.fail('preflight-result-digest-invalid')
    return value


def make_result(effect_result, cases):
    value = {'schema': 'dependency-preflight-result/v1', 'scope': 'local-packaged-postgresql-prerequisites',
             'verdict': 'passed', **effects.BLOCKED, 'effect_result_digest': effect_result['result_digest'],
             'profile_digest': effect_result['profile_digest'], 'run_id': effect_result['run_id'],
             'artifact': deepcopy(effect_result['profile']['artifact']),
             'certificate_digest': effect_result['certificate_digest'],
             'runner_digest': effect_result['profile']['runner_digest'], 'schema_digests': schema_digests(),
             'commands': deepcopy(COMMANDS), 'cases': deepcopy(cases), 'cleanup_verified': True,
             'pending': ['aws-identity-and-injection', 'queue-permissions-and-effects', 'isolated-restore-target']}
    value['result_digest'] = effects.digest(value)
    return validate_result(value, effect_result)
