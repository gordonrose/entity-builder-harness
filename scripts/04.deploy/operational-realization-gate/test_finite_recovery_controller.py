"""Durable finite recovery across controller interruption; no Docker daemon needed."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.finite-recovery-controller
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove persisted identity, permanently consumed dispatches and exact recovery after interrupted controllers.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import finite_recovery_contracts as c
from finite_recovery_controller import RecoveryController,make_intent
from finite_recovery_engine import RecoveryEngine
from operation_actions import OperationActionStore
from test_finite_recovery_engine import RecoveryDocker,IMAGE,CID

class Crash(BaseException):pass

class RecoveryControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.now=1000000
        self.store=OperationActionStore(self.root,_clock=lambda:self.now);self.addCleanup(self.store.close)
        self.fake=RecoveryDocker();self.engine=RecoveryEngine(self.root,runner=self.fake)
        self.attempt=c.make_attempt(IMAGE);self.intent=make_intent(self.attempt)
        self.controller=RecoveryController(self.store,self.engine,_sleep=lambda seconds:None)
        self.controller.prepare(self.intent,self.attempt)

    def run_controller(self):return self.controller.run(self.attempt['operation_id'],'a'*32)
    def reopen(self):
        self.store.close();self.now+=3100
        self.store=OperationActionStore(self.root,_clock=lambda:self.now);self.addCleanup(self.store.close)
        self.engine=RecoveryEngine(self.root,runner=self.fake)
        self.controller=RecoveryController(self.store,self.engine,_sleep=lambda seconds:None)
        return self.controller.run(self.attempt['operation_id'],'b'*32)
    def crash(self,phase):
        def stop(actual):
            if actual==phase:raise Crash()
        self.controller._checkpoint=stop
        with self.assertRaises(Crash):self.run_controller()
    def assert_closed(self,result,terminal=True):
        self.assertEqual(result['state'],'closed',result)
        self.assertIs(result['terminal_observed'],terminal)
        self.assertTrue(result['cleanup_verified']);self.assertFalse(result['authorized'])
        self.assertEqual(result['semantic_verdict'],'unverified')
        self.assertEqual(result['product_profile_updates'],[])
        self.assertEqual(result['operation_authorization'],'blocked')

    def test_normal_success_is_one_create_one_start_and_exact_cleanup(self):
        result=self.run_controller();self.assert_closed(result)
        self.assertEqual((self.fake.creates,self.fake.starts),(1,1));self.assertTrue(self.fake.deleted)
        self.assertEqual(result['resource_id'],CID)
        self.assertEqual(self.controller.result(self.attempt['operation_id']),result)

    def test_attempt_is_durable_before_first_engine_effect(self):
        runner=self.engine.runner
        def check(argv,**kwargs):
            self.assertEqual(self.store.read_attempt(self.attempt['operation_id']),self.attempt)
            if argv[3]=='create':
                self.assertEqual(self.store.read_actions(self.attempt['operation_id'])['counts']['create'],1)
            if argv[3]=='start':
                self.assertEqual(self.store.read_actions(self.attempt['operation_id'])['counts']['start'],1)
            return runner(argv,**kwargs)
        self.engine.runner=check;self.assert_closed(self.run_controller())

    def test_crash_before_create_call_and_negative_lookup_never_retries(self):
        self.crash('create-reserved');result=self.reopen()
        self.assertEqual(result['state'],'unknown');self.assertFalse(result['cleanup_verified'])
        self.assertEqual((self.fake.creates,self.fake.starts),(0,0))
        self.assertEqual(result['action_counts']['create'],1)
        result=self.reopen();self.assertEqual(result['state'],'unknown');self.assertEqual(self.fake.creates,0)

    def test_crash_after_create_adopts_exact_identity_and_abandons_without_start(self):
        self.crash('create-effect');result=self.reopen();self.assert_closed(result,False)
        self.assertEqual(result['resource_id'],CID)
        self.assertEqual((self.fake.creates,self.fake.starts),(1,0));self.assertTrue(self.fake.deleted)

    def test_crash_before_start_never_replays_even_when_container_is_created(self):
        self.crash('start-reserved');result=self.reopen()
        self.assertEqual(result['state'],'unknown');self.assertFalse(self.fake.deleted)
        self.assertEqual(result['action_counts']['start'],1);self.assertEqual(self.fake.starts,0)

    def test_crash_after_start_recovers_terminal_without_replaying_start(self):
        self.crash('start-effect');result=self.reopen();self.assert_closed(result)
        self.assertEqual((self.fake.creates,self.fake.starts),(1,1));self.assertTrue(self.fake.deleted)

    def test_missing_container_after_consumed_start_does_not_prove_success_or_absence(self):
        self.crash('start-effect');self.fake.deleted=True;result=self.reopen()
        self.assertEqual(result['state'],'unknown');self.assertFalse(result['terminal_observed'])
        self.assertEqual((self.fake.creates,self.fake.starts),(1,1))

    def test_crash_after_terminal_keeps_terminal_bound_and_does_not_restart(self):
        self.crash('terminal-observed');result=self.reopen();self.assert_closed(result)
        self.assertEqual(self.fake.starts,1)

    def test_crash_after_cleanup_effect_reconciles_absence_without_redeleting(self):
        self.crash('cleanup-effect');result=self.reopen();self.assert_closed(result)
        self.assertEqual(result['action_counts']['cleanup'],1)
        self.assertEqual(len([call for call in self.fake.calls if call[3]=='rm']),1)

    def test_crash_after_cleanup_verified_refreshes_proof_under_new_fence(self):
        self.crash('cleanup-verified');result=self.reopen();self.assert_closed(result)
        self.assertEqual(result['action_counts']['cleanup'],1)

    def test_foreign_identity_recovery_preserves_resource_and_reports_unknown(self):
        self.crash('start-effect');self.fake.container['Config']['Labels']['release-control.owner']='foreign'
        # Use actual owner-label spelling from the shared engine.
        import container_engine
        self.fake.container['Config']['Labels'][container_engine.OWNER_LABEL]='f'*32
        result=self.reopen();self.assertEqual(result['state'],'unknown');self.assertFalse(self.fake.deleted)

    def test_expired_call_reservation_never_dispatches(self):
        def expire(phase):
            if phase=='create-reserved':self.now+=2001
        self.controller._checkpoint=expire
        result=self.run_controller();self.assertEqual(result['state'],'unknown');self.assertEqual(self.fake.creates,0)

    def test_failed_atomic_prepare_never_calls_engine(self):
        with patch.object(self.store,'prepare_attempt',side_effect=c.journal.ControlFailure('fixture-failure')):
            with self.assertRaises(c.journal.ControlFailure):self.controller.prepare(self.intent,self.attempt)
        self.assertEqual(self.fake.calls,[])

    def test_raw_diagnostic_is_not_in_safe_unresolved_result(self):
        self.fake.log_output=b'PRIVATE_FIXTURE_CANARY'
        result=self.run_controller();self.assertEqual(result['state'],'unknown')
        self.assertNotIn('PRIVATE_FIXTURE_CANARY',str(result));self.assertFalse(result['authorized'])

if __name__=='__main__':unittest.main()
