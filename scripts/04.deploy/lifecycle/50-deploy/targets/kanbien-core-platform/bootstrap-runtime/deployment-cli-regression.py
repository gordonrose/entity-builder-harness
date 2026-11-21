#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.bootstrap-deployment-cli
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise deployment CLI prerequisite ordering and uncertain operation reconciliation with disposable subprocess providers.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh
import copy
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[7]
DEPLOY=Path('scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/deploy.py')
TEMPLATE=Path('infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml')
PARSER=Path('scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py')
FAKE=r"""#!/usr/bin/env python3
import json,os,pathlib,sys
args=sys.argv[1:];op=args[1];case=os.environ['FIXTURE_CASE'];log=pathlib.Path(os.environ['FIXTURE_LOG']);root=pathlib.Path(os.environ['FIXTURE_ROOT'])
with log.open('a') as out:out.write(op+'\n')
with (root/'argv.jsonl').open('a') as out:out.write(json.dumps(args)+'\n')
params=json.loads((root/'params.json').read_text());done=(root/'submitted').exists();operation=os.environ['FIXTURE_OPERATION'];name='kanbien-core-platform-'+operation+'-'+'a'*12
selected=[{'ParameterKey':k,'ParameterValue':v} for k,v in params.items()]
current=[{'ParameterKey':k,'ParameterValue':('sha256:'+'b'*64 if k=='ImageDigest' else 'b'*40 if k=='SourceRevision' else v)} for k,v in params.items()]
if done:current=selected.copy()
def parameter(items,key):return next(i for i in items if i['ParameterKey']==key)
if op=='describe-change-set':
 if case=='missing':print('An error occurred (ChangeSetNotFoundException) when calling the DescribeChangeSet operation: synthetic-only',file=sys.stderr);sys.exit(1)
 changes=[{'ResourceChange':{'LogicalResourceId':'BootstrapRuntimeTaskDefinition','ResourceType':'AWS::ECS::TaskDefinition','Action':'Modify','Replacement':'True'}},{'ResourceChange':{'LogicalResourceId':'BootstrapRuntimeService','ResourceType':'AWS::ECS::Service','Action':'Modify','Replacement':'False'}}]
 if case=='removed':changes[0]['ResourceChange']['Action']='Remove'
 if case=='resource-logical-shape':changes[0]['ResourceChange']['LogicalResourceId']=[]
 if case=='wrong-role':parameter(selected,'TaskExecutionRoleArn')['ParameterValue']='unreviewed-role'
 if case in {'use-previous','conflicting-previous','unavailable-previous','ambiguous-previous'}:
  entry=parameter(selected,'TaskExecutionRoleArn');entry.pop('ParameterValue');entry['UsePreviousValue']=True
  if case=='conflicting-previous':entry['ParameterValue']='unreviewed-role'
  if case=='ambiguous-previous':entry['UsePreviousValue']='true'
 if case=='duplicate-param':selected.append(dict(selected[-1]))
 if case=='missing-param':selected=[i for i in selected if i['ParameterKey']!='TaskExecutionRoleArn']
 if case=='unknown-param':selected.append({'ParameterKey':'UndeclaredConfiguration','ParameterValue':'same-unreviewed-value'})
 if case=='parameter-type':parameter(selected,'TaskExecutionRoleArn')['ParameterValue']=[]
 if case=='masked-param':parameter(selected,'TaskExecutionRoleArn')['ParameterValue']='****'
 status='CREATE_IN_PROGRESS' if case=='pending-review' else 'CREATE_COMPLETE'
 execution='EXECUTE_COMPLETE' if done or case in {'complete','failed','pending-stack','wrong-completion'} else 'EXECUTE_IN_PROGRESS' if case=='pending-execution' else 'AVAILABLE'
 value={'ChangeSetName':name,'Status':status,'ExecutionStatus':execution,'Parameters':selected,'Changes':changes}
 if case=='truncated':value['NextToken']='unobserved-resource-changes'
 print(json.dumps(value));sys.exit(0)
if op=='describe-stacks':
 status='UPDATE_IN_PROGRESS' if case=='pending-stack' else 'UPDATE_ROLLBACK_COMPLETE' if case=='failed' else 'UPDATE_COMPLETE'
 if case=='stack-status-shape':status=[]
 if case=='wrong-completion':parameter(current,'ImageDigest')['ParameterValue']='sha256:'+'c'*64
 if case=='complete':current=selected.copy()
 if case=='unavailable-previous':current=[i for i in current if i['ParameterKey']!='TaskExecutionRoleArn']
 if case=='duplicate-current':current.append(dict(current[-1]))
 if case=='unknown-param':current.append({'ParameterKey':'UndeclaredConfiguration','ParameterValue':'same-unreviewed-value'})
 if case=='masked-param':parameter(current,'TaskExecutionRoleArn')['ParameterValue']='****'
 print(json.dumps({'Stacks':[{'StackName':'kanbien-core-platform-bootstrap-runtime','StackStatus':status,'Parameters':current}]}));sys.exit(0)
if op=='get-template':
 if '--change-set-name' not in args:
  if case=='current-template-unavailable':print('An error occurred (AccessDenied) when calling the GetTemplate operation: synthetic-only',file=sys.stderr);sys.exit(1)
  if case=='current-template-missing':print('{}');sys.exit(0)
  value=json.loads((root/'current-template.json').read_text())
  if case=='current-template-invalid':value='Resources: ['
  if case=='current-template-drift':value['Description']='different deployed configuration'
  if case=='current-template-changed-role':value['Resources']['BootstrapRuntimeTaskDefinition']['Properties']['TaskRoleArn']='unreviewed-current-role'
  print(json.dumps({'TemplateBody':value}));sys.exit(0)
 if case=='template-unavailable':print('An error occurred (AccessDenied) when calling the GetTemplate operation: synthetic-only',file=sys.stderr);sys.exit(1)
 if case=='template-invalid-json':print('{');sys.exit(0)
 if case=='template-missing':print('{}');sys.exit(0)
 if case=='source-drift':(root/os.environ['FIXTURE_TEMPLATE']).write_text('Changed after qualification')
 print(json.dumps({'TemplateBody':json.loads((root/'proposal.json').read_text())}));sys.exit(0)
if op=='execute-change-set':
 if case=='lost-submit':print('synthetic timeout',file=sys.stderr);sys.exit(1)
 (root/'submitted').write_text('submitted');print('{}');sys.exit(0)
raise AssertionError(op)
"""


