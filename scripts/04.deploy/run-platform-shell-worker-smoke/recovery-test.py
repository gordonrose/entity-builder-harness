#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.platform-shell-worker-recovery
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise worker CLI lost-response cleanup and read-only reconciliation against disposable provider fixtures.
#   portability: { class: internal, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.run-platform-shell-worker-smoke.smoke-test
#     path: scripts/04.deploy/run-platform-shell-worker-smoke/smoke-test.sh
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
SCRIPT=Path(__file__).with_name('script.py')
spec=importlib.util.spec_from_file_location('worker_fixture_subject',SCRIPT)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
policy=module.resolve_policy(module.load_profile(ROOT/module.DEFAULT_PROFILE))
FAKE='''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
path=Path(os.environ['WORKER_FIXTURE_STATE']);state=json.loads(path.read_text());args=sys.argv[1:];action=' '.join(args[:2]);state['calls'].append(args[:2]);response={};failed=False
if action=='sts get-caller-identity':response={'Account':state['account']}
elif action=='sqs get-queue-url':response={'QueueUrl':'fixture-dlq' if args[args.index('--queue-name')+1]==state['dlq_name'] else 'fixture-source'}
elif action=='sqs get-queue-attributes':
 queue='dlq' if args[args.index('--queue-url')+1]=='fixture-dlq' else 'source';response={'Attributes':{'ApproximateNumberOfMessages':str(state[queue]),'ApproximateNumberOfMessagesNotVisible':str(state[queue+'_inflight'])}}
 if state['scenario']=='read-denied':failed=True
elif action=='ecs describe-services':response={'services':[{'taskDefinition':'fixture-task:7','desiredCount':state['desired'],'runningCount':state['running'],'pendingCount':state['pending']}]}
elif action=='sqs send-message':
 state['source']=0 if state['running'] else 1
 if state['scenario']=='lost-send':failed=True
elif action=='ecs update-service':
 value=int(args[args.index('--desired-count')+1]);state['updates'].append(value)
 if value==0 and state['scenario']=='lost-start-cleanup-denied':failed=True
 else:
  state['desired']=state['running']=value
  if value==1:
   state['source']=0
   if state['scenario']=='residual-source':state['source']=1
   if state['scenario']=='residual-dlq':state['dlq_inflight']=1
  if (value==1 and state['scenario'] in ('lost-start','lost-start-cleanup-denied','residual-source','residual-dlq')) or (value==0 and state['scenario']=='lost-stop'):failed=True
else:raise RuntimeError('unexpected fixture operation')
path.write_text(json.dumps(state))
if failed:print('private-provider-canary',file=sys.stderr);sys.exit(1)
print(json.dumps(response))
'''
# Only elapsed-time waiting is accelerated; the real parser/main/process and
# each provider subprocess, emitted report and exit status are exercised.
DRIVER="import runpy,sys,time,itertools,subprocess; ticks=itertools.count(0,100);time.monotonic=lambda:next(ticks);time.sleep=lambda seconds:None;sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"

with tempfile.TemporaryDirectory(prefix='worker-recovery-') as directory:
    root=Path(directory);aws=root/'aws';aws.write_text(FAKE);aws.chmod(0o755);state_path=root/'state.json';checks=0
    def run(scenario,operation,expected,verdict,patch=None):
        global checks
        state={'scenario':scenario,'account':policy['account_id'],'dlq_name':policy['dead_letter_queue_name'],'desired':0,'running':0,'pending':0,'source':0,'source_inflight':0,'dlq':0,'dlq_inflight':0,'calls':[],'updates':[]}
        state.update(patch or {});state_path.write_text(json.dumps(state))
        args=[sys.executable,'-B','-c',DRIVER,str(SCRIPT),operation,'--aws-cli',str(aws),'--timeout-seconds','60']
        if operation=='--execute':args.append('--approve-live-worker-smoke')
        result=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,env={**os.environ,'WORKER_FIXTURE_STATE':str(state_path)})
        assert result.returncode==expected,(scenario,result.returncode,result.stdout,result.stderr)
        assert json.loads(result.stdout)['worker_smoke']==verdict,(scenario,result.stdout)
        assert 'private-provider-canary' not in result.stdout+result.stderr
        after=json.loads(state_path.read_text());checks+=1
        if operation=='--reconcile':assert not after['updates'] and all(call[1] not in ('send-message','update-service') for call in after['calls'])
        return after,result
    after,_=run('valid','--execute',0,'passed');assert after['updates']==[1,0]
    after,_=run('lost-start','--execute',1,'inconclusive');assert after['updates']==[1,0] and after['desired']==0
    after,result=run('lost-start-cleanup-denied','--execute',1,'cleanup-failed');assert after['updates']==[1,0]
    assert 'an approved AWS worker-proof operation did not complete' in result.stderr and 'cleanup could not confirm' in result.stderr
    run('lost-stop','--execute',0,'passed')
    after,_=run('lost-send','--execute',1,'cleanup-failed');assert after['updates']==[0] and after['source']==1
    run('residual-source','--execute',1,'cleanup-failed')
    run('residual-dlq','--execute',1,'cleanup-failed')
    run('valid','--reconcile',0,'cleaned-up')
    for key in ('desired','running','pending','source','source_inflight','dlq','dlq_inflight'):
        run('valid','--reconcile',1,'pending',{key:1})
    run('read-denied','--reconcile',1,'uncertain')
    result=subprocess.run([sys.executable,'-B',str(SCRIPT),'--reconcile','--execute'],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==2;checks+=1
    print(json.dumps({'schema':'deploy/worker-recovery-test/v1','verdict':'passed','evidence_class':'simulated','cli_checks':checks}))
