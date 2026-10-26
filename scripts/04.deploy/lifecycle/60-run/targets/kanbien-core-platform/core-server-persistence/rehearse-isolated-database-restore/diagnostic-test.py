#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.persistence-connection-diagnostic
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: persistence.diagnostics
#   disciplines: [security, sre]
#   kind: script
#   effects: [read-only, writes-files]
#   purpose: Exercise bounded diagnostic controller execution, retained evidence, log reconciliation and recovery separation with disposable provider fixtures.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.test.kanbien-core-platform.isolated-persistence-restore
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/smoke-test.sh
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[7]
SID='kanbien-core-platform-persistence-recovery-20261024-d1'
RID='kanbien-core-platform-persistence-restore-20261024-d1'
CANARY='password=synthetic-canary postgres://user:canary@private.invalid secret-token'
FAILURE='KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED'
IMAGE='sha256:'+'a'*64

def load(path, name='test_controller'):
 spec=importlib.util.spec_from_file_location(name,path); value=importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value

class Logs:
 def __init__(self,responses):self.responses=list(responses);self.calls=[]
 def aws(self,*args):
  self.calls.append(args)
  return self.responses.pop(0) if len(self.responses)>1 else self.responses[0]

def logs(events,**extra):return True,{'events':events,**extra},'ok'
def event(value):return {'message':json.dumps(value)}

class Provider:
 def __init__(self,module):
  self.module=module;self.calls=[];self.tasks=[];self.policy=True;self.foreign_policy=False;self.lost_response=False;self.result={'schema':'deploy/persistence-restore-verifier-result/v2','verdict':'diagnosed','code':module.DIAGNOSTIC_RESULT}
 def aws_in_region(self,region,*args):
  assert region=="us-east-1"
  return self.aws(*args)
 def live_budget(self):return True,"ok"
 def aws(self,*args):
  self.calls.append(args);service,operation=args[:2]
  if operation=='describe-task-definition':
   return True,{'taskDefinition':{'containerDefinitions':[{'name':'persistence-restoration-verifier','command':['artifacts/kanbien-core-server-persistence-restore-verifier.main.js'],'image':'fixture@'+IMAGE,'secrets':[],'environment':[{'name':k,'value':v} for k,v in {'PERSISTENCE_POSTGRES_PORT':'5432','PERSISTENCE_POSTGRES_DATABASE':'kanbienpersistence','PERSISTENCE_POSTGRES_SCHEMA':'platform','PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME':'core_runtime','PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE':'restoration-identity-supplied-at-governed-task-run','PERSISTENCE_POSTGRES_IAM_REGION':'eu-west-1'}.items()]}]}},'ok'
  if operation=='list-tasks':
   state=args[args.index('--desired-status')+1]
   return True,{'taskArns':[t['taskArn'] for t in self.tasks if (t['lastStatus']=='STOPPED')==(state=='STOPPED')]},'ok'
  if operation=='describe-tasks':return True,{'tasks':self.tasks,'failures':[]},'ok'
  if operation=='get-role-policy':
   if not self.policy:return False,None,'aws-resource-missing'
   return True,{'PolicyDocument':{'Version':'2012-10-17','Statement':[{'Effect':'Allow','Action':'rds-db:connect','Resource':self.module.restore_identity_resource(self.restored) if not self.foreign_policy else 'fixture-foreign-resource'}]}},'ok'
  if operation=='put-role-policy':self.policy=True;return True,{},'ok'
  if operation=='delete-role-policy':self.policy=False;return True,{},'ok'
  if operation=='lookup-events':return True,{'Events':[{'EventTime':'2020-01-01T00:00:00Z','CloudTrailEvent':json.dumps({'requestParameters':{'roleName':'fixture-role','policyName':'kanbien-core-platform-restoration-verifier-current-instance'}})}]},'ok'
  if operation=='run-task':
   identity=args[args.index('--started-by')+1];overrides=json.loads(args[args.index('--overrides')+1])
   self.tasks=[{'taskArn':'fixture/task-1','startedBy':identity,'taskDefinitionArn':'fixture-definition:1','lastStatus':'RUNNING','createdAt':datetime.now(timezone.utc).isoformat(),'startedAt':'2026-10-26T02:00:00Z','stoppedAt':'2026-10-26T02:00:01Z','overrides':overrides,'containers':[{'exitCode':0,'imageDigest':IMAGE}]}]
   return (False,None,'aws-command-timeout') if self.lost_response else (True,{},'ok')
  if operation=='stop-task':return True,{},'ok'
  if operation=='get-log-events':return logs([event(self.result)])
  if operation=='filter-log-events':return logs([{'message':'PAM authentication failed '+CANARY}])
  if operation=='delete-db-instance':return True,{},'ok'
  raise AssertionError((service,operation))

