#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.platform-shell-release-control
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines: [security, sre]
#   kind: script
#   purpose: Rehearse shell runtime production and guarded first/successor/rollback operations using actual CLI subprocesses and disposable provider observations.
#   portability: { class: internal, targets: [kanbien/staging] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.script.reconcile-platform-shell-staging.smoke-test
#     path: scripts/04.deploy/reconcile-platform-shell-staging/smoke-test.sh
import importlib.util,json,os,shutil,subprocess,sys,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[3]
BASE=Path('infra/04.deploy/03.product/targets/kanbien/staging')
OWNER=Path('scripts/04.deploy/reconcile-platform-shell-staging')
FAKE=r'''#!/usr/bin/env python3
import json,os,pathlib,sys
args=sys.argv[1:];op=args[1];path=pathlib.Path(os.environ['FIXTURE_STATE']);s=json.loads(path.read_text());scenario=s['scenario'];s['calls'].append(op);path.write_text(json.dumps(s))
def out(value):print(json.dumps(value));sys.exit(0)
def arg(key):return args[args.index(key)+1]
def absent():print('An error occurred (ValidationError) when calling the DescribeStacks operation: Stack with id fixture does not exist',file=sys.stderr);sys.exit(1)
if op=='get-caller-identity':out({'Account':'337159794548'})
if op=='describe-stacks':
 name=arg('--stack-name')
 if name==s['service'] and s.get('first') and not s.get('submitted'):absent()
 value=s['stacks'][name]
 if name==s['service'] and scenario=='current-image-drift':value={**value,'Parameters':[{**item,'ParameterValue':'fixture.invalid/unaccepted@sha256:'+'f'*64} if item['ParameterKey']=='ImageUri' else item for item in value['Parameters']]}
 if name==s['service'] and scenario=='pending-stack':value={**value,'StackStatus':'UPDATE_IN_PROGRESS'}
 if name==s['service'] and scenario=='failed-stack':value={**value,'StackStatus':'UPDATE_ROLLBACK_COMPLETE'}
 if scenario=='stale':value={**value,'DriftInformation':{'StackDriftStatus':'IN_SYNC','LastCheckTimestamp':'2000-01-01T00:00:00Z'}}
 if scenario=='denied':print('An error occurred (AccessDenied) when calling the DescribeStacks operation: denied',file=sys.stderr);sys.exit(1)
 out({'Stacks':[value]})
if op=='get-template':
 value=s['templates'][arg('--stack-name')]
 if scenario=='template-drift':value={**value,'Description':'different source'}
 out({'TemplateBody':value})
if op=='describe-stack-resource':out({'StackResourceDetail':{'LogicalResourceId':arg('--logical-resource-id'),'PhysicalResourceId':s['physical'][arg('--logical-resource-id')]}})
if op=='describe-task-definition':
 value=s['definition']
 if scenario=='configuration':value={**value,'containerDefinitions':[{**value['containerDefinitions'][0],'environment':[]}]}
 if scenario=='extra-command':value={**value,'containerDefinitions':[{**value['containerDefinitions'][0],'command':['wrong']}]}
 out({'taskDefinition':value,'tags':[]})
if op=='get-role':out({'Role':{'Arn':s['role'],'AssumeRolePolicyDocument':s['trust']}})
if op=='list-attached-role-policies':out({'AttachedPolicies':[{'PolicyArn':'unexpected'}] if scenario=='permission' else ([{'PolicyArn':'arn:aws:iam::aws:policy/fixture'}] if s.get('managed_version') else [])})
if op=='get-policy':out({'Policy':{'Arn':'arn:aws:iam::aws:policy/fixture','DefaultVersionId':s['managed_version']}})
if op=='get-policy-version':out({'PolicyVersion':{'VersionId':s['managed_version'],'IsDefaultVersion':True,'Document':{'Version':'2012-10-17','Statement':[{'Effect':'Allow','Action':'fixture:'+s['managed_version'],'Resource':'*'}]}}})
if op=='list-role-policies':out({'PolicyNames':['unexpected'] if scenario=='authority' else []})
if op=='describe-services':out({'services':[{'taskDefinition':'definition','desiredCount':1,'runningCount':1,'pendingCount':1 if scenario=='pending-runtime' else 0,'deployments':[{'rolloutState':'COMPLETED'}],'networkConfiguration':{'awsvpcConfiguration':{'subnets':['safe'],'securityGroups':['group'],'assignPublicIp':'DISABLED'}}}]})
if op=='list-tasks':out({'taskArns':['task'],**({'nextToken':'more'} if scenario=='truncated' else {})})
if op=='describe-tasks':out({'tasks':[{'taskArn':'task','taskDefinitionArn':'definition','lastStatus':'RUNNING','healthStatus':'HEALTHY','containers':[{'image':s['image'],'imageDigest':'sha256:'+'f'*64 if scenario=='digest' else s['digest']}]}]})
if op=='describe-budget':out({'name':s['budget'],'limit':{'Amount':'25','Unit':'USD'},'period':'MONTHLY','type':'COST','filters':{'TagKeyValue':['user:service$platform-shell']}})
if op=='get-role-policy':out(s['reconciliation_policy'])
if op=='get-public-access-block':out({key:True for key in ('BlockPublicAcls','IgnorePublicAcls','BlockPublicPolicy','RestrictPublicBuckets')})
if op=='get-bucket-encryption':out('AES256')
if op=='get-bucket-ownership-controls':out('BucketOwnerEnforced')
if op=='get-bucket-policy-status':out(False)
if op=='get-bucket-lifecycle-configuration':out([{'ID':'expire-reviewed-change-set-templates','Status':'Enabled','Filter':{'Prefix':'change-sets/'},'Expiration':{'Days':30},'AbortIncompleteMultipartUpload':{'DaysAfterInitiation':1}}])
if op=='describe-change-set':
 if scenario=='absent-change':print('An error occurred (ChangeSetNotFound) when calling the DescribeChangeSet operation: missing',file=sys.stderr);sys.exit(1)
 value=s['change']
 if scenario=='extra-resource':value={**value,'Changes':[{'ResourceChange':{'LogicalResourceId':'Unexpected','Action':'Add'}}]}
 if scenario=='wrong-image':value={**value,'Parameters':[{**i,'ParameterValue':'wrong'} if i['ParameterKey']=='ImageUri' else i for i in value['Parameters']]}
 if scenario=='pending-change':value={**value,'Status':'CREATE_IN_PROGRESS'}
 if s.get('submitted'):value={**value,'ExecutionStatus':'EXECUTE_COMPLETE' if scenario in {'complete','pending-stack','failed-stack'} else 'EXECUTE_IN_PROGRESS'}
 out(value)
if op=='execute-change-set':
 s['submitted']=True;path.write_text(json.dumps(s))
 if scenario=='lost-submit':sys.exit(1)
 out({})
raise AssertionError(op)
'''

