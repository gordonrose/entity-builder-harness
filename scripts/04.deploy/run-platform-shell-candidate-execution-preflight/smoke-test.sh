#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.run-platform-shell-candidate-execution-preflight.smoke-test
#   version: 2
#   status: active
#   created_on: "2026-09-27"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Verify the candidate preflight's source-only and safety boundaries without AWS calls.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   - writes-files
#   used_by:
#   - id: package.script.platform-shell-candidate-execution-preflight-check
#     path: package.json
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py").read_text(encoding="utf-8"), "candidate-execution-preflight.py", "exec")'
if [[ "$(bash scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.sh --validate)" != *'"candidate_execution_preflight": "validated"'* ]]; then
  echo "ERROR: candidate preflight validation must emit only the reviewed safe verdict" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.sh --execute >/dev/null 2>&1; then
  echo "ERROR: candidate execution must require its explicit approval guard" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.sh --validate --approve-candidate-execution-preflight >/dev/null 2>&1; then
  echo "ERROR: candidate execution approval must be unavailable in validation mode" >&2
  exit 1
fi
if grep -Eq -- 'parser\.add_argument\("--(target|image|network|task-definition|started-by|timeout|label|profile)' scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py; then
  echo "ERROR: candidate preflight must not accept caller-selected execution inputs" >&2
  exit 1
fi
if ! grep -Eq -- 'stop_and_wait\(accepted_task, policy\)' scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py; then
  echo "ERROR: an accepted candidate task must be cleaned up on every terminal path" >&2
  exit 1
fi
if ! grep -Eq -- 'signal\.signal\(signal\.SIGTERM, interrupted\)' scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py || ! grep -Eq -- 'cleanup_active_candidate\(\)' scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py; then
  echo "ERROR: an interrupted candidate preflight must attempt controlled cleanup" >&2
  exit 1
fi
python3 - <<'PY'
import runpy
from pathlib import Path
import tempfile

module = runpy.run_path(Path("scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py"))
assert "/tmp/" not in str(module["DEFAULT_CANDIDATE_LEDGER_PATH"])
assert module["DEFAULT_CANDIDATE_LEDGER_PATH"].parent.name == "postgresql-stage6-receipts"
image_a = "example.invalid/repository@sha256:" + "a" * 64
image_b = "example.invalid/repository@sha256:" + "b" * 64
base = {
    "cpu": "512",
    "memory": "1024",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "runtimePlatform": {"cpuArchitecture": "X86_64", "operatingSystemFamily": "LINUX"},
    "executionRoleArn": "reviewed-execution-role",
    "taskRoleArn": "reviewed-task-role",
    "containerDefinitions": [
        {"name": "platform-shell", "image": image_a, "essential": True, "healthCheck": {"command": ["CMD", "node"]}},
        {"name": "otel-collector", "image": "collector@sha256:" + "c" * 64, "essential": True},
    ],
}
candidate = {**base, "family": "kanbien-staging-platform-shell-candidate-preflight"}
server = {**base, "family": "kanbien-staging-platform-shell", "containerDefinitions": [dict(base["containerDefinitions"][0], image=image_b), base["containerDefinitions"][1]]}
policy = {"candidate_task_family": "kanbien-staging-platform-shell-candidate-preflight", "application_container": "platform-shell"}
assert module["verify_candidate_shape"](candidate, server, policy) == image_a
drifted = dict(candidate, cpu="1024")
try:
    module["verify_candidate_shape"](drifted, server, policy)
except module["CandidatePreflightError"] as error:
    assert str(error) == "candidate-task-shape-drift"
else:
    raise AssertionError("candidate task shape drift was accepted")
assert module["attempt_label"](image_a) == module["attempt_label"](image_a)
assert module["attempt_label"](image_a) != module["attempt_label"](image_b)
assert len(module["attempt_label"](image_a)) <= 36
ledger = Path(tempfile.mkdtemp()) / "candidate-receipts.json"
assert module["reserve_candidate_attempt"](image_a, ledger).endswith("-a1")
module["record_candidate_state"](module["attempt_label"](image_a, 1), "failed", ledger)
assert module["reserve_candidate_attempt"](image_a, ledger).endswith("-a2")
assert len(module["load_candidate_ledger"](ledger)["attempts"]) == 2
assert module["terminal_category"]({"containers": [{"reason": "CannotPullContainerError"}]}) == "candidate-image-distribution-failure"
assert module["terminal_category"]({"containers": [{"reason": "ResourceInitializationError"}]}) == "candidate-runtime-initialization-failure"
assert module["terminal_category"]({"stopCode": "TaskFailedToStart", "containers": []}) == "candidate-task-startup-failure"
assert module["candidate_admission_category"]("AccessDeniedException: iam:PassRole") == "candidate-run-task-authorization-failure"
assert module["candidate_admission_category"]("RESOURCE:ENI") == "candidate-run-task-network-configuration-failure"
assert module["candidate_admission_category"]("RESOURCE:CPU") == "candidate-run-task-capacity-or-placement-failure"
assert module["candidate_admission_category"]("unsupported FARGATE launch type") == "candidate-run-task-definition-or-launch-contract-failure"
assert module["candidate_admission_category"]("unknown provider condition") == "candidate-run-task-provider-rejection-unclassified"
calls = []
def no_tasks(label, state, _policy):
    calls.append((label, state))
    return []
