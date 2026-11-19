#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.persistence-controller-reconciliation
#   version: 15
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-11-19"
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
import hashlib
import subprocess
import tempfile
import unittest
import yaml
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

ROOT = Path(__file__).resolve().parents[7]
DEPLOY = ROOT / 'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence'
RUN = ROOT / 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence'
FIXTURE_STACK = None

def load(path):
    spec = importlib.util.spec_from_file_location(path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if path.name == 'change-set-operations.py':
        # Every update test uses a disposable store, including nested real callers.
        directory = FIXTURE_STACK.enter_context(tempfile.TemporaryDirectory(prefix='persistence-update-fixture-'))
        owner = module.Store(Path(directory))
        module.store = lambda _root: owner
    elif path == DEPLOY / 'prepare-candidate/script.py':
        module._UPDATE_OPERATIONS = load(DEPLOY / 'change-set-operations.py')
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
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)
        receipts.RECEIPTS = root / 'proof-receipts'
        receipts.EVIDENCE_CLASS = 'simulated'
        with patch.object(controller, 'proof_receipts', return_value=receipts), patch.object(controller, 'ROOT', root), (patch.object(controller, 'OPERATION_DIAGNOSTICS', root / 'operation-diagnostics') if hasattr(controller, 'OPERATION_DIAGNOSTICS') else contextlib.nullcontext()):
            yield receipts

@contextlib.contextmanager
def temporary_change_sets(controller):
    """Exercise the real immutable protocol outside canonical Git metadata."""
    owner = controller.operations()
    with tempfile.TemporaryDirectory(prefix='persistence-change-set-fixture-') as directory:
        store = owner.Store(Path(directory))
        with patch.object(owner, 'store', return_value=store), patch.object(controller, 'operations', return_value=owner):
            yield store


@contextlib.contextmanager
def temporary_replacements(controller):
    owner = controller.operations()
    with tempfile.TemporaryDirectory(prefix='persistence-replacement-fixture-') as directory:
        store = owner.Store(Path(directory))
        with patch.object(owner, 'store', return_value=store), patch.object(controller, 'operations', return_value=owner):
            yield owner, store


class Provider:
    def __init__(self, responder):
        self.calls = []
        self.responder = responder
        self.change_tokens = {}
        self.execution_token = None
    def aws(self, *parts):
        self.calls.append(parts)
        if parts[1] == 'list-tasks':
            assert not ('--started-by' in parts and ('--desired-status' in parts or '--family' in parts)), 'unsupported AWS filter combination'
        if parts[1] == 'create-change-set' and '--description' in parts:
            self.change_tokens[parts[parts.index('--change-set-name')+1]] = parts[parts.index('--description')+1]
        if parts[1] == 'execute-change-set' and '--client-request-token' in parts:
            self.execution_token = parts[parts.index('--client-request-token')+1]
        if parts[1] == 'describe-stack-events' and self.execution_token:
            return True, {'StackEvents':[{'PhysicalResourceId':'fixture-stack', 'ClientRequestToken':self.execution_token, 'ResourceStatus':'UPDATE_COMPLETE'}]}, 'ok'
        outcome = self.responder(parts)
        if parts[1] == 'describe-stacks' and outcome[0] and isinstance(outcome[1], dict) and self.change_tokens:
            return outcome[0], {**outcome[1], 'Stacks':[{**stack, 'StackId':'fixture-stack'} for stack in outcome[1]['Stacks']]}, outcome[2]
        if parts[1] == 'describe-change-set' and outcome[0] and isinstance(outcome[1], dict):
            token = self.change_tokens.get(parts[parts.index('--change-set-name')+1])
            if token and 'Description' not in outcome[1]:
                return outcome[0], {**outcome[1], 'Description':token}, outcome[2]
        return outcome
    def retained_release(self,receipt):
        return False
    def live_budget(self):
        return True, 'ok'
    def update_owner(self):
        if not hasattr(self, '_updates'):
            self._updates = load(DEPLOY / 'change-set-operations.py')
        return self._updates
    def labelled_update_name(self, name, label):
        return self.update_owner().labelled_name(name, label)
    def begin_update(self, **arguments):
        return self.update_owner().begin_update(ROOT, stack='kanbien-core-platform-core-server-persistence', **arguments)
    def apply_update(self, **arguments):
        # Keep synthetic provider responses, but exercise the actual shared
        # command binding rather than replacing the extracted implementation.
        return self.update_owner().apply_update(self.aws, root=ROOT, stack='kanbien-core-platform-core-server-persistence', **arguments)

