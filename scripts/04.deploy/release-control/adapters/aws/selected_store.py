"""Conditional AWS request seam for selected operation conformance; no live transport."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.aws-selected-store
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Encode conditional shared journal and immutable evidence requests without activating AWS or effect execution.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [network]
#   used_by:
#   - id: deploy.test.aws-selected-store
#     path: scripts/04.deploy/operational-realization-gate/test_selected_store.py
import base64
from copy import deepcopy
import hashlib
import re
import uuid

import operation_journal as journal
import selected_operation as contract
from selected_store_evidence import validate_evidence

ACCOUNT = '337159794548'
REGION = 'eu-west-1'
TABLE = 'kanbien-staging-platform-shell-release-control'
BUCKET = 'kanbien-staging-platform-shell-release-evidence-337159794548'
PREFIX = 'kanbien/staging/operations/'
PARTITION = 'selected-control/v2/kanbien/staging'
CAPABILITIES = {'scope': 'injected-shared-store-conformance', 'live_proven': False,
                'authorized': False, 'release_eligibility': 'blocked',
                'operation_authorization': 'blocked'}


class ConditionalConflict(Exception):
    """Injected transport attests a definite, wholly rejected conditional write.

    An eventual live transport must map ONLY a proven conditional rejection here;
    timeout, cancellation, throttling and unclassified errors remain uncertain.
    """


class SelectedStore:
    """One fixed selected scope. The injected transport is mandatory and private.

    No SDK, shell, subprocess, credentials, network or transport factory exists
    in this module. Store names are proposed source bindings, not live resources.
    """
    def __init__(self, generation, *, _transport):
        if type(generation) is not str or not re.fullmatch('[0-9a-f]{32}', generation):
            journal.fail('store-generation-invalid')
        if not callable(_transport):
            journal.fail('transport-required')
        self.generation = generation
        self._transport = _transport
        self._quarantined = False

    def _send(self, service, operation, parameters, *, mutation=False):
        if mutation and self._quarantined:
            journal.fail('store-reconciliation-required')
        request = {'service': service, 'operation': operation, 'region': REGION,
                   'parameters': deepcopy(parameters)}
        try:
            response = self._transport(request)
        except ConditionalConflict:
            journal.fail('store-conditional-conflict')
        except Exception:
            if mutation:
                self._quarantined = True
            journal.fail('store-outcome-unknown' if mutation else 'store-read-unavailable')
        if type(response) is not dict:
            if mutation:
                self._quarantined = True
            journal.fail('store-response-invalid')
        return response

    @staticmethod
    def _key(suffix):
        return {'pk': {'S': PARTITION}, 'sk': {'S': suffix}}

    def _item(self, suffix, value):
        return {**self._key(suffix), 'digest': {'S': contract.digest(value)},
                'document': {'S': journal.canonical(value).decode('ascii')},
                'generation': {'S': self.generation}}

    def _decode(self, item, suffix):
        if (type(item) is not dict or set(item) != {'pk', 'sk', 'digest', 'document', 'generation'}
                or {key: item[key] for key in ('pk', 'sk')} != self._key(suffix)
                or item['generation'] != {'S': self.generation}
                or type(item['document']) is not dict or set(item['document']) != {'S'}):
            journal.fail('store-record-corrupt')
        value = journal.decode(item['document']['S'])
        if item['digest'] != {'S': contract.digest(value)}:
            journal.fail('store-record-corrupt')
        return value

    def _generation_check(self):
        return {'ConditionCheck': {'TableName': TABLE, 'Key': self._key('generation'),
                 'ConditionExpression': '#g = :g',
                 'ExpressionAttributeNames': {'#g': 'generation'},
                 'ExpressionAttributeValues': {':g': {'S': self.generation}}}}

    def _put(self, suffix, value, previous):
        request = {'TableName': TABLE, 'Item': self._item(suffix, value)}
        if previous is None:
            request.update(ConditionExpression='attribute_not_exists(#pk)',
                           ExpressionAttributeNames={'#pk': 'pk'})
        else:
            request.update(ConditionExpression='#d = :d AND #g = :g',
                           ExpressionAttributeNames={'#d': 'digest', '#g': 'generation'},
                           ExpressionAttributeValues={':d': {'S': contract.digest(previous)},
                                                      ':g': {'S': self.generation}})
        return {'Put': request}

    def read(self):
        """Transactional generation and selected-scope snapshot; no ownership grant."""
        response = self._send('dynamodb', 'TransactGetItems', {'TransactItems': [
            {'Get': {'TableName': TABLE, 'Key': self._key(suffix)}}
            for suffix in ('generation', 'scope')]})
        rows = response.get('Responses')
        if set(response) != {'Responses'}:
            journal.fail('store-response-invalid')
        if (type(rows) is not list or len(rows) != 2 or any(type(row) is not dict for row in rows)
                or set(rows[0]) != {'Item'}
                or rows[0].get('Item') != {**self._key('generation'), 'generation': {'S': self.generation}}):
            journal.fail('store-generation-mismatch')
        if not rows[1]:
            return None
        if set(rows[1]) != {'Item'}:
            journal.fail('store-record-corrupt')
        value = self._decode(rows[1]['Item'], 'scope')
        contract.validate_record(value)
        if value['generation'] != self.generation:
            journal.fail('store-generation-mismatch')
        return value

    def apply(self, before, after, *, event, now_ms, evidence_reference=None):
        """Atomic scope/operation CAS and append-only event, after pure validation.

        A result is a persisted conformance record, never permission to dispatch.
        There is no retry. Unknown response quarantines this instance; a future
        controller must reconcile through independently observed shared records.
        This in-memory quarantine alone does not survive a process restart.
        """
        contract.validate_transition(before, after, event=event, now_ms=now_ms)
        if after['generation'] != self.generation or before is not None and before['generation'] != self.generation:
            journal.fail('store-generation-mismatch')
        # This first seam retains one operation for its lifetime. Reusing a closed
        # scope for another operation needs the separately reviewed controller.
        if before is not None and before['operation_id'] != after['operation_id']:
            journal.fail('operation-binding-invalid')
        if event in ('observe', 'verify-cleanup'):
            if before is None or evidence_reference is None:
                journal.fail('evidence-required')
            evidence = self.read_evidence(evidence_reference)
            expected_assertion = 'fixture-observation' if event == 'observe' else 'fixture-cleanup'
            if (evidence['record_digest'] != contract.digest(before)
                    or evidence['operation_id'] != after['operation_id']
                    or evidence['subject_digest'] != after['intent']['image_digest']
                    or evidence['assertion'] != expected_assertion or evidence['verdict'] != 'passed'
                    or evidence['observed_at_ms'] < before['updated_at_ms']
                    or evidence['observed_at_ms'] > now_ms or evidence['expires_at_ms'] <= now_ms
                    or evidence['expires_at_ms'] > after['authority_expires_at_ms']
                    or after['observation_digest'] != contract.digest(evidence)):
                journal.fail('evidence-binding-invalid')
        elif evidence_reference is not None:
            journal.fail('evidence-unexpected')
        operation = after['operation_id']
        event_value = {'schema': 'selected-store-event/v2', 'operation_id': operation,
                       'generation': self.generation, 'revision': after['revision'],
                       'event': event, 'observed_at_ms': now_ms,
                       'previous_digest': None if before is None else contract.digest(before),
                       'record_digest': contract.digest(after), 'evidence_reference': evidence_reference, 'authorized': False}
        contract.validate('selected-store-event', event_value)
        items = [self._generation_check(), self._put('scope', after, before),
                 self._put('operation/' + operation, after, before),
                 self._put('event/' + operation + '/' + str(after['revision']), event_value, None)]
        # A fresh submission token prevents DynamoDB's ten-minute idempotency
        # cache from returning an old success instead of evaluating these CAS
        # conditions. This adapter does not retry a dispatched request.
        parameters = {'TransactItems': items, 'ClientRequestToken': uuid.uuid4().hex}
        response = self._send('dynamodb', 'TransactWriteItems', parameters, mutation=True)
        # The eventual SDK adapter must strip transport metadata to this closed
        # shape. Arbitrary provider output is never accepted as an acknowledgement.
        if response != {}:
            self._quarantined = True
            journal.fail('store-response-invalid')
        return {'record_digest': contract.digest(after), 'revision': after['revision'], **CAPABILITIES}

    def put_evidence(self, value):
        """Conditional create then version-specific readback before returning link."""
        validate_evidence(value)
        if value['generation'] != self.generation:
            journal.fail('store-generation-mismatch')
        current = self.read()
        if (current is None or current['operation_id'] != value['operation_id']
                or contract.digest(current) != value['record_digest']
                or current['intent']['image_digest'] != value['subject_digest']
                or current['state'] not in ('reserved', 'observed')
                or value['observed_at_ms'] < current['updated_at_ms']
                or value['expires_at_ms'] > current['authority_expires_at_ms']):
            journal.fail('evidence-binding-invalid')
        raw = journal.canonical(value)
        digest = contract.digest(value)
        checksum = base64.b64encode(hashlib.sha256(raw).digest()).decode('ascii')
        key = PREFIX + self.generation + '/' + value['operation_id'] + '/' + digest[7:] + '.json'
        response = self._send('s3', 'PutObject', {'Bucket': BUCKET, 'Key': key,
            'ExpectedBucketOwner': ACCOUNT, 'IfNoneMatch': '*', 'Body': raw,
            'ContentType': 'application/json', 'ServerSideEncryption': 'AES256',
            'ChecksumSHA256': checksum}, mutation=True)
        version = response.get('VersionId')
        if (set(response) != {'VersionId', 'ChecksumSHA256', 'ServerSideEncryption'}
                or type(version) is not str or not re.fullmatch('[A-Za-z0-9._~+/=-]{1,256}', version)
                or version == 'null' or response.get('ChecksumSHA256') != checksum
                or response.get('ServerSideEncryption') != 'AES256'):
            self._quarantined = True
            journal.fail('evidence-write-unverified')
        reference = {'generation': self.generation, 'operation_id': value['operation_id'],
                     'digest': digest, 'version_id': version}
        try:
            observed = self.read_evidence(reference)
        except journal.ControlFailure:
            self._quarantined = True
            raise
        if journal.canonical(observed) != raw:
            self._quarantined = True
            journal.fail('evidence-readback-mismatch')
        return reference

    def read_evidence(self, reference):
        if (type(reference) is not dict or set(reference) != {'generation', 'operation_id', 'digest', 'version_id'}
                or reference['generation'] != self.generation):
            journal.fail('evidence-reference-invalid')
        journal.identifier(reference['operation_id'])
        if type(reference['digest']) is not str or not journal.DIGEST.fullmatch(reference['digest']):
            journal.fail('evidence-reference-invalid')
        version = reference['version_id']
        if type(version) is not str or not re.fullmatch('[A-Za-z0-9._~+/=-]{1,256}', version) or version == 'null':
            journal.fail('evidence-reference-invalid')
        key = PREFIX + self.generation + '/' + reference['operation_id'] + '/' + reference['digest'][7:] + '.json'
        response = self._send('s3', 'GetObject', {'Bucket': BUCKET, 'Key': key,
            'ExpectedBucketOwner': ACCOUNT, 'VersionId': version, 'ChecksumMode': 'ENABLED'})
        body = response.get('Body')
        if (set(response) != {'Body', 'VersionId', 'ChecksumSHA256', 'ContentLength', 'ServerSideEncryption'}
                or type(body) is not bytes or len(body) > journal.MAX_BYTES):
            journal.fail('evidence-readback-invalid')
        checksum = base64.b64encode(hashlib.sha256(body).digest()).decode('ascii')
        if (response.get('VersionId') != version or response.get('ChecksumSHA256') != checksum
                or response.get('ServerSideEncryption') != 'AES256'
                or type(response.get('ContentLength')) is not int or response['ContentLength'] != len(body)):
            journal.fail('evidence-readback-invalid')
        value = journal.decode(body)
        validate_evidence(value)
        if (value['generation'] != self.generation or value['operation_id'] != reference['operation_id']
                or contract.digest(value) != reference['digest'] or journal.canonical(value) != body):
            journal.fail('evidence-readback-mismatch')
        return value
