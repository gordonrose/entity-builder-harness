#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.persistence-acceptance-route.impl
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Rehearse the complete acceptance route with actual controllers, temporary simulated evidence and controlled current observations.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.persistence-acceptance-route
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.sh
from __future__ import annotations
import contextlib
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
import yaml

ROOT=Path(__file__).resolve().parents[8]
RUN=Path('scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence')
TARGET=Path('infra/04.deploy/03.product/targets/kanbien-core-platform')
SCOPE=TARGET/'20-scopes/core-server-persistence'
CONTRACT=SCOPE/'00-declaration/declaration-contract.yml'
ROUTE=SCOPE/'00-declaration/acceptance-route-contract.yml'
RECORD=SCOPE/'30-release-evidence/accepted-release.yml'
CATALOG=Path('scripts/repo/check-selection/checks.yml')
ARN='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'
DEFINITION='arn:aws:ecs:eu-west-1:337159794548:task-definition/'
COUNT=0

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def passed(name):
    global COUNT
    COUNT+=1;print('PASS '+name)

def cli(path,*args,ok=True):
    result=subprocess.run(['bash',str(ROOT/path),*map(str,args)],cwd=ROOT,capture_output=True,text=True,check=False)
    try:report=json.loads(result.stdout)
    except json.JSONDecodeError:raise AssertionError((str(path),result.returncode,result.stdout,result.stderr)) from None
    assert (result.returncode==0)==ok,(str(path),report,result.stderr)
    return report

def capture(module,args):
    out=io.StringIO()
    with patch.object(sys,'argv',[str(module.__file__),*args]),contextlib.redirect_stdout(out):code=module.main()
    try:return code,json.loads(out.getvalue())
    except json.JSONDecodeError:raise AssertionError(out.getvalue()) from None

def custody(path,digest):
    value={'schema':'deploy/package-custody-receipt/v1','target':'kanbien-core-platform','environment_class':'private-bootstrap','provider_region_alias':'aws-eu-west-1','candidate_id':'kanbien-core-server-persistence-candidate','package_contract_id':'kanbien-core-server-persistence-image','program_id':'kanbien-core-server-persistence','source_revision':'a'*40,'image_digest':digest,'release_identity':'source-a','checked_at':'2026-10-25T12:00:00Z','checks':{name:'passed' for name in ['runnable_program_contract','dependency_boundary','delivery_access_static','delivery_access_live','local_image_smoke','ecr_scan','sbom','provenance_attestation']},'verdict':'qualified','receipt_reference':'github-actions-run:12345'}
    path.write_text(json.dumps(value));return str(path)

def hashes():
    files=[ROOT/RECORD,ROOT/TARGET/'20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml',ROOT/TARGET/'20-scopes/scope-index.yml',*(ROOT/SCOPE/'30-release-evidence/proof-receipts').glob('*.json')]
    # Durable live receipts accumulate as governed proofs complete. The
    # rehearsal protects byte-for-byte preservation of the current set below;
    # it must not assume a fixed historical receipt count.
    return {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}

def route_tests():
    route=load(Path('scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py'),'route_tests')
    coverage=load(Path('scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py'),'coverage_tests')
    catalog=yaml.safe_load((ROOT/CATALOG).read_text())
    assert route.inspect(ROOT/CONTRACT,ROOT)['verdict']=='covered'
    passed('complete template probes actual command parsers')
    original=yaml.safe_load((ROOT/ROUTE).read_text());read_text=Path.read_text
    def check_mutation(mutator,expected,no_probe=False):
        mutated=copy.deepcopy(original);mutator(mutated)
        def text(path,*a,**kw):return yaml.safe_dump(mutated) if path==ROOT/ROUTE else read_text(path,*a,**kw)
        with patch.object(Path,'read_text',text):
            if no_probe:
                with patch('subprocess.run',side_effect=AssertionError('invalid route executed command')):report=coverage.inspect(ROOT/CONTRACT,ROOT,catalog)
            else:report=coverage.inspect(ROOT/CONTRACT,ROOT,catalog)
        assert expected in {item['code'] for item in report['findings']},report
    def missing_mode(value):
        argv=value['commands']['current-health']['argv'];position=argv.index('--mode');del argv[position:position+2]
    check_mutation(missing_mode,'acceptance-route-command-arguments-invalid')
    passed('missing actual required mode fails through declaration coverage')
    check_mutation(lambda v:v['proofs']['credential-revocation'].__setitem__('command','migration-state-observation'),'acceptance-route-proof-command-contract-mismatch')
    check_mutation(lambda v:v['proofs']['migration-applied-state'].pop('deadline_workload'),'acceptance-route-proof-command-contract-mismatch')
    check_mutation(lambda v:v['proofs'].pop('isolated-restore'),'acceptance-route-required-proofs-mismatch',True)
    passed('valid wrong operation, missing proof contract and omitted required restore fail preflight')
    check_mutation(lambda v:v['proofs']['migration-applied-state'].__setitem__('command',[]),'acceptance-route-proof-binding-invalid',True)
    check_mutation(lambda v:v['commands']['collect'].__setitem__('effects',[]),'acceptance-route-command-owner-or-effects-mismatch',True)
    check_mutation(lambda v:v['commands']['collect'].__setitem__('owner','foreign.owner'),'acceptance-route-command-owner-or-effects-mismatch',True)
    check_mutation(lambda v:v['accepted_record'].__setitem__('schema_path','missing/schema.yml'),'acceptance-route-record-schema-missing',True)
    passed('malformed proof, wrong owner/effects and missing schema never execute commands')