class ControllerRegression(unittest.TestCase):
    def setUp(self):
        global FIXTURE_STACK
        FIXTURE_STACK = contextlib.ExitStack()
        self.addCleanup(FIXTURE_STACK.close)
    def test_foundation_checks_and_provider_failures_reach_preparation(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        expected=prepare.INPUTS['foundation_expected']
        outputs={key:'fixture' for key in prepare.REQUIRED_FOUNDATION}
        outputs.update(ClusterArn=expected['cluster_arn'],LogGroupName=expected['log_group'],RepositoryUri=prepare.INPUTS['repository_uri'])
        document={'Stacks':[{'StackStatus':'UPDATE_COMPLETE','Outputs':[{'OutputKey':key,'OutputValue':value} for key,value in outputs.items()]}]}
        with patch.object(prepare,'aws',return_value=(True,document,'ok')) as provider:
            self.assertEqual(prepare.foundation_outputs(),(outputs,'ok'))
            self.assertEqual(json.loads(provider.call_args.args[-1]),{'StackName':prepare.FOUNDATION})
            document['Stacks'][0]['Outputs'].append(copy.deepcopy(document['Stacks'][0]['Outputs'][0]))
            self.assertEqual(prepare.foundation_outputs(),(None,'foundation-outputs-ambiguous'))
        with patch.object(prepare,'aws',return_value=(False,None,'aws-access-denied')) as provider:
            self.assertEqual(prepare.foundation_outputs(),(None,'aws-access-denied'))
            provider.assert_called_once()
        with patch.object(prepare,'aws',return_value=(True,document,'ok')), patch.object(prepare.FOUNDATION_CHECKS,'foundation',side_effect=prepare.FOUNDATION_CHECKS.FoundationFailure('foundation-cluster-mismatch')) as shared:
            self.assertEqual(prepare.foundation_outputs(),(None,'foundation-cluster-mismatch'))
            shared.assert_called_once_with(document,prepare.REQUIRED_FOUNDATION,expected)

    def test_preparation_consumes_shared_image_checks(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        digest='sha256:'+'a'*64; child='sha256:'+'b'*64;receipt={'image_digest':digest}
        manifest={'images':[{'imageId':{'imageDigest':digest},'imageManifest':json.dumps({'mediaType':'application/vnd.oci.image.index.v1+json','manifests':[{'mediaType':'application/vnd.oci.image.manifest.v1+json','digest':child,'platform':{'architecture':'amd64','os':'linux'}}]})}]}
        scan={'repositoryName':prepare.REPOSITORY,'imageId':{'imageDigest':child},'imageScanStatus':{'status':'COMPLETE'},'imageScanFindings':{'findingSeverityCounts':{}}}
        for change,expected in [(None,(True,'ok')),('pending',(False,'ecr-scan-not-complete')),('identity',(False,'ecr-scan-identity-mismatch')),('severity',(False,'ecr-scan-blocked-severity'))]:
            observed=copy.deepcopy(scan)
            if change=='pending':observed['imageScanStatus']['status']='IN_PROGRESS'
            if change=='identity':observed['imageId']['imageDigest']=digest
            if change=='severity':observed['imageScanFindings']['findingSeverityCounts']={'HIGH':1}
            with patch.object(prepare,'aws',side_effect=[(True,manifest,'ok'),(True,observed,'ok')]) as provider:
                self.assertEqual(prepare.candidate_image(receipt),expected)
            self.assertEqual(provider.call_count,2)
            self.assertEqual(json.loads(provider.call_args_list[0].args[-1])['imageIds'],[{'imageDigest':digest}])
            self.assertEqual(json.loads(provider.call_args_list[1].args[-1]),{'repositoryName':prepare.REPOSITORY,'imageId':{'imageDigest':child},'maxResults':1})
        with patch.object(prepare.IMAGE_CHECKS,'check_image',side_effect=prepare.IMAGE_CHECKS.ScanFailure('ecr-scan-findings-invalid')) as shared:
            self.assertEqual(prepare.candidate_image(receipt),(False,'ecr-scan-findings-invalid'))
            shared.assert_called_once_with(prepare.image_observation,prepare.REPOSITORY,digest)
        with patch.object(prepare.IMAGE_CHECKS,'runnable_digest',return_value=child) as shared:
            self.assertEqual(prepare.candidate_runnable_manifest(receipt),(child,'ok'))
            shared.assert_called_once_with(prepare.image_observation,prepare.REPOSITORY,digest)
        with patch.object(prepare,'aws',return_value=(False,None,'aws-access-denied')) as provider:
            self.assertEqual(prepare.candidate_image(receipt),(False,'aws-access-denied'))
            self.assertEqual(provider.call_count,1)

    def test_native_reconciliation_shapes_are_unknown_without_mutations(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        receipt={'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40}
        name='retained-operation'
        for field,value,expected in [('Status',[],'persistence-update-review-status-unobservable'),('ExecutionStatus',{},'persistence-update-execution-status-unobservable')]:
            change={'ChangeSetName':name,'Status':'CREATE_COMPLETE','ExecutionStatus':'EXECUTE_COMPLETE',field:value}
            with patch.object(prepare,'aws',return_value=(True,change,'ok')) as provider:
                self.assertEqual(prepare.observe_update(name,{},lambda _change:True),('uncertain',expected))
                self.assertEqual(provider.call_count,1)
        with patch.object(prepare,'aws',return_value=(True,{'ChangeSetName':name,'Status':'CREATE_COMPLETE'},'ok')) as provider:
            self.assertEqual(prepare.observe_update(name,{},lambda _change:(_ for _ in ()).throw(ValueError('private-native-canary'))),('uncertain','persistence-update-review-unobservable'))
            self.assertEqual(provider.call_count,1)
        for stack in [{'StackStatus':[],'Parameters':[]},{'StackStatus':'UPDATE_COMPLETE','Parameters':[{'ParameterKey':[],'ParameterValue':'private-native-canary'}]}]:
            provider=Provider(lambda parts:(False,None,'aws-resource-missing') if parts[1]=='describe-change-set' else (True,{'Stacks':[stack]},'ok'))
            with patch.object(prepare,'aws',side_effect=provider.aws):
                outcome,code=prepare.observe_update(name,{},lambda _change:(_ for _ in ()).throw(AssertionError('missing review is not replayed')))
            self.assertEqual(outcome,'uncertain');self.assertIn(code,{'persistence-update-stack-status-unobservable','persistence-update-stack-parameters-unobservable'})
            self.assertEqual([parts[1] for parts in provider.calls],['describe-change-set','describe-stacks'])
        manifest={'images':[{'imageId':{'imageDigest':receipt['image_digest']},'imageManifest':json.dumps({'mediaType':'application/vnd.oci.image.manifest.v1+json'})}]}
        scan={'repositoryName':prepare.REPOSITORY,'imageId':{'imageDigest':receipt['image_digest']},'imageScanStatus':None}
        with patch.object(prepare,'aws',side_effect=[(True,manifest,'ok'),(True,scan,'ok')]):
            self.assertEqual(prepare.candidate_image(receipt),(False,'ecr-scan-not-complete'))
        with patch.object(prepare,'aws',return_value=(True,{'Budget':{**prepare.INPUTS['budget'],'BudgetLimit':{'Amount':'sNaN','Unit':'USD'}}},'ok')):
            self.assertEqual(prepare.live_budget(),(False,'foundation-budget-amount-invalid'))
        create=load(DEPLOY/'create-change-set/script.py')
        for field,value,code in [('Status',[],'persistence-change-set-status-unobservable'),('Parameters',[{'ParameterKey':[],'ParameterValue':'private-native-canary'}],'persistence-change-set-parameters-unobservable')]:
            provider=Provider(lambda _parts:(True,{'ChangeSetName':name,'Status':'CREATE_COMPLETE','Parameters':[],field:value},'ok'));provider.change_name_matches=prepare.change_name_matches
            status,report,_=result(lambda:create.reconcile(provider,name,receipt))
            self.assertEqual((status,report['verdict'],report['findings']),(1,'uncertain',[{'code':code}]))
            self.assertEqual(len(provider.calls),1);self.assertNotIn('private-native-canary',json.dumps(report))
        retire=load(DEPLOY/'retire-failed-candidate/script.py')
        with patch.object(retire,'aws',side_effect=[(True,{'Stacks':[{'StackStatus':'ROLLBACK_FAILED'}]},'ok'),(True,{'StackResources':1},'ok')]) as provider:
            self.assertEqual(retire.failed_candidate_database(),(False,'persistence-failed-candidate-resources-unobservable'));self.assertEqual(provider.call_count,2)
        for checker,unlocked in [(retire.protected_target_database,False),(retire.protected_target_database_after_unlock,True)]:
            instance={'DBInstanceIdentifier':retire.DATABASE,'PubliclyAccessible':False,'DeletionProtection':not unlocked,'DBInstanceStatus':'available','DBInstanceArn':'fixture-arn'}
            with patch.object(retire,'aws',side_effect=[(True,{'DBInstances':[instance]},'ok'),(True,{'TagList':1},'ok')]) as provider:
                self.assertEqual(checker(),(False,'persistence-failed-candidate-tags-unobservable'));self.assertEqual(provider.call_count,2)

    def test_create_parameter_file_failures_preserve_submission_boundary(self):
        module=load(DEPLOY/'create-change-set/script.py')
        receipt={'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40}
        provider=SimpleNamespace(validate_receipt=lambda _path:receipt,declaration_covered=lambda:True,foundation_outputs=lambda:({},'ok'),infrastructure_parameters=lambda _:({},'ok'),candidate_image=lambda _:(True,'ok'),live_budget=lambda:(True,'ok'),candidate_parameters=lambda *args:{'ImageDigest':receipt['image_digest']})
        class CleanupFailure(io.StringIO):
            name='fixture-only.json'
            def __exit__(self,*args):super().__exit__(*args);raise OSError('private-native-canary')
        for cleanup in (False,True):
            calls=[]
            def aws(*parts):
                calls.append(parts[1]);return (False,None,'aws-resource-missing') if parts[1]=='describe-stacks' else (True,{},'ok')
            provider.aws=aws
            temporary=patch.object(module.tempfile,'NamedTemporaryFile',return_value=CleanupFailure()) if cleanup else patch.object(module.tempfile,'NamedTemporaryFile',side_effect=OSError('private-native-canary'))
            with temporary_change_sets(module),temporary,patch.object(module,'controls',return_value=provider),patch.object(module,'diagnostic_path_is_governed',return_value=True),patch.object(module,'diagnostics_ready',return_value=True),patch.object(module,'package_gates',return_value=True),patch.object(sys,'argv',['fixture','--receipt','fixture']):
                status,report,_=result(module.main)
            self.assertEqual((status,report['verdict']),(1,'uncertain' if cleanup else 'blocked'))
            self.assertEqual(calls,['describe-stacks','create-change-set'] if cleanup else ['describe-stacks'])
            self.assertEqual(report['findings'],[{'code':'persistence-submission-or-parameter-cleanup-unavailable' if cleanup else 'persistence-parameter-file-unavailable'}]);self.assertNotIn('private-native-canary',json.dumps(report))

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

    def test_baseline_change_set_actual_callers_reserve_and_never_replay(self):
        receipt = {'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40}
        name = 'kanbien-core-platform-persistence-create-'+'a'*12
        stack_id = 'arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-core-platform-core-server-persistence/fixture-id'
        for command, phase in [('create-change-set','create'),('deploy-candidate','execute')]:
            for lost in (False, True):
                module = load(DEPLOY/command/'script.py')
                expected = {'ImageDigest':receipt['image_digest'],'SupportImageDigest':receipt['image_digest'],
                            'RestoreVerifierImageDigest':receipt['image_digest'],'SourceRevision':receipt['source_revision'],
                            'PrivateSubnetIds':'PRIVATE_PARAMETER_CANARY'}
                state = {'submitted':False,'identity':None,'foreign':False}
                calls = []
                def aws(*parts):
                    calls.append(parts)
                    operation = parts[1]
                    if operation in ('create-change-set','execute-change-set'):
                        records = list(store.root.glob('*.json'))
                        self.assertEqual(len(records),1)
                        retained = json.loads(records[0].read_text())
                        self.assertEqual(records[0].stat().st_mode & 0o777,0o600)
                        token = '--client-token' if phase == 'create' else '--client-request-token'
                        self.assertEqual(parts[parts.index(token)+1],retained['operation_id'])
                        self.assertNotIn('PRIVATE_PARAMETER_CANARY',records[0].read_text())
                        state.update(submitted=True,identity=retained['operation_id'])
                        if phase == 'create':
                            self.assertEqual(parts[parts.index('--description')+1],state['identity'])
                            self.assertIn('CAPABILITY_NAMED_IAM',parts)
                            self.assertNotIn('--on-stack-failure',parts)
                        else: self.assertNotIn('--disable-rollback',parts)
                        return (False,None,'aws-command-timeout') if lost else (True,{},'ok')
                    if operation == 'describe-stacks':
                        if phase == 'create' and not state['submitted']: return False,None,'aws-resource-missing'
                        return True,{'Stacks':[{'StackId':stack_id,'StackStatus':'CREATE_COMPLETE' if phase == 'execute' and state['submitted'] else 'REVIEW_IN_PROGRESS',
                                               'Parameters':[{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()]}]},'ok'
                    if operation == 'describe-change-set':
                        return True,{'ChangeSetName':name,'Description':'foreign' if state['foreign'] else state['identity'],
                            'Status':'CREATE_COMPLETE','ExecutionStatus':'EXECUTE_COMPLETE' if phase == 'execute' and state['submitted'] else 'AVAILABLE',
                            'ChangeSetType':'CREATE','Parameters':[{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()],
                            'Changes':[{'ResourceChange':{'ResourceType':'AWS::RDS::DBInstance'}}]},'ok'
                    if operation == 'describe-stack-events':
                        return True,{'StackEvents':[{'PhysicalResourceId':stack_id,'ClientRequestToken':'foreign' if state['foreign'] else state['identity']}]},'ok'
                    raise AssertionError(parts)
                provider = SimpleNamespace(validate_receipt=lambda _path:receipt,declaration_covered=lambda:True,
                    foundation_outputs=lambda:({},'ok'),infrastructure_parameters=lambda _:({},'ok'),
                    candidate_image=lambda _:(True,'ok'),live_budget=lambda:(True,'ok'),candidate_parameters=lambda *args:expected,
                    change_name_matches=lambda actual,wanted:actual == wanted,aws=aws)
                argv = ['fixture','--receipt','fixture'] + (['--approved-change-set',name] if phase == 'execute' else [])
                with temporary_change_sets(module) as store, contextlib.ExitStack() as fixtures:
                    fixtures.enter_context(patch.object(module,'controls',return_value=provider))
                    fixtures.enter_context(patch.object(sys,'argv',argv))
                    if phase == 'create':
                        for key in ('diagnostic_path_is_governed','diagnostics_ready','package_gates'):
                            fixtures.enter_context(patch.object(module,key,return_value=True))
                        fixtures.enter_context(patch.object(module,'retain_diagnostic',return_value=None))
                    first = result(module.main)[1]
                    successful = 'created-awaiting-review' if phase == 'create' else 'deployed-awaiting-migration'
                    self.assertEqual(first['verdict'],'uncertain' if lost else successful)
                    retained = next(store.root.glob('*.json')).read_bytes()
                    self.assertEqual(result(module.main)[1]['verdict'],successful)
                    self.assertEqual(next(store.root.glob('*.json')).read_bytes(),retained)
                    state['foreign'] = True
                    self.assertIn(result(module.main)[1]['verdict'],('blocked','uncertain'))
                    state['foreign'] = False
                    expected['PrivateSubnetIds'] = 'changed-private-input'
                    changed = result(module.main)[1]
                    self.assertEqual(changed['findings'],[{'code':'persistence-change-set-reservation-mismatch'}])
                    self.assertEqual(sum(parts[1] in ('create-change-set','execute-change-set') for parts in calls),1)
    def test_all_update_entrypoints_use_shared_sequence_and_keep_guards(self):
        commands = (
            ('transition-qualified-release', 'transitioned', ['--operation', 'update']),
            ('apply-private-verifier-route-update', 'updated', []),
            ('apply-database-permission-surface', 'updated-awaiting-administration', ['--rollback-receipt', 'prior', '--rollback-compatibility-id', 'fixture']),
            ('apply-observability-mvp-surface', 'updated-awaiting-observability-proof', ['--collector-receipt', 'collector', '--alert-email', 'private-canary@example.invalid']),
            ('apply-restoration-verifier-surface', 'applied', ['--mode', 'image']),
        )
        for command, success, extra in commands:
            for scenario in ('success', 'create-timeout', 'execute-timeout', 'unknown', 'resource-rejected', 'parameter-rejected', 'pending', 'failed'):
                with self.subTest(command=command, scenario=scenario), contextlib.ExitStack() as contexts:
                    module = load(DEPLOY / command / 'script.py')
                    prepare = load(DEPLOY / 'prepare-candidate/script.py')
                    owner = load(DEPLOY / 'change-set-operations.py')
                    candidate = {'image_digest': 'sha256:'+'a'*64, 'source_revision': 'a'*40}
                    collector = {**candidate, 'image_digest': 'sha256:'+'c'*64}
                    previous = {**candidate, 'image_digest': 'sha256:'+'b'*64}
                    foundation = {'RepositoryUri': prepare.INPUTS['repository_uri']}
                    current = {**prepare.candidate_parameters(foundation, {}, previous), 'EnableObservability': 'false',
                               'ObservabilityCollectorImage': 'old-collector', 'ObservabilityAlertEmail': '****', 'UnownedSetting': 'retained'}
                    state = {'parameters': None, 'executed': False, 'name': None, 'description': None}
                    if command in ('apply-database-permission-surface', 'apply-observability-mvp-surface'):
                        changes = [{'ResourceChange': {'LogicalResourceId': logical, 'ResourceType': kind, 'Action': action}}
                                   for action, collection in (('Add', module.ADDED), ('Modify', module.MODIFIED)) for logical, kind in collection.items()]
                    elif command == 'apply-private-verifier-route-update':
                        changes = [{'ResourceChange': {'LogicalResourceId': 'VerifierEgressToServer', 'ResourceType': 'AWS::EC2::SecurityGroupEgress', 'Action': 'Add'}}]
                    else:
                        changes = [{'ResourceChange': {'LogicalResourceId': 'CoreServerPersistenceRestorationVerifierTaskDefinition', 'ResourceType': 'AWS::ECS::TaskDefinition', 'Action': 'Modify'}}]
                    if scenario == 'resource-rejected':
                        changes.append({'ResourceChange': {'LogicalResourceId': 'UnrelatedBucket', 'ResourceType': 'AWS::S3::Bucket', 'Action': 'Add'}})
                    def response(parts):
                        operation = parts[1]
                        if operation == 'describe-stacks':
                            values = state['parameters'] if state['executed'] else current
                            status = ('UPDATE_IN_PROGRESS' if scenario=='pending' else 'UPDATE_ROLLBACK_COMPLETE') if state['executed'] and scenario in ('pending','failed') else 'UPDATE_COMPLETE'
                            return True, {'Stacks': [{'StackStatus': status, 'Parameters': [{'ParameterKey': k, 'ParameterValue': v} for k, v in values.items()]}]}, 'ok'
                        if operation == 'describe-services':
                            return True, {'services': [{'status': 'ACTIVE', 'desiredCount': 1, 'runningCount': 1}]}, 'ok'
                        if operation == 'describe-change-set':
                            if scenario == 'unknown': return False, None, 'aws-command-timeout'
                            if state['parameters'] is None: return False, None, 'aws-resource-missing'
                            values = {**state['parameters']}
                            if scenario == 'parameter-rejected': values['UnownedSetting'] = 'private-parameter-canary'
                            return True, {'ChangeSetName': state['name'], 'Description': state['description'], 'Status': 'CREATE_COMPLETE', 'ChangeSetType': 'UPDATE',
                                          'ExecutionStatus': 'EXECUTE_COMPLETE' if state['executed'] else 'AVAILABLE', 'Changes': changes,
                                          'Parameters': [{'ParameterKey': k, 'ParameterValue': v} for k, v in values.items()]}, 'ok'
                        if operation == 'create-change-set':
                            state['name'] = parts[parts.index('--change-set-name')+1]
                            state['description'] = parts[parts.index('--description')+1]
                            self.assertEqual(state['description'], parts[parts.index('--client-token')+1])
                            self.assertIsNotNone(owner.store(ROOT).read('update-create', request_seen[0]))
                            submitted = json.loads(Path(parts[parts.index('--parameters')+1].removeprefix('file://')).read_text())
                            state['parameters'] = {**current, **{item['ParameterKey']: current[item['ParameterKey']] if item.get('UsePreviousValue') else item['ParameterValue'] for item in submitted}}
                            if command == 'apply-observability-mvp-surface':
                                self.assertEqual(state['parameters']['ObservabilityAlertEmail'], 'private-canary@example.invalid')
                                state['parameters']['ObservabilityAlertEmail'] = '****'
                            self.assertEqual('--use-previous-template' in parts, command in ('transition-qualified-release', 'apply-restoration-verifier-surface'))
                            self.assertIn('CAPABILITY_NAMED_IAM', parts)
                            return (False, None, 'aws-command-timeout') if scenario == 'create-timeout' else (True, {}, 'ok')
                        if operation == 'execute-change-set':
                            reservation = owner.store(ROOT).read('update-execute', request_seen[0])
                            self.assertEqual(parts[parts.index('--client-request-token')+1], reservation['operation_id'])
                            state['executed'] = True
                            return (False, None, 'aws-command-timeout') if scenario == 'execute-timeout' else (True, {}, 'ok')
                        raise AssertionError(operation)
                    provider = Provider(response)
                    contexts.enter_context(patch.object(prepare, 'aws', provider.aws))
                    contexts.enter_context(patch.object(prepare, '_UPDATE_OPERATIONS', owner))
                    for key, value in {'validate_receipt': candidate, 'retained_release': False, 'rollback_compatibility': True,
                                       'declaration_covered': True, 'live_budget': (True, 'ok'), 'foundation_outputs': (foundation, 'ok'),
                                       'infrastructure_parameters': ({}, 'ok'), 'candidate_image': (True, 'ok')}.items():
                        contexts.enter_context(patch.object(prepare, key, return_value=value))
                    create = SimpleNamespace(package_gates=lambda _path: True)
                    loader = 'module' if command == 'apply-private-verifier-route-update' else 'load'
                    loader_mock = contexts.enter_context(patch.object(module, loader, side_effect=[prepare] if command == 'apply-restoration-verifier-surface' else [prepare, create]))
                    contexts.enter_context(patch.object(module.time, 'sleep'))
                    if command == 'transition-qualified-release':
                        contexts.enter_context(patch.object(module, 'retain_failure_diagnostic', return_value=None))
                    if command == 'apply-observability-mvp-surface':
                        contexts.enter_context(patch.object(module, 'receipt', side_effect=lambda path, **_expected: collector if path.name == 'collector' else candidate))
                        contexts.enter_context(patch.object(module, 'collector_image_available', return_value=True))
                        contexts.enter_context(patch.object(subprocess, 'run', return_value=SimpleNamespace(returncode=0)))
                    contexts.enter_context(patch.object(sys, 'argv', ['fixture', '--server-receipt' if command == 'apply-observability-mvp-surface' else '--receipt', 'candidate', *extra, '--operation-label', 'fixture']))
                    request_seen = []
                    original_begin = owner.begin_update
                    def begin(*args, **kwargs):
                        value = original_begin(*args, **kwargs)
                        request_seen[:] = [value[0]]
                        return value
                    contexts.enter_context(patch.object(owner, 'begin_update', side_effect=begin))
                    shared = contexts.enter_context(patch.object(owner.CHANGE_SETS, 'prepare', wraps=owner.CHANGE_SETS.prepare))
                    execute = contexts.enter_context(patch.object(owner.CHANGE_SETS, 'execute', wraps=owner.CHANGE_SETS.execute))
                    selection = contexts.enter_context(patch.object(owner.CHANGE_SETS, 'retained_execution', wraps=owner.CHANGE_SETS.retained_execution))
                    status, report, _ = result(module.main)
                    self.assertEqual(selection.call_count, 2)  # Admission and submission recheck use the same owner.
                    self.assertEqual(shared.call_count, 1)
                    expected = success if scenario == 'success' else scenario if scenario in ('pending','failed') else 'uncertain' if scenario in ('create-timeout', 'execute-timeout') else 'blocked'
                    self.assertEqual(report['verdict'], expected, report)
                    self.assertEqual(status, 0 if scenario == 'success' else 1)
                    operations = [parts[1] for parts in provider.calls]
                    self.assertEqual(operations.count('create-change-set'), 0 if scenario == 'unknown' else 1)
                    self.assertEqual(operations.count('execute-change-set'), 1 if scenario in ('success', 'execute-timeout', 'pending', 'failed') else 0)
                    self.assertEqual(execute.call_count, 1 if scenario in ('success', 'execute-timeout', 'pending', 'failed') else 0)
                    self.assertNotIn('private-canary', json.dumps(report))
                    self.assertNotIn('private-parameter-canary', json.dumps(report))
                    if scenario in ('success', 'create-timeout', 'execute-timeout', 'pending', 'failed'):
                        before = len(provider.calls)
                        loader_mock.side_effect = [prepare] if command == 'apply-restoration-verifier-surface' else [prepare, create]
                        # Ordinary invocation resumes; an executed attempt must
                        # bypass gates demanding a healthy predecessor.
                        if scenario != 'create-timeout':
                            contexts.enter_context(patch.object(prepare, 'live_budget', side_effect=AssertionError('execution retry entered fresh gates')))
                        selection.reset_mock()
                        resumed = result(module.main)[1]
                        self.assertEqual(selection.call_count, 2 if scenario == 'create-timeout' else 1)
                        self.assertEqual(resumed['verdict'], scenario if scenario in ('pending','failed') else success)
                        self.assertEqual(sum(parts[1]=='create-change-set' for parts in provider.calls), 1)
                        self.assertEqual(sum(parts[1]=='execute-change-set' for parts in provider.calls), 1)
                        if scenario != 'create-timeout':
                            self.assertTrue(all(parts[1].startswith('describe-') for parts in provider.calls[before:]))

    def test_shared_update_parameter_transport_failures_and_renamed_binding(self):
        owner = load(DEPLOY / 'change-set-operations.py')
        class CleanupFailure(io.StringIO):
            name = 'fixture-only.json'
            def __exit__(self, *args):
                super().__exit__(*args)
                raise OSError('private-file-canary')
        for mode in ('before', 'cleanup', 'provider-and-cleanup', 'renamed'):
            with self.subTest(mode=mode), contextlib.ExitStack() as contexts:
                calls = []
                state = {}
                def aws(*parts):
                    calls.append(parts)
                    self.assertEqual(parts[parts.index('--stack-name')+1], 'renamed-private-workload')
                    if parts[1] == 'describe-change-set':
                        return (True, state, 'ok') if state else (False, None, 'aws-resource-missing')
                    if parts[1] == 'create-change-set':
                        state.update(Description=parts[parts.index('--description')+1], ExecutionStatus='AVAILABLE')
                    if mode == 'provider-and-cleanup': return False, None, 'aws-command-timeout'
                    return True, {}, 'ok'
                if mode == 'before': contexts.enter_context(patch.object(owner.tempfile, 'NamedTemporaryFile', side_effect=OSError('private-file-canary')))
                elif mode != 'renamed': contexts.enter_context(patch.object(owner.tempfile, 'NamedTemporaryFile', return_value=CleanupFailure()))
                request = {'stack':'renamed-private-workload','change_set':'renamed-review-'+mode,'inputs_sha256':'a'*64}
                result_value = owner.apply_update(aws, root=ROOT, stack=request['stack'], name=request['change_set'], request=request, parameters=[{'ParameterKey': 'PrivateValue', 'ParameterValue': 'private-file-canary'}],
                                                 template_arguments=('--use-previous-template',), review=lambda *_: (state, 'ok'),
                                                 admit=lambda _: None, observe=lambda _reservation: ('complete', 'observed'), failure=lambda verdict, code: (verdict, code))
                expected = {'before': ('blocked', 'persistence-update-parameter-file-unavailable'),
                            'cleanup': ('uncertain', 'persistence-update-parameter-file-outcome-uncertain'),
                            'provider-and-cleanup': ('uncertain', 'aws-command-timeout'), 'renamed': ('complete', 'observed')}[mode]
                self.assertEqual(result_value, expected)
                self.assertEqual(sum(parts[1]=='create-change-set' for parts in calls), 0 if mode=='before' else 1)
                self.assertEqual(sum(parts[1]=='execute-change-set' for parts in calls), 1 if mode=='renamed' else 0)
                self.assertNotIn('private-file-canary', repr(result_value))

    def test_reserved_updates_bind_intent_and_never_replay_interrupted_submissions(self):
        for scenario in ('missing-create', 'before-create', 'before-execute', 'foreign', 'changed-intent', 'changed-source', 'missing-source', 'changed-receipt', 'orphan', 'corrupt', 'new-label', 'delayed', 'expired-observation'):
            with self.subTest(scenario=scenario):
                owner = load(DEPLOY/'change-set-operations.py')
                store = owner.store(ROOT)
                calls, state = [], {}
                receipt = {'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40}
                intent = dict(stack='different-workload', name='review-one', receipt=receipt,
                              controller=__file__, template=DEPLOY/'change-set-operations.py',
                              settings={'private':'sensitive-intent-canary'})
                def observation(reservation):
                    if scenario=='expired-observation' and not state.get('authenticated'):
                        prepare = load(DEPLOY/'prepare-candidate/script.py')
                        with patch.object(prepare, 'aws', return_value=(False, None, 'aws-credentials-expired')) as read:
                            result = prepare.observe_update(intent['name'], {}, lambda value: value, reservation=reservation)
                            self.assertEqual(read.call_count, 1)
                            self.assertEqual(read.call_args.args[:2], ('cloudformation', 'describe-change-set'))
                            return result
                    return ('observed', reservation['phase'])
                failure = lambda verdict, code: (verdict, code)
                def begin(**overrides):
                    return owner.begin_update(ROOT, **{**intent, **overrides}, observe=observation, failure=failure)
                request, resumed = begin()
                self.assertIsNone(resumed)
                def aws(*parts):
                    calls.append(parts)
                    if parts[1]=='describe-change-set':
                        if scenario=='foreign': return True, {'Description':'unowned'}, 'ok'
                        return (True, state, 'ok') if state else (False, None, 'aws-resource-missing')
                    if parts[1]=='create-change-set':
                        self.assertIsNotNone(store.read('update-create', request))
                        if scenario=='missing-create': return False, None, 'aws-command-timeout'
                        state.update(Description=parts[parts.index('--description')+1], ExecutionStatus='AVAILABLE')
                        return True, {}, 'ok'
                    if parts[1]=='execute-change-set':
                        token=store.read('update-execute', request)['operation_id']
                        self.assertEqual(parts[parts.index('--client-request-token')+1], token)
                        return True, {}, 'ok'
                    raise AssertionError(parts[1])
                def apply():
                    return owner.apply_update(aws, root=ROOT, stack=intent['stack'], name=request['change_set'], request=request,
                        parameters=[], template_arguments=('--use-previous-template',),
                        review=lambda value,_: (None if scenario=='delayed' and not state.get('ready') else value, 'ok'),
                        admit=lambda _:None, observe=observation, failure=failure)
                if scenario in ('before-create','before-execute'):
                    reserve = store.reserve
                    interrupted = 'update-create' if scenario=='before-create' else 'update-execute'
                    def interrupt(phase, value):
                        result = reserve(phase, value)
                        if phase==interrupted: raise KeyboardInterrupt()
                        return result
                    with patch.object(store,'reserve',side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
                        apply()
                else:
                    first=apply()
                    if scenario=='foreign': self.assertEqual(first, ('blocked','persistence-update-unowned-change-set'))
                    if scenario=='missing-create': self.assertEqual(first, ('uncertain','aws-command-timeout'))
                    if scenario=='expired-observation':
                        self.assertEqual(first, ('uncertain','aws-credentials-expired'))
                        retained = {path:path.read_bytes() for path in store.root.glob('*.json')}
                        self.assertIsNotNone(store.read('update-execute', request))
                        state['authenticated']=True
                before = len(calls)
                if scenario=='changed-intent':
                    self.assertEqual(begin(settings={'private':'different'})[1], ('blocked','persistence-change-set-reservation-mismatch'))
                elif scenario=='changed-receipt':
                    self.assertEqual(begin(receipt={**receipt,'source_revision':'b'*40})[1], ('blocked','persistence-change-set-reservation-mismatch'))
                elif scenario=='changed-source':
                    original=Path.read_bytes
                    with patch.object(Path,'read_bytes',lambda path: b'changed-controller' if path==Path(__file__) else original(path)):
                        self.assertEqual(begin()[1], ('blocked','persistence-change-set-reservation-mismatch'))
                elif scenario=='missing-source':
                    self.assertEqual(begin(controller=store.root/'absent.py')[1], ('blocked','persistence-change-set-inputs-unavailable'))
                elif scenario=='orphan':
                    store.path_for('update-create',request).unlink()
                    self.assertEqual(begin()[1], ('blocked','persistence-change-set-reservation-mismatch'))
                    self.assertEqual(apply(), ('blocked','persistence-change-set-reservation-mismatch'))
                elif scenario=='corrupt':
                    store.path_for('update-execute',request).write_text('{malformed-sensitive-intent-canary')
                    self.assertEqual(begin()[1], ('blocked','persistence-change-set-reservation-unavailable'))
                elif scenario=='new-label':
                    label=owner.labelled_name(intent['name'],'next-release')
                    request,resumed=begin(name=label)
                    self.assertIsNone(resumed)
                    state.clear()
                    self.assertEqual(apply(), ('observed','update-execute'))
                    self.assertIsNone(owner.labelled_name(intent['name'],'../private'))
                else:
                    request,resumed=begin()
                    if resumed is None:
                        if scenario=='delayed': state['ready']=True
                        resumed=apply()
                    expected = ('observed','update-execute') if scenario in ('before-execute','delayed','expired-observation') else (
                        ('blocked','persistence-update-change-set-lineage-not-confirmed') if scenario=='foreign'
                        else ('uncertain','aws-resource-missing'))
                    self.assertEqual(resumed, expected)
                mutations=[parts[1] for parts in calls if parts[1] in ('create-change-set','execute-change-set')]
                if scenario=='new-label': self.assertEqual(mutations, ['create-change-set','execute-change-set']*2)
                elif scenario=='delayed': self.assertEqual(mutations, ['create-change-set','execute-change-set'])
                else: self.assertTrue(all(parts[1].startswith('describe-') for parts in calls[before:]))
                if scenario=='expired-observation':
                    self.assertEqual(mutations, ['create-change-set','execute-change-set'])
                    self.assertTrue(all(path.read_bytes()==raw for path,raw in retained.items()))
                if scenario!='corrupt':
                    for path in store.root.glob('*.json'):
                        self.assertNotIn('sensitive-intent-canary',path.read_text())

    def test_retained_execution_pair_is_read_only_and_preserves_failures(self):
        owner = load(DEPLOY / 'change-set-operations.py')
        store = owner.store(ROOT)
        request = {'stack': 'another-workload', 'change_set': 'another-review', 'inputs_sha256': 'a' * 64}
        def select():
            return owner.CHANGE_SETS.retained_execution(store,
                preparation_phase='update-create', preparation_request=request,
                execution_phase='update-execute', execution_request=request,
                missing_preparation=lambda: owner.OperationFailure('blocked', 'persistence-change-set-reservation-mismatch'))
        self.assertIsNone(select())
        self.assertEqual(list(store.root.glob('*.json')), [])
        prepared, _ = store.reserve('update-create', request)
        self.assertIsNone(select())
        executed, _ = store.reserve('update-execute', request)
        original = {path: path.read_bytes() for path in store.root.glob('*.json')}
        with patch.object(store, 'reserve', side_effect=AssertionError('selection must not reserve')):
            self.assertEqual(select(), executed)
            self.assertTrue(all(path.read_bytes() == raw for path, raw in original.items()))
            failure = owner.OperationFailure('blocked', 'persistence-change-set-reservation-unavailable')
            with patch.object(store, 'read', side_effect=failure), self.assertRaises(owner.OperationFailure) as caught:
                select()
            self.assertIs(caught.exception, failure)
            with patch.object(store, 'read', side_effect=[prepared, failure]), self.assertRaises(owner.OperationFailure) as caught:
                select()
            self.assertIs(caught.exception, failure)
            with patch.object(store, 'read', side_effect=[prepared, executed]):
                self.assertIs(select(), executed)

    def test_reserved_update_completion_requires_its_own_terminal_event(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        params={'ImageDigest':'sha256:'+'a'*64}
        reservation={'phase':'update-execute','operation_id':'kp-'+'a'*32}
        event={'PhysicalResourceId':'fixture-stack','ClientRequestToken':reservation['operation_id'],'ResourceStatus':'UPDATE_COMPLETE'}
        stack={'StackId':'fixture-stack','StackStatus':'UPDATE_COMPLETE','Parameters':[{'ParameterKey':k,'ParameterValue':v} for k,v in params.items()]}
        for events, phase, expected in (
            ([event],'update-execute','complete'),
            ([], 'update-execute','uncertain'),
            ([{**event,'ClientRequestToken':'another-operation'}],'update-execute','uncertain'),
            ([{**event,'PhysicalResourceId':'another-stack'}],'update-execute','uncertain'),
            ([{**event,'ResourceStatus':'UPDATE_IN_PROGRESS'}],'update-execute','uncertain'),
            ([event],'update-create','uncertain'),
        ):
            def aws(*parts):
                if parts[1]=='describe-change-set':return False,None,'aws-resource-missing'
                if parts[1]=='describe-stacks':return True,{'Stacks':[stack]},'ok'
                if parts[1]=='describe-stack-events':return True,{'StackEvents':events},'ok'
                raise AssertionError('unexpected mutation')
            with patch.object(prepare,'aws',side_effect=aws):
                result=prepare.observe_update('named-update',params,lambda _:True,reservation={**reservation,'phase':phase})
                self.assertEqual(result[0],expected)
                if expected=='uncertain':self.assertEqual(result[1],'persistence-update-execution-lineage-not-confirmed')
                # Historical records retain their separate read-only contract.
                self.assertEqual(prepare.observe_update('named-update',params,lambda _:True)[0],'complete')

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

    def test_restoration_verifier_image_mode_is_exact_and_preserves_parameters(self):
        module=load(DEPLOY/'apply-restoration-verifier-surface/script.py')
        predecessor='sha256:'+'a'*64; digest='sha256:'+'b'*64
        state={'Parameters':[
            {'ParameterKey':'ImageDigest','ParameterValue':predecessor},
            {'ParameterKey':'SupportImageDigest','ParameterValue':predecessor},
            {'ParameterKey':'RestoreVerifierImageDigest','ParameterValue':predecessor},
            {'ParameterKey':'SourceRevision','ParameterValue':'a'*40},
            {'ParameterKey':'EnableObservability','ParameterValue':'true'},
        ]}
        expected=module.expected_parameters(state,digest)
        name=module.change_name(digest,'image')
        good={'ChangeSetName':name,'Status':'CREATE_COMPLETE','ExecutionStatus':'AVAILABLE','ChangeSetType':'UPDATE','Parameters':[{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()],'Changes':[{'ResourceChange':{'LogicalResourceId':'CoreServerPersistenceRestorationVerifierTaskDefinition','Action':'Modify','ResourceType':'AWS::ECS::TaskDefinition'}}]}
        self.assertTrue(module.review(good,name,digest,'image',expected))
        self.assertEqual(name,'kanbien-core-platform-persistence-restore-image-'+digest[7:19])
        for mutation in ('add','extra','wrong-parameter','missing-parameter','duplicate-parameter'):
            candidate=copy.deepcopy(good)
            if mutation=='add': candidate['Changes'][0]['ResourceChange']['Action']='Add'
            if mutation=='extra': candidate['Changes'].append({'ResourceChange':{'LogicalResourceId':'CoreServerPersistenceTaskDefinition','Action':'Modify','ResourceType':'AWS::ECS::TaskDefinition'}})
            if mutation=='wrong-parameter': next(item for item in candidate['Parameters'] if item['ParameterKey']=='EnableObservability')['ParameterValue']='false'
            if mutation=='missing-parameter': candidate['Parameters']=candidate['Parameters'][:-1]
            if mutation=='duplicate-parameter': candidate['Parameters'].append(copy.deepcopy(candidate['Parameters'][0]))
            self.assertFalse(module.review(candidate,name,digest,'image',expected),mutation)

    def test_restoration_verifier_image_uses_deployed_template_and_discards_only_rejected_review(self):
        module=load(DEPLOY/'apply-restoration-verifier-surface/script.py')
        previous='sha256:'+'a'*64; digest='sha256:'+'b'*64
        state={'StackStatus':'UPDATE_COMPLETE','Parameters':[
            {'ParameterKey':'ImageDigest','ParameterValue':previous},
            {'ParameterKey':'RestoreVerifierImageDigest','ParameterValue':previous},
            {'ParameterKey':'SourceRevision','ParameterValue':'a'*40},
        ]}
        expected=module.expected_parameters(state,digest); name=module.change_name(digest,'image')
        rejected={'ChangeSetName':name,'Status':'CREATE_COMPLETE','ExecutionStatus':'AVAILABLE','ChangeSetType':'UPDATE','Parameters':[{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()],'Changes':[{'ResourceChange':{'LogicalResourceId':'PersistenceDatabase','Action':'Modify','ResourceType':'AWS::RDS::DBInstance'}}]}
        calls={'describes':0}
        def response(parts):
            if parts[1]=='describe-change-set':
                calls['describes']+=1
                return (True,rejected,'ok') if calls['describes']==1 else (False,None,'aws-resource-missing')
            if parts[1]=='delete-change-set': return True,{},'ok'
            raise AssertionError(parts)
        provider=Provider(response)
        report=result(lambda:module.discard_rejected_image_review(provider,name,digest,expected))[1]
        self.assertEqual(report['verdict'],'discarded')
        self.assertEqual([parts[1] for parts in provider.calls],['describe-change-set','delete-change-set','describe-change-set'])

        provider=Provider(lambda parts:(True,{**rejected,'Changes':[{'ResourceChange':{'LogicalResourceId':'CoreServerPersistenceRestorationVerifierTaskDefinition','Action':'Modify','ResourceType':'AWS::ECS::TaskDefinition'}}]},'ok') if parts[1]=='describe-change-set' else (_ for _ in ()).throw(AssertionError('must not delete review accepted by the guard')))
        self.assertEqual(result(lambda:module.discard_rejected_image_review(provider,name,digest,expected))[1]['verdict'],'blocked')

        provider=Provider(lambda parts:(True,{'Stacks':[state]},'ok') if parts[1]=='describe-stacks' else (False,None,'aws-resource-missing') if parts[1]=='describe-change-set' else (False,None,'aws-command-timeout') if parts[1]=='create-change-set' else (_ for _ in ()).throw(AssertionError(parts)))
        provider.validate_receipt=lambda path:{'image_digest':digest,'source_revision':'b'*40};provider.declaration_covered=lambda:True;provider.candidate_image=lambda receipt:(True,'ok')
        with patch.object(module,'load',return_value=provider),patch.object(sys,'argv',['test','--receipt','synthetic','--mode','image']):
            self.assertEqual(result(module.main)[1]['verdict'],'uncertain')
        submitted=next(parts for parts in provider.calls if parts[1]=='create-change-set')
        self.assertIn('--use-previous-template',submitted)
        self.assertNotIn('--template-body',submitted)

    def test_shared_update_parameters_reject_ambiguous_rows_and_preserve_unowned_values(self):
        transition = load(DEPLOY / 'transition-qualified-release/script.py')
        prepare = load(DEPLOY / 'prepare-candidate/script.py')
        shared = transition.CHANGE_SETS
        current = {'ImageDigest': 'old', 'EnableObservability': 'true', 'PrivateSetting': '****'}
        desired = {'ImageDigest': 'new'}
        self.assertIs(transition.update_parameter_inputs, shared.update_parameter_inputs)
        self.assertEqual(shared.update_parameter_inputs(current, desired), [
            {'ParameterKey': 'EnableObservability', 'UsePreviousValue': True},
            {'ParameterKey': 'PrivateSetting', 'UsePreviousValue': True},
            {'ParameterKey': 'ImageDigest', 'ParameterValue': 'new'},
        ])
        inputs = [{'ParameterKey': key, 'ParameterValue': value} for key, value in current.items()]
        self.assertEqual(shared.parameter_values(inputs), current)
        self.assertEqual(shared.parameter_values([{'ParameterKey': 'key', 'ParameterValue': '****', 'ResolvedValue': 'private-canary'}]), {'key': '****'})
        for invalid in (None, {}, [None], [{'ParameterKey': 'key'}],
                        [{'ParameterKey': '', 'ParameterValue': 'private-canary'}],
                        [{'ParameterKey': [], 'ParameterValue': 'private-canary'}],
                        [{'ParameterKey': 'key', 'ParameterValue': 0}],
                        inputs + [inputs[0]], inputs + [{'ParameterKey': 'ImageDigest', 'ParameterValue': 'private-canary'}]):
            with self.subTest(invalid=type(invalid).__name__):
                self.assertIsNone(shared.parameter_values(invalid))
        for invalid in (None, [], {'ImageDigest': 1}, {'': 'private-canary'}):
            self.assertIsNone(shared.update_parameter_inputs(invalid, desired))
            self.assertIsNone(shared.update_parameter_inputs(current, invalid))
            self.assertFalse(prepare.update_parameters_match(invalid, desired, current))
        self.assertIsNone(shared.update_parameter_inputs(current, {'NewParameter': 'private-canary'}))
        for actual, expected in (({**current, **desired}, True), (current, False),
                                 ({**current, **desired, 'EnableObservability': 'false'}, False),
                                 ({**current, **desired, 'Unexpected': 'private-canary'}, False),
                                 (desired, False)):
            self.assertEqual(prepare.update_parameters_match(actual, desired, current), expected)
        owner = prepare.update_operations()
        with patch.object(owner.CHANGE_SETS, 'update_parameters_match', return_value=False) as guard:
            self.assertFalse(prepare.update_parameters_match({**current, **desired}, desired, current))
            guard.assert_called_once_with({**current, **desired}, desired, current)

    def test_update_reconciliation_rejects_ambiguous_completion_without_replay(self):
        prepare = load(DEPLOY / 'prepare-candidate/script.py')
        name, expected = 'fixture-update', {'ImageDigest': 'expected'}
        row = {'ParameterKey': 'ImageDigest', 'ParameterValue': 'expected'}
        for change in (None,
                       {'ChangeSetName': name, 'Status': 'FAILED', 'ExecutionStatus': 'UNAVAILABLE', 'Changes': [], 'StatusReason': "The submitted information didn't contain changes."},
                       {'ChangeSetName': name, 'Status': 'CREATE_COMPLETE', 'ExecutionStatus': 'EXECUTE_COMPLETE'}):
            for rows in (None, [row, row], [{'ParameterKey': 'ImageDigest', 'ParameterValue': 'private-canary'}, row], [None, row]):
                def response(parts):
                    if parts[1] == 'describe-change-set':
                        return (False, None, 'aws-resource-missing') if change is None else (True, change, 'ok')
                    self.assertEqual(parts[1], 'describe-stacks')
                    return True, {'Stacks': [{'StackStatus': 'UPDATE_COMPLETE', 'Parameters': rows}]}, 'ok'
                provider = Provider(response)
                with patch.object(prepare, 'aws', provider.aws):
                    observed = prepare.observe_update(name, expected, lambda _change: True)
                self.assertEqual(observed, ('uncertain', 'persistence-update-stack-parameters-unobservable'))
                self.assertEqual([parts[1] for parts in provider.calls], ['describe-change-set', 'describe-stacks'])
                self.assertNotIn('private-canary', json.dumps(observed))

    def test_image_transition_rejects_invalid_stack_parameters_before_provider_mutation(self):
        module = load(DEPLOY / 'transition-qualified-release/script.py')
        prepare = load(DEPLOY / 'prepare-candidate/script.py')
        receipt = {'image_digest': 'sha256:' + 'a' * 64, 'source_revision': 'a' * 40}
        row = {'ParameterKey': 'ImageDigest', 'ParameterValue': 'sha256:' + 'b' * 64}
        for rows in (None, [row, row], [row, {'ParameterKey': 'ImageDigest', 'ParameterValue': 'private-canary'}], [row, None]):
            for operation in ('update', 'discard-rejected-review'):
                provider = Provider(lambda parts: (True, {'Stacks': [{'StackStatus': 'UPDATE_COMPLETE', 'Parameters': rows}]}, 'ok'))
                with patch.object(module, 'load', side_effect=[prepare, SimpleNamespace(package_gates=lambda _path: True)]), \
                     patch.object(prepare, 'validate_receipt', return_value=receipt), \
                     patch.object(prepare, 'retained_release', return_value=False), \
                     patch.object(prepare, 'live_budget', return_value=(True, 'ok')), \
                     patch.object(prepare, 'aws', provider.aws), \
                     patch.object(sys, 'argv', ['fixture', '--receipt', 'candidate', '--operation', operation]):
                    code, report, _ = result(module.main)
                self.assertEqual(code, 1)
                self.assertEqual(report['findings'], [{'code': 'persistence-release-transition-update-parameter-inputs-invalid'}])
                self.assertEqual([parts[1] for parts in provider.calls], ['describe-stacks'])
                self.assertNotIn('private-canary', json.dumps(report))

    def test_image_transition_uses_deployed_template_and_keeps_resource_guard(self):
        module = load(DEPLOY/'transition-qualified-release/script.py')
        prepare = load(DEPLOY/'prepare-candidate/script.py')
        receipt = {'image_digest': 'sha256:'+'a'*64, 'source_revision': 'a'*40}
        desired = {'ImageDigest': receipt['image_digest'], 'SupportImageDigest': receipt['image_digest'], 'RestoreVerifierImageDigest': receipt['image_digest'], 'SourceRevision': receipt['source_revision']}
        current = {**desired, 'ImageDigest': 'sha256:'+'b'*64, 'SupportImageDigest': 'sha256:'+'b'*64, 'RestoreVerifierImageDigest': 'sha256:'+'b'*64, 'SourceRevision': 'b'*40, 'EnableObservability': 'true'}
        name = 'kanbien-core-platform-persistence-update-' + receipt['image_digest'][7:19]
        for forced_type in (None, 'AWS::IAM::Role', 'AWS::RDS::DBInstance', 'duplicate-parameter', 'malformed-parameter'):
            with self.subTest(forced_type=forced_type):
                prepare = load(DEPLOY/'prepare-candidate/script.py')
                state = {'submitted': None, 'executed': False, 'uses_deployed': False}
                def response(parts):
                    operation = parts[1]
                    if operation == 'describe-stacks':
                        values = {**current, **desired} if state['executed'] else current
                        return True, {'Stacks': [{'StackStatus': 'UPDATE_COMPLETE', 'Parameters': [{'ParameterKey': k, 'ParameterValue': v} for k, v in values.items()]}]}, 'ok'
                    if operation == 'describe-services': return True, {'services': [{'desiredCount': 1, 'runningCount': 1}]}, 'ok'
                    if operation == 'create-change-set':
                        state['uses_deployed'] = '--use-previous-template' in parts and '--template-body' not in parts
                        submitted = json.loads(Path(parts[parts.index('--parameters')+1].removeprefix('file://')).read_text())
                        resolved = {item['ParameterKey']: current[item['ParameterKey']] if item.get('UsePreviousValue') else item['ParameterValue'] for item in submitted}
                        self.assertEqual(resolved, {**current, **desired})
                        self.assertTrue(next(item for item in submitted if item['ParameterKey']=='EnableObservability')['UsePreviousValue'])
                        state['submitted'] = resolved
                        return True, {}, 'ok'
                    if operation == 'describe-change-set':
                        if state['submitted'] is None: return False, None, 'aws-resource-missing'
                        # The real failed review brought in RDS/IAM changes from
                        # the repository template. A deployed-template request
                        # avoids that input, but never waives the result guard.
                        resource_type = forced_type if forced_type in ('AWS::IAM::Role', 'AWS::RDS::DBInstance') else ('AWS::ECS::TaskDefinition' if state['uses_deployed'] else 'AWS::RDS::DBInstance')
                        rows = [{'ParameterKey': k, 'ParameterValue': v} for k, v in state['submitted'].items()]
                        if forced_type == 'duplicate-parameter': rows.insert(0, {'ParameterKey': 'ImageDigest', 'ParameterValue': 'private-canary'})
                        if forced_type == 'malformed-parameter': rows.append(None)
                        return True, {'ChangeSetName': name, 'Status': 'CREATE_COMPLETE', 'ExecutionStatus': 'EXECUTE_COMPLETE' if state['executed'] else 'AVAILABLE', 'ChangeSetType': 'UPDATE', 'Parameters': rows, 'Changes': [{'ResourceChange': {'ResourceType': resource_type}}]}, 'ok'
                    if operation == 'execute-change-set': state['executed'] = True; return True, {}, 'ok'
                    raise AssertionError(operation)
                provider = Provider(response)
                with patch.object(module, 'load', side_effect=[prepare, SimpleNamespace(package_gates=lambda _path: True)]), patch.object(sys, 'argv', ['test', '--receipt', 'synthetic', '--operation', 'update', '--json']), patch.object(module.time, 'sleep'), patch.object(prepare, 'aws', provider.aws), patch.object(prepare, 'validate_receipt', return_value=receipt), patch.object(prepare, 'retained_release', return_value=False), patch.object(prepare, 'live_budget', return_value=(True, 'ok')), patch.object(prepare, 'foundation_outputs', return_value=({'RepositoryUri': 'synthetic'}, 'ok')), patch.object(prepare, 'infrastructure_parameters', return_value=({}, 'ok')), patch.object(prepare, 'candidate_image', return_value=(True, 'ok')), patch.object(prepare, 'candidate_parameters', return_value=desired):
                    report = result(module.main)[1]
                if forced_type is None:
                    self.assertEqual(report['verdict'], 'transitioned')
                    self.assertTrue(state['uses_deployed'])
                    self.assertEqual(sum(parts[1]=='execute-change-set' for parts in provider.calls), 1)
                else:
                    self.assertEqual(report['verdict'], 'blocked')
                    self.assertEqual(report['findings'], [{'code': 'persistence-update-change-set-review-invalid'}])
                    self.assertFalse(state['executed'])
                    self.assertNotIn('private-canary', json.dumps(report))

    def test_qualified_rollback_main_retains_support_and_restoration_images(self):
        module = load(DEPLOY/'transition-qualified-release/script.py')
        prepare = load(DEPLOY/'prepare-candidate/script.py')
        evidence = ROOT/'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence'
        retained_path = evidence/'package-receipts/package-custody-40232309637.json'
        support_path = evidence/'package-receipts/package-custody-40419185209.json'
        retained, support = prepare.validate_receipt(retained_path), prepare.validate_receipt(support_path)
        outputs = {'RepositoryUri': 'synthetic-image-repository'}
        original = {**prepare.candidate_parameters(outputs, {}, support), 'EnableObservability': 'true'}
        desired = {**prepare.candidate_parameters(outputs, {}, retained), 'SupportImageDigest': support['image_digest'], 'RestoreVerifierImageDigest': support['image_digest'], 'EnableObservability': 'true'}
        name = 'kanbien-core-platform-persistence-rollback-' + retained['image_digest'][7:19]
        arguments = ['test', '--receipt', str(retained_path), '--operation', 'rollback', '--rollback-compatibility-id', 'rollback-compatibility-8f1ffbb5741c5ce923b0cfab', '--support-receipt', str(support_path), '--json']
        # This fixture owns transition/pin behavior, not live compatibility.
        # The companion provider CLI fixtures exercise the actual immutable
        # reader with valid and changed contracts. An old archive is not
        # automatically compatible with today's template.
        for wrong_pin in (None, 'stopped', 'wrong-service', 'wrong-definition', 'wrong-candidate', 'compatibility', 'SupportImageDigest', 'RestoreVerifierImageDigest', 'support-scan', 'retained-scan', 'foundation'):
            with self.subTest(wrong_pin=wrong_pin):
                prepare = load(DEPLOY/'prepare-candidate/script.py')
                current = {**original}
                if wrong_pin in ('SupportImageDigest', 'RestoreVerifierImageDigest'): current[wrong_pin] = 'sha256:'+'a'*64
                if wrong_pin == 'wrong-candidate': current['ImageDigest'] = 'sha256:' + 'a' * 64
                state = {'submitted': None, 'executed': False}
                def response(parts):
                    operation = parts[1]
                    if operation == 'describe-stacks':
                        params = desired if state['executed'] else current
                        return True, {'Stacks': [{'StackStatus': 'UPDATE_COMPLETE', 'Parameters': [{'ParameterKey': k, 'ParameterValue': v} for k, v in params.items()],
                            'Outputs': [{'OutputKey': 'CoreServerPersistenceTaskDefinitionArn', 'OutputValue': 'fixture-owned-definition'}]}]}, 'ok'
                    if operation == 'describe-services': return True, {'services': [{'desiredCount': 1, 'runningCount': 0 if wrong_pin == 'stopped' else 1,
                        'serviceName': 'wrong' if wrong_pin == 'wrong-service' else module.SERVICE,
                        'taskDefinition': 'wrong' if wrong_pin == 'wrong-definition' else 'fixture-owned-definition'}]}, 'ok'
                    if operation == 'create-change-set':
                        self.assertIn('--use-previous-template', parts)
                        self.assertNotIn('--template-body', parts)
                        submitted = json.loads(Path(parts[parts.index('--parameters')+1].removeprefix('file://')).read_text())
                        resolved = {item['ParameterKey']: current[item['ParameterKey']] if item.get('UsePreviousValue') else item['ParameterValue'] for item in submitted}
                        self.assertEqual(resolved, desired)
                        self.assertTrue(next(item for item in submitted if item['ParameterKey']=='EnableObservability')['UsePreviousValue'])
                        state['submitted'] = resolved
                        return True, {}, 'ok'
                    if operation == 'describe-change-set':
                        if state['submitted'] is None: return False, None, 'aws-resource-missing'
                        return True, {'ChangeSetName': name, 'Status': 'CREATE_COMPLETE', 'ChangeSetType': 'UPDATE', 'ExecutionStatus': 'EXECUTE_COMPLETE' if state['executed'] else 'AVAILABLE', 'Parameters': [{'ParameterKey': k, 'ParameterValue': v} for k, v in state['submitted'].items()], 'Changes': [{'ResourceChange': {'ResourceType': 'AWS::ECS::TaskDefinition'}}]}, 'ok'
                    if operation == 'execute-change-set': state['executed'] = True; return True, {}, 'ok'
                    raise AssertionError(f'unexpected provider operation: {operation}')
                provider = Provider(response)
                create = SimpleNamespace(package_gates=lambda _path: True)
                def image_check(receipt):
                    failed = (wrong_pin=='support-scan' and receipt['image_digest']==support['image_digest']) or (wrong_pin=='retained-scan' and receipt['image_digest']==retained['image_digest'])
                    return not failed, 'persistence-candidate-image-scan-not-clean' if failed else 'ok'
                infrastructure = (None, 'foundation-endpoint-missing') if wrong_pin=='foundation' else ({}, 'ok')
                with patch.object(module, 'load', side_effect=[prepare, create]), patch.object(sys, 'argv', arguments), patch.object(prepare, 'aws', provider.aws), patch.object(prepare, 'rollback_compatibility', return_value=wrong_pin != 'compatibility') as compatibility, patch.object(prepare, 'live_budget', return_value=(True, 'ok')), patch.object(prepare, 'foundation_outputs', return_value=(outputs, 'ok')), patch.object(prepare, 'infrastructure_parameters', return_value=infrastructure), patch.object(prepare, 'candidate_image', side_effect=image_check) as scans:
                    report = result(module.main)[1]
                compatibility.assert_called_once_with(retained, 'rollback-compatibility-8f1ffbb5741c5ce923b0cfab')
                if wrong_pin in (None, 'stopped'):
                    self.assertEqual(report['verdict'], 'transitioned')
                    self.assertEqual([call.args[0]['image_digest'] for call in scans.call_args_list], [support['image_digest'], retained['image_digest']])
                    self.assertEqual(sum(parts[1]=='execute-change-set' for parts in provider.calls), 1)
                else:
                    self.assertEqual(report['verdict'], 'blocked')
                    code = {**{key: 'persistence-rollback-current-candidate-mismatch' for key in ('wrong-service', 'wrong-definition', 'wrong-candidate')}, 'compatibility': 'persistence-rollback-compatibility-not-proven', 'support-scan': 'persistence-rollback-support-package-not-proven', 'RestoreVerifierImageDigest': 'persistence-rollback-restoration-image-mismatch', 'retained-scan': 'persistence-release-transition-alignment-not-proven', 'foundation': 'persistence-release-transition-alignment-not-proven'}.get(wrong_pin, 'persistence-rollback-support-image-mismatch')
                    self.assertEqual(report['findings'][0]['code'], code)
                    if wrong_pin in ('SupportImageDigest', 'RestoreVerifierImageDigest'): scans.assert_not_called()
                    if wrong_pin in ('support-scan', 'retained-scan', 'foundation'):
                        reason = 'foundation-endpoint-missing' if wrong_pin=='foundation' else 'persistence-candidate-image-scan-not-clean'
                        self.assertEqual(report['findings'], [{'code': code}, {'code': reason}])
                    self.assertFalse(any(parts[1] in ('create-change-set', 'execute-change-set') for parts in provider.calls))
                    if wrong_pin == 'compatibility':
                        self.assertEqual(provider.calls, [])
                        scans.assert_not_called()
        parameters = [{'ParameterKey': key, 'ParameterValue': value} for key, value in desired.items()]
        completed = {'ChangeSetName': name, 'Status': 'CREATE_COMPLETE', 'ExecutionStatus': 'EXECUTE_COMPLETE', 'ChangeSetType': 'UPDATE', 'Parameters': parameters, 'Changes': [{'ResourceChange': {'ResourceType': 'AWS::ECS::TaskDefinition'}}]}
        for restore_digest, expected in ((support['image_digest'], 'transitioned'), (retained['image_digest'], 'uncertain')):
            observed = {**desired, 'RestoreVerifierImageDigest': restore_digest}
            provider = Provider(lambda parts: (True, completed, 'ok') if parts[1]=='describe-change-set' else (True, {'Stacks': [{'StackStatus': 'UPDATE_COMPLETE', 'Parameters': [{'ParameterKey': k, 'ParameterValue': v} for k, v in observed.items()]}]}, 'ok'))
            with patch.object(prepare, 'aws', provider.aws), patch.object(module, 'retain_failure_diagnostic', return_value=None):
                self.assertEqual(result(lambda: module.reconcile(prepare, name, retained['image_digest'], retained['source_revision'], support['image_digest']))[1]['verdict'], expected)
            self.assertTrue(all(parts[1].startswith('describe-') for parts in provider.calls))

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
            with temporary_change_sets(module),patch.object(module,'controls',return_value=provider),patch.object(sys,'argv',['test','--receipt','synthetic','--approved-change-set',name]):
                self.assertEqual(result(module.main)[1]['verdict'],'pending')
            self.assertFalse(any(parts[1]=='execute-change-set' for parts in provider.calls))

    def test_default_execution_does_not_adopt_concurrent_foreign_completion(self):
        module = load(DEPLOY/'deploy-candidate/script.py')
        receipt = {'image_digest':'sha256:'+'a'*64,'source_revision':'a'*40}
        name = 'kanbien-core-platform-persistence-create-'+'a'*12
        stack_id = 'arn:aws:cloudformation:eu-west-1:337159794548:stack/'+module.STACK+'/foreign-operation'
        expected = {'ImageDigest':receipt['image_digest'],'SupportImageDigest':receipt['image_digest'],
                    'RestoreVerifierImageDigest':receipt['image_digest'],'SourceRevision':receipt['source_revision']}
        parameters = [{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()]
        stack_reads = 0
        def response(parts):
            nonlocal stack_reads
            if parts[1] == 'describe-change-set':
                return True,{'ChangeSetName':name,'Status':'CREATE_COMPLETE','ExecutionStatus':'EXECUTE_COMPLETE','ChangeSetType':'CREATE',
                    'Parameters':parameters,'Changes':[{'ResourceChange':{'ResourceType':'AWS::RDS::DBInstance'}}]},'ok'
            if parts[1] == 'describe-stacks':
                stack_reads += 1
                return True,{'Stacks':[{'StackId':stack_id,'StackStatus':'REVIEW_IN_PROGRESS' if stack_reads == 1 else 'CREATE_COMPLETE','Parameters':parameters}]},'ok'
            if parts[1] == 'describe-stack-events':
                return True,{'StackEvents':[{'PhysicalResourceId':stack_id,'ClientRequestToken':'foreign-token'}]},'ok'
            raise AssertionError(('unexpected mutation',parts))
        provider = Provider(response)
        provider.validate_receipt=lambda _:receipt;provider.declaration_covered=lambda:True
        provider.foundation_outputs=lambda:({},'ok');provider.infrastructure_parameters=lambda _:({},'ok')
        provider.candidate_image=lambda _:(True,'ok');provider.candidate_parameters=lambda *args:expected
        with temporary_change_sets(module),patch.object(module,'controls',return_value=provider),patch.object(sys,'argv',['fixture','--receipt','fixture','--approved-change-set',name]):
            observed = result(module.main)[1]
            self.assertEqual(observed['verdict'],'uncertain')
            self.assertEqual(observed['findings'],[{'code':'persistence-stack-execution-lineage-unproven'}])
            # Historical receipt inspection remains explicitly read-only and
            # does not pretend the new local reservation executed that release.
            with patch.object(sys,'argv',['fixture','--receipt','fixture','--approved-change-set',name,'--reconcile']):
                self.assertEqual(result(module.main)[1]['verdict'],'deployed-awaiting-migration')
        self.assertFalse(any(parts[1] == 'execute-change-set' for parts in provider.calls))

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
            with temporary_replacements(module),patch.object(module,'module',side_effect=[provider,create]),patch.object(module,'current_task',return_value=(wrong,'ok','definition-safe')),patch.object(sys,'argv',['test','--receipt','synthetic',*continuation]):
                self.assertEqual(result(module.main)[1]['verdict'],'blocked')
            self.assertFalse(any(parts[1]=='stop-task' for parts in provider.calls))

    def test_normal_replacement_retains_original_and_never_stops_successor(self):
        """Run both normal command invocations through actual provider readers."""
        for loss in ('none', 'submission', 'receipt', 'credential'):
            with self.subTest(loss=loss):
                module=load(RUN/'rehearse-server-replacement/script.py')
                receipt={'image_digest':'sha256:'+'c'*64,'source_revision':'a'*40}
                prefix='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'
                definition='arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-core-server-persistence:34'
                image='337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server@'+receipt['image_digest']
                original={'taskArn':prefix+'a'*32,'taskDefinitionArn':definition,'group':'service:'+module.SERVICE,'lastStatus':'RUNNING','startedAt':'2026-11-15T12:00:00Z','containers':[{'name':'core-server-persistence','image':image,'imageDigest':receipt['image_digest'],'exitCode':137}]}
                successor={**original,'taskArn':prefix+'b'*32,'startedAt':'2026-11-15T12:00:02Z'}
                current=[original]
                admin_definition='arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:12'
                # Support/admin image may legitimately differ from runtime after rollback.
                admin_digest='sha256:'+'d'*64
                with temporary_receipts(module) as receipts, temporary_replacements(module) as (owner,store):
                    def response(parts):
                        operation=parts[1]
                        if operation=='describe-stacks': return True,{'Stacks':[{'Outputs':[{'OutputKey':'CoreServerPersistenceAdministrationTaskDefinitionArn','OutputValue':admin_definition}]}]},'ok'
                        if operation=='describe-services': return True,{'services':[{'status':'ACTIVE','desiredCount':1,'runningCount':1,'taskDefinition':definition,'deployments':[{'status':'PRIMARY','rolloutState':'COMPLETED'}]}]},'ok'
                        if operation=='list-tasks': return True,{'taskArns':[current[0]['taskArn']]},'ok'
                        if operation=='describe-tasks': return True,{'tasks':[original if parts[-1]==original['taskArn'] else successor]},'ok'
                        if operation=='describe-task-definition':
                            if parts[-1]==admin_definition: return True,{'taskDefinition':{'taskDefinitionArn':admin_definition,'containerDefinitions':[{'name':'persistence-administration','image':'337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server@'+admin_digest}]}},'ok'
                            return True,{'taskDefinition':{'taskDefinitionArn':definition,'containerDefinitions':[{'name':'core-server-persistence','image':image,'environment':[{'name':'PLATFORM_SOURCE_COMMIT_SHA','value':receipt['source_revision']}]}]}},'ok'
                        self.assertEqual(operation,'stop-task')
                        selected=store.selected(receipt,active_admission[0])
                        self.assertEqual(selected['request']['original_task'],original['taskArn'])
                        self.assertEqual(store.selection_path(receipt,active_admission[0]).stat().st_mode & 0o777,0o600)
                        self.assertEqual(parts,('ecs','stop-task','--cluster',module.CLUSTER,'--task',original['taskArn'],'--reason','governed core-server-persistence replacement rehearsal'))
                        boundary=datetime.fromisoformat(selected['reserved_at'])
                        original.update(lastStatus='STOPPED',stoppedAt=(boundary+timedelta(seconds=1)).isoformat(),stoppedReason=parts[-1])
                        successor.update(createdAt=(boundary+timedelta(seconds=1)).isoformat(),startedAt=(boundary+timedelta(seconds=2)).isoformat());current[0]=successor
                        return (False,{},'aws-command-timeout') if loss=='submission' else (True,{},'ok')
                    active_admission=[None]
                    prepare=Provider(response);prepare.ACCOUNT='337159794548';prepare.REGION='eu-west-1';prepare.REPOSITORY='kanbien-core-platform/core-server'
                    prepare.validate_receipt=lambda _:receipt;prepare.candidate_runnable_manifest=lambda _:(receipt['image_digest'],'ok')
                    create=SimpleNamespace(package_gates=lambda _:True)
                    with patch.object(module,'module',side_effect=lambda path,name:prepare if name=='prepare' else create),patch.object(sys,'argv',['test','--receipt','synthetic']):
                        with patch.object(receipts,'persist',side_effect=OSError('private-canary')) if loss=='receipt' else contextlib.nullcontext():
                            first=result(module.main)[1]
                        self.assertEqual(first['verdict'],'uncertain' if loss in {'submission','receipt'} else 'replaced',first)
                        if loss=='submission': self.assertEqual(first['findings'],[{'code':'aws-command-timeout'}])
                        self.assertNotIn('private-canary',json.dumps(first))
                        second=result(module.main)[1]
                        self.assertEqual(second['verdict'],'replaced',second)
                        proof=module.ROOT/second['facts']['proof_receipt'];before=proof.read_bytes()
                        third=result(module.main)[1]
                        self.assertEqual(third['facts']['original_task'],original['taskArn'])
                        self.assertEqual(third['facts']['replacement_task'],successor['taskArn'])
                        self.assertEqual(proof.read_bytes(),before)
                    self.assertEqual(sum(parts[1]=='stop-task' for parts in prepare.calls),1)
                    selected=store.selected(receipt)
                    changed={**selected['request'],'original_task':successor['taskArn']}
                    with self.assertRaises(owner.OperationFailure): store.reserve(owner.PHASE,changed)
                    self.assertEqual(store.selected(receipt),selected)
                    # Newly reserved completions cannot adopt stale timestamps or a
                    # historical receipt with a different reservation boundary.
                    for target,key in ((original,'stoppedAt'),(successor,'createdAt'),(successor,'startedAt')):
                        saved=target[key];target[key]='2020-01-01T00:00:00Z'
                        report=result(lambda:module.replace_current(prepare,receipt))[1]
                        self.assertEqual(report['findings'],[{'code':'persistence-replacement-reservation-lineage-not-confirmed'}])
                        target[key]=saved
                    altered=json.loads(proof.read_text());altered['context']['recovery_boundary']='2020-01-01T00:00:00Z'
                    altered['integrity']['payload_sha256']=receipts.digest({key:value for key,value in altered.items() if key!='integrity'})
                    proof.write_text(json.dumps(altered))
                    self.assertEqual(result(lambda:module.replace_current(prepare,receipt))[1]['findings'],[{'code':'persistence-replacement-retained-reservation-mismatch'}])
                    proof.write_bytes(before)
                    if loss=='credential':
                        lifecycle=load(RUN/'rehearse-runtime-credential-lifecycle/script.py')
                        for index,operation in enumerate(('revoke-runtime','restore-runtime')):
                            start=datetime.now(timezone.utc)-timedelta(seconds=10)
                            admin={'taskArn':prefix+str(index+5)*32,'taskDefinitionArn':admin_definition,'lastStatus':'STOPPED','startedAt':start.isoformat(),'stoppedAt':(start+timedelta(seconds=1)).isoformat(),'containers':[{'exitCode':0}]}
                            body=receipts.make(proof_type='administration',operation=operation,task=admin,image_digest=admin_digest,result_code='PERSISTENCE_RUNTIME_IAM_ACCESS_'+('REVOKED' if index==0 else 'RESTORED'),context={'completion_deadline_seconds':90,'completion_duration_seconds':1},controller='run-administration',collected_at=datetime.now(timezone.utc).isoformat())
                            admission=receipts.persist(body).relative_to(module.ROOT).as_posix()
                            admission_path=module.ROOT/admission;admission_bytes=admission_path.read_bytes()
                            for field,value in (('operation','confirm-runtime-iam-access'),('exit_code',1),('result_code','PERSISTENCE_RUNTIME_IAM_ACCESS_CONFIRMED'),('controller','other-controller'),('evidence_class','live'),('definition',admin_definition[:-2]+'99'),('image_digest',receipt['image_digest']),('completion_duration_seconds',91)):
                                rejected=copy.deepcopy(body)
                                if field=='operation': rejected[field]=value
                                elif field in {'controller','evidence_class'}: rejected['provenance'][field]=value
                                elif field=='completion_duration_seconds': rejected['context'][field]=value
                                else: rejected['task'][field]=value
                                rejected['integrity']['payload_sha256']=receipts.digest({key:value for key,value in rejected.items() if key!='integrity'})
                                admission_path.write_text(json.dumps(rejected))
                                with self.assertRaises(owner.OperationFailure): owner.administration_admission(module.ROOT,admission,receipts,prepare.aws)
                            admission_path.write_bytes(admission_bytes)
                            active_admission[0]=owner.administration_admission(module.ROOT,admission,receipts,prepare.aws)[0]
                            original=successor
                            successor={**original,'taskArn':prefix+str(index+3)*32,'lastStatus':'RUNNING'}
                            current[0]=original
                            lifecycle.LAST_SUCCESS={'operation':operation,'proof_receipt':admission}
                            def child(path,*args):
                                self.assertTrue(path.endswith('rehearse-server-replacement/script.sh'))
                                self.assertEqual(args,('--receipt','synthetic','--after-administration-receipt',admission,'--json'))
                                with patch.object(module,'module',side_effect=lambda path,name:prepare if name=='prepare' else create),patch.object(sys,'argv',['test',*args]):
                                    code,observed,_=result(module.main)
                                self.assertEqual(code,0,observed)
                                return observed
                            with patch.object(lifecycle,'child',side_effect=child):
                                self.assertTrue(lifecycle.replace(Path('synthetic')))
                                self.assertTrue(lifecycle.replace(Path('synthetic')))
                            selected=store.selected(receipt,active_admission[0])
                            self.assertEqual(selected['request']['original_task'],original['taskArn'])
                            with self.assertRaises(owner.OperationFailure): store.reserve(owner.PHASE,{**selected['request'],'original_task':successor['taskArn']})
                        self.assertEqual(sum(parts[1]=='stop-task' for parts in prepare.calls),3)

    def test_replacement_interrupted_reservation_never_reselects_or_replays(self):
        module=load(RUN/'rehearse-server-replacement/script.py')
        receipt={'image_digest':'sha256:'+'c'*64,'source_revision':'a'*40}
        definition='arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-core-server-persistence:34'
        original={'taskArn':'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'a'*32}
        prepare=Provider(lambda _: (_ for _ in ()).throw(AssertionError('no mutation permitted')))
        with temporary_replacements(module) as (owner,store),patch.object(module,'current_task',return_value=(original,'ok',definition)),patch.object(module,'receipt_matches_task',return_value=(True,'ok')):
            reserve=store.reserve
            def interrupted(*args):
                reserve(*args)
                raise KeyboardInterrupt()
            with patch.object(store,'reserve',side_effect=interrupted),self.assertRaises(KeyboardInterrupt):
                module.replace_current(prepare,receipt)
            selected=store.selected(receipt)
            self.assertEqual(selected['request']['original_task'],original['taskArn'])
            # No fresh current-task selection on resume, even before any stop.
            with patch.object(module,'current_task',side_effect=AssertionError('must retain original')),patch.object(module,'replacement_task',return_value=(None,'persistence-replacement-not-healthy')) as observed:
                report=result(lambda:module.replace_current(prepare,receipt))[1]
                self.assertEqual(report['verdict'],'pending')
                self.assertEqual(observed.call_args.args[1:3],(original['taskArn'],definition))
            self.assertFalse(prepare.calls)

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
                if '/validate-accepted-release/script.sh' in script or script.endswith('/entity-smoke/acceptance-state.sh'):
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
        """Retain the failed operation, not an uncorrelated event's cause."""
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
            self.assertEqual(saved['original_failure']['code'],'persistence-update-stack-failed')
            self.assertEqual(saved['classification']['code'],'provider-details-unavailable')
            self.assertEqual(saved['facts']['provider_status'],'CREATE_COMPLETE')
            self.assertNotIn('resource_logical_id',saved['facts'])
            self.assertNotIn('resource_type',saved['facts'])
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

    def test_no_change_review_is_complete_only_when_the_exact_candidate_is_already_live(self):
        prepare=load(DEPLOY/'prepare-candidate/script.py')
        expected={'RestoreVerifierImageDigest':'sha256:'+'a'*64}
        parameters=[{'ParameterKey':key,'ParameterValue':value} for key,value in expected.items()]
        no_change={
            'ChangeSetName':'synthetic-operation','Status':'FAILED','ExecutionStatus':'UNAVAILABLE',
            'Changes':[],'StatusReason':"The submitted information didn't contain changes.",
            'Parameters':parameters,
        }
        provider=Provider(lambda parts: (True,no_change,'ok') if parts[1]=='describe-change-set' else (True,{'Stacks':[{'StackStatus':'UPDATE_COMPLETE','Parameters':parameters}]},'ok'))
        with patch.object(prepare,'aws',provider.aws):
            self.assertEqual(prepare.observe_update('synthetic-operation',expected,lambda change: True),('complete','persistence-update-noop-candidate-already-applied'))
        wrong=[{'ParameterKey':'RestoreVerifierImageDigest','ParameterValue':'sha256:'+'b'*64}]
        provider=Provider(lambda parts: (True,no_change,'ok') if parts[1]=='describe-change-set' else (True,{'Stacks':[{'StackStatus':'UPDATE_COMPLETE','Parameters':wrong}]},'ok'))
        with patch.object(prepare,'aws',provider.aws):
            self.assertEqual(prepare.observe_update('synthetic-operation',expected,lambda change: True)[0],'failed')
        malformed={**no_change,'StatusReason':'unrelated provider failure'}
        provider=Provider(lambda parts:(True,malformed,'ok'))
        with patch.object(prepare,'aws',provider.aws):
            self.assertEqual(prepare.observe_update('synthetic-operation',expected,lambda change: True)[0],'failed')

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
        with patch.object(module,'administer',return_value=True) as administer,patch.object(module,'replace',return_value=True) as replace,patch.object(module,'healthy',return_value=True) as healthy,patch.object(module,'verifier_receipt',return_value='fixture-readiness-receipt'):
            self.assertEqual(module.recover(receipt),('ok','fixture-readiness-receipt'))
        administer.assert_called_once_with('restore-runtime')
        replace.assert_called_once_with(receipt)
        self.assertEqual(healthy.call_args_list,[call('health-ready'),call('read')])

    def test_verifier_failure_reference_requires_terminal_retained_evidence(self):
        module=load(RUN/'verify-candidate/script.py')
        task={'taskArn':'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'a'*32,
              'taskDefinitionArn':'arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:17',
              'startedBy':'kp-'+'b'*32,'lastStatus':'STOPPED','containers':[{'exitCode':1}],
              'startedAt':'2026-10-24T10:00:00Z','stoppedAt':'2026-10-24T10:00:02Z'}
        with temporary_receipts(module) as receipts, patch.object(module,'image_digest',return_value='sha256:'+'a'*64), patch.object(module,'failed_task_log',return_value={}) as logs:
            for altered in ({**task,'lastStatus':'RUNNING'},{**task,'containers':[{'exitCode':True}]},{**task,'stoppedAt':None}):
                remembered=[]
                report=result(lambda:module.accepted_completion(altered,120,'read',remembered.append))[1]
                self.assertEqual(report['verdict'],'uncertain')
                self.assertNotIn('proof_receipt',report['facts'])
                self.assertEqual(remembered,[])
            logs.assert_not_called()
            remembered=[]
            report=result(lambda:module.accepted_completion(task,120,'read',remembered.append))[1]
            self.assertEqual(report['verdict'],'failed')
            self.assertEqual(len(remembered),1)
            path=remembered[0]; proof=receipts.validate(json.loads(path.read_text()))
            self.assertEqual(proof['task']['arn'],task['taskArn'])
            self.assertEqual(proof['task']['exit_code'],1)
            self.assertEqual(report['facts']['proof_receipt'],path.relative_to(module.ROOT).as_posix())
            self.assertEqual(report['facts']['proof_sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            value={'proof_receipt':report['facts']['proof_receipt'],'proof_sha256':report['facts']['proof_sha256'],
                   'mode':'read','task_arn':task['taskArn'],'operation_id':task['startedBy'],'request':{'task_definition':task['taskDefinitionArn']}}
            with patch.object(module,'aws',side_effect=AssertionError('retained observation must not launch a task')):
                retained=result(lambda:module.observe_reserved(value,module.ROOT/'unused',120,'read'))[1]
            self.assertEqual(retained['verdict'],'failed')
            self.assertEqual(retained['facts']['proof_sha256'],report['facts']['proof_sha256'])
            self.assertEqual(retained['facts']['evidence_reuse'],'historical-completion')
            def broken_journal(_path): raise OSError('private-canary')
            failed=result(lambda:module.accepted_completion(task,120,'read',broken_journal))[1]
            self.assertEqual(failed['verdict'],'failed')
            self.assertNotIn('proof_receipt',failed['facts'])
            self.assertNotIn('private-canary',json.dumps(failed))
            with patch.object(receipts,'persist',side_effect=OSError('private-canary')):
                failed=result(lambda:module.accepted_completion(task,120,'read',remembered.append))[1]
            self.assertNotIn('proof_receipt',failed['facts'])
            self.assertEqual(len(remembered),1)
            unjournalled=result(lambda:module.accepted_completion(task,120,'read'))[1]
            self.assertNotIn('proof_receipt',unjournalled['facts'])

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

    def test_administration_terminal_failure_requires_retained_receipt_and_callback(self):
        module=load(RUN/'run-administration/script.py')
        task={'taskArn':'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'a'*32,
              'taskDefinitionArn':'arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:17',
              'startedBy':'kp-'+'b'*32,'lastStatus':'STOPPED','containers':[{'exitCode':1}],
              'startedAt':'2026-10-24T10:00:00Z','stoppedAt':'2026-10-24T10:00:02Z'}
        with tempfile.TemporaryDirectory() as directory, patch.object(module,'ROOT',Path(directory)), \
             patch.object(module.RECEIPTS,'RECEIPTS',Path(directory)/'proofs'), \
             patch.object(module.MIGRATION,'image_digest',return_value='sha256:'+'a'*64), \
             patch.object(module.MIGRATION,'aws',return_value=(True,{'events':[]},'ok')):
            retained=[]
            report=result(lambda:module.accept(task,120,'observe-migration-state',retained.append))[1]
            self.assertEqual(report['verdict'],'failed')
            self.assertEqual(report['facts']['proof_sha256'],hashlib.sha256(retained[0].read_bytes()).hexdigest())
            self.assertEqual(report['facts']['operation_id'],task['startedBy'])
            for altered in ({**task,'lastStatus':'RUNNING'},{**task,'containers':[{'exitCode':True}]}):
                rejected=result(lambda:module.accept(altered,120,'observe-migration-state',retained.append))[1]
                self.assertNotIn('proof_receipt',rejected.get('facts',{}))
            def broken(_): raise OSError('private-canary')
            rejected=result(lambda:module.accept(task,120,'observe-migration-state',broken))[1]
            self.assertEqual(rejected['verdict'],'uncertain')
            self.assertNotIn('proof_receipt',rejected.get('facts',{}))
            self.assertNotIn('private-canary',json.dumps(rejected))

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
        digest='sha256:'+'d'*64;definition='arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:7'
        task={'taskArn':'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'+'d'*32,'taskDefinitionArn':definition,'lastStatus':'STOPPED','startedAt':'2026-10-26T12:00:00Z','stoppedAt':'2026-10-26T12:00:08Z','stoppedReason':'Essential container in task exited','containers':[{'exitCode':0}]}
        receipt=module.RECEIPTS.make(proof_type='administration',operation='prove-effective-privilege',task=task,image_digest=digest,result_code='PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN',context={'completion_deadline_seconds':300,'completion_duration_seconds':8},controller='run-administration',collected_at='2026-10-26T12:00:09Z')
        with tempfile.TemporaryDirectory(prefix='administration-retained-receipt-') as directory:
            subprocess.run(['git','init','--quiet',directory],check=True)
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
        values=surface.surface_parameters({'Parameters':[{'ParameterKey':'ImageDigest','ParameterValue':'sha256:'+'c'*64},{'ParameterKey':'RestoreVerifierImageDigest','ParameterValue':'sha256:'+'c'*64}]},digest)
        self.assertEqual(len([item for item in values if item['ParameterKey']=='RestoreVerifierImageDigest']),1)
        self.assertEqual(values[-1]['ParameterValue'],digest)
        egress_change={'ChangeSetName':'restore-egress','Status':'CREATE_COMPLETE','ExecutionStatus':'AVAILABLE','ChangeSetType':'UPDATE','Parameters':[{'ParameterKey':'ImageDigest','ParameterValue':'sha256:'+'c'*64},{'ParameterKey':'RestoreVerifierImageDigest','ParameterValue':digest}], 'Changes':[{'ResourceChange':{'LogicalResourceId':'RestorationVerifierRestoredDatabaseEgress','ResourceType':'AWS::EC2::SecurityGroupEgress','Action':'Add'}}]}
        self.assertTrue(surface.review(egress_change,'restore-egress',digest,'egress'))
        self.assertEqual(surface.change_name(digest,'egress'),'kanbien-core-platform-persistence-restore-egress-'+'a'*12)
        egress_change['Changes'].append({'ResourceChange':{'LogicalResourceId':'RestoredDatabaseIngressFromRestorationVerifier','ResourceType':'AWS::EC2::SecurityGroupIngress','Action':'Add'}})
        self.assertFalse(surface.review(egress_change,'restore-egress',digest,'egress'))
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
            with temporary_change_sets(module),patch.object(module,'controls',return_value=provider),patch.object(sys,'argv',['test','--receipt','synthetic.json','--approved-change-set',name]):
                report=result(module.main)[1]
                self.assertEqual(report['findings'][0]['code'],'persistence-change-set-live-parameters-mismatch')
            self.assertFalse(any(parts[1]=='execute-change-set' for parts in provider.calls))

    def test_parent_preserves_timeout_operation_receipt(self):
        import subprocess
        module=load(RUN/'rehearse-runtime-credential-lifecycle/script.py')
        command='scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh'
        receipt={'schema':'deploy/persistence-administration-report/v1','target':'kanbien-core-platform','scope':'core-server-persistence','verdict':'pending','facts':{'administration_task':'a'*32,'secret':'must-not-escape'}}
        error=subprocess.TimeoutExpired(['synthetic'],180,stderr=json.dumps(receipt).encode())
        with patch.object(module.subprocess,'run',side_effect=error):
            self.assertIsNone(module.child(command))
        report=result(lambda:module.report('blocked','child-unconfirmed'))[1]
        self.assertEqual(report['verdict'],'pending')
        self.assertEqual(report['facts']['child_checkpoint']['command'],command)
        self.assertEqual(report['facts']['child_checkpoint']['schema'],'deploy/persistence-administration-report/v1')
        self.assertEqual(report['facts']['child_checkpoint']['facts'],{'administration_task':'a'*32})
        self.assertNotIn('must-not-escape',json.dumps(report))

    def test_shared_network_and_endpoint_prerequisites(self):
        module=load(DEPLOY/'prepare-candidate/script.py')
        endpoints=[{'ServiceName':name,'State':'available','Groups':[{'GroupId':'sg-safe'}],'VpcId':'vpc-safe','VpcEndpointType':'Interface','PrivateDnsEnabled':True} for name in module.INTERFACE_SERVICES]
        outputs={'VpcId':'vpc-safe','ServiceDiscoveryArn':'arn/service-safe','PrivateSubnetIds':'subnet-safe','ClusterArn':'cluster-safe','VerifierSecurityGroupId':'sg-safe','LogGroupName':'logs-safe'}
        def response(parts):
            if parts[1]=='describe-vpcs':return True,{'Vpcs':[{'VpcId':'vpc-safe','State':'available','CidrBlock':'10.0.0.0/16'}]},'ok'
            if parts[1]=='describe-subnets':return True,{'Subnets':[{'SubnetId':'subnet-safe','VpcId':'vpc-safe','State':'available','MapPublicIpOnLaunch':False}]},'ok'
            if parts[1]=='get-service':return True,{'Service':{'DnsConfig':{'NamespaceId':'ns-safe'}}},'ok'
            if parts[1]=='get-namespace':return True,{'Namespace':{'Id':'ns-safe','Name':module.INPUTS['foundation_expected']['namespace'],'Type':'DNS_PRIVATE','Properties':{'DnsProperties':{'HostedZoneId':'Z123'}}}},'ok'
            if parts[1]=='get-hosted-zone':return True,{'HostedZone':{'Config':{'PrivateZone':True}},'VPCs':[{'VPCId':'vpc-safe','VPCRegion':module.REGION}]},'ok'
            if parts[1]=='describe-vpc-endpoints':return True,{'VpcEndpoints':endpoints},'ok'
            if parts[1]=='describe-managed-prefix-lists':return True,{'PrefixLists':[{'PrefixListId':'pl-safe'}]},'ok'
            raise AssertionError(parts)
        provider=Provider(response)
        with patch.object(module,'aws',provider.aws):
            with patch.object(module.FOUNDATION_CHECKS,'private_endpoints',wraps=module.FOUNDATION_CHECKS.private_endpoints) as shared, patch.object(module.FOUNDATION_CHECKS,'s3_prefix_list',wraps=module.FOUNDATION_CHECKS.s3_prefix_list) as prefix:
                facts,code=module.infrastructure_parameters(outputs)
                self.assertEqual((code,facts['EndpointSecurityGroupId'],facts['S3ArtifactPrefixListId']),('ok','sg-safe','pl-safe'))
                self.assertEqual(module.INTERFACE_SERVICES,{'com.amazonaws.'+module.REGION+'.'+name for name in ('ecr.api','ecr.dkr','logs')})
                shared.assert_called_once_with(module.foundation_observation,outputs['VpcId'],module.INTERFACE_SERVICES)
                prefix.assert_called_once_with(module.foundation_observation,module.REGION)
            with patch.object(module.FOUNDATION_CHECKS,'private_network',side_effect=module.FOUNDATION_CHECKS.FoundationFailure('foundation-subnet-not-private')) as shared:
                before=len(provider.calls)
                self.assertEqual(module.infrastructure_parameters(outputs),(None,'foundation-subnet-not-private'))
                self.assertEqual(len(provider.calls),before)
                shared.assert_called_once_with(module.foundation_observation,outputs,module.INPUTS['foundation_expected']['namespace'],module.REGION)
            for owner,reason,last_call in [('private_endpoints','foundation-endpoint-group-invalid','get-hosted-zone'),('s3_prefix_list','foundation-s3-prefix-missing','describe-vpc-endpoints')]:
                with patch.object(module.FOUNDATION_CHECKS,owner,side_effect=module.FOUNDATION_CHECKS.FoundationFailure(reason)):
                    self.assertEqual(module.infrastructure_parameters(outputs),(None,reason))
                    self.assertEqual(provider.calls[-1][1],last_call)
            endpoints[0]['Groups']=[{'GroupId':[]}]
            self.assertEqual(module.infrastructure_parameters(outputs),(None,'foundation-endpoint-group-invalid'))
            self.assertEqual(provider.calls[-1][1],'describe-vpc-endpoints')
            for operation in ('describe-vpc-endpoints','describe-managed-prefix-lists'):
                denied=Provider(lambda parts: (False,None,'aws-access-denied') if parts[1]==operation else response(parts))
                endpoints[0]['Groups']=[{'GroupId':'sg-safe'}]
                with patch.object(module,'aws',denied.aws):
                    self.assertEqual(module.infrastructure_parameters(outputs),(None,'aws-access-denied'))
                self.assertEqual(denied.calls[-1][1],operation)

    def test_credential_lifecycle_main_keeps_distinct_recovery_order(self):
        module=load(RUN/'rehearse-runtime-credential-lifecycle/script.py')
        recovery=[('administration','restore-runtime'),('replace',),('health','health-ready'),('health','read')]
        revoked=[('health','health-ready'),('administration','revoke-runtime'),('replace',),('health','health-unready')]
        for operation,expected,verdict in [('revoke-and-recover',revoked+recovery,'accepted'),('revoke-await-observability',revoked,'prepared'),('recover-after-revocation',[('health','health-unready')]+recovery,'accepted')]:
            for fail_at in [None,*range(len(expected))]:
                with self.subTest(operation=operation,fail_at=fail_at):
                    calls=[]
                    def invoke(*parts):
                        calls.append(parts)
                        return len(calls)-1!=fail_at
                    prepare=SimpleNamespace(validate_receipt=lambda _: {'image_digest':'sha256:'+'a'*64},live_budget=lambda:(True,'ok'))
                    create=SimpleNamespace(package_gates=lambda _:True)
                    with patch.object(module,'module',side_effect=[prepare,create]),patch.object(module,'healthy',side_effect=lambda mode:invoke('health',mode)),patch.object(module,'administer',side_effect=lambda mode:invoke('administration',mode)),patch.object(module,'replace',side_effect=lambda _:invoke('replace')),patch.object(module,'verifier_receipt',return_value='retained-proof.json'),patch.object(sys,'argv',['fixture','--receipt','candidate','--operation',operation]):
                        report=result(module.main)[1]
                    self.assertEqual(calls,expected if fail_at is None else expected[:fail_at+1])
                    self.assertEqual(report['verdict'],verdict if fail_at is None else 'blocked')
                    if operation=='recover-after-revocation':self.assertNotIn(('administration','revoke-runtime'),calls)

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
        self.assertEqual([parts[1] for parts in provider.calls],['describe-db-snapshots'])
        provider.calls=[]
        self.assertEqual(result(lambda:module.observe_or_create(provider,sid,True))[1]['verdict'],'uncertain')
        self.assertEqual([parts[1] for parts in provider.calls],['describe-db-snapshots'])

    def test_snapshot_normal_path_reserves_source_and_never_replays(self):
        module=load(RUN/'create-recovery-point/script.py');owner=module.operations()
        sid='kanbien-core-platform-persistence-recovery-20261115';resource='db-ABCDEFGHIJKLMNOP'
        for failure in ('none','lost','interrupted','preexisting'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as directory:
                store=owner.Store(Path(directory)); state={'snapshot':None,'tags':[], 'resource':resource}
                request={'database':module.DATABASE,'snapshot':sid,'source_resource_id':resource}
                if failure=='preexisting':state['snapshot']={'DBSnapshotIdentifier':sid,'DBInstanceIdentifier':module.DATABASE,'Encrypted':True,'Status':'available'}
                def response(parts):
                    operation=parts[1]
                    if operation=='describe-services':return True,{'services':[{'desiredCount':1,'runningCount':1}]},'ok'
                    if operation=='describe-db-instances':return True,{'DBInstances':[{'DBInstanceIdentifier':module.DATABASE,'DbiResourceId':state['resource'],'DBInstanceStatus':'available','PubliclyAccessible':False,'StorageEncrypted':True}]},'ok'
                    if operation=='describe-db-snapshots':
                        return (True,{'DBSnapshots':[state['snapshot']]},'ok') if state['snapshot'] else (False,None,'aws-resource-missing')
                    if operation=='list-tags-for-resource':return True,{'TagList':state['tags']},'ok'
                    if operation=='create-db-snapshot':
                        reservation=store.read('create-recovery-point',request)
                        self.assertIsNotNone(reservation)
                        self.assertEqual(store.path_for('create-recovery-point',request).stat().st_mode & 0o777,0o600)
                        self.assertEqual(parts[:6],('rds','create-db-snapshot','--db-instance-identifier',module.DATABASE,'--db-snapshot-identifier',sid))
                        state['tags']=json.loads(parts[7])
                        self.assertEqual(state['tags'],[{'Key':'Target','Value':'kanbien-core-platform'},{'Key':'Scope','Value':'core-server-persistence'},{'Key':'Operation','Value':reservation['operation_id']}])
                        state['snapshot']={'DBSnapshotIdentifier':sid,'DBSnapshotArn':'arn:aws:rds:eu-west-1:337159794548:snapshot:'+sid,'DBInstanceIdentifier':module.DATABASE,'DbiResourceId':resource,'Encrypted':True,'SnapshotType':'manual','SnapshotCreateTime':datetime.now(timezone.utc).isoformat(),'Status':'available'}
                        if failure=='lost':return False,None,'aws-command-timeout'
                        return True,{},'ok'
                    raise AssertionError(parts)
                provider=Provider(response);provider.live_budget=lambda:(True,'ok')
                argv=['test','--snapshot-id',sid]
                with patch.object(module,'load',return_value=provider),patch.object(module,'operations',return_value=owner),patch.object(owner,'store',return_value=store),patch.object(sys,'argv',argv):
                    if failure=='interrupted':
                        original=store.reserve
                        def interrupt(*args):
                            original(*args)
                            raise KeyboardInterrupt()
                        with patch.object(store,'reserve',side_effect=interrupt):
                            with self.assertRaises(KeyboardInterrupt):result(module.main)
                        report=result(module.main)[1]
                        self.assertEqual(report['findings'],[{'code':'persistence-recovery-point-operation-not-observed'}])
                    else:
                        first=result(module.main)[1]
                        self.assertEqual(first['verdict'],{'none':'pending','lost':'uncertain','preexisting':'blocked'}[failure])
                        if failure=='lost':self.assertEqual(first['findings'],[{'code':'aws-command-timeout'}])
                        report=result(module.main)[1]
                        self.assertEqual(report['verdict'],'uncertain' if failure=='preexisting' else 'available')
                    submitted=[parts for parts in provider.calls if parts[1]=='create-db-snapshot']
                    self.assertEqual(len(submitted),0 if failure in {'interrupted','preexisting'} else 1)
                    state['resource']='db-CHANGED'
                    self.assertEqual(result(module.main)[1]['findings'],[{'code':'persistence-recovery-point-reservation-mismatch'}])
                    state['resource']=resource
                    if failure in {'none','lost'}:
                        for field,altered in [('DbiResourceId','db-FOREIGN'),('SnapshotCreateTime','2000-01-01T00:00:00+00:00'),('SnapshotType','automated'),('DBSnapshotArn','arn:foreign')]:
                            prior=state['snapshot'][field];state['snapshot'][field]=altered
                            self.assertEqual(result(module.main)[1]['findings'],[{'code':'persistence-recovery-point-lineage-not-confirmed'}])
                            state['snapshot'][field]=prior
                        original_tags=copy.deepcopy(state['tags'])
                        for tags in ([],original_tags+[original_tags[0]],[{**row,'Value':'foreign'} for row in original_tags]):
                            state['tags']=tags
                            self.assertEqual(result(module.main)[1]['findings'],[{'code':'persistence-recovery-point-ownership-not-confirmed'}])
                        state['tags']=original_tags
                        state['snapshot']=None
                        self.assertEqual(result(module.main)[1]['findings'],[{'code':'persistence-recovery-point-operation-not-observed'}])
                        self.assertEqual(len([parts for parts in provider.calls if parts[1]=='create-db-snapshot']),1)
                    # Historical mode remains read-only and does not require new intent/tags.
                    state['snapshot']={'DBSnapshotIdentifier':sid,'DBInstanceIdentifier':module.DATABASE,'Encrypted':True,'Status':'available'}
                    with patch.object(sys,'argv',argv+['--observe-only']),patch.object(owner,'store',side_effect=AssertionError('historical reader reached new store')):
                        self.assertEqual(result(module.main)[1]['verdict'],'available')

    def test_task_reconciliation_and_lost_submission(self):
        for name,mode_arg,mode,output_key in [('run-migration','--migration-operation','apply','CoreServerPersistenceMigrationTaskDefinitionArn'),('verify-candidate','--mode','create','CoreServerPersistenceVerifierTaskDefinitionArn')]:
            module=load(RUN/name/'script.py'); operation='kp-'+'a'*32
            family='migration' if name=='run-migration' else 'verifier'
            definition=f'arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-{family}:7'
            arn=f'arn:aws:ecs:{module.REGION}:{module.ACCOUNT}:task/{module.CLUSTER}/'+'b'*32
            task={'taskArn':arn,'taskDefinitionArn':definition,'startedBy':operation,'lastStatus':'STOPPED','containers':[{'exitCode':0}],'startedAt':'2026-10-24T10:00:00Z','stoppedAt':'2026-10-24T10:00:02Z'}
            expected_env={'PERSISTENCE_MIGRATION_OPERATION':mode} if name=='run-migration' else {'PERSISTENCE_VERIFIER_MODE':mode,'PERSISTENCE_ACCEPTANCE_RECORD_ID':module.RECORD_ID,'PERSISTENCE_ACCEPTANCE_FACT':module.FACT}
            task['overrides']={'inferenceAcceleratorOverrides':[],'containerOverrides':[{'name':'persistence-migration' if name=='run-migration' else 'private-persistence-verifier','environment':[{'name':key,'value':value} for key,value in expected_env.items()]}]}
            def response(parts):
                if parts[1]=='list-tasks':return True,{'taskArns':[arn]},'ok'
                if parts[1]=='describe-tasks':return True,{'tasks':[task]},'ok'
                if parts[1]=='get-log-events':return True,{'events':[{'message':json.dumps({'verdict':'accepted','code':module.SUCCESS[mode]})}]},'ok'
                if parts[1]=='describe-task-definition':return True,{'taskDefinition':{'containerDefinitions':[{'image':'synthetic.invalid/persistence@sha256:'+'c'*64}]}},'ok'
                raise AssertionError(f'unexpected mutation {parts}')
            provider=Provider(response)
            output={output_key:definition,'PersistenceMigrationSecurityGroupId':'sg-safe','PrivateSubnetIds':'subnet-safe','VerifierSecurityGroupId':'sg-safe'}
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(module,'outputs',return_value=(output,'ok')))
                stack.enter_context(patch.object(module,'deadline',return_value=120))
                stack.enter_context(patch.object(module,'aws',provider.aws))
                receipts = stack.enter_context(temporary_receipts(module))
                if name=='verify-candidate':stack.enter_context(patch.object(module,'no_direct_database_credential',return_value=True))
                for status,exitcode,verdict in [(status,0,'pending') for status in ('PROVISIONING','PENDING','ACTIVATING','RUNNING','DEACTIVATING','STOPPING','DEPROVISIONING')]+[('STOPPED',1,'failed'),('STOPPED',0,'accepted')]:
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
                stack.enter_context(temporary_receipts(module))
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
                    state['database']={'DBInstanceIdentifier':restored_id,'DBInstanceStatus':'creating','TagList':tags,'PubliclyAccessible':False,'StorageEncrypted':True,'IAMDatabaseAuthenticationEnabled':True,'EnabledCloudwatchLogsExports':['postgresql','iam-db-auth-error'],'Engine':'postgres','DBSubnetGroup':{'DBSubnetGroupName':'private-subnets'},'VpcSecurityGroups':[{'VpcSecurityGroupId':'sg-restored'}]}
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

    def test_restore_task_discovery_uses_shared_complete_observation(self):
        module=load(RUN/'rehearse-isolated-database-restore/script.py');shared=module.task_operations()
        definition='arn:aws:ecs:eu-west-1:337159794548:task-definition/renamed-private-reader:4'
        prefix='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'
        first,second=prefix+'a'*32,prefix+'b'*32
        for mode in ('complete','all','empty','pagination','oversized','missing','foreign','duplicates','provider-failure'):
            with self.subTest(mode=mode):
                def response(parts):
                    if parts[1]=='list-tasks':
                        self.assertEqual(parts[2:10],('--cluster',module.CLUSTER,'--family','renamed-private-reader','--max-results','100','--no-paginate','--desired-status'))
                        if mode=='provider-failure':return False,None,'aws-command-timeout'
                        values=[] if mode=='empty' else [first,second]
                        if mode=='oversized':values=[first]*101
                        return True,{'taskArns':values,**({'nextToken':'private-page-canary'} if mode=='pagination' else {})},'ok'
                    self.assertEqual(parts,('ecs','describe-tasks','--cluster',module.CLUSTER,'--tasks',first,second))
                    values=[{'taskArn':first,'startedBy':'original'},{'taskArn':second,'startedBy':'different'}]
                    if mode=='missing':values.pop()
                    if mode=='foreign':values[1]['taskArn']=prefix+'c'*32
                    if mode=='duplicates':values[1]=values[0]
                    return True,{'tasks':values},'ok'
                provider=Provider(response)
                with patch.object(module,'task_operations',return_value=shared),patch.object(shared,'observed_tasks',wraps=shared.observed_tasks) as observed:
                    value,code=module.verifier_tasks(provider,None if mode=='all' else 'original',definition)
                self.assertEqual(observed.call_count,1)
                self.assertEqual(value, [first,second] if mode=='all' else [first] if mode=='complete' else [] if mode=='empty' else None)
                self.assertEqual(code,'ok' if mode in {'complete','all','empty'} else 'persistence-restoration-verifier-observation-uncertain')
                self.assertFalse(any(parts[1]=='run-task' for parts in provider.calls))
                self.assertNotIn('private-page-canary',repr((value,code)))
        # The discovery API's all-operation mode must not widen exact-one callers.
        for matches,operation,accepted in [([{'startedBy':'foreign'}],None,False),([{'startedBy':None}],None,True),([{'startedBy':'original'},{'startedBy':'original'}],'original',False),([], 'original', False)]:
            with patch.object(shared,'observed_tasks',return_value=matches):
                action=lambda:shared.reconcile_task(lambda *_:None,cluster='fixture',definition=definition,operation_id=operation,validate_task=lambda task:task)
                if accepted:self.assertEqual(action(),matches[0])
                else:
                    with self.assertRaises(shared.TaskFailure):action()

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
            for status,exitcode,verdict in [(status,0,'pending') for status in ('PROVISIONING','PENDING','ACTIVATING','RUNNING','DEACTIVATING','STOPPING','DEPROVISIONING')]+[('STOPPED',1,'failed'),('STOPPED',0,'accepted')]:
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
            with patch.object(module,'verifier_tasks',return_value=([],'ok')),patch.object(module,'remove_temporary_restore_identity_policy',return_value='ok'):
                self.assertEqual(result(lambda:module.cleanup(provider,sid,rid))[1]['verdict'],'pending')
            self.assertFalse(provider.calls)

if __name__ == '__main__':
    unittest.main()
