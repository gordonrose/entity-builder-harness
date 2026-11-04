#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.rehearse-accepted-workload-replacement
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the controlled accepted-workload replacement command rejects selector substitution and preserves safe task identity handling.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh
ROOT="$(git rev-parse --show-toplevel)"
COMMAND="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.sh"
if output="$("$COMMAND" --target kanbien/staging 2>&1)"; then
  echo "ERROR: fixed replacement rehearsal accepted a target selector" >&2; exit 1
fi
[[ "$output" == *"workload-recovery-arguments-invalid"* ]] || { echo "ERROR: missing fixed-target rejection" >&2; exit 1; }
[[ "$output" != *"kanbien/staging"* ]] || { echo "ERROR: unsafe selector echo" >&2; exit 1; }
python3 - "$COMMAND" <<'PY'
import importlib.util, sys
from pathlib import Path
from unittest.mock import patch
import contextlib, io, json
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location("rehearsal", Path(sys.argv[1]).with_name("script.py"))
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
canonical="arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/0123456789abcdef0123456789abcdef"
assert module.task_suffix({"taskArn":canonical}) == "456789abcdef"
for value in ['private-identity-canary',canonical.replace('337159794548','123456789012'),canonical.replace('eu-west-1','eu-west-2'),canonical.replace('/kanbien-core-platform/','/foreign/'),canonical[:-1],canonical.upper(),canonical+'\nprivate-identity-canary']:
    assert module.task_arn_is_reportable(value) is False
    assert module.task_suffix({'taskArn':value})=='identity-unavailable'
class Failed:
    returncode = 1
    stdout = ""
    stderr = ""
with patch.object(module.subprocess, "run", return_value=Failed()):
    assert module.preflight({}, Path("/tmp/accepted-receipt.json")) == (None, "cost-condition-not-approved")
with patch.object(module.subprocess, 'run', side_effect=OSError('private-canary')) as call:
    assert module.aws('ecs','stop-task')==(False,None,'aws-command-unavailable')
    assert call.call_count==1
with patch.object(module,'aws',return_value=(True,{'services':[]},'ok')) as call:
    assert module.current_workload({})==(None,'runtime-service-count-invalid')
    assert call.call_count==1
service={'status':'ACTIVE','desiredCount':1,'runningCount':1,'taskDefinition':'definition','deployments':[{'status':'PRIMARY','rolloutState':'COMPLETED'}]}
with patch.object(module,'aws',side_effect=[(True,{'services':[service]},'ok'),(True,{'taskArns':['task']},'ok'),(True,{'tasks':[]},'ok')]) as call:
    assert module.current_workload({'runtime_task_definition':'definition'})==(None,'runtime-task-count-invalid')
    assert call.call_count==3
for service_value in ([None], [{'status':'ACTIVE','desiredCount':1,'runningCount':1,'taskDefinition':None}], [{'status':'ACTIVE','desiredCount':1,'runningCount':1,'taskDefinition':'definition','deployments':[None]}]):
    with patch.object(module,'aws',return_value=(True,{'services':service_value},'ok')) as call:
        assert module.current_workload({'runtime_task_definition':'definition'})==(None,'runtime-service-observation-invalid')
        assert call.call_count==1
release={'source_revision':'a'*40,'image_digest':'sha256:'+'b'*64,'runtime_task_definition':'runtime:10','verifier_task_definition':'kanbien-core-platform-release-verifier:11'}
original={'taskArn':canonical};replacement={'taskArn':canonical[:-1]+'a'}
def invoke():
    out=io.StringIO()
    with contextlib.redirect_stdout(out),patch.object(sys,'argv',['fixture','--execute']):status=module.main()
    return status,[json.loads(line) for line in out.getvalue().splitlines()]
for child_facts in [{'verifier_task_definition':release['verifier_task_definition'],'verification_mode':'fresh-private-task'},{'verifier_task_definition':release['verifier_task_definition'],'verification_mode':'reused-completed-private-task'},{'verifier_task_definition':'private-report-canary','verification_mode':'private-report-canary'},None,{},[],0,False,'',1]:
    with patch.object(module,'accepted_release',return_value=release),patch.object(module,'receipt',return_value=None),patch.object(module,'preflight',return_value=(original,'ok')),patch.object(module,'aws',return_value=(True,{},'ok')) as provider,patch.object(module,'replacement',return_value=(replacement,'ok')),patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'facts':child_facts}))):
        status,reports=invoke()
    projectable=not child_facts or isinstance(child_facts,dict)
    assert status==(0 if projectable else 1) and reports[-1]['verdict']==('accepted' if projectable else 'uncertain'),reports
    if projectable:
        supported=isinstance(child_facts,dict) and child_facts.get('verifier_task_definition')==release['verifier_task_definition']
        assert reports[-1]['facts']['verifier_task_definition']==(release['verifier_task_definition'] if supported else None)
        assert reports[-1]['facts']['verification_mode']==(child_facts['verification_mode'] if supported else None)
    assert provider.call_count==1 and provider.call_args.args[:2]==('ecs','stop-task')
    assert 'private-report-canary' not in json.dumps(reports)
class CleanupFailure:
    def __enter__(self):return '/tmp/fixture-only'
    def __exit__(self,*args):raise OSError('private-cleanup-canary')
with patch.object(module,'accepted_release',return_value=release),patch.object(module,'receipt',return_value=None),patch.object(module,'preflight',return_value=(original,'ok')),patch.object(module,'aws',return_value=(True,{},'ok')),patch.object(module,'replacement',return_value=(replacement,'ok')),patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'facts':{'verifier_task_definition':release['verifier_task_definition'],'verification_mode':'fresh-private-task'}}))),patch.object(module.tempfile,'TemporaryDirectory',return_value=CleanupFailure()):
    status,reports=invoke()
assert status==1 and [report['verdict'] for report in reports]==['accepted','uncertain'],reports
assert reports[-1]['findings']==[{'code':'replacement-temporary-cleanup-unavailable'}]
assert 'private-cleanup-canary' not in json.dumps(reports)
PY
