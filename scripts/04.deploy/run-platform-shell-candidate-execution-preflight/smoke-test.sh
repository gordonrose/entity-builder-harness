#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-candidate-execution-preflight.smoke-test
#   version: 2
#   status: active
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
