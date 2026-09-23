#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-synthetic-scheduler
#   version: 4
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Statically verify the temporary Kanbien staging protected-route synthetic workflow and its separate least-privilege IAM source.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-synthetic-scheduler-check
#     path: package.json
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

try:
    import yaml
except ImportError as error:
    raise SystemExit("ERROR: PyYAML is required. Install PyYAML==6.0.2 before this check.") from error


TARGET_PROFILE_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
READINESS_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml")
WORKFLOW_PATH = Path(".github/workflows/platform-shell-staging-synthetic.yml")
POLICY_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-synthetic-policy.json")
TRUST_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-synthetic-trust.json")


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"ERROR: required YAML source is missing: {path}")
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(document, dict):
        raise SystemExit(f"ERROR: required YAML source must be a mapping: {path}")
    return document


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"ERROR: required JSON source is missing: {path}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"ERROR: required JSON source is invalid: {path}") from error
    if not isinstance(document, dict):
        raise SystemExit(f"ERROR: required JSON source must be a mapping: {path}")
    return document


def mapping(value: object, name: str) -> dict:
    if not isinstance(value, dict):
        failures.append(f"{name} must be a mapping")
        return {}
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def nested(document: dict, *keys: str) -> object:
    value: object = document
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def named_step(steps: list, name: str) -> dict:
    matches = [step for step in steps if isinstance(step, dict) and step.get("name") == name]
    if len(matches) != 1:
        failures.append(f"workflow must contain exactly one step named: {name}")
        return {}
    return matches[0]


target_profile = load_yaml(TARGET_PROFILE_PATH)
readiness = load_yaml(READINESS_PATH)
workflow = load_yaml(WORKFLOW_PATH)
policy = load_json(POLICY_PATH)
trust = load_json(TRUST_PATH)
failures: list[str] = []

expected_execution_policy = {
    "mutation_style": "github-actions-oidc-read-only-protected-smoke",
    "workflow": ".github/workflows/platform-shell-staging-synthetic.yml",
    "trigger": "schedule-and-manual-dispatch",
    "schedule_cron_utc": "17 */4 * * *",
    "delivery_assurance": "best-effort-nominal-four-hour-cadence-not-slo-coverage-proof",
    "deployable_ref": "refs/heads/main",
    "github_environment": "none",
    "role_name": "github-platform-shell-staging-synthetic",
    "role_arn": "arn:aws:iam::337159794548:role/github-platform-shell-staging-synthetic",
    "inline_policy_name": "ReadOnlyControlledSmokeSecret",
    "tags": {
        "service": "platform-shell",
        "environment": "staging",
        "managed-by": "github-actions",
        "purpose": "protected-synthetic",
    },
    "role_policy_source": str(POLICY_PATH),
    "trust_policy_source": str(TRUST_PATH),
    "role_policy_deployment_status": "deployed-and-live-inspected",
    "live_policy_proof": {
        "inspection": ["aws-iam-get-role", "aws-iam-get-role-policy"],
        "verified_at_utc": "2026-09-22T09:31:57Z",
        "allowed_mutation_scope": "two-declared-secret-reads-and-two-fixed-public-smoke-requests-with-75-second-counter-advance-interval",
    },
    "allowed_aws_action": "secretsmanager:GetSecretValue",
    "allowed_secret_arn": "arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-machine-client-ibNhn5",
    "command": "npm run platform:shell:controlled-smoke -- --aws-credential-source environment",
    "metric_coverage_sequence": {
        "request_count": "2",
        "inter_request_wait_seconds": "75",
        "purpose": "establish-and-advance-the-cumulative-counter-after-a-fresh-task-start",
        "output_policy": "per-request-status-and-safe-latency-only-no-token-secret-or-response-body",
    },
    "replacement": "replace-with-governed-platform-scheduler-contract-and-adapter",
    "activation_status": "active-manual-first-run-proven-scheduled-trigger-pending",
    "activation_prerequisites": [
        "record-first-scheduled-trigger-result",
    ],
    "first_live_proof": {
        "source_commit_sha": "9ccad368a34684afaa9b7ed64d7dba85f4b3fae8",
        "github_run_id": "35711517748",
        "github_run_url": "https://github.com/gordonrose/entity-builder-harness/actions/runs/35711517748",
        "completed_at_utc": "2026-09-22T09:38:37Z",
        "result": "passed",
        "http_status": "200",
        "duration_ms": "266",
        "output_policy": "status-and-safe-latency-only-no-token-secret-or-response-body",
    },
}
target_execution_policy = nested(target_profile, "deployment", "execution_policy", "temporary_synthetic_scheduler")
require(target_execution_policy == expected_execution_policy, "target profile must retain the exact reviewed temporary synthetic scheduler policy")
readiness_execution_policy = nested(readiness, "deployment", "execution_policy", "temporary_synthetic_scheduler")
require(readiness_execution_policy == expected_execution_policy, "readiness manifest must mirror the exact temporary synthetic scheduler policy")

