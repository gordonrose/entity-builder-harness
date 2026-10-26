#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.persistence-acceptance-route.impl
#   version: 2
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
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
    evidence = ROOT / SCOPE / '30-release-evidence'
    files=[ROOT/RECORD,ROOT/TARGET/'20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml',ROOT/TARGET/'20-scopes/scope-index.yml',*(evidence/'proof-receipts').glob('*.json'),*(evidence/'observability-receipts').glob('*.json')]
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
    check_mutation(lambda v:v.pop('release_succession'),'acceptance-route-release-succession-missing',True)
    check_mutation(lambda v:v['release_succession'].__setitem__('promotion','promote'),'acceptance-route-release-succession-command-invalid',True)
    check_mutation(lambda v:v.pop('outputs'),'acceptance-route-outputs-invalid',True)
    check_mutation(lambda v:v.pop('candidate_validator'),'acceptance-route-stage-missing',True)
    check_mutation(lambda v:v.__setitem__('release_succession',{'not_applicable':'accepted-historical'}),'acceptance-route-succession-non-applicability-invalid',True)
    passed('malformed proof, missing succession, scope activation substitution, wrong owner/effects and missing schema never execute commands')



def fresh_verifier_route_tests():
    """Resolve the declared phase argv and exercise real CLI producer/consumer IDs."""
    route_api=load(Path('scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py'),'fresh_route_api')
    operation_tests=load(RUN/'verify-candidate/operation-test.py','fresh_operation_fixture')
    route=yaml.safe_load((ROOT/ROUTE).read_text())
    phases=['server-replacement-read','credential-revocation-unready','credential-recovery-health','credential-recovery-read','rollback-b-health','rollback-b-read','rollback-final-health','rollback-final-read','current-health']
    fixture=operation_tests.Fixture();temporary=fixture.root
    latest={};proofs={}
    try:
        fixture.update(submission='normal',status='STOPPED')
        def invoke(argv):
            result=subprocess.run(argv,cwd=fixture.root,env=fixture.env,capture_output=True,text=True,timeout=20)
            return result,json.loads(result.stdout)
        for name in phases:
            command=route['commands'][name];argv=command['argv'];mode=argv[argv.index('--mode')+1]
            predecessor_key=name.replace('-','_')+'_predecessor'
            assert '--new-operation' in argv and argv[argv.index('--expected-operation')+1]=='{'+predecessor_key+'}',name
            predecessor=latest.get(mode,'none');values={predecessor_key:predecessor}
            resolved=route_api.resolve(argv,values);assert resolved is not None
            before=len(fixture.runs());result,observed=invoke(resolved)
            assert result.returncode==0 and observed['verdict']=='accepted' and observed['facts']['evidence_reuse']=='fresh-terminal-observation',(name,result.stdout,result.stderr)
            current=observed['facts']['operation_id'];assert current!=predecessor and len(fixture.runs())==before+1
            latest[mode]=current;proof=fixture.root/observed['facts']['proof_receipt'];proofs[str(proof)]=hashlib.sha256(proof.read_bytes()).hexdigest()
            retry,reused=invoke(resolved)
            assert retry.returncode==0 and reused['facts']['operation_id']==current and reused['facts']['evidence_reuse']=='historical-completion' and len(fixture.runs())==before+1
            assert reused['facts']['proof_receipt']==observed['facts']['proof_receipt']
        passed('nine declared fresh verifier phases consume actual same-mode predecessor outputs; identical retries retain historical completion without new tasks')
        # Removing both successor flags is syntactically valid but cannot stand
        # in for a new phase: the actual command exposes retained completion.
        argv=route_api.resolve(route['commands']['credential-recovery-read']['argv'],{'credential_recovery_read_predecessor':latest['read']})
        old=list(argv);old.remove('--new-operation');at=old.index('--expected-operation');del old[at:at+2]
        before=len(fixture.runs());result,historical=invoke(old)
        assert result.returncode==0 and historical['facts']['evidence_reuse']=='historical-completion' and len(fixture.runs())==before
        invalid=list(argv);invalid.remove('--new-operation');result,blocked=invoke(invalid)
        assert result.returncode==1 and blocked['findings'][0]['code']=='private-persistence-verifier-new-operation-arguments-invalid' and len(fixture.runs())==before
        wrong=list(argv);wrong[wrong.index('--expected-operation')+1]=latest['health-ready'];result,blocked=invoke(wrong)
        assert result.returncode==1 and blocked['findings'][0]['code']=='private-persistence-verifier-operation-predecessor-mismatch' and len(fixture.runs())==before
        assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in proofs.items())
        passed('omitted fresh flags expose historical proof; incomplete and cross-mode predecessors block; prior immutable receipts remain unchanged')
    finally:fixture.close()
    assert not temporary.exists()
    passed('fresh-phase CLI rehearsal disposable operation state and provider effects are removed')


