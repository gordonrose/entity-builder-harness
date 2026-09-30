"""Bind existing passive target inspectors; never infer source equivalence or authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.aws-selected-readiness
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind fixed passive staging inspections to the current selected source graph with blocked execution authority.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [network]
#   used_by:
#   - id: deploy.script.selected-readiness-cli
#     path: scripts/04.deploy/operational-realization-gate/selected_readiness_cli.py
from argparse import Namespace
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import time
from jsonschema import Draft202012Validator

import selected_blueprint as bp
import release_compiler as release

ROOT = Path(__file__).resolve().parents[5]
ADAPTER = 'scripts/04.deploy/release-control/adapters/aws/selected_readiness.py'
CLI = 'scripts/04.deploy/operational-realization-gate/selected_readiness_cli.py'
SCHEMAS = 'infra/04.deploy/contracts/release-control/v1/'
LEGACY = {
 'reconciliation':'scripts/04.deploy/reconcile-platform-shell-staging/script.py',
 'candidate':'scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py',
 'relational':'scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py',
}
ALLOW = {('sts','get-caller-identity'),('cloudformation','describe-stacks'),
 ('ecs','describe-services'),('ecs','describe-task-definition'),
 ('s3api','get-public-access-block'),('s3api','get-bucket-encryption'),
 ('s3api','get-bucket-ownership-controls'),('s3api','get-bucket-lifecycle-configuration'),
 ('s3api','get-bucket-policy-status'),('budgets','describe-budget')}
CHECK_IDS=('aws-account','artifact-stack-status','artifact-passive-drift','foundation-stack-status','foundation-passive-drift','service-stack-status','service-passive-drift','artifact-bucket-public-access-control','artifact-bucket-encryption','artifact-bucket-ownership','artifact-bucket-lifecycle','artifact-bucket-policy-status','platform-shell-budget','task-group-and-candidate-observation')
MAX_BYTES=1024*1024
WHOLE_SECONDS=180
CALL_SECONDS=30
BLOCKED={'authorized':False,'release_eligibility':'blocked','operation_authorization':'blocked',
 'qualification_verdict':'blocked','source_equivalence':'blocked','source_revision_status':'declared',
 'artifact_identity_status':'declared'}

class ReadinessFailure(Exception):
 def __init__(self,code): self.code=code;super().__init__(code)

def fail(code):raise ReadinessFailure(code)
def digest(v):return release.digest_document(v)
def stamp(seconds):return datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def load_module(name,path):
 spec=importlib.util.spec_from_file_location('_selected_readiness_'+name,path)
 if spec is None or spec.loader is None:fail('readiness-dependency-unavailable')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def implementation():
 paths=[ADAPTER,CLI,SCHEMAS+'selected-readiness-result.schema.yml',SCHEMAS+'selected-readiness-error.schema.yml',
  'scripts/04.deploy/release-control/selected_blueprint.py','scripts/04.deploy/operational-realization-gate/release_compiler.py',
  'scripts/04.deploy/operational-realization-gate/blueprint_cli.py',*LEGACY.values()]
 values={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
 return digest(values)

def bounded_aws(command,policy,timeout):
 """Capture capped provider bytes in memory only; no raw diagnostic or response files."""
 if tuple(command[:2]) not in ALLOW:fail('readiness-call-not-allowed')
 env=dict(os.environ);env.update(AWS_PAGER='',AWS_CLI_AUTO_PROMPT='off',AWS_MAX_ATTEMPTS='1',AWS_RETRY_MODE='standard')
 argv=['aws',*command,'--region',policy['region'],'--profile',policy['aws_profile'],'--output','json']
 try:child=subprocess.Popen(argv,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 except OSError:fail('readiness-inspection-unavailable')
 selector=selectors.DefaultSelector();buffers={'stdout':bytearray(),'stderr':bytearray()}
 selector.register(child.stdout,selectors.EVENT_READ,'stdout');selector.register(child.stderr,selectors.EVENT_READ,'stderr')
 deadline=time.monotonic()+timeout
 try:
  while selector.get_map():
   remaining=deadline-time.monotonic()
   if remaining<=0:fail('readiness-inspection-timeout')
   for key,_ in selector.select(min(remaining,.2)):
    data=os.read(key.fileobj.fileno(),65536)
    if not data:selector.unregister(key.fileobj);continue
    if len(buffers[key.data])+len(data)>MAX_BYTES:fail('readiness-output-limit')
    buffers[key.data].extend(data)
  if child.wait(timeout=max(.001,deadline-time.monotonic()))!=0:fail('readiness-inspection-unavailable')
  def pairs(items):
   result={}
   for k,v in items:
    if k in result:fail('readiness-provider-shape-invalid')
    result[k]=v
   return result
  value=json.loads(buffers['stdout'],object_pairs_hook=pairs,parse_constant=lambda _:fail('readiness-provider-shape-invalid'))
  release.bounded_json(value,max_nodes=30000)
  return value
 except (ValueError,UnicodeError,subprocess.TimeoutExpired):fail('readiness-provider-shape-invalid')
 finally:
  selector.close()
  if child.poll() is None:
   try:os.killpg(child.pid,signal.SIGKILL)
   except ProcessLookupError:pass
  child.wait();child.stdout.close();child.stderr.close()

def validate_result(result):
 release.bounded_json(result,max_nodes=20000)
 schema=release.load_document(ROOT/SCHEMAS/'selected-readiness-result.schema.yml')
 if schema.get('$id')!='urn:release-control:selected-readiness-result:v1' or schema.get('$schema')!='https://json-schema.org/draft/2020-12/schema':fail('readiness-result-invalid')
 def closed(node):
  if isinstance(node,dict):
   if any(key in node for key in ('$ref','$dynamicRef','$recursiveRef')):fail('readiness-result-invalid')
   if node.get('type')=='object' and (node.get('additionalProperties') is not False or set(node.get('properties',{}))!=set(node.get('required',[]))):fail('readiness-result-invalid')
   for value in node.values():closed(value)
  elif isinstance(node,list):
   for value in node:closed(value)
 closed(schema);Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(result)
 if any(result[k]!=v or type(result[k]) is not type(v) for k,v in BLOCKED.items()):fail('readiness-result-invalid')
 if result['result_digest']!=digest({k:v for k,v in result.items() if k!='result_digest'}):fail('readiness-result-invalid')
 if result['implementation_digest']!=implementation():fail('readiness-result-invalid')
 observed=datetime.fromisoformat(result['observed_at_utc'].replace('Z','+00:00')).timestamp()
 expires=datetime.fromisoformat(result['expires_at_utc'].replace('Z','+00:00')).timestamp()
 if not observed<=time.time()<expires or not 0<expires-observed<=900:fail('readiness-result-invalid')
 if any(x['id'] not in CHECK_IDS for x in result['checks']) or len({x['id'] for x in result['checks']})!=len(result['checks']):fail('readiness-result-invalid')
 if result['verdict']=='observed' and [x['id'] for x in result['checks']]!=list(CHECK_IDS):fail('readiness-result-invalid')
 if len({x['operation_id'] for x in result['subjects']})!=13:fail('readiness-result-invalid')
 if len({x['group_digest'] for x in result['groups']})!=len(result['groups']):fail('readiness-result-invalid')
 known={x['group_digest']:x for x in result['groups']}
 for row in result['subjects']:
  if row['observation']=='pending' and any(row[k] is not None for k in ('task_revision_digest','configured_image_digest','identity_digest','configuration_digest','image_matches_declared_release','explicit_command_matches_source')):fail('readiness-result-invalid')
  if row['observation']=='observed' and any(row[k] is None for k in ('task_revision_digest','configured_image_digest','identity_digest','configuration_digest','image_matches_declared_release')):fail('readiness-result-invalid')
  if row['observation']=='observed' and (row['group_digest'] not in known or row['task_revision_digest']!=known[row['group_digest']]['task_revision_digest']):fail('readiness-result-invalid')
 if result['verdict']=='observed' and (len(known)!=9 or any(x['observation']!='observed' for x in result['subjects']) or result['findings'] or any(c['verdict']!='observed' for c in result['checks'])):fail('readiness-result-invalid')
 if result['effect_summary']!={'provider_effects_requested':0,'secret_values_requested':0,'observed_task_groups':len(result['groups']),'observed_subjects':sum(x['observation']=='observed' for x in result['subjects'])}:fail('readiness-result-invalid')
 return result

def inspect(root,blueprint,source_revision,image_digest,release_id,*,_transport=None,_clock=None,_monotonic=None):
 clock=_clock or time.time;monotonic=_monotonic or time.monotonic
 start=clock();deadline=monotonic()+WHOLE_SECONDS
 impl=implementation()
 compiled=bp.compile_blueprint(root,blueprint,source_revision,image_digest,release_id)
 root=Path(root).resolve()
 # Maintained inspectors are code, never executable files uploaded with a source tree.
 if any((root/path).read_bytes()!=(ROOT/path).read_bytes() for path in [bp.PROFILE,*LEGACY.values()]):fail('readiness-inspector-source-mismatch')
 modules={name:load_module(name,ROOT/path) for name,path in LEGACY.items()}
 rec,candidate,relational=(modules[x] for x in ('reconciliation','candidate','relational'))
 policy=rec.resolve_policy(rec.load_yaml(root/bp.PROFILE))
 if (policy['account_id'],policy['region'],policy['aws_profile'])!=(candidate.ACCOUNT,candidate.REGION,'kanbien-dev'):fail('readiness-target-mismatch')
 ttl=policy['maximum_service_stage_six_evidence_age_seconds']
 if type(ttl) is not int or ttl!=900:fail('readiness-policy-invalid')
 args=Namespace(aws_cli='aws',aws_credential_source='target-profile',timeout_seconds=CALL_SECONDS)
 calls=[];evidence_expiry=start+ttl;stale_drift=False
 def read(command):
  nonlocal evidence_expiry,stale_drift
  if type(command) is not list or any(type(v) is not str for v in command) or tuple(command[:2]) not in ALLOW:fail('readiness-call-not-allowed')
  remaining=deadline-monotonic()
  if remaining<=0:fail('readiness-inspection-timeout')
  calls.append(tuple(command[:2]))
  value=(_transport or bounded_aws)(command,policy,min(CALL_SECONDS,remaining))
  release.bounded_json(value,max_nodes=30000)
  if command[:2]==['ecs','describe-services']:
   services=value.get('services') if type(value) is dict else None
   if type(services) is not list or len(services)!=1 or type(services[0]) is not dict or value.get('failures',[]):fail('readiness-target-baseline-invalid')
   service=services[0];name=command[command.index('--services')+1]
   service_arn=candidate.CLUSTER.replace(':cluster/',':service/')+'/'+name
   if (service.get('serviceName')!=name or service.get('clusterArn')!=candidate.CLUSTER or service.get('serviceArn')!=service_arn
    or service.get('status')!='ACTIVE' or any(type(service.get(key)) is not int or service[key]<0 for key in ('desiredCount','runningCount','pendingCount'))
    or service['pendingCount']!=0):fail('readiness-target-baseline-invalid')
  if command[:2]==['cloudformation','describe-stacks'] and any('DriftInformation' in v for v in command) and type(value) is dict:
   try:
    checked=datetime.fromisoformat(str(value.get('checked')).replace('Z','+00:00'))
    if checked.tzinfo is None:fail('readiness-provider-shape-invalid')
    age=clock()-checked.timestamp()
    stale_drift=stale_drift or age<0 or age>policy['maximum_drift_evidence_age_seconds']
    evidence_expiry=min(evidence_expiry,checked.timestamp()+policy['maximum_drift_evidence_age_seconds'])
   except (ValueError,TypeError):fail('readiness-provider-shape-invalid')
  return value
 rec.run_aws=lambda _args,_policy,command,failure_code='aws-verification-unavailable':read(command)
 candidate.aws=lambda command,_policy,_failure:read(command)
 relational.aws=lambda command,_policy,allowed_not_found_code=None:read(command)
 cpolicy={'profile':policy['aws_profile'],'source_service':candidate.SOURCE_SERVICE,'application_container':'platform-shell',
  'candidate_task_family':'kanbien-staging-platform-shell-candidate-preflight'}
 rpolicy={'profile':policy['aws_profile'],'cluster':candidate.CLUSTER}
 source_rows={r['id']:r for r in bp.profiles.discover(root)}
 projected={r['operation_id']:r for r in compiled['operation_projection']}
 grouped={}
 subjects=[]
 for op in blueprint['operations']:
  logical=op['source_profile'].split('-')[1];container=op['source_profile'].split('-',2)[2]
  projected_row=projected[op['operation_id']]
  grouped.setdefault(logical,[]).append((op,container,projected_row))
  subjects.append({'operation_id':op['operation_id'],'group_digest':projected_row['execution_group_digest'],
   'task_revision_digest':None,'configured_image_digest':None,'image_matches_declared_release':None,
   'explicit_command_matches_source':None,'identity_digest':None,'configuration_digest':None,'observation':'pending'})
 if len(grouped)!=9 or len(subjects)!=13:fail('readiness-source-groups-invalid')
 result={'schema':'selected-readiness-result/v1','scope':'selected-target-passive-readiness','target_id':'kanbien/staging','verdict':'blocked',**BLOCKED,
  'blueprint_result_digest':compiled['result_digest'],'release_digest':compiled['compiled_release']['release_digest'],
  'source_bindings':compiled['source_bindings'],'implementation_digest':impl,
  'target_binding_digest':digest({k:policy[k] for k in ('account_id','region','aws_profile','foundation_stack','service_stack','artifact_stack')}),
  'observed_at_utc':stamp(start),'expires_at_utc':stamp(start+ttl),'checks':[],'groups':[],'subjects':subjects,
  'effect_summary':{},'findings':[],
  'remaining_obligations':['source-to-live-configuration-equivalence','task-role-authority-and-network-proof','per-task-no-effect-preflight',
   'independent-effect-and-cleanup-proof','durable-operation-control','explicit-operation-approval','all-seventeen-release-gates']}
 def check(name,fn):
  try:fn()
  except Exception:
   result['checks'].append({'id':name,'verdict':'blocked'});raise ReadinessFailure('readiness-inspection-blocked') from None
  result['checks'].append({'id':name,'verdict':'observed'})
 def stack_revisions():
  payload=read(['cloudformation','describe-stacks','--stack-name',policy['service_stack']])
  stacks=payload.get('Stacks') if type(payload) is dict else None
  if type(stacks) is not list or len(stacks)!=1 or stacks[0].get('StackStatus')!='UPDATE_COMPLETE':fail('readiness-task-revisions-invalid')
  stack=stacks[0]
  if stack.get('StackName')!=policy['service_stack'] or type(stack.get('StackId')) is not str or not re.fullmatch(r'arn:aws:cloudformation:'+re.escape(policy['region'])+':'+re.escape(policy['account_id'])+r':stack/'+re.escape(policy['service_stack'])+r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',stack['StackId']):fail('readiness-task-revisions-invalid')
  rows=stack.get('Outputs');outputs={}
  if type(rows) is not list:fail('readiness-task-revisions-invalid')
  for row in rows:
   if type(row) is not dict or type(row.get('OutputKey')) is not str or row['OutputKey'] in outputs:fail('readiness-task-revisions-invalid')
   outputs[row['OutputKey']]=row.get('OutputValue')
  values={}
  for logical in grouped:
   value=outputs.get(logical+'Arn')
   if type(value) is not str or not re.fullmatch(r'arn:aws:ecs:'+re.escape(policy['region'])+':'+re.escape(policy['account_id'])+r':task-definition/[A-Za-z0-9_-]+:[1-9][0-9]*',value):fail('readiness-task-revisions-invalid')
   values[logical]=value
  if len(set(values.values()))!=9:fail('readiness-task-revisions-invalid')
  return values
 try:
  checks=[('aws-account',lambda:rec.check_identity(args,policy))]
  for name,state in [('artifact','CREATE_COMPLETE'),('foundation','UPDATE_COMPLETE'),('service','UPDATE_COMPLETE')]:
   stack=policy[name+'_stack'];checks.extend([(name+'-stack-status',lambda s=stack,v=state,n=name:rec.check_stack_status(args,policy,s,v,n+'-stack-status')),
    (name+'-passive-drift',lambda s=stack,n=name:rec.check_stack_drift_evidence(args,policy,s,n+'-stack-drift'))])
  checks.extend(rec.artifact_bucket_checks(args,policy));checks.append(('platform-shell-budget',lambda:rec.check_budget(args,policy)))
  for name,fn in checks:check(name,fn)
  refs=stack_revisions();server_ref,network=candidate.active_server(cpolicy)
  if server_ref!=refs['TaskDefinition'] or relational.service_counts(relational.WORKER_SERVICE,rpolicy)!=(0,0):fail('readiness-target-baseline-invalid')
  definitions={}
  for logical,rows in grouped.items():
   definition=candidate.task_definition(refs[logical],cpolicy,'readiness-task-inspection-unavailable')
   family,revision=refs[logical].split('/')[-1].rsplit(':',1)
   if (definition.get('taskDefinitionArn')!=refs[logical] or definition.get('status')!='ACTIVE' or definition.get('family')!=family
    or type(definition.get('revision')) is not int or definition['revision']!=int(revision)
    or definition.get('networkMode')!='awsvpc' or definition.get('requiresCompatibilities')!=['FARGATE']):fail('readiness-task-revisions-invalid')
   containers=definition.get('containerDefinitions')
   if type(containers) is not list or any(type(c) is not dict for c in containers):fail('readiness-task-shape-invalid')
   names=[c.get('name') for c in containers]
   if len(names)!=len(set(names)) or set(names)!={name for _,name,_ in rows}:fail('readiness-task-shape-invalid')
   if any(type(definition.get(k)) is not str or not re.fullmatch(r'arn:aws:iam::'+re.escape(policy['account_id'])+r':role/[A-Za-z0-9_+=,.@/-]+',definition[k]) for k in ('taskRoleArn','executionRoleArn')):fail('readiness-task-shape-invalid')
   definitions[logical]=definition
   group_digest=rows[0][2]['execution_group_digest'];revision_digest=digest(refs[logical])
   result['groups'].append({'group_digest':group_digest,'task_revision_digest':revision_digest,'task_configuration_digest':digest(definition)})
   for op,name,projection in rows:
    container=next(c for c in containers if c['name']==name);image=container.get('image')
    match=re.fullmatch(r'.+@(sha256:[0-9a-f]{64})',image) if type(image) is str else None
    if not match:fail('readiness-image-not-immutable')
    expected=next(a['digest'] for a in compiled['definition']['artifact_digests'] if a['artifact_id']==op['artifact_id'])
    row=next(x for x in subjects if x['operation_id']==op['operation_id'])
    if 'command' in container and container['command']!=source_rows[op['source_profile']]['command']:fail('readiness-command-drift')
    row.update(task_revision_digest=revision_digest,configured_image_digest=match[1],image_matches_declared_release=match[1]==expected,
     explicit_command_matches_source=container['command']==source_rows[op['source_profile']]['command'] if 'command' in container else None,
     identity_digest=digest({k:definition[k] for k in ('taskRoleArn','executionRoleArn')}),configuration_digest=digest(container),observation='observed')
  candidate.verify_candidate_shape(definitions['CandidatePreflightTaskDefinition'],definitions['TaskDefinition'],cpolicy)
  if refs!=stack_revisions() or (server_ref,network)!=candidate.active_server(cpolicy):fail('readiness-target-changed')
  result['checks'].append({'id':'task-group-and-candidate-observation','verdict':'observed'})
  if any(row['image_matches_declared_release'] is False for row in subjects):fail('readiness-image-mismatch')
  result['verdict']='observed'
 except Exception as error:
  code='readiness-passive-drift-stale' if stale_drift else ('readiness-image-mismatch' if getattr(error,'code',None)=='readiness-image-mismatch' else 'readiness-inspection-blocked')
  result['findings']=[{'code':code}]
  if result['checks'] and result['checks'][-1]['id']=='task-group-and-candidate-observation':result['checks'][-1]['verdict']='blocked'
  elif not result['checks'] or result['checks'][-1]['verdict']!='blocked':result['checks'].append({'id':'task-group-and-candidate-observation','verdict':'blocked'})
 if impl!=implementation() or bp.compile_blueprint(root,blueprint,source_revision,image_digest,release_id)!=compiled:fail('readiness-source-changed')
 if clock()>=start+ttl or monotonic()>deadline:fail('readiness-inspection-timeout')
 if result['verdict']=='observed' and clock()>=evidence_expiry:fail('readiness-evidence-expired')
 result['expires_at_utc']=stamp(evidence_expiry if result['verdict']=='observed' else start+ttl)
 result['effect_summary']={'provider_effects_requested':0,'secret_values_requested':0,'observed_task_groups':len(result['groups']),'observed_subjects':sum(x['observation']=='observed' for x in subjects)}
 result['result_digest']=digest(result)
 return validate_result(result)


def validate_current_result(result,root,blueprint,source_revision,image_digest,release_id):
 validate_result(result)
 compiled=bp.compile_blueprint(root,blueprint,source_revision,image_digest,release_id)
 if (result['blueprint_result_digest']!=compiled['result_digest'] or result['release_digest']!=compiled['compiled_release']['release_digest']
  or result['source_bindings']!=compiled['source_bindings']
  or {(x['operation_id'],x['group_digest']) for x in result['subjects']}!={(x['operation_id'],x['execution_group_digest']) for x in compiled['operation_projection']}):fail('readiness-result-invalid')
 rec=load_module('reconciliation_validation',ROOT/LEGACY['reconciliation'])
 policy=rec.resolve_policy(rec.load_yaml(Path(root)/bp.PROFILE))
 if result['target_binding_digest']!=digest({k:policy[k] for k in ('account_id','region','aws_profile','foundation_stack','service_stack','artifact_stack')}):fail('readiness-result-invalid')
 if not {x['group_digest'] for x in result['groups']}<={x['execution_group_digest'] for x in compiled['operation_projection']}:fail('readiness-result-invalid')
 artifacts={x['artifact_id']:x['digest'] for x in compiled['definition']['artifact_digests']}
 operations={x['operation_id']:x for x in blueprint['operations']}
 for row in result['subjects']:
  if row['observation']=='observed' and (row['image_matches_declared_release']!=(row['configured_image_digest']==artifacts[operations[row['operation_id']]['artifact_id']]) or row['explicit_command_matches_source'] is False):fail('readiness-result-invalid')
 if any(x['image_matches_declared_release'] is False for x in result['subjects']) and (result['verdict']!='blocked' or {'code':'readiness-image-mismatch'} not in result['findings']):fail('readiness-result-invalid')
 return result