synthetic_checks = nested(target_profile, "observability", "synthetic_checks")
expected_synthetic_check = {
    "id": "platform-smoke-protected-read",
    "status": "active-manual-first-run-proven-scheduled-trigger-pending",
    "command": "npm run platform:shell:controlled-smoke",
    "cadence_target": "nominal-every-4-hours-best-effort",
    "identity": "dedicated-least-privilege-machine-client",
    "request": {
        "method": "GET",
        "route_pattern": "/smoke/<safe-synthetic-id>",
        "expected_http_status": "200",
    },
    "output_policy": "status-and-safe-latency-only-no-token-secret-or-response-body",
    "metric_coverage_sequence": {
        "request_count": "2",
        "inter_request_wait_seconds": "75",
        "purpose": "establish-and-advance-the-cumulative-counter-after-a-fresh-task-start",
    },
    "evidence_interpretation": "synthetic-boundary-evidence-not-unqualified-customer-traffic",
    "scheduler": "github-actions-temporary-active-manual-first-run-proven-scheduled-trigger-pending",
    "scheduler_execution_policy": "deployment.execution_policy.temporary_synthetic_scheduler",
}
require(synthetic_checks == [expected_synthetic_check], "target profile must retain the single bounded, explicitly non-SLO synthetic check")

expected_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadOnlyControlledSmokeSecret",
            "Effect": "Allow",
            "Action": ["secretsmanager:GetSecretValue"],
            "Resource": [expected_execution_policy["allowed_secret_arn"]],
        }
    ],
}
require(policy == expected_policy, "synthetic GitHub role policy must allow only the one declared secret read")

expected_trust = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::337159794548:oidc-provider/token.actions.githubusercontent.com",
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    "token.actions.githubusercontent.com:repository": "gordonrose/entity-builder-harness",
                    "token.actions.githubusercontent.com:ref": "refs/heads/main",
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:gordonrose/entity-builder-harness:ref:refs/heads/main",
                },
            },
        }
    ],
}
require(trust == expected_trust, "synthetic GitHub trust policy must allow only main-branch repository OIDC tokens")

triggers = mapping(workflow.get("on"), "workflow triggers")
require(triggers.get("schedule") == [{"cron": "17 */4 * * *"}], "workflow must use only the reviewed nominal four-hour UTC schedule")
require(triggers.get("workflow_dispatch") == {}, "workflow must permit manual dispatch without free-form inputs")
require(workflow.get("permissions") == {"contents": "read", "id-token": "write"}, "workflow must use only read-only repository and OIDC permissions")
require(workflow.get("concurrency") == {"group": "platform-shell-staging-synthetic", "cancel-in-progress": "false"}, "workflow must retain the non-overlapping synthetic concurrency policy")
require(workflow.get("env") == {
    "AWS_REGION": "eu-west-1",
    "AWS_ROLE_ARN": expected_execution_policy["role_arn"],
}, "workflow must use the declared target region and separate synthetic role")