def loaded(path):
    spec=importlib.util.spec_from_file_location('fixture_template',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class DeploymentCli(unittest.TestCase):
    def test_reconciliation_native_shapes_keep_named_operation_and_call_order(self):
        module=loaded(ROOT/DEPLOY);receipt={'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40};name='retained-operation'
        params=[{'ParameterKey':'ImageDigest','ParameterValue':receipt['image_digest']},{'ParameterKey':'SourceRevision','ParameterValue':receipt['source_revision']}]
        for field,value,code in [('Status',[],'runtime-change-set-status-unobservable'),('Parameters',[{'ParameterKey':[],'ParameterValue':'private-native-canary'}],'runtime-change-set-parameters-unobservable'),('ExecutionStatus',{},'runtime-change-set-execution-status-unobservable')]:
            out=io.StringIO();change={'ChangeSetName':name,'Status':'CREATE_COMPLETE','ExecutionStatus':'EXECUTE_COMPLETE','Parameters':params,field:value}
            with patch.object(module,'aws',return_value=(True,change,'ok')) as provider,contextlib.redirect_stdout(out):status=module.reconcile(name,receipt)
            report=json.loads(out.getvalue());self.assertEqual(status,1);self.assertEqual(report['verdict'],'uncertain');self.assertEqual(report['findings'],[{'code':code}]);self.assertEqual(provider.call_count,1);self.assertNotIn('private-native-canary',out.getvalue())
        out=io.StringIO()
        with patch.object(module,'aws',side_effect=[(True,{'ChangeSetName':name,'Status':'CREATE_COMPLETE','ExecutionStatus':'EXECUTE_COMPLETE','Parameters':params},'ok'),(True,{'Stacks':[{'StackStatus':[]}]},'ok')]) as provider,contextlib.redirect_stdout(out):
            self.assertEqual(module.reconcile(name,receipt),1)
        self.assertEqual(json.loads(out.getvalue())['findings'],[{'code':'runtime-stack-status-unobservable'}]);self.assertEqual(provider.call_count,2)
        class ChangingStatus(dict):
            reads=0
            def get(self,key,*args):
                if key=='Status':
                    self.reads+=1;return 'CREATE_COMPLETE' if self.reads==1 else []
                return super().get(key,*args)
        changing=ChangingStatus(ChangeSetName=name)
        out=io.StringIO()
        with patch.object(module,'aws',return_value=(True,changing,'ok')) as provider,contextlib.redirect_stdout(out):self.assertEqual(module.reconcile(name,receipt),1)
        self.assertEqual(changing.reads,2);self.assertEqual(provider.call_count,1)
        self.assertEqual(json.loads(out.getvalue())['findings'],[{'code':'runtime-change-set-status-unobservable'}])

    def test_parameter_file_failure_before_and_after_create(self):
        module=loaded(ROOT/DEPLOY.parents[1]/'create-change-set/script.py')
        class CleanupFailure(io.StringIO):
            name='fixture-only.json'
            def __exit__(self,*args):super().__exit__(*args);raise OSError('private-native-canary')
        for cleanup in (False,True):
            calls=[]
            def aws(*parts):
                calls.append(parts[1])
                if parts[1]=='describe-stacks':return True,{'Stacks':[{'Outputs':[{'OutputKey':key,'OutputValue':'fixture'} for key in module.REQUIRED]}]},'ok'
                return (False,None,'aws-resource-missing') if parts[1]=='describe-change-set' else (True,{},'ok')
            temporary=patch.object(module.tempfile,'NamedTemporaryFile',return_value=CleanupFailure()) if cleanup else patch.object(module.tempfile,'NamedTemporaryFile',side_effect=OSError('private-native-canary'))
            out=io.StringIO()
            with temporary,patch.object(module,'receipt',return_value=('sha256:'+'a'*64,'a'*40)),patch.object(module,'baseline',return_value=('sha256:'+'b'*64,'b'*40)),patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=0)),patch.object(module,'aws',side_effect=aws),patch.object(sys,'argv',['fixture','--receipt','fixture','--operation','update']),contextlib.redirect_stdout(out):
                self.assertEqual(module.main(),1)
            report=json.loads(out.getvalue());self.assertEqual(report['verdict'],'uncertain' if cleanup else 'blocked');self.assertEqual(calls,['describe-stacks','describe-change-set','create-change-set'] if cleanup else ['describe-stacks','describe-change-set']);self.assertNotIn('private-native-canary',out.getvalue())

    def test_native_boundaries_are_fixed_and_do_not_retry(self):
        module=loaded(ROOT/DEPLOY)
        module._AWS_RESPONSE=SimpleNamespace(inventory_covered=lambda _root:True)
        for error,code in [(OSError('private-native-canary'),'aws-command-unavailable'),(UnicodeDecodeError('utf8',b'\xff',0,1,'private-native-canary'),'aws-response-invalid'),(subprocess.TimeoutExpired(['private-argv-canary'],1),'aws-command-timeout')]:
            with self.subTest(code=code),patch.object(module.subprocess,'run',side_effect=error) as call:
                self.assertEqual(module.aws('cloudformation','execute-change-set'),(False,None,code))
                self.assertEqual(call.call_count,1)
        for response in [SimpleNamespace(returncode=0,stdout='{private-json-canary'),SimpleNamespace(returncode=1,stdout='private-native-canary')]:
            with patch.object(module.subprocess,'run',return_value=response) as call:
                self.assertIsNone(module.candidate(Path('private-path-canary')))
                self.assertEqual(call.call_count,1)
        create=loaded(ROOT/DEPLOY.parents[1]/'create-change-set/script.py')
        for text in ['{private-json-canary','[]','{}']:
            with patch.object(create.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=text)):
                self.assertIsNone(create.receipt(Path('private-path-canary')))

    def test_rejected_cli_choice_never_echoes_input(self):
        for relative,code in [(DEPLOY,'runtime-deployment-arguments-invalid'),(DEPLOY.parents[1]/'create-change-set/script.py','runtime-change-set-arguments-invalid')]:
            result=subprocess.run([sys.executable,'-B',str(ROOT/relative),'--receipt','private-path-canary','--operation','private-argument-canary\nsecond-line'],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,2)
            self.assertEqual(result.stdout,'')
            self.assertEqual(result.stderr,'ERROR: '+code+'\n')

    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='delivery-bootstrap-cli-');self.root=Path(self.temporary.name);root=self.root
        for relative in [DEPLOY,DEPLOY.with_name('script.sh'),PARSER,Path('scripts/04.deploy/shared/provider-adapters/aws/response.py'),TEMPLATE]:
            (root/relative).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,root/relative)
        inventory=root/'scripts/04.deploy/inventory-deploy-control/script.py';inventory.parent.mkdir(parents=True);inventory.write_text('import os,sys\nsys.exit(1 if os.environ["FIXTURE_CASE"]=="inventory-gap" else 0)\n')
        receipt=root/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh';receipt.parent.mkdir(parents=True);receipt.write_text('echo \'{"image_digest":"sha256:'+('a'*64)+'","source_revision":"'+('a'*40)+'"}\'\n')
        for name,path in [('release','50-deploy/targets/kanbien-core-platform/bootstrap-runtime/release-contract'),('alignment','50-deploy/targets/kanbien-core-platform/bootstrap-runtime/prepare-candidate'),('cost','00-target-alignment/targets/kanbien-core-platform/validate-cost-condition')]:
            gate=root/'scripts/04.deploy/lifecycle'/path/'script.sh';gate.parent.mkdir(parents=True);gate.write_text(f'echo {name} >> "$FIXTURE_LOG"\nif [[ "$FIXTURE_CASE" == "{name}-gap" ]]; then exit 1; fi\n')
        executable=root/'aws';executable.write_text(FAKE);executable.chmod(0o755)
        self.parameters={'ClusterArn':'arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-core-platform','PrivateSubnetIds':'subnet-11111111,subnet-22222222','ServiceSecurityGroupId':'sg-11111111','VerifierSecurityGroupId':'sg-22222222','ServiceDiscoveryArn':'arn:aws:servicediscovery:eu-west-1:337159794548:service/srv-11111111','TaskExecutionRoleArn':'arn:aws:iam::337159794548:role/kanbien-core-platform-task-execution','LogGroupName':'/aws/ecs/kanbien-core-platform','ImageRepositoryUri':'337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server','ImageDigest':'sha256:'+'a'*64,'SourceRevision':'a'*40}
        (root/'params.json').write_text(json.dumps(self.parameters));self.source=loaded(ROOT/PARSER).template((ROOT/TEMPLATE).read_text())

    def tearDown(self):self.temporary.cleanup()

    def command(self,case,*,reconcile=False,operation='update',verdict='blocked',code=None,execute=0,proposal=None,wrapper=False,source_override=None):
        root=self.root;log=root/'calls.log'
        for path in [log,root/'argv.jsonl',root/'submitted']:path.unlink(missing_ok=True)
        shutil.copyfile(ROOT/TEMPLATE,root/TEMPLATE)
        if source_override is not None:(root/TEMPLATE).write_text(json.dumps(source_override))
        (root/'current-template.json').write_text(json.dumps(self.source))
        (root/'proposal.json').write_text(json.dumps(self.source if proposal is None else proposal))
        env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'FIXTURE_CASE':case,'FIXTURE_LOG':str(log),'FIXTURE_ROOT':str(root),'FIXTURE_OPERATION':operation,'FIXTURE_TEMPLATE':str(TEMPLATE),'PYTHONDONTWRITEBYTECODE':'1'}
        entry=['bash',str(root/DEPLOY.with_name('script.sh'))] if wrapper else [sys.executable,'-B',str(root/DEPLOY)]
        command=[*entry,'--receipt','synthetic.json','--operation',operation,'--approved-change-set','kanbien-core-platform-'+operation+'-'+('a'*12),'--json']+(['--reconcile'] if reconcile else [])
        result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=10)
        self.assertTrue(result.stdout,(case,result.stderr));report=json.loads(result.stdout)
        self.assertEqual(report['verdict'],verdict,(case,result.stdout,result.stderr))
        if code:self.assertEqual(report['findings'][0]['code'],code,(case,result.stdout))
        self.assertEqual(result.returncode,0 if verdict=='deployed-awaiting-private-verification' else 1,(case,result.stdout,result.stderr))
        calls=log.read_text().splitlines() if log.exists() else []
        self.assertEqual(calls.count('execute-change-set'),execute,(case,calls))
        if reconcile:self.assertFalse(any(item in calls for item in ('release','alignment','cost')))
        if case.endswith('-gap'):self.assertFalse(any(item.startswith('describe-') for item in calls))
        if 'get-template' in calls:
            invocations=[json.loads(line) for line in (root/'argv.jsonl').read_text().splitlines() if json.loads(line)[1]=='get-template']
            self.assertNotIn('--change-set-name',invocations[0])
            for invocation in invocations:
                self.assertEqual(invocation[invocation.index('--template-stage')+1],'Original')
                if '--change-set-name' in invocation:self.assertEqual(invocation[invocation.index('--change-set-name')+1],'kanbien-core-platform-'+operation+'-'+('a'*12))
            if execute:self.assertEqual(len(invocations),2)
        if execute and case!='lost-submit':self.assertLess(calls.index('get-template'),calls.index('execute-change-set'))
        return report,calls

    def test_real_cli_guards_and_reconciliation(self):
        cases=[('release-gap',False,'blocked','release-contract-not-proven'),('alignment-gap',False,'blocked','runtime-update-alignment-not-proven'),('cost-gap',False,'blocked','cost-condition-not-proven'),('inventory-gap',False,'blocked','delivery-inventory-not-covered'),('wrong-role',False,'blocked','change-set-candidate-mismatch'),('removed',False,'blocked','change-set-resource-boundary-violated'),('lost-submit',False,'uncertain','aws-command-failed'),('pending-review',True,'pending','runtime-change-set-review-pending'),('pending-execution',True,'pending','runtime-change-set-execution-pending'),('missing',True,'uncertain','aws-resource-missing'),('failed',True,'failed','runtime-stack-update-failed'),('pending-stack',True,'pending','runtime-stack-update-pending'),('wrong-completion',True,'uncertain','runtime-stack-completion-identity-unproven'),('complete',True,'deployed-awaiting-private-verification','runtime-change-set-executed')]
        for case,reconcile,verdict,code in cases:
            with self.subTest(case=case):self.command(case,reconcile=reconcile,verdict=verdict,code=code,execute=1 if case=='lost-submit' else 0)
        for case,code in [('resource-logical-shape','runtime-resource-observation-invalid'),('stack-status-shape','runtime-change-set-observation-invalid')]:
            with self.subTest(case=case):self.command(case,verdict='uncertain',code=code)

    def test_proposed_configuration_blocks_before_execute(self):
        variants={}
        for case in ['task-role','verifier-task-role','environment','command','network','typed-scalar']:
            proposal=copy.deepcopy(self.source);properties=proposal['Resources']['BootstrapRuntimeTaskDefinition']['Properties']
            if case=='task-role':properties['TaskRoleArn']='arn:aws:iam::337159794548:role/unreviewed-task-role'
            if case=='verifier-task-role':proposal['Resources']['ReleaseVerifierTaskDefinition']['Properties']['TaskRoleArn']='arn:aws:iam::337159794548:role/unreviewed-task-role'
            if case=='environment':properties['ContainerDefinitions'][0]['Environment']=[]
            if case=='command':properties['ContainerDefinitions'][0]['Command']=['unreviewed']
            if case=='network':proposal['Resources']['BootstrapRuntimeService']['Properties']['NetworkConfiguration']['AwsvpcConfiguration']['AssignPublicIp']='ENABLED'
            if case=='typed-scalar':properties['Memory']=512
            variants[case]=proposal
        for case,proposal in variants.items():
            with self.subTest(case=case):self.command(case,proposal=proposal,code='change-set-template-mismatch')
        raw=(ROOT/TEMPLATE).read_text()
        malformed={'malformed':'Resources: [','duplicate-key':raw+'\nResources: {}\n','duplicate-intrinsic':raw.replace('ExecutionRoleArn: !Ref TaskExecutionRoleArn','ExecutionRoleArn: {Ref: hidden-role, Ref: TaskExecutionRoleArn}'),'null':None,'sequence':[]}
        for case,proposal in malformed.items():
            with self.subTest(case=case):
                if case=='null':proposal='null'
                self.command(case,proposal=proposal,code='change-set-template-invalid')
        for case,code in [('template-unavailable','change-set-template-unavailable'),('template-invalid-json','change-set-template-unavailable'),('template-missing','change-set-template-invalid'),('source-drift','runtime-template-source-changed'),('truncated','change-set-resource-boundary-violated')]:
            with self.subTest(case=case):self.command(case,code=code)
        for case in ['duplicate-param','missing-param','unknown-param','parameter-type','masked-param','conflicting-previous','unavailable-previous','ambiguous-previous','duplicate-current']:
            with self.subTest(case=case):self.command(case,code='change-set-candidate-mismatch')
        # The public shell entrypoint reaches the same proposed-template guard.
        self.command('task-role-wrapper',proposal=variants['task-role'],wrapper=True,code='change-set-template-mismatch')

    def test_current_configuration_must_match_qualified_source(self):
        for case,code in [('current-template-unavailable','runtime-template-unavailable'),('current-template-missing','runtime-template-invalid'),('current-template-invalid','runtime-template-invalid'),('current-template-drift','runtime-template-mismatch'),('current-template-changed-role','runtime-template-mismatch')]:
            with self.subTest(case=case):self.command(case,code=code)
        changed=copy.deepcopy(self.source)
        changed['Resources']['BootstrapRuntimeTaskDefinition']['Properties']['ContainerDefinitions'][0]['Environment'].append({'Name':'OPTIONAL_MODE','Value':'changed'})
        self.command('both-source-and-proposal-changed',proposal=changed,source_override=changed,code='runtime-template-mismatch')

    def test_matching_update_and_qualified_restoration(self):
        for operation in ['update','restore']:
            for case,body in [('matching',self.source),('yaml',(ROOT/TEMPLATE).read_text()),('json-text',json.dumps(self.source)),('use-previous',self.source)]:
                with self.subTest(operation=operation,case=case):self.command(case,operation=operation,proposal=body,wrapper=operation=='restore',verdict='deployed-awaiting-private-verification',code='runtime-change-set-executed',execute=1)

    def test_shared_normalizer_preserves_intrinsics_and_rejects_ambiguity(self):
        parser=loaded(ROOT/PARSER)
        self.assertTrue(parser.templates_equal('Value: !GetAtt Resource.Arn',{'Value':{'Fn::GetAtt':['Resource','Arn']}}))
        self.assertFalse(parser.templates_equal({'Value':True},{'Value':1}))
        for raw in ['Value: !Sub {one: a, one: b}','Value: {Ref: hidden, Ref: reviewed}','Value: &cycle [*cycle]','Value: .nan']:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):parser.template(raw)

    def test_shared_normalizer_compiled_and_safe_fallback_agree(self):
        parser=loaded(ROOT/PARSER)
        with patch.dict(parser.yaml.__dict__):
            parser.yaml.__dict__.pop('CSafeLoader',None)
            fallback=loaded(ROOT/PARSER)
        self.assertTrue(issubclass(fallback.Loader,parser.yaml.SafeLoader))
        if hasattr(parser.yaml,'CSafeLoader'):
            self.assertTrue(issubclass(parser.Loader,parser.yaml.CSafeLoader))
        accepted=['Value: !Ref Resource','Value: !GetAtt Resource.Arn','Value: !GetAtt [Resource, Arn]',
                  'Value: !Sub ["${Name}", {Name: example}]','Value: !Join [":", [one, two]]',
                  'Value: {enabled: true, count: 1, nullable: null, names: [one, two]}']
        directory=ROOT/'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation'
        accepted.extend((directory/name).read_text() for name in ('bootstrap-runtime.yml','entity-smoke.yml','entity-smoke-isolated-restore.yml'))
        for raw in accepted:
            with self.subTest(raw=raw[:32]):
                self.assertEqual(json.dumps(parser.template(raw),sort_keys=True),json.dumps(fallback.template(raw),sort_keys=True))
        invalid=['Resources: [','Value: {Ref: hidden, Ref: reviewed}','Value: !Sub {one: a, one: b}',
                 'Value: &cycle [*cycle]','Value: .nan','Value: .inf','Value: 2026-11-08',
                 'Value: {1: hidden}','Value: !!python/object:private-canary {}','[]','null','{}']
        for owner in (parser,fallback):
            self.assertFalse(owner.templates_equal({'Value':True},{'Value':1}))
            for raw in invalid:
                with self.subTest(loader=owner.Loader,raw=raw):
                    with self.assertRaisesRegex(ValueError,'^cloudformation-template-body-invalid$'):owner.template(raw)

if __name__=='__main__':unittest.main()
