"""Fixed passive inspectors: exact task groups, safe receipts and refusal boundaries."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.selected-readiness
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove passive selected target inspection binding and authority refusal with local fixtures.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh
from copy import deepcopy
from datetime import datetime,timezone
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
# Draft tests use a source mirror; integration needs no environment override.
SOURCE=Path(os.environ.get('SELECTED_READINESS_TEST_SOURCE_ROOT',str(ROOT)))
sys.path[:0]=[str(ROOT/'scripts/04.deploy/operational-realization-gate'),str(SOURCE/'scripts/04.deploy/operational-realization-gate'),str(SOURCE/'scripts/04.deploy/release-control')]
import selected_blueprint as bp
import release_compiler as release
import selected_readiness_cli as cli
spec=importlib.util.spec_from_file_location('readiness_test_adapter',ROOT/'scripts/04.deploy/release-control/adapters/aws/selected_readiness.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
BLUEPRINT=bp.TARGET+'operational-realization/target-release-blueprint.v1.yml'
REV='a'*40;IMAGE='sha256:'+'b'*64;RID='selected-readiness-fixture'

class ReadinessTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)
  cls.blueprint=release.load_document(SOURCE/BLUEPRINT)
  paths={x['path'] for x in cls.blueprint['source_bindings']}|{cls.blueprint['realization_contract'],cls.blueprint['acceptance_policy'],BLUEPRINT,*mod.LEGACY.values(),bp.PROFILE,
   'scripts/04.deploy/release-control/selected_blueprint.py','scripts/04.deploy/operational-realization-gate/release_compiler.py','scripts/04.deploy/operational-realization-gate/blueprint_cli.py'}
  for rel in paths:
   p=cls.root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SOURCE/rel,p)
  for rel in [mod.ADAPTER,mod.CLI,mod.SCHEMAS+'selected-readiness-result.schema.yml',mod.SCHEMAS+'selected-readiness-error.schema.yml']:
   p=cls.root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,p)
  for row in cls.blueprint['source_bindings']:row['digest']='sha256:'+hashlib.sha256((cls.root/row['path']).read_bytes()).hexdigest()
  cls.compiled=bp.compile_blueprint(cls.root,cls.blueprint,REV,IMAGE,RID)
  cls.source_rows={x['id']:x for x in bp.profiles.discover(cls.root)}
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def setUp(self):
  self.addCleanup(patch.stopall);patch.object(mod,'ROOT',self.root).start()
  self.compile=patch.object(bp,'compile_blueprint',return_value=deepcopy(self.compiled)).start()
  self.calls=[];self.mutate=None;self.stack_reads=0;self.drift_age=0
  self.account='337159794548';self.prefix='arn:aws:ecs:eu-west-1:'+self.account+':task-definition/'
  self.defs={};artifacts={x['artifact_id']:x['digest'] for x in self.compiled['definition']['artifact_digests']}
  for op in self.blueprint['operations']:
   logical=op['source_profile'].split('-')[1];name=op['source_profile'].split('-',2)[2]
   family='kanbien-staging-platform-shell-candidate-preflight' if logical=='CandidatePreflightTaskDefinition' else 'fixture-'+logical
   d=self.defs.setdefault(logical,{'family':family,'taskDefinitionArn':self.prefix+family+':1','status':'ACTIVE','revision':1,'taskRoleArn':'arn:aws:iam::'+self.account+':role/fixture-task','executionRoleArn':'arn:aws:iam::'+self.account+':role/fixture-execution','cpu':'256','memory':'512','networkMode':'awsvpc','requiresCompatibilities':['FARGATE'],'runtimePlatform':{'cpuArchitecture':'X86_64','operatingSystemFamily':'LINUX'},'containerDefinitions':[]})
   c={'name':name,'image':'ghcr.io/kanbien/fixture@'+artifacts[op['artifact_id']]}
   if logical not in {'TaskDefinition','CandidatePreflightTaskDefinition'}:c['command']=self.source_rows[op['source_profile']]['command']
   d['containerDefinitions'].append(c)
 def transport(self,cmd,policy,timeout):
  self.calls.append(cmd);self.assertLessEqual(timeout,30);self.assertIn(tuple(cmd[:2]),mod.ALLOW)
  service,action=cmd[:2]
  if service=='sts':value={'Account':self.account}
  elif service=='cloudformation':
   if '--query' in cmd:
    query=cmd[cmd.index('--query')+1]
    value={'status':'IN_SYNC','checked':datetime.fromtimestamp(time.time()-self.drift_age,timezone.utc).isoformat()} if 'DriftInformation' in query else ('CREATE_COMPLETE' if cmd[3]==policy['artifact_stack'] else 'UPDATE_COMPLETE')
   else:
    self.stack_reads+=1;value={'Stacks':[{'StackStatus':'UPDATE_COMPLETE','StackName':policy['service_stack'],'StackId':'arn:aws:cloudformation:eu-west-1:'+self.account+':stack/'+policy['service_stack']+'/12345678-1234-1234-1234-123456789abc','Outputs':[{'OutputKey':k+'Arn','OutputValue':d['taskDefinitionArn']} for k,d in self.defs.items()]}]}
  elif service=='s3api':
   value={'get-public-access-block':{'BlockPublicAcls':True,'IgnorePublicAcls':True,'BlockPublicPolicy':True,'RestrictPublicBuckets':True},'get-bucket-encryption':'AES256','get-bucket-ownership-controls':'BucketOwnerEnforced','get-bucket-lifecycle-configuration':[{'ID':'expire-reviewed-change-set-templates','Status':'Enabled','Filter':{'Prefix':'change-sets/'},'Expiration':{'Days':30},'AbortIncompleteMultipartUpload':{'DaysAfterInitiation':1}}],'get-bucket-policy-status':False}[action]
  elif service=='budgets':value={'name':policy['budget_name'],'limit':{'Amount':'25','Unit':'USD'},'period':'MONTHLY','type':'COST','filters':{'TagKeyValue':['user:service$platform-shell']}}
  elif action=='describe-task-definition':value={'taskDefinition':deepcopy(next(d for d in self.defs.values() if d['taskDefinitionArn']==cmd[-1]))}
  else:
   name=cmd[-1];worker=name.endswith('-worker');value={'services':[{'serviceName':name,'serviceArn':'arn:aws:ecs:eu-west-1:'+self.account+':service/kanbien-staging/'+name,'clusterArn':'arn:aws:ecs:eu-west-1:'+self.account+':cluster/kanbien-staging','status':'ACTIVE','pendingCount':0,'desiredCount':0 if worker else 1,'runningCount':0 if worker else 1,'taskDefinition':self.defs['TaskDefinition']['taskDefinitionArn'],'networkConfiguration':{'awsvpcConfiguration':{'assignPublicIp':'ENABLED','subnets':['subnet-fixture'],'securityGroups':['sg-fixture']}}}]}
  if self.mutate:value=self.mutate(cmd,value)
  return value
 def inspect(self):return mod.inspect(self.root,self.blueprint,REV,IMAGE,RID,_transport=self.transport)
 def reseal(self,result):result['result_digest']=mod.digest({k:v for k,v in result.items() if k!='result_digest'});return result
 def test_exact_source_graph_and_passive_positive(self):
  r=self.inspect();self.assertEqual(r['verdict'],'observed');self.assertEqual(len(r['groups']),9);self.assertEqual(len(r['subjects']),13)
  self.assertEqual(r['qualification_verdict'],'blocked');self.assertEqual(r['source_equivalence'],'blocked');self.assertFalse(r['authorized']);self.assertEqual(self.compile.call_count,2)
  text=json.dumps(r)
  for secret in ('arn:',self.account,'sg-fixture','subnet-fixture','ghcr.io','SENSITIVE'):self.assertNotIn(secret,text)
  self.assertTrue(all(tuple(c[:2]) in mod.ALLOW for c in self.calls))
 def test_image_difference_is_observed_but_blocks_overall(self):
  self.defs['RelationalMigrationTaskDefinition']['containerDefinitions'][0]['image']='ghcr.io/fixture@sha256:'+'c'*64
  r=self.inspect();self.assertEqual(r['verdict'],'blocked');self.assertEqual(r['findings'],[{'code':'readiness-image-mismatch'}]);self.assertFalse(next(x for x in r['subjects'] if x['operation_id']=='migration')['image_matches_declared_release']);self.assertEqual(r['qualification_verdict'],'blocked')
 def test_wrong_account_blocks_and_redacts(self):
  self.mutate=lambda c,v:{'Account':'SENSITIVE'} if c[0]=='sts' else v
  r=self.inspect();self.assertEqual(r['verdict'],'blocked');self.assertEqual(len(self.calls),1);self.assertNotIn('SENSITIVE',json.dumps(r))
 def test_stale_drift_blocks_without_misleading_timeout(self):
  self.drift_age=21601;r=self.inspect();self.assertEqual(r['verdict'],'blocked');self.assertEqual(r['findings'],[{'code':'readiness-passive-drift-stale'}])
 def test_nearly_expired_drift_shortens_receipt(self):
  self.drift_age=21590;r=self.inspect();self.assertLessEqual(datetime.fromisoformat(r['expires_at_utc'].replace('Z','+00:00')).timestamp()-time.time(),11)
 def test_mutable_task_reference_blocks(self):
  self.defs['RelationalMigrationTaskDefinition']['taskDefinitionArn']=self.prefix+'mutable-family';self.assertEqual(self.inspect()['verdict'],'blocked')
 def test_wrong_stack_identity_blocks(self):
  for field in ('StackName','StackId'):
   def mutation(c,v):
    if c[:2]==['cloudformation','describe-stacks'] and '--query' not in c:v['Stacks'][0][field]='SENSITIVE'
    return v
   self.mutate=mutation;self.assertEqual(self.inspect()['verdict'],'blocked')
 def test_missing_group_blocks(self):
  def mutation(c,v):
   if c[:2]==['cloudformation','describe-stacks'] and '--query' not in c:v['Stacks'][0]['Outputs'].pop()
   return v
  self.mutate=mutation;self.assertEqual(self.inspect()['verdict'],'blocked')
 def test_wrong_container_set_blocks(self):
  self.defs['RelationalMigrationTaskDefinition']['containerDefinitions'].append({'name':'unexpected','image':'SENSITIVE'})
  self.assertEqual(self.inspect()['verdict'],'blocked')
 def test_task_revision_family_network_and_role_mismatch_block(self):
  original=deepcopy(self.defs['RelationalMigrationTaskDefinition'])
  for field,value in (('family','unrelated'),('revision',True),('revision',2),('networkMode','bridge'),('requiresCompatibilities',['EC2']),('taskRoleArn','arn:aws:iam::999999999999:role/wrong')):
   with self.subTest(field=field,value=value):
    self.defs['RelationalMigrationTaskDefinition']=deepcopy(original);self.defs['RelationalMigrationTaskDefinition'][field]=value
    self.assertEqual(self.inspect()['verdict'],'blocked')
 def test_returned_service_identity_and_counts_block(self):
  for field,value in (('serviceName','unrelated'),('clusterArn','unrelated'),('serviceArn','unrelated'),('status','DRAINING'),('pendingCount',1),('runningCount',True),('desiredCount','1')):
   def mutation(c,v):
    if c[:2]==['ecs','describe-services']:v['services'][0][field]=value
    return v
   with self.subTest(field=field,value=value):
    self.mutate=mutation;self.assertEqual(self.inspect()['verdict'],'blocked')
 def test_worker_service_must_match_requested_identity(self):
  def mutation(c,v):
   if c[:2]==['ecs','describe-services'] and c[-1].endswith('-worker'):v['services'][0]['serviceName']='unrelated'
   return v
  self.mutate=mutation;self.assertEqual(self.inspect()['verdict'],'blocked')
 def test_command_drift_blocks(self):
  self.defs['RelationalMigrationTaskDefinition']['containerDefinitions'][0]['command']=['SENSITIVE'];r=self.inspect();self.assertEqual(r['verdict'],'blocked');self.assertNotIn('SENSITIVE',json.dumps(r))
 def test_changed_task_revision_during_inspection_blocks(self):
  def mutation(c,v):
   if c[:2]==['cloudformation','describe-stacks'] and '--query' not in c and self.stack_reads==2:v['Stacks'][0]['Outputs'][0]['OutputValue']+= '2'
   return v
  self.mutate=mutation;self.assertEqual(self.inspect()['verdict'],'blocked')
 def test_provider_error_is_redacted(self):
  self.mutate=lambda c,v:(_ for _ in ()).throw(RuntimeError('SENSITIVE provider error'))
  self.assertNotIn('SENSITIVE',json.dumps(self.inspect()))
 def test_current_source_change_refuses(self):
  changed=deepcopy(self.compiled);changed['result_digest']='sha256:'+'f'*64;self.compile.side_effect=[self.compiled,changed]
  with self.assertRaises(mod.ReadinessFailure):self.inspect()
 def test_whole_deadline_bounds_calls(self):
  with self.assertRaises(mod.ReadinessFailure):mod.inspect(self.root,self.blueprint,REV,IMAGE,RID,_transport=self.transport,_monotonic=iter([0,181,181]).__next__)
 def test_forbidden_provider_operation_not_executed(self):
  with patch.object(mod.subprocess,'Popen') as process:
   with self.assertRaises(mod.ReadinessFailure):mod.bounded_aws(['cloudformation','detect-stack-drift'],{},1)
   process.assert_not_called()
 def test_result_extra_and_authority_mutations_rejected(self):
  good=self.inspect()
  for change in ({'private':'SENSITIVE'},{'authorized':True},{'operation_authorization':'allowed'},{'source_equivalence':'passed'}):
   with self.subTest(change=change):
    r=deepcopy(good);r.update(change)
    with self.assertRaises(Exception):mod.validate_result(self.reseal(r))
 def test_result_current_implementation_expiry_and_checksum_rejected(self):
  good=self.inspect()
  for change in ({'implementation_digest':'sha256:'+'f'*64},{'expires_at_utc':'2000-01-01T00:00:00Z'},{'observed_at_utc':'2099-01-01T00:00:00Z'},{'result_digest':'sha256:'+'0'*64}):
   with self.subTest(change=change):
    r=deepcopy(good);r.update(change)
    if 'result_digest' not in change:self.reseal(r)
    with self.assertRaises(Exception):mod.validate_result(r)
 def test_current_source_and_subject_joins_rejected(self):
  good=self.inspect()
  for key in ('blueprint_result_digest','release_digest','target_binding_digest','subject'):
   r=deepcopy(good)
   if key=='subject':r['subjects'][0]['operation_id']='invented-operation'
   else:r[key]='sha256:'+'f'*64
   with self.assertRaises(Exception):mod.validate_current_result(self.reseal(r),self.root,self.blueprint,REV,IMAGE,RID)
 def test_schema_remote_reference_refuses_without_resolving(self):
  result=self.inspect();path=self.root/mod.SCHEMAS/'selected-readiness-result.schema.yml';before=path.read_bytes()
  try:
   schema=release.load_document(path);schema['properties']['verdict']={'$ref':'https://invalid.example/SENSITIVE'};path.write_text(json.dumps(schema))
   result['implementation_digest']=mod.implementation();self.reseal(result)
   with self.assertRaises(mod.ReadinessFailure):mod.validate_result(result)
  finally:path.write_bytes(before)
 def test_missing_observed_checks_and_null_facts_refuse(self):
  good=self.inspect()
  for key in ('checks','fact','image'):
   result=deepcopy(good)
   if key=='checks':result['checks'].pop()
   elif key=='fact':result['subjects'][0]['identity_digest']=None
   else:result['subjects'][0]['image_matches_declared_release']=False
   with self.assertRaises(Exception):mod.validate_current_result(self.reseal(result),self.root,self.blueprint,REV,IMAGE,RID)
 def subprocess_call(self,program,timeout=2):
  real=mod.subprocess.Popen
  def launch(argv,**kwargs):
   self.assertEqual(argv[0],'aws');self.assertEqual(kwargs['env']['AWS_MAX_ATTEMPTS'],'1')
   return real([sys.executable,'-c',program],**kwargs)
  with patch.object(mod.subprocess,'Popen',side_effect=launch):return mod.bounded_aws(['sts','get-caller-identity'],{'region':'eu-west-1','aws_profile':'kanbien-dev'},timeout)
 def test_bounded_subprocess_parses_fixed_read(self):self.assertEqual(self.subprocess_call('print("{}")'),{})
 def test_bounded_subprocess_rejects_duplicate_json(self):
  with self.assertRaises(mod.ReadinessFailure):self.subprocess_call("print('{\"x\":1,\"x\":2}')")
 def test_bounded_subprocess_caps_output(self):
  with self.assertRaises(mod.ReadinessFailure) as error:self.subprocess_call('print("x"*1100000)')
  self.assertEqual(error.exception.code,'readiness-output-limit')
 def test_bounded_subprocess_timeout_kills_child(self):
  with self.assertRaises(mod.ReadinessFailure) as error:self.subprocess_call('import time; time.sleep(10)',.05)
  self.assertEqual(error.exception.code,'readiness-inspection-timeout')
 def test_bounded_subprocess_redacts_provider_failure(self):
  with self.assertRaises(mod.ReadinessFailure) as error:self.subprocess_call('import sys; print("SENSITIVE",file=sys.stderr); sys.exit(7)')
  self.assertNotIn('SENSITIVE',str(error.exception))
 def args(self):return ['--selected-readiness','--inspect-target','--blueprint',str(self.root/BLUEPRINT),'--source-root',str(self.root),'--source-revision',REV,'--image-digest',IMAGE,'--release-id',RID,'--json']
 def cli(self,args=None):
  stream=io.StringIO()
  with contextlib.redirect_stdout(stream):status=cli.main(self.args() if args is None else args)
  return status,json.loads(stream.getvalue())
 def test_cli_positive_revalidates_current_contract(self):
  r=self.inspect()
  with patch.object(cli,'load_adapter',return_value=mod),patch.object(mod,'inspect',return_value=r):
   status,output=self.cli();self.assertEqual(status,0);self.assertEqual(output,r)
 def test_all_fallback_codes_satisfy_closed_error_contract(self):
  schema=release.load_document(ROOT/mod.SCHEMAS/'selected-readiness-error.schema.yml')
  for code in (*cli.CODES,'SENSITIVE'):
   value=cli.failure(code);mod.Draft202012Validator(schema).validate(value);self.assertNotIn('SENSITIVE',json.dumps(value))
 def test_cli_closed_error_on_dependency_loss(self):
  with patch.object(cli,'load_adapter',side_effect=RuntimeError('SENSITIVE')):
   status,output=self.cli();self.assertEqual(status,1);self.assertNotIn('SENSITIVE',json.dumps(output));self.assertEqual(output['findings'][0]['code'],'readiness-dependency-unavailable')
 def test_cli_rejects_extra_field_before_emission(self):
  r=self.inspect();r['extra']='SENSITIVE';self.reseal(r)
  with patch.object(cli,'load_adapter',return_value=mod),patch.object(mod,'inspect',return_value=r):
   status,out=self.cli();self.assertEqual(status,1);self.assertNotIn('SENSITIVE',json.dumps(out))
 def test_cli_mixed_duplicate_upload_and_missing_selector_refuse(self):
  for args in (self.args()+['--blueprint','SENSITIVE'],self.args()+['--run-task'],self.args()+['--provider-fixture','SENSITIVE'],[a for a in self.args() if a!='--inspect-target'],self.args()+['--aws-cli','SENSITIVE']):
   with self.subTest(args=args),patch.object(cli,'load_adapter') as load:
    status,out=self.cli(args);self.assertEqual(status,1);load.assert_not_called();self.assertNotIn('SENSITIVE',json.dumps(out))

if __name__=='__main__':unittest.main()