jobs = mapping(workflow.get("jobs"), "workflow jobs")
require(set(jobs) == {"run-synthetic"}, "workflow must contain only the bounded synthetic job")
job = mapping(jobs.get("run-synthetic"), "run-synthetic job")
require(job.get("if") == "${{ github.ref == 'refs/heads/main' }}", "synthetic job must fail closed outside main")
require(job.get("runs-on") == "ubuntu-latest", "synthetic job must use the reviewed GitHub-hosted runner")
require(job.get("timeout-minutes") == "5", "synthetic job must have the reviewed five-minute execution bound")
require("environment" not in job, "synthetic job must not reuse the manually approved deployment environment")
steps = job.get("steps")
if not isinstance(steps, list):
    failures.append("synthetic job must declare ordered steps")
    steps = []

checkout = named_step(steps, "Check out repository")
require(checkout.get("uses") == "actions/checkout@v4", "synthetic workflow must use the reviewed checkout action")
require(checkout.get("with") == {"persist-credentials": "false"}, "synthetic checkout must not persist repository credentials")
main_guard = named_step(steps, "Enforce remote-main source")
require("GITHUB_REF" in str(main_guard.get("run")) and "refs/heads/main" in str(main_guard.get("run")), "synthetic workflow must retain its shell-level main-source guard")
node = named_step(steps, "Set up Node")
require(node.get("uses") == "actions/setup-node@v4" and node.get("with") == {"node-version": "22"}, "synthetic workflow must use the reviewed Node 22 runtime")
python = named_step(steps, "Set up Python")
require(python.get("uses") == "actions/setup-python@v5" and python.get("with") == {"python-version": "3.11"}, "synthetic workflow must use the reviewed Python runtime")
install = named_step(steps, "Install script dependencies")
require(install.get("run") == "python -m pip install --disable-pip-version-check PyYAML==6.0.2", "synthetic workflow must install only its fixed parser dependency")
validate = named_step(steps, "Validate fixed synthetic policy locally")
require(validate.get("run") == "npm run platform:shell:controlled-smoke -- --validate", "synthetic workflow must validate its bounded smoke policy before credential acquisition")
credentials = named_step(steps, "Configure read-only AWS credentials")
require(credentials.get("uses") == "aws-actions/configure-aws-credentials@v4", "synthetic workflow must use the reviewed AWS OIDC credential action")
require(credentials.get("with") == {"role-to-assume": "${{ env.AWS_ROLE_ARN }}", "aws-region": "${{ env.AWS_REGION }}"}, "synthetic workflow must assume only its declared role and region")
run = named_step(steps, "Run protected staging synthetic")
require(run.get("run") == expected_execution_policy["command"], "synthetic workflow must run only the exact bounded OIDC credential-source command")
wait = named_step(steps, "Wait for first cumulative counter export")
require(wait.get("run") == "sleep 75", "synthetic workflow must retain the reviewed counter-baseline export wait")
advance = named_step(steps, "Run protected staging synthetic counter advance")
require(advance.get("run") == expected_execution_policy["command"], "synthetic workflow must use the same exact bounded command for the counter-advancing request")

step_names = [step.get("name") for step in steps if isinstance(step, dict)]
required_order = [
    "Validate fixed synthetic policy locally",
    "Configure read-only AWS credentials",
    "Run protected staging synthetic",
    "Wait for first cumulative counter export",
    "Run protected staging synthetic counter advance",
]
require(all(name in step_names for name in required_order) and [step_names.index(name) for name in required_order] == sorted(step_names.index(name) for name in required_order), "synthetic policy validation, OIDC configuration, baseline request, bounded export wait, and counter-advancing request must occur in that order")

workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
for forbidden_text in (
    "aws iam ",
    "aws cloudformation ",
    "aws ecs ",
    "aws secretsmanager put",
    "aws secretsmanager update",
    "aws secretsmanager delete",
    "secrets.",
):
    require(forbidden_text not in workflow_text, f"synthetic workflow must not contain broad mutation or GitHub-secret use: {forbidden_text.strip()}")

if failures:
    print("Platform-shell synthetic scheduler policy check failed:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    raise SystemExit(1)

print("Platform-shell synthetic scheduler policy check passed.")
PY
