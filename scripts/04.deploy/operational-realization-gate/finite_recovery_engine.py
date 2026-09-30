"""The existing bounded container engine, with exact inert attempt reconstruction."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.finite-recovery-engine
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reconstruct a durably bound inert fixture container without repeating create or start requests.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.finite-recovery-conformance
#     path: scripts/04.deploy/operational-realization-gate/finite_recovery_conformance.py
import json
import re
import time

from container_engine import Engine, CONTAINER_PATTERN, EngineFailure
import finite_recovery_contracts as contract

LOG_CONFIG={'Type':'local','Config':{'max-size':'16k','max-file':'1','compress':'false'}}

class RecoveryEngine(Engine):
    """Private inert-fixture adapter. Store tickets are scheduling records only.

    The controller reserves each action durably before calling this adapter.
    Actual effects remain restricted to the fixed fixture image/command and local
    Docker endpoint. Neither a lease nor a ticket grants provider authority.
    """
    def __init__(self,scratch,runner=None,*,_monotonic=None):
        super().__init__(scratch,runner=runner)
        self._monotonic=_monotonic or time.monotonic
        self._action_deadline=None

    def _call(self,args,**kwargs):
        if self._action_deadline is None:contract.fail('action-not-started')
        remaining=self._action_deadline-self._monotonic()
        if remaining<=0:contract.fail('action-deadline')
        kwargs['timeout']=min(kwargs.get('timeout',remaining),remaining)
        result=super()._call(args,**kwargs)
        if self._monotonic()>=self._action_deadline:contract.fail('action-deadline')
        return result

    def _binding(self,attempt,known_id):
        contract.validate_attempt(attempt)
        if known_id is not None and (type(known_id) is not str or not CONTAINER_PATTERN.fullmatch(known_id)):
            contract.fail('resource-id-invalid')
        resource=attempt['resource'];image=attempt['profile']['artifact']['image_id']
        if self.inspect_job_image(image)['command']!=['jobs/task.cjs','success']:
            contract.fail('fixture-image-required')
        name=resource['name'];entry={'token':resource['ownership_token'],'image':image,'id':known_id}
        old=self._owned.get(name)
        if old is not None and old['id'] is not None and known_id is not None and old['id']!=known_id:
            contract.fail('resource-id-mismatch')
        self._owned[name]=entry
        return name,image,{'RELEASE_CONTROL_PROFILE_DIGEST':contract.finite.profile_digest(attempt['profile']),
                           'RELEASE_CONTROL_RUN_ID':attempt['run_id']}

    def _observed(self,attempt,name,image,environment):
        value=self._container(name)
        state=self._restrictions(value,image,running=None,command=attempt['profile']['execution']['command'],
                                 environment=environment,allow_oom=True)
        if value['HostConfig'].get('LogConfig')!=LOG_CONFIG:contract.fail('log-restriction-mismatch')
        status=state.get('Status')
        if (status not in ('created','running','exited') or (status=='running') is not state['Running']
                or value.get('RestartCount')!=0):contract.fail('resource-state-invalid')
        code=state.get('ExitCode') if status=='exited' else None
        return contract.observation(attempt,status,value['Id'],code,state['OOMKilled'])

    def _absent(self,name,known_id=None):
        # Only a successful exact-name list can establish current absence; an
        # inspect failure, unreachable daemon or foreign resource cannot.
        raw=self._call(['container','ls','--all','--quiet','--no-trunc','--filter','name=^/'+name+'$'],max_output=4096)
        try:rows=raw.decode('ascii').splitlines()
        except UnicodeError:contract.fail('resource-list-invalid')
        if len(rows)>1 or any(not CONTAINER_PATTERN.fullmatch(row) for row in rows):contract.fail('resource-list-invalid')
        if rows:return False
        if known_id is not None:
            remaining=self._call(['container','ls','--all','--quiet','--no-trunc','--filter','id='+known_id],max_output=4096)
            if remaining.strip():contract.fail('resource-name-changed')
        return True

    def perform(self,attempt,action,known_id=None,*,timeout_seconds=2):
        """Execute one previously reserved local action; never retry inside transport."""
        if action not in contract.ACTION_LIMITS:contract.fail('action-invalid')
        if type(timeout_seconds) not in (int,float) or not 0<timeout_seconds<=2:contract.fail('action-bound-invalid')
        self._action_deadline=self._monotonic()+timeout_seconds
        name,image,environment=self._binding(attempt,known_id)
        if action=='create':
            if known_id is not None:contract.fail('resource-already-known')
            args=self._create_arguments(image,name,attempt['resource']['ownership_token'],
                command=attempt['profile']['execution']['command'],environment=environment,retain_fixture_terminal=True)
            raw=self._call(args,max_output=4096)
            try:resource_id=raw.decode('ascii').strip()
            except UnicodeError:contract.fail('resource-id-invalid')
            if not CONTAINER_PATTERN.fullmatch(resource_id):contract.fail('resource-id-invalid')
            self._owned[name]['id']=resource_id
            return self._observed(attempt,name,image,environment)
        if action=='inspect':
            if self._absent(name,known_id):return contract.observation(attempt,'absent')
            return self._observed(attempt,name,image,environment)
        if known_id is None:contract.fail('resource-id-required')
        observed=self._observed(attempt,name,image,environment)
        if action=='start':
            if observed['state']!='created':contract.fail('start-state-invalid')
            started=self._call(['start',known_id],max_output=4096).strip()
            if started!=known_id.encode('ascii'):contract.fail('start-response-invalid')
            return self._observed(attempt,name,image,environment)
        if action=='logs':
            if observed['state']!='exited' or observed['exit_code']!=0 or observed['oom_killed']:
                contract.fail('terminal-state-invalid')
            raw=self._call(['logs','--tail','2',known_id],max_output=attempt['profile']['limits']['output_bytes'])
            contract.finite.evaluate_terminal(raw,attempt['profile'],attempt['run_id'])
            observed['terminal']=contract.terminal(attempt)
            return contract.validate_observation(observed,attempt)
        if action=='cleanup':
            self._cleanup(name)
            if not self._absent(name,known_id):contract.fail('cleanup-unverified')
            return contract.observation(attempt,'absent')
        contract.fail('action-invalid')
