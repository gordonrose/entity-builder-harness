"""Separate local prerequisites: strict identities, immutable bindings and no observed effects."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.dependency-preflights
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Reject false preflight success, state mutations, unsafe command modes and stale qualified image reuse.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate.smoke-test
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dependency_preflight_contracts as p
import dependency_effect_contracts as c
import dependency_effect_engine as e
import dependency_effects as runner
from test_dependency_effect_contracts import result as effect_result
from test_dependency_effects import EMPTY, bootstrapped, migrated, EXPECTED

D = 'sha256:' + 'a' * 64
ID = 'a' * 64


def terminal(task='bootstrap', verdict='passed'):
    return json.dumps({'schema':'relational-task-preflight/v1','scope':'read-only-database-prerequisites',
                       'operation':task,'verdict':verdict,'authorized':False}).encode()


def cases():
    return [{'case': name, 'operation': task, 'verdict': verdict, 'phase': phase,
             'attempt_id': f'{index+100:032x}', 'exit_code': 0 if verdict == 'passed' else 1,
             'terminal_digest': p.terminal(terminal(task,verdict),task,verdict), 'elapsed_ms': 5,
             'before_digest':D, 'after_digest':D,
             'observed_row_counts':{} if phase in {'before-bootstrap','after-bootstrap'} else {name:0 for name in p.TABLES},
             'assertions':[{'id':item,'verdict':'passed'} for item in p.ASSERTIONS]}
            for index,(name,task,verdict,phase) in enumerate(p.CASES)]


def receipt(): return p.make_result(effect_result(), cases())


class PreflightContracts(unittest.TestCase):
    def refuse(self, value):
        value['result_digest']=c.digest({key:item for key,item in value.items() if key!='result_digest'})
        with self.assertRaises(c.release.ReleaseFailure):p.validate_result(value,effect_result())
    def test_complete_separate_receipt(self):
        value=receipt();self.assertEqual(p.validate_result(value,effect_result()),value)
        self.assertEqual(len(value['cases']),8);self.assertEqual(len(effect_result()['cases']),9)
        self.assertFalse(value['authorized']);self.assertIn('isolated-restore-target',value['pending'])
    def test_failed_prerequisite_is_not_successful_job(self):
        self.assertEqual(receipt()['cases'][1]['verdict'],'failed')
        with self.assertRaises(c.release.ReleaseFailure):c.terminal(terminal(),'bootstrap','succeeded')
    def test_job_completion_is_not_preflight(self):
        from test_dependency_effect_contracts import terminal as old_terminal
        with self.assertRaises(c.release.ReleaseFailure):p.terminal(old_terminal(),'bootstrap','passed')
    def test_duplicate_terminal_key(self):
        with self.assertRaises(c.release.ReleaseFailure):p.terminal(terminal().replace(b'"authorized": false',b'"authorized": true,"authorized":false'),'bootstrap','passed')
    def test_terminal_wrong_identity(self):
        with self.assertRaises(c.release.ReleaseFailure):p.terminal(terminal('migration'),'bootstrap','passed')
    def test_terminal_secret_extra_refused(self):
        value=json.loads(terminal());value['password']='private'
        with self.assertRaises(c.release.ReleaseFailure):p.terminal(json.dumps(value).encode(),'bootstrap','passed')
    def test_terminal_boolean_zero_refused(self):
        value=json.loads(terminal());value['authorized']=0
        with self.assertRaises(c.release.ReleaseFailure):p.terminal(json.dumps(value).encode(),'bootstrap','passed')
    def test_terminal_multiple_documents(self):
        with self.assertRaises(c.release.ReleaseFailure):p.terminal(terminal()+terminal(),'bootstrap','passed')
    def test_terminal_oversize(self):
        with self.assertRaises(c.release.ReleaseFailure):p.terminal(b' '*4097,'bootstrap','passed')
    def test_terminal_nonfinite(self):
        with self.assertRaises(c.release.ReleaseFailure):p.terminal(b'{"authorized":NaN}','bootstrap','passed')
    def test_state_changed_refused(self):
        before={'state':EMPTY,'row_counts':{}};after={'state':bootstrapped(),'row_counts':{}}
        with self.assertRaises(c.release.ReleaseFailure):p.check_unchanged(before,after)
    def test_nonempty_runtime_refused_even_when_unchanged(self):
        value={'state':migrated(),'row_counts':{name:0 for name in p.TABLES}};value['row_counts'][p.TABLES[0]]=1
        with self.assertRaises(c.release.ReleaseFailure):p.check_unchanged(value,value)
    def test_boolean_row_count_refused(self):
        value={'state':migrated(),'row_counts':{name:False for name in p.TABLES}}
        with self.assertRaises(c.release.ReleaseFailure):p.check_unchanged(value,value)
    def test_exact_independent_observation_order(self):
        engine=Mock();engine.preflight_snapshot.return_value={'state':EMPTY,'row_counts':{}}
        engine.run_preflight.return_value={key:cases()[0][key] for key in ('attempt_id','exit_code','terminal_digest','elapsed_ms')}
        row=p.observe(engine,D,'bootstrap-ready')
        self.assertEqual(row['before_digest'],row['after_digest'])
        self.assertEqual([call[0] for call in engine.mock_calls],['preflight_snapshot','run_preflight','preflight_snapshot'])
    def test_unknown_case_never_executes(self):
        engine=Mock()
        with self.assertRaises(c.release.ReleaseFailure):p.observe(engine,D,'restore-ready')
        engine.assert_not_called();engine.run_preflight.assert_not_called()
    def test_open_schema_refused(self):
        schema=p.load_schema('dependency-preflight-result');schema['additionalProperties']=True
        with patch.object(c.release,'load_document',return_value=schema):
            with self.assertRaises(c.release.ReleaseFailure):p.load_schema('dependency-preflight-result')
    def test_remote_schema_reference_refused(self):
        schema=p.load_schema('dependency-preflight-result');schema['properties']['cases']['$ref']='https://invalid.example/schema'
        with patch.object(c.release,'load_document',return_value=schema):
            with self.assertRaises(c.release.ReleaseFailure):p.load_schema('dependency-preflight-result')
    def test_wrong_schema_identity_refused(self):
        schema=p.load_schema('dependency-preflight-result');schema['$id']='urn:wrong'
        with patch.object(c.release,'load_document',return_value=schema):
            with self.assertRaises(c.release.ReleaseFailure):p.load_schema('dependency-preflight-result')
    def test_old_effect_receipt_cannot_substitute(self):
        with self.assertRaises(c.release.ReleaseFailure):p.validate_result(effect_result(),effect_result())


def mutation(name,change):
    def test(self):
        value=receipt();change(value);self.refuse(value)
    setattr(PreflightContracts,'test_refuse_'+name,test)
for name,change in [
 ('authority',lambda v:v.update(authorized=True)),
 ('job_scope',lambda v:v.update(scope='local-packaged-postgresql-effects')),
 ('extra_secret',lambda v:v.update(password='private')),
 ('missing_case',lambda v:v['cases'].pop()),
 ('duplicate_case',lambda v:v['cases'].__setitem__(1,deepcopy(v['cases'][0]))),
 ('wrong_order',lambda v:v['cases'].reverse()),
 ('unmatched_state',lambda v:v['cases'][0].update(after_digest='sha256:'+'b'*64)),
 ('terminal_drift',lambda v:v['cases'][0].update(terminal_digest='sha256:'+'b'*64)),
 ('shared_effect_attempt',lambda v:v['cases'][0].update(attempt_id=effect_result()['cases'][0]['attempt_id'])),
 ('shared_preflight_attempt',lambda v:v['cases'][1].update(attempt_id=v['cases'][0]['attempt_id'])),
 ('positive_exit_failure',lambda v:v['cases'][0].update(exit_code=1)),
 ('negative_exit_success',lambda v:v['cases'][1].update(exit_code=0)),
 ('old_schema',lambda v:v['schema_digests'].update({'dependency-preflight-result/v1':'sha256:'+'b'*64})),
 ('different_effect',lambda v:v.update(effect_result_digest='sha256:'+'b'*64)),
 ('different_artifact',lambda v:v['artifact'].update(image_id='sha256:'+'b'*64)),
 ('different_runner',lambda v:v.update(runner_digest='sha256:'+'b'*64)),
 ('execution_argv',lambda v:v['commands']['bootstrap'].pop()),
 ('unobserved_counts',lambda v:v['cases'][4].update(observed_row_counts={})),
]:mutation(name,change)


class PreflightEngine(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.engine=e.DependencyEngine(Path(self.temp.name))
        self.engine._owned['owned']={'id':ID}
    def tearDown(self):self.temp.cleanup()
    def execute(self,task,case,verdict,output=None,code=None):
        wanted=0 if verdict=='passed' else 1
        with patch.object(self.engine,'_create_bound',return_value='owned') as create,patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],wanted if code is None else code,output or terminal(task,verdict),b'')),patch.object(self.engine,'inspect_bound',return_value={'ExitCode':wanted}),patch.object(self.engine,'_cleanup') as cleanup:
            result=self.engine.run_preflight(D,task,case,verdict)
        cleanup.assert_called_once_with('owned')
        return create.call_args.kwargs,result
    def test_bootstrap_same_packaged_entrypoint_explicit_mode(self):
        args,result=self.execute('bootstrap','bootstrap-ready','passed')
        self.assertEqual(args['command'],p.COMMANDS['bootstrap']);self.assertEqual(args['command'][-1],'--preflight')
        self.assertNotIn('RELATIONAL_CONFIG_JSON',args['environment'])
    def test_migration_only_selected_credentials(self):
        args,_=self.execute('migration','migration-ready','passed')
        self.assertEqual(set(args['environment']),{'RELATIONAL_MIGRATION_SECRET_JSON','RELATIONAL_CONFIG_JSON','RELATIONAL_TLS_CA_MODE','RELATIONAL_LOCAL_QUALIFICATION_ID'})
    def test_runtime_no_master_or_migration_credentials(self):
        args,_=self.execute('relay','relay-ready','passed')
        self.assertEqual(set(args['environment']),{'RELATIONAL_RUNTIME_SECRET_JSON','RELATIONAL_CONFIG_JSON','RELATIONAL_SMOKE_QUEUE_URL','RELATIONAL_TLS_CA_MODE','RELATIONAL_LOCAL_QUALIFICATION_ID'})
        self.assertEqual(args['environment']['RELATIONAL_SMOKE_QUEUE_URL'],'https://invalid.example/local-preflight-only')
    def test_bootstrap_denied_identity_uses_wrong_password(self):
        args,_=self.execute('bootstrap','bootstrap-denied-identity','failed')
        self.assertNotEqual(json.loads(args['environment']['RELATIONAL_MASTER_SECRET_JSON'])['password'],self.engine.credentials['master'])
    def test_migration_denied_identity_uses_runtime_identity(self):
        args,_=self.execute('migration','migration-denied-identity','failed')
        self.assertEqual(json.loads(args['environment']['RELATIONAL_MIGRATION_SECRET_JSON'])['username'],'psmokeruntime')
    def test_refuse_wrong_case_pair_before_transport(self):
        with patch.object(self.engine,'_create_bound') as create:
            with self.assertRaises(c.release.ReleaseFailure):self.engine.run_preflight(D,'migration','bootstrap-ready','passed')
            create.assert_not_called()
    def test_refuse_restore_preflight_in_nonisolated_fixture(self):
        with self.assertRaises(c.release.ReleaseFailure):self.engine.run_preflight(D,'restore-verify','restore-ready','passed')
    def test_wrong_exit_refused_and_cleaned(self):
        with patch.object(self.engine,'_create_bound',return_value='owned'),patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],1,terminal(),b'')),patch.object(self.engine,'inspect_bound',return_value={'ExitCode':1}),patch.object(self.engine,'_cleanup') as cleanup:
            with self.assertRaises(c.release.ReleaseFailure):self.engine.run_preflight(D,'bootstrap','bootstrap-ready','passed')
        cleanup.assert_called_once_with('owned')
    def test_empty_database_counts(self):
        with patch.object(self.engine,'snapshot',return_value=EMPTY),patch.object(self.engine,'sql') as sql:
            self.assertEqual(self.engine.preflight_snapshot(),{'state':EMPTY,'row_counts':{}})
            sql.assert_not_called()
    def test_actual_table_count_query_selected_once(self):
        counts={name:0 for name in p.TABLES}
        with patch.object(self.engine,'snapshot',return_value=migrated()),patch.object(self.engine,'sql',return_value=json.dumps(counts).encode()) as sql:
            self.assertEqual(self.engine.preflight_snapshot()['row_counts'],counts)
            sql.assert_called_once_with('preflight-counts')
    def test_partial_table_membership_refused(self):
        state=migrated();state['tables'].pop()
        with patch.object(self.engine,'snapshot',return_value=state):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.preflight_snapshot()
    def test_malformed_count_output_refused(self):
        with patch.object(self.engine,'snapshot',return_value=migrated()),patch.object(self.engine,'sql',return_value=b'[]'):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.preflight_snapshot()


class QualifiedReuse(unittest.TestCase):
    def test_handoff_requires_verified_receipt_and_current_source(self):
        result={'result_digest':D}
        with patch.object(runner.qualified_publication,'verify',return_value={'container_result_digest':D}) as verify,patch.object(runner.qualified_publication,'read',return_value=b'{}'),patch.object(runner.qualified_publication,'checked_document',return_value=result),patch.object(runner.qualified_publication,'current_result',return_value=result) as current:
            self.assertEqual(runner.qualified_build(Path('/tmp/root'),Path('/tmp/scratch'),Path('/tmp/handoff')),result)
        verify.assert_called_once();current.assert_called_once()
    def test_handoff_changed_between_verification_and_read_refused(self):
        with patch.object(runner.qualified_publication,'verify',return_value={'container_result_digest':D}),patch.object(runner.qualified_publication,'read',return_value=b'{}'),patch.object(runner.qualified_publication,'checked_document',return_value={'result_digest':'sha256:'+'b'*64}),patch.object(runner.qualified_publication,'current_result') as current:
            with self.assertRaises(c.release.ReleaseFailure):runner.qualified_build(Path('/tmp/root'),Path('/tmp/scratch'),Path('/tmp/handoff'))
        current.assert_not_called()
    def test_qualification_failure_not_fallback_build(self):
        with patch.object(runner.qualified_publication,'verify',side_effect=c.release.ReleaseFailure('unsafe')),patch.object(runner.local_container,'run') as build:
            with self.assertRaises(c.release.ReleaseFailure):runner.qualified_build(Path('/tmp/root'),Path('/tmp/scratch'),Path('/tmp/handoff'))
        build.assert_not_called()
    def test_conflicting_modes_safe(self):
        output=io.StringIO()
        with patch.object(runner,'run') as run,contextlib.redirect_stdout(output):
            code=runner.main(['--source-root','/tmp','--scratch-root','/tmp','--package-cache','/private/cache','--qualified-publication-directory','/private/handoff'])
        self.assertEqual(code,1);run.assert_not_called();self.assertNotIn('/private/',output.getvalue())
    def test_handoff_public_dispatch(self):
        output=io.StringIO()
        with patch.object(runner.local_container,'checked_scratch',return_value=Path('/tmp')),patch.object(runner,'run',return_value=effect_result()) as run,contextlib.redirect_stdout(output):
            code=runner.main(['--source-root','/tmp','--scratch-root','/tmp','--qualified-publication-directory','/tmp/handoff'])
        self.assertEqual(code,0);self.assertEqual(run.call_args.kwargs,{'publication_directory':'/tmp/handoff'})
        self.assertIsNone(run.call_args.args[2])


class Orchestration(unittest.TestCase):
    def test_same_verified_image_original_effects_and_distinct_receipt(self):
        order=[]
        class FakeEngine:
            run_id='f'*32
            def __init__(self,work):self.state=deepcopy(EMPTY);self.counter=1000;self.cleaned=False
            def dependency_identity(self,lock):return D
            def inspect_image(self,image):self_image=image;order.append(('image',image))
            def inventory(self,image):return []
            def version(self):return {'client':'29.5.2','server':'29.5.2'}
            def prepare_certificates(self):return D
            def create_network(self):pass
            def start_dependency(self,image):pass
            def verify_tls(self):pass
            def snapshot(self):return deepcopy(self.state)
            def preflight_snapshot(self):
                return {'state':self.snapshot(),'row_counts':{name:0 for name in p.TABLES} if self.state['tables'] else {}}
            def execution(self,task,verdict,preflight):
                self.counter+=1
                return {'attempt_id':f'{self.counter:032x}','exit_code':0 if verdict in {'passed','succeeded'} else 1,
                        'elapsed_ms':2,'terminal_digest':p.terminal(terminal(task,verdict),task,verdict) if preflight else D}
            def run_preflight(self,image,task,case,verdict):
                order.append(('preflight',case,image));return self.execution(task,verdict,True)
            def run_task(self,image,task,case,verdict):
                order.append(('effect',case,image))
                if case=='bootstrap':self.state=bootstrapped()
                if case=='migration':self.state=migrated()
                return self.execution(task,verdict,False)
            def sql(self,operation,**kwargs):
                if operation=='corrupt':self.state['history'][1]['checksum']='0'*64
                if operation.startswith('revoke-'):self.state['tables'][-1]['runtime_dml']=False
                if operation.startswith('grant-'):self.state['tables'][-1]['runtime_dml']=True
            def restore_checksum(self,expected):self.state=migrated()
            def cleanup_all(self):self.cleaned=True
        source=Path(__file__).resolve().parents[3]
        files={runner.LOCK:(source/runner.LOCK).read_bytes(),runner.EXPECTATIONS:(source/runner.EXPECTATIONS).read_bytes()}
        profile=effect_result()['profile'];profile['source_digest']=runner.digest(runner.canonical([]))
        built={'payload':{'files':[]}}
        with tempfile.TemporaryDirectory() as temporary:
            scratch=Path(temporary)
            with patch.object(runner.local_container,'checked_scratch',return_value=scratch),patch.object(runner,'snapshot',return_value=(files,D)),patch.object(runner,'DependencyEngine',side_effect=FakeEngine),patch.object(runner,'qualified_build',return_value=built) as qualified,patch.object(runner.local_container,'run') as build,patch.object(runner,'profile',return_value=profile),patch.object(runner,'source_manifest',return_value=[]),patch.object(runner.local_container,'repository_head',return_value=profile['repository_head']):
                result=runner.run(source,scratch,publication_directory=scratch/'handoff')
            qualified.assert_called_once();build.assert_not_called()
            evidence=scratch/('dependency-effect-evidence-'+'f'*32)
            self.assertEqual({item.name for item in evidence.iterdir()},{'build-result.json','effect-result.json','preflight-result.json'})
            checked=json.loads((evidence/'preflight-result.json').read_text());p.validate_result(checked,result)
            self.assertEqual(len(result['cases']),9);self.assertEqual(len(checked['cases']),8)
            self.assertEqual([row['case'] for row in result['cases']],[row[0] for row in c.CASES])
            self.assertEqual({row[-1] for row in order}, {D})
            self.assertLess(order.index(('preflight','bootstrap-ready',D)),order.index(('effect','bootstrap',D)))
            self.assertLess(order.index(('effect','bootstrap',D)),order.index(('preflight','migration-ready',D)))
            self.assertLess(order.index(('preflight','migration-ready',D)),order.index(('effect','migration',D)))
            self.assertLess(order.index(('effect','migration',D)),order.index(('preflight','relay-ready',D)))
            self.assertEqual(list(scratch.glob('dependency-effects-*')),[])


if __name__=='__main__':unittest.main()
