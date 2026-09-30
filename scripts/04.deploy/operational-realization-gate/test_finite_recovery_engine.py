"""Exact inert resource adoption, bounded logs and unchanged normal engine defaults."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.finite-recovery-engine
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify bounded inert recovery ownership and durable action refusal paths.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from copy import deepcopy

import container_engine as base
import finite_recovery_contracts as c
from finite_recovery_engine import RecoveryEngine,LOG_CONFIG
from test_finite_job_engine import JobDocker, IMAGE, CID

class RecoveryDocker(JobDocker):
    def __init__(self):
        super().__init__();self.log_output=None;self.lose_create=False;self.creates=0;self.starts=0
    def __call__(self,argv,**kwargs):
        args=argv[3:]
        if args[:2]==['container','ls'] and any(arg.startswith('name=') for arg in args):
            self.calls.append(argv)
            return subprocess.CompletedProcess(argv,0,b'' if self.deleted or not self.container else CID.encode()+b'\n',b'')
        if args[0]=='start' and '--attach' not in args:
            self.calls.append(argv);self.snapshots.append(kwargs);self.starts+=1
            self.container['State'].update(Status='exited',Running=False,ExitCode=0,OOMKilled=False)
            return subprocess.CompletedProcess(argv,0,CID.encode()+b'\n',b'')
        if args[0]=='logs':
            self.calls.append(argv);self.snapshots.append(kwargs)
            env=dict(row.split('=',1) for row in self.container['Config']['Env'])
            value={'schema':'finite-job-terminal/v1','run_id':env['RELEASE_CONTROL_RUN_ID'],
                   'profile_digest':env['RELEASE_CONTROL_PROFILE_DIGEST'],'outcome':'completed',
                   'checks':[{'id':'fixture-calculation','verdict':'passed'}]}
            raw=json.dumps(value).encode() if self.log_output is None else self.log_output
            return subprocess.CompletedProcess(argv,0,raw,b'')
        result=super().__call__(argv,**kwargs)
        if args[0]=='create':
            self.creates+=1;self.container['HostConfig']['LogConfig']=deepcopy(LOG_CONFIG)
            self.container['State'].update(Status='created',Running=False,ExitCode=0,OOMKilled=False)
            self.container['RestartCount']=0
            if self.lose_create:raise base.EngineFailure('local-container-engine-timeout')
        return result

class RecoveryEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.fake=RecoveryDocker();self.engine=RecoveryEngine(Path(self.tmp.name),runner=self.fake)
        self.attempt=c.make_attempt(IMAGE)
    def call(self,action,known=None):return self.engine.perform(self.attempt,action,known)
    def create(self):return self.call('create')['resource_id']
    def reject(self,call,*args):
        with self.assertRaises((c.journal.ControlFailure,base.EngineFailure,c.finite.ReleaseFailure)):call(*args)
    def test_exact_finite_fixture_lifecycle(self):
        known=self.create();self.assertEqual(self.call('start',known)['state'],'exited')
        value=self.call('logs',known);self.assertEqual(value['terminal'],c.terminal(self.attempt))
        self.assertEqual(self.call('cleanup',known)['state'],'absent')
        self.assertEqual(self.call('inspect',known)['state'],'absent')
        self.assertEqual((self.fake.creates,self.fake.starts),(1,1))
    def test_lost_create_response_adopts_same_exact_container(self):
        self.fake.lose_create=True;self.reject(self.call,'create')
        self.assertFalse(self.fake.deleted)
        fresh=RecoveryEngine(Path(self.tmp.name),runner=self.fake)
        observed=fresh.perform(self.attempt,'inspect')
        self.assertEqual(observed['resource_id'],CID);self.assertEqual(self.fake.creates,1)
    def test_foreign_owner_not_adopted_or_removed(self):
        self.create();self.fake.container['Config']['Labels'][base.OWNER_LABEL]='f'*32
        self.reject(self.call,'inspect');self.assertFalse(self.fake.deleted)
    def test_known_id_cannot_be_replaced(self):
        self.create();self.reject(self.call,'inspect','f'*64);self.assertFalse(self.fake.deleted)
    def test_image_mutation_refused(self):
        self.fake.image['Id']='sha256:'+'b'*64;self.reject(self.call,'create')
    def test_isolation_mutation_refused(self):
        known=self.create();self.fake.container['HostConfig']['NetworkMode']='host'
        self.reject(self.call,'start',known);self.assertEqual(self.fake.starts,0)
    def test_unbounded_log_driver_refused(self):
        known=self.create();self.fake.container['HostConfig']['LogConfig']={'Type':'json-file','Config':{}}
        self.reject(self.call,'start',known)
    def test_repeated_container_start_refused(self):
        known=self.create();self.call('start',known);self.reject(self.call,'start',known)
        self.assertEqual(self.fake.starts,1)
    def test_duplicated_terminal_refused(self):
        known=self.create();self.call('start',known)
        self.fake.log_output=(json.dumps(c.terminal(self.attempt))+'\n') .encode()*2
        self.reject(self.call,'logs',known)
    def test_raw_diagnostic_never_normalized_as_terminal(self):
        known=self.create();self.call('start',known);self.fake.log_output=b'PRIVATE_FIXTURE_CANARY'
        self.reject(self.call,'logs',known)
    def test_output_limit_refused(self):
        known=self.create();self.call('start',known);self.fake.log_output=b'x'*4097
        self.reject(self.call,'logs',known)
    def test_no_name_only_start_or_cleanup(self):
        self.create();self.reject(self.call,'start');self.reject(self.call,'cleanup')
    def test_no_arbitrary_action(self):self.reject(self.call,'exec')
    def test_no_arbitrary_product_command(self):
        self.attempt['profile']['execution']['command']=['jobs/production.cjs','success']
        self.reject(self.call,'create')
    def test_call_deadlines_remain_bounded(self):
        self.create();self.assertTrue(self.fake.snapshots)
        self.assertTrue(all(row['timeout']<=2 for row in self.fake.snapshots))
    def test_entire_action_has_one_fractional_deadline(self):
        clock=[0.0]
        def slow(argv,**kwargs):
            result=self.fake(argv,**kwargs);clock[0]+=0.3;return result
        engine=RecoveryEngine(Path(self.tmp.name),runner=slow,_monotonic=lambda:clock[0])
        with self.assertRaises(c.journal.ControlFailure):engine.perform(self.attempt,'create',timeout_seconds=0.5)
        self.assertEqual(self.fake.creates,1)
        self.assertLessEqual(max(row['timeout'] for row in self.fake.snapshots),0.5)

    def test_image_with_server_default_is_not_the_inert_fixture(self):
        self.fake.image['Config']['Cmd']=list(base.SERVER_COMMAND)
        self.reject(self.call,'create');self.assertEqual(self.fake.creates,0)

    def test_known_identity_cannot_be_hidden_by_name_absence(self):
        known=self.create();runner=self.engine.runner
        def renamed(argv,**kwargs):
            if argv[3:5]==['container','ls'] and any(value.startswith('name=') for value in argv):
                return subprocess.CompletedProcess(argv,0,b'',b'')
            return runner(argv,**kwargs)
        self.engine.runner=renamed
        self.reject(self.call,'inspect',known)
        self.assertFalse(self.fake.deleted)

    def test_ordinary_create_keeps_logging_disabled(self):
        args=self.engine._create_arguments(IMAGE,'release-control-'+'a'*32,'a'*32)
        self.assertEqual(args[args.index('--log-driver')+1],'none');self.assertNotIn('--log-opt',args)

if __name__=='__main__':unittest.main()
