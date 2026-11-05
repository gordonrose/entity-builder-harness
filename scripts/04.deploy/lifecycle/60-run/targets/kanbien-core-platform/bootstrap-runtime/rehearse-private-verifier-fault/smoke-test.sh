#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.rehearse-private-verifier-fault
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove fixed verifier-fault fixtures cannot accept arbitrary input and contain rejection/timeout behaviour without AWS access.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh
ROOT="$(git rev-parse --show-toplevel)"
COMMAND="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/script.sh"
if output="$("$COMMAND" --target kanbien/staging 2>&1)"; then
  echo "ERROR: fixed verifier fault rehearsal accepted a target selector" >&2; exit 1
fi
[[ "$output" == *"private-verifier-fault-arguments-invalid"* ]] || { echo "ERROR: missing selector rejection" >&2; exit 1; }
[[ "$output" != *"kanbien/staging"* ]] || { echo "ERROR: unsafe selector echo" >&2; exit 1; }
python3 - "$COMMAND" <<'PY'
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

script = Path(sys.argv[1]).with_name("script.py")
spec = importlib.util.spec_from_file_location("fault", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
actual_run_fault = module.run_fault
for shape in [1, {'private-canary':1}, [None]]:
    assert module.task_exit_code({'containers':shape}) is None

from unittest.mock import patch
with patch.object(module.subprocess,'run',side_effect=OSError('private-canary')) as call:
    assert module.aws('ecs','run-task')==(False,None,'aws-command-unavailable')
    assert call.call_count==1
canonical_prefix='arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'
observed={'taskArn':canonical_prefix+'c'*32,'taskDefinitionArn':'unproven-definition'}
with patch.object(module,'aws',return_value=(True,{'tasks':[observed]},'ok')) as call:
    assert module.run_fault('controller-deadline','expected-definition','subnets','group')==(observed,'private-verifier-fault-task-definition-mismatch')
    assert call.call_count==1
with patch.object(module,'aws',return_value=(True,{'events':[]},'ok')):
    assert module.task_log_contains(observed,'EXPECTED_CODE')==(False,'private-verifier-rejection-log-not-observed')
with patch.object(module,'aws',return_value=(True,{'tasks':[]},'ok')) as call:
    assert module.run_fault('controller-deadline','expected-definition','subnets','group')==(None,'private-verifier-fault-task-observation-unconfirmed')
    assert call.call_count==1

assert module.fault_override("expected-source-mismatch") == {
    "containerOverrides": [{"name": "private-release-verifier", "environment": [{"name": "KANBIEN_EXPECTED_SOURCE_REVISION", "value": "0" * 40}]}]
}
assert module.fault_override("controller-deadline") == {
    "containerOverrides": [{"name": "private-release-verifier", "command": ["-e", "setTimeout(() => process.exit(0), 121000)"]}]
}

release = {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64, "runtime_task_definition": "runtime:10"}
accepted = {"taskArn": canonical_prefix+'a'*32}
fixture = {"taskArn": canonical_prefix+'b'*32, "taskDefinitionArn": "verifier:11"}
module.REPLACEMENT.accepted_release = lambda: release
module.REPLACEMENT.receipt = lambda _release, _path: None
module.REPLACEMENT.preflight = lambda _release, _path: (accepted, "ok")
module.outputs = lambda name: (({"ReleaseVerifierTaskDefinitionArn": "verifier:11"} if name == module.RUNTIME_STACK else {"PrivateSubnetIds": "subnet-a,subnet-b", "VerifierSecurityGroupId": "sg-a"}), "ok")
module.VERIFIER.verifier_completion_deadline = lambda: 120
module.service_unchanged = lambda _release, _task: True

def invoke(*args):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        prior = sys.argv
        sys.argv = ["fault", *args]
        try:
            status = module.main()
        finally:
            sys.argv = prior
    return status, json.loads(output.getvalue())

status, report = invoke("--case", "expected-source-mismatch", "--json")
assert status == 0 and report["verdict"] == "prepared", report

calls = []
module.run_fault = lambda case, definition, subnets, sg: (calls.append((case, definition, subnets, sg)) or fixture, "ok")
module.VERIFIER.wait_for_verifier_stop = lambda *_args: ("stopped", {**fixture, "containers": [{"exitCode": 1}]})
module.VERIFIER.completed_within_deadline = lambda *_args: (True, "ok")
module.VERIFIER.verifier_duration_seconds = lambda _task: 2
module.task_log_contains = lambda _task, code: (code == "KANBIEN_CORE_RELEASE_VERIFICATION_FAILED", "ok")
status, report = invoke("--case", "expected-source-mismatch", "--execute", "--json")
assert status == 0 and report["verdict"] == "rejected-as-expected", report
assert calls == [("expected-source-mismatch", "verifier:11", "subnet-a,subnet-b", "sg-a")], calls
with patch.object(module.VERIFIER,'completed_within_deadline',return_value=(False,'ok')):
    status, report=invoke('--case','expected-source-mismatch','--execute','--json')
    assert status==1 and report['findings']==[{'code':'private-verifier-rejection-not-contained'}],report
with patch.object(module.VERIFIER,'wait_for_verifier_stop',side_effect=ValueError('private-native-canary')):
    status, report=invoke('--case','expected-source-mismatch','--execute','--json')
    assert status==1 and report['verdict']=='uncertain' and report['facts']['fixture_task_arn']==fixture['taskArn'],report
    assert report['findings']==[{'code':'private-verifier-wait-observation-unavailable'}]
    assert 'private-native-canary' not in json.dumps(report)

# A launched task is retained even when definition proof fails; do not wait or stop it.
with patch.object(module,'run_fault',return_value=(observed,'private-verifier-fault-task-definition-mismatch')),patch.object(module.VERIFIER,'wait_for_verifier_stop',side_effect=AssertionError('must not wait')),patch.object(module,'aws',side_effect=AssertionError('must not clean up')):
    status, report = invoke('--case','controller-deadline','--execute','--json')
    assert status==1 and report['verdict']=='uncertain'
    assert report['facts']['fixture_task_arn']==observed['taskArn']
    assert report['facts']['fixture_task_suffix']=='c'*12
    assert report['findings']==[{'code':'private-verifier-fault-task-definition-mismatch'}]
# Projection rejection is not a new task-admission or controller predicate.
for identity in ['private-identity-canary',observed['taskArn'].replace('337159794548','123456789012'),observed['taskArn'].replace('eu-west-1','eu-west-2'),observed['taskArn'].replace('/kanbien-core-platform/','/foreign/'),observed['taskArn'][:-1],observed['taskArn'].upper(),observed['taskArn']+'\nprivate-identity-canary']:
    unproven={**observed,'taskArn':identity}
    with patch.object(module,'aws',return_value=(True,{'tasks':[unproven]},'ok')) as call:
        assert actual_run_fault('controller-deadline','expected-definition','subnets','group')==(unproven,'private-verifier-fault-task-definition-mismatch')
        assert call.call_count==1
    with patch.object(module,'run_fault',return_value=(unproven,'private-verifier-fault-task-definition-mismatch')),patch.object(module.VERIFIER,'wait_for_verifier_stop',side_effect=AssertionError('must not wait')),patch.object(module,'aws',side_effect=AssertionError('must not clean up')):
        status, report=invoke('--case','controller-deadline','--execute','--json')
        assert status==1 and report['verdict']=='uncertain'
        assert 'fixture_task_arn' not in report['facts']
        assert report['facts']['fixture_task_identity']=='unavailable'
        assert report['facts']['fixture_task_suffix']=='identity-unavailable'
        assert identity not in json.dumps(report) and 'private-identity-canary' not in json.dumps(report)
    # A matching-definition path still passes the original ARN to the waiter.
    with patch.object(module,'run_fault',return_value=({**unproven,'taskDefinitionArn':'verifier:11'},'ok')),patch.object(module.VERIFIER,'wait_for_verifier_stop',return_value=('stopped',{**unproven,'containers':[{'exitCode':1}]})) as wait,patch.object(module,'aws',side_effect=AssertionError('must not clean up')):
        status, report=invoke('--case','expected-source-mismatch','--execute','--json')
        assert status==0 and report['verdict']=='rejected-as-expected'
        assert wait.call_count==1 and wait.call_args.args[0]==identity
        assert identity not in json.dumps(report) and report['facts']['fixture_task_suffix']=='identity-unavailable'
with patch.object(module,'run_fault',return_value=(None,'private-verifier-fault-task-observation-unconfirmed')),patch.object(module.VERIFIER,'wait_for_verifier_stop',side_effect=AssertionError('must not wait')),patch.object(module,'aws',side_effect=AssertionError('must not replay')):
    status, report = invoke('--case','controller-deadline','--execute','--json')
    assert status==1 and report['verdict']=='uncertain'
    assert report['findings']==[{'code':'private-verifier-fault-task-observation-unconfirmed'}]

for invalid_exit_code in (None, "1", True, False, 0):
    calls.clear()
    module.VERIFIER.wait_for_verifier_stop = lambda *_args, value=invalid_exit_code: ("stopped", {**fixture, "containers": [{"exitCode": value}]})
    status, report = invoke("--case", "expected-source-mismatch", "--execute", "--json")
    assert status == 1 and report["verdict"] == "blocked", (invalid_exit_code, report)
    assert report["findings"] == [{"code": "private-verifier-rejection-not-contained"}], (invalid_exit_code, report)

module.VERIFIER.wait_for_verifier_stop = lambda *_args: ("stopped", {**fixture, "containers": [{"exitCode": 1}]})

calls.clear()
module.VERIFIER.wait_for_verifier_stop = lambda *_args: ("still-running", fixture)
module.aws = lambda *args: (True, {}, "ok") if args[:2] == ("ecs", "stop-task") else (_ for _ in ()).throw(AssertionError(args))
module.wait_for_cleanup_stop = lambda task_arn: ({**fixture, "taskArn": task_arn, "lastStatus": "STOPPED"}, "ok")
status, report = invoke("--case", "controller-deadline", "--execute", "--json")
assert status == 0 and report["verdict"] == "controller-deadline-confirmed", report
assert calls == [("controller-deadline", "verifier:11", "subnet-a,subnet-b", "sg-a")], calls
class CleanupFailure:
    def __enter__(self):return '/tmp/fixture-only'
    def __exit__(self,*args):raise OSError('private-cleanup-canary')
with patch.object(module.tempfile,'TemporaryDirectory',return_value=CleanupFailure()):
    output=io.StringIO()
    with contextlib.redirect_stdout(output),patch.object(sys,'argv',['fixture','--case','controller-deadline','--execute']):status=module.main()
    reports=[json.loads(line) for line in output.getvalue().splitlines()]
assert status==1 and [item['verdict'] for item in reports]==['controller-deadline-confirmed','uncertain'],reports
assert reports[-1]['findings']==[{'code':'private-verifier-temporary-cleanup-unavailable'}] and 'private-cleanup-canary' not in output.getvalue()
with patch.object(module.tempfile,'TemporaryDirectory',side_effect=OSError('private-native-canary')),patch.object(module,'run_fault',side_effect=AssertionError('no submission')):
    status,report=invoke('--case','controller-deadline','--execute')
assert status==1 and report['verdict']=='blocked' and report['findings']==[{'code':'private-verifier-temporary-directory-unavailable'}]
PY
