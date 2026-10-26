#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.provider-cli-boundaries
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise real controller CLI cleanup and AWS response boundaries using a disposable provider executable.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.core-server-persistence-target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/smoke-test.sh
"""Synthetic provider processes only. These tests never invoke AWS or produce live proof."""
import importlib.util
import json
import shutil
import hashlib
import copy
import yaml
from unittest.mock import patch
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[7]
RESTORE = ROOT / 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh'
FAKE_AWS = '''#!/usr/bin/env python3
import json, os, pathlib, sys
args=sys.argv[1:]; service,op=args[:2]; scenario=os.environ['FIXTURE_SCENARIO']; log=pathlib.Path(os.environ['FIXTURE_CALLS'])
with log.open('a') as out:out.write(json.dumps([service,op])+'\\n')
def fail(code,message='synthetic-only'):
 print(f'An error occurred ({code}) when calling the Fixture operation: {message}',file=sys.stderr);sys.exit(254)
def emit(value):print(json.dumps(value));sys.exit(0)
if op=='describe-budget':emit({'Budget':{'BudgetLimit':{'Amount':'100','Unit':'USD'},'CostFilters':{'TagKeyValue':['user:Target$kanbien-core-platform']}}})
if op=='describe-db-instances':
 if scenario=='database-denied':fail('AccessDenied','resource not found')
 fail('DBInstanceNotFound')
if op=='describe-stacks':
 outputs={'CoreServerPersistenceRestorationVerifierTaskDefinitionArn':'arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-restoration-verifier:7','PersistenceRestorationVerifierSecurityGroupId':'sg-verifier','PersistenceRestoredDatabaseSecurityGroupId':'sg-restored','PersistenceRestorationVerifierTaskRoleName':'fixture-role','PrivateSubnetIds':'subnet-private'}
 emit({'Stacks':[{'Outputs':[{'OutputKey':k,'OutputValue':v} for k,v in outputs.items()]}]})
if op=='list-tasks':
 if scenario=='tasks-denied':fail('AccessDenied')
 if scenario=='tasks-paginated':emit({'taskArns':[],'nextToken':'unobserved'})
 emit({'taskArns':['task-safe'] if scenario in {'tasks-running','tasks-provisioning','tasks-unknown','tasks-stopped','tasks-mismatch'} else []})
if op=='describe-tasks':emit({'tasks':[{'taskArn':'different-task' if scenario=='tasks-mismatch' else 'task-safe','lastStatus':{'tasks-running':'RUNNING','tasks-provisioning':'PROVISIONING','tasks-stopped':'STOPPED','tasks-unknown':'unrecognized'}.get(scenario,'STOPPED')}]})
if op=='get-role-policy':
 if scenario=='policy-denied':fail('AccessDenied')
 if scenario=='policy-unknown':fail('ServiceFailure','resource not found')
 if scenario=='policy-present':emit({'PolicyDocument':{'Version':'2012-10-17','Statement':[]}})
 fail('NoSuchEntity')
if op=='delete-role-policy':emit({})
raise AssertionError(f'unexpected provider command: {service} {op}')
'''

