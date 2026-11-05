#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.private-verifier-operation-continuation
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual verifier CLI reservation, interruption, concurrent retries and fresh successor proofs against disposable provider processes.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.private-persistence-verifier-isolation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/smoke-test.sh
#   - id: deploy.test.persistence-acceptance-route.impl
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.py
"""Simulated provider-only evidence. No AWS credential or live task is accessed."""
from pathlib import Path
import importlib.util, signal, time, unittest
import contextlib,io,json,os,shutil,subprocess,sys,tempfile,yaml
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[8]
OWNER=Path('scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate')
FAKE=r'''#!/usr/bin/env python3
import fcntl,json,os,pathlib,sys,time
p=pathlib.Path(os.environ['FIXTURE_PROVIDER_STATE']);args=sys.argv[1:];service,op=args[:2]
def value(flag):return args[args.index(flag)+1]
with p.with_suffix('.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 state=json.loads(p.read_text());state.setdefault('calls',[]).append(args)
 definition=state.get('definition','arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:7')
 if op=='describe-stacks':result={'Stacks':[{'Outputs':[{'OutputKey':k,'OutputValue':v} for k,v in {'CoreServerPersistenceVerifierTaskDefinitionArn':definition,'PrivateSubnetIds':'subnet-private','VerifierSecurityGroupId':'sg-verifier'}.items()]}]}
 elif op=='describe-task-definition':result={'taskDefinition':{'taskDefinitionArn':value('--task-definition'),'family':'kanbien-core-platform-persistence-verifier','containerDefinitions':[{'name':'private-persistence-verifier','image':'fixture.invalid/verifier@sha256:'+'a'*64,'environment':[],'secrets':[]}]}}
 elif op=='run-task':
  index=1+len(state.get('tasks',[]));arn='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+f'{index:032x}'
  task={'taskArn':arn,'taskDefinitionArn':value('--task-definition'),'startedBy':value('--started-by'),'lastStatus':'PENDING','containers':[{'name':'private-persistence-verifier','exitCode':state.get('exit_code',0)}],'startedAt':'2026-10-26T12:00:00Z','stoppedAt':state.get('stopped_at','2026-10-26T12:00:01Z'),'overrides':json.loads(value('--overrides'))}
  mode=next(item['value'] for item in task['overrides']['containerOverrides'][0]['environment'] if item['name']=='PERSISTENCE_VERIFIER_MODE')
  reservation=pathlib.Path('.git/private-persistence-verifier')/(mode+'.json')
  state.setdefault('durable_before_submission',[]).append(reservation.exists() and json.loads(reservation.read_text()).get('operation_id')==value('--client-token')==value('--started-by'))
  state.setdefault('tasks',[]).append(task);result={'tasks':[task]}
 elif op=='list-tasks':
  tasks=state.get('tasks',[])
  if state.get('observation')=='missing':tasks=[]
  result={'taskArns':[t['taskArn'] for t in tasks if ('--desired-status' not in args or (value('--desired-status')=='STOPPED')==(state.get('status','PENDING')=='STOPPED'))]}
 elif op=='describe-tasks':
  requested=args[args.index('--tasks')+1:];requested=requested[:next((i for i,v in enumerate(requested) if v.startswith('--')),len(requested))]
  tasks=[] if state.get('observation')=='missing' else [dict(t,lastStatus=state.get('status','PENDING')) for t in state.get('tasks',[]) if t['taskArn'] in requested]
  result={'tasks':tasks,'failures':[]}
 elif op=='get-log-events':
  mode=next(v['value'] for v in state['tasks'][-1]['overrides']['containerOverrides'][0]['environment'] if v['name']=='PERSISTENCE_VERIFIER_MODE')
  code={'create':'KANBIEN_CORE_PERSISTENCE_RECORD_ACCEPTED','read':'KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED','cleanup':'KANBIEN_CORE_PERSISTENCE_RECORD_CLEANED_UP','health-ready':'KANBIEN_CORE_PERSISTENCE_HEALTHY','health-unready':'KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY'}[mode]
  result={'events':[{'message':json.dumps({'verdict':'accepted','code':code})}]}
  if 'failure_log_messages' in state:result={'events':[{'message':message} for message in state['failure_log_messages']]}
 else:raise AssertionError((service,op))
 p.write_text(json.dumps(state))
if op=='run-task' and state.get('submission') in {'pause','hold'}:time.sleep(1 if state['submission']=='pause' else 600)
if op in {'list-tasks','describe-tasks','get-log-events'} and state.get('observation')=='denied':print('An error occurred (AccessDeniedException) when calling the '+{'list-tasks':'ListTasks','describe-tasks':'DescribeTasks','get-log-events':'GetLogEvents'}[op]+' operation: PRIVATE_VERIFIER_LOG_CANARY',file=sys.stderr);sys.exit(254)
if op=='get-log-events' and state.get('logs')=='expired':result={'events':[]}
if op=='get-log-events' and state.get('logs')=='denied':print('An error occurred (AccessDeniedException) when calling the GetLogEvents operation: PRIVATE_VERIFIER_LOG_CANARY',file=sys.stderr);sys.exit(254)
if op=='run-task' and state.get('submission')=='lost':print('lost provider response');sys.exit(0)
print(json.dumps(result))
'''
class Fixture:
 def __init__(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='verifier-operation-cli-');self.root=Path(self.tmp.name)
  subprocess.run(['git','init','--quiet',str(self.root)],check=True)
  for path in [OWNER/'script.py',OWNER/'script.sh',OWNER.parent/'ecs-task-evidence.py',OWNER.parent/'proof-receipts.py',OWNER.parent/'rehearse-runtime-credential-lifecycle/script.py',
               Path('scripts/04.deploy/shared/deployment-operation-diagnostics.py'),Path('scripts/repo/diagnostic-coverage/runtime_contract.py'),
               Path('scripts/04.deploy/shared/provider-adapters/aws/response.py'),
               Path('packages/core/contracts/diagnostics.v1.json'),Path('platform/persistence/contracts/diagnostics.v1.json'),
               Path('platform/security/contracts/diagnostics.v1.json'),Path('platform/observability/contracts/diagnostics.v1.json'),
               Path('infra/04.deploy/03.product/entrypoints/contracts/diagnostics.v1.json'),
               Path('infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-persistence-operation-diagnostics.v1.json')]:
   out=self.root/path;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,out)
  proof=self.root/OWNER.parent/'proof-receipts.py';proof.write_text(proof.read_text().replace('EVIDENCE_CLASS = "live"','EVIDENCE_CLASS = "simulated"'))
  contract=self.root/'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml';contract.parent.mkdir(parents=True)
  contract.write_text(yaml.safe_dump({'health_recovery':{'workloads':[{'id':'private-release-verifier','completion':{'deadline_seconds':1}}]}}))
  binary=self.root/'bin';binary.mkdir();(binary/'aws').write_text(FAKE);(binary/'aws').chmod(0o755)
  self.state=self.root/'provider.json';self.state.write_text(json.dumps({'submission':'lost'}))
  self.env={**os.environ,'PATH':str(binary)+os.pathsep+os.environ['PATH'],'FIXTURE_PROVIDER_STATE':str(self.state),'PYTHONDONTWRITEBYTECODE':'1'}
 def call(self,*args):
  argv=['bash',str(OWNER/'script.sh'),'--mode','create','--json',*args]
  r=subprocess.run(argv,cwd=self.root,env=self.env,capture_output=True,text=True,timeout=20)
  return r,json.loads(r.stdout)
 def close(self):self.tmp.cleanup()
 def data(self):return json.loads(self.state.read_text())
 def update(self,**values):
  state=self.data();state.update(values);self.state.write_text(json.dumps(state))
 def runs(self):return [c for c in self.data().get('calls',[]) if c[:2]==['ecs','run-task']]
 def command(self):return ['bash',str(OWNER/'script.sh'),'--mode','create','--json']
 def state_path(self):return self.root/'.git/private-persistence-verifier/create.json'


