"""Closed inert-fixture attempt identity; a lease is never provider authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.finite-recovery-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind fixed inert finite commands and exact owned resource identity before durable dispatch.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.finite-recovery-engine
#     path: scripts/04.deploy/operational-realization-gate/finite_recovery_engine.py
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import uuid

from jsonschema import Draft202012Validator
import finite_job_contracts as finite
import operation_journal as journal

DIRECTORY=Path(__file__).resolve().parent
SCHEMAS=('finite-recovery-attempt','finite-recovery-observation','finite-recovery-result','finite-recovery-conformance','finite-recovery-error','finite-recovery-image-lock')
DISPATCH_ACTIONS=frozenset({'create','start'})
ACTION_LIMITS={'create':1,'start':1,'inspect':32,'logs':3,'cleanup':3}
BLOCKED=dict(authorized=False,release_eligibility='blocked',operation_authorization='blocked',
             qualification_verdict='blocked',source_closure='blocked')
digest=journal.digest

def fail(code):journal.fail('finite-recovery-'+code)

def schema(name):
    if name not in SCHEMAS:fail('schema-invalid')
    return journal._parse_schema(name,journal.read_source(journal.SCHEMA_DIR/(name+'.schema.yml')))

def validate(name,value):
    journal.canonical(value)
    if next(Draft202012Validator(schema(name)).iter_errors(value),None):fail('record-invalid')
    return value

def fixture_files():
    raw=journal.read_source(DIRECTORY/'fixtures/finite-jobs/jobs/task.cjs',16384)
    return [{'path':'jobs/task.cjs','digest':'sha256:'+hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}]

def make_attempt(image_id, *, run_id=None, ownership_token=None):
    run_id=run_id or uuid.uuid4().hex;token=ownership_token or uuid.uuid4().hex
    files=fixture_files()
    profile={'schema':'finite-job-profile/v1','id':'fixture-success',
             'artifact':{'image_id':image_id,'payload_digest':digest(files)},
             'execution':{'entrypoint':['/nodejs/bin/node'],'command':['jobs/task.cjs','success'],'working_dir':'/app'},
             'limits':{'timeout_seconds':15,'output_bytes':4096},
             'completion':{'protocol':'finite-job-terminal/v1','required_checks':['fixture-calculation']}}
    return validate_attempt({'schema':'finite-recovery-attempt/v1','operation_id':'finite-recovery-'+run_id,
        'run_id':run_id,'resource':{'kind':'docker-container','name':'release-control-'+token,'ownership_token':token},
        'profile':profile,'expected_files':files,'limits':{'recovery_timeout_ms':30000,'action_limits':dict(ACTION_LIMITS)}})

def validate_attempt(value):
    validate('finite-recovery-attempt',value)
    profile=value['profile'];finite.validate_profile(profile)
    if (value['operation_id']!='finite-recovery-'+value['run_id']
            or value['resource']['name']!='release-control-'+value['resource']['ownership_token']
            or value['run_id']==value['resource']['ownership_token']
            or value['expected_files']!=fixture_files()
            or profile['artifact']['payload_digest']!=digest(value['expected_files'])
            or profile['id']!='fixture-success'
            or profile['execution']!={'entrypoint':['/nodejs/bin/node'],'command':['jobs/task.cjs','success'],'working_dir':'/app'}
            or profile['limits']!={'timeout_seconds':15,'output_bytes':4096}
            or profile['completion']!={'protocol':'finite-job-terminal/v1','required_checks':['fixture-calculation']}):
        fail('attempt-binding-invalid')
    return value

def validate_observation(value,attempt):
    validate_attempt(attempt);validate('finite-recovery-observation',value)
    if value['operation_id']!=attempt['operation_id'] or value['attempt_digest']!=digest(attempt):fail('observation-binding-invalid')
    state=value['state']
    if state=='absent':
        if any(value[key] is not None for key in ('resource_id','exit_code','oom_killed','terminal')):fail('observation-invalid')
    elif value['resource_id'] is None or type(value['oom_killed']) is not bool:fail('observation-invalid')
    elif state in ('created','running'):
        if value['exit_code'] is not None or value['terminal'] is not None or value['oom_killed']:fail('observation-invalid')
    elif type(value['exit_code']) is not int:fail('observation-invalid')
    if value['terminal'] is not None:
        if state!='exited' or value['exit_code']!=0 or value['oom_killed']:fail('observation-invalid')
        finite.evaluate_terminal(journal.canonical(value['terminal']),attempt['profile'],attempt['run_id'])
    return value

def observation(attempt,state,resource_id=None,exit_code=None,oom_killed=None,terminal=None):
    return validate_observation({'schema':'finite-recovery-observation/v1','operation_id':attempt['operation_id'],
        'attempt_digest':digest(attempt),'resource_id':resource_id,'state':state,'exit_code':exit_code,
        'oom_killed':oom_killed,'terminal':deepcopy(terminal)},attempt)

def terminal(attempt):
    return {'schema':'finite-job-terminal/v1','run_id':attempt['run_id'],
            'profile_digest':finite.profile_digest(attempt['profile']),'outcome':'completed',
            'checks':[{'id':'fixture-calculation','verdict':'passed'}]}


def validate_action_observation(action,value,attempt):
    validate_observation(value,attempt)
    states={'create':{'created'},'start':{'running','exited'},'inspect':{'absent','created','running','exited'},
            'logs':{'exited'},'cleanup':{'absent'}}
    if action not in states or value['state'] not in states[action]:fail('action-observation-invalid')
    if (action=='logs') != (value['terminal'] is not None):fail('action-observation-invalid')
    return value


def validate_action_preconditions(action,attempt,history,state,mode):
    validate_attempt(attempt)
    if action not in ACTION_LIMITS:fail('action-invalid')
    known=history['known_resource_id'];counts=history['counts']
    fresh=bool(history['records'] and history['records'][-1]['event']=='observed')
    observations=history['observations'];last=observations[-1]['observation'] if observations else None
    if action=='create':
        if known is not None or counts['start'] or counts['create']:fail('dispatch-precondition')
    elif action=='start':
        if known is None or counts['create']!=1 or counts['start'] or counts['cleanup'] or not fresh or last is None or last['state']!='created':fail('dispatch-precondition')
    elif action=='logs':
        if known is None or counts['start']!=1 or not fresh or last is None or last['state']!='exited':fail('logs-precondition')
    elif action=='cleanup':
        if known is None or not fresh or last is None or last['state']=='absent':fail('cleanup-precondition')
        settled=state in ('succeeded','failed','cleanup-verified')
        never_started=counts['start']==0 and last['state']=='created'
        if not settled and not never_started:fail('cleanup-precondition')
    return True
