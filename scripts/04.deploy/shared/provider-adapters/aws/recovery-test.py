#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.provisioning-recovery
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove observation-only partial Cognito and budget recovery through disposable provider subprocesses.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.script.provision-platform-shell-negative-authz-client.smoke-test
#     path: scripts/04.deploy/provision-platform-shell-negative-authz-client/smoke-test.sh
#   - id: deploy.script.run-platform-shell-postgresql-relational-smoke.smoke-test
#     path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/smoke-test.sh
#   - id: deploy.test.kanbien-core-platform.provision-target-budget
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/smoke-test.sh
import importlib.util,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
AUTH_FAKE='''#!/usr/bin/env python3
import json,os,pathlib,sys
args=sys.argv[1:];op=args[1];policy=json.loads(os.environ['FIXTURE_POLICY']);scenario=os.environ['FIXTURE_SCENARIO'];calls=pathlib.Path(os.environ['FIXTURE_CALLS'])
with calls.open('a') as out:out.write(op+'\\n')
assert not any(word in op for word in ('create','update','delete','get-secret','describe-user-pool-client')),op
if op=='get-caller-identity':print(json.dumps({'Account':policy['account_id']}));sys.exit(0)
if scenario=='denied':sys.exit(1)
if scenario=='malformed':print('{}');sys.exit(0)
if op=='list-resource-servers':
 server={'Identifier':policy['resource_server_identifier'],'Name':policy['resource_server_name'],'Scopes':[{'ScopeName':scope} for scope in json.loads(os.environ['FIXTURE_SCOPES'])]}
 if scenario=='absent':server=None if os.environ['FIXTURE_MODE']=='negative-authz' else {**server,'Scopes':[{'ScopeName':'smoke.read'}]}
 result={'ResourceServers':[] if server is None else [server]}
elif op=='list-user-pool-clients':result={'UserPoolClients':[{'ClientName':policy['client_name'],'ClientId':'fixture-client'}] if scenario in {'present','deleting','duplicate'} else []}
elif op=='list-secrets':result={'SecretList':[{'Name':policy['secret_name'],**({'DeletedDate':'2026-10-26'} if scenario=='deleting' else {})}] if scenario in {'present','deleting','duplicate'} else []}
else:raise AssertionError(op)
if scenario=='partial-page':result['NextToken']='unobserved'
if scenario=='duplicate' and op=='list-user-pool-clients':result['UserPoolClients']*=2
print(json.dumps(result))
'''
BUDGET_FAKE='''#!/usr/bin/env python3
import json,os,pathlib,sys
args=sys.argv[1:];op=args[1];p=pathlib.Path(os.environ['FIXTURE_STATE']);state=json.loads(p.read_text());state['calls'].append(op)
def result(value):p.write_text(json.dumps(state));print(json.dumps(value));sys.exit(0)
def fail(code):p.write_text(json.dumps(state));print(f'An error occurred ({code}) when calling the Fixture operation: fixture-only',file=sys.stderr);sys.exit(1)
if op=='describe-stacks':result({'Stacks':[{'StackStatus':state.get('stack','UPDATE_COMPLETE'),'Parameters':[{'ParameterKey':'EnableTargetBudget','ParameterValue':'false'},{'ParameterKey':'CostAlertEmail','ParameterValue':'fixture.invalid'}]}]})
if op=='describe-change-set':
 if not state.get('change'):fail('ChangeSetNotFoundException')
 result(state['change'])
if op=='create-change-set':
 name=args[args.index('--change-set-name')+1];assert args[args.index('--client-token')+1]==name
 state['change']={'ChangeSetName':name,'Status':'CREATE_IN_PROGRESS','ExecutionStatus':'UNAVAILABLE','Parameters':[{'ParameterKey':'EnableTargetBudget','ParameterValue':'true'}],'Changes':[{'ResourceChange':{'Action':'Add','LogicalResourceId':'Budget','ResourceType':'AWS::Budgets::Budget'}}]}
 p.write_text(json.dumps(state));print('lost-response');sys.exit(0)
if op=='execute-change-set':
 state['change']['ExecutionStatus']='EXECUTE_COMPLETE';p.write_text(json.dumps(state));print('lost-response');sys.exit(0)
if op=='describe-budget':result({'Budget':{'BudgetName':'kanbien-core-platform-monthly','BudgetType':'COST','TimeUnit':'MONTHLY','BudgetLimit':{'Amount':'100','Unit':'USD'},'CostFilters':{'TagKeyValue':['user:Target$kanbien-core-platform']}}})
raise AssertionError(op)
'''
def load(path):
 spec=importlib.util.spec_from_file_location(path.stem,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def copy(root,relative):
 path=Path(relative);target=root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target);return target

def fixture_root(root):
 for path in ['scripts/04.deploy/shared/provider-adapters/aws/response.py','scripts/04.deploy/shared/provider-adapters/aws/cognito-provisioning.py']:copy(root,path)
 inventory=root/'scripts/04.deploy/inventory-deploy-control/script.py';inventory.parent.mkdir(parents=True);inventory.write_text('print("covered synthetic fixture")\n')