module["assert_fresh_attempt"].__globals__["labelled_tasks"] = no_tasks
module["assert_fresh_attempt"]("derived-label", {})
assert calls == [("derived-label", "RUNNING"), ("derived-label", "STOPPED")]
PY
echo "Candidate execution preflight local validation passed."
python3 -B - <<'PY'
import copy, importlib.util, json, os, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
import yaml
root=Path.cwd()
def load(path):
 spec=importlib.util.spec_from_file_location(path.stem,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
compiler=load(root/'scripts/04.deploy/operational-realization-gate/script.py')
controller=load(root/'scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py')
contract=compiler.load_yaml(root/'infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/candidate-execution-preflight.v1.yml','contract-unreadable')
identifier=compiler.validate_contract(contract);_,known=compiler.ids(contract)
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z");digest='sha256:'+'a'*64
facts={'schema':compiler.FACTS_SCHEMA,'contract_id':identifier,'gate_evidence':[{'gate':gate['id'],'check_id':gate['evidence'][0],'timestamp':now,'verdict':'passed'} for gate in contract['gates'][:6]],'component_evidence':[{'component_id':key,'component_kind':kind,'check_id':key+'-check','timestamp':now,'verdict':'passed'} for key,kind in known.items()],'artifact_bindings':[{'component_id':'candidate-runtime-artifact','immutable_reference':digest,'check_id':'candidate-artifact-check','timestamp':now,'verdict':'passed'}]}
bindings=compiler.evidence_bindings(contract,facts)
for entry in facts['gate_evidence']:entry['input_sha256']=bindings['gates'][entry['gate']]
for entry in facts['component_evidence']:entry['input_sha256']=bindings['components'][entry['component_id']]
summary={'schema':compiler.CHANGE_SCHEMA,'contract_id':identifier,'check_id':'candidate-change-shape-check','timestamp':now,'input_sha256':bindings['gates']['change-set'],'operation_counts':{'create':1,'update':0,'delete':0,'replace':0,'broaden-permission':0}}
with tempfile.TemporaryDirectory(prefix='candidate-realization-') as directory:
 temp=Path(directory);fact_path=temp/'facts.yml';summary_path=temp/'summary.yml'
 fact_path.write_text(yaml.safe_dump(facts));summary_path.write_text(yaml.safe_dump(summary))
 assert controller.realization_preflight(fact_path,summary_path)==digest
 # Actual CLI reaches no AWS executable when binding/freshness proof is absent.
 aws=temp/'aws';marker=temp/'provider-called';aws.write_text('#!/bin/sh\ntouch "'+str(marker)+'"\nexit 1\n');aws.chmod(0o755)
 command=[sys.executable,'-B',str(root/'scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py'),'--execute','--approve-candidate-execution-preflight','--realization-facts',str(fact_path),'--realization-change-summary',str(summary_path)]
 invalid=copy.deepcopy(facts);invalid['gate_evidence'][0]['input_sha256']='sha256:'+'f'*64;fact_path.write_text(yaml.safe_dump(invalid))
 result=subprocess.run(command,cwd=root,capture_output=True,text=True,env={**os.environ,'PATH':str(temp)+os.pathsep+os.environ['PATH']},timeout=15)
 assert result.returncode==1 and 'candidate-realization-gate-evidence-input-mismatch' in result.stdout,(result.stdout,result.stderr)
 assert not marker.exists()
 # Cleanup failures must not erase the original cause.
 state=controller.execute.__globals__
 state['verify_account']=lambda policy:None
 state['candidate_task_definition']=lambda policy:'candidate'
 state['active_server']=lambda policy:('server',{})
 state['task_definition']=lambda *args:{}
 state['verify_candidate_shape']=lambda *args:'fixture.invalid/image@'+digest
 state['load_candidate_ledger']=lambda:{'attempts':[]}
 state['assert_fresh_attempt']=lambda *args:None
 state['reserve_candidate_attempt']=lambda image,**kwargs:'candidate-label'
 state['run_candidate']=lambda *args:'task-safe'
 state['record_candidate_state']=lambda *args:None
 def fail_health(*args):raise controller.CandidatePreflightError('candidate-health-failed')
 def fail_cleanup():raise controller.CandidatePreflightError('cleanup-unavailable')
 state['wait_for_healthy']=fail_health;state['cleanup_active_candidate']=fail_cleanup
 import contextlib,io
 output=io.StringIO()
 with contextlib.redirect_stdout(output):assert controller.execute({'qualified_artifact_digest':digest})==1
 report=json.loads(output.getvalue());assert report['failure_category']=='candidate-health-failed' and report['secondary_failure_category']=='candidate-cleanup-failure'
print('Candidate realization prerequisites, artifact identity and original failure retention passed (synthetic only).')
PY

python3 -B "$ROOT/scripts/04.deploy/run-platform-shell-candidate-execution-preflight/continuation-test.py"
