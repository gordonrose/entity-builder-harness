#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.platform-shell-candidate-continuation
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise lost candidate submissions and bounded observation/cleanup through real subprocess interfaces.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.script.run-platform-shell-candidate-execution-preflight.smoke-test
#     path: scripts/04.deploy/run-platform-shell-candidate-execution-preflight/smoke-test.sh
import importlib.util
import json
import multiprocessing
import os
from datetime import datetime,timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[3]
CONTROLLER=Path('scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py')
CONTRACT=Path('infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/candidate-execution-preflight.v1.yml')
FAKE='''#!/usr/bin/env python3
import json,os,pathlib,sys
args=sys.argv[1:];op=args[1];p=pathlib.Path(os.environ['FIXTURE_STATE']);state=json.loads(p.read_text())
state['calls'].append(op)
def output(value):p.write_text(json.dumps(state));print(json.dumps(value));sys.exit(0)
if op=='get-caller-identity':output({'Account':'337159794548'})
if op=='describe-stacks':output({'Stacks':[{'StackStatus':'UPDATE_COMPLETE','Outputs':[{'OutputKey':'CandidatePreflightTaskDefinitionArn','OutputValue':'candidate-definition'}]}]})
if op=='describe-services':output({'services':[{'serviceName':'kanbien-staging-platform-shell','desiredCount':1,'runningCount':1,'taskDefinition':'server-definition','networkConfiguration':{'awsvpcConfiguration':{'assignPublicIp':'ENABLED','subnets':['subnet-safe'],'securityGroups':['sg-safe']}}}]})
if op=='describe-task-definition':output({'taskDefinition':{'family':'kanbien-staging-platform-shell-candidate-preflight' if args[args.index('--task-definition')+1]=='candidate-definition' else 'server','cpu':'512','memory':'1024','networkMode':'awsvpc','requiresCompatibilities':['FARGATE'],'runtimePlatform':{'cpuArchitecture':'X86_64','operatingSystemFamily':'LINUX'},'executionRoleArn':'role-safe','taskRoleArn':'runtime-safe','containerDefinitions':[{'name':'platform-shell','image':'fixture.invalid/image@sha256:'+'a'*64,'essential':True,'healthCheck':{'command':['CMD','node']}}]}})
if op=='list-tasks':
 assert '--started-by' not in args,'AWS rejects mixed startedBy filters'
 task=state.get('task');desired=args[args.index('--desired-status')+1]
 output({'taskArns':[task['taskArn']] if task and ((task['lastStatus']=='STOPPED')==(desired=='STOPPED')) else []})
if op=='describe-tasks':output({'tasks':[state['task']] if state.get('task') else []})
if op=='run-task':
 assert args[args.index('--client-token')+1]==args[args.index('--started-by')+1]
 state['task']={'taskArn':'task-safe','taskDefinitionArn':'candidate-definition','startedBy':args[args.index('--started-by')+1],'lastStatus':'PROVISIONING'}
 p.write_text(json.dumps(state));print('lost-response');sys.exit(0)
if op=='stop-task':state['task']['lastStatus']='STOPPED';output({})
raise AssertionError(op)
'''

