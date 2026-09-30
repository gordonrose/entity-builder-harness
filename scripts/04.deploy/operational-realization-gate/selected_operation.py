"""Selected target journal conformance; source policy grants no operation authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-operation
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate versioned selected operation records and pure bounded transitions without provider execution authority.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.aws-selected-store
#     path: scripts/04.deploy/release-control/adapters/aws/selected_store.py
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator
import operation_journal as journal

SCHEMA_DIR = Path(__file__).resolve().parents[3] / 'infra/04.deploy/contracts/release-control/v2'
SCHEMAS = frozenset(('selected-operation-record', 'selected-operation-evidence', 'selected-store-event'))
EVENTS = frozenset(('prepare', 'claim', 'renew', 'reserve', 'mark-unknown', 'reconcile', 'observe', 'verify-cleanup', 'close', 'block'))
POLICY = {
    'schema': 'selected-control-policy/v1',
    'approval_scope': 'source-implementation-only',
    'executor': 'protected-github-main-staging',
    'retention_minimum_days': 90, 'pitr_days': 35,
    'recovery_point_objective_ms': 300000, 'recovery_time_objective_ms': 14400000,
    'authority_window_ms': 7200000, 'operation_timeout_ms': 5400000,
    'recovery_timeout_ms': 1800000, 'lease_ms': 60000, 'renew_interval_ms': 20000,
    'call_timeout_ms': 30000, 'call_safety_margin_ms': 5000,
    'clock_uncertainty_max_ms': 5000, 'max_effect_attempts': 1, 'max_read_attempts': 3,
    'additional_monthly_ceiling_usd': 5, 'total_monthly_ceiling_usd': 25,
    'initial_qualification_ceiling_usd': 2,
    'automatic_deletion': False,
}
AUTHORITY = {'authorized': False, 'release_eligibility': 'blocked', 'operation_authorization': 'blocked'}

digest = journal.digest
ControlFailure = journal.ControlFailure
fail = journal.fail


def policy():
    return deepcopy(POLICY)


def load_schema(name):
    if type(name) is not str or name not in SCHEMAS:
        fail('selected-schema-unsupported')
    return _schema(name, journal.read_source(SCHEMA_DIR / (name + '.schema.yml')))


@lru_cache(maxsize=8)
def _schema(name, raw):
    return journal._parse_schema(name, raw, version='v2')


def validate(name, value):
    journal.canonical(value)
    if next(Draft202012Validator(load_schema(name)).iter_errors(value), None):
        fail('selected-record-invalid')
    return value


def validate_record(record):
    validate('selected-operation-record', record)
    intent = record['intent']
    if intent['policy'] != POLICY or intent['policy_digest'] != digest(intent['policy']):
        fail('selected-policy-invalid')
    created = intent['created_at_ms']
    deadline = record['authority_expires_at_ms']
    if not created < deadline <= created + POLICY['authority_window_ms']:
        fail('selected-budget-invalid')
    if not created <= record['updated_at_ms']:
        fail('selected-clock-regressed')
    if record['lease_expires_at_ms'] > deadline:
        fail('selected-budget-invalid')
    if record['owner'] is None and record['lease_expires_at_ms'] != 0:
        fail('selected-owner-invalid')
    state = record['state']
    if record['fence'] > record['revision'] or (state != 'prepared' and record['revision'] == 0):
        fail('selected-record-invalid')
    reservation = record['reservation']
    if state == 'prepared':
        if any((record['revision'], record['fence'], record['attempt'], record['lease_expires_at_ms'])) or record['owner'] is not None:
            fail('selected-record-invalid')
    if state in ('claimed', 'reserved', 'unknown', 'observed', 'cleanup-verified'):
        if record['owner'] is None or record['fence'] < 1 or record['lease_expires_at_ms'] <= created:
            fail('selected-owner-invalid')
    if state in ('closed', 'blocked') and (record['owner'] is not None or record['lease_expires_at_ms'] != 0):
        fail('selected-owner-invalid')
    if reservation is None:
        if record['attempt'] != 0 or state in ('reserved', 'unknown', 'observed', 'cleanup-verified', 'closed'):
            fail('selected-reservation-invalid')
    else:
        if (record['attempt'] != 1 or state in ('prepared', 'claimed')
                or not created <= reservation['reserved_at_ms'] <= record['updated_at_ms']
                or not reservation['reserved_at_ms'] < reservation['credential_expires_at_ms'] <= deadline
                or reservation['fence'] > record['fence']):
            fail('selected-reservation-invalid')
        if record['mode'] == 'normal' and record['owner'] is not None and (reservation['owner'] != record['owner'] or reservation['fence'] != record['fence']):
            fail('selected-reservation-invalid')
    if state in ('observed', 'cleanup-verified', 'closed') and record['observation_digest'] is None:
        fail('selected-observation-invalid')
    if state in ('prepared', 'claimed', 'reserved', 'unknown') and record['observation_digest'] is not None:
        fail('selected-observation-invalid')
    if record['mode'] == 'reconcile' and state not in ('unknown', 'blocked'):
        fail('selected-quarantine-active')
    return record


def _time(before, now_ms):
    if type(now_ms) is not int or now_ms < before['updated_at_ms'] or now_ms > 2**63 - 1:
        fail('selected-clock-regressed')


def _active(before, now_ms):
    if now_ms >= min(before['authority_expires_at_ms'], before['intent']['created_at_ms'] + POLICY['operation_timeout_ms']):
        fail('selected-budget-expired')
    if before['owner'] is None or now_ms >= before['lease_expires_at_ms']:
        fail('selected-lease-expired')
    if before['mode'] != 'normal':
        fail('selected-quarantine-active')


def validate_transition(before, after, *, event, now_ms):
    if type(event) is not str or event not in EVENTS:
        fail('selected-event-unsupported')
    validate_record(after)
    if before is None:
        if (event != 'prepare' or type(now_ms) is not int or after['state'] != 'prepared'
                or after['intent']['created_at_ms'] != now_ms or after['updated_at_ms'] != now_ms
                or after['mode'] != 'normal' or after['reservation'] is not None or after['observation_digest'] is not None):
            fail('selected-transition-invalid')
        return after
    validate_record(before)
    _time(before, now_ms)
    if event == 'prepare' or before['state'] in ('closed', 'blocked'):
        fail('selected-transition-invalid')
    expected = deepcopy(before)
    expected['revision'] += 1
    expected['updated_at_ms'] = now_ms
    if event == 'claim':
        if before['state'] != 'prepared' or now_ms >= min(before['authority_expires_at_ms'], before['intent']['created_at_ms'] + POLICY['operation_timeout_ms']):
            fail('selected-transition-invalid')
        expected.update(state='claimed', owner=after['owner'], fence=before['fence'] + 1,
                        lease_expires_at_ms=min(now_ms + POLICY['lease_ms'], before['authority_expires_at_ms']))
    elif event == 'renew':
        _active(before, now_ms)
        if before['state'] == 'unknown':
            fail('selected-quarantine-active')
        expected['lease_expires_at_ms'] = min(now_ms + POLICY['lease_ms'], before['authority_expires_at_ms'])
    elif event == 'reserve':
        _active(before, now_ms)
        if before['state'] != 'claimed' or before['attempt'] != 0:
            fail('selected-transition-invalid')
        if now_ms + POLICY['call_timeout_ms'] + POLICY['call_safety_margin_ms'] > min(before['lease_expires_at_ms'], before['intent']['created_at_ms'] + POLICY['operation_timeout_ms'], before['authority_expires_at_ms']):
            fail('selected-call-budget-exhausted')
        reservation = after['reservation']
        if (reservation is None or reservation['owner'] != before['owner'] or reservation['fence'] != before['fence']
                or reservation['reserved_at_ms'] != now_ms
                or reservation['credential_expires_at_ms'] < now_ms + POLICY['call_timeout_ms'] + POLICY['call_safety_margin_ms']):
            fail('selected-reservation-invalid')
        expected.update(state='reserved', attempt=1, reservation=deepcopy(reservation))
    elif event == 'mark-unknown':
        if before['state'] != 'reserved':
            fail('selected-transition-invalid')
        expected['state'] = 'unknown'
    elif event == 'reconcile':
        if before['state'] != 'unknown' or now_ms < before['lease_expires_at_ms'] or now_ms >= before['authority_expires_at_ms']:
            fail('selected-quarantine-active')
        if after['owner'] is None or after['owner'] == before['owner']:
            fail('selected-owner-invalid')
        expected.update(mode='reconcile', owner=after['owner'], fence=before['fence'] + 1,
                        lease_expires_at_ms=min(now_ms + POLICY['lease_ms'], before['authority_expires_at_ms']))
    elif event in ('observe', 'verify-cleanup', 'close'):
        _active(before, now_ms)
        wanted = {'observe': 'reserved', 'verify-cleanup': 'observed', 'close': 'cleanup-verified'}[event]
        if before['state'] != wanted:
            fail('selected-quarantine-active' if before['state'] == 'unknown' else 'selected-transition-invalid')
        if event == 'close':
            expected.update(state='closed', owner=None, lease_expires_at_ms=0)
        else:
            if after['observation_digest'] is None:
                fail('selected-observation-invalid')
            expected.update(state='observed' if event == 'observe' else 'cleanup-verified', observation_digest=after['observation_digest'])
    elif event == 'block':
        expected.update(state='blocked', owner=None, lease_expires_at_ms=0)
    if expected != after:
        fail('selected-transition-invalid')
    return after


def require_execution_authority(record):
    """No value accepted by this conformance seam grants real operation authority."""
    validate_record(record)
    fail('selected-operation-authority-unavailable')


def fixture_record(now_ms=1000000, operation_id='candidate-fixture', generation='a' * 32):
    """Explicitly inert fixture; fixed synthetic bindings are never live proof."""
    p = policy()
    record = {
        'schema': 'selected-operation-record/v2', 'scope': 'selected-operation-conformance',
        'operation_id': operation_id, 'generation': generation, 'revision': 0, 'fence': 0,
        'state': 'prepared', 'owner': None, 'lease_expires_at_ms': 0,
        'authority_expires_at_ms': now_ms + POLICY['authority_window_ms'], 'updated_at_ms': now_ms,
        'attempt': 0, 'mode': 'normal', 'reservation': None, 'observation_digest': None,
        'intent': {'target': 'kanbien/staging', 'provider': 'aws', 'account': '337159794548',
                   'region': 'eu-west-1', 'operation': 'candidate-preflight',
                   'release_digest': 'sha256:' + '1' * 64, 'source_revision': '2' * 40,
                   'image_digest': 'sha256:' + '3' * 64, 'blueprint_digest': 'sha256:' + '4' * 64,
                   'policy': p, 'policy_digest': digest(p), 'created_at_ms': now_ms,
                   'authority_status': 'not-granted'}, **AUTHORITY,
    }
    return validate_transition(None, record, event='prepare', now_ms=now_ms)


def next_record(before, event, *, now_ms, owner=None, request_digest=None, observation_digest=None):
    """Construct conformance snapshots only; never execute a request or admit authority."""
    after = deepcopy(before)
    after['revision'] += 1
    after['updated_at_ms'] = now_ms
    if event == 'claim':
        after.update(state='claimed', owner=owner, fence=before['fence'] + 1, lease_expires_at_ms=min(now_ms + POLICY['lease_ms'], before['authority_expires_at_ms']))
    elif event == 'renew':
        after['lease_expires_at_ms'] = min(now_ms + POLICY['lease_ms'], before['authority_expires_at_ms'])
    elif event == 'reserve':
        after.update(state='reserved', attempt=1, reservation={'action': 'candidate-start', 'request_digest': request_digest,
                     'credential_expires_at_ms': before['authority_expires_at_ms'], 'reserved_at_ms': now_ms,
                     'owner': before['owner'], 'fence': before['fence']})
    elif event == 'mark-unknown':
        after['state'] = 'unknown'
    elif event == 'reconcile':
        after.update(mode='reconcile', owner=owner, fence=before['fence'] + 1, lease_expires_at_ms=min(now_ms + POLICY['lease_ms'], before['authority_expires_at_ms']))
    elif event in ('observe', 'verify-cleanup'):
        after.update(state='observed' if event == 'observe' else 'cleanup-verified', observation_digest=observation_digest)
    elif event in ('close', 'block'):
        after.update(state='closed' if event == 'close' else 'blocked', owner=None, lease_expires_at_ms=0)
    return validate_transition(before, after, event=event, now_ms=now_ms)