def loaded(path,name):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class ReleaseControl(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='shell-release-control-');self.root=Path(self.temp.name);r=self.root
  subprocess.run(['git','init','-q',str(r)],check=True,capture_output=True)
  files=[OWNER/'script.py',OWNER/'release_control.py',BASE/'target-profile.yml',BASE/'operational-realization/candidate-execution-preflight.v1.yml',Path('scripts/04.deploy/shared/provider-adapters/aws/response.py'),Path('scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py'),Path('scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py'),Path('scripts/04.deploy/operational-realization-gate/script.py')]
  for p in files:(r/p).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,r/p)
  inventory=r/'scripts/04.deploy/inventory-deploy-control/script.py';inventory.parent.mkdir(parents=True);inventory.write_text('print("covered fixture graph")\n')
  helper=r/'scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py';helper.parent.mkdir(parents=True)
  original=ROOT/'scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py'
  helper.write_text(original.read_text().replace('ROOT = Path(__file__).resolve().parents[3]','ROOT = Path('+repr(str(ROOT))+')'))
  self.evidence=loaded(original,'shell_evidence_fixture');self.owner=loaded(ROOT/OWNER/'script.py','shell_owner_fixture');policy=self.owner.resolve_policy(yaml.safe_load((r/BASE/'target-profile.yml').read_text()))
  profile_path=policy['reconciliation_policy_source'];(r/profile_path).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/profile_path,r/profile_path)
  self.digest='sha256:'+'a'*64;image='fixture.invalid/platform-shell@'+self.digest;role='arn:aws:iam::337159794548:role/fixture-role';trust={'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':'ecs-tasks.amazonaws.com'},'Action':'sts:AssumeRole'}]}
  foundation={'Resources':{'Role':{'Type':'AWS::IAM::Role','Properties':{'RoleName':'fixture-role','AssumeRolePolicyDocument':trust}}},'Outputs':{'RoleArn':{'Value':role,'Export':{'Name':'fixture-role-export'}}}}
  task={'Family':'fixture','Cpu':'512','Memory':'1024','NetworkMode':'awsvpc','ExecutionRoleArn':{'Fn::ImportValue':'fixture-role-export'},'TaskRoleArn':{'Fn::ImportValue':'fixture-role-export'},'ContainerDefinitions':[{'Name':'app','Image':{'Ref':'ImageUri'},'Environment':[{'Name':'REQUIRED_CONFIG','Value':'connected'}]}]}
  network={'AwsvpcConfiguration':{'Subnets':['safe'],'SecurityGroups':['group'],'AssignPublicIp':'DISABLED'}}
  service={'Parameters':{'ImageUri':{'Type':'String'},'CandidateImageUri':{'Type':'String'},'DesiredCount':{'Type':'Number','Default':1},'ClusterArn':{'Type':'String','Default':'cluster'}},'Resources':{'TaskDefinition':{'Type':'AWS::ECS::TaskDefinition','Properties':task},'Service':{'Type':'AWS::ECS::Service','Properties':{'Cluster':{'Ref':'ClusterArn'},'ServiceName':'service','TaskDefinition':{'Ref':'TaskDefinition'},'DesiredCount':{'Ref':'DesiredCount'},'NetworkConfiguration':network}}}}
  for name,value in [('service',service),('foundation',foundation)]:path=r/BASE/f'cloudformation/{name}.yml';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(yaml.safe_dump(value))
  renderer=r/'scripts/04.deploy/render-platform-shell-foundation-template/script.sh';renderer.parent.mkdir(parents=True);renderer.write_text('#!/bin/bash\ncp '+str(r/BASE/'cloudformation/foundation.yml')+' "$2"\n')
  now=datetime.now(timezone.utc).isoformat();past=(datetime.now(timezone.utc)-timedelta(seconds=20)).isoformat();parameters=[{'ParameterKey':k,'ParameterValue':v} for k,v in {'ImageUri':image,'CandidateImageUri':image,'DesiredCount':'1','ClusterArn':'cluster'}.items()]
  self.state={'scenario':'valid','calls':[],'service':policy['service_stack'],'budget':policy['budget_name'],'image':image,'digest':self.digest,'role':role,'trust':trust,'physical':{'TaskDefinition':'definition','Service':'service'},'reconciliation_policy':json.loads((r/profile_path).read_text()),'templates':{policy['foundation_stack']:foundation,policy['service_stack']:service},'stacks':{name:{'StackName':name,'StackStatus':'UPDATE_COMPLETE','Parameters':parameters if name==policy['service_stack'] else [],'Outputs':[{'OutputKey':'RoleArn','OutputValue':role}],'CreationTime':past,'DriftInformation':{'StackDriftStatus':'IN_SYNC','LastCheckTimestamp':now}} for name in (policy['foundation_stack'],policy['service_stack'])},'definition':{'taskDefinitionArn':'definition','status':'ACTIVE','family':'fixture','cpu':'512','memory':'1024','networkMode':'awsvpc','executionRoleArn':role,'taskRoleArn':role,'containerDefinitions':[{'name':'app','image':image,'environment':[{'name':'REQUIRED_CONFIG','value':'connected'}]}]},'change':{'ChangeSetName':'reviewed','ChangeSetId':'arn:fixture/reviewed/identity','ChangeSetType':'CREATE','Status':'CREATE_COMPLETE','ExecutionStatus':'AVAILABLE','Parameters':parameters,'Changes':[{'ResourceChange':{'LogicalResourceId':'TaskDefinition','Action':'Add'}}]}}
  self.state_path=r/'state.json';self.save();fake=r/'aws';fake.write_text(FAKE);fake.chmod(0o755)
  publication={'commit_sha':'b'*40,'workflow_run_id':'123','workflow_path':'.github/workflows/deploy-platform-shell-staging.yml','repository':'fixture/repository'}
  self.manifest={'client':{'id':'kanbien'},'environment':{'id':'staging'},'deployment':{'service_id':'platform-shell'},'source':publication,'github':publication.copy(),'artifacts':{'source_commit_sha':'b'*40,'image':{'image_digest':self.digest,'repository_uri':'fixture.invalid/platform-shell','deploy_uri':image}},'acceptance':{'evidence_root':'release-evidence','current_observation':'current-observation.json','package_custody_receipt':'custody.json'}}
  self.manifest_path=r/'manifest.yml';self.manifest_path.write_text(yaml.safe_dump(self.manifest))
  receipt={'schema':'deploy/package-custody-receipt/v1','target':'kanbien-staging','environment_class':'staging','provider_region_alias':'aws-eu-west-1','candidate_id':'platform-shell','package_contract_id':'kanbien-staging-platform-shell','program_id':'platform-shell','source_revision':'b'*40,'image_digest':self.digest,'release_identity':'fixture','checked_at':now,'receipt_reference':'github-actions-run:123','checks':{key:'passed' for key in ('runnable_program_contract','dependency_boundary','delivery_access_static','delivery_access_live','local_image_smoke','sbom','provenance_attestation','ecr_scan')},'verdict':'qualified'};(r/'custody.json').write_text(json.dumps(receipt))
  compiler=loaded(ROOT/'scripts/04.deploy/operational-realization-gate/script.py','compiler_fixture');contract=yaml.safe_load((r/BASE/'operational-realization/candidate-execution-preflight.v1.yml').read_text());_,known=compiler.ids(contract);stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
  facts={'schema':compiler.FACTS_SCHEMA,'contract_id':contract['id'],'gate_evidence':[{'gate':gate['id'],'check_id':gate['evidence'][0],'timestamp':stamp,'verdict':'passed'} for gate in contract['gates'][:6]],'component_evidence':[{'component_id':key,'component_kind':kind,'check_id':key+'-check','timestamp':stamp,'verdict':'passed'} for key,kind in known.items()],'artifact_bindings':[{'component_id':'candidate-runtime-artifact','immutable_reference':self.digest,'check_id':'artifact-check','timestamp':stamp,'verdict':'passed'}]};bindings=compiler.evidence_bindings(contract,facts)
  for entry in facts['gate_evidence']:entry['input_sha256']=bindings['gates'][entry['gate']]
  for entry in facts['component_evidence']:entry['input_sha256']=bindings['components'][entry['component_id']]
  (r/'facts.yml').write_text(yaml.safe_dump(facts));(r/'summary.yml').write_text(yaml.safe_dump({'schema':compiler.CHANGE_SCHEMA,'contract_id':contract['id'],'check_id':'candidate-change-shape-check','timestamp':stamp,'input_sha256':bindings['gates']['change-set'],'operation_counts':{'create':1,'update':0,'delete':0,'replace':0,'broaden-permission':0}}))
 def tearDown(self):self.temp.cleanup()
 def save(self):self.state_path.write_text(json.dumps(self.state)) if hasattr(self,'state_path') else None
 def command(self,mode='runtime-alignment',*args,expected=0,reason=None):
  result=subprocess.run([sys.executable,'-B',str(self.root/OWNER/'script.py'),'--mode',mode,'--deployment-manifest',str(self.manifest_path),'--rehearsal-root',str(self.root),'--aws-cli',str(self.root/'aws'),*args,'--json'],cwd=self.root,env={**os.environ,'FIXTURE_STATE':str(self.state_path),'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True,timeout=30)
  self.assertEqual(result.returncode,expected,(result.stdout,result.stderr));report=json.loads(result.stdout)
  if reason:self.assertEqual(report.get('reason'),reason,report)
  return report
 def mutation(self,*extra,expected=1,reason=None):return self.command('service-update','--service-change-set','reviewed','--expected-predecessor','none','--realization-facts',str(self.root/'facts.yml'),'--realization-change-summary',str(self.root/'summary.yml'),*extra,expected=expected,reason=reason)
 def test_current_source_task_and_permission_shapes_resolve(self):
  control_module=loaded(ROOT/OWNER/'release_control.py','source_resolver_fixture');control=control_module.Control.__new__(control_module.Control);control.root=ROOT;control.policy=self.owner.resolve_policy(yaml.safe_load((ROOT/BASE/'target-profile.yml').read_text()));control.template_cache=control.sources()
  def observed(name,**_):
   template=control.template_cache[name];parameters=[{'ParameterKey':key,'ParameterValue':str(value.get('Default','fixture-value'))} for key,value in template.get('Parameters',{}).items()]
   outputs=[{'OutputKey':key,'OutputValue':'fixture-'+key} for key in template.get('Outputs',{})]
   return {'Parameters':parameters,'Outputs':outputs}
  control.stack=observed;control.physical=lambda name,logical:'physical-'+logical
  control.aws=lambda *args,**kwargs:{'DBInstances':[{'DBInstanceIdentifier':args[-1],'MasterUserSecret':{'SecretArn':'arn:aws:secretsmanager:eu-west-1:337159794548:secret:fixture'}}]}
  task_count=0;role_count=0
  for name,source in control.template_cache.items():
   for logical,item in source['Resources'].items():
    if item['Type']=='AWS::ECS::TaskDefinition':control.resolve(item['Properties'],name);task_count+=1
    if item['Type']=='AWS::IAM::Role' and logical in {'TaskExecutionRole','TaskRole','WorkerTaskRole','RelayTaskRole','RelationalTaskExecutionRole','RelationalRelayTaskRole','RelationalWorkerTaskRole','RelationalRestoreVerificationTaskRole'}:control.resolve(item['Properties'],name);role_count+=1
  self.assertGreaterEqual(task_count,9);self.assertGreaterEqual(role_count,8)
 def test_runtime_producer_negative_boundaries(self):
  cases={'configuration':'shell-task-configuration-mismatch','extra-command':'shell-task-configuration-addition','permission':'shell-role-managed-policy-mismatch','authority':'shell-role-inline-policy-mismatch','digest':'shell-runtime-digest-mismatch','pending-runtime':'shell-service-not-steady','template-drift':'shell-stack-template-mismatch','stale':'shell-stack-drift-stale','truncated':'shell-service-task-observation-incomplete','denied':'shell-observation-aws-access-denied'}
  for scenario,reason in cases.items():
   with self.subTest(scenario=scenario):self.state['scenario']=scenario;self.save();self.command(expected=1,reason=reason);self.assertFalse((self.root/'current-observation.json').exists())
  self.state['scenario']='valid';self.save();report=self.command();self.assertEqual(report['verdict'],'passed');record=yaml.safe_load(Path(report['candidate_record']).read_text());self.assertEqual(record['evidence_class'],'simulated');self.assertFalse((self.root/'release-evidence/current-accepted-release.yml').exists())
 def test_managed_policy_version_change_invalidates_current_evidence(self):
  foundation=next(name for name in self.state['templates'] if name!=self.state['service']);source=self.state['templates'][foundation];source['Resources']['Role']['Properties']['ManagedPolicyArns']=['arn:aws:iam::aws:policy/fixture'];(self.root/BASE/'cloudformation/foundation.yml').write_text(yaml.safe_dump(source));self.state['managed_version']='v1';self.save()
  first=self.command();self.promote(first,'none');previous=json.loads((self.root/'current-observation.json').read_text())['permission_state_sha256']
  self.assertEqual(self.evidence.validate_ready(self.manifest,root=self.root,evidence_class='simulated'),first['release_id'])
  self.state['managed_version']='v2';self.save();second=self.command();current=json.loads((self.root/'current-observation.json').read_text())['permission_state_sha256'];self.assertNotEqual(previous,current)
  with self.assertRaisesRegex(ValueError,'shell-release-current-permission-identity-changed'):self.evidence.validate_ready(self.manifest,root=self.root,evidence_class='simulated')
  owner=self.evidence.succession(self.root,'simulated');owner.history_record_for_id(self.root/'release-evidence',first['release_id'])
 def test_first_create_lost_response_and_resume(self):
  self.state.update(first=True,scenario='lost-submit');self.save();self.mutation(reason='shell-operation-uncertain');self.mutation(reason='shell-operation-pending')
  self.state=json.loads(self.state_path.read_text());self.assertEqual(self.state['calls'].count('execute-change-set'),1)
  for scenario,reason in [('pending-stack','shell-stack-operation-pending'),('failed-stack','shell-stack-operation-failed'),('complete','shell-operation-runtime-verified')]:
   self.state['scenario']=scenario;self.save();self.command('service-operation-status','--service-change-set','reviewed',expected=0 if scenario=='complete' else 1,reason=reason)
  self.state=json.loads(self.state_path.read_text());self.assertEqual(self.state['calls'].count('execute-change-set'),1)
 def promote(self,report,predecessor):
  owner=self.evidence.succession(self.root,'simulated');path=Path(report['candidate_record']);record,raw=owner.document(path);target,scope,_,identity=owner.candidate_identity(record,self.root/'release-evidence')
  owner.promote(self.root/'release-evidence',target=target,scope=scope,identity=identity,source_path=path,source_digest=owner.sha256_bytes(raw),expected_predecessor=predecessor,legacy=False)
 def facts_digest(self,digest):
  compiler=loaded(ROOT/'scripts/04.deploy/operational-realization-gate/script.py','compiler_update');facts=yaml.safe_load((self.root/'facts.yml').read_text());facts['artifact_bindings'][0]['immutable_reference']=digest;contract=yaml.safe_load((self.root/BASE/'operational-realization/candidate-execution-preflight.v1.yml').read_text());bindings=compiler.evidence_bindings(contract,facts)
  for entry in facts['gate_evidence']:entry['input_sha256']=bindings['gates'][entry['gate']]
  for entry in facts['component_evidence']:entry['input_sha256']=bindings['components'][entry['component_id']]
  (self.root/'facts.yml').write_text(yaml.safe_dump(facts));summary=yaml.safe_load((self.root/'summary.yml').read_text());summary['input_sha256']=bindings['gates']['change-set'];(self.root/'summary.yml').write_text(yaml.safe_dump(summary))
 def test_successor_and_rollback_use_actual_immutable_history(self):
  self.manifest['acceptance']['current_observation']='observation-a.json';self.manifest['acceptance']['package_custody_receipt']='custody-a.json';shutil.copyfile(self.root/'custody.json',self.root/'custody-a.json');self.manifest_path.write_text(yaml.safe_dump(self.manifest))
  first=self.command();self.promote(first,'none');original=json.loads(json.dumps(self.manifest));a=self.root/'manifest-a.yml';a.write_text(yaml.safe_dump(original))
  b_digest='sha256:'+'c'*64;b_image='fixture.invalid/platform-shell@'+b_digest
  self.manifest['artifacts']['image'].update(image_digest=b_digest,deploy_uri=b_image);self.manifest['acceptance'].update(current_observation='observation-b.json',package_custody_receipt='custody-b.json');self.manifest_path.write_text(yaml.safe_dump(self.manifest));receipt=json.loads((self.root/'custody-a.json').read_text());receipt['image_digest']=b_digest;(self.root/'custody-b.json').write_text(json.dumps(receipt));self.facts_digest(b_digest)
  self.state['change'].update(ChangeSetType='UPDATE',Changes=[{'ResourceChange':{'LogicalResourceId':'TaskDefinition','Action':'Modify','Replacement':'True'}}]);self.state['change']['Parameters']=[{**i,'ParameterValue':b_image} if i['ParameterKey']=='ImageUri' else i for i in self.state['change']['Parameters']];self.save()
  args=['--service-change-set','reviewed','--expected-predecessor',first['release_id'],'--current-deployment-manifest',str(a),'--realization-facts',str(self.root/'facts.yml'),'--realization-change-summary',str(self.root/'summary.yml')]
  self.state['scenario']='current-image-drift';self.save()
  self.command('service-update',*args,expected=1,reason='shell-current-image-identity-changed')
  self.assertNotIn('execute-change-set',json.loads(self.state_path.read_text())['calls'])
  self.state=json.loads(self.state_path.read_text());self.state['scenario']='valid';self.save()
  self.command('service-update',*args,expected=1,reason='shell-operation-submitted-reconcile-required')
  self.state=json.loads(self.state_path.read_text());self.state.pop('submitted');self.state.update(image=b_image,digest=b_digest);self.state['definition']['containerDefinitions'][0]['image']=b_image;self.state['stacks'][self.state['service']]['Parameters']=json.loads(json.dumps(self.state['change']['Parameters']));self.save()
  second=self.command();self.promote(second,first['release_id']);b=self.root/'manifest-b.yml';b.write_text(yaml.safe_dump(self.manifest))
  compatibility=self.evidence.write_compatibility_from_history(original,first['release_id'],root=self.root,evidence_class='simulated')
  self.manifest=original;self.manifest_path.write_text(yaml.safe_dump(original));self.facts_digest(self.digest);self.state['change']['Parameters']=[{**i,'ParameterValue':self.state['templates'][self.state['service']]['Parameters']['ImageUri'].get('Default','fixture.invalid/platform-shell@'+self.digest)} if i['ParameterKey']=='ImageUri' else i for i in self.state['change']['Parameters']];self.save()
  args=['--service-change-set','reviewed','--expected-predecessor',second['release_id'],'--current-deployment-manifest',str(b),'--realization-facts',str(self.root/'facts.yml'),'--realization-change-summary',str(self.root/'summary.yml')]
  self.command('service-update',*args,expected=1,reason='shell-retained-image-requires-rollback')
  self.command('service-rollback',*args,'--rollback-compatibility-id','rollback-compatibility-'+'f'*24,expected=1,reason='release-succession-record-unreadable')
  observation=self.root/'observation-b.json';before=observation.read_bytes();nested=self.root/BASE/'iam/changed-policy.json';nested.write_text('{"policy":"changed"}')
  fresh=json.loads(before);fresh['input_files']=self.evidence.source_inputs(self.root);observation.write_text(json.dumps(fresh))
  self.command('service-rollback',*args,'--rollback-compatibility-id',compatibility['rollback_compatibility_id'],expected=1,reason='shell-rollback-inputs-changed')
  nested.unlink();observation.write_bytes(before)
  self.state=json.loads(self.state_path.read_text());self.state['scenario']='current-image-drift';self.save()
  self.command('service-rollback',*args,'--rollback-compatibility-id',compatibility['rollback_compatibility_id'],expected=1,reason='shell-current-image-identity-changed')
  self.assertEqual(json.loads(self.state_path.read_text())['calls'].count('execute-change-set'),1)
  self.state=json.loads(self.state_path.read_text());self.state['scenario']='valid';self.save()
  self.command('service-rollback',*args,'--rollback-compatibility-id',compatibility['rollback_compatibility_id'],expected=1,reason='shell-operation-submitted-reconcile-required')
  self.assertEqual(json.loads(self.state_path.read_text())['calls'].count('execute-change-set'),2)
 def test_first_create_rejects_before_execute(self):
  self.state['first']=True
  for scenario,reason in [('extra-resource','shell-change-set-resource-unknown'),('wrong-image','shell-change-set-image-mismatch'),('permission','shell-role-managed-policy-mismatch'),('absent-change','shell-change-set-absent-no-replay')]:
   self.state['scenario']=scenario;self.save();self.mutation(reason=reason);self.assertNotIn('execute-change-set',json.loads(self.state_path.read_text())['calls'])
  (self.root/'custody.json').unlink();self.state['calls']=[];self.save();self.mutation(reason='shell-release-package-custody-unavailable');self.assertEqual(json.loads(self.state_path.read_text())['calls'],[])

if __name__=='__main__':unittest.main()