def competing_reservation(source, path, letter, ready, start, results):
 spec=importlib.util.spec_from_file_location('candidate_concurrent',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 original=module.load_candidate_ledger
 def slow_load(*args,**kwargs):
  value=original(*args,**kwargs)
  # Widen the load/save window: the sibling must not read and overwrite it.
  import time
  time.sleep(.25)
  return value
 module.load_candidate_ledger=slow_load
 ready.put(letter);start.wait(5)
 try:results.put(('reserved',module.reserve_candidate_attempt('fixture@sha256:'+letter*64,Path(path),task_definition='task-'+letter)))
 except module.CandidatePreflightError as error:results.put(('blocked',str(error)))

class CandidateContinuation(unittest.TestCase):
 def test_concurrent_different_images_cannot_lose_a_permitted_reservation(self):
  with tempfile.TemporaryDirectory(prefix='candidate-concurrent-') as directory:
   path=Path(directory)/'receipts.json';context=multiprocessing.get_context('fork');ready=context.Queue();start=context.Event();results=context.Queue()
   processes=[context.Process(target=competing_reservation,args=(str(ROOT/CONTROLLER),str(path),letter,ready,start,results)) for letter in 'ab']
   for process in processes:process.start()
   self.assertEqual({ready.get(timeout=5),ready.get(timeout=5)},{'a','b'});start.set()
   outcomes=[results.get(timeout=10),results.get(timeout=10)]
   for process in processes:process.join(5);self.assertEqual(process.exitcode,0)
   permitted=[label for state,label in outcomes if state=='reserved'];self.assertEqual(len(permitted),1,outcomes)
   self.assertTrue(all(state=='reserved' or label in {'candidate-attempt-ledger-busy','candidate-prior-attempt-reconciliation-required'} for state,label in outcomes),outcomes)
   entries=json.loads(path.read_text())['attempts'];self.assertEqual([entry['label'] for entry in entries],permitted);self.assertEqual(entries[0]['state'],'reserved')

 def test_lost_response_never_replays_and_cleanup_requires_bound_observation(self):
  with tempfile.TemporaryDirectory(prefix='candidate-continuation-') as directory:
   root=Path(directory);subprocess.run(['git','init','-q',str(root)],check=True,capture_output=True)
   for relative in [CONTROLLER,CONTRACT,Path('infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml'),Path('scripts/04.deploy/operational-realization-gate/script.py'),Path('scripts/04.deploy/shared/provider-adapters/aws/response.py')]:
    target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
   inventory=root/'scripts/04.deploy/inventory-deploy-control/script.py';inventory.parent.mkdir(parents=True);inventory.write_text('print("covered synthetic fixture")\n')
   fake=root/'aws';fake.write_text(FAKE);fake.chmod(0o755);state=root/'provider.json';state.write_text('{"calls":[]}')
   spec=importlib.util.spec_from_file_location('realization',ROOT/'scripts/04.deploy/operational-realization-gate/script.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
   contract=yaml.safe_load((root/CONTRACT).read_text());_,known=owner.ids(contract);now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
   facts={'schema':owner.FACTS_SCHEMA,'contract_id':contract['id'],'gate_evidence':[{'gate':gate['id'],'check_id':gate['evidence'][0],'timestamp':now,'verdict':'passed'} for gate in contract['gates'][:6]],'component_evidence':[{'component_id':key,'component_kind':kind,'check_id':key+'-check','timestamp':now,'verdict':'passed'} for key,kind in known.items()],'artifact_bindings':[{'component_id':'candidate-runtime-artifact','immutable_reference':'sha256:'+'a'*64,'check_id':'candidate-artifact-check','timestamp':now,'verdict':'passed'}]}
   bindings=owner.evidence_bindings(contract,facts)
   for entry in facts['gate_evidence']:entry['input_sha256']=bindings['gates'][entry['gate']]
   for entry in facts['component_evidence']:entry['input_sha256']=bindings['components'][entry['component_id']]
   summary={'schema':owner.CHANGE_SCHEMA,'contract_id':contract['id'],'check_id':'candidate-change-shape-check','timestamp':now,'input_sha256':bindings['gates']['change-set'],'operation_counts':{'create':1,'update':0,'delete':0,'replace':0,'broaden-permission':0}}
   fact_path=root/'facts.yml';fact_path.write_text(yaml.safe_dump(facts));summary_path=root/'summary.yml';summary_path.write_text(yaml.safe_dump(summary))
   env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'FIXTURE_STATE':str(state),'PYTHONDONTWRITEBYTECODE':'1'}
   def run(*args):
    result=subprocess.run([sys.executable,'-B',str(root/CONTROLLER),*args],cwd=root,env=env,capture_output=True,text=True,timeout=20)
    return result,json.loads(result.stdout)
   execute=['--execute','--approve-candidate-execution-preflight','--realization-facts',str(fact_path),'--realization-change-summary',str(summary_path)]
   first,report=run(*execute);self.assertEqual(report['candidate_execution_preflight'],'uncertain',(first.stdout,first.stderr));self.assertEqual(first.returncode,1)
   again,report=run(*execute);self.assertEqual(report['failure_category'],'candidate-prior-attempt-reconciliation-required')
   self.assertEqual(json.loads(state.read_text())['calls'].count('run-task'),1)
   observed,report=run('--reconcile');self.assertEqual(report['candidate_execution_preflight'],'pending');self.assertEqual(observed.returncode,1)
   current=json.loads(state.read_text());task=current.pop('task');state.write_text(json.dumps(current))
   missing,report=run('--reconcile');self.assertEqual(report['candidate_execution_preflight'],'uncertain');self.assertEqual(report['failure_category'],'candidate-prior-submission-uncertain')
   current=json.loads(state.read_text());current['task']={**task,'taskDefinitionArn':'unrelated'};state.write_text(json.dumps(current))
   wrong,report=run('--cleanup','--approve-candidate-execution-preflight');self.assertEqual(report['failure_category'],'candidate-prior-task-identity-mismatch')
   current=json.loads(state.read_text());current['task']=task;state.write_text(json.dumps(current))
   cleaned,report=run('--cleanup','--approve-candidate-execution-preflight');self.assertEqual(cleaned.returncode,0);self.assertEqual(report['candidate_execution_preflight'],'cleaned-up')
   complete,report=run('--reconcile');self.assertEqual(complete.returncode,0);self.assertEqual(report['candidate_execution_preflight'],'reconciled')
   calls=json.loads(state.read_text())['calls'];self.assertEqual(calls.count('run-task'),1);self.assertEqual(calls.count('stop-task'),1)
   ledger=json.loads((root/'.git/postgresql-stage6-receipts/candidate-attempts.json').read_text());self.assertEqual(len(ledger['attempts']),1);self.assertEqual(ledger['attempts'][0]['state'],'stopped-reconciled')

if __name__=='__main__':unittest.main()
