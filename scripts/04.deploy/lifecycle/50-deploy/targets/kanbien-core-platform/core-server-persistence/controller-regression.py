#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.persistence-controller-reconciliation
#   version: 6
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove provider controller outcomes and interrupted observation reconciliation with synthetic AWS responses only.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.core-server-persistence-target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/smoke-test.sh
"""Regression fixtures never invoke a provider or a runtime subprocess."""
import contextlib
import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import yaml
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

ROOT = Path(__file__).resolve().parents[7]
DEPLOY = ROOT / 'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence'
RUN = ROOT / 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence'

def load(path):
    spec = importlib.util.spec_from_file_location(path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def result(call):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = call()
    reports = [json.loads(line) for line in out.getvalue().splitlines()]
    return code, reports[-1], reports

@contextlib.contextmanager
def temporary_receipts(controller):
    """Exercise real receipt writes outside every canonical release-evidence path."""
    receipts = load(RUN / 'proof-receipts.py')
    with tempfile.TemporaryDirectory(prefix='persistence-controller-receipts-') as directory:
        root = Path(directory)
        receipts.RECEIPTS = root / 'proof-receipts'
        receipts.EVIDENCE_CLASS = 'simulated'
        with patch.object(controller, 'proof_receipts', return_value=receipts), patch.object(controller, 'ROOT', root):
            yield receipts

class Provider:
    def __init__(self, responder):
        self.calls = []
        self.responder = responder
    def aws(self, *parts):
        self.calls.append(parts)
        if parts[1] == 'list-tasks':
            assert not ('--started-by' in parts and ('--desired-status' in parts or '--family' in parts)), 'unsupported AWS filter combination'
        return self.responder(parts)
    def live_budget(self):
        return True, 'ok'

class ControllerRegression(unittest.TestCase):
    def test_exact_change_set_and_restore_image_parameter(self):
        module = load(DEPLOY / 'deploy-candidate/script.py')
        digest, revision, name = 'sha256:'+'a'*64, 'a'*40, 'candidate-name'
        good = {'ChangeSetName': name, 'Status': 'CREATE_COMPLETE', 'ChangeSetType': 'CREATE', 'Parameters': [{'ParameterKey': key, 'ParameterValue': value} for key, value in [('ImageDigest',digest),('SupportImageDigest',digest),('RestoreVerifierImageDigest',digest),('SourceRevision',revision)]], 'Changes':[{'ResourceChange':{'ResourceType':'AWS::RDS::DBInstance'}}]}
        self.assertTrue(module.reviewable(good, 'REVIEW_IN_PROGRESS', name, digest, revision))
        for bad in [{**good,'ChangeSetName':name+'-other'}, {**good,'Parameters':good['Parameters'][:1]+good['Parameters'][2:]}]:
            self.assertFalse(module.reviewable(bad,'REVIEW_IN_PROGRESS',name,digest,revision))
        wrong = copy.deepcopy(good); wrong['Parameters'][1]['ParameterValue']='sha256:'+'b'*64
        self.assertFalse(module.reviewable(wrong,'REVIEW_IN_PROGRESS',name,digest,revision))
        expected={item['ParameterKey']:item['ParameterValue'] for item in good['Parameters']}
        expected.update({'PrivateSubnetIds':'subnet-safe','EndpointSecurityGroupId':'sg-safe'})
        complete={**good,'Parameters':[{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()]}
        self.assertTrue(module.parameters_match(complete,expected))
        for key in ('PrivateSubnetIds','EndpointSecurityGroupId'):
            wrong=copy.deepcopy(complete)
            next(item for item in wrong['Parameters'] if item['ParameterKey']==key)['ParameterValue']='unrelated'
            self.assertFalse(module.parameters_match(wrong,expected))
        receipt = {'image_digest':digest,'source_revision':revision}
        for status, verdict in [('CREATE_IN_PROGRESS','pending'),('ROLLBACK_FAILED','failed'),('CREATE_COMPLETE','deployed-awaiting-migration')]:
            provider=Provider(lambda parts: (True,{**good,'ExecutionStatus':'EXECUTE_COMPLETE'},'ok') if parts[1]=='describe-change-set' else (True,{'Stacks':[{'StackStatus':status,'Parameters':good['Parameters']}]},'ok'))
            self.assertEqual(result(lambda:module.reconcile(provider,name,receipt))[1]['verdict'],verdict)
            self.assertFalse(any(parts[1]=='execute-change-set' for parts in provider.calls))

    def test_update_submission_timeouts_preserve_operation_identity(self):
        receipt={'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40}
        for name in ('transition-qualified-release','apply-private-verifier-route-update','apply-restoration-verifier-surface'):
            module=load(DEPLOY/name/'script.py')
            def response(parts):
                if parts[1]=='describe-stacks':return True,{'Stacks':[{'StackStatus':'CREATE_COMPLETE','Parameters':[{'ParameterKey': key, 'ParameterValue': value} for key, value in {'ImageDigest': receipt['image_digest'], 'SupportImageDigest': receipt['image_digest'], 'RestoreVerifierImageDigest': receipt['image_digest'], 'SourceRevision': receipt['source_revision']}.items()]}]},'ok'
                if parts[1]=='describe-services':return True,{'services':[{'desiredCount':1,'runningCount':1}]},'ok'
                if parts[1]=='describe-change-set':return False,None,'aws-resource-missing'
                if parts[1]=='create-change-set':return False,None,'aws-command-timeout'
                raise AssertionError(f'unexpected consequential operation: {parts}')
            provider=Provider(response)
            provider.validate_receipt=lambda path:receipt
            provider.declaration_covered=lambda:True
            provider.foundation_outputs=lambda:({'RepositoryUri':'synthetic'},'ok')
            provider.infrastructure_parameters=lambda outputs:({},'ok')
            provider.candidate_image=lambda receipt:(True,'ok')
            provider.candidate_parameters=lambda *args:{'ImageDigest':receipt['image_digest']}
            create=SimpleNamespace(package_gates=lambda path:True)
            args=['test','--receipt','synthetic']
            if name=='transition-qualified-release':args+=['--operation','update']
            loader='module' if name=='apply-private-verifier-route-update' else 'load'
            values=[provider] if name=='apply-restoration-verifier-surface' else [provider,create]
            with patch.object(module,loader,side_effect=values),patch.object(sys,'argv',args):
                report=result(module.main)[1]
            self.assertEqual(report['verdict'],'uncertain')
            self.assertTrue(report['facts']['change_set'].endswith('a'*12))
            self.assertEqual(len([parts for parts in provider.calls if parts[1]=='create-change-set']),1)
            self.assertFalse(any(parts[1]=='execute-change-set' for parts in provider.calls))

    def test_image_transition_retains_unowned_stack_parameters_and_discards_only_rejected_review(self):
        module = load(DEPLOY/'transition-qualified-release/script.py')
        digest, revision = 'sha256:' + 'a' * 64, 'a' * 40
        desired = {'ImageDigest': digest, 'SupportImageDigest': digest, 'RestoreVerifierImageDigest': digest, 'SourceRevision': revision}
        current = {**desired, 'ImageDigest': 'sha256:' + 'c' * 64, 'SupportImageDigest': 'sha256:' + 'c' * 64, 'RestoreVerifierImageDigest': 'sha256:' + 'c' * 64, 'SourceRevision': 'c' * 40, 'EnableObservability': 'true', 'ObservabilityCollectorImage': 'synthetic@sha256:' + 'b' * 64, 'ObservabilityAlertEmail': '****'}
        inputs = module.update_parameter_inputs(current, desired)
        self.assertEqual({item['ParameterKey'] for item in inputs if item.get('UsePreviousValue')}, {'EnableObservability', 'ObservabilityCollectorImage', 'ObservabilityAlertEmail'})
        self.assertTrue(all(item.get('UsePreviousValue') is True for item in inputs if item['ParameterKey'] not in desired))
        self.assertIsNone(module.update_parameter_inputs({'ImageDigest': digest}, desired))

        name = 'kanbien-core-platform-persistence-update-' + digest[7:19]
        rejected = {'ChangeSetName': name, 'Status': 'CREATE_COMPLETE', 'ExecutionStatus': 'AVAILABLE', 'ChangeSetType': 'UPDATE', 'Parameters': [{'ParameterKey': key, 'ParameterValue': value} for key, value in {**desired, 'EnableObservability': 'false'}.items()], 'Changes': [{'ResourceChange': {'ResourceType': 'AWS::CloudWatch::Alarm'}}]}
        calls = {'describes': 0}
        def response(parts):
            if parts[1] == 'describe-change-set':
                calls['describes'] += 1
                return ((True, rejected, 'ok') if calls['describes'] == 1 else (False, None, 'aws-resource-missing'))
            if parts[1] == 'delete-change-set': return True, {}, 'ok'
            raise AssertionError(parts)
        provider = Provider(response)
        report = result(lambda: module.discard_rejected_review(provider, name, current, digest, revision))[1]
        self.assertEqual(report['verdict'], 'discarded')
        self.assertEqual(len([parts for parts in provider.calls if parts[1] == 'delete-change-set']), 1)

        provider = Provider(lambda parts: (False, None, 'aws-resource-missing'))
        self.assertEqual(result(lambda: module.discard_rejected_review(provider, name, current, digest, revision))[1]['verdict'], 'reconciled')
        self.assertFalse(any(parts[1] == 'delete-change-set' for parts in provider.calls))

        executable = {**rejected, 'Changes': [{'ResourceChange': {'ResourceType': 'AWS::ECS::Service'}}]}
        provider = Provider(lambda parts: (True, executable, 'ok') if parts[1] == 'describe-change-set' else (_ for _ in ()).throw(AssertionError('must not delete executable review')))
        self.assertEqual(result(lambda: module.discard_rejected_review(provider, name, current, digest, revision))[1]['verdict'], 'blocked')

    def test_original_create_command_does_not_execute_known_operation_twice(self):
        module=load(DEPLOY/'deploy-candidate/script.py')
        digest='sha256:'+'a'*64;revision='a'*40;name='kanbien-core-platform-persistence-create-'+'a'*12
        receipt={'image_digest':digest,'source_revision':revision}
        expected={'ImageDigest':digest,'SupportImageDigest':digest,'RestoreVerifierImageDigest':digest,'SourceRevision':revision}
        for status in ('EXECUTE_IN_PROGRESS','EXECUTE_COMPLETE'):
            change={'ChangeSetName':name,'Status':'CREATE_COMPLETE','ExecutionStatus':status,'ChangeSetType':'CREATE','Parameters':[{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()],'Changes':[{'ResourceChange':{'ResourceType':'AWS::RDS::DBInstance'}}]}
            def response(parts):
                if parts[1]=='describe-change-set':return True,change,'ok'
                if parts[1]=='describe-stacks':return True,{'Stacks':[{'StackStatus':'REVIEW_IN_PROGRESS'}]},'ok'
                raise AssertionError(f'duplicate execution attempted: {parts}')
            provider=Provider(response)
            provider.validate_receipt=lambda path:receipt;provider.declaration_covered=lambda:True
            provider.foundation_outputs=lambda:({},'ok');provider.infrastructure_parameters=lambda outputs:({},'ok')
            provider.candidate_image=lambda receipt:(True,'ok');provider.candidate_parameters=lambda *args:expected
            with patch.object(module,'controls',return_value=provider),patch.object(sys,'argv',['test','--receipt','synthetic','--approved-change-set',name]):
                self.assertEqual(result(module.main)[1]['verdict'],'pending')
            self.assertFalse(any(parts[1]=='execute-change-set' for parts in provider.calls))

    def test_retirement_requires_complete_exact_service_quiescence(self):
        module=load(DEPLOY/'retire-failed-candidate/script.py')
        safe={'serviceName':module.SERVICE,'serviceArn':f'arn:aws:ecs:{module.REGION}:337159794548:service/{module.CLUSTER}/{module.SERVICE}','desiredCount':0,'runningCount':0,'pendingCount':0}
        malformed=[{}, {**safe,'serviceName':'unrelated'}, {key:value for key,value in safe.items() if key!='pendingCount'}, {**safe,'runningCount':False}, {**safe,'runningCount':-1}]
        for service in malformed:
            with patch.object(module,'aws',return_value=(True,{'services':[service]},'ok')):
                self.assertFalse(module.no_active_service()[0])
        with patch.object(module,'aws',return_value=(True,{'services':[safe]},'ok')):
            self.assertTrue(module.no_active_service()[0])

    def test_replacement_receipt_matches_actual_image_and_source_before_stop(self):
        module=load(RUN/'rehearse-server-replacement/script.py')
        digest='sha256:'+'a'*64;child='sha256:'+'b'*64
        receipt={'image_digest':digest,'source_revision':'a'*40}
        image=f'337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server@{digest}'
        definition={'taskDefinitionArn':'definition-safe','containerDefinitions':[{'name':'core-server-persistence','image':image,'environment':[{'name':'PLATFORM_SOURCE_COMMIT_SHA','value':receipt['source_revision']}]}]}
        provider=Provider(lambda parts:(True,{'taskDefinition':definition},'ok'))
        provider.ACCOUNT='337159794548';provider.REGION='eu-west-1';provider.REPOSITORY='kanbien-core-platform/core-server'
        provider.candidate_runnable_manifest=lambda receipt:(child,'ok')
        provider.validate_receipt=lambda path:receipt
        task={'taskArn':'original','taskDefinitionArn':'definition-safe','containers':[{'name':'core-server-persistence','image':image,'imageDigest':child}]}
        self.assertTrue(module.receipt_matches_task(provider,receipt,task,'definition-safe')[0])
        for override in ({'containerOverrides':None},{'containerOverrides':[{'name':'core-server-persistence','environmentFiles':[{'value':'synthetic','type':'s3'}]}]}):
            self.assertFalse(module.receipt_matches_task(provider,receipt,{**task,'overrides':override},'definition-safe')[0])
        self.assertFalse(module.receipt_matches_task(provider,{**receipt,'source_revision':'old'},task,'definition-safe')[0])
        self.assertFalse(module.receipt_matches_task(provider,{**receipt,'image_digest':'sha256:'+'c'*64},task,'definition-safe')[0])
        wrong=copy.deepcopy(task);wrong['containers'][0]['imageDigest']='sha256:'+'c'*64
        create=SimpleNamespace(package_gates=lambda path:True)
        for continuation in ([],['--reconcile-original-task','original']):
            provider.calls=[]
            with patch.object(module,'module',side_effect=[provider,create]),patch.object(module,'current_task',return_value=(wrong,'ok','definition-safe')),patch.object(sys,'argv',['test','--receipt','synthetic',*continuation]):
                self.assertEqual(result(module.main)[1]['verdict'],'blocked')
            self.assertFalse(any(parts[1]=='stop-task' for parts in provider.calls))

    def test_replacement_wait_observes_original_before_new_task(self):
        module=load(RUN/'rehearse-server-replacement/script.py')
        original={'taskArn':'original'};replacement={'taskArn':'replacement'}
        with patch.object(module,'current_task',side_effect=[(original,'ok','definition'),(replacement,'ok','definition')]),patch.object(module.time,'monotonic',return_value=0),patch.object(module.time,'sleep'):
            self.assertEqual(module.replacement_task(SimpleNamespace(),'original','definition',60),(replacement,'ok'))

    def test_package_gates_execute_nested_mandatory_checks_once(self):
        import subprocess
        create=load(DEPLOY/'create-change-set/script.py')
        active=load(ROOT/'scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.py')
        target=ROOT/'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes'
        for rejected in (None,'validate-secret-dependency-declaration','validate-persistence-diagnostic-mapping'):
            counts={key:0 for key in ('validate-secret-dependency-declaration','validate-persistence-diagnostic-mapping')}
            def invoke(command,**kwargs):
                script=command[0] if command[0].endswith('.sh') else command[1]
                if 'validate-active-workload-health-recovery/script.sh' in script:
                    with patch.object(sys,'argv',['active','--target-root',str(target),'--json']),contextlib.redirect_stdout(io.StringIO()):
                        code=active.main()
                    return subprocess.CompletedProcess(command,code,stdout='',stderr='')
                if '/validate-accepted-release/script.sh' in script:
                    return subprocess.CompletedProcess(command,0,stdout=json.dumps({'verdict':'validated'}),stderr='')
                relevant='--scope-contract' in command and '/core-server-persistence/' in command[command.index('--scope-contract')+1]
                for key in counts:
                    if relevant and key in script:
                        counts[key]+=1
                        return subprocess.CompletedProcess(command,1 if rejected==key else 0,stdout='',stderr='')
                return subprocess.CompletedProcess(command,0,stdout='',stderr='')
            with patch.object(create,'controls',return_value=SimpleNamespace(declaration_covered=lambda:True)),patch.object(create.subprocess,'run',side_effect=invoke):
                self.assertEqual(create.package_gates(Path('synthetic')),rejected is None)
            self.assertEqual(counts,{'validate-secret-dependency-declaration':1,'validate-persistence-diagnostic-mapping':1})

    def test_change_set_submission_reconciliation_is_observation_only(self):
        module=load(DEPLOY/'create-change-set/script.py');prepare=load(DEPLOY/'prepare-candidate/script.py')
        receipt={'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40};name='synthetic-create'
        params=[{'ParameterKey':key,'ParameterValue':value} for key,value in {'ImageDigest':receipt['image_digest'],'SupportImageDigest':receipt['image_digest'],'RestoreVerifierImageDigest':receipt['image_digest'],'SourceRevision':receipt['source_revision']}.items()]
        with tempfile.TemporaryDirectory() as directory:
            diagnostic=Path(directory)/'synthetic-diagnostic.json'
            for status,verdict in [('CREATE_PENDING','pending'),('FAILED','failed'),('CREATE_COMPLETE','created-awaiting-review')]:
                provider=Provider(lambda parts:(True,{'ChangeSetName':name,'Status':status,'ExecutionStatus':'AVAILABLE','Parameters':params},'ok'))
                provider.change_name_matches=prepare.change_name_matches
                self.assertEqual(result(lambda:module.reconcile(provider,name,receipt,diagnostic))[1]['verdict'],verdict)
                expected = ['describe-change-set']
                if status == 'FAILED':
                    # A rejected named change set receives bounded read-only
                    # diagnosis before its safe evidence report is retained.
                    expected += ['describe-change-set', 'describe-stack-events']
                self.assertEqual([parts[1] for parts in provider.calls],expected)
            provider=Provider(lambda parts:(False,None,'aws-command-timeout'))
            self.assertEqual(result(lambda:module.reconcile(provider,name,receipt,diagnostic))[1]['verdict'],'uncertain')

    def test_update_controllers_reconcile_without_mutation(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py');digest='sha256:'+'a'*64;revision='a'*40
        for name,success in [('transition-qualified-release','transitioned'),('apply-private-verifier-route-update','updated'),('apply-restoration-verifier-surface','applied')]:
            module=load(DEPLOY/name/'script.py');change_name='synthetic-operation'
            params={'ImageDigest':digest,'SupportImageDigest':digest,'RestoreVerifierImageDigest':digest,'SourceRevision':revision}
            if name=='apply-restoration-verifier-surface':
                changes=[{'ResourceChange':{'LogicalResourceId':item,'ResourceType':'AWS::EC2::SecurityGroup','Action':'Add'}} for item in module.ADDED]
            elif name=='apply-private-verifier-route-update':changes=[{'ResourceChange':{'LogicalResourceId':'VerifierEgressToServer','ResourceType':'AWS::EC2::SecurityGroupEgress','Action':'Add'}}]
            else:changes=[{'ResourceChange':{'LogicalResourceId':'Runtime','ResourceType':'AWS::ECS::TaskDefinition','Action':'Modify'}}]
            change={'ChangeSetName':change_name,'Status':'CREATE_COMPLETE','ExecutionStatus':'EXECUTE_COMPLETE','ChangeSetType':'UPDATE','Parameters':[{'ParameterKey':key,'ParameterValue':value} for key,value in params.items()],'Changes':changes}
            with tempfile.TemporaryDirectory(prefix='persistence-controller-diagnostics-') as directory:
                # A synthetic provider failure must never create a file in the
                # canonical retained-evidence directory.  The production
                # controller keeps that durable route; this fixture uses a
                # temporary substitute while exercising the same write path.
                diagnostics = patch.object(module, 'DIAGNOSTIC_DIRECTORY', Path(directory)) if name=='transition-qualified-release' else contextlib.nullcontext()
                with diagnostics:
                    for status,verdict in [('UPDATE_IN_PROGRESS','pending'),('UPDATE_ROLLBACK_FAILED','failed'),('UPDATE_COMPLETE',success)]:
                        def response(parts):
                            if parts[1]=='describe-change-set':return True,change,'ok'
                            if parts[1]=='describe-stacks':return True,{'Stacks':[{'StackStatus':status,'Parameters':change['Parameters']}]},'ok'
                            raise AssertionError(f'mutation during reconciliation: {parts}')
                        provider=Provider(response)
                        with patch.object(prepare,'aws',provider.aws):
                            call=(lambda:module.reconcile(prepare,change_name,digest)) if name=='apply-restoration-verifier-surface' else (lambda:module.reconcile(prepare,change_name,digest,revision))
                            self.assertEqual(result(call)[1]['verdict'],verdict)
                        self.assertTrue(all(parts[1].startswith('describe-') for parts in provider.calls))
            with tempfile.TemporaryDirectory(prefix='persistence-controller-diagnostics-') as directory:
                diagnostics = patch.object(module, 'DIAGNOSTIC_DIRECTORY', Path(directory)) if name=='transition-qualified-release' else contextlib.nullcontext()
                with diagnostics, patch.object(prepare,'aws',return_value=(False,None,'aws-command-timeout')):
                    call=(lambda:module.reconcile(prepare,change_name,digest)) if name=='apply-restoration-verifier-surface' else (lambda:module.reconcile(prepare,change_name,digest,revision))
                    self.assertEqual(result(call)[1]['verdict'],'uncertain')

    def test_transition_failure_retains_allowlisted_diagnostic(self):
        """A circuit-breaker failure survives controller reconciliation safely."""
        module=load(DEPLOY/'transition-qualified-release/script.py')
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        digest='sha256:'+'a'*64; revision='a'*40; name='kanbien-core-platform-persistence-rollback-'+'a'*12
        parameters=[{'ParameterKey':key,'ParameterValue':value} for key,value in {
            'ImageDigest':digest,'SupportImageDigest':digest,
            'RestoreVerifierImageDigest':digest,'SourceRevision':revision,
        }.items()]
        change={'ChangeSetName':name,'Status':'CREATE_COMPLETE','ExecutionStatus':'EXECUTE_COMPLETE','ChangeSetType':'UPDATE','Parameters':parameters,'Changes':[{'ResourceChange':{'ResourceType':'AWS::ECS::TaskDefinition'}}]}
        self.assertTrue(module.reviewable(change,'UPDATE_ROLLBACK_COMPLETE',name,digest,revision))
        def response(parts):
            if parts[1]=='describe-change-set': return True,change,'ok'
            if parts[1]=='describe-stacks': return True,{'Stacks':[{'StackStatus':'UPDATE_ROLLBACK_COMPLETE','Parameters':parameters}]},'ok'
            if parts[1]=='describe-stack-events': return True,{'StackEvents':[{'LogicalResourceId':'CoreServerPersistenceService','ResourceType':'AWS::ECS::Service','ResourceStatus':'UPDATE_FAILED','ResourceStatusReason':'ECS deployment circuit breaker triggered'}]},'ok'
            raise AssertionError(f'unexpected mutation or observation: {parts}')
        provider=Provider(response)
        with tempfile.TemporaryDirectory() as directory, patch.object(prepare,'aws',provider.aws), patch.object(module,'DIAGNOSTIC_DIRECTORY',Path(directory)):
            report=result(lambda:module.reconcile(prepare,name,digest,revision))[1]
            path=Path(directory)/(name+'.json')
            self.assertEqual(report['verdict'],'failed')
            self.assertTrue(path.is_file())
            saved=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(saved['operation_outcome'],'failed')
            self.assertEqual(saved['facts']['resource_logical_id'],'CoreServerPersistenceService')
            self.assertNotIn('ECS deployment circuit breaker triggered',path.read_text(encoding='utf-8'))
        self.assertTrue(all(parts[1].startswith('describe-') for parts in provider.calls))

    def test_missing_executed_change_set_reconciles_through_matching_stack_only(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        expected={'ImageDigest':'sha256:'+'a'*64,'SupportImageDigest':'sha256:'+'a'*64,'RestoreVerifierImageDigest':'sha256:'+'a'*64,'SourceRevision':'a'*40}
        params=[{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()]
        for status,verdict in [('UPDATE_IN_PROGRESS','pending'),('UPDATE_COMPLETE','complete'),('UPDATE_ROLLBACK_COMPLETE','uncertain')]:
            provider=Provider(lambda parts: (False,None,'aws-resource-missing') if parts[1]=='describe-change-set' else (True,{'Stacks':[{'StackStatus':status,'Parameters':params}]},'ok'))
            with patch.object(prepare,'aws',provider.aws):
                self.assertEqual(prepare.observe_update('synthetic-operation',expected,lambda change: True)[0],verdict)
            self.assertEqual([parts[1] for parts in provider.calls],['describe-change-set','describe-stacks'])
        wrong=[{'ParameterKey':key,'ParameterValue':value} for key,value in {**expected,'ImageDigest':'sha256:'+'b'*64}.items()]
        provider=Provider(lambda parts: (False,None,'aws-resource-missing') if parts[1]=='describe-change-set' else (True,{'Stacks':[{'StackStatus':'UPDATE_COMPLETE','Parameters':wrong}]},'ok'))
        with patch.object(prepare,'aws',provider.aws):
            self.assertEqual(prepare.observe_update('synthetic-operation',expected,lambda change: True)[0],'uncertain')

    def test_retirement_reobserves_exact_stack_and_never_repeats_effects(self):
        module=load(DEPLOY/'retire-failed-candidate/script.py')
        identity=f'arn:aws:cloudformation:{module.REGION}:337159794548:stack/{module.STACK}/synthetic'
        for status,verdict in [('DELETE_IN_PROGRESS','pending'),('DELETE_FAILED','failed'),('DELETE_COMPLETE','pending'),('ROLLBACK_FAILED','pending')]:
            provider=Provider(lambda parts:(True,{'Stacks':[{'StackId':identity,'StackName':module.STACK,'StackStatus':status}]},'ok'))
            with patch.object(module,'aws',provider.aws):
                report=result(lambda:module.observed_retirement(identity))[1]
                self.assertEqual(report['verdict'],verdict)
                if status=='DELETE_COMPLETE':self.assertEqual(report['facts']['final_snapshot_proof'],'separately-required')
            self.assertEqual([parts[1] for parts in provider.calls],['describe-stacks'])
        with patch.object(module,'aws',return_value=(False,None,'aws-command-timeout')):
            self.assertEqual(module.no_active_service(),(False,'aws-command-timeout'))
            self.assertEqual(result(lambda:module.observed_retirement(identity))[1]['verdict'],'uncertain')
        # An explicit continuation after deletion has started still cannot delete twice.
        provider=Provider(lambda parts:(True,{'Stacks':[{'StackId':identity,'StackName':module.STACK,'StackStatus':'DELETE_IN_PROGRESS'}]},'ok'))
        with patch.object(module,'aws',provider.aws):self.assertEqual(result(lambda:module.observed_retirement(identity,True))[1]['verdict'],'pending')
        self.assertEqual(len(provider.calls),1)

    def test_server_replacement_reconciliation_cannot_stop_twice(self):
        module=load(RUN/'rehearse-server-replacement/script.py')
        identity='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/synthetic'
        prepare=SimpleNamespace(REGION='eu-west-1',ACCOUNT='337159794548',validate_receipt=lambda path:{'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40},live_budget=lambda:(True,'ok'))
        create=SimpleNamespace(package_gates=lambda path:True)
        original={'taskArn':identity,'taskDefinitionArn':'definition-safe','lastStatus':'STOPPED','stoppedReason':'governed core-server-persistence replacement rehearsal','stoppedAt':'2026-10-24T10:00:00Z'}
        for code,verdict in [('persistence-replacement-service-not-healthy','pending'),('persistence-replacement-rollout-failed','failed'),('aws-command-timeout','uncertain')]:
            provider=Provider(lambda parts:(True,{'tasks':[original]},'ok'))
            prepare.aws=provider.aws
            with patch.object(module,'module',side_effect=[prepare,create]),patch.object(module,'current_task',return_value=(None,code,None)),patch.object(sys,'argv',['test','--receipt','synthetic','--reconcile-original-task',identity]):
                self.assertEqual(result(module.main)[1]['verdict'],verdict)
            self.assertFalse(any(parts[1]=='stop-task' for parts in provider.calls))

    def test_runtime_identity_lifecycle_has_no_password_rotation_path(self):
        module=load(RUN/'rehearse-runtime-credential-lifecycle/script.py')
        # IAM task-role renewal and per-connection database tokens replace the
        # former secret-version controller. A lifecycle rehearsal must not
        # regain an API that reads, writes, or transports a database password.
        for obsolete in ('advance_secret','current_secret_version','RUNTIME_SECRET_OUTPUT','SECRET_CHECKPOINT'):
            self.assertFalse(hasattr(module,obsolete))
        receipt=Path('synthetic-receipt.json')
        with patch.object(module,'administer',return_value=True) as administer,patch.object(module,'replace',return_value=True) as replace,patch.object(module,'healthy',return_value=True) as healthy,patch.object(module,'verifier_receipt',return_value='retained-receipt.json'):
            self.assertEqual(module.recover(receipt)[0],'ok')
        administer.assert_called_once_with('restore-runtime')
        replace.assert_called_once_with(receipt)
        self.assertEqual(healthy.call_args_list,[call('health-ready'),call('read')])

    def test_migration_rejection_preserves_only_closed_safe_log_facts(self):
        module=load(RUN/'run-migration/script.py')
        task={'taskArn':'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'a'*32,'startedBy':'kp-'+'b'*32,'lastStatus':'STOPPED','containers':[{'exitCode':1}],'startedAt':'2026-10-24T10:00:00Z','stoppedAt':'2026-10-24T10:00:02Z'}
        safe=json.dumps({'verdict':'rejected','code':'PERSISTENCE_MIGRATION_NOT_CONFIRMED','stage':'migration','provider_failure_class':'access_denied'})
        provider=Provider(lambda parts:(True,{'events':[{'message':safe}]},'ok'))
        with patch.object(module,'aws',provider.aws):
            report=result(lambda:module.accepted_completion(task,120,'apply'))[1]
        self.assertEqual(report['verdict'],'failed')
        self.assertEqual(report['facts']['safe_result_code'],'PERSISTENCE_MIGRATION_NOT_CONFIRMED')
        self.assertEqual(report['facts']['safe_provider_failure_class'],'access_denied')
        unsafe=json.dumps({'verdict':'rejected','code':'PERSISTENCE_MIGRATION_NOT_CONFIRMED','stage':'migration','password':'synthetic-canary'})
        provider=Provider(lambda parts:(True,{'events':[{'message':unsafe}]},'ok'))
        with patch.object(module,'aws',provider.aws):
            report=result(lambda:module.accepted_completion(task,120,'apply'))[1]
        self.assertEqual(report['verdict'],'failed')
        self.assertNotIn('safe_result_code',report['facts'])
        self.assertNotIn('synthetic-canary',json.dumps(report))

    def test_administration_completion_requires_a_closed_safe_result_record(self):
        module=load(RUN/'run-administration/script.py')
        task={'taskArn':'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'a'*32}
        for result_code in ('PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED','PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED'):
            expected=json.dumps({'verdict':'accepted','code':result_code})
            provider=Provider(lambda parts:(True,{'events':[{'message':expected}]},'ok'))
            with patch.object(module.MIGRATION,'aws',provider.aws):
                self.assertEqual(module.accepted_log(task,'observe-migration-state'),(result_code,'ok'))
        rejected=json.dumps({'verdict':'rejected','code':'PERSISTENCE_MIGRATION_STATE_ALREADY_APPLIED'})
        provider=Provider(lambda parts:(True,{'events':[{'message':rejected}]},'ok'))
        with patch.object(module.MIGRATION,'aws',provider.aws):
            self.assertEqual(module.accepted_log(task,'observe-migration-state'),(None,'persistence-administration-not-confirmed'))

    def test_administration_observation_retry_reuses_exact_retained_receipt(self):
        """An interrupted observation retry must not start a second task."""
        module=load(RUN/'run-administration/script.py')
        digest='sha256:'+'d'*64;definition='definition-safe'
        task={'taskArn':'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'d'*32,'taskDefinitionArn':definition,'lastStatus':'STOPPED','startedAt':'2026-10-26T12:00:00Z','stoppedAt':'2026-10-26T12:00:08Z','stoppedReason':'Essential container in task exited','containers':[{'exitCode':0}]}
        receipt=module.RECEIPTS.make(proof_type='administration',operation='prove-effective-privilege',task=task,image_digest=digest,result_code='PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN',context={'completion_deadline_seconds':300,'completion_duration_seconds':8},controller='run-administration',collected_at='2026-10-26T12:00:09Z')
        with tempfile.TemporaryDirectory(prefix='administration-retained-receipt-') as directory:
            destination=Path(directory)/'proof-receipts'
            with patch.object(module,'ROOT',Path(directory)),patch.object(module,'deadline',return_value=300),patch.object(module.RECEIPTS,'RECEIPTS',destination),patch.object(module.MIGRATION,'outputs',side_effect=[({'CoreServerPersistenceAdministrationTaskDefinitionArn':definition,'PersistenceAdministrationSecurityGroupId':'sg-safe'},'ok'),({'PrivateSubnetIds':'subnet-safe'},'ok')]),patch.object(module.MIGRATION,'image_digest',return_value=digest),patch.object(module.MIGRATION,'aws',side_effect=AssertionError('retained observation retry must not submit or query a task')):
                path=module.RECEIPTS.persist(receipt)
                with patch.object(sys,'argv',['test','--operation','prove-effective-privilege']):
                    code,report,_=result(module.main)
            self.assertEqual(code,0,report)
            self.assertEqual(report['findings'],[{'code':'persistence-administration-reconciled-retained-receipt'}])
            self.assertTrue(report['facts']['proof_receipt'].endswith(path.name))
            self.assertEqual(module.retained_observation('restore-runtime',definition),(None,None))
        unsafe=json.dumps({'verdict':'accepted','code':'PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED','password':'synthetic-canary'})
        provider=Provider(lambda parts:(True,{'events':[{'message':unsafe}]},'ok'))
        with patch.object(module.MIGRATION,'aws',provider.aws):
            self.assertEqual(module.accepted_log(task,'observe-migration-state'),(None,'persistence-administration-not-confirmed'))

    def test_correction_parameters_remain_complete_and_unique(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        digest='sha256:'+'a'*64
        parameters=prepare.candidate_parameters({'RepositoryUri':'synthetic-image'},{'PrivateSubnetIds':'subnet-safe'},{'image_digest':digest,'source_revision':'a'*40})
        self.assertEqual(parameters['ImageDigest'],digest)
        self.assertEqual(parameters['SupportImageDigest'],digest)
        self.assertEqual(parameters['RestoreVerifierImageDigest'],digest)
        surface=load(DEPLOY/'apply-restoration-verifier-surface/script.py')
        values=surface.surface_parameters({'Parameters':[{'ParameterKey':'ImageDigest'},{'ParameterKey':'RestoreVerifierImageDigest'}]},digest)
        self.assertEqual(len([item for item in values if item['ParameterKey']=='RestoreVerifierImageDigest']),1)
        self.assertEqual(values[-1]['ParameterValue'],digest)
        egress_change={'ChangeSetName':'restore-egress','Status':'CREATE_COMPLETE','ExecutionStatus':'AVAILABLE','ChangeSetType':'UPDATE','Parameters':[{'ParameterKey':item['ParameterKey'],'ParameterValue':item.get('ParameterValue')} for item in values], 'Changes':[{'ResourceChange':{'LogicalResourceId':'RestorationVerifierRestoredDatabaseEgress','ResourceType':'AWS::EC2::SecurityGroupEgress','Action':'Add'}}]}
        self.assertTrue(surface.review(egress_change,'restore-egress',digest,surface.EGRESS_ONLY))
        self.assertEqual(surface.change_name(digest,'egress'),'kanbien-core-platform-persistence-restore-egress-'+'a'*12)
        egress_change['Changes'].append({'ResourceChange':{'LogicalResourceId':'RestoredDatabaseIngressFromRestorationVerifier','ResourceType':'AWS::EC2::SecurityGroupIngress','Action':'Add'}})
        self.assertFalse(surface.review(egress_change,'restore-egress',digest,surface.EGRESS_ONLY))
        route=load(DEPLOY/'apply-private-verifier-route-update/script.py')
        report=result(lambda:route.report('updated','persistence-private-verifier-route-updated',facts={'change_set':'synthetic'}))[1]
        self.assertEqual(report['facts']['change_set'],'synthetic')
        self.assertTrue(all(isinstance(item['code'],str) for item in report['findings']))

    def test_update_parameter_review_preserves_unowned_stack_values(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        digest='sha256:'+'a'*64
        desired={'ImageDigest':digest,'SupportImageDigest':digest,'RestoreVerifierImageDigest':digest,'SourceRevision':'a'*40}
        current={**desired,'EnableObservability':'false','ObservabilityCollectorImage':'collector-safe','ObservabilityAlertEmail':'alert-safe'}
        self.assertTrue(prepare.update_parameters_match(current,desired,current))
        changed={**current,'EnableObservability':'true'}
        self.assertFalse(prepare.update_parameters_match(changed,desired,current))
        self.assertFalse(prepare.update_parameters_match({key:value for key,value in current.items() if key!='ObservabilityAlertEmail'},desired,current))
        self.assertFalse(prepare.update_parameters_match({**current,'Unexpected':'value'},desired,current))

    def test_declaration_gap_blocks_before_provider_calls(self):
        import subprocess
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        malformed=subprocess.CompletedProcess(['synthetic-check'],1,stdout=json.dumps({'verdict':'gap','findings':[{'code':'requirement-implementation-missing'}]}),stderr='')
        with patch.object(prepare.subprocess,'run',return_value=malformed):
            self.assertFalse(prepare.declaration_covered())
        receipt={'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40}
        with patch.object(prepare,'validate_receipt',return_value=receipt),patch.object(prepare,'declaration_covered',return_value=False),patch.object(prepare,'aws',side_effect=AssertionError('provider reached')),patch.object(sys,'argv',['test','--receipt','synthetic']):
            self.assertEqual(result(prepare.main)[1]['findings'][0]['code'],'persistence-declaration-coverage-gap')
        for name in ('create-change-set','deploy-candidate'):
            module=load(DEPLOY/name/'script.py')
            provider=SimpleNamespace(validate_receipt=lambda path:receipt,declaration_covered=lambda:False,aws=lambda *parts:(_ for _ in ()).throw(AssertionError('provider reached')))
            args=['test','--receipt','synthetic']
            if name=='deploy-candidate':args+=['--approved-change-set','kanbien-core-platform-persistence-create-'+'a'*12]
            with patch.object(module,'controls',return_value=provider),patch.object(sys,'argv',args):
                self.assertEqual(result(module.main)[1]['findings'][0]['code'],'persistence-declaration-coverage-gap')

    def test_wrong_live_parameters_cannot_execute(self):
        module=load(DEPLOY/'deploy-candidate/script.py')
        digest,revision='sha256:'+'a'*64,'a'*40
        receipt={'image_digest':digest,'source_revision':revision}
        name='kanbien-core-platform-persistence-create-'+digest[7:19]
        expected={'ImageDigest':digest,'SupportImageDigest':digest,'RestoreVerifierImageDigest':digest,'SourceRevision':revision,'PrivateSubnetIds':'subnet-safe','EndpointSecurityGroupId':'sg-safe'}
        for key in ('PrivateSubnetIds','EndpointSecurityGroupId'):
            wrong={**expected,key:'unrelated'}
            change={'ChangeSetName':name,'Status':'CREATE_COMPLETE','ChangeSetType':'CREATE','Parameters':[{'ParameterKey':k,'ParameterValue':v} for k,v in wrong.items()],'Changes':[{'ResourceChange':{'ResourceType':'AWS::RDS::DBInstance'}}]}
            def response(parts):
                if parts[1]=='describe-change-set':return True,change,'ok'
                if parts[1]=='describe-stacks':return True,{'Stacks':[{'StackStatus':'REVIEW_IN_PROGRESS'}]},'ok'
                raise AssertionError(f'consequential operation reached: {parts}')
            provider=Provider(response)
            provider.declaration_covered=lambda:True
            provider.validate_receipt=lambda path:receipt
            provider.foundation_outputs=lambda:({},'ok')
            provider.infrastructure_parameters=lambda outputs:({},'ok')
            provider.candidate_image=lambda receipt:(True,'ok')
            provider.candidate_parameters=lambda *args:expected
            with patch.object(module,'controls',return_value=provider),patch.object(sys,'argv',['test','--receipt','synthetic.json','--approved-change-set',name]):
                report=result(module.main)[1]
                self.assertEqual(report['findings'][0]['code'],'persistence-change-set-live-parameters-mismatch')
            self.assertFalse(any(parts[1]=='execute-change-set' for parts in provider.calls))

    def test_parent_preserves_timeout_operation_receipt(self):
        import subprocess
        module=load(RUN/'rehearse-runtime-credential-lifecycle/script.py')
        receipt={'verdict':'pending','facts':{'administration_task':'task-safe','secret':'must-not-escape'}}
        error=subprocess.TimeoutExpired(['synthetic'],180,stderr=json.dumps(receipt).encode())
        with patch.object(module.subprocess,'run',side_effect=error):
            self.assertIsNone(module.child('synthetic-controller'))
        report=result(lambda:module.report('blocked','child-unconfirmed'))[1]
        self.assertEqual(report['verdict'],'pending')
        self.assertEqual(report['facts']['child_checkpoint']['facts'],{'administration_task':'task-safe'})
        self.assertNotIn('must-not-escape',json.dumps(report))

    def test_malformed_endpoint_group_blocks_before_mutation(self):
        module=load(DEPLOY/'prepare-candidate/script.py')
        endpoints=[{'ServiceName':name,'State':'available','Groups':[{'GroupId':'sg-safe'}],'VpcId':'vpc-safe','VpcEndpointType':'Interface','PrivateDnsEnabled':True} for name in module.INTERFACE_SERVICES]
        outputs={'VpcId':'vpc-safe','ServiceDiscoveryArn':'arn/service-safe','PrivateSubnetIds':'subnet-safe','ClusterArn':'cluster-safe','VerifierSecurityGroupId':'sg-safe','LogGroupName':'logs-safe'}
        def response(parts):
            if parts[1]=='describe-vpcs':return True,{'Vpcs':[{'CidrBlock':'10.0.0.0/16'}]},'ok'
            if parts[1]=='get-service':return True,{'Service':{'DnsConfig':{'NamespaceId':'ns-safe'}}},'ok'
            if parts[1]=='describe-vpc-endpoints':return True,{'VpcEndpoints':endpoints},'ok'
            if parts[1]=='describe-managed-prefix-lists':return True,{'PrefixLists':[{'PrefixListId':'pl-safe'}]},'ok'
            raise AssertionError(parts)
        provider=Provider(response)
        with patch.object(module,'aws',provider.aws):
            self.assertIsNotNone(module.infrastructure_parameters(outputs)[0])
            for field,value in [('VpcId','vpc-unrelated'),('VpcEndpointType','Gateway'),('PrivateDnsEnabled',False)]:
                original=endpoints[0][field]; endpoints[0][field]=value
                self.assertEqual(module.infrastructure_parameters(outputs)[1],'persistence-private-startup-endpoint-posture-invalid')
                endpoints[0][field]=original
            for groups in [[],[{'GroupId':'sg-safe'},{'GroupId':'sg-other'}],None]:
                endpoints[0]['Groups']=groups
                self.assertEqual(module.infrastructure_parameters(outputs)[1],'persistence-endpoint-security-group-unavailable')

    def test_snapshot_reobserves_existing_operation(self):
        module=load(RUN/'create-recovery-point/script.py'); sid='kanbien-core-platform-persistence-recovery-20261024'
        snapshot={'DBSnapshotIdentifier':sid,'DBInstanceIdentifier':module.DATABASE,'Encrypted':True,'Status':'creating'}
        for status,verdict in [('creating','pending'),('available','available'),('failed','failed'),('unexpected','uncertain')]:
            snapshot['Status']=status
            provider=Provider(lambda parts:(True,{'DBSnapshots':[snapshot]},'ok'))
            self.assertEqual(result(lambda:module.observe_or_create(provider,sid))[1]['verdict'],verdict)
            self.assertEqual(len(provider.calls),1)
        provider=Provider(lambda parts:(False,None,'aws-resource-missing') if parts[1]=='describe-db-snapshots' else (False,None,'aws-command-timeout'))
        self.assertEqual(result(lambda:module.observe_or_create(provider,sid))[1]['verdict'],'uncertain')
        self.assertEqual([parts[1] for parts in provider.calls],['describe-db-snapshots','create-db-snapshot'])
        provider.calls=[]
        self.assertEqual(result(lambda:module.observe_or_create(provider,sid,True))[1]['verdict'],'uncertain')
        self.assertEqual([parts[1] for parts in provider.calls],['describe-db-snapshots'])

    def test_task_reconciliation_and_lost_submission(self):
        for name,mode_arg,mode,output_key in [('run-migration','--migration-operation','apply','CoreServerPersistenceMigrationTaskDefinitionArn'),('verify-candidate','--mode','create','CoreServerPersistenceVerifierTaskDefinitionArn')]:
            module=load(RUN/name/'script.py'); operation='kp-'+'a'*32
            arn=f'arn:aws:ecs:{module.REGION}:{module.ACCOUNT}:task/{module.CLUSTER}/'+'b'*32
            task={'taskArn':arn,'taskDefinitionArn':'definition-safe','startedBy':operation,'lastStatus':'STOPPED','containers':[{'exitCode':0}],'startedAt':'2026-10-24T10:00:00Z','stoppedAt':'2026-10-24T10:00:02Z'}
            expected_env={'PERSISTENCE_MIGRATION_OPERATION':mode} if name=='run-migration' else {'PERSISTENCE_VERIFIER_MODE':mode,'PERSISTENCE_ACCEPTANCE_RECORD_ID':module.RECORD_ID,'PERSISTENCE_ACCEPTANCE_FACT':module.FACT}
            task['overrides']={'inferenceAcceleratorOverrides':[],'containerOverrides':[{'name':'persistence-migration' if name=='run-migration' else 'private-persistence-verifier','environment':[{'name':key,'value':value} for key,value in expected_env.items()]}]}
            def response(parts):
                if parts[1]=='list-tasks':return True,{'taskArns':[arn]},'ok'
                if parts[1]=='describe-tasks':return True,{'tasks':[task]},'ok'
                if parts[1]=='get-log-events':return True,{'events':[{'message':json.dumps({'verdict':'accepted','code':module.SUCCESS[mode]})}]},'ok'
                if parts[1]=='describe-task-definition':return True,{'taskDefinition':{'containerDefinitions':[{'image':'synthetic.invalid/persistence@sha256:'+'c'*64}]}},'ok'
                raise AssertionError(f'unexpected mutation {parts}')
            provider=Provider(response)
            output={output_key:'definition-safe','PersistenceMigrationSecurityGroupId':'sg-safe','PrivateSubnetIds':'subnet-safe','VerifierSecurityGroupId':'sg-safe'}
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(module,'outputs',return_value=(output,'ok')))
                stack.enter_context(patch.object(module,'deadline',return_value=120))
                stack.enter_context(patch.object(module,'aws',provider.aws))
                receipts = stack.enter_context(temporary_receipts(module))
                if name=='verify-candidate':stack.enter_context(patch.object(module,'no_direct_database_credential',return_value=True))
                for status,exitcode,verdict in [('RUNNING',0,'pending'),('STOPPED',1,'failed'),('STOPPED',0,'accepted')]:
                    task['lastStatus']=status;task['containers'][0]['exitCode']=exitcode
                    with patch.object(sys,'argv',['test',mode_arg,mode,'--reconcile-operation',operation]):
                        self.assertEqual(result(module.main)[1]['verdict'],verdict)
                self.assertFalse(any(parts[1]=='run-task' for parts in provider.calls))
                valid_overrides=copy.deepcopy(task['overrides'])
                for mutation in ('wrong-record','command','duplicate','task-role'):
                    task['overrides']=copy.deepcopy(valid_overrides)
                    container=task['overrides']['containerOverrides'][0]
                    if mutation=='wrong-record':container['environment'][0]['value']='unrelated'
                    if mutation=='command':container['command']=['unrelated.js']
                    if mutation=='duplicate':container['environment'].append(copy.deepcopy(container['environment'][0]))
                    if mutation=='task-role':task['overrides']['taskRoleArn']='unrelated-role'
                    with patch.object(sys,'argv',['test',mode_arg,mode,'--reconcile-operation',operation]):
                        self.assertEqual(result(module.main)[1]['verdict'],'blocked')
                task['overrides']=valid_overrides
                # A timeout after submission retains the emitted operation identity.
                provider.responder=lambda parts:(False,None,'aws-command-timeout')
                with patch.object(sys,'argv',['test',mode_arg,mode]):
                    _, final, reports=result(module.main)
                    self.assertEqual(final['verdict'],'uncertain')
                    self.assertEqual(reports[0]['facts']['operation_id'],final['facts']['operation_id'])
                    call=provider.calls[-1];self.assertIn('--client-token',call)
            self.assertFalse(module.accepted_message('prefix '+json.dumps({'verdict':'accepted','code':module.SUCCESS[mode]}),module.SUCCESS[mode]))

    def test_sanitized_captured_ecs_defaults_and_consequential_mismatches(self):
        fixture=yaml.safe_load((RUN/'fixtures/ecs-captured-responses.yml').read_text())
        self.assertEqual(fixture['evidence_class'],'simulated')
        for kind,script,container_name in [('migration','run-migration','persistence-migration'),('verifier','verify-candidate','private-persistence-verifier'),('derived_restore','rehearse-isolated-database-restore','persistence-restoration-verifier')]:
            controller=load(RUN/script/'script.py');task=fixture['tasks'][kind]
            environment={item['name']:item['value'] for item in task['overrides']['containerOverrides'][0]['environment']}
            predicate=lambda candidate:controller.task_evidence().task_overrides_match(candidate,container_name,environment)
            self.assertTrue(predicate(task))
            if kind=='migration':self.assertTrue(controller.task_operation_bound(task,environment['PERSISTENCE_MIGRATION_OPERATION']))
            if kind=='verifier':self.assertTrue(controller.task_operation_bound(task,environment['PERSISTENCE_VERIFIER_MODE']))
            without_default=copy.deepcopy(task);del without_default['overrides']['inferenceAcceleratorOverrides'];self.assertTrue(predicate(without_default))
            negatives=[]
            for key,value in [('inferenceAcceleratorOverrides',[{'deviceName':'changed'}]),('inferenceAcceleratorOverrides',None),('taskRoleArn','changed'),('executionRoleArn','changed'),('cpu','256'),('memory','512'),('ephemeralStorage',{'sizeInGiB':30}),('unknownDefault',[])]:
                altered=copy.deepcopy(task);altered['overrides'][key]=value;negatives.append(altered)
            for key,value in [('name','unrelated'),('command',['unrelated.js']),('environmentFiles',[]),('cpu',1),('memory',1),('resourceRequirements',[{'type':'GPU','value':'1'}]),('environment',None)]:
                altered=copy.deepcopy(task);altered['overrides']['containerOverrides'][0][key]=value;negatives.append(altered)
            for value in (None,[],{},1,False,'invalid'):
                altered=copy.deepcopy(task);altered['overrides']=value;negatives.append(altered)
                altered=copy.deepcopy(task);altered['overrides']['containerOverrides']=value;negatives.append(altered)
            for mutation in ('wrong-value','duplicate','unhashable-name','non-string-value','extra-key'):
                altered=copy.deepcopy(task);entries=altered['overrides']['containerOverrides'][0]['environment']
                if mutation=='wrong-value':entries[0]['value']='other'
                if mutation=='duplicate':entries.append(copy.deepcopy(entries[0]))
                if mutation=='unhashable-name':entries[0]['name']=[]
                if mutation=='non-string-value':entries[0]['value']={}
                if mutation=='extra-key':entries[0]['unrelated']='other'
                negatives.append(altered)
            for candidate in negatives:self.assertFalse(predicate(candidate))

    def test_malformed_provider_evidence_is_structured(self):
        arn='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'b'*32
        for name,mode_arg,mode,output_key in [('run-migration','--migration-operation','apply','CoreServerPersistenceMigrationTaskDefinitionArn'),('verify-candidate','--mode','read','CoreServerPersistenceVerifierTaskDefinitionArn')]:
            module=load(RUN/name/'script.py')
            output={output_key:'definition-safe','PersistenceMigrationSecurityGroupId':'sg-safe','PrivateSubnetIds':'subnet-safe','VerifierSecurityGroupId':'sg-safe'}
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(module,'outputs',return_value=(output,'ok')))
                stack.enter_context(patch.object(module,'deadline',return_value=120))
                if name=='verify-candidate':stack.enter_context(patch.object(module,'no_direct_database_credential',return_value=True))
                for tasks in (None,{},True,'unexpected',[None]):
                    with patch.object(module,'aws',return_value=(True,{'tasks':tasks},'ok')),patch.object(sys,'argv',['test',mode_arg,mode,'--reconcile-task',arn]):
                        self.assertEqual(result(module.main)[1]['verdict'],'uncertain')
            for definition in (None,[],True,{'containerDefinitions':None}):
                with patch.object(module,'aws',return_value=(True,{'taskDefinition':definition},'ok')):
                    self.assertIsNone(module.image_digest('definition-safe'))
                    if name=='verify-candidate':self.assertFalse(module.no_direct_database_credential('definition-safe'))
            self.assertIsNone(module.duration({'startedAt':'2026-10-25T10:00:00','stoppedAt':'2026-10-25T10:00:02Z'}))
            for value in (None,[],{},False,1,float('nan')):
                self.assertIsNone(module.duration({'startedAt':value,'stoppedAt':'2026-10-25T10:00:02Z'}))
                self.assertIsNone(module.duration({'startedAt':'2026-10-25T10:00:02Z','stoppedAt':value}))
            def bad_identity(*parts):
                return (True,{'taskArns':[arn]},'ok') if parts[1]=='list-tasks' else (True,{'tasks':[{'taskArn':[]}]},'ok')
            with patch.object(module,'aws',side_effect=bad_identity):self.assertIsNone(module.reconciliation_operation('kp-'+'a'*32,'definition-safe')[0])
        module=load(RUN/'rehearse-isolated-database-restore/script.py')
        restored={'Endpoint':{'Address':'synthetic.invalid'},'DbiResourceId':'db-fixture'}
        ctl={'CoreServerPersistenceRestorationVerifierTaskDefinitionArn':'definition-safe','PersistenceRestoredDatabaseSecurityGroupId':'sg-restored','PersistenceRestorationVerifierTaskRoleName':'restore-role'}
        identity='arn:aws:rds-db:eu-west-1:337159794548:dbuser:db-fixture/core_runtime'
        with patch.object(module,'source',return_value=({},'ok')),patch.object(module,'controls',return_value=(ctl,'ok')),patch.object(module,'db',return_value=(restored,'ok')),patch.object(module,'correct',return_value=True),patch.object(module,'task_def_valid',return_value=True),patch.object(module,'temporary_restore_identity_policy',return_value=('ok',identity)),patch.object(module,'verifier_tasks',return_value=([arn],'ok')):
            for tasks in (None,{},True,'unexpected',[None]):
                provider=Provider(lambda _: (True,{'tasks':tasks},'ok'))
                self.assertEqual(result(lambda:module.verify(provider,'snapshot','restore',True))[1]['verdict'],'uncertain')

    def test_argument_preflight_checks_required_inputs_without_provider_access(self):
        cases=[('run-migration',['--migration-operation','apply'],['--migration-operation','unsupported']),
               ('verify-candidate',['--mode','read'],[]),
               ('rehearse-isolated-database-restore',['--operation','restore','--snapshot-id','kanbien-core-platform-persistence-recovery-20261025-b','--record-proof-receipt','not-read-during-parser-check'],['--operation','restore','--snapshot-id','kanbien-core-platform-persistence-recovery-20261025-b'])]
        for name,valid,invalid in cases:
            controller=load(RUN/name/'script.py')
            with patch.object(controller,'proof_receipts',side_effect=AssertionError('argument preflight cannot load receipts')),patch.object(controller,'load' if name=='rehearse-isolated-database-restore' else 'aws',side_effect=AssertionError('argument preflight cannot access provider')):
                with patch.object(sys,'argv',['test','--validate-arguments',*valid]):self.assertEqual(result(controller.main)[1]['verdict'],'valid')
                with patch.object(sys,'argv',['test','--validate-arguments',*invalid]):self.assertEqual(result(controller.main)[1]['verdict'],'blocked')

    def test_restore_rejects_earlier_snapshot_and_binds_exact_continuation(self):
        controller=load(RUN/'rehearse-isolated-database-restore/script.py')
        snapshot='kanbien-core-platform-persistence-recovery-20261025-b';restored_id=controller.restore_id(snapshot)
        source={'DBInstanceIdentifier':controller.DATABASE,'DbiResourceId':'db-SOURCE','InstanceCreateTime':'2026-10-25T09:00:00Z','DBSubnetGroup':{'DBSubnetGroupName':'private-subnets'},'DBInstanceClass':'db.t4g.micro'}
        point={'DBSnapshotIdentifier':snapshot,'DbiResourceId':'db-SOURCE','DBInstanceIdentifier':controller.DATABASE,'Status':'available','Encrypted':True,'SnapshotCreateTime':'2026-10-25T11:00:00Z'}
        task={'taskArn':'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'a'*32,'taskDefinitionArn':'arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:17','lastStatus':'STOPPED','startedAt':'2026-10-25T11:59:58Z','stoppedAt':'2026-10-25T12:00:00Z','containers':[{'exitCode':0}]}
        with temporary_receipts(controller) as receipts,patch.object(controller,'EVIDENCE_CLASS','simulated'):
            proof=receipts.make(proof_type='verifier',operation='read',task=task,image_digest='sha256:'+'a'*64,result_code='KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED',context={'record_id':controller.RECORD_ID,'completion_deadline_seconds':120,'completion_duration_seconds':2},controller='verify-candidate',collected_at='2026-10-25T12:00:01Z')
            path=receipts.persist(proof)
            state={'database':None};mutations=[]
            def response(parts):
                if parts[1]=='describe-db-snapshots':return True,{'DBSnapshots':[point]},'ok'
                if parts[1]=='describe-db-instances':return (True,{'DBInstances':[state['database']]},'ok') if state['database'] else (False,None,'aws-resource-missing')
                if parts[1]=='restore-db-instance-from-db-snapshot':
                    mutations.append(parts)
                    tag_values=parts[parts.index('--tags')+1:]
                    tags=[{'Key':value.split(',Value=',1)[0][4:],'Value':value.split(',Value=',1)[1]} for value in tag_values]
                    state['database']={'DBInstanceIdentifier':restored_id,'DBInstanceStatus':'creating','TagList':tags,'PubliclyAccessible':False,'StorageEncrypted':True,'IAMDatabaseAuthenticationEnabled':True,'EnabledCloudwatchLogsExports':['postgresql'],'Engine':'postgres','DBSubnetGroup':{'DBSubnetGroupName':'private-subnets'},'VpcSecurityGroups':[{'VpcSecurityGroupId':'sg-restored'}]}
                    return True,{},'ok'
                raise AssertionError(f'unexpected provider action {parts}')
            provider=Provider(response)
            with patch.object(controller,'source',return_value=(source,'ok')),patch.object(controller,'controls',return_value=({'PersistenceRestoredDatabaseSecurityGroupId':'sg-restored'},'ok')):
                run=lambda observe=False:result(lambda:controller.restore(provider,snapshot,restored_id,observe,path))[1]
                rejected=run();self.assertEqual(rejected['findings'][0]['code'],'persistence-restore-snapshot-precedes-retained-record');self.assertFalse(mutations)
                point['SnapshotCreateTime']='2026-10-25T12:00:00+00:00'
                self.assertEqual(run(True)['verdict'],'uncertain');self.assertFalse(mutations)
                self.assertEqual(run()['verdict'],'pending');self.assertEqual(len(mutations),1)
                self.assertEqual(run()['verdict'],'pending');self.assertEqual(run(True)['verdict'],'pending');self.assertEqual(len(mutations),1)
                state['database']['DBInstanceStatus']='available'
                self.assertEqual(run(True)['verdict'],'restored');self.assertEqual(len(mutations),1)
                state['database']['TagList'][2]['Value']='other-snapshot'
                self.assertEqual(run(True)['verdict'],'blocked');self.assertEqual(len(mutations),1)
                state['database']['TagList']=[]
                self.assertEqual(run(True)['verdict'],'uncertain');self.assertEqual(len(mutations),1)
                state['database']=None;mutations.clear()
                for field,value in [('DbiResourceId','different-source'),('DBSnapshotIdentifier','other-snapshot'),('SnapshotCreateTime',True),('SnapshotCreateTime',float('nan')),('SnapshotCreateTime','not-time'),('SnapshotCreateTime','2026-10-25T12:00:00')]:
                    original=point[field];point[field]=value;self.assertEqual(run()['verdict'],'blocked');point[field]=original;self.assertFalse(mutations)
                point['OriginalSnapshotCreateTime']='2026-10-25T11:00:00Z'
                self.assertEqual(run()['findings'][0]['code'],'persistence-restore-snapshot-precedes-retained-record');del point['OriginalSnapshotCreateTime']
                source['InstanceCreateTime']='2026-10-25T12:00:00Z'
                self.assertEqual(run()['findings'][0]['code'],'persistence-restore-record-source-incarnation-mismatch');self.assertFalse(mutations)
            with patch.object(controller,'EVIDENCE_CLASS','live'):
                provider.calls=[];self.assertEqual(result(lambda:controller.restore(provider,snapshot,restored_id,False,path))[1]['verdict'],'blocked');self.assertFalse(provider.calls)
            path.write_text('[]')
            provider.calls=[];self.assertEqual(result(lambda:controller.restore(provider,snapshot,restored_id,False,path))[1]['verdict'],'blocked');self.assertFalse(provider.calls)

    def test_historical_task_capture_preserves_qualified_receipts(self):
        for name,mode_arg,mode,output_key,family in [
            ('run-migration','--migration-operation','apply','CoreServerPersistenceMigrationTaskDefinitionArn','kanbien-core-platform-persistence-migration'),
            ('verify-candidate','--mode','read','CoreServerPersistenceVerifierTaskDefinitionArn','kanbien-core-platform-persistence-verifier'),
        ]:
            module=load(RUN/name/'script.py'); digest='sha256:'+'c'*64
            arn=f'arn:aws:ecs:{module.REGION}:{module.ACCOUNT}:task/{module.CLUSTER}/'+'d'*32
            old_definition=f'arn:aws:ecs:{module.REGION}:{module.ACCOUNT}:task-definition/{family}:7'
            task={'taskArn':arn,'taskDefinitionArn':old_definition,'lastStatus':'STOPPED','containers':[{'exitCode':0}],
                  'startedAt':'2026-10-24T10:00:00Z','stoppedAt':'2026-10-24T10:00:02Z'}
            environment={'PERSISTENCE_MIGRATION_OPERATION':mode} if name=='run-migration' else {'PERSISTENCE_VERIFIER_MODE':mode,'PERSISTENCE_ACCEPTANCE_RECORD_ID':module.RECORD_ID,'PERSISTENCE_ACCEPTANCE_FACT':module.FACT}
            task['overrides']={'inferenceAcceleratorOverrides':[],'containerOverrides':[{'name':'persistence-migration' if name=='run-migration' else 'private-persistence-verifier','environment':[{'name':key,'value':value} for key,value in environment.items()]}]}
            def response(parts):
                if parts[1]=='describe-tasks':return True,{'tasks':[task]},'ok'
                if parts[1]=='describe-task-definition':
                    self.assertEqual(parts[-1],old_definition)
                    return True,{'taskDefinition':{'family':family,'containerDefinitions':[{'image':'synthetic.invalid/persistence@'+digest}]}},'ok'
                if parts[1]=='get-log-events':return True,{'events':[{'message':json.dumps({'verdict':'accepted','code':module.SUCCESS[mode]})}]},'ok'
                raise AssertionError(f'historical capture cannot mutate {parts}')
            provider=Provider(response)
            output={output_key:'current-definition:99','PersistenceMigrationSecurityGroupId':'sg-safe','PrivateSubnetIds':'subnet-safe','VerifierSecurityGroupId':'sg-safe'}
            with contextlib.ExitStack() as stack:
                receipts=stack.enter_context(temporary_receipts(module))
                stack.enter_context(patch.object(module,'outputs',return_value=(output,'ok')))
                stack.enter_context(patch.object(module,'deadline',return_value=120))
                stack.enter_context(patch.object(module,'qualified_digest',return_value=digest))
                stack.enter_context(patch.object(module,'aws',provider.aws))
                if name=='verify-candidate':stack.enter_context(patch.object(module,'no_direct_database_credential',return_value=True))
                argv=['test',mode_arg,mode,'--capture-completed-task',arn,'--qualified-receipt','synthetic']
                with patch.object(sys,'argv',argv):
                    self.assertEqual(result(module.main)[1]['verdict'],'accepted')
                    stored=next(receipts.RECEIPTS.glob('*.json'));original=stored.read_bytes()
                    self.assertEqual(result(module.main)[1]['verdict'],'accepted')
                    self.assertEqual(stored.read_bytes(),original)
                    captured=receipts.validate(json.loads(original))
                    self.assertEqual(captured['task']['definition'],old_definition)
                    task['overrides']['containerOverrides'][0]['environment'][0]['value']='unrelated'
                    self.assertEqual(result(module.main)[1]['verdict'],'blocked')
                provider.calls=[]
                with patch.object(sys,'argv',argv+['--reconcile-operation','kp-'+'e'*32]):
                    self.assertEqual(result(module.main)[1]['verdict'],'blocked')
                self.assertFalse(provider.calls)

    def test_historical_replacement_retains_predecessor_successor(self):
        module=load(RUN/'rehearse-server-replacement/script.py'); digest='sha256:'+'c'*64
        prefix='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'
        old_definition='arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-core-server-persistence:7'
        original={'taskArn':prefix+'a'*32,'taskDefinitionArn':old_definition,'group':'service:'+module.SERVICE,'lastStatus':'STOPPED',
                  'startedAt':'2026-10-24T09:00:00Z','stoppedAt':'2026-10-24T10:00:00Z','containers':[{'exitCode':137}],
                  'stoppedReason':'governed core-server-persistence replacement rehearsal'}
        successor={'taskArn':prefix+'b'*32,'taskDefinitionArn':old_definition,'group':'service:'+module.SERVICE,'startedAt':'2026-10-24T10:00:01Z'}
        def response(parts):
            if parts[1]=='describe-tasks':return True,{'tasks':[original if parts[-1]==original['taskArn'] else successor]},'ok'
            if parts[1]=='describe-task-definition':return True,{'taskDefinition':{'containerDefinitions':[{'image':'synthetic.invalid/persistence@'+digest}]}},'ok'
            raise AssertionError(f'historical replacement cannot mutate {parts}')
        prepare=Provider(response);prepare.REGION='eu-west-1';prepare.ACCOUNT='337159794548'
        prepare.validate_receipt=lambda _: {'image_digest':digest,'source_revision':'revision-safe'}
        create=SimpleNamespace(package_gates=lambda _:True)
        argv=['test','--receipt','synthetic','--capture-completed-original-task',original['taskArn'],'--capture-completed-successor-task',successor['taskArn']]
        with temporary_receipts(module) as receipts,patch.object(module,'module',side_effect=[prepare,create]),patch.object(module,'current_task',side_effect=AssertionError('historical capture must use historical definitions')),patch.object(sys,'argv',argv):
            self.assertEqual(result(module.main)[1]['verdict'],'replaced')
            captured=receipts.validate(json.loads(next(receipts.RECEIPTS.glob('*.json')).read_text()))
            self.assertEqual(captured['task']['arn'],original['taskArn'])
            self.assertEqual(captured['context']['successor_task_arn'],successor['taskArn'])
            self.assertEqual(captured['context']['runtime_task_definition'],old_definition)

    def test_replacement_reconciliation_reuses_exact_retained_receipt(self):
        """A host interruption after receipt persistence must not repeat a stop."""
        module=load(RUN/'rehearse-server-replacement/script.py'); digest='sha256:'+'c'*64
        prefix='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'
        definition='arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-core-server-persistence:34'
        original={'taskArn':prefix+'a'*32,'taskDefinitionArn':definition,'group':'service:'+module.SERVICE,'lastStatus':'STOPPED','startedAt':'2026-10-26T12:08:37Z','stoppedAt':'2026-10-26T12:08:40Z','containers':[{'exitCode':137}],'stoppedReason':'governed core-server-persistence replacement rehearsal'}
        image=f'337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server@{digest}'
        successor={'taskArn':prefix+'b'*32,'taskDefinitionArn':definition,'group':'service:'+module.SERVICE,'lastStatus':'RUNNING','startedAt':'2026-10-26T12:08:41Z','containers':[{'name':'core-server-persistence','image':image,'imageDigest':digest}]}
        def response(parts):
            if parts[1]=='describe-tasks': return True,{'tasks':[original if parts[-1]==original['taskArn'] else successor]},'ok'
            if parts[1]=='describe-task-definition': return True,{'taskDefinition':{'taskDefinitionArn':definition,'containerDefinitions':[{'name':'core-server-persistence','image':image,'environment':[{'name':'PLATFORM_SOURCE_COMMIT_SHA','value':'a'*40}]}]}},'ok'
            raise AssertionError(f'unexpected provider action: {parts}')
        prepare=Provider(response); prepare.REGION='eu-west-1'; prepare.ACCOUNT='337159794548'; prepare.REPOSITORY='kanbien-core-platform/core-server'
        prepare.validate_receipt=lambda _: {'image_digest':digest,'source_revision':'a'*40}; prepare.candidate_runnable_manifest=lambda _: (digest,'ok')
        create=SimpleNamespace(package_gates=lambda _:True)
        with temporary_receipts(module) as receipts:
            first=receipts.make(proof_type='server-replacement',operation='controlled-replacement',task=original,image_digest=digest,result_code='PERSISTENCE_SERVER_REPLACED',context={'original_stopped_reason':'governed core-server-persistence replacement rehearsal','successor_task_arn':successor['taskArn'],'successor_started_at':successor['startedAt'],'runtime_task_definition':definition,'recovery_boundary':'2026-10-26T12:08:38Z'},controller='rehearse-server-replacement',collected_at='2026-10-26T12:08:42Z')
            path=receipts.persist(first); original_bytes=path.read_bytes()
            current=(successor,'ok',definition)
            argv=['test','--receipt','synthetic','--reconcile-original-task',original['taskArn'],'--reconcile-successor-task',successor['taskArn']]
            with patch.object(module,'module',side_effect=[prepare,create]),patch.object(module,'current_task',return_value=current),patch.object(sys,'argv',argv):
                report=result(module.main)[1]
            self.assertEqual(report['verdict'],'replaced')
            self.assertEqual(report['facts']['recovery_boundary'],'2026-10-26T12:08:38Z')
            self.assertEqual(path.read_bytes(),original_bytes)
            self.assertFalse(any(parts[1]=='stop-task' for parts in prepare.calls))
            altered=json.loads(path.read_text()); altered['context']['successor_task_arn']=prefix+'d'*32; altered['integrity']['payload_sha256']=receipts.digest({key:value for key,value in altered.items() if key!='integrity'}); path.write_text(json.dumps(altered),encoding='utf-8')
            with patch.object(module,'module',side_effect=[prepare,create]),patch.object(module,'current_task',return_value=current),patch.object(sys,'argv',argv):
                self.assertEqual(result(module.main)[1]['findings'],[{'code':'persistence-replacement-reconciliation-receipt-mismatch'}])

    def test_main_snapshot_suffix_support_is_preserved(self):
        snapshot=load(RUN/'create-recovery-point/script.py');restore=load(RUN/'rehearse-isolated-database-restore/script.py')
        for suffix in ('','-b','-followup'):
            identifier='kanbien-core-platform-persistence-recovery-20261024'+suffix
            self.assertIsNotNone(snapshot.PATTERN.fullmatch(identifier))
            self.assertEqual(restore.restore_id(identifier),'kanbien-core-platform-persistence-restore-20261024'+suffix)
        for suffix in ('-too-long-suffix','-UPPER','-'):
            identifier='kanbien-core-platform-persistence-recovery-20261024'+suffix
            self.assertIsNone(snapshot.PATTERN.fullmatch(identifier))
            self.assertIsNone(restore.restore_id(identifier))

    def test_restore_reconciliation_pending_failed_and_strict_evidence(self):
        module=load(RUN/'rehearse-isolated-database-restore/script.py'); sid='kanbien-core-platform-persistence-recovery-20261024'; rid=module.restore_id(sid)
        restored={'DBInstanceStatus':'available','DbiResourceId':'db-restore-safe','PubliclyAccessible':False,'IAMDatabaseAuthenticationEnabled':True,'VpcSecurityGroups':[{'VpcSecurityGroupId':'sg-restored'}],'Endpoint':{'Address':'synthetic.invalid'}}
        operation=module.restore_run_identity(restored); arn='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'f'*32
        identity='arn:aws:rds-db:eu-west-1:337159794548:dbuser:db-restore-safe/core_runtime'
        task={'taskArn':arn,'taskDefinitionArn':'definition-safe','startedBy':operation,'lastStatus':'STOPPED','containers':[{'exitCode':0}],'startedAt':'2026-10-24T10:00:00Z','stoppedAt':'2026-10-24T10:00:02Z','overrides':{'inferenceAcceleratorOverrides':[],'containerOverrides':[{'name':'persistence-restoration-verifier','environment':[{'name':key,'value':value} for key,value in {'PERSISTENCE_POSTGRES_HOST':'synthetic.invalid','PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE':identity,'PERSISTENCE_ACCEPTANCE_RECORD_ID':module.RECORD_ID,'PERSISTENCE_ACCEPTANCE_FACT_DIGEST':module.FACT_DIGEST}.items()]}]}}
        log=json.dumps({'verdict':'accepted','code':'KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED'})
        def response(parts):
            if parts[1]=='list-tasks':return True,{'taskArns':[arn]},'ok'
            if parts[1]=='describe-tasks':return True,{'tasks':[task]},'ok'
            if parts[1]=='get-log-events':return True,{'events':[{'message':log}]},'ok'
            if parts[1]=='describe-task-definition':return True,{'taskDefinition':{'containerDefinitions':[{'image':'synthetic.invalid/persistence@sha256:'+'c'*64}]}},'ok'
            raise AssertionError(f'unexpected mutation {parts}')
        provider=Provider(response)
        ctl={'CoreServerPersistenceRestorationVerifierTaskDefinitionArn':'definition-safe','PersistenceRestoredDatabaseSecurityGroupId':'sg-restored','PersistenceRestorationVerifierTaskRoleName':'restore-role','PrivateSubnetIds':'subnet-safe','PersistenceRestorationVerifierSecurityGroupId':'sg-verifier'}
        with temporary_receipts(module),patch.object(module,'source',return_value=({},'ok')),patch.object(module,'controls',return_value=(ctl,'ok')),patch.object(module,'db',return_value=(restored,'ok')),patch.object(module,'correct',return_value=True),patch.object(module,'task_def_valid',return_value=True),patch.object(module,'temporary_restore_identity_policy',return_value=('ok',identity)):
            for status,exitcode,verdict in [('RUNNING',0,'pending'),('STOPPED',1,'failed'),('STOPPED',0,'accepted')]:
                task['lastStatus']=status;task['containers'][0]['exitCode']=exitcode
                self.assertEqual(result(lambda:module.verify(provider,sid,rid))[1]['verdict'],verdict)
            log='prefix '+log
            self.assertEqual(result(lambda:module.verify(provider,sid,rid))[1]['verdict'],'pending')
            valid_overrides=copy.deepcopy(task['overrides'])
            for mutation in ('command','extra-env','duplicate','task-role'):
                task['overrides']=copy.deepcopy(valid_overrides)
                container=task['overrides']['containerOverrides'][0]
                if mutation=='command':container['command']=['unrelated.js']
                if mutation=='extra-env':container['environment'].append({'name':'PERSISTENCE_POSTGRES_DATABASE','value':'other'})
                if mutation=='duplicate':container['environment'].append(copy.deepcopy(container['environment'][0]))
                if mutation=='task-role':task['overrides']['taskRoleArn']='unrelated-role'
                self.assertEqual(result(lambda:module.verify(provider,sid,rid))[1]['verdict'],'blocked')
            task['overrides']=valid_overrides
            task['startedBy']='other-operation'
            self.assertEqual(result(lambda:module.verify(provider,sid,rid,True))[1]['verdict'],'uncertain')
            self.assertFalse(any(parts[1]=='run-task' for parts in provider.calls))
            provider.responder=lambda parts:(True,{'taskArns':[]},'ok')
            provider.calls=[]
            self.assertEqual(result(lambda:module.verify(provider,sid,rid,True))[1]['verdict'],'uncertain')
            self.assertFalse(any(parts[1]=='run-task' for parts in provider.calls))
            restored['DBInstanceStatus']='deleting'; provider.calls=[]
            self.assertEqual(result(lambda:module.cleanup(provider,sid,rid))[1]['verdict'],'pending')
            self.assertFalse(provider.calls)

if __name__ == '__main__':
    unittest.main()