class RecoveryCli(unittest.TestCase):
 def test_cognito_partial_absent_unknown_and_present_never_mutate(self):
  with tempfile.TemporaryDirectory(prefix='cognito-recovery-') as directory:
   root=Path(directory);fixture_root(root)
   profile=copy(root,'infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml')
   aws=root/'aws';aws.write_text(AUTH_FAKE);aws.chmod(0o755)
   for mode in ['negative-authz','persistence-write']:
    relative=f'scripts/04.deploy/provision-platform-shell-{mode}-client/script.py';controller=copy(root,relative);module=load(ROOT/relative);policy=module.resolve_policy(module.load_yaml(profile));scopes=[policy['scope_name']] if mode=='negative-authz' else ['smoke.read','smoke.write']
    for scenario,verdict in [('absent','absent'),('present','present-unqualified'),('partial','partial'),('deleting','partial'),('denied','uncertain'),('malformed','uncertain'),('partial-page','uncertain'),('duplicate','uncertain')]:
     with self.subTest(mode=mode,scenario=scenario):
      calls=root/f'{mode}-{scenario}.log';env={**os.environ,'FIXTURE_POLICY':json.dumps(policy),'FIXTURE_SCOPES':json.dumps(scopes),'FIXTURE_MODE':mode,'FIXTURE_SCENARIO':scenario,'FIXTURE_CALLS':str(calls),'PYTHONDONTWRITEBYTECODE':'1'}
      result=subprocess.run([sys.executable,'-B',str(controller),'--reconcile','--target-profile',str(profile),'--aws-cli',str(aws)],cwd=root,env=env,capture_output=True,text=True,timeout=20)
      report=json.loads(result.stdout);self.assertEqual(report['verdict'],verdict,(result.stdout,result.stderr));self.assertEqual(result.returncode,0 if verdict=='absent' else 1);self.assertFalse(report['mutation_performed'])
      self.assertNotIn('secret-value',calls.read_text())
 def test_relational_provider_filters_and_partial_observations(self):
  fake="""#!/usr/bin/env python3
import json,os,sys
args=sys.argv[1:];scenario=os.environ['FIXTURE_SCENARIO']
assert not ('--started-by' in args and '--desired-status' in args)
if args[1]=='list-tasks':
 print(json.dumps({'taskArns':['expected'],**({'nextToken':'unread'} if scenario=='paginated' else {})}));sys.exit(0)
if args[1]=='describe-tasks':
 print(json.dumps({'tasks':[{'taskArn':'wrong' if scenario=='wrong-identity' else 'expected','startedBy':'reviewed','lastStatus':'STOPPED'}],**({'failures':[{'reason':'DENIED'}]} if scenario=='partial' else {})}));sys.exit(0)
raise AssertionError(args)
"""
  driver="""import importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('controller',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
try:print(json.dumps(m.labelled_tasks('reviewed',sys.argv[2],{'cluster':'fixture','profile':'fixture'})))
except m.RelationalSmokeError as error:print(str(error));sys.exit(1)
"""
  with tempfile.TemporaryDirectory(prefix='relational-provider-filters-') as directory:
   root=Path(directory);subprocess.run(['git','init','-q',str(root)],check=True,capture_output=True);aws=root/'aws';aws.write_text(fake);aws.chmod(0o755)
   for scenario,status,expected in [('valid','RUNNING',0),('valid','STOPPED',0),('paginated','STOPPED',1),('wrong-identity','STOPPED',1),('partial','STOPPED',1)]:
    result=subprocess.run([sys.executable,'-B','-c',driver,str(ROOT/'scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py'),status],cwd=root,env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'FIXTURE_SCENARIO':scenario},text=True,capture_output=True,timeout=10)
    self.assertEqual(result.returncode,expected,(scenario,result.stdout,result.stderr))
    if expected:self.assertIn('observation is incomplete',result.stdout)
 def test_budget_lost_response_resumes_exact_operation(self):
  with tempfile.TemporaryDirectory(prefix='budget-recovery-') as directory:
   root=Path(directory);fixture_root(root)
   relative='scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py';controller=copy(root,relative)
   copy(root,'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/foundation.yml')
   tag=root/'scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.sh';tag.parent.mkdir(parents=True);tag.write_text('exit 0\n')
   aws=root/'aws';aws.write_text(BUDGET_FAKE);aws.chmod(0o755);state=root/'provider.json';state.write_text('{"calls":[]}')
   env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'FIXTURE_STATE':str(state),'KANBIEN_CORE_PLATFORM_COST_ALERT_EMAIL':'fixture@example.invalid','PYTHONDONTWRITEBYTECODE':'1'}
   def run(*args):
    result=subprocess.run([sys.executable,'-B',str(controller),*args,'--json'],cwd=root,env=env,capture_output=True,text=True,timeout=20);return result,json.loads(result.stdout)
   result,report=run('--mode','create');self.assertEqual(report['verdict'],'uncertain');name=report['change_set']
   result,report=run('--mode','create');self.assertEqual(report['verdict'],'pending');self.assertEqual(report['change_set'],name)
   result,report=run('--mode','reconcile','--change-set',name);self.assertEqual(report['verdict'],'pending')
   value=json.loads(state.read_text());value['change']['Status']='CREATE_COMPLETE';value['change']['ExecutionStatus']='AVAILABLE';state.write_text(json.dumps(value))
   result,report=run('--mode','execute','--change-set',name);self.assertEqual(report['verdict'],'uncertain')
   result,report=run('--mode','reconcile','--change-set',name);self.assertEqual(report['verdict'],'executed-and-verified');self.assertEqual(result.returncode,0)
   result,report=run('--mode','execute','--change-set',name);self.assertEqual(report['verdict'],'executed-and-verified')
   calls=json.loads(state.read_text())['calls'];self.assertEqual(calls.count('create-change-set'),1);self.assertEqual(calls.count('execute-change-set'),1)
   value=json.loads(state.read_text());value['stack']='UPDATE_ROLLBACK_COMPLETE';state.write_text(json.dumps(value))
   result,report=run('--mode','reconcile','--change-set',name);self.assertEqual(report['verdict'],'failed')
   value=json.loads(state.read_text());value['change']=None;state.write_text(json.dumps(value))
   result,report=run('--mode','reconcile','--change-set',name);self.assertEqual(report['verdict'],'uncertain')

if __name__=='__main__':unittest.main()
