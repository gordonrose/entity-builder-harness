"""Closed conformance receipts and safe errors remain unsuitable as release evidence."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.finite-recovery-conformance
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject unsafe or replayed inert conformance receipt claims and redact command failures.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
from contextlib import redirect_stdout,redirect_stderr
from copy import deepcopy
import io
import json
import unittest
from unittest.mock import patch

import finite_recovery_contracts as c
import finite_recovery_conformance as subject


def fixture():
    rows=[]
    for index,phase in enumerate(subject.PHASES):
        identity=None if phase=='create-reserved' else format(index+1,'064x')
        result={'schema':'finite-recovery-result/v1','scope':'local-inert-recovery',
                'operation_id':'fixture-'+str(index),'attempt_digest':'sha256:'+format(index+1,'064x'),
                'state':'unknown' if phase=='create-reserved' else 'closed',
                'terminal_observed':phase not in ('create-reserved','create-effect'),
                'cleanup_verified':phase!='create-reserved','resource_id':identity,
                'action_counts':{'create':1,'start':0 if phase in ('create-reserved','create-effect') else 1,
                                 'inspect':1,'logs':0 if phase in ('create-reserved','create-effect') else 1,
                                 'cleanup':0 if phase=='create-reserved' else 1},
                'journal_digest':'sha256:'+'a'*64,'action_journal_digest':'sha256:'+'b'*64,
                'semantic_verdict':'unverified','product_profile_updates':[],**c.BLOCKED}
        marker=identity if phase in ('create-effect','start-effect','terminal-observed') else None
        rows.append({'case':phase,'controller_interrupted':phase!='normal','verdict':'passed',
                     'recorded_resource_id':marker,'result':result})
    files=c.fixture_files()
    result={'schema':'finite-recovery-conformance/v1','scope':'local-inert-process-recovery','verdict':'passed',
            'started_at':'2026-09-30T10:00:00Z','completed_at':'2026-09-30T10:01:00Z',
            'runner_digest':'sha256:'+'c'*64,'artifact':{'image_id':'sha256:'+'d'*64,'payload_digest':c.digest(files)},
            'payload_files':files,'engine':{'client':'28.0.1','server':'28.0.1'},'cases':rows,
            'semantic_verdict':'unverified','product_profile_updates':[],**c.BLOCKED}
    result['result_digest']=c.digest(result)
    return result


class RecoveryConformanceTests(unittest.TestCase):
    def reject(self,value):
        value['result_digest']=c.digest({key:item for key,item in value.items() if key!='result_digest'})
        with self.assertRaises(c.journal.ControlFailure):subject.validate_result(value)
    def test_complete_closed_fixture_shape_is_valid(self):subject.validate_result(fixture())
    def test_authority_flags_cannot_be_promoted_even_after_rehash(self):
        for key,value in [('authorized',True),('release_eligibility','passed'),('qualification_verdict','passed'),('semantic_verdict','verified')]:
            with self.subTest(key=key):
                result=fixture();result[key]=value;self.reject(result)
    def test_missing_duplicate_and_out_of_order_cases_fail(self):
        result=fixture();result['cases'].pop();self.reject(result)
        result=fixture();result['cases'][1]=deepcopy(result['cases'][0]);self.reject(result)
        result=fixture();result['cases'][:2]=reversed(result['cases'][:2]);self.reject(result)
    def test_negative_lookup_case_cannot_claim_completion(self):
        result=fixture();row=result['cases'][2]['result'];row.update(state='closed',cleanup_verified=True)
        self.reject(result)
    def test_replayed_operation_or_resource_identity_fails(self):
        for key in ('operation_id','attempt_digest','resource_id'):
            with self.subTest(key=key):
                result=fixture();result['cases'][1]['result'][key]=result['cases'][0]['result'][key];self.reject(result)
    def test_lost_response_identity_must_match_recorded_resource(self):
        result=fixture();result['cases'][4]['recorded_resource_id']='f'*64;self.reject(result)
        result=fixture();result['cases'][4]['recorded_resource_id']=None;self.reject(result)
    def test_payload_digest_and_dates_are_checked(self):
        result=fixture();result['artifact']['payload_digest']='sha256:'+'f'*64;self.reject(result)
        result=fixture();result['completed_at']='2026-09-30T09:00:00Z';self.reject(result)
    def test_unknown_and_secret_fields_fail(self):
        result=fixture();result['cases'][0]['result']['secret_value']='PRIVATE_FIXTURE_CANARY';self.reject(result)
    def test_caller_selected_unqualified_image_is_refused_before_receipt_or_engine(self):
        with self.assertRaises(c.journal.ControlFailure) as found:
            subject.qualified_image('/unreadable-source','sha256:'+'f'*64)
        self.assertEqual(found.exception.code,'finite-recovery-conformance-image-not-qualified')

    def test_closed_pin_rejects_schema_extra_fields_and_changed_bindings(self):
        from pathlib import Path
        import hashlib
        import tempfile
        pin=json.loads((subject.DIRECTORY/'finite-recovery-image.lock.json').read_text())
        read=c.journal.read_source
        raw=read(subject.DIRECTORY/'fixtures/finite-jobs/Dockerfile')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            recipe=root/'scripts/04.deploy/operational-realization-gate/fixtures/finite-jobs/Dockerfile'
            recipe.parent.mkdir(parents=True);recipe.write_bytes(raw)
            receipt={'schema':'finite-job-conformance-result/v1','verdict':'passed',
                     'repository_head':pin['qualified_source_revision'],
                     'artifact':{key:pin[key] for key in ('image_id','payload_digest','recipe_digest','runtime_image','runtime_config_digest')},**c.BLOCKED}
            raw_receipt=json.dumps(receipt).encode();path=root/pin['qualification_receipt']
            path.parent.mkdir(parents=True);path.write_bytes(raw_receipt)
            pin['qualification_receipt_digest']='sha256:'+hashlib.sha256(raw_receipt).hexdigest()
            current=[pin]
            def source(path,*args):
                if Path(path)==subject.DIRECTORY/'finite-recovery-image.lock.json':return json.dumps(current[0]).encode()
                return read(path,*args)
            with patch.object(c.journal,'read_source',side_effect=source):
                self.assertEqual(subject.qualified_image(root,pin['image_id']),pin)
                for key,value in [('schema','finite-recovery-image-lock/v2'),('secret_value','PRIVATE_FIXTURE_CANARY'),
                                  ('runtime_config_digest','sha256:'+'f'*64),('qualified_source_revision','f'*40)]:
                    with self.subTest(key=key):
                        current[0]={**pin,key:value}
                        with self.assertRaises(c.journal.ControlFailure):subject.qualified_image(root,pin['image_id'])

    def test_pinned_receipt_mutation_is_refused(self):
        from pathlib import Path
        import tempfile
        pin=json.loads((subject.DIRECTORY/'finite-recovery-image.lock.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/pin['qualification_receipt'];path.parent.mkdir(parents=True)
            path.write_text('{}')
            with self.assertRaises(c.journal.ControlFailure) as found:subject.qualified_image(root,pin['image_id'])
            self.assertEqual(found.exception.code,'finite-recovery-conformance-qualification-receipt-changed')

    def public_call(self,runner_result):
        output=io.StringIO();errors=io.StringIO()
        with patch.object(subject,'run',return_value=runner_result),redirect_stdout(output),redirect_stderr(errors):
            status=subject.main(['--source-root','unused','--scratch-root','unused','--image-id','unused'])
        self.assertEqual('',errors.getvalue())
        self.assertNotIn('PRIVATE_FIXTURE_CANARY',output.getvalue())
        return status,json.loads(output.getvalue())

    def public_fixture(self):
        value=fixture();value['runner_digest']=subject._bindings()
        value['result_digest']=c.digest({key:item for key,item in value.items() if key!='result_digest'})
        return value

    def public_rejected(self,value):
        status,result=self.public_call(value)
        self.assertEqual(1,status)
        self.assertEqual([{'code':'finite-recovery-conformance-failed'}],result['findings'])
        c.validate('finite-recovery-error',result)

    def test_cli_success_is_revalidated_at_public_boundary(self):
        value=self.public_fixture();status,result=self.public_call(value)
        self.assertEqual(0,status);self.assertEqual(value,result)
        subject.validate_result(result)

    def test_cli_unsafe_extra_field_is_rejected_even_after_rehash(self):
        for nested in (False,True):
            with self.subTest(nested=nested):
                value=self.public_fixture()
                target=value['cases'][0]['result'] if nested else value
                target['password']='PRIVATE_FIXTURE_CANARY'
                value['result_digest']=c.digest({key:item for key,item in value.items() if key!='result_digest'})
                self.public_rejected(value)

    def test_cli_authority_drift_is_rejected_even_after_rehash(self):
        for key,item in [('authorized',True),('release_eligibility','passed'),('operation_authorization','passed'),
                         ('qualification_verdict','passed'),('source_closure','passed'),('semantic_verdict','verified'),
                         ('product_profile_updates',[{'profile':'PRIVATE_FIXTURE_CANARY'}])]:
            for nested in (False,True):
                with self.subTest(key=key,nested=nested):
                    value=self.public_fixture();target=value['cases'][0]['result'] if nested else value
                    target[key]=item
                    value['result_digest']=c.digest({key:item for key,item in value.items() if key!='result_digest'})
                    self.public_rejected(value)

    def test_cli_wrong_result_digest_is_rejected(self):
        value=self.public_fixture();value['result_digest']='sha256:'+'0'*64
        self.public_rejected(value)

    def test_cli_rehashed_stale_runner_binding_is_rejected(self):
        value=self.public_fixture();value['runner_digest']='sha256:'+'0'*64
        value['result_digest']=c.digest({key:item for key,item in value.items() if key!='result_digest'})
        self.public_rejected(value)

    def test_cli_missing_or_corrupt_schema_has_fixed_redacted_error(self):
        from pathlib import Path
        value=self.public_fixture()
        with patch.object(c.journal,'SCHEMA_DIR',Path('/missing-schema-PRIVATE_FIXTURE_CANARY')):
            status,result=self.public_call(value)
        self.assertEqual(1,status);c.validate('finite-recovery-error',result)
        read=c.journal.read_source
        for corrupted in (b'PRIVATE_FIXTURE_CANARY: [',b'{"PRIVATE_FIXTURE_CANARY":true}'):
            def source(path,*args):
                if Path(path).name=='finite-recovery-conformance.schema.yml':return corrupted
                return read(path,*args)
            with self.subTest(corrupted=corrupted),patch.object(c.journal,'read_source',side_effect=source):
                status,result=self.public_call(value)
            self.assertEqual(1,status);c.validate('finite-recovery-error',result)

    def test_cli_parser_and_internal_errors_are_redacted(self):
        for argv in (['--private-value','PRIVATE_FIXTURE_CANARY'],['--source-root','PRIVATE_FIXTURE_CANARY']):
            output=io.StringIO()
            with redirect_stdout(output):self.assertEqual(subject.main(argv),1)
            self.assertNotIn('PRIVATE_FIXTURE_CANARY',output.getvalue())
            c.validate('finite-recovery-error',json.loads(output.getvalue()))
        with patch.object(subject,'run',side_effect=ValueError('PRIVATE_FIXTURE_CANARY')):
            output=io.StringIO()
            with redirect_stdout(output):self.assertEqual(subject.main(['--source-root','unused','--scratch-root','unused','--image-id','unused']),1)
            self.assertNotIn('PRIVATE_FIXTURE_CANARY',output.getvalue())

if __name__=='__main__':unittest.main()