def full_route():
    initial=hashes();fixtures=load(RUN/'acceptance-route-rehearsal/controller-fixtures.py','controller_fixtures')
    with tempfile.TemporaryDirectory(prefix='acceptance-route-rehearsal-') as directory:
        root=Path(directory);shutil.copytree(ROOT/TARGET,root/TARGET)
        shutil.copytree(ROOT/'.agentic/04.deploy/60-run/schemas',root/'.agentic/04.deploy/60-run/schemas')
        shutil.copytree(ROOT/'infra/04.deploy/03.product/image/core-server-persistence-observability-collector',root/'infra/04.deploy/03.product/image/core-server-persistence-observability-collector')
        image_contract=Path(yaml.safe_load((root/CONTRACT).read_text())['program']['image_contract']);(root/image_contract).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/image_contract,root/image_contract)
        evidence_root=root/SCOPE/'30-release-evidence'
        # Construct a simulated predecessor in this disposable tree. Copied
        # live archives cannot be relabelled as simulated history.
        for name in ['current-accepted-release.yml','accepted-releases']:
            path=evidence_root/name
            if path.is_dir():shutil.rmtree(path)
            elif path.exists():path.unlink()
        legacy=yaml.safe_load((root/RECORD).read_text());legacy.update(status='rehearsed',evidence_class='simulated')
        (root/RECORD).write_text(yaml.safe_dump(legacy,sort_keys=False))
        cli(Path('scripts/04.deploy/lifecycle/60-run/release-succession/script.sh'),'--operation','initialize-legacy','--evidence-root',evidence_root,'--legacy-record',root/RECORD,'--expected-predecessor','none','--rehearsal-root',root,'--json')
        historical_record=(root/RECORD).read_bytes()
        initial_candidates={path:path.read_bytes() for path in (evidence_root/'release-candidates').glob('*.yml')}
        shutil.rmtree(evidence_root/'proof-receipts')
        facts=fixtures.capture_proofs(root)
        assert len(facts['proof_receipts'])==15
        passed('actual controller observations retain all 15 simulated proof receipts')
        collector=load(RUN/'collect-acceptance-evidence/script.py','rehearsal_collector');collector.ROOT=root;collector.RECORD=root/RECORD;collector.EVIDENCE_ROOT=evidence_root;collector.EVIDENCE_CLASS='simulated'
        now=datetime.now(timezone.utc);stamp=lambda value:value.isoformat().replace('+00:00','Z')
        runnable='sha256:'+'c'*64;image='337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server@'+facts['candidate_digest']
        current=ARN+'f'*32;health=ARN+'e'*32
        definitions={'CoreServerPersistenceTaskDefinitionArn':DEFINITION+'kanbien-core-platform-core-server-persistence:1','CoreServerPersistenceVerifierTaskDefinitionArn':DEFINITION+'kanbien-core-platform-persistence-verifier:1','CoreServerPersistenceMigrationTaskDefinitionArn':DEFINITION+'kanbien-core-platform-persistence-migration:1','CoreServerPersistenceRestorationVerifierTaskDefinitionArn':DEFINITION+'kanbien-core-platform-persistence-restoration-verifier:1'}
        observability_module=load(RUN/'observability-receipts.py','rehearsal_observability_receipts')
        observability_module.RECEIPTS=root/SCOPE/'30-release-evidence/observability-receipts'
        proof_module=load(RUN/'proof-receipts.py','rehearsal_task_receipts')
        def observability_source(path):
            raw=Path(path).read_bytes();proof=proof_module.validate(json.loads(raw))
            task=proof['task']
            return {'path':str(Path(path).relative_to(root)),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest(),'task_arn':task['arn'],'task_definition':task['definition'],'image_digest':task['image_digest'],'result_code':task['result_code']}
        failure_source=observability_source(facts['proof_receipts']['credential-revocation-unready'])
        recovery_source=observability_source(facts['proof_receipts']['credential-recovery-health'])
        failure_alarm=stamp(now-timedelta(minutes=4));failure_metric=stamp(now-timedelta(minutes=5));delivery=stamp(now-timedelta(minutes=3));recovery_metric=stamp(now-timedelta(minutes=2));recovery_alarm=stamp(now-timedelta(minutes=1))
        failure=observability_module.persist(observability_module.make(receipt_type='readiness-failure-observed',source_proof=failure_source,observation_value={'alarm_name':observability_module.ALARM,'alarm_state':'ALARM','alarm_state_updated_at':failure_alarm,'metric_name':observability_module.METRIC,'dimensions':observability_module.DIMENSIONS,'metric_value':0,'metric_observed_at':failure_metric},collected_at=failure_alarm,evidence_class='simulated'))
        notified=observability_module.persist(observability_module.make(receipt_type='readiness-alarm-notified',source_proof=failure_source,observation_value={'alarm_name':observability_module.ALARM,'alarm_state':'ALARM','alarm_state_updated_at':failure_alarm,'subscription_confirmed_at':stamp(now-timedelta(minutes=6)),'operator_delivery_confirmed_at':delivery},collected_at=delivery,evidence_class='simulated'))
        recovered=observability_module.persist(observability_module.make(receipt_type='readiness-recovery-observed',source_proof=recovery_source,observation_value={'alarm_name':observability_module.ALARM,'alarm_state':'OK','alarm_state_updated_at':recovery_alarm,'metric_name':observability_module.METRIC,'dimensions':observability_module.DIMENSIONS,'metric_value':1,'metric_observed_at':recovery_metric},collected_at=recovery_alarm,evidence_class='simulated'))
        observability_receipts={'readiness-failure-observed':str(failure),'readiness-alarm-notified':str(notified),'readiness-recovery-observed':str(recovered)}
        # Package custody is acceptance evidence too.  Keep the simulated
        # files in the same durable evidence root as production receipts so
        # the generic successor validator exercises its allowlisted-root rule.
        values={'candidate_receipt':custody(evidence_root/'package-receipts/candidate.json',facts['candidate_digest']),'rollback_receipt':custody(evidence_root/'package-receipts/rollback.json',facts['rollback_digest']),'proof_receipts':facts['proof_receipts'],'server_replacement_original':facts['original_task'],'server_replacement_successor':facts['successor_task'],'recovery_snapshot':facts['recovery_snapshot'],'record_proof_receipt':facts['record_proof_receipt'],'current_health_task':health,'proof_applicability':None,'observability_receipts':observability_receipts}
        values["rollback_compatibility_id"]="rollback-compatibility-"+"a"*24
        route_inputs=yaml.safe_load((ROOT/ROUTE).read_text())['inputs']
        values.update({key:spec['example'] for key,spec in route_inputs.items() if key.endswith('_predecessor')})
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
            parsed_observability = collector.parse_observability_receipts([name+'='+path for name,path in observability_receipts.items()], facts['candidate_digest'])
            assert set(parsed_observability) == set(observability_receipts)
            unchanged=lambda:{path:path.read_bytes() for path in (evidence_root/'release-candidates').glob('*.yml')}==initial_candidates
            state['healthy']=False;code,report=capture(collector,['--inputs',str(manifest),'--write-candidate','--json']);assert code and report['findings']==[{'code':'acceptance-evidence-current-service-task-invalid'}] and unchanged(),report
            state['healthy']=True;state['cleanup']=False;code,report=capture(collector,['--inputs',str(manifest),'--write-candidate','--json']);assert code and report['findings']==[{'code':'acceptance-evidence-restored-database-not-cleaned-up'}] and unchanged(),report
            state['cleanup']=True;original=(health_task['startedAt'],health_task['stoppedAt']);health_task['startedAt']=stamp(now-timedelta(hours=1));health_task['stoppedAt']=stamp(now-timedelta(minutes=59,seconds=40));code,report=capture(collector,['--inputs',str(manifest),'--write-candidate','--json']);assert code and report['findings']==[{'code':'acceptance-evidence-current-health-stale-or-mismatched'}] and unchanged(),report;health_task['startedAt'],health_task['stoppedAt']=original
            passed('fresh unhealthy, stale readiness and remaining restore block candidate publication')
            code,report=capture(collector,['--inputs',str(manifest),'--write-candidate','--json']);assert code==0 and report['verdict']=='recorded' and report['facts']['candidate_record'],report
            candidate_path=root/report['facts']['candidate_record'];candidate_bytes=candidate_path.read_bytes()
            candidate_value=yaml.safe_load(candidate_bytes)
            assert {'candidate-package','rollback-package','record-source','observability-readiness-failure-observed','observability-readiness-alarm-notified','observability-readiness-recovery-observed'} <= set(candidate_value['proof_set'])
            succession=load(Path('scripts/04.deploy/lifecycle/60-run/release-succession/script.py'),'retained_evidence_succession');succession.REPOSITORY_ROOT=root;succession.EVIDENCE_CLASS='simulated'
            protected=evidence_root/candidate_value['proof_set']['observability-readiness-recovery-observed']['path'];original_protected=protected.read_bytes()
            succession.candidate_identity(candidate_value,evidence_root)
            protected.write_bytes(b'{"fabricated":true}')
            try:
                succession.candidate_identity(candidate_value,evidence_root)
            except succession.SuccessionFailure: pass
            else: raise AssertionError('modified retained observability receipt accepted')
            protected.write_bytes(original_protected)
            code,resumed=capture(collector,['--inputs',str(manifest),'--write-candidate','--json']);assert code==0 and resumed['facts']==report['facts'] and candidate_path.read_bytes()==candidate_bytes,resumed
        assert (root/RECORD).read_bytes()==historical_record
        record=yaml.safe_load(collector.RECORD.read_text())
        assert {parts[-1] for parts in observations if parts[:2]==('ecs','describe-tasks')}=={health,current}
        passed('complete collector publishes an idempotent successor candidate using zero historical task queries and preserves history')
        succession=load(Path('scripts/04.deploy/lifecycle/60-run/release-succession/script.py'),'rehearsal_succession');succession.REPOSITORY_ROOT=root;succession.EVIDENCE_CLASS='simulated'
        candidate,raw=succession.document(candidate_path);target,scope,_,identity=succession.candidate_identity(candidate,evidence_root)
        current_reference=succession.current(evidence_root);assert current_reference is not None
        verdict,release_id=succession.promote(evidence_root,target=target,scope=scope,identity=identity,source_path=candidate_path,source_digest=succession.sha256_bytes(raw),expected_predecessor=current_reference['release_id'],legacy=False)
        assert verdict=='promoted' and release_id==report['facts']['release_id'] and succession.current(evidence_root)['release_id']==release_id
        passed('generic succession validates and atomically promotes the collector candidate after preserving the predecessor')
        # Keep the complete historical-succession scenario, then exercise first
        # scope activation with fresh observations in a separate evidence tree.
        prior_scenario=root/'historical-succession-scenario'
        evidence_root.rename(prior_scenario);evidence_root.mkdir()
        for name in ['proof-receipts','observability-receipts','package-receipts']:
            if (prior_scenario/name).exists():shutil.copytree(prior_scenario/name,evidence_root/name)
        with patch.object(collector,'aws',aws),patch.object(collector,'live_budget',lambda:None),patch('subprocess.run',run):
            code,fresh=capture(collector,['--inputs',str(manifest),'--write','--json']);assert code==0 and fresh['verdict']=='recorded',fresh
            code,fresh_candidate=capture(collector,['--inputs',str(manifest),'--write-candidate','--json']);assert code==0,fresh_candidate
        candidate_path=root/fresh_candidate['facts']['candidate_record']
        record=yaml.safe_load(collector.RECORD.read_text())

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
        except ValueError as error:assert str(error)=='scope-promotion-inventory-invalid',(str(error),route_api.inspect(root/CONTRACT,root,ROOT))
        else:raise AssertionError('duplicate scope promoted')
        assert index.read_bytes()==invalid_bytes
        index.write_text(index_before)
        passed('promotion and downstream reject foreign evidence, outside roots and invalid current ownership before writes')
        cli(Path('scripts/04.deploy/lifecycle/60-run/promote-accepted-scope/script.sh'),'--scope-contract',root/CONTRACT,'--rehearsal-root',root,'--write','--json')
        promoted=yaml.safe_load(index.read_text());assert [item['lifecycle'] for item in promoted['scopes']]==['accepted-historical','active']
        cli(Path('scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh'),'--target-root',root/TARGET/'20-scopes','--rehearsal-root',root,'--json')
        cli(Path('scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh'),'--target-root',root/TARGET,'--rehearsal-root',root,'--json')
        passed('actual promotion and lifecycle/target downstream gates accept complete temporary route')
        succession=Path('scripts/04.deploy/lifecycle/60-run/release-succession/script.sh')
        evidence=collector.RECORD.parent
        first=cli(succession,'--operation','initialize-legacy','--evidence-root',evidence,'--legacy-record',collector.RECORD,'--expected-predecessor','none','--rehearsal-root',root,'--json')
        predecessor=first['facts']['release_id'];accepted_bytes=collector.RECORD.read_bytes()
        successor=cli(succession,'--operation','promote','--evidence-root',evidence,'--candidate-record',candidate_path,'--expected-predecessor',predecessor,'--rehearsal-root',root,'--json')
        assert successor['facts']['release_id'] != predecessor and collector.RECORD.read_bytes()==accepted_bytes
        cli(succession,'--operation','validate-current','--evidence-root',evidence,'--rehearsal-root',root,'--json')
        cli(succession,'--operation','promote','--evidence-root',evidence,'--candidate-record',candidate_path,'--expected-predecessor',predecessor,'--rehearsal-root',root,'--json')
        cli(succession,'--operation','promote','--evidence-root',evidence,'--candidate-record',candidate_path,'--expected-predecessor','release-'+ '0'*24,'--rehearsal-root',root,'--json',ok=False)
        cli(RUN/'validate-accepted-release/script.sh','--record',collector.RECORD,'--rehearsal-root',root,'--json')
        passed('actual producer candidate uses evidence-relative paths and CLI succession preserves legacy, resumes idempotently and rejects stale predecessor')
        # Incomplete inputs and old raw task forms fail safely without provider access.
        with patch.object(collector,'aws',side_effect=AssertionError('malformed input queried provider')):
            code,report=capture(collector,['--receipt']);assert code and report['findings'],report
            code,report=capture(collector,['--receipt',values['candidate_receipt'],'--rollback-receipt',values['rollback_receipt'],'--server-replacement-original',facts['original_task'],'--server-replacement-successor',facts['successor_task'],'--recovery-snapshot',facts['recovery_snapshot'],'--record-proof-receipt',facts['record_proof_receipt'],'--current-health-task',health,'--proof','server-replacement='+facts['original_task']]);assert code and report['findings']==[{'code':'acceptance-evidence-retained-proof-receipts-required'}],report
            broken=yaml.safe_load(manifest.read_text());del broken['values']['proof_receipts']['migration-applied-state'];manifest.write_text(yaml.safe_dump(broken));code,report=capture(collector,['--inputs',str(manifest),'--json']);assert code and report['findings'],report
        passed('missing argument and incomplete retained proof set return structured pre-observation failures')
    assert hashes()==initial,'genuine accepted evidence changed'
    passed('all genuine accepted evidence and lifecycle files preserved byte-for-byte')

if __name__=='__main__':
    route_tests();fresh_verifier_route_tests();full_route();print(json.dumps({'schema':'deploy/acceptance-route-rehearsal-report/v1','verdict':'passed','evidence_class':'simulated','checks':COUNT}))