class ProviderCliRegression(unittest.TestCase):
    def test_cleanup_accounts_for_database_tasks_and_authority(self):
        with tempfile.TemporaryDirectory(prefix='delivery-provider-cli-') as directory:
            root=Path(directory); executable=root/'aws'; executable.write_text(FAKE_AWS); executable.chmod(0o755)
            repository=root/'repository'
            for relative in [RESTORE.with_name('script.py').relative_to(ROOT),Path('scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py'),Path('scripts/04.deploy/shared/provider-adapters/aws/response.py')]:
                destination=repository/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,destination)
            inventory=repository/'scripts/04.deploy/inventory-deploy-control/script.py';inventory.parent.mkdir(parents=True);inventory.write_text('import os,sys\nsys.exit(1 if os.environ.get("FIXTURE_SCENARIO")=="inventory-gap" else 0)\n')
            command_path=repository/RESTORE.with_name('script.py').relative_to(ROOT)

            cases=[('inventory-gap','blocked',False),('all-absent','cleaned-up',False),('tasks-stopped','cleaned-up',False),('policy-present','blocked',False),('policy-present','blocked',True),('policy-denied','blocked',False),('policy-unknown','blocked',False),('database-denied','uncertain',False),('tasks-denied','uncertain',False),('tasks-paginated','uncertain',False),('tasks-running','pending',False),('tasks-provisioning','pending',False),('tasks-unknown','uncertain',False),('tasks-mismatch','uncertain',False)]
            for index,(scenario,verdict,observe) in enumerate(cases):
                with self.subTest(scenario=scenario,observe=observe):
                    calls=root/f'calls-{index}.jsonl'
                    env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'PYTHONDONTWRITEBYTECODE':'1','FIXTURE_SCENARIO':scenario,'FIXTURE_CALLS':str(calls)}
                    command=[sys.executable,'-B',str(command_path),'--operation','cleanup','--snapshot-id','kanbien-core-platform-persistence-recovery-20261026','--json']+(['--observe-only'] if observe else [])
                    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,env=env,timeout=20)
                    report=json.loads(result.stdout)
                    self.assertEqual(report['verdict'],verdict,(result.stdout,result.stderr))
                    self.assertEqual(result.returncode,0 if verdict=='cleaned-up' else 1)
                    operations=[json.loads(line)[1] for line in calls.read_text().splitlines()] if calls.exists() else []
                    self.assertNotIn('delete-db-instance',operations)
                    self.assertNotIn('delete-role-policy',operations)
                    if scenario=='policy-present':self.assertEqual(report['findings'][0]['code'],'persistence-restoration-temporary-identity-policy-mismatch')
                    if verdict=='cleaned-up':
                        self.assertIn('get-role-policy',operations)
                        self.assertEqual(report['facts']['temporary_authority'],'absent')

    def test_missing_rollback_prerequisites_block_real_interfaces(self):
        base=ROOT/'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence'
        for command,args,code in [('transition-qualified-release',['--operation','rollback'],'persistence-rollback-compatibility-required'),('apply-database-permission-surface',[],'persistence-permission-change-rollback-compatibility-required')]:
            result=subprocess.run([sys.executable,'-B',str(base/command/'script.py'),'--receipt','missing.json',*args,'--json'],cwd=ROOT,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,1)
            self.assertEqual(json.loads(result.stdout)['findings'][0]['code'],code)

    def test_rollback_uses_immutable_owner_and_current_contracts(self):
        def load(path):
            spec=importlib.util.spec_from_file_location(path.stem,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
        prepare=load(ROOT/'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py')
        transition=load(ROOT/'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.py')
        owner=load(ROOT/'scripts/04.deploy/lifecycle/60-run/release-succession/script.py')
        with tempfile.TemporaryDirectory(prefix='delivery-rollback-') as directory:
            root=Path(directory);owner.REPOSITORY_ROOT=root;owner.EVIDENCE_CLASS='simulated'
            evidence=root/'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence';evidence.mkdir(parents=True)
            rollback={'source_revision':'a'*40,'image_digest':'sha256:'+'a'*64}
            legacy={'schema':owner.LEGACY_SCHEMA,'status':'rehearsed','evidence_class':'simulated','target':'kanbien-core-platform','scope':'core-server-persistence','release':{'source_revision':'b'*40,'image_digest':'sha256:'+'b'*64},'acceptance':{'rollback_release':rollback}}
            (evidence/'accepted-release.yml').write_text(yaml.safe_dump(legacy))
            retained=owner.retained_rollback_identity(evidence)
            contracts={}
            for key,path in [('configuration_contract','infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml'),('permission_contract','infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml')]:
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(key+': fixture\n');contracts[key]={'path':path,'sha256':owner.sha256_bytes(target.read_bytes())}
            proof=evidence/'proof-receipts/compatibility.json';proof.parent.mkdir();proof.write_text('{"evidence_class":"simulated"}')
            proofs={'compatibility':{'path':'proof-receipts/compatibility.json','sha256':owner.sha256_bytes(proof.read_bytes())}}
            identity={'target':'kanbien-core-platform','scope':'core-server-persistence','historical_release_id':retained['release_id'],**rollback,**contracts,'workloads':['core-server-service','persistence-restoration-verifier-task','private-release-verifier-task'],'proof_set_sha256':owner.sha256_bytes(owner.canonical(proofs))}
            identifier='rollback-compatibility-'+hashlib.sha256(owner.canonical(identity)).hexdigest()[:24]
            record={'schema':owner.COMPATIBILITY_SCHEMA,'status':'verified','evidence_class':'simulated','target':identity['target'],'scope':identity['scope'],'historical_release':{'release_id':retained['release_id'],**rollback},'rollback':{'id':identifier,**contracts,'workloads':identity['workloads'],'proof_set_sha256':identity['proof_set_sha256']},'proof':{'qualified_at':'2026-10-26T10:00:00Z','receipt_count':1},'proof_set':proofs}
            candidate=evidence/owner.CANDIDATE_DIRECTORY/(identifier+'.yml');candidate.parent.mkdir();candidate.write_text(yaml.safe_dump(record))
            owner.record_compatibility(evidence,candidate)
            with patch.object(prepare,'ROOT',root),patch.object(prepare,'succession_control',return_value=owner):
                self.assertTrue(prepare.rollback_compatibility(rollback,identifier))
                self.assertTrue(prepare.retained_release(rollback))
                self.assertFalse(prepare.rollback_compatibility({**rollback,'image_digest':'sha256:'+'c'*64},identifier))
                self.assertFalse(prepare.rollback_compatibility(rollback,None))
                permission=root/contracts['permission_contract']['path'];before=permission.read_bytes();permission.write_text('changed-security-boundary: fixture\n')
                self.assertFalse(prepare.rollback_compatibility(rollback,identifier));self.assertTrue(prepare.retained_release(rollback))
                permission.write_bytes(before);self.assertTrue(prepare.rollback_compatibility(rollback,identifier))
                proof.write_text('{"evidence_class":"changed"}');self.assertFalse(prepare.rollback_compatibility(rollback,identifier))
            params=[{'ParameterKey':k,'ParameterValue':v} for k,v in {'ImageDigest':rollback['image_digest'],'RestoreVerifierImageDigest':rollback['image_digest'],'SupportImageDigest':'sha256:'+'b'*64,'SourceRevision':rollback['source_revision']}.items()]
            change={'ChangeSetName':'rollback-safe','Status':'CREATE_COMPLETE','ChangeSetType':'UPDATE','Parameters':params,'Changes':[{'ResourceChange':{'ResourceType':'AWS::ECS::TaskDefinition'}}]}
            self.assertTrue(transition.reviewable(change,'UPDATE_COMPLETE','rollback-safe',rollback['image_digest'],rollback['source_revision'],'sha256:'+'b'*64))
            self.assertFalse(transition.reviewable(change,'UPDATE_COMPLETE','rollback-safe',rollback['image_digest'],rollback['source_revision']))

    def test_provider_absence_is_operation_specific(self):
        path=ROOT/'scripts/04.deploy/shared/provider-adapters/aws/response.py'
        spec=importlib.util.spec_from_file_location('aws_response',path);adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        for service,operation,code in [('rds','describe-db-instances','DBInstanceNotFound'),('rds','describe-db-snapshots','DBSnapshotNotFound'),('iam','get-role-policy','NoSuchEntity'),('cloudformation','describe-change-set','ChangeSetNotFoundException')]:
            message=f'An error occurred ({code}) when calling the Fixture operation: synthetic-only'
            self.assertEqual(adapter.classify_error(service,operation,message),'aws-resource-missing')
            self.assertNotEqual(adapter.classify_error(service,'create-resource',message),'aws-resource-missing')
        for code in ['AccessDenied','ServiceFailure','ValidationError','ExpiredToken']:
            message=f'An error occurred ({code}) when calling the Fixture operation: resource not found and does not exist'
            self.assertNotEqual(adapter.classify_error('rds','describe-db-instances',message),'aws-resource-missing')
        self.assertEqual(adapter.classify_error('cloudformation','describe-stacks','An error occurred (ValidationError) when calling the DescribeStacks operation: Stack with id synthetic does not exist'),'aws-resource-missing')

if __name__=='__main__':unittest.main()
