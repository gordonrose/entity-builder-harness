"""Transaction, lifetime, conflict, corruption and typed-evidence regressions."""
import copy
import os
import sqlite3
from pathlib import Path
import tempfile
import unittest

import operation_journal as c
from local_control_store import LocalControlStore
import control_store_fixtures as f

class LocalControlStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.now=f.NOW;self.s=LocalControlStore(self.tmp.name,_clock=lambda:self.now);self.addCleanup(self.s.close)
        self.doc=f.intent();self.s.prepare(self.doc)

    def reject(self,code,call,*args,**kwargs):
        with self.assertRaises(c.ControlFailure) as found:call(*args,**kwargs)
        self.assertEqual(found.exception.code,code)

    def snapshot(self):return self.s.read(self.doc['operation_id'])
    def renew(self,claim):return self.s.renew(claim,self.snapshot()['revision'])
    def start(self):return self.s.claim(self.doc['operation_id'],f.OWNER_A)
    def advance(self,claim,event,proof=None):return self.s.advance(claim,self.snapshot()['revision'],event,proof)
    def evidence(self,claim,assertion='fixture-effect',**kwargs):
        snap=self.snapshot()
        return f.evidence(self.doc,snap['attempt'],assertion,now=self.now,revision=snap['revision'],fences=copy.deepcopy(claim['fences']),**kwargs)
    def attach(self,claim,assertion='fixture-effect',**kwargs):return self.s.put_evidence(claim,self.evidence(claim,assertion,**kwargs))
    def succeed(self,claim):
        self.advance(claim,'effect-intent');self.advance(claim,'observed')
        proof=self.attach(claim);self.advance(claim,'succeeded',proof)
    def close_operation(self,claim):
        proof=self.attach(claim,'fixture-cleanup');self.advance(claim,'cleanup-verified',proof);self.advance(claim,'closed')

    def test_prepare_is_durable_idempotent_and_binding_immutable(self):
        before=self.snapshot();self.s.prepare(copy.deepcopy(self.doc));self.assertEqual(before,self.snapshot())
        changed=copy.deepcopy(self.doc);changed['release_digest']='sha256:'+'9'*64
        self.reject('intent-conflict',self.s.prepare,changed)
        self.s.close()
        with LocalControlStore(self.tmp.name,_clock=lambda:self.now) as opened:
            self.assertEqual(opened.read(self.doc['operation_id'])['intent_digest'],c.digest(self.doc))

    def test_idempotency_key_cannot_move_between_operations(self):
        changed=f.intent('another-operation');changed['idempotency_key']=self.doc['idempotency_key']
        self.reject('intent-conflict',self.s.prepare,changed)

    def test_full_lifecycle_retains_retrievable_evidence_and_blocks_authority(self):
        claim=self.start();self.succeed(claim);self.close_operation(claim)
        snap=self.snapshot();self.assertEqual(snap['state'],'closed');self.assertFalse(snap['authorized'])
        self.assertEqual(snap['release_eligibility'],'blocked');self.assertEqual(snap['operation_authorization'],'blocked')
        for event in snap['journal']:
            if event['evidence_digest']:
                content=self.s.read_evidence(self.doc['operation_id'],event['evidence_digest'])
                self.assertEqual(c.digest(content),event['evidence_digest'])
        self.reject('operation-closed',self.s.claim,self.doc['operation_id'],f.OWNER_B)

    def test_current_lease_cannot_be_stolen(self):
        claim=self.start();self.reject('lease-held',self.s.claim,self.doc['operation_id'],f.OWNER_B)
        self.renew(claim)

    def test_expiry_produces_only_reconciliation_and_rejects_old_fence(self):
        old=self.start();self.advance(old,'effect-intent');self.now+=1001
        new=self.s.claim(self.doc['operation_id'],f.OWNER_B)
        self.assertEqual(new['mode'],'reconcile');self.assertGreater(new['fences'][0]['generation'],old['fences'][0]['generation'])
        self.assertEqual(self.snapshot()['state'],'unknown');self.reject('claim-stale',self.renew,old)
        proof=self.attach(new,'fixture-absent',effect=0);self.advance(new,'reconciled-absent',proof)
        self.reject('reconciliation-required',self.advance,new,'effect-intent')

    def test_expired_unresolved_scope_blocks_different_release(self):
        old=self.start();self.advance(old,'effect-intent');self.now+=1001
        other=f.intent('other-release',release='8');self.s.prepare(other)
        self.reject('scope-unresolved',self.s.claim,other['operation_id'],f.OWNER_B)

    def test_closed_scope_preserves_fence_across_releases(self):
        old=self.start();self.succeed(old);self.close_operation(old)
        other=f.intent('other-release',release='8');self.s.prepare(other)
        new=self.s.claim(other['operation_id'],f.OWNER_B)
        self.assertGreater(new['fences'][0]['generation'],old['fences'][0]['generation'])
        self.reject('claim-stale',self.renew,old)

    def test_atomic_multiscope_claim_does_not_take_free_scope_on_conflict(self):
        self.start()
        other=f.intent('multiscope-operation',resources=('free-resource','shared-resource'))
        self.s.prepare(other);self.reject('scope-unresolved',self.s.claim,other['operation_id'],f.OWNER_B)
        third=f.intent('free-operation',resources=('free-resource',));self.s.prepare(third)
        self.assertEqual(self.s.claim(third['operation_id'],f.OWNER_C)['mode'],'execute')

    def test_unknown_result_cannot_close_or_release_conflicting_scope(self):
        claim=self.start();self.advance(claim,'effect-intent');self.advance(claim,'unknown')
        self.reject('transition-invalid',self.advance,claim,'closed')
        self.reject('evidence-phase-invalid',self.attach,claim,'fixture-cleanup')
        other=f.intent('conflicting-operation');self.s.prepare(other)
        self.reject('scope-unresolved',self.s.claim,other['operation_id'],f.OWNER_B)

    def test_unverified_cleanup_cannot_close_even_after_success(self):
        claim=self.start();self.succeed(claim)
        self.reject('transition-invalid',self.advance,claim,'closed')
        proof=self.attach(claim,'fixture-cleanup',resources=1)
        self.reject('evidence-incompatible',self.advance,claim,'cleanup-verified',proof)

    def test_stale_revision_bool_and_fence_rejected(self):
        claim=self.start();revision=self.snapshot()['revision'];self.advance(claim,'effect-intent')
        self.reject('revision-stale',self.s.advance,claim,revision,'observed')
        self.reject('revision-invalid',self.s.advance,claim,True,'observed')
        changed=copy.deepcopy(claim);changed['fences'][0]['generation']=True
        self.reject('claim-stale',self.renew,changed)

    def test_expired_rejection_commits_clock_highwater_across_restart(self):
        claim=self.start();self.now+=1001;self.reject('claim-stale',self.renew,claim)
        self.s.close();self.now-=1000
        self.reject('clock-regressed',LocalControlStore,self.tmp.name,_clock=lambda:self.now)

    def test_clock_invalid_and_regression_rejected(self):
        self.start();self.now-=1;self.reject('clock-regressed',self.snapshot)
        self.now=True;self.reject('clock-invalid',self.snapshot)

    def test_boot_change_refuses_reopen(self):
        self.s.db.execute("UPDATE meta SET value='another-boot' WHERE key='boot'")
        self.s.close();self.reject('store-boot-changed',LocalControlStore,self.tmp.name,_clock=lambda:self.now)

    def test_deadline_does_not_grant_new_execution(self):
        self.now+=10001
        claim=self.start();self.assertEqual(claim['mode'],'reconcile');self.assertEqual(self.snapshot()['state'],'unknown')

    def test_renew_cannot_extend_execution_deadline(self):
        claim=self.start()
        for _ in range(10):self.now+=999;self.renew(claim)
        row=self.s.db.execute('SELECT expires,deadline FROM operations').fetchone()
        self.assertEqual(row['expires'],row['deadline'])
        self.now+=11;self.reject('claim-stale',self.renew,claim)

    def test_evidence_cannot_precede_effect_or_cleanup_phase(self):
        claim=self.start();self.reject('evidence-phase-invalid',self.attach,claim)
        self.advance(claim,'effect-intent');self.reject('evidence-phase-invalid',self.attach,claim,'fixture-cleanup')
        self.reject('evidence-phase-invalid',self.attach,claim,'fixture-absent',effect=0)

    def test_evidence_binding_wrong_attempt_subject_release_and_profile_rejected(self):
        claim=self.start();self.advance(claim,'effect-intent')
        for field,value in [('attempt',0),('subject_digest','sha256:'+'a'*64),('release_digest','sha256:'+'a'*64),('profile_digest','sha256:'+'a'*64),('operation_id','wrong-operation')]:
            with self.subTest(field=field):
                proof=self.evidence(claim);proof[field]=value
                self.reject('evidence-binding-invalid',self.s.put_evidence,claim,proof)

    def test_future_expired_excess_lifetime_and_pre_current_revision_evidence_rejected(self):
        claim=self.start();self.advance(claim,'effect-intent');self.now+=10;self.renew(claim)
        for changes in ({'observed_at_ms':self.now+1},{'expires_at_ms':self.now},{'expires_at_ms':self.now+5001},{'observed_at_ms':self.now-1},{'observed_revision':0}):
            with self.subTest(changes=changes):
                proof=self.evidence(claim);proof.update(changes)
                self.reject('evidence-binding-invalid',self.s.put_evidence,claim,proof)

    def test_pre_takeover_absence_and_effect_proof_rejected(self):
        old=self.start();self.advance(old,'effect-intent');proof=self.evidence(old)
        self.now+=1001;new=self.s.claim(self.doc['operation_id'],f.OWNER_B)
        self.reject('evidence-binding-invalid',self.s.put_evidence,new,proof)
        proof=self.evidence(new,'fixture-absent',effect=0);proof['fences']=old['fences']
        self.reject('evidence-binding-invalid',self.s.put_evidence,new,proof)

    def test_evidence_consumption_requires_current_journal_attachment(self):
        claim=self.start();self.advance(claim,'effect-intent');self.advance(claim,'observed');proof=self.attach(claim)
        self.renew(claim);self.reject('evidence-stale',self.advance,claim,'succeeded',proof)

    def test_cleanup_proof_expiry_or_content_loss_blocks_closure(self):
        claim=self.start();self.succeed(claim);proof=self.attach(claim,'fixture-cleanup');self.advance(claim,'cleanup-verified',proof)
        self.s.db.execute('DELETE FROM evidence WHERE digest=?',(proof,))
        self.reject('evidence-corrupt',self.advance,claim,'closed')

    def test_takeover_after_verified_cleanup_requires_new_fence_proof(self):
        old=self.start();self.succeed(old);proof=self.attach(old,'fixture-cleanup');self.advance(old,'cleanup-verified',proof)
        self.now+=1001;new=self.s.claim(self.doc['operation_id'],f.OWNER_B)
        self.reject('evidence-stale',self.advance,new,'closed')
        self.close_operation(new)

    def test_reconciliation_completed_observation_can_finish_without_reexecution(self):
        old=self.start();self.advance(old,'effect-intent');self.now+=1001;new=self.s.claim(self.doc['operation_id'],f.OWNER_B)
        proof=self.attach(new);self.advance(new,'reconciled-completed',proof)
        proof=self.attach(new);self.advance(new,'succeeded',proof);self.close_operation(new)
        self.assertEqual(self.snapshot()['attempt'],1)

    def test_evidence_payload_corruption_blocks_read_and_mutation(self):
        claim=self.start();self.advance(claim,'effect-intent');proof=self.attach(claim)
        content=self.s.read_evidence(self.doc['operation_id'],proof);content['counts']['effect_count']=0
        self.s.db.execute('UPDATE evidence SET document=? WHERE digest=?',(c.canonical(content),proof))
        self.reject('evidence-corrupt',self.snapshot);self.reject('evidence-corrupt',self.renew,claim)

    def test_intent_and_journal_corruption_fail_closed(self):
        claim=self.start()
        self.s.db.execute("UPDATE events SET digest=? WHERE sequence=0",('sha256:'+'0'*64,))
        self.reject('journal-corrupt',self.snapshot);self.reject('journal-corrupt',self.renew,claim)

    def test_changed_intent_digest_rejected(self):
        self.s.db.execute("UPDATE operations SET digest=?",('sha256:'+'0'*64,))
        self.reject('intent-corrupt',self.snapshot)

    def test_missing_evidence_cannot_be_read_by_digest_only(self):
        self.reject('evidence-missing',self.s.read_evidence,self.doc['operation_id'],'sha256:'+'0'*64)

    def test_unsafe_directory_and_database_links_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root);insecure=base/'insecure';insecure.mkdir(mode=0o755)
            self.reject('store-directory-not-private',LocalControlStore,insecure)
            linked=base/'linked';linked.symlink_to(self.tmp.name,target_is_directory=True)
            self.reject('store-unavailable',LocalControlStore,linked)
            another=base/'another';another.mkdir(mode=0o700)
            (another/'control.sqlite3').symlink_to(Path(self.tmp.name)/'control.sqlite3')
            self.reject('store-file-invalid',LocalControlStore,another)

    def test_corrupt_deadline_owner_mode_expiry_and_scope_projection_rejected(self):
        claim=self.start()
        changes=(('operations','deadline',f.NOW+100000),('operations','owner',f.OWNER_B),
                 ('operations','mode','reconcile'),('operations','expires',f.NOW+2000),
                 ('scopes','generation',99),('scopes','owner',f.OWNER_B),('scopes','expires',f.NOW+2000))
        for table,column,value in changes:
            with self.subTest(table=table,column=column):
                previous=self.s.db.execute('SELECT '+column+' FROM '+table).fetchone()[0]
                self.s.db.execute('UPDATE '+table+' SET '+column+'=?',(value,))
                self.reject('fence-corrupt' if table=='scopes' else 'journal-corrupt',self.snapshot)
                self.s.db.execute('UPDATE '+table+' SET '+column+'=?',(previous,))
        self.renew(claim)

    def test_renewal_requires_current_revision_and_rejects_bool(self):
        claim=self.start();revision=self.snapshot()['revision'];self.renew(claim)
        self.reject('revision-stale',self.s.renew,claim,revision)
        self.reject('revision-invalid',self.s.renew,claim,True)

    def test_changed_stored_schema_fingerprint_refuses_reopen(self):
        self.s.db.execute("UPDATE meta SET value='sha256:changed' WHERE key='schemas'")
        self.s.close();self.reject('store-format-changed',LocalControlStore,self.tmp.name,_clock=lambda:self.now)

    def test_closed_tombstone_fence_corruption_cannot_reuse_generation(self):
        claim=self.start();self.succeed(claim);self.close_operation(claim)
        other=f.intent('other-release');self.s.prepare(other)
        self.s.db.execute('UPDATE scopes SET generation=0')
        self.reject('fence-corrupt',self.s.claim,other['operation_id'],f.OWNER_B)

    def test_active_scope_cannot_be_disguised_as_free_for_another_release(self):
        self.start();other=f.intent('other-release');self.s.prepare(other)
        self.s.db.execute('UPDATE scopes SET operation=NULL')
        self.reject('fence-corrupt',self.s.claim,other['operation_id'],f.OWNER_B)
        self.s.db.execute('UPDATE scopes SET owner=NULL,expires=0')
        self.reject('fence-corrupt',self.s.claim,other['operation_id'],f.OWNER_B)

    def test_released_scope_requires_complete_prior_closed_journal(self):
        claim=self.start();self.succeed(claim);self.close_operation(claim)
        other=f.intent('other-release');self.s.prepare(other)
        self.s.db.execute('DELETE FROM events WHERE operation=? AND sequence=(SELECT max(sequence) FROM events WHERE operation=?)',
                          (self.doc['operation_id'],self.doc['operation_id']))
        self.reject('journal-corrupt',self.s.claim,other['operation_id'],f.OWNER_B)

    def test_missing_fence_lineage_refuses_new_claim(self):
        claim=self.start();self.succeed(claim);self.close_operation(claim)
        other=f.intent('other-release');self.s.prepare(other)
        self.s.db.execute('DELETE FROM fence_history')
        self.reject('fence-corrupt',self.s.claim,other['operation_id'],f.OWNER_B)

    def test_delete_full_mode_verified_and_existing_wal_refused(self):
        self.assertEqual(self.s.db.execute('PRAGMA journal_mode').fetchone()[0],'delete')
        self.assertEqual(self.s.db.execute('PRAGMA synchronous').fetchone()[0],2)
        self.s.db.execute('PRAGMA journal_mode=WAL');self.s.close()
        self.reject('store-journal-mode-invalid',LocalControlStore,self.tmp.name,_clock=lambda:self.now)
        with sqlite3.connect(str(Path(self.tmp.name)/'control.sqlite3')) as existing:
            self.assertEqual(existing.execute('PRAGMA journal_mode').fetchone()[0],'wal')

    def test_oversized_existing_sql_value_is_bounded_classified_failure(self):
        self.s.close()
        with sqlite3.connect(str(Path(self.tmp.name)/'control.sqlite3')) as existing:
            existing.execute("UPDATE operations SET document=?",(b'x'*65536,))
        self.s=LocalControlStore(self.tmp.name,_clock=lambda:self.now);self.addCleanup(self.s.close)
        self.reject('store-transaction-failed',self.snapshot)

    def test_closed_connection_reports_classified_failure(self):
        self.s.close()
        self.reject('store-unavailable',self.snapshot)

if __name__=='__main__':unittest.main()
