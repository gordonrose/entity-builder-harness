"""Typed immutable attachments, consumed dispatches and durable action CAS tests."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operation-actions
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify bounded inert recovery ownership and durable action refusal paths.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import operation_actions as subject
import operation_journal as c
import control_store_fixtures as f
import finite_recovery_contracts as adapter

class OperationActionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.now=f.NOW
        self.s=subject.OperationActionStore(self.tmp.name,_clock=lambda:self.now);self.addCleanup(self.s.close)
        self.attempt=adapter.make_attempt('sha256:'+'3'*64,run_id='a'*32,ownership_token='b'*32)
        self.intent=f.intent(self.attempt['operation_id'])
        self.intent.update(idempotency_key=c.digest(self.attempt),profile_digest=c.digest(self.attempt['profile']),artifact_digest=self.attempt['profile']['artifact']['image_id'])
        self.s.prepare_attempt(self.intent,self.attempt)
        self.claim=self.s.claim(self.intent['operation_id'],f.OWNER_A)
        self.s.advance(self.claim,1,'effect-intent')

    def reject(self,code,call,*args,**kwargs):
        with self.assertRaises(c.ControlFailure) as found:call(*args,**kwargs)
        self.assertEqual(found.exception.code,code)
    def history(self):return self.s.read_actions(self.intent['operation_id'])
    def reserve(self,action):return self.s.reserve_action(self.claim,self.history()['revision'],action)
    def observe(self,ticket,state='created',resource='c'*64,**kwargs):
        observation=adapter.observation(self.attempt,state,resource,oom_killed=None if state=='absent' else False,**kwargs)
        return self.s.observe_action(self.claim,self.history()['revision'],ticket,observation)
    def created(self):
        ticket=self.reserve('create');self.observe(ticket);return ticket

    def test_attempt_content_and_action_journal_survive_reopen(self):
        self.created();before=self.history();self.s.close()
        self.s=subject.OperationActionStore(self.tmp.name,_clock=lambda:self.now);self.addCleanup(self.s.close)
        self.assertEqual(self.s.read_attempt(self.intent['operation_id']),self.attempt)
        self.assertEqual(self.history(),before)
        self.assertEqual(before['known_resource_id'],'c'*64)
        self.assertFalse(before['authorized'])

    def test_atomic_prepare_rolls_back_both_intent_and_attachment(self):
        with tempfile.TemporaryDirectory() as root,subject.OperationActionStore(root,_clock=lambda:self.now) as store:
            with patch.object(store,'_append',side_effect=c.ControlFailure('fixture-failure')):
                self.reject('fixture-failure',store.prepare_attempt,self.intent,self.attempt)
            self.assertEqual(store.db.execute('SELECT count(*) FROM operations').fetchone()[0],0)
            self.assertEqual(store.db.execute('SELECT count(*) FROM action_attachments').fetchone()[0],0)

    def test_prepare_is_idempotent_but_immutable_binding_changes_fail(self):
        before=self.history();self.s.prepare_attempt(self.intent,copy.deepcopy(self.attempt));self.assertEqual(self.history(),before)
        changed=copy.deepcopy(self.intent);changed['profile_digest']='sha256:'+'9'*64
        self.reject('attachment-binding-invalid',self.s.prepare_attempt,changed,self.attempt)

    def test_unsupported_or_unsafe_attachment_rejected(self):
        changed=copy.deepcopy(self.attempt);changed['schema']='arbitrary-payload/v1'
        self.reject('attachment-type-unsupported',self.s.prepare_attempt,self.intent,changed)
        changed=copy.deepcopy(self.attempt);changed['command']='unsafe command'
        with self.assertRaises(c.ControlFailure):self.s.prepare_attempt(self.intent,changed)

    def test_create_reservation_is_spent_permanently_on_missing_response(self):
        ticket=self.reserve('create')
        self.reject('action-budget-exhausted',self.reserve,'create')
        self.s.close();self.s=subject.OperationActionStore(self.tmp.name,_clock=lambda:self.now);self.addCleanup(self.s.close)
        self.reject('action-budget-exhausted',self.reserve,'create')
        self.assertEqual(self.history()['observations'],[])
        self.assertEqual(ticket['deadline_ms'],self.now+self.intent['policy']['call_timeout_ms'])
        self.assertFalse(ticket['authorized'])

    def test_start_needs_observed_created_identity_and_is_spent_once(self):
        with self.assertRaises(c.ControlFailure):self.reserve('start')
        self.created();ticket=self.reserve('start');self.observe(ticket,'running')
        self.reject('action-budget-exhausted',self.reserve,'start')

    def test_create_start_refused_after_reconciliation_takeover(self):
        self.now+=1001;self.claim=self.s.claim(self.intent['operation_id'],f.OWNER_B)
        self.reject('action-reconciliation-only',self.reserve,'create')
        self.reject('action-reconciliation-only',self.reserve,'start')
        self.assertEqual(self.reserve('inspect')['action'],'inspect')

    def test_composite_revision_rejects_action_replay_and_operation_changes(self):
        prior=self.history()['revision'];self.reserve('create')
        self.reject('action-revision-stale',self.s.reserve_action,self.claim,prior,'inspect')
        prior=self.history()['revision'];snap=self.s.read(self.intent['operation_id']);self.s.renew(self.claim,snap['revision'])
        self.reject('action-revision-stale',self.s.reserve_action,self.claim,prior,'inspect')
        prior=self.history()['revision'];prior['actions']=True
        self.reject('action-revision-invalid',self.s.reserve_action,self.claim,prior,'inspect')

    def test_ticket_observation_is_exactly_once_and_rejects_tampering(self):
        ticket=self.created();proof=adapter.observation(self.attempt,'created','c'*64,oom_killed=False)
        self.reject('action-ticket-invalid',self.s.observe_action,self.claim,self.history()['revision'],ticket,proof)
        ticket=self.reserve('inspect');ticket['ordinal']=17
        self.reject('action-ticket-invalid',self.s.observe_action,self.claim,self.history()['revision'],ticket,proof)

    def test_repeated_identical_inspection_content_is_allowed(self):
        self.created()
        for _ in range(2):self.observe(self.reserve('inspect'))
        values=self.history()['observations']
        self.assertEqual(len(values),3)
        self.assertEqual(len({row['observation_digest'] for row in values}),1)

    def test_response_from_stale_claim_or_after_call_deadline_refused(self):
        ticket=self.reserve('create');proof=adapter.observation(self.attempt,'created','c'*64,oom_killed=False)
        self.now+=501
        self.reject('action-deadline',self.s.observe_action,self.claim,self.history()['revision'],ticket,proof)
        self.now+=500;self.claim=self.s.claim(self.intent['operation_id'],f.OWNER_B)
        self.reject('action-ticket-invalid',self.s.observe_action,self.claim,self.history()['revision'],ticket,proof)

    def test_resource_id_cannot_change_after_any_recorded_observation(self):
        self.created();ticket=self.reserve('inspect')
        self.reject('action-resource-changed',self.observe,ticket,resource='d'*64)

    def test_cleanup_and_inspection_budgets_are_durable(self):
        self.created()
        for _ in range(3):
            self.reserve('cleanup');self.observe(self.reserve('inspect'))
        self.reject('action-budget-exhausted',self.reserve,'cleanup')
        self.assertEqual(self.history()['counts']['cleanup'],3)

    def test_recovery_deadline_does_not_move_with_lease_takeover(self):
        expected=f.NOW+self.intent['policy']['operation_timeout_ms']+self.attempt['limits']['recovery_timeout_ms']
        self.assertEqual(self.history()['recovery_deadline_ms'],expected)
        self.now=expected;self.claim=self.s.claim(self.intent['operation_id'],f.OWNER_B)
        self.reject('action-deadline',self.reserve,'inspect')

    def test_missing_corrupt_observation_content_blocks_further_actions(self):
        self.created();self.s.db.execute('DELETE FROM action_observations')
        self.reject('action-observation-missing',self.history)
        self.reject('action-observation-missing',self.reserve,'inspect')

    def test_atomic_observation_rolls_back_payload_on_journal_failure(self):
        ticket=self.reserve('create');proof=adapter.observation(self.attempt,'created','c'*64,oom_killed=False)
        with patch.object(self.s,'_append',side_effect=c.ControlFailure('fixture-failure')):
            self.reject('fixture-failure',self.s.observe_action,self.claim,self.history()['revision'],ticket,proof)
        self.assertEqual(self.history()['observations'],[])
        self.assertEqual(self.s.db.execute('SELECT count(*) FROM action_observations').fetchone()[0],0)

    def test_action_and_attachment_corruption_fail_closed(self):
        self.created();self.s.db.execute("UPDATE action_events SET digest=? WHERE sequence=1",('sha256:'+'0'*64,))
        self.reject('action-journal-corrupt',self.history)

    def test_unknown_cleanup_never_permits_start_or_another_cleanup(self):
        self.created();self.reserve('cleanup')
        with self.assertRaises(c.ControlFailure):self.reserve('start')
        with self.assertRaises(c.ControlFailure):self.reserve('cleanup')
        self.observe(self.reserve('inspect'))
        with self.assertRaises(c.ControlFailure):self.reserve('start')
        self.assertEqual(self.reserve('cleanup')['ordinal'],2)

    def test_late_observation_after_later_reservation_is_refused(self):
        ticket=self.reserve('create');self.reserve('inspect')
        self.reject('action-ticket-stale',self.observe,ticket)

    def test_transport_budget_requires_current_lease_revision_and_ticket(self):
        ticket=self.reserve('create')
        self.assertEqual(self.s.action_budget(self.claim,self.history()['revision'],ticket),500)
        self.s.renew(self.claim,self.s.read(self.intent['operation_id'])['revision'])
        self.reject('action-ticket-invalid',self.s.action_budget,self.claim,self.history()['revision'],ticket)

    def test_plain_unit_a_store_is_never_migrated_or_modified(self):
        from local_control_store import LocalControlStore
        with tempfile.TemporaryDirectory() as root:
            with LocalControlStore(root,_clock=lambda:self.now) as plain:plain.prepare(f.intent())
            path=Path(root)/'control.sqlite3';before=path.read_bytes()
            self.reject('action-store-format-required',subject.OperationActionStore,root,_clock=lambda:self.now+1)
            self.assertEqual(path.read_bytes(),before)
            with LocalControlStore(root,_clock=lambda:self.now) as plain:
                self.assertIsNone(plain.db.execute("SELECT name FROM sqlite_master WHERE name='action_attachments'").fetchone())

    def test_cached_valid_content_cannot_validate_a_mutated_attachment(self):
        self.s.read_attempt(self.intent['operation_id'])
        changed=copy.deepcopy(self.attempt);changed['profile']['execution']['command'][-1]='unsafe-mode'
        with self.assertRaises(c.ControlFailure):subject._registered(changed)
        self.assertEqual(self.history()['counts']['create'],0)

    def test_changed_binding_reopen_refuses_without_modifying_database(self):
        self.s.close();path=Path(self.tmp.name)/'control.sqlite3';before=path.read_bytes()
        with patch.object(subject,'_bindings',return_value='sha256:'+'f'*64):
            self.reject('action-store-format-changed',subject.OperationActionStore,self.tmp.name,_clock=lambda:self.now+1)
        self.assertEqual(path.read_bytes(),before)

    def test_live_registered_source_binding_change_blocks_actions(self):
        with patch.object(subject,'_bindings',return_value='sha256:'+'f'*64):
            self.reject('action-store-format-changed',self.reserve,'create')

    def test_public_shell_mutation_invalidates_binding_and_cached_store_reads(self):
        wrapper=Path(subject.__file__).resolve().parent/'script.sh'
        self.assertIn(wrapper,subject.binding_sources())
        before=subject._bindings();self.s.read_attempt(self.intent['operation_id'])
        read=c.read_source
        def changed(path,*args):
            raw=read(path,*args)
            return raw+b'\n# fixture wrapper mutation\n' if Path(path)==wrapper else raw
        with patch.object(c,'read_source',side_effect=changed):
            self.assertNotEqual(before,subject._bindings())
            self.reject('action-store-format-changed',self.s.read_attempt,self.intent['operation_id'])
        self.assertEqual(self.history()['counts']['create'],0)

    def test_missing_typed_attachment_cannot_be_replaced_by_hash(self):
        self.s.db.execute('DELETE FROM action_attachments')
        self.reject('attachment-missing',self.s.read_attempt,self.intent['operation_id'])

if __name__=='__main__':unittest.main()