class OperationTests(unittest.TestCase):
 def test_aws_native_failures_and_anchored_denial_preserve_one_call(self):
  spec=importlib.util.spec_from_file_location('verifier_native_boundary',ROOT/OWNER/'script.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  expected=['aws','ecs','describe-tasks','--cli-connect-timeout','5','--cli-read-timeout','20','--profile','kanbien-dev','--region','eu-west-1','--output','json']
  faults=[(OSError('PRIVATE_NATIVE_CANARY'),'aws-command-unavailable'),(UnicodeDecodeError('utf8',b'\xff',0,1,'PRIVATE_NATIVE_CANARY'),'aws-response-invalid'),(subprocess.TimeoutExpired(['PRIVATE_NATIVE_CANARY'],30),'aws-command-timeout')]
  results=[(0,'','',(True,{},'ok')),(0,'{"tasks":[]}','',(True,{'tasks':[]},'ok')),(0,'{PRIVATE_NATIVE_CANARY','',(False,None,'aws-response-invalid')),(254,'','An error occurred (AccessDeniedException) when calling the DescribeTasks operation: PRIVATE_NATIVE_CANARY',(False,None,'aws-access-denied')),(254,'','PRIVATE_NATIVE_CANARY accessdenied not authorized',(False,None,'aws-command-failed'))]
  for fault,code in faults:
   with self.subTest(code=code),patch.object(module.subprocess,'run',side_effect=fault) as call:
    output=io.StringIO();errors=io.StringIO()
    with contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors):observed=module.aws('ecs','describe-tasks')
    self.assertEqual(observed,(False,None,code));self.assertEqual(call.call_count,1)
    self.assertEqual(call.call_args.args,(expected,));self.assertEqual(call.call_args.kwargs,{'capture_output':True,'text':True,'timeout':30,'env':{**os.environ,'AWS_PAGER':''}})
    self.assertEqual(output.getvalue()+errors.getvalue(),'');self.assertNotIn('PRIVATE_NATIVE_CANARY',repr(observed))
  for status,stdout,stderr,expected_result in results:
   with self.subTest(expected=expected_result),patch.object(module.subprocess,'run',return_value=subprocess.CompletedProcess([],status,stdout,stderr)) as call:
    output=io.StringIO();errors=io.StringIO()
    with contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors):observed=module.aws('ecs','describe-tasks')
    self.assertEqual(observed,expected_result);self.assertEqual(call.call_count,1)
    self.assertEqual(call.call_args.args,(expected,));self.assertEqual(call.call_args.kwargs,{'capture_output':True,'text':True,'timeout':30,'env':{**os.environ,'AWS_PAGER':''}})
    self.assertEqual(output.getvalue()+errors.getvalue(),'');self.assertNotIn('PRIVATE_NATIVE_CANARY',repr(observed))
 def fixture(self):
  value=Fixture();self.addCleanup(value.close);return value
 def invoke(self,f,*args,verdict=None):
  completed,value=f.call(*args)
  if verdict:self.assertEqual(value['verdict'],verdict,(completed.stdout,completed.stderr))
  self.assertEqual(completed.returncode,0 if value['verdict']=='accepted' else 1)
  return value
 def test_identical_lost_response_retry_reconciles_same_operation(self):
  f=self.fixture();first=self.invoke(f,verdict='uncertain');second=self.invoke(f,verdict='pending')
  self.assertEqual(first['facts']['operation_id'],second['facts']['operation_id']);self.assertEqual(len(f.runs()),1)
  self.assertEqual(f.data()['durable_before_submission'],[True])
 def test_explicit_initial_none_is_idempotent_and_checks_predecessor(self):
  f=self.fixture();f.update(submission='normal',status='STOPPED')
  first=self.invoke(f,'--new-operation','--expected-operation','none',verdict='accepted')
  again=self.invoke(f,'--new-operation','--expected-operation','none',verdict='accepted')
  self.assertEqual(first['facts']['operation_id'],again['facts']['operation_id']);self.assertEqual(len(f.runs()),1)
  self.invoke(f,'--new-operation','--expected-operation',first['facts']['operation_id'],verdict='accepted')
  self.invoke(f,'--new-operation','--expected-operation','none',verdict='blocked');self.assertEqual(len(f.runs()),2)
 def test_initial_none_cannot_replace_pending_uncertain_or_missing_state(self):
  f=self.fixture();first=self.invoke(f,verdict='uncertain')
  same=self.invoke(f,'--new-operation','--expected-operation','none',verdict='pending')
  self.assertEqual(first['facts']['operation_id'],same['facts']['operation_id']);self.assertEqual(len(f.runs()),1)
  f.update(observation='missing');self.invoke(f,'--new-operation','--expected-operation','none',verdict='uncertain');self.assertEqual(len(f.runs()),1)
  f.state_path().unlink();self.invoke(f,'--new-operation','--expected-operation','none',verdict='blocked');self.assertEqual(len(f.runs()),1)
 def test_pending_first_execution_and_repeat_submit_once(self):
  f=self.fixture();f.update(submission='normal',status='PROVISIONING')
  start=time.monotonic();first=self.invoke(f,verdict='pending');self.assertGreaterEqual(time.monotonic()-start,1)
  second=self.invoke(f,verdict='pending');self.assertEqual(first['facts']['operation_id'],second['facts']['operation_id']);self.assertEqual(len(f.runs()),1)
 def test_missing_expired_denied_provider_metadata_never_replays(self):
  for outcome in ('missing','denied'):
   with self.subTest(outcome=outcome):
    f=self.fixture();self.invoke(f,verdict='uncertain');os.utime(f.state_path(),(1,1));f.update(observation=outcome)
    self.invoke(f,verdict='uncertain');self.invoke(f,verdict='uncertain');self.assertEqual(len(f.runs()),1)
 def test_missing_malformed_private_metadata_blocks(self):
  for mutation in ('missing-state','missing-lock','invalid-json','invalid-sentinel','changed-integrity'):
   with self.subTest(mutation=mutation):
    f=self.fixture();self.invoke(f,verdict='uncertain');path=f.state_path();lock=path.with_suffix('.lock')
    if mutation=='missing-state':path.unlink()
    elif mutation=='missing-lock':lock.unlink()
    elif mutation=='invalid-json':path.write_text('{')
    elif mutation=='invalid-sentinel':lock.write_text('expired')
    else:
     value=json.loads(path.read_text());value['operation_id']='kp-'+'f'*32;path.write_text(json.dumps(value))
    self.invoke(f,verdict='blocked');self.assertEqual(len(f.runs()),1)
 def test_request_change_and_new_operation_while_pending_block(self):
  f=self.fixture();first=self.invoke(f,verdict='uncertain');operation=first['facts']['operation_id']
  value=self.invoke(f,'--new-operation','--expected-operation',operation,verdict='blocked')
  self.assertIn('private-persistence-verifier-prior-operation-not-complete',[v['code'] for v in value['findings']])
  f.update(definition='arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:8')
  value=self.invoke(f,verdict='blocked');self.assertIn('private-persistence-verifier-operation-request-changed',[v['code'] for v in value['findings']]);self.assertEqual(len(f.runs()),1)
 def test_concurrent_invocations_submit_once(self):
  f=self.fixture();f.update(submission='pause')
  first=subprocess.Popen(f.command(),cwd=f.root,env=f.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  self.addCleanup(lambda: first.poll() is None and os.killpg(first.pid,signal.SIGKILL))
  limit=time.monotonic()+10
  while not f.runs() and time.monotonic()<limit:time.sleep(.01)
  self.assertTrue(f.runs());second=self.invoke(f,verdict='pending');self.assertEqual(second['findings'][0]['code'],'private-persistence-verifier-operation-busy')
  out,err=first.communicate(timeout=10);self.assertEqual(json.loads(out)['verdict'],'pending',(out,err));self.assertEqual(len(f.runs()),1)
 def test_interruption_before_submission_never_replays_reserved_operation(self):
  f=self.fixture();hook=f.root/'hooks';hook.mkdir();marker=f.root/'before-submit'
  (hook/'sitecustomize.py').write_text("import os, pathlib, subprocess, time\noriginal=subprocess.run\ndef run(args,*a,**kw):\n if isinstance(args,list) and args[:3]==['aws','ecs','run-task']:\n  pathlib.Path(os.environ['BEFORE_SUBMIT']).write_text('reserved');time.sleep(600)\n return original(args,*a,**kw)\nsubprocess.run=run\n")
  process=subprocess.Popen(f.command(),cwd=f.root,env={**f.env,'PYTHONPATH':str(hook),'BEFORE_SUBMIT':str(marker)},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  self.addCleanup(lambda: process.poll() is None and os.killpg(process.pid,signal.SIGKILL))
  limit=time.monotonic()+10
  while not marker.exists() and time.monotonic()<limit:time.sleep(.01)
  self.assertTrue(marker.exists());os.killpg(process.pid,signal.SIGTERM);process.communicate(timeout=5)
  self.assertTrue(f.state_path().exists());self.invoke(f,verdict='uncertain');self.assertEqual(len(f.runs()),0)
 def test_interruption_after_possible_submission_reconciles_same_task(self):
  f=self.fixture();f.update(submission='hold')
  process=subprocess.Popen(f.command(),cwd=f.root,env=f.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  self.addCleanup(lambda: process.poll() is None and os.killpg(process.pid,signal.SIGKILL))
  limit=time.monotonic()+10
  while not f.runs() and time.monotonic()<limit:time.sleep(.01)
  self.assertTrue(f.runs());os.killpg(process.pid,signal.SIGTERM);process.communicate(timeout=5)
  self.invoke(f,verdict='pending');self.assertEqual(len(f.runs()),1)
 def test_terminal_receipt_survives_expiry_and_new_operation_is_idempotent(self):
  f=self.fixture();f.update(submission='normal',status='STOPPED');first=self.invoke(f,verdict='accepted');old=first['facts']['operation_id']
  proof=f.root/first['facts']['proof_receipt'];before=proof.read_bytes();f.update(observation='missing')
  retained=self.invoke(f,verdict='accepted');self.assertEqual(retained['facts']['evidence_reuse'],'historical-completion');self.assertEqual(proof.read_bytes(),before);self.assertEqual(len(f.runs()),1)
  f.update(observation='present');new=self.invoke(f,'--new-operation','--expected-operation',old,verdict='accepted');again=self.invoke(f,'--new-operation','--expected-operation',old,verdict='accepted')
  self.assertNotEqual(old,new['facts']['operation_id']);self.assertEqual(new['facts']['operation_id'],again['facts']['operation_id']);self.assertEqual(len(f.runs()),2)
  self.invoke(f,'--new-operation','--expected-operation','kp-'+'e'*32,verdict='blocked');self.assertEqual(proof.read_bytes(),before)
 def test_known_terminal_failures_allow_only_explicit_successor(self):
  for changes,code in [({'exit_code':3},'private-persistence-verifier-unsuccessful-completion'),({'stopped_at':'2026-10-26T12:00:05Z'},'private-persistence-verifier-completion-deadline-exceeded')]:
   with self.subTest(code=code):
    f=self.fixture();f.update(submission='normal',status='STOPPED',**changes);first=self.invoke(f,verdict='failed');operation=first['facts']['operation_id']
    again=self.invoke(f,verdict='failed');self.assertEqual(again['findings'][0]['code'],code);self.assertEqual(len(f.runs()),1)
    self.invoke(f,'--new-operation','--expected-operation',operation,verdict='failed');self.assertEqual(len(f.runs()),2)
 def test_failed_task_one_bounded_read_retains_source_nine_and_late_frame(self):
  f=self.fixture()
  sources=[{'schema':'core/diagnostic-record/v1','code':'core.persistence.in-memory-boundary-failed','definitionVersion':1,'detail':{'operation':'initialize','phase':'get-id','reason':'boundary-threw','effect':'write-not-reached','ordinal':index}} for index in range(10)]
  own={'schema':'core/diagnostic-record/v1','code':'kanbien-core-server.operations.verification-boundary-failed','definitionVersion':1,'detail':{'task':'verification','operation':'verification','phase':'fetch','condition':'rejected','effect':'unknown'}}
  failure={'schema':'deploy/persistence-task-failure/v1','task':'verification','verdict':'rejected','code':'KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE','diagnostic':sources[0],'related_diagnostics':sources[1:9],'observations':[own]}
  late={**failure,'diagnostic':sources[9]}
  f.update(submission='normal',status='STOPPED',exit_code=3,failure_log_messages=['PRIVATE_VERIFIER_LOG_CANARY',json.dumps(failure),json.dumps(late)])
  completed,value=f.call();self.assertEqual(completed.returncode,1);self.assertEqual(value['verdict'],'failed')
  self.assertEqual(value['findings'][0]['code'],'private-persistence-verifier-unsuccessful-completion')
  observed=value['facts']['task_failure'];self.assertEqual(observed['diagnostic'],sources[0]);self.assertEqual(observed['related_diagnostics'],sources[1:9]);self.assertEqual(observed['observations'],[own,own])
  self.assertEqual(observed['source_bundles'],[{'diagnostic':sources[9],'related_diagnostics':sources[1:9]}]);self.assertEqual(value['facts']['task_log_observation'],'malformed')
  self.assertNotIn('PRIVATE_VERIFIER_LOG_CANARY',completed.stdout+completed.stderr)
  reads=[call for call in f.data()['calls'] if call[:2]==['logs','get-log-events']];self.assertEqual(len(reads),1)
  self.assertEqual(reads[0][reads[0].index('--limit')+1],'100');self.assertEqual(reads[0][reads[0].index('--log-stream-name')+1],'persistence-verifier/private-persistence-verifier/'+f.data()['tasks'][0]['taskArn'].rsplit('/',1)[-1])
  again=self.invoke(f,verdict='failed');self.assertEqual(again['facts']['task_failure'],observed);self.assertEqual(len(f.runs()),1)
  self.assertEqual(len([call for call in f.data()['calls'] if call[:2]==['logs','get-log-events']]),2)
 def test_failed_task_log_denial_does_not_replace_original_failure_or_identity(self):
  f=self.fixture();f.update(submission='normal',status='STOPPED',exit_code=3,logs='denied')
  completed,value=f.call();self.assertEqual(completed.returncode,1);self.assertEqual(value['verdict'],'failed')
  self.assertEqual(value['findings'][0]['code'],'private-persistence-verifier-unsuccessful-completion')
  self.assertEqual(value['facts']['task_log_observation'],'failed');self.assertNotIn('task_failure',value['facts'])
  self.assertEqual(value['facts']['verifier_task'],f.data()['tasks'][0]['taskArn']);self.assertNotIn('PRIVATE_VERIFIER_LOG_CANARY',completed.stdout+completed.stderr)
  self.assertEqual(len([call for call in f.data()['calls'] if call[:2]==['logs','get-log-events']]),1)
 def test_missing_terminal_proof_or_expired_logs_never_authorize_new_operation(self):
  f=self.fixture();f.update(submission='normal',status='STOPPED');first=self.invoke(f,verdict='accepted');(f.root/first['facts']['proof_receipt']).unlink()
  self.invoke(f,verdict='blocked');self.invoke(f,'--new-operation','--expected-operation',first['facts']['operation_id'],verdict='blocked');self.assertEqual(len(f.runs()),1)
  other=self.fixture();other.update(submission='normal',status='STOPPED',logs='expired');value=self.invoke(other,verdict='pending')
  self.invoke(other,'--new-operation','--expected-operation',value['facts']['operation_id'],verdict='blocked');self.assertEqual(len(other.runs()),1)
 def test_explicit_reconciliation_captures_durable_current_completion(self):
  f=self.fixture();first=self.invoke(f,verdict='uncertain');f.update(status='STOPPED')
  accepted=self.invoke(f,'--reconcile-operation',first['facts']['operation_id'],verdict='accepted')
  f.update(observation='missing');retained=self.invoke(f,verdict='accepted');self.assertEqual(accepted['facts']['proof_receipt'],retained['facts']['proof_receipt']);self.assertEqual(len(f.runs()),1)
 def test_old_request_reconciles_after_current_definition_changes_before_successor(self):
  f=self.fixture();first=self.invoke(f,verdict='uncertain');operation=first['facts']['operation_id']
  changed='arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:8'
  f.update(definition=changed,status='STOPPED',submission='normal')
  self.invoke(f,verdict='blocked');self.invoke(f,'--new-operation','--expected-operation',operation,verdict='blocked')
  completed=self.invoke(f,'--reconcile-operation',operation,verdict='accepted');self.assertEqual(len(f.runs()),1)
  proof=json.loads((f.root/completed['facts']['proof_receipt']).read_text());self.assertTrue(proof['task']['definition'].endswith(':7'))
  self.assertEqual(completed['facts']['verifier_task'],proof['task']['arn'])
  successor=self.invoke(f,'--new-operation','--expected-operation',operation,verdict='accepted');self.assertEqual(len(f.runs()),2)
  self.assertNotEqual(operation,successor['facts']['operation_id']);self.assertEqual(f.data()['tasks'][-1]['taskDefinitionArn'],changed)
 def test_runtime_identity_caller_requests_fresh_successor_and_resumes_pending(self):
  f=self.fixture();f.update(submission='normal',status='STOPPED')
  path=f.root/OWNER.parent/'rehearse-runtime-credential-lifecycle/script.py';spec=importlib.util.spec_from_file_location('identity_lifecycle',path);controller=importlib.util.module_from_spec(spec);spec.loader.exec_module(controller)
  old_environment=os.environ.copy()
  try:
   os.environ.update(f.env)
   self.assertTrue(controller.healthy('health-ready'));self.assertTrue(controller.healthy('health-ready'));self.assertEqual(len(f.runs()),2)
   f.update(status='PROVISIONING');self.assertFalse(controller.healthy('health-ready'));self.assertEqual(len(f.runs()),3)
   self.assertIn('operation_id',controller.CHILD_CHECKPOINT['facts'])
   f.update(status='STOPPED');self.assertTrue(controller.healthy('health-ready'));self.assertEqual(len(f.runs()),3)
   f.update(exit_code=3);self.assertFalse(controller.healthy('health-ready'));self.assertEqual(len(f.runs()),4)
   f.update(exit_code=0);self.assertTrue(controller.healthy('health-ready'));self.assertEqual(len(f.runs()),5)
   output=io.StringIO()
   with contextlib.redirect_stdout(output):self.assertEqual(controller.report('accepted','fixture-recovery-proved'),0)
   handoff=json.loads(output.getvalue())['facts']['verifier_operations']['health-ready']
   self.assertEqual(handoff['operation_id'],f.data()['tasks'][-1]['startedBy']);self.assertEqual(handoff['verifier_task'],f.data()['tasks'][-1]['taskArn'])
   next_phase=self.invoke(f,'--mode','health-ready','--new-operation','--expected-operation',handoff['operation_id'],verdict='accepted')
   self.assertNotEqual(next_phase['facts']['operation_id'],handoff['operation_id']);self.assertEqual(len(f.runs()),6)
  finally:
   os.environ.clear();os.environ.update(old_environment)

if __name__=='__main__':unittest.main(verbosity=2)
