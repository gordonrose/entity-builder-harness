#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.reconcile-platform-shell-staging.smoke-test
#   version: 5
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Verify local fail-closed reconciliation source validation without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: package.script.platform-shell-deployment-reconciliation-check
#     path: package.json
#   effects:
#   - read-only

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if grep -Eq -- 'ThreadPoolExecutor|concurrent\.futures' scripts/04.deploy/reconcile-platform-shell-staging/script.py; then
  echo "ERROR: reconciliation AWS calls must remain serial." >&2
  exit 1
fi
if ! grep -Eq -- 'role-policy-alignment requires the declared administrator target-profile credentials' scripts/04.deploy/reconcile-platform-shell-staging/script.py; then
  echo "ERROR: reconciliation role-policy alignment must remain administrator-only." >&2
  exit 1
fi
if ! grep -Eq -- 'a controlled Service preflight requires declared administrator target-profile credentials' scripts/04.deploy/reconcile-platform-shell-staging/script.py; then
  echo "ERROR: controlled Service preflight must remain target-admin only." >&2
  exit 1
fi
if ! grep -Eq -- 'pre-relational-stage6-bootstrap-recovery-service-change-set' scripts/04.deploy/reconcile-platform-shell-staging/script.py; then
  echo "ERROR: bootstrap recovery must retain its distinct Service change-set guard." >&2
  exit 1
fi
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/reconcile-platform-shell-staging/script.py").read_text(encoding="utf-8"), "reconcile-platform-shell-staging.py", "exec")'
python3 - <<'PY'
import runpy
import subprocess
import json
import tempfile
from types import SimpleNamespace
from pathlib import Path

module = runpy.run_path(Path("scripts/04.deploy/reconcile-platform-shell-staging/script.py"))

assert module["normalized_replacement"]("True") is True
assert module["normalized_replacement"]("False") is False
assert module["normalized_replacement"](None) is None
assert module["normalized_replacement"]("unexpected") == "unexpected"

bootstrap_recovery_changes = {
    ("Modify", "TaskDefinition", "AWS::ECS::TaskDefinition", True),
    ("Modify", "WorkerTaskDefinition", "AWS::ECS::TaskDefinition", True),
    ("Modify", "RelayTaskDefinition", "AWS::ECS::TaskDefinition", True),
    ("Modify", "RelationalBootstrapTaskDefinition", "AWS::ECS::TaskDefinition", True),
    ("Modify", "RelationalMigrationTaskDefinition", "AWS::ECS::TaskDefinition", True),
    ("Modify", "RelationalRelayTaskDefinition", "AWS::ECS::TaskDefinition", True),
    ("Modify", "RelationalWorkerTaskDefinition", "AWS::ECS::TaskDefinition", True),
    ("Modify", "RelationalRestoreVerificationTaskDefinition", "AWS::ECS::TaskDefinition", True),
    ("Modify", "Service", "AWS::ECS::Service", False),
    ("Modify", "WorkerService", "AWS::ECS::Service", False),
}
assert len(bootstrap_recovery_changes) == 10