class DiagnosticTests(unittest.TestCase):
 def setUp(self):
  self.m=load(HERE/'script.py');self.directory=tempfile.TemporaryDirectory();self.m.OPERATION_DIAGNOSTICS=Path(self.directory.name)/'diagnostics';self.m.ROOT=Path(self.directory.name)
 def tearDown(self):self.directory.cleanup()
 def capture(self,function,*args,**kwargs):
  out=io.StringIO()
  with contextlib.redirect_stdout(out):status=function(*args,**kwargs)
  value=json.loads(out.getvalue());self.assertNotIn(CANARY,json.dumps(value));return status,value
 def test_task_discovery_is_bounded_and_refuses_partial_pages(self):
  provider=Logs([(True,{'taskArns':['fixture/task-'+str(n) for n in range(101)]},'ok')])
  tasks,code=self.m.verifier_tasks(provider,'fixture-operation','fixture-definition:1')
  self.assertIsNone(tasks);self.assertEqual(code,'persistence-restoration-verifier-observation-uncertain')
  self.assertIn('--no-paginate',provider.calls[0]);self.assertEqual(provider.calls[0][provider.calls[0].index('--max-results')+1],'100')
 def test_log_states_and_delayed_reads(self):
  for response,state in [(logs([]),'empty'),(logs([{'message':'{'}]),'malformed'),(logs([event({'verdict':'accepted','code':'OTHER_CODE'})]),'unrecognized'),((False,None,'aws-resource-missing'),'unavailable'),((False,None,'aws-access-denied'),'failed'),(logs([event({'verdict':'accepted','code':self.m.RESTORE_ACCEPTED_RESULT})],nextForwardToken='new'),'incomplete')]:
   provider=Logs([response]);value=self.m.observe_terminal_result(provider,'fixture/task-1');self.assertEqual(value['status'],state);self.assertLessEqual(len(provider.calls),3)
  provider=Logs([logs([]),logs([event({'verdict':'rejected','code':FAILURE})])]);value=self.m.observe_terminal_result(provider,'fixture/task-1')
  self.assertEqual((value['status'],value['result']),('rejected',FAILURE));self.assertEqual(len(provider.calls),2)
  self.assertTrue(all(call[:2]==('logs','get-log-events') for call in provider.calls))
 def test_rejection_survives_mixed_and_truncated_logs(self):
  rejection=event({'verdict':'rejected','code':FAILURE})
  for responses,expected in [([logs([rejection,{'message':'malformed '+CANARY}])],'malformed'),([logs([rejection],nextForwardToken='more'),(False,None,'aws-command-timeout')],'failed'),([logs([rejection],nextForwardToken='changing')],'incomplete'),([logs([rejection]*100)],'incomplete')]:
   result=self.m.observe_terminal_result(Logs(responses),'fixture/task-1');self.assertEqual(result['status'],expected);self.assertEqual(result['result'],FAILURE)
 def test_safe_current_and_legacy_envelopes(self):
  execution={'phase':'pool_connect','elapsed_ms':12,'code_status':'unrecognized','classification':'unknown'}
  for value in [{'verdict':'rejected','code':FAILURE},{'schema':'deploy/persistence-restore-verifier-result/v2','verdict':'rejected','code':FAILURE,'execution':execution}]:
   result=self.m.observe_terminal_result(Logs([logs([event(value)])]),'fixture/task-1');self.assertEqual(result['result'],FAILURE)
  for field in ['message','stack','host','password','sql','values','certificate','connection_string']:
   value={'schema':'deploy/persistence-restore-verifier-result/v2','verdict':'rejected','code':FAILURE,'execution':{**execution,field:CANARY}}
   self.assertEqual(self.m.observe_terminal_result(Logs([logs([event(value)])]),'fixture/task-1')['status'],'malformed')
 def test_server_collection_and_preserved_failure(self):
  task={'startedAt':'2026-10-26T02:00:00Z','stoppedAt':'2026-10-26T02:00:01Z','containers':[{'exitCode':7,'imageDigest':IMAGE}]}
  for response,state in [(logs([]),'empty'),(logs([{'message':CANARY}]),'unrecognized'),(logs([None]),'malformed'),(logs([{'message':CANARY}]*100),'incomplete'),(logs([{'message':'PAM authentication failed '+CANARY}],nextToken='more'),'incomplete'),((False,None,'aws-access-denied'),'failed')]:
   observation=self.m.collect_server_logs(Logs([response]),RID,task);self.assertEqual(observation['observation'],state)
  provider=Logs([logs([{'message':'PAM authentication failed '+CANARY}])])
  self.assertEqual(self.m.retain_verifier_rejection(provider,'kanbien-restore-fixture',FAILURE,RID,task),())
  report=json.loads(next(self.m.OPERATION_DIAGNOSTICS.glob('kanbien-restore-fixture-*.json')).read_text())
  self.assertEqual(report['original_failure'],{'code':FAILURE,'exit_status':7});self.assertEqual(report['facts']['artifact_identity'],IMAGE);self.assertNotIn(CANARY,json.dumps(report))
  before={p.name:p.read_bytes() for p in self.m.OPERATION_DIAGNOSTICS.iterdir()}
  self.m.retain_verifier_rejection(Logs([logs([])]),'kanbien-restore-fixture',FAILURE,RID,task)
  self.assertTrue(all((self.m.OPERATION_DIAGNOSTICS/name).read_bytes()==content for name,content in before.items()),'reconciliation must preserve historical diagnostics')
  self.m.OPERATION_DIAGNOSTICS=Path(self.directory.name)/'file';self.m.OPERATION_DIAGNOSTICS.write_text('owned fixture')
  self.assertEqual(self.m.retain_verifier_rejection(provider,'kanbien-restore-fixture',FAILURE,RID,task),('persistence-diagnostic-report-write-failed',))
 def target(self):
  src={'DBInstanceIdentifier':self.m.DATABASE,'DbiResourceId':'db-SOURCE','InstanceCreateTime':'2020-01-01T00:00:00Z','DBSubnetGroup':{'DBSubnetGroupName':'fixture-subnets'}}
  point={'DBSnapshotIdentifier':SID,'DBInstanceIdentifier':self.m.DATABASE,'DbiResourceId':'db-SOURCE','SnapshotCreateTime':'2026-10-24T00:00:00Z'}
  proof={'task':{'started_at':'2026-10-23T00:00:00Z','stopped_at':'2026-10-23T00:00:01Z'},'integrity':{'payload_sha256':'b'*64}}
  tags,_=self.m.recovery_point_binding(src,point,SID,RID,proof)[0]
  restored={**src,'DBInstanceIdentifier':RID,'DbiResourceId':'db-RESTORED','DBInstanceStatus':'available','PubliclyAccessible':False,'StorageEncrypted':True,'IAMDatabaseAuthenticationEnabled':True,'Engine':'postgres','VpcSecurityGroups':[{'VpcSecurityGroupId':'sg-restored'}],'EnabledCloudwatchLogsExports':['postgresql'],'Endpoint':{'Address':'fixture.invalid'},'TagList':[{'Key':k,'Value':v} for k,v in tags.items()]}
  controls={'CoreServerPersistenceRestorationVerifierTaskDefinitionArn':'fixture-definition:1','PersistenceRestoredDatabaseSecurityGroupId':'sg-restored','PersistenceRestorationVerifierTaskRoleName':'fixture-role','PrivateSubnetIds':'subnet-fixture','PersistenceRestorationVerifierSecurityGroupId':'sg-verifier'}
  provider=Provider(self.m);provider.restored=restored
  stack=contextlib.ExitStack();stack.enter_context(patch.object(self.m,'source',return_value=(src,'ok')));stack.enter_context(patch.object(self.m,'controls',return_value=(controls,'ok')));stack.enter_context(patch.object(self.m,'db',return_value=(restored,'ok')));stack.enter_context(patch.object(self.m,'snapshot',return_value=(point,'ok')));stack.enter_context(patch.object(self.m,'read_record_proof',return_value=(proof,'ok')))
  return provider,stack
 def run_diagnostic(self,provider,**kwargs):return self.capture(self.m.diagnose_connection,provider,SID,RID,record_proof_path=Path('fixture-proof.json'),**kwargs)
 def test_repeated_interrupted_and_retention_lost(self):
  provider,stack=self.target()
  with stack:
   provider.lost_response=True
   _,result=self.run_diagnostic(provider);self.assertEqual(result['verdict'],'uncertain')
   _,result=self.run_diagnostic(provider);self.assertEqual(result['verdict'],'pending')
   self.assertEqual(sum(call[1]=='run-task' for call in provider.calls),1)
   provider.tasks=[]
   _,result=self.run_diagnostic(provider);self.assertEqual(result['findings'][0]['code'],'persistence-connection-diagnostic-reserved-reconcile-only')
   self.assertEqual(sum(call[1]=='run-task' for call in provider.calls),1)
 def test_uncertain_launch_blocks_cleanup_and_policy_ownership(self):
  provider,stack=self.target()
  with stack:
   provider.lost_response=True;self.run_diagnostic(provider);provider.tasks=[]
   _,result=self.capture(self.m.cleanup,provider,SID,RID)
   self.assertEqual(result['verdict'],'uncertain');self.assertFalse(any(call[1] in {'delete-role-policy','delete-db-instance'} for call in provider.calls))
  provider,stack=self.target()
  with stack:
   self.m.OPERATION_DIAGNOSTICS=Path(self.directory.name)/'foreign-policy-case'
   self.run_diagnostic(provider);provider.tasks[0]['lastStatus']='STOPPED';provider.foreign_policy=True
   _,result=self.run_diagnostic(provider)
   self.assertIn('persistence-restoration-temporary-identity-policy-mismatch',[finding['code'] for finding in result['findings']]);self.assertFalse(any(call[1]=='delete-role-policy' for call in provider.calls))
 def test_absent_database_still_requires_tasks_policy_and_reservation_resolution(self):
  provider,stack=self.target()
  with stack:
   self.run_diagnostic(provider)
   with patch.object(self.m,'db',return_value=(None,'aws-resource-missing')):
    _,result=self.capture(self.m.cleanup,provider,SID,RID)
    self.assertEqual(result['verdict'],'pending')
    provider.tasks[0]['lastStatus']='STOPPED';provider.foreign_policy=True
    _,result=self.capture(self.m.cleanup,provider,SID,RID)
    self.assertEqual(result['verdict'],'blocked')
    self.assertFalse(any(call[1]=='delete-role-policy' for call in provider.calls))
    provider.policy=False
    _,result=self.capture(self.m.cleanup,provider,SID,RID)
    self.assertEqual(result['verdict'],'cleaned-up',result)
    provider.tasks=[]
    _,result=self.capture(self.m.cleanup,provider,SID,RID)
    self.assertEqual(result['verdict'],'uncertain',result)
    self.assertIn('reservation-binding-unproven',result['findings'][0]['code'])
 def test_diagnostic_cli_declares_dynamic_host_without_recovery_proof(self):
  command=['bash',str(HERE/'script.sh'),'--operation','diagnose-connection','--snapshot-id',SID,'--record-proof-receipt','/tmp/fixture-proof.json','--validate-arguments']
  result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=10)
  report=json.loads(result.stdout);self.assertEqual(result.returncode,0,result.stderr)
  self.assertEqual(report['runtime_input_contract']['names'],['PERSISTENCE_POSTGRES_HOST'])
  self.assertTrue(report['runtime_input_contract']['observation_required']);self.assertIsNone(report['proof_contract'])
 def test_cleanup_requires_exact_final_task_set(self):
  provider,stack=self.target()
  with stack:
   self.run_diagnostic(provider);provider.tasks[0]['lastStatus']='STOPPED'
   original=provider.aws;describes=0
   def altered(*args):
    nonlocal describes
    if args[1]=='describe-tasks':
     describes+=1
     if describes==3:return True,{'tasks':[{**provider.tasks[0],'taskArn':'fixture/foreign-task'}]},'ok'
    return original(*args)
   with patch.object(provider,'aws',side_effect=altered):_,result=self.capture(self.m.cleanup,provider,SID,RID)
   self.assertEqual(result['verdict'],'uncertain');self.assertFalse(any(call[1] in {'delete-role-policy','delete-db-instance'} for call in provider.calls))
 def test_thrown_log_collection_preserves_operation_result(self):
  task={'startedAt':'2026-10-26T02:00:00Z','stoppedAt':'2026-10-26T02:00:01Z','containers':[{'exitCode':9,'imageDigest':IMAGE}]}
  with patch.object(self.m,'collect_server_logs',side_effect=OSError(CANARY)):
   self.assertEqual(self.m.retain_verifier_rejection(None,'kanbien-restore-fixture',FAILURE,RID,task),('persistence-diagnostic-collection-failed',))
  report=json.loads(next(self.m.OPERATION_DIAGNOSTICS.glob('*.json')).read_text());self.assertEqual(report['original_failure'],{'code':FAILURE,'exit_status':9});self.assertNotIn(CANARY,json.dumps(report))
 def test_verify_preserves_original_when_report_write_fails(self):
  provider,stack=self.target()
  with stack:
   self.run_diagnostic(provider)
   task=provider.tasks[0];task['startedBy']=self.m.restore_run_identity(provider.restored);task['lastStatus']='STOPPED';task['containers'][0]['exitCode']=7
   identity=self.m.restore_identity_resource(provider.restored)
   task['overrides']={'containerOverrides':[{'name':'persistence-restoration-verifier','environment':[{'name':key,'value':value} for key,value in {'PERSISTENCE_POSTGRES_HOST':'fixture.invalid','PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE':identity,'PERSISTENCE_ACCEPTANCE_RECORD_ID':self.m.RECORD_ID,'PERSISTENCE_ACCEPTANCE_FACT_DIGEST':self.m.FACT_DIGEST}.items()]}]}
   provider.result={'schema':'deploy/persistence-restore-verifier-result/v2','verdict':'rejected','code':FAILURE}
   self.m.OPERATION_DIAGNOSTICS=Path(self.directory.name)/'file';self.m.OPERATION_DIAGNOSTICS.write_text('fixture')
   status,result=self.capture(self.m.verify,provider,SID,RID)
   self.assertEqual(status,1);self.assertEqual(result['facts']['safe_result_code'],FAILURE)
   self.assertEqual(result['findings'][0]['code'],FAILURE);self.assertIn({'code':'persistence-diagnostic-report-write-failed'},result['findings'])
 def test_concurrent_cli_dispatch_serializes_launch_decisions(self):
  provider,stack=self.target();entered=threading.Event();release=threading.Event();errors=[];emitted=[]
  original=provider.aws
  def blocking(*args):
   if args[1]=='run-task':
    entered.set()
    if not release.wait(3):raise AssertionError('fixture controller barrier timed out')
   return original(*args)
  def launch():
   try:self.m.main(['--operation','diagnose-connection','--snapshot-id',SID,'--record-proof-receipt','fixture-proof.json'])
   except Exception as error:errors.append(type(error).__name__)
  with stack,patch.object(self.m,'load',return_value=provider),patch.object(provider,'aws',side_effect=blocking),patch.object(self.m,'emit',side_effect=lambda verdict,*codes,**kwargs:emitted.extend(codes) or 1),patch.object(self.m,'emit_diagnostic',return_value=1):
   thread=threading.Thread(target=launch);thread.start()
   try:
    self.assertTrue(entered.wait(3));self.m.main(['--operation','verify','--snapshot-id',SID])
    self.assertIn('persistence-restoration-controller-busy',emitted)
   finally:release.set();thread.join(3)
   self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
   self.assertEqual(sum(call[1]=='run-task' for call in provider.calls),1)
 def test_ownership_and_observe_only(self):
  provider,stack=self.target()
  with stack:
   self.run_diagnostic(provider,observe_only=True);self.assertFalse(any(call[1] in {'run-task','put-role-policy','delete-role-policy'} for call in provider.calls))
   provider.restored['TagList']=[]
   _,result=self.run_diagnostic(provider);self.assertEqual(result['verdict'],'blocked',result);self.assertFalse(any(call[1]=='run-task' for call in provider.calls))
 def test_terminal_diagnostic_cleanup_and_recovery_separation(self):
  provider,stack=self.target()
  with stack:
   self.run_diagnostic(provider);provider.tasks[0]['lastStatus']='STOPPED'
   _,result=self.run_diagnostic(provider);self.assertEqual(result['verdict'],'pending');self.assertFalse(provider.policy)
   status,result=self.run_diagnostic(provider);self.assertEqual((status,result['verdict']),(0,'diagnosed'));self.assertFalse(result['acceptance_evidence'])
   self.assertEqual(sum(call[1]=='run-task' for call in provider.calls),1)
   self.assertFalse(any(call[1] in {'restore-db-instance-from-db-snapshot','create-db-instance','modify-db-instance'} for call in provider.calls))
   self.assertFalse(list(self.m.OPERATION_DIAGNOSTICS.glob('*receipt*')))
   collector=load(ROOT/'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py','collector')
   self.assertFalse(collector.safe_result(event(provider.result),self.m.RESTORE_ACCEPTED_RESULT))
   self.assertFalse(collector.safe_result(event({**provider.result,'code':self.m.RESTORE_ACCEPTED_RESULT}),self.m.RESTORE_ACCEPTED_RESULT))
   self.assertFalse(collector.safe_result(event({'verdict':'accepted','code':self.m.RESTORE_ACCEPTED_RESULT,'diagnostic':True}),self.m.RESTORE_ACCEPTED_RESULT))
   receipts=self.m.proof_receipts()
   with self.assertRaises(Exception):receipts.make(proof_type='diagnostic',operation='diagnose-connection',task=provider.tasks[0],image_digest=IMAGE,result_code=self.m.RESTORE_ACCEPTED_RESULT,context={},controller='rehearse-isolated-database-restore',collected_at='2026-10-26T02:01:00Z')
 def test_deadline_and_failure_to_reserve(self):
  provider,stack=self.target()
  with stack:
   self.m.OPERATION_DIAGNOSTICS=Path(self.directory.name)/'file';self.m.OPERATION_DIAGNOSTICS.write_text('fixture')
   _,result=self.run_diagnostic(provider);self.assertEqual(result['verdict'],'blocked',result);self.assertFalse(any(call[1]=='run-task' for call in provider.calls))
   self.m.OPERATION_DIAGNOSTICS=Path(self.directory.name)/'restored-directory'
   self.run_diagnostic(provider);provider.tasks[0]['createdAt']='2020-01-01T00:00:00Z'
   self.run_diagnostic(provider);self.assertEqual(sum(call[1]=='stop-task' for call in provider.calls),1);self.assertEqual(sum(call[1]=='run-task' for call in provider.calls),1)
 def rejected_task(self,provider):
  self.run_diagnostic(provider)
  operation=self.m.restore_run_identity(provider.restored)
  provider.tasks[0].update(startedBy=operation,lastStatus='STOPPED')
  provider.tasks[0]['containers'][0]['exitCode']=7
  provider.result={'schema':'deploy/persistence-restore-verifier-result/v2','verdict':'rejected','code':'KANBIEN_CORE_PERSISTENCE_RESTORE_IAM_TOKEN_MATERIAL_INVALID','execution':{'phase':'pool_connect','elapsed_ms':5,'code_status':'absent','classification':'authentication_material_invalid'}}
  provider.calls=[]
  return operation
 def test_reobserve_rejected_cli_collects_delayed_logs_without_replaying(self):
  provider,stack=self.target()
  with stack:
   operation=self.rejected_task(provider)
   original=provider.aws;reads=0
   def delayed(*args):
    nonlocal reads
    if args[1]=='get-log-events':
     reads+=1
     if reads==1:return logs([])
    return original(*args)
   with patch.object(self.m,'load',return_value=provider),patch.object(provider,'aws',side_effect=delayed):
    status,report=self.capture(self.m.main,['--operation','diagnose-rejected','--snapshot-id',SID,'--operation-id',operation,'--json'])
   self.assertEqual((status,report['verdict']),(0,'diagnosed'),report)
   self.assertEqual(report['facts']['safe_result_code'],provider.result['code'])
   retained={p:p.read_bytes() for p in self.m.OPERATION_DIAGNOSTICS.glob('*.json')}
   self.m.diagnose_rejected(provider,SID,RID,operation)
   self.assertTrue(all(path.read_bytes()==raw for path,raw in retained.items()))
   self.assertFalse(any(call[1] in {'run-task','put-role-policy','delete-role-policy','restore-db-instance-from-db-snapshot','delete-db-instance'} for call in provider.calls))
   observations=[json.loads(p.read_text()) for p in retained if p.name.startswith(operation)]
   self.assertEqual(observations[0]['original_failure'],{'code':provider.result['code'],'exit_status':7})
   self.assertEqual(observations[0]['execution']['phase'],'pool_connect')
 def test_reobserve_write_failure_keeps_specific_original_result(self):
  provider,stack=self.target()
  with stack:
   operation=self.rejected_task(provider)
   self.m.OPERATION_DIAGNOSTICS=Path(self.directory.name)/'not-directory';self.m.OPERATION_DIAGNOSTICS.write_text('fixture')
   _,report=self.capture(self.m.diagnose_rejected,provider,SID,RID,operation)
   self.assertEqual(report['facts']['safe_result_code'],provider.result['code'])
   self.assertEqual(report['findings'],[{'code':provider.result['code']},{'code':'persistence-diagnostic-report-write-failed'}])
 def test_reobserve_cli_is_proofless_and_requires_exact_operation_identity(self):
  args=['--operation','diagnose-rejected','--snapshot-id',SID,'--operation-id','kanbien-restore-'+'a'*16,'--validate-arguments']
  status,report=self.capture(self.m.main,args)
  self.assertEqual(status,0);self.assertIsNone(report['proof_contract']);self.assertIsNone(report['runtime_input_contract'])
  status,report=self.capture(self.m.main,[*args,'--record-proof-receipt','/tmp/unexpected.json'])
  self.assertEqual(report['verdict'],'blocked')
  status,report=self.capture(self.m.main,[*args[:-2],'unknown','--validate-arguments'])
  self.assertEqual(report['verdict'],'blocked')
 def test_real_cli_argument_contract(self):
  command=['bash',str(HERE/'script.sh'),'--operation','diagnose-connection','--snapshot-id',SID,'--record-proof-receipt','/tmp/fixture-proof.json','--json','--validate-arguments']
  result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stderr);self.assertIsNone(json.loads(result.stdout)['proof_contract'])
  command.remove('--record-proof-receipt');command.remove('/tmp/fixture-proof.json')
  result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=10);self.assertNotEqual(result.returncode,0)

if __name__=='__main__':unittest.main()
