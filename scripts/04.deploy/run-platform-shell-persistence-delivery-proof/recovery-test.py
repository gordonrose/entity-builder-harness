#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.platform-shell-persistence-delivery-recovery
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise fixed delivery stage CLI submission reservations, terminal capture, expiry, no-replay and cleanup against disposable provider fixtures.
#   portability: { class: internal, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.run-platform-shell-persistence-delivery-proof.smoke-test
#     path: scripts/04.deploy/run-platform-shell-persistence-delivery-proof/smoke-test.sh
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
SCRIPT=Path(__file__).with_name('script.py')
DRIVER='''import importlib.util,os,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('delivery',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=m.resolve_policy(m.load_profile());p['delivery_status']=m.RECOVERY_DEPLOYED_READY;m.resolve_policy=lambda _:p
m.PROFILE_PATH=Path(os.environ['DELIVERY_FIXTURE_ROOT'])/'source/target-profile.yml';m.RECEIPT_ROOT=Path(os.environ['DELIVERY_FIXTURE_ROOT'])/'receipts';m.load_profile=lambda:{}
sys.argv=sys.argv[1:]
try:raise SystemExit(m.main())
except (m.DeliveryProofError,OSError,m.subprocess.SubprocessError) as error:
 print(str(error) if isinstance(error,m.DeliveryProofError) else 'delivery-proof-operation-uncertain',file=sys.stderr);raise SystemExit(1)
'''
FAKE='''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
path=Path(os.environ['DELIVERY_FIXTURE_ROOT'])/'state.json';s=json.loads(path.read_text());a=sys.argv[1:];op=' '.join(a[:2]);s['calls'].append(op);result={}
def arg(name):return a[a.index(name)+1]
def task(kind,status):
 family='kanbien-staging-platform-shell-'+kind
 return {'taskArn':('wrong-task' if s.get('mismatched_task') else 'task-'+kind),'taskDefinitionArn':family+':1','startedBy':'kanbien-outbox-'+('worker-' if kind=='worker' else '')+'recovery-v3','group':'family:'+family,'lastStatus':status,'containers':[{'name':'platform-shell-'+kind,'exitCode':0,'imageDigest':s.get('image_digest','sha256:'+'a'*64)}]}
if op=='sts get-caller-identity':result={'Account':'337159794548'}
elif op=='cloudformation describe-stacks':result={'Stacks':[{'StackStatus':'UPDATE_COMPLETE','Outputs':[{'OutputKey':key,'OutputValue':value} for key,value in {'PlatformPersistenceTableName':'table','PlatformPersistenceOutboxDueIndexName':'due','WorkerQueueUrl':'source','WorkerDeadLetterQueueUrl':'dlq','PublicSubnetIdsCsv':'one,two','RelaySecurityGroupId':'relay-sg','TargetGroupArn':'target'}.items()]}]}
elif op=='elbv2 describe-target-health':result={'TargetHealthDescriptions':[{'TargetHealth':{'State':'healthy'}}]}
elif op=='dynamodb scan':result={'Count':s['records']}
elif op=='dynamodb query':result={'Count':s['due']}
elif op=='sqs get-queue-attributes':
 key=arg('--queue-url');result={'Attributes':{'ApproximateNumberOfMessages':str(s[key]),'ApproximateNumberOfMessagesNotVisible':str(s[key+'_inflight'])}}
elif op=='ecs describe-services':
 worker=arg('--services').endswith('-worker');result={'services':[{'desiredCount':0 if worker else 1,'runningCount':0 if worker else 1,'pendingCount':s['service_pending'] if worker else 0,'taskDefinition':'kanbien-staging-platform-shell-worker:1','networkConfiguration':{'awsvpcConfiguration':{'subnets':['one','two'],'securityGroups':['worker-sg'],'assignPublicIp':'ENABLED'}}}]}
elif op=='ecs describe-task-definition':
 name=arg('--task-definition');name=name if ':' in name else name+':1';result={'taskDefinition':{'taskDefinitionArn':name,'containerDefinitions':[{'name':'platform-shell-'+('worker' if 'worker' in name else 'relay'),'image':'fixture:mutable' if s.get('mutable_image') else 'fixture@sha256:'+'a'*64}],'taskRoleArn':'role'}}
elif op=='ecs list-tasks':
 kinds=[kind for kind in ('relay','worker') if s[kind] is not None]
 if '--started-by' in a:kinds=[kind for kind in kinds if task(kind,s[kind])['startedBy']==arg('--started-by') and s[kind]!='STOPPED']
 else:
  family=arg('--family');stopped='--desired-status' in a and arg('--desired-status')=='STOPPED';kinds=[kind for kind in kinds if family.endswith('-'+kind) and ((s[kind]=='STOPPED')==stopped)]
 result={'taskArns':['task-'+kind for kind in kinds]}
 if s['paginated']:result['nextToken']='incomplete'
elif op=='ecs describe-tasks':result={'tasks':[task(kind,s[kind]) for kind in ('relay','worker') if 'task-'+kind in a and s[kind] is not None],'failures':[]}
elif op=='ecs run-task':
 kind='worker' if arg('--task-definition').split(':')[0].endswith('-worker') else 'relay';s['submissions'].append({'kind':kind,'token':arg('--client-token')});s[kind]='PROVISIONING';result={'tasks':[task(kind,'PROVISIONING')],'failures':[]}
elif op=='cloudwatch describe-alarms':result={'MetricAlarms':[{'StateValue':'OK'}]*5}
else:raise RuntimeError('unexpected fixture operation')
path.write_text(json.dumps(s))
if op=='ecs run-task' and s['lose_response']:print('private-provider-canary',file=sys.stderr);sys.exit(1)
print(json.dumps(result))
'''
with tempfile.TemporaryDirectory(prefix='delivery-recovery-') as directory:
    root=Path(directory);(root/'source/cloudformation').mkdir(parents=True);(root/'source/cloudformation/service.yml').write_text('immutable: first\n')
    aws=root/'aws';aws.write_text(FAKE);aws.chmod(0o755);state_path=root/'state.json'
    initial={'calls':[],'submissions':[],'records':3,'due':1,'source':0,'source_inflight':0,'dlq':0,'dlq_inflight':0,'service_pending':0,'relay':None,'worker':None,'paginated':False,'lose_response':False};state_path.write_text(json.dumps(initial));checks=0
    def patch(**values):
        value=json.loads(state_path.read_text());value.update(values);state_path.write_text(json.dumps(value));return value
    def run(mode,expected=0,reason=None):
        global checks
        args=[sys.executable,'-B','-c',DRIVER,str(SCRIPT),mode]
        if mode.startswith('--start-'):args.append('--approve-outbox-delivery-recovery')
        result=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,env={**os.environ,'DELIVERY_FIXTURE_ROOT':str(root),'PATH':str(root)+os.pathsep+os.environ['PATH']})
        assert result.returncode==expected,(mode,result.stdout,result.stderr)
        if reason:assert reason in result.stdout+result.stderr,(reason,result.stdout,result.stderr)
        assert 'private-provider-canary' not in result.stdout+result.stderr
        checks+=1;return result
    patch(mutable_image=True);run('--start-relay',1,'immutable-image-required');assert not json.loads(state_path.read_text())['submissions']
    patch(mutable_image=False,lose_response=True);run('--start-relay',1,'did not complete')
    assert len(json.loads(state_path.read_text())['submissions'])==1
    run('--start-relay',1);assert len(json.loads(state_path.read_text())['submissions'])==1
    patch(mismatched_task=True);run('--assess-relay',1,'description was incomplete')
    patch(mismatched_task=False);run('--assess-relay',1,'outcome-pending')
    patch(relay=None);run('--reconcile',1,'uncertain');run('--start-relay',1);assert len(json.loads(state_path.read_text())['submissions'])==1
    patch(relay='STOPPED',source=1,due=0,lose_response=False,image_digest='sha256:'+'b'*64);run('--assess-relay',1,'observed-image-mismatch')
    patch(image_digest='sha256:'+'a'*64);run('--assess-relay',0,'relay-succeeded')
    terminal=next((root/'receipts').glob('*relay*terminal*'),None)
    # Capture before ECS expiry; later stages use the immutable receipt.
    patch(relay=None);run('--assess-relay',0,'relay-succeeded')
    patch(worker='PROVISIONING');run('--start-worker',1,'already started or completed')
    patch(worker=None,paginated=True);run('--start-worker',1,'inspection is incomplete')
    patch(paginated=False);run('--start-worker');assert len(json.loads(state_path.read_text())['submissions'])==2
    run('--assess-worker',1,'outcome-pending')
    patch(worker='STOPPED',source=0,records=4);run('--assess-worker',0,'worker-settled')
    captured={path:path.read_bytes() for path in (root/'receipts').glob('*.json')}
    patch(worker=None);run('--verify-terminal',0,'passed');run('--reconcile',0,'cleaned-up')
    for name in ('source','source_inflight','dlq','dlq_inflight','service_pending'):
        patch(**{name:1});run('--reconcile',1);patch(**{name:0})
    (root/'source/cloudformation/service.yml').write_text('immutable: changed\n');run('--verify-terminal',1,'receipt-inputs-changed')
    (root/'source/cloudformation/service.yml').write_text('immutable: first\n')
    for path,raw in captured.items():assert path.read_bytes()==raw
    run('--start-worker',1);assert len(json.loads(state_path.read_text())['submissions'])==2
    print(json.dumps({'schema':'deploy/persistence-delivery-recovery-test/v1','verdict':'passed','evidence_class':'simulated','cli_checks':checks}))