profile = module["load_yaml"](Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"))
policy = module["resolve_policy"](profile)
assert policy["expected_candidate_execution_preflight_onboarding_changes"] == {
    ("Add", "CandidatePreflightTaskDefinition", "AWS::ECS::TaskDefinition", None),
}
assert policy["expected_candidate_execution_preflight_image_changes"] == {
    ("Modify", "CandidatePreflightTaskDefinition", "AWS::ECS::TaskDefinition", True),
}

# Promotion of the corrected image is unavailable until the independently
# reconciled no-write database-effect receipt is durable and successful.
receipt_path = Path(tempfile.mkdtemp()) / "stage-attempts.json"
receipt_path.write_text(json.dumps({"schema": "postgresql-stage6-attempt-ledger/v1", "stages": {}}), encoding="utf-8")
try:
    module["check_bootstrap_effects_reconciliation_receipt"](receipt_path)
except module["ReconciliationError"] as exception:
    assert str(exception) == "bootstrap-effect-reconciliation-receipt-missing"
else:
    raise AssertionError("promotion accepted a missing bootstrap-effect reconciliation receipt")
receipt_path.write_text(json.dumps({"schema": "postgresql-stage6-attempt-ledger/v1", "stages": {"bootstrap_effects_reconciliation": {"label": "kb-pg6-bootstrap-effects-r5-a1", "state": "succeeded"}}}), encoding="utf-8")
module["check_bootstrap_effects_reconciliation_receipt"](receipt_path)

try:
    module["run_check"](
        "artifact-bucket-public-access-control",
        lambda: (_ for _ in ()).throw(module["ReconciliationError"]("aws-verification-unavailable")),
    )
except module["ReconciliationError"] as exception:
    assert str(exception) == "artifact-bucket-public-access-control-verification-unavailable"
else:
    raise AssertionError("unavailable provider result was not attributed to its owning control")

attempts = 0
original_run = module["subprocess"].run
original_sleep = module["time"].sleep

def transient_then_success(*_arguments, **_keywords):
    global attempts
    attempts += 1
    if attempts < 3:
        raise subprocess.CalledProcessError(1, "aws")
    return SimpleNamespace(stdout='"retry-success"')

module["subprocess"].run = transient_then_success
module["time"].sleep = lambda _seconds: None
try:
    result = module["run_aws"](
        SimpleNamespace(aws_cli="aws", aws_credential_source="environment", timeout_seconds=1),
        {"region": "eu-west-1"},
        ["sts", "get-caller-identity"],
    )
finally:
    module["subprocess"].run = original_run
    module["time"].sleep = original_sleep
assert result == "retry-success"
assert attempts == 3

attempts = 0

def always_fail(*_arguments, **_keywords):
    global attempts
    attempts += 1
    raise subprocess.CalledProcessError(1, "aws")

module["subprocess"].run = always_fail
module["time"].sleep = lambda _seconds: None
try:
    module["run_aws"](
        SimpleNamespace(aws_cli="aws", aws_credential_source="environment", timeout_seconds=1),
        {"region": "eu-west-1"},
        ["cloudformation", "describe-stacks"],
        "artifact-stack-drift-summary-unavailable",
    )
except module["ReconciliationError"] as exception:
    assert str(exception) == "artifact-stack-drift-summary-unavailable"
else:
    raise AssertionError("provider unavailability did not preserve the supplied safe failure code")
finally:
    module["subprocess"].run = original_run
    module["time"].sleep = original_sleep
assert attempts == 3

def stale_summary(*_arguments, **_keywords):
    return SimpleNamespace(stdout='{"status":"IN_SYNC","checked":"2020-01-01T00:00:00Z"}')

module["subprocess"].run = stale_summary
try:
    module["check_stack_drift_evidence"](
        SimpleNamespace(aws_cli="aws", aws_credential_source="environment", timeout_seconds=1),
        {"region": "eu-west-1", "maximum_drift_evidence_age_seconds": 21600},
        "kanbien-staging-platform-shell-foundation",
        "foundation-stack-drift",
    )
except module["ReconciliationError"] as exception:
    assert str(exception) == "foundation-stack-drift-evidence-stale"
else:
    raise AssertionError("stale passive drift evidence was accepted")
finally:
    module["subprocess"].run = original_run

policy_source = "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json"
desired_policy = json.loads(Path(policy_source).read_text(encoding="utf-8"))

def matching_live_policy(*_arguments, **_keywords):
    return SimpleNamespace(stdout=json.dumps(desired_policy))

module["subprocess"].run = matching_live_policy
try:
    module["check_reconciliation_live_role_policy"](
        SimpleNamespace(aws_cli="aws", aws_credential_source="environment", timeout_seconds=1),
        {
            "region": "eu-west-1",
            "reconciliation_policy_source": policy_source,
            "reconciliation_role_name": "github-platform-shell-staging-reconciliation",
            "reconciliation_inline_policy_name": "ReadDeclaredStagingControls",
        },
    )
finally:
    module["subprocess"].run = original_run
PY
result="$(bash scripts/04.deploy/reconcile-platform-shell-staging/script.sh --validate --json)"
if [[ "$result" != *'"verdict": "passed"'* || "$result" != *'"id": "source-policy"'* ]]; then
  echo "ERROR: reconciliation source validation did not emit the expected safe result" >&2
  exit 1
fi
echo "Platform-shell deployment reconciliation local check passed."
