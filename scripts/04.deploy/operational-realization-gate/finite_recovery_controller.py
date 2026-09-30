"""Recover one durably bound inert fixture through the existing local operation store."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.finite-recovery-controller
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Consume durable actions before exact inert effects and reconcile without replay or authority grants.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.finite-recovery-conformance
#     path: scripts/04.deploy/operational-realization-gate/finite_recovery_conformance.py
from copy import deepcopy
import time

import finite_recovery_contracts as contract
from container_engine import EngineFailure
from operation_actions import OperationActionStore


def make_intent(attempt):
    """Explicit fixed fixture budgets, not policy defaults for production."""
    contract.validate_attempt(attempt)
    scope={'provider':'local-fixture','namespace':'finite-recovery-conformance',
           'target':'local-docker','resource':attempt['resource']['name']}
    policy={'scope':'local-conformance','lease_ms':3000,'operation_timeout_ms':15000,
            'call_timeout_ms':2000,'max_attempts':1,'evidence_lifetime_ms':10000}
    value={'schema':'operation-control/v1','operation_id':attempt['operation_id'],
           'idempotency_key':contract.digest(attempt),
           'release_digest':contract.digest({'fixture':attempt['expected_files']}),
           'profile_digest':contract.digest(attempt['profile']),
           'artifact_digest':attempt['profile']['artifact']['image_id'],
           'environment_digest':contract.digest({'scope':'isolated-inert-fixture'}),
           'authority_policy_digest':contract.digest(policy),'recovery_route':'local-fixture-reconcile',
           'scopes':[{'scope_id':contract.digest(scope),**scope}],'policy':policy}
    return contract.journal.validate('operation-control',value)


class RecoveryController:
    def __init__(self,store,engine,*,_checkpoint=None,_sleep=None):
        if not isinstance(store,OperationActionStore):contract.fail('store-required')
        self.store=store;self.engine=engine
        self._checkpoint=_checkpoint or (lambda phase:None)
        self._sleep=_sleep or time.sleep

    def prepare(self,intent,attempt):
        digest=self.store.prepare_attempt(intent,attempt)
        self._checkpoint('intent-committed')
        return digest

    def _advance(self,claim,event,evidence=None):
        current=self.store.read(claim['operation_id'])
        return self.store.advance(claim,current['revision'],event,evidence)

    def _action(self,claim,attempt,action):
        history=self.store.read_actions(claim['operation_id'])
        ticket=self.store.reserve_action(claim,history['revision'],action)
        self._checkpoint(action+'-reserved')
        history=self.store.read_actions(claim['operation_id'])
        remaining=self.store.action_budget(claim,history['revision'],ticket)
        observation=self.engine.perform(attempt,action,history['known_resource_id'],
                                        timeout_seconds=min(2,remaining/1000))
        self._checkpoint(action+'-effect')
        history=self.store.read_actions(claim['operation_id'])
        self.store.observe_action(claim,history['revision'],ticket,observation)
        if action=='logs':self._checkpoint('terminal-observed')
        return observation

    def _evidence(self,claim,assertion,effects):
        current=self.store.read(claim['operation_id']);intent=current['intent']
        history=self.store.read_actions(claim['operation_id'])
        last=history['observations'][-1]['observation'] if history['observations'] else None
        if assertion=='fixture-effect':
            if last is None or last['terminal'] is None or history['counts']['start']!=1:
                contract.fail('effect-unproven')
        elif last is None or last['state']!='absent':contract.fail('absence-unproven')
        now=self.store._clock()
        value={'schema':'operation-evidence/v1','operation_id':intent['operation_id'],
               'release_digest':intent['release_digest'],'profile_digest':intent['profile_digest'],
               'attempt':current['attempt'],'observed_revision':current['revision'],
               'fences':deepcopy(claim['fences']),'assertion':assertion,'verdict':'passed',
               'subject_digest':intent['artifact_digest'],'observed_at_ms':now,
               'expires_at_ms':min(now+intent['policy']['evidence_lifetime_ms'],history['recovery_deadline_ms']),
               'counts':{'effect_count':effects,'owned_resources':0 if last['state']=='absent' else 1}}
        return self.store.put_evidence(claim,value)

    def result(self,operation):
        current=self.store.read(operation);history=self.store.read_actions(operation)
        attempt=self.store.read_attempt(operation)
        terminal=any(row['observation']['terminal'] is not None for row in history['observations'])
        value={'schema':'finite-recovery-result/v1','scope':'local-inert-recovery',
               'operation_id':operation,'attempt_digest':contract.digest(attempt),'state':current['state'],
               'terminal_observed':terminal,'cleanup_verified':current['state']=='closed',
               'resource_id':history['known_resource_id'],'action_counts':history['counts'],
               'journal_digest':contract.digest([row['event_digest'] for row in current['journal']]),
               'action_journal_digest':contract.digest([row['event_digest'] for row in history['records']]),
               'semantic_verdict':'unverified','product_profile_updates':[],**contract.BLOCKED}
        return contract.validate('finite-recovery-result',value)

    def run(self,operation,owner):
        """Continue while known safe; unresolved consumed actions are never repeated."""
        current=self.store.read(operation)
        if current['state']=='closed':return self.result(operation)
        attempt=self.store.read_attempt(operation)
        claim=self.store.claim(operation,owner)
        try:
            if claim['mode']=='reconcile':self._action(claim,attempt,'inspect')
            for unused in range(64):
                current=self.store.read(operation);history=self.store.read_actions(operation)
                state=current['state'];counts=history['counts']
                last=history['observations'][-1]['observation'] if history['observations'] else None
                if state=='closed':return self.result(operation)
                self.store.renew(claim,current['revision'])
                if state=='prepared':
                    if claim['mode']=='execute':self._advance(claim,'effect-intent')
                    else:self._advance(claim,'failed')
                elif state=='executing' and counts['create']==0:
                    self._action(claim,attempt,'create')
                elif state=='executing' and counts['start']==0 and last is not None and last['state']=='created':
                    self._action(claim,attempt,'start')
                elif state in ('executing','unknown'):
                    if last is None:
                        self._action(claim,attempt,'inspect')
                    elif last['state']=='absent':
                        # Absence cannot resolve a dispatched request. Only no create
                        # reservation, or a never-started identity positively observed
                        # and then cleaned, is sufficient to abandon this fixture.
                        cleaned=(counts['start']==0 and history['known_resource_id'] is not None
                                 and any(row['observation']['state']=='created' for row in history['observations'])
                                 and counts['cleanup']>0)
                        if state=='unknown' and (counts['create']==0 or cleaned):
                            proof=self._evidence(claim,'fixture-absent',0)
                            self._advance(claim,'reconciled-absent',proof)
                        else:return self.result(operation)
                    elif last['state']=='created':
                        if state=='unknown' and counts['start']==0:self._action(claim,attempt,'cleanup')
                        else:return self.result(operation)
                    elif last['state']=='running':
                        self._sleep(0.05);self._action(claim,attempt,'inspect')
                    elif last['exit_code']!=0 or last['oom_killed']:
                        if state=='executing':self._advance(claim,'failed')
                        else:return self.result(operation)
                    elif last['terminal'] is None:
                        self._action(claim,attempt,'logs')
                    elif state=='executing':self._advance(claim,'observed')
                    else:
                        proof=self._evidence(claim,'fixture-effect',1)
                        self._advance(claim,'reconciled-completed',proof)
                elif state=='observing':
                    proof=self._evidence(claim,'fixture-effect',1)
                    self._advance(claim,'succeeded',proof)
                elif state in ('succeeded','failed','cleanup-verified'):
                    if last is None or last['state']!='absent':self._action(claim,attempt,'cleanup')
                    else:
                        proof=self._evidence(claim,'fixture-cleanup',1 if counts['start'] else 0)
                        self._advance(claim,'cleanup-verified',proof)
                        self._checkpoint('cleanup-verified')
                        self._advance(claim,'closed')
                        return self.result(operation)
            return self.result(operation)
        except (contract.journal.ControlFailure,contract.finite.ReleaseFailure,EngineFailure):
            # Preserve the consumed request and scope ownership. Safe inspection
            # by a later claim, never a blind replay, is the only continuation.
            current=self.store.read(operation)
            if current['state'] in ('executing','observing'):
                try:self._advance(claim,'unknown')
                except contract.journal.ControlFailure:pass
            return self.result(operation)