def full_route():
    initial=hashes();fixtures=load(RUN/'acceptance-route-rehearsal/controller-fixtures.py','controller_fixtures')
    with tempfile.TemporaryDirectory(prefix='acceptance-route-rehearsal-') as directory:
        root=Path(directory);shutil.copytree(ROOT/TARGET,root/TARGET)
        shutil.copytree(ROOT/'.agentic/04.deploy/60-run/schemas',root/'.agentic/04.deploy/60-run/schemas')
        shutil.copytree(ROOT/'infra/04.deploy/03.product/image/core-server-persistence-observability-collector',root/'infra/04.deploy/03.product/image/core-server-persistence-observability-collector')
        image_contract=Path(yaml.safe_load((root/CONTRACT).read_text())['program']['image_contract']);(root/image_contract).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/image_contract,root/image_contract)
        shutil.rmtree(root/SCOPE/'30-release-evidence/proof-receipts');(root/RECORD).unlink()
        facts=fixtures.capture_proofs(root)
        assert len(facts['proof_receipts'])==15
        passed('actual controller observations retain all 15 simulated proof receipts')
        collector=load(RUN/'collect-acceptance-evidence/script.py','rehearsal_collector');collector.ROOT=root;collector.RECORD=root/RECORD;collector.EVIDENCE_CLASS='simulated'
        now=datetime.now(timezone.utc);stamp=lambda value:value.isoformat().replace('+00:00','Z')
        runnable='sha256:'+'c'*64;image='337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server@'+facts['candidate_digest']
        current=ARN+'f'*32;health=ARN+'e'*32
        definitions={'CoreServerPersistenceTaskDefinitionArn':DEFINITION+'kanbien-core-platform-core-server-persistence:1','CoreServerPersistenceVerifierTaskDefinitionArn':DEFINITION+'kanbien-core-platform-persistence-verifier:1','CoreServerPersistenceMigrationTaskDefinitionArn':DEFINITION+'kanbien-core-platform-persistence-migration:1','CoreServerPersistenceRestorationVerifierTaskDefinitionArn':DEFINITION+'kanbien-core-platform-persistence-restoration-verifier:1'}
        values={'candidate_receipt':custody(root/'candidate.json',facts['candidate_digest']),'rollback_receipt':custody(root/'rollback.json',facts['rollback_digest']),'proof_receipts':facts['proof_receipts'],'server_replacement_original':facts['original_task'],'server_replacement_successor':facts['successor_task'],'recovery_snapshot':facts['recovery_snapshot'],'record_proof_receipt':facts['record_proof_receipt'],'current_health_task':health}
        manifest=root/'inputs.yml';manifest.write_text(yaml.safe_dump({'schema':'deploy/acceptance-inputs/v1','target':'kanbien-core-platform','scope':'core-server-persistence','values':values}))
        health_task={'taskArn':health,'taskDefinitionArn':definitions['CoreServerPersistenceVerifierTaskDefinitionArn'],'lastStatus':'STOPPED','startedAt':stamp(now-timedelta(seconds=60)),'stoppedAt':stamp(now-timedelta(seconds=40)),'containers':[{'name':'private-persistence-verifier','exitCode':0,'image':image,'imageDigest':runnable}],'overrides':{'containerOverrides':[{'name':'private-persistence-verifier','environment':[{'name':'PERSISTENCE_VERIFIER_MODE','value':'health-ready'},{'name':'PERSISTENCE_ACCEPTANCE_RECORD_ID','value':'core-persistence-acceptance-v1'},{'name':'PERSISTENCE_ACCEPTANCE_FACT','value':'kanbien-core-persistence-acceptance-v1'}]}]}}
        observations=[];state={'healthy':True,'cleanup':True}
        def aws(*parts):
            observations.append(parts)
            if parts[:2]==('ecr','batch-get-image'):return {'images':[{'imageManifest':json.dumps({'manifests':[{'digest':runnable,'mediaType':'application/vnd.oci.image.manifest.v1+json','platform':{'architecture':'amd64','os':'linux'}}]})}]}
            if parts[:2]==('cloudformation','describe-stacks'):return {'Stacks':[{'StackStatus':'UPDATE_COMPLETE','Outputs':[{'OutputKey':k,'OutputValue':v} for k,v in definitions.items()]}]}
            if parts[:2]==('ecs','describe-services'):return {'services':[{'serviceName':collector.SERVICE,'status':'ACTIVE','desiredCount':1,'runningCount':1,'pendingCount':0,'taskDefinition':definitions['CoreServerPersistenceTaskDefinitionArn'],'deployments':[{'status':'PRIMARY','rolloutState':'COMPLETED'}]}]}
            if parts[:2]==('ecs','list-tasks'):return {'taskArns':[current]}
            if parts[:2]==('ecs','describe-tasks'):
                selected=parts[parts.index('--tasks')+1:]
                assert len(selected)==1 and selected[0] in {current,health},'historical task query forbidden: '+str(selected)
                if selected[0]==health:return {'tasks':[copy.deepcopy(health_task)]}
                return {'tasks':[{'taskArn':current,'taskDefinitionArn':definitions['CoreServerPersistenceTaskDefinitionArn'],'lastStatus':'RUNNING','healthStatus':'HEALTHY' if state['healthy'] else 'UNHEALTHY','group':'service:'+collector.SERVICE,'overrides':{'containerOverrides':[],'inferenceAcceleratorOverrides':[]},'containers':[{'name':'core-server-persistence','image':image,'imageDigest':runnable}]}]}
            if parts[:2]==('ecs','describe-task-definition'):
                definition=parts[-1];name='core-server-persistence' if definition==definitions['CoreServerPersistenceTaskDefinitionArn'] else 'private-persistence-verifier';return {'taskDefinition':{'taskDefinitionArn':definition,'family':definition.rsplit('/',1)[-1].rsplit(':',1)[0],'containerDefinitions':[{'name':name,'image':image,'environment':[{'name':'PLATFORM_SOURCE_COMMIT_SHA','value':'a'*40}]}]}}
            if parts[:2]==('logs','get-log-events'):return {'events':[{'message':json.dumps({'verdict':'accepted','code':'KANBIEN_CORE_PERSISTENCE_HEALTHY'})}]}
            if parts[:2]==('rds','describe-db-instances'):return {'DBInstances':[{'DBInstanceIdentifier':collector.DATABASE,'DBInstanceStatus':'available','Engine':'postgres','PubliclyAccessible':False,'StorageEncrypted':True,'DeletionProtection':True,'DbiResourceId':'db-FIXTURE-SOURCE','InstanceCreateTime':stamp(now-timedelta(days=1))}]}
            if parts[:2]==('rds','describe-db-snapshots'):return {'DBSnapshots':[{'DBSnapshotIdentifier':facts['recovery_snapshot'],'Status':'available','Encrypted':True,'DBInstanceIdentifier':collector.DATABASE,'SnapshotCreateTime':facts['snapshot_created_at'],'DbiResourceId':'db-FIXTURE-SOURCE'}]}
            raise AssertionError('unexpected provider call '+str(parts))
        real_run=subprocess.run
        def run(argv,*args,**kwargs):
            if argv[0]=='aws':
                assert argv[1:3]==['rds','describe-db-instances'] and '-restore-' in argv[4],argv
                return subprocess.CompletedProcess(argv,1 if state['cleanup'] else 0,'{}','DBInstanceNotFound' if state['cleanup'] else '')
            return real_run(argv,*args,**kwargs)
        with patch.object(collector,'aws',aws),patch.object(collector,'live_budget',lambda:None),patch('subprocess.run',run):
            state['healthy']=False;code,report=capture(collector,['--inputs',str(manifest),'--write','--json']);assert code and report['findings']==[{'code':'acceptance-evidence-current-service-task-invalid'}] and not collector.RECORD.exists(),report
            state['healthy']=True;state['cleanup']=False;code,report=capture(collector,['--inputs',str(manifest),'--write','--json']);assert code and report['findings']==[{'code':'acceptance-evidence-restored-database-not-cleaned-up'}] and not collector.RECORD.exists(),report
            state['cleanup']=True;original=(health_task['startedAt'],health_task['stoppedAt']);health_task['startedAt']=stamp(now-timedelta(hours=1));health_task['stoppedAt']=stamp(now-timedelta(minutes=59,seconds=40));code,report=capture(collector,['--inputs',str(manifest),'--write','--json']);assert code and report['findings']==[{'code':'acceptance-evidence-current-health-stale-or-mismatched'}] and not collector.RECORD.exists(),report;health_task['startedAt'],health_task['stoppedAt']=original
            passed('fresh unhealthy, stale readiness and remaining restore block writes')
            code,report=capture(collector,['--inputs',str(manifest),'--write','--json']);assert code==0 and report['verdict']=='recorded',report
        record=yaml.safe_load(collector.RECORD.read_text());assert record['status']=='rehearsed' and record['evidence_class']=='simulated'
        assert {parts[-1] for parts in observations if parts[:2]==('ecs','describe-tasks')}=={health,current}
        passed('complete collector writes temporary rehearsal using zero historical task queries')
        validator=RUN/'validate-accepted-release/script.sh'
        cli(validator,'--record',collector.RECORD,'--root',root,'--json',ok=False)
        cli(validator,'--record',collector.RECORD,'--rehearsal-root',root,'--json')
        passed('production rejects simulation; explicit temporary rehearsal validates retained chain')
        with patch.object(collector,'RECORD',ROOT/RECORD):
            try:collector.write_record(record)
            except collector.EvidenceFailure as error:assert str(error)=='acceptance-evidence-simulation-production-write-forbidden'
            else:raise AssertionError('simulation written to canonical evidence')
        receipts=collector.receipt_module();receipt=json.loads(Path(facts['record_proof_receipt']).read_text())
        for field,value in [('proof_type',[]),('operation',[]),('operation','../escape')]:
            malformed=copy.deepcopy(receipt);malformed[field]=value
            try:receipts.validate(malformed)
            except receipts.ReceiptError:pass
            else:raise AssertionError('malformed imported receipt accepted')
        passed('simulation cannot write canonical evidence and malformed receipts fail safely')
        corrupted=copy.deepcopy(record);corrupted['provider_observation']['database']['snapshot']=facts['recovery_snapshot']+'x'
        try:collector.validate_record(corrupted,evidence_class='simulated')
        except collector.EvidenceFailure:pass
        else:raise AssertionError('mismatched recovery context accepted')
        passed('record validation rejects cross-proof snapshot mismatch')
        # Exercise actual promotion and downstream validators in the temporary target.
        index=root/TARGET/'20-scopes/scope-index.yml';value=yaml.safe_load(index.read_text())
        for entry in value['scopes']:
            if entry['id']=='core-server-persistence':entry['lifecycle']='candidate'
            else:entry['lifecycle']='active';entry.pop('successor',None)
        index.write_text(yaml.safe_dump(value,sort_keys=False))
        bootstrap=root/TARGET/'20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml';record_b=yaml.safe_load(bootstrap.read_text());record_b.update(status='rehearsed',evidence_class='simulated');bootstrap.write_text(yaml.safe_dump(record_b))
        for field in ('last_rehearsal','last_restoration_rehearsal'):
            retained=bootstrap.parent/record_b['acceptance'][field];item=yaml.safe_load(retained.read_text());item['evidence_class']='simulated';retained.write_text(yaml.safe_dump(item))
        promotion=load(Path('scripts/04.deploy/lifecycle/60-run/promote-accepted-scope/script.py'),'promotion_test');route_api=promotion.route_module();route,path=route_api.load_route(root/CONTRACT,root);route['commands'][route['accepted_record']['validator']]['effects']=['aws-mutation']
        with patch.object(route_api,'load_route',return_value=(route,path)),patch.object(promotion,'route_module',return_value=route_api),patch('subprocess.run',side_effect=AssertionError('untrusted validator executed')):
            try:promotion.promote(root/CONTRACT,root,True,True)
            except ValueError as error:assert str(error)=='scope-promotion-validator-owner-or-effects-invalid'
            else:raise AssertionError('promotion accepted mutating validator')
        passed('direct promotion rejects a mutating record validator before invocation')
        original_record=collector.RECORD.read_text();foreign=copy.deepcopy(record);foreign['scope']='bootstrap-runtime';collector.RECORD.write_text(yaml.safe_dump(foreign))
        with patch('subprocess.run',side_effect=AssertionError('foreign record invoked validator')):
            try:promotion.promote(root/CONTRACT,root,True,True)
            except ValueError as error:assert str(error)=='scope-promotion-record-subject-invalid'
            else:raise AssertionError('foreign record promoted scope')
            lifecycle=load(Path('scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.py'),'lifecycle_identity_test')
            assert lifecycle.acceptance_codes(yaml.safe_load((root/CONTRACT).read_text()),root/CONTRACT,root)==['scope-lifecycle-accepted-release-identity-invalid']
        collector.RECORD.write_text(original_record)
        with tempfile.TemporaryDirectory(prefix='acceptance-outside-root-') as sibling:
            with patch('subprocess.run',side_effect=AssertionError('outside root invoked validator')):
                try:promotion.promote(root/CONTRACT,Path(sibling),True,True)
                except ValueError as error:assert str(error)=='scope-promotion-path-outside-root'
                else:raise AssertionError('outside-root index promoted')
        index_before=index.read_text();invalid=copy.deepcopy(value);invalid['scopes'].append(copy.deepcopy(invalid['scopes'][1]));index.write_text(yaml.safe_dump(invalid));invalid_bytes=index.read_bytes()
        try:promotion.promote(root/CONTRACT,root,True,True)
        except ValueError as error:assert str(error)=='scope-promotion-inventory-invalid',error
        else:raise AssertionError('duplicate scope promoted')
        assert index.read_bytes()==invalid_bytes
        index.write_text(index_before)
        passed('promotion and downstream reject foreign evidence, outside roots and invalid current ownership before writes')
        cli(Path('scripts/04.deploy/lifecycle/60-run/promote-accepted-scope/script.sh'),'--scope-contract',root/CONTRACT,'--rehearsal-root',root,'--write','--json')
        promoted=yaml.safe_load(index.read_text());assert [item['lifecycle'] for item in promoted['scopes']]==['accepted-historical','active']
        cli(Path('scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh'),'--target-root',root/TARGET/'20-scopes','--rehearsal-root',root,'--json')
        cli(Path('scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh'),'--target-root',root/TARGET,'--rehearsal-root',root,'--json')
        passed('actual promotion and lifecycle/target downstream gates accept complete temporary route')
        # Incomplete inputs and old raw task forms fail safely without provider access.
        with patch.object(collector,'aws',side_effect=AssertionError('malformed input queried provider')):
            code,report=capture(collector,['--receipt']);assert code and report['findings'],report
            code,report=capture(collector,['--receipt',values['candidate_receipt'],'--rollback-receipt',values['rollback_receipt'],'--server-replacement-original',facts['original_task'],'--server-replacement-successor',facts['successor_task'],'--recovery-snapshot',facts['recovery_snapshot'],'--record-proof-receipt',facts['record_proof_receipt'],'--current-health-task',health,'--proof','server-replacement='+facts['original_task']]);assert code and report['findings']==[{'code':'acceptance-evidence-retained-proof-receipts-required'}],report
            broken=yaml.safe_load(manifest.read_text());del broken['values']['proof_receipts']['migration-applied-state'];manifest.write_text(yaml.safe_dump(broken));code,report=capture(collector,['--inputs',str(manifest),'--json']);assert code and report['findings'],report
        passed('missing argument and incomplete retained proof set return structured pre-observation failures')
    assert hashes()==initial,'genuine accepted evidence changed'
    passed('all genuine accepted evidence and lifecycle files preserved byte-for-byte')

if __name__=='__main__':
    route_tests();full_route();print(json.dumps({'schema':'deploy/acceptance-route-rehearsal-report/v1','verdict':'passed','evidence_class':'simulated','checks':COUNT}))
