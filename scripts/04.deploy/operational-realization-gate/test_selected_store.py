"""Independent conditional transport fixtures, no network or AWS credentials."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.aws-selected-store
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise conditional journal races, unknown responses and versioned evidence readback with injected transports.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py
import base64
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import threading
import unittest

import operation_journal as journal
import selected_operation as contract
from selected_store_evidence import validate_evidence

SPEC = importlib.util.spec_from_file_location('selected_store', Path(__file__).resolve().parents[1] / 'release-control/adapters/aws/selected_store.py')
backend = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backend)


class MemoryTransport:
    """Models atomic conditional puts, independent from backend record validation."""
    def __init__(self, generation='a' * 32):
        self.calls = []
        self.rows = {'generation': {'pk': {'S': backend.PARTITION}, 'sk': {'S': 'generation'},
                                   'generation': {'S': generation}}}
        self.objects = {}
        self.lock = threading.Lock()
        self.failure = None
        self.mutate_response = None

    def __call__(self, request):
        self.calls.append(deepcopy(request))
        service, operation, p = request['service'], request['operation'], request['parameters']
        if request['region'] != backend.REGION:
            raise AssertionError('unexpected region')
        with self.lock:
            if self.failure == 'before':
                self.failure = None
                raise TimeoutError('private provider diagnostic must not escape')
            if service == 'dynamodb' and operation == 'TransactGetItems':
                result = {'Responses': []}
                for entry in p['TransactItems']:
                    self._table(entry['Get'])
                    item = self.rows.get(entry['Get']['Key']['sk']['S'])
                    result['Responses'].append({} if item is None else {'Item': deepcopy(item)})
            elif service == 'dynamodb' and operation == 'TransactWriteItems':
                changes = {}
                seen = set()
                for entry in p['TransactItems']:
                    op, value = next(iter(entry.items()))
                    self._table(value)
                    key = value.get('Key', value.get('Item'))['sk']['S']
                    if key in seen:
                        raise AssertionError('duplicate item transaction')
                    seen.add(key)
                    previous = self.rows.get(key)
                    expression = value['ConditionExpression']
                    if expression == '#g = :g':
                        valid = previous is not None and previous.get('generation') == value['ExpressionAttributeValues'][':g']
                    elif expression == 'attribute_not_exists(#pk)':
                        valid = previous is None
                    elif expression == '#d = :d AND #g = :g':
                        valid = (previous is not None and previous.get('digest') == value['ExpressionAttributeValues'][':d']
                                 and previous.get('generation') == value['ExpressionAttributeValues'][':g'])
                    else:
                        raise AssertionError('unsupported conditional expression')
                    if not valid:
                        raise backend.ConditionalConflict()
                    if op == 'Put':
                        changes[key] = deepcopy(value['Item'])
                self.rows.update(changes)
                result = {}
            elif service == 's3' and operation == 'PutObject':
                self._bucket(p)
                assert p['IfNoneMatch'] == '*' and p['ServerSideEncryption'] == 'AES256'
                assert p['ContentType'] == 'application/json'
                checksum = base64.b64encode(hashlib.sha256(p['Body']).digest()).decode()
                assert checksum == p['ChecksumSHA256']
                if p['Key'] in self.objects:
                    raise backend.ConditionalConflict()
                self.objects[p['Key']] = {'Body': p['Body'], 'VersionId': 'fixture-version-1',
                    'ChecksumSHA256': checksum, 'ContentLength': len(p['Body']), 'ServerSideEncryption': 'AES256'}
                result = {k: self.objects[p['Key']][k] for k in ('VersionId', 'ChecksumSHA256', 'ServerSideEncryption')}
            elif service == 's3' and operation == 'GetObject':
                self._bucket(p)
                assert p['ChecksumMode'] == 'ENABLED'
                result = deepcopy(self.objects[p['Key']])
                if p['VersionId'] != result['VersionId']:
                    raise LookupError('no such version')
            else:
                raise AssertionError('unexpected request')
            if self.failure == 'after':
                self.failure = None
                raise TimeoutError('private provider diagnostic must not escape')
            if self.mutate_response:
                result = self.mutate_response(service, operation, result)
            return result

    @staticmethod
    def _table(value):
        assert value['TableName'] == backend.TABLE
        assert value.get('Key', value.get('Item'))['pk'] == {'S': backend.PARTITION}

    @staticmethod
    def _bucket(value):
        assert value['Bucket'] == backend.BUCKET
        assert value['ExpectedBucketOwner'] == backend.ACCOUNT
        assert value['Key'].startswith(backend.PREFIX)


class SelectedStoreTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000000
        self.transport = MemoryTransport()
        self.store = backend.SelectedStore('a' * 32, _transport=self.transport)
        self.current = None

    def reject(self, code, fn, *args, **kwargs):
        with self.assertRaises(journal.ControlFailure) as caught:
            fn(*args, **kwargs)
        if code is not None:
            self.assertEqual(caught.exception.code, code)
        self.assertNotIn('private provider', str(caught.exception))

    def prepare(self):
        after = contract.fixture_record(now_ms=self.now)
        result = self.store.apply(None, after, event='prepare', now_ms=self.now)
        self.current = after
        return result

    def advance(self, event, **kwargs):
        after = contract.next_record(self.current, event, now_ms=self.now, **kwargs)
        result = self.store.apply(self.current, after, event=event, now_ms=self.now)
        self.current = after
        return result

    def reserve(self):
        self.prepare()
        self.advance('claim', owner='b' * 32)
        self.advance('reserve', request_digest='sha256:' + 'c' * 64)

    def evidence(self, assertion='fixture-observation', **changes):
        value = {'schema': 'selected-operation-evidence/v2', 'generation': 'a' * 32,
                 'operation_id': self.current['operation_id'], 'record_digest': contract.digest(self.current),
                 'assertion': assertion, 'verdict': 'passed', 'subject_digest': self.current['intent']['image_digest'],
                 'observed_at_ms': self.now, 'expires_at_ms': self.now + 1000, 'authorized': False}
        value.update(changes)
        return value

    def test_prepare_atomic_record_and_event_and_authority_blocked(self):
        result = self.prepare()
        self.assertFalse(result['authorized'])
        self.assertEqual(result['operation_authorization'], 'blocked')
        self.assertEqual(self.store.read(), self.current)
        self.assertEqual(len(self.transport.rows), 4)
        write = self.transport.calls[0]['parameters']
        self.assertEqual(len(write['TransactItems']), 4)
        self.assertLessEqual(len(write['ClientRequestToken']), 36)

    def test_empty_store_read_does_not_create_anything(self):
        self.assertIsNone(self.store.read())
        self.assertEqual(len(self.transport.rows), 1)

    def test_initial_generation_must_exist(self):
        self.transport.rows.clear()
        self.reject('store-conditional-conflict', self.prepare)
        self.assertEqual(self.transport.rows, {})

    def test_same_revision_competing_claim_only_one_writer(self):
        self.prepare()
        before = deepcopy(self.current)
        a = contract.next_record(before, 'claim', now_ms=self.now, owner='b' * 32)
        b = contract.next_record(before, 'claim', now_ms=self.now, owner='c' * 32)
        self.store.apply(before, a, event='claim', now_ms=self.now)
        other = backend.SelectedStore('a' * 32, _transport=self.transport)
        self.reject('store-conditional-conflict', other.apply, before, b, event='claim', now_ms=self.now)
        tokens = [x['parameters']['ClientRequestToken'] for x in self.transport.calls if x['operation'] == 'TransactWriteItems']
        self.assertEqual(len(tokens), len(set(tokens)))
        self.assertEqual(other.read(), a)
        self.assertEqual(len(self.transport.rows), 5)

    def test_other_operation_cannot_take_unresolved_scope(self):
        self.prepare()
        after = contract.fixture_record(now_ms=self.now, operation_id='another-operation')
        self.reject('store-conditional-conflict', self.store.apply, None, after, event='prepare', now_ms=self.now)
        self.assertFalse(any('another-operation' in key for key in self.transport.rows))

    def test_lost_committed_response_quarantines_no_automatic_retry(self):
        self.transport.failure = 'after'
        self.reject('store-outcome-unknown', self.prepare)
        count = len(self.transport.calls)
        self.reject('store-reconciliation-required', self.prepare)
        self.assertEqual(len(self.transport.calls), count)
        fresh = backend.SelectedStore('a' * 32, _transport=self.transport)
        self.assertEqual(fresh.read()['state'], 'prepared')

    def test_lost_uncommitted_response_also_quarantines(self):
        self.transport.failure = 'before'
        self.reject('store-outcome-unknown', self.prepare)
        self.assertEqual(len(self.transport.rows), 1)
        self.reject('store-reconciliation-required', self.prepare)

    def test_malformed_write_acknowledgement_quarantines(self):
        self.transport.mutate_response = lambda s, o, r: {'surprise': 'raw'} if o == 'TransactWriteItems' else r
        self.reject('store-response-invalid', self.prepare)
        self.reject('store-reconciliation-required', self.prepare)

    def test_restored_generation_rejects_stale_writer(self):
        self.prepare()
        after = contract.next_record(self.current, 'claim', now_ms=self.now, owner='b' * 32)
        self.transport.rows['generation']['generation'] = {'S': 'f' * 32}
        self.reject('store-conditional-conflict', self.store.apply, self.current, after, event='claim', now_ms=self.now)
        self.reject('store-generation-mismatch', self.store.read)

    def test_tampered_snapshot_digest_rejected(self):
        self.prepare()
        self.transport.rows['scope']['digest'] = {'S': 'sha256:' + 'f' * 64}
        self.reject('store-record-corrupt', self.store.read)

    def test_unknown_fields_refused_before_transport(self):
        value = contract.fixture_record(now_ms=self.now)
        value['secret'] = 'not-allowed'
        self.reject(None, self.store.apply, None, value, event='prepare', now_ms=self.now)
        self.assertEqual(self.transport.calls, [])

    def test_exact_evidence_version_and_digest_readback(self):
        self.reserve()
        value = self.evidence()
        reference = self.store.put_evidence(value)
        self.assertEqual(reference['digest'], contract.digest(value))
        self.assertEqual(self.store.read_evidence(reference), value)
        put = next(x['parameters'] for x in self.transport.calls if x['operation'] == 'PutObject')
        self.assertEqual(put['IfNoneMatch'], '*')
        self.assertTrue(put['Key'].endswith(contract.digest(value)[7:] + '.json'))

    def test_duplicate_evidence_cannot_overwrite(self):
        self.reserve()
        self.store.put_evidence(self.evidence())
        self.reject('store-conditional-conflict', self.store.put_evidence, self.evidence())
        self.assertEqual(len(self.transport.objects), 1)

    def test_unknown_s3_write_quarantines_and_retains_object(self):
        self.reserve()
        def transport(request):
            result = self.transport(request)
            if request['operation'] == 'PutObject':
                raise TimeoutError('private')
            return result
        self.store._transport = transport
        self.reject('store-outcome-unknown', self.store.put_evidence, self.evidence())
        self.assertEqual(len(self.transport.objects), 1)
        self.reject('store-reconciliation-required', self.store.put_evidence, self.evidence())

    def test_readback_bad_version_checksum_encryption_length_or_body_rejected(self):
        for field, replacement in [('VersionId', 'wrong'), ('ChecksumSHA256', 'wrong'),
                                   ('ServerSideEncryption', 'aws:kms'), ('ContentLength', True), ('Body', b'{}')]:
            with self.subTest(field=field):
                self.setUp()
                self.reserve()
                self.transport.mutate_response = lambda s, o, r, f=field, x=replacement: {**r, f: x} if o == 'GetObject' else r
                self.reject(None, self.store.put_evidence, self.evidence())
                self.assertTrue(self.store._quarantined)

    def test_null_version_rejected(self):
        self.reserve()
        self.transport.mutate_response = lambda s, o, r: {**r, 'VersionId': 'null'} if o == 'PutObject' else r
        self.reject('evidence-write-unverified', self.store.put_evidence, self.evidence())

    def test_evidence_cannot_bind_other_record_or_image(self):
        self.reserve()
        for field in ('record_digest', 'subject_digest'):
            with self.subTest(field=field):
                self.reject('evidence-binding-invalid', self.store.put_evidence,
                            self.evidence(**{field: 'sha256:' + 'f' * 64}))
        self.assertFalse(any(x['service'] == 's3' for x in self.transport.calls))

    def test_raw_log_secret_authority_fields_not_evidence(self):
        self.reserve()
        for field in ('raw_log', 'secret', 'authorization'):
            with self.subTest(field=field):
                self.reject(None, self.store.put_evidence, self.evidence(**{field: 'forbidden'}))
        self.reject(None, self.store.put_evidence, self.evidence(authorized=True))

    def test_evidence_lifetime_is_bounded(self):
        self.reserve()
        for expires in (self.now, self.now - 1, self.now + 900001):
            self.reject('evidence-lifetime-invalid', validate_evidence, self.evidence(expires_at_ms=expires))

    def test_observation_requires_exact_versioned_evidence_link(self):
        self.reserve()
        value = self.evidence()
        after = contract.next_record(self.current, 'observe', now_ms=self.now, observation_digest=contract.digest(value))
        self.reject('evidence-required', self.store.apply, self.current, after, event='observe', now_ms=self.now)
        reference = self.store.put_evidence(value)
        result = self.store.apply(self.current, after, event='observe', now_ms=self.now, evidence_reference=reference)
        self.assertFalse(result['authorized'])
        self.assertEqual(self.store.read()['state'], 'observed')

    def test_expired_or_failed_evidence_cannot_be_linked(self):
        for changes in ({'expires_at_ms': self.now + 1}, {'verdict': 'failed'}, {'assertion': 'fixture-cleanup'}):
            with self.subTest(changes=changes):
                self.setUp()
                self.reserve()
                value = self.evidence(**changes)
                reference = self.store.put_evidence(value)
                after = contract.next_record(self.current, 'observe', now_ms=self.now + 2, observation_digest=contract.digest(value))
                self.reject('evidence-binding-invalid', self.store.apply, self.current, after,
                            event='observe', now_ms=self.now + 2, evidence_reference=reference)

    def test_arbitrary_evidence_reference_fields_refused(self):
        self.reserve()
        reference = self.store.put_evidence(self.evidence())
        for change in ({'bucket': 'other'}, {'version_id': 'null'}, {'operation_id': '../secret'}, {'generation': 'b' * 32}):
            self.reject(None, self.store.read_evidence, {**reference, **change})

    def test_duplicate_reservation_refused_without_provider_request(self):
        self.reserve()
        count = len(self.transport.calls)
        self.reject(None, contract.next_record, self.current, 'reserve', now_ms=self.now,
                    request_digest='sha256:' + 'e' * 64)
        self.assertEqual(len(self.transport.calls), count)

    def test_concurrent_clients_use_one_atomic_writer(self):
        self.prepare()
        before = deepcopy(self.current)
        barrier = threading.Barrier(2)
        outcomes = []
        def compete(owner):
            store = backend.SelectedStore('a' * 32, _transport=self.transport)
            after = contract.next_record(before, 'claim', now_ms=self.now, owner=owner)
            barrier.wait(timeout=5)
            try:
                store.apply(before, after, event='claim', now_ms=self.now)
                outcomes.append('accepted')
            except journal.ControlFailure as error:
                outcomes.append(error.code)
        clients = [threading.Thread(target=compete, args=(owner * 32,)) for owner in ('b', 'c')]
        for client in clients:
            client.start()
        for client in clients:
            client.join(timeout=5)
            self.assertFalse(client.is_alive())
        self.assertCountEqual(outcomes, ['accepted', 'store-conditional-conflict'])

    def test_complete_fixture_evidence_chain_closes_without_authority(self):
        self.reserve()
        for event, assertion in [('observe', 'fixture-observation'), ('verify-cleanup', 'fixture-cleanup')]:
            value = self.evidence(assertion)
            reference = self.store.put_evidence(value)
            after = contract.next_record(self.current, event, now_ms=self.now, observation_digest=contract.digest(value))
            self.store.apply(self.current, after, event=event, now_ms=self.now, evidence_reference=reference)
            self.current = after
        self.advance('close')
        self.assertEqual(self.store.read()['state'], 'closed')
        self.reject(None, contract.require_execution_authority, self.store.read())
        self.assertEqual(len(self.transport.objects), 2)

    def test_lease_expiry_reconciliation_preserves_consumed_reservation(self):
        self.reserve()
        reservation = deepcopy(self.current['reservation'])
        old = deepcopy(self.current)
        self.advance('mark-unknown')
        self.now += 60001
        self.advance('reconcile', owner='d' * 32)
        self.assertEqual(self.current['reservation'], reservation)
        self.assertEqual(self.current['attempt'], 1)
        self.assertEqual(self.current['mode'], 'reconcile')
        self.reject(None, contract.next_record, self.current, 'reserve', now_ms=self.now,
                    request_digest='sha256:' + 'f' * 64)
        self.reject(None, contract.next_record, self.current, 'observe', now_ms=self.now,
                    observation_digest='sha256:' + 'e' * 64)
        after = contract.next_record(old, 'mark-unknown', now_ms=old['updated_at_ms'])
        self.reject('store-conditional-conflict', self.store.apply, old, after,
                    event='mark-unknown', now_ms=old['updated_at_ms'])

    def test_evidence_uploaded_but_link_response_lost_never_replays(self):
        self.reserve()
        before = deepcopy(self.current)
        value = self.evidence()
        reference = self.store.put_evidence(value)
        after = contract.next_record(before, 'observe', now_ms=self.now, observation_digest=contract.digest(value))
        self.transport.failure = 'after'
        # The evidence read happens first; inject loss only at journal commit.
        def lose_link(request):
            if request['operation'] != 'TransactWriteItems':
                self.transport.failure = None
                return self.transport(request)
            self.transport.failure = 'after'
            return self.transport(request)
        self.store._transport = lose_link
        self.reject('store-outcome-unknown', self.store.apply, before, after,
                    event='observe', now_ms=self.now, evidence_reference=reference)
        self.assertEqual(len(self.transport.objects), 1)
        self.assertTrue(self.store._quarantined)
        restarted = backend.SelectedStore('a' * 32, _transport=self.transport)
        self.assertFalse(restarted._quarantined)  # Explicit process-local limitation.
        self.assertEqual(restarted.read()['state'], 'observed')
        self.assertEqual(restarted.read_evidence(reference), value)
        self.reject(None, contract.require_execution_authority, restarted.read())
        self.reject('store-conditional-conflict', restarted.apply, before, after,
                    event='observe', now_ms=self.now, evidence_reference=reference)

    def test_unbounded_or_malformed_read_response_rejected_safely(self):
        self.prepare()
        original = deepcopy(self.transport.rows['scope'])
        for document in ('x' * (journal.MAX_BYTES + 1), 10, {'secret': 'value'}):
            with self.subTest(document_type=type(document).__name__):
                self.transport.rows['scope'] = deepcopy(original)
                self.transport.rows['scope']['document'] = {'S': document}
                self.reject(None, self.store.read)
        self.transport.rows['scope'] = deepcopy(original)
        self.transport.mutate_response = lambda s, o, r: {'Responses': 'wrong'} if o == 'TransactGetItems' else r
        self.reject('store-generation-mismatch', self.store.read)

    def test_unbounded_evidence_readback_rejected_before_decode(self):
        self.reserve()
        reference = self.store.put_evidence(self.evidence())
        self.transport.mutate_response = lambda s, o, r: {**r, 'Body': b'x' * (journal.MAX_BYTES + 1)} if o == 'GetObject' else r
        self.reject('evidence-readback-invalid', self.store.read_evidence, reference)

    def test_renew_after_another_revision_cannot_replace_new_owner_or_state(self):
        self.prepare()
        self.advance('claim', owner='b' * 32)
        old = deepcopy(self.current)
        self.now += 1
        self.advance('renew')
        changed = contract.next_record(old, 'renew', now_ms=self.now + 1)
        self.reject('store-conditional-conflict', self.store.apply, old, changed,
                    event='renew', now_ms=self.now + 1)
        self.assertEqual(self.store.read(), self.current)

    def test_no_default_transport_or_arbitrary_target_surface(self):
        with self.assertRaises(TypeError):
            backend.SelectedStore('a' * 32)
        with self.assertRaises(TypeError):
            backend.SelectedStore('a' * 32, _transport=self.transport, bucket='arbitrary')
        self.reject('transport-required', backend.SelectedStore, 'a' * 32, _transport=None)
        self.reject('store-generation-invalid', backend.SelectedStore, '../bad', _transport=self.transport)


if __name__ == '__main__':
    unittest.main()
