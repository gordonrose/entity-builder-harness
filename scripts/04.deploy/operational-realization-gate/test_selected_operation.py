"""Selected journal transitions refuse stale, unauthorized and uncertain effects."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.selected-operation
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: test
#   purpose: Prove selected record bindings, bounded transitions and authority refusal.
#   portability: {class: internal, targets: [kanbien-staging]}
#   used_by:
#   - id: deploy.script.selected-operation
#     path: scripts/04.deploy/operational-realization-gate/selected_operation.py
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import selected_operation as c
import operation_journal as old
import control_store_fixtures as local

OWNER = 'b' * 32
OTHER = 'c' * 32
DIGEST = 'sha256:' + 'd' * 64

class SelectedOperationTests(unittest.TestCase):
    def setUp(self):
        self.p = c.fixture_record()
        self.claimed = c.next_record(self.p, 'claim', now_ms=1000001, owner=OWNER)
        self.reserved = c.next_record(self.claimed, 'reserve', now_ms=1000002, request_digest=DIGEST)

    def reject(self, callback, *args, **kwargs):
        with self.assertRaises(c.ControlFailure):
            callback(*args, **kwargs)

    def test_complete_normal_conformance_lifecycle(self):
        observed = c.next_record(self.reserved, 'observe', now_ms=1000003, observation_digest=DIGEST)
        clean = c.next_record(observed, 'verify-cleanup', now_ms=1000004, observation_digest=DIGEST)
        closed = c.next_record(clean, 'close', now_ms=1000005)
        self.assertEqual((closed['state'], closed['attempt'], closed['owner']), ('closed', 1, None))
        self.assertFalse(closed['authorized'])
        self.assertEqual(closed['operation_authorization'], 'blocked')

    def test_v1_unchanged_local_fixtures_remain_valid(self):
        old.validate('operation-control', local.intent())
        self.reject(c.validate_record, local.intent())
        self.reject(old.validate, 'operation-control', self.p)

    def test_missing_every_top_level_field(self):
        for key in self.p:
            with self.subTest(key=key):
                row=deepcopy(self.p);del row[key];self.reject(c.validate_record,row)

    def test_extra_unsafe_fields_at_each_record_boundary(self):
        for path in ((),('intent',),('intent','policy'),('reservation',)):
            for field in ('command','secret','provider_payload','approval_flag'):
                with self.subTest(path=path,field=field):
                    row=deepcopy(self.reserved);node=row
                    for key in path:node=node[key]
                    node[field]='unexpected';self.reject(c.validate_record,row)

    def test_selected_target_and_policy_mismatch(self):
        for key,value in (('target','other/staging'),('provider','azure'),('account','000000000000'),('region','us-east-1'),('operation','relational-bootstrap')):
            with self.subTest(key=key):
                row=deepcopy(self.p);row['intent'][key]=value;self.reject(c.validate_record,row)
        row=deepcopy(self.p);row['intent']['policy']['lease_ms']=120000
        row['intent']['policy_digest']=c.digest(row['intent']['policy']);self.reject(c.validate_record,row)

    def test_policy_digest_cannot_be_stale(self):
        row=deepcopy(self.p);row['intent']['policy_digest']=DIGEST;self.reject(c.validate_record,row)

    def test_declaration_never_grants_operation_authority(self):
        for row in (self.p,self.claimed,self.reserved):
            self.reject(c.require_execution_authority,row)
        for key,value in (('authorized',True),('operation_authorization','approved'),('release_eligibility','eligible')):
            row=deepcopy(self.p);row[key]=value;self.reject(c.validate_record,row)
        row=deepcopy(self.p);row['intent']['authority_status']='approved';self.reject(c.validate_record,row)

    def test_source_receipt_and_boolean_approval_are_not_authority(self):
        for value in ({'authorized':False,'schema':'local-build-result/v1'},True,{'approve':True}):
            self.reject(c.require_execution_authority,value)

    def test_boolean_numbers_and_bad_bindings_rejected(self):
        for key in ('revision','fence','lease_expires_at_ms','authority_expires_at_ms','attempt','updated_at_ms'):
            row=deepcopy(self.p);row[key]=True;self.reject(c.validate_record,row)
        for key in ('source_revision','image_digest','release_digest','blueprint_digest'):
            row=deepcopy(self.p);row['intent'][key]='latest';self.reject(c.validate_record,row)

    def test_claim_checks_start_and_expiry(self):
        self.reject(c.next_record,self.p,'claim',now_ms=self.p['authority_expires_at_ms'],owner=OWNER)
        self.reject(c.next_record,self.claimed,'claim',now_ms=1000002,owner=OTHER)

    def test_intent_generation_operation_and_authority_immutable(self):
        valid=c.next_record(self.claimed,'renew',now_ms=1000020)
        for key,value in (('generation','e'*32),('operation_id','different-operation'),('authority_expires_at_ms',self.p['authority_expires_at_ms']-1)):
            row=deepcopy(valid);row[key]=value;self.reject(c.validate_transition,self.claimed,row,event='renew',now_ms=1000020)
        row=deepcopy(valid);row['intent']['image_digest']=DIGEST;self.reject(c.validate_transition,self.claimed,row,event='renew',now_ms=1000020)

    def test_stale_owner_fence_revision_rejected(self):
        valid=c.next_record(self.claimed,'renew',now_ms=1000020)
        for key,value in (('owner',OTHER),('fence',0),('fence',2),('revision',1),('revision',3)):
            row=deepcopy(valid);row[key]=value;self.reject(c.validate_transition,self.claimed,row,event='renew',now_ms=1000020)

    def test_clock_regression_and_boolean_now_rejected(self):
        for now in (999999,True,1.5):self.reject(c.next_record,self.claimed,'renew',now_ms=now)

    def test_expired_lease_and_insufficient_call_budget_rejected(self):
        self.reject(c.next_record,self.claimed,'renew',now_ms=self.claimed['lease_expires_at_ms'])
        self.reject(c.next_record,self.claimed,'reserve',now_ms=self.claimed['lease_expires_at_ms']-34999,request_digest=DIGEST)

    def test_one_reservation_no_duplicate_attempt(self):
        self.reject(c.next_record,self.reserved,'reserve',now_ms=1000003,request_digest=DIGEST)
        row=deepcopy(self.reserved);row['attempt']=2;self.reject(c.validate_record,row)

    def test_reservation_identity_and_credential_expiry_bound(self):
        for key,value in (('owner',OTHER),('fence',2),('reserved_at_ms',1000001),('credential_expires_at_ms',self.p['authority_expires_at_ms']+1)):
            row=deepcopy(self.reserved);row['reservation'][key]=value
            self.reject(c.validate_transition,self.claimed,row,event='reserve',now_ms=1000002)

    def test_unknown_preserves_consumed_reservation(self):
        unknown=c.next_record(self.reserved,'mark-unknown',now_ms=1000003)
        self.assertEqual(unknown['reservation'],self.reserved['reservation'])
        self.assertEqual(unknown['attempt'],1)
        for event in ('reserve','observe','verify-cleanup','close','renew'):
            self.reject(c.next_record,unknown,event,now_ms=1000004,observation_digest=DIGEST,request_digest=DIGEST)

    def test_unknown_reconciliation_changes_owner_only_after_lease_expiry(self):
        unknown=c.next_record(self.reserved,'mark-unknown',now_ms=1000003)
        self.reject(c.next_record,unknown,'reconcile',now_ms=1000004,owner=OTHER)
        reconciled=c.next_record(unknown,'reconcile',now_ms=unknown['lease_expires_at_ms'],owner=OTHER)
        self.assertEqual((reconciled['fence'],reconciled['mode'],reconciled['state']),(2,'reconcile','unknown'))
        self.assertEqual(reconciled['reservation'],unknown['reservation'])
        for event in ('reserve','observe','verify-cleanup','close'):
            self.reject(c.next_record,reconciled,event,now_ms=1060002,observation_digest=DIGEST,request_digest=DIGEST)

    def test_unknown_cannot_reconcile_with_old_owner_or_after_authority_window(self):
        unknown=c.next_record(self.reserved,'mark-unknown',now_ms=1000003)
        self.reject(c.next_record,unknown,'reconcile',now_ms=1060001,owner=OWNER)
        self.reject(c.next_record,unknown,'reconcile',now_ms=unknown['authority_expires_at_ms'],owner=OTHER)

    def test_unknown_can_be_blocked_without_releasing_reservation(self):
        unknown=c.next_record(self.reserved,'mark-unknown',now_ms=1000003)
        blocked=c.next_record(unknown,'block',now_ms=9000000)
        self.assertEqual(blocked['reservation'],unknown['reservation'])
        self.assertEqual(blocked['state'],'blocked')
        self.reject(c.next_record,blocked,'claim',now_ms=9000001,owner=OTHER)

    def test_observation_requires_reservation_and_cleanup_before_close(self):
        self.reject(c.next_record,self.claimed,'observe',now_ms=1000002,observation_digest=DIGEST)
        observed=c.next_record(self.reserved,'observe',now_ms=1000003,observation_digest=DIGEST)
        self.reject(c.next_record,observed,'close',now_ms=1000004)
        self.reject(c.next_record,self.reserved,'observe',now_ms=1000003)

    def test_terminal_record_cannot_reopen(self):
        blocked=c.next_record(self.p,'block',now_ms=1000001)
        self.reject(c.next_record,blocked,'claim',now_ms=1000002,owner=OWNER)

    def test_unknown_event_and_schema_version_rejected(self):
        self.reject(c.next_record,self.p,'approve',now_ms=1000001)
        raw=old.read_source(old.SCHEMA_DIR/'operation-control.schema.yml')
        self.reject(old._parse_schema,'operation-control',raw,version='v3')
        self.reject(old._parse_schema,'operation-control',raw,version='v2')
        self.reject(c.load_schema,'operation-control')

    def test_schema_duplicate_open_remote_ref_and_identity_rejected(self):
        raw=old.read_source(c.SCHEMA_DIR/'selected-operation-record.schema.yml')
        variants=(raw.replace(b'"additionalProperties": false',b'"additionalProperties": true',1),raw.replace(b'"$id":',b'"$ref": "https://invalid.example/schema", "$id":',1),raw.replace(b'"$id":',b'"$id": "duplicate", "$id":',1),raw.replace(b':v2"',b':v1"',1))
        with tempfile.TemporaryDirectory() as folder:
            for content in variants:
                Path(folder,'selected-operation-record.schema.yml').write_bytes(content)
                with patch.object(c,'SCHEMA_DIR',Path(folder)):
                    self.reject(c.validate_record,self.p)

    def test_record_rejects_impossible_revision_and_reservation_owner(self):
        for key,value in (('revision',0),('fence',3)):
            row=deepcopy(self.claimed);row[key]=value;self.reject(c.validate_record,row)
        row=deepcopy(self.reserved);row['reservation']['owner']=OTHER;self.reject(c.validate_record,row)

    def test_physical_positive_and_negative_fixtures(self):
        directory=Path(__file__).resolve().parent/'fixtures/selected-operation'
        good=old.decode(old.read_source(directory/'valid-record.json'))
        bad=old.decode(old.read_source(directory/'invalid-authority.json'))
        c.validate_record(good)
        self.reject(c.validate_record,bad)

    def test_credential_expiry_must_cover_call_and_safety_margin(self):
        for remaining in (29999,30000,34999):
            row=deepcopy(self.reserved)
            row['reservation']['credential_expires_at_ms']=1000002+remaining
            self.reject(c.validate_transition,self.claimed,row,event='reserve',now_ms=1000002)
        row=deepcopy(self.reserved)
        row['reservation']['credential_expires_at_ms']=1035002
        c.validate_transition(self.claimed,row,event='reserve',now_ms=1000002)

if __name__ == '__main__':unittest.main()
