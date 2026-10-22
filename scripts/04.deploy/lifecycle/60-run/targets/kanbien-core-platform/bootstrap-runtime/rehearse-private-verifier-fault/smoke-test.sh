#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.rehearse-private-verifier-fault
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
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

assert module.fault_override("expected-source-mismatch") == {
    "containerOverrides": [{"name": "private-release-verifier", "environment": [{"name": "KANBIEN_EXPECTED_SOURCE_REVISION", "value": "0" * 40}]}]
}
assert module.fault_override("controller-deadline") == {
    "containerOverrides": [{"name": "private-release-verifier", "command": ["-e", "setTimeout(() => process.exit(0), 121000)"]}]
}

release = {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64, "runtime_task_definition": "runtime:10"}
accepted = {"taskArn": "arn:aws:ecs:eu-west-1:123456789012:task/cluster/accepted-task"}
fixture = {"taskArn": "arn:aws:ecs:eu-west-1:123456789012:task/cluster/fixture-task", "taskDefinitionArn": "verifier:11"}
module.REPLACEMENT.accepted_release = lambda: release
module.REPLACEMENT.receipt = lambda _release, _path: None
module.REPLACEMENT.preflight = lambda _release, _path: (accepted, "ok")
module.REPLACEMENT.task_suffix = lambda task: task["taskArn"].rsplit("/", 1)[-1]
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
PY
