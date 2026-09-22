#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-metric-coverage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Statically verify the Kanbien staging metric-coverage workflow, policy, and least-privilege IAM sources.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-metric-coverage-policy-check
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
WORKFLOW_PATH = Path(".github/workflows/platform-shell-staging-metric-coverage.yml")
POLICY_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/iam/github-platform-shell-staging-metric-coverage-policy.json")
TRUST_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/iam/github-platform-shell-staging-metric-coverage-trust.json")
COMMAND_PATH = Path("scripts/04.deploy/run-platform-shell-metric-coverage/script.py")
PACKAGE_PATH = Path("package.json")
failures: list[str] = []


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


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def mapping(value: object, name: str) -> dict:
    if not isinstance(value, dict):
        failures.append(f"{name} must be a mapping")
        return {}
    return value


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
package = load_json(PACKAGE_PATH)
coverage = mapping(nested(target_profile, "observability", "metric_coverage"), "target metric_coverage")
expected_coverage = {
    "status": "activated-and-live-verified-exporter-loss-proof-pending",
    "id": "platform-smoke-protected-read-metric-coverage",
    "command": "npm run platform:shell:metric-coverage",
    "scheduler": {
        "workflow": ".github/workflows/platform-shell-staging-metric-coverage.yml",
        "cadence_target": "nominal-every-4-hours-best-effort-after-protected-synthetic",
        "schedule_cron_utc": "35 */4 * * *",
        "execution_identity": "github-platform-shell-staging-metric-coverage",
        "role_arn": "arn:aws:iam::337159794548:role/github-platform-shell-staging-metric-coverage",
        "deployment_status": "deployed-and-live-inspected",
    },
    "expected_metric": {
        "instrument_name": "kanbien.platform.server.request.outcome",
        "required_labels": {
            "capability": "platform-smoke.smoke.read",
            "action": "read",
            "execution_context": "server",
            "http_method": "GET",
            "outcome": "succeeded",
        },
    },
    "query_window_seconds": "1200",
    "arrival_grace_seconds": "300",
    "rehearsal_isolation_wait_seconds": "1200",
    "verdicts": ["observed", "missing", "query-failed", "notification-failed"],
    "non_observed_slo_confidence": "insufficient-confidence",
    "output_policy": "safe-verdict-and-aggregate-only-no-query-body-token-or-response-payload",
    "alert": {
        "delivery": "sns-existing-target-owned-topic-only",
        "topic_arn": "arn:aws:sns:eu-west-1:337159794548:kanbien-staging-platform-shell-alarms",
        "subject": "Kanbien staging platform-shell metric coverage",
        "message_policy": "fixed-safe-verdict-only-no-metric-response-or-request-data",
    },
}
require(coverage == expected_coverage, "target profile must retain the exact reviewed metric-coverage contract")
require(nested(target_profile, "observability", "slo_query") == {
    "provider_documented_max_request_range_days": "7",
    "effective_max_increase_lookback_days": "1",
    "rolling_window_segment_count": "28",
    "implementation": "segmented-promql-one-day-increase-and-histogram-bucket-aggregation",
    "effective_limit_evidence": "live-read-only-query-proven-2026-09-22",
}, "target profile must retain the exact reviewed effective segmented SLO query policy")

expected_execution_policy = {
    "mutation_style": "github-actions-oidc-promql-coverage-and-fixed-sns-alert",
    "workflow": ".github/workflows/platform-shell-staging-metric-coverage.yml",
    "trigger": "schedule-and-manual-dispatch",
    "schedule_cron_utc": "35 */4 * * *",
    "delivery_assurance": "best-effort-nominal-four-hour-cadence-coverage-concern-not-customer-slo-proof",
    "deployable_ref": "refs/heads/main",
    "github_environment": "none",
    "role_name": "github-platform-shell-staging-metric-coverage",
    "role_arn": "arn:aws:iam::337159794548:role/github-platform-shell-staging-metric-coverage",
    "inline_policy_name": "ReadDeclaredPromqlAndPublishCoverageConcern",
    "tags": {"service": "platform-shell", "environment": "staging", "managed-by": "github-actions", "purpose": "metric-coverage"},
    "role_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-platform-shell-staging-metric-coverage-policy.json",
    "trust_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-platform-shell-staging-metric-coverage-trust.json",
    "role_policy_deployment_status": "deployed-and-live-inspected",
    "allowed_aws_actions": ["cloudwatch:GetMetricData", "cloudwatch:ListMetrics", "sns:Publish"],
    "allowed_alert_topic_arn": "arn:aws:sns:eu-west-1:337159794548:kanbien-staging-platform-shell-alarms",
    "command": "npm run platform:shell:metric-coverage -- --aws-credential-source environment --notify-on-non-observed",
    "replacement": "replace-with-governed-platform-scheduler-contract-and-adapter",
    "activation_status": "active-manual-observed-and-non-observed-verdicts-proven-scheduled-trigger-pending",
    "live_policy_proof": {
        "inspection": ["aws-iam-get-role", "aws-iam-get-role-policy"],
        "verified_at_utc": "2026-09-22",
        "allowed_mutation_scope": "declared-promql-read-and-one-fixed-sns-coverage-concern-only",
    },
    "first_live_verdicts": {
        "observed": {
            "source_commit_sha": "e33fbad5ccbb4c0845bb68651cd52c87d96197eb",
            "github_run_id": "35737959555",
            "result": "passed",
            "metric_coverage": "observed",
            "output_policy": "safe-verdict-and-aggregate-only-no-query-body-token-or-response-payload",
        },
        "non_observed": {
            "source_commit_sha": "e33fbad5ccbb4c0845bb68651cd52c87d96197eb",
            "github_run_id": "35737520603",
            "result": "expected-failure",
            "metric_coverage": "missing",
            "affected_slo_confidence": "insufficient-confidence",
            "alert_publish_path": "completed-without-operator-receipt-claim",
            "output_policy": "safe-verdict-and-aggregate-only-no-query-body-token-or-response-payload",
        },
    },
}
require(nested(readiness, "deployment", "execution_policy", "temporary_metric_coverage") == expected_execution_policy, "readiness manifest must retain the exact reviewed metric-coverage execution policy")

expected_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "ReadDeclaredCloudWatchPromql", "Effect": "Allow", "Action": ["cloudwatch:GetMetricData", "cloudwatch:ListMetrics"], "Resource": "*"},
        {"Sid": "PublishDeclaredCoverageConcern", "Effect": "Allow", "Action": ["sns:Publish"], "Resource": "arn:aws:sns:eu-west-1:337159794548:kanbien-staging-platform-shell-alarms"},
    ],
}
require(policy == expected_policy, "metric-coverage IAM policy may query only CloudWatch PromQL and publish only to the declared SNS topic")

expected_trust = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Federated": "arn:aws:iam::337159794548:oidc-provider/token.actions.githubusercontent.com"},
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
            "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com", "token.actions.githubusercontent.com:repository": "gordonrose/entity-builder-harness", "token.actions.githubusercontent.com:ref": "refs/heads/main"},
            "StringLike": {"token.actions.githubusercontent.com:sub": "repo:gordonrose/entity-builder-harness:ref:refs/heads/main"},
        },
    }],
}
require(trust == expected_trust, "metric-coverage GitHub trust policy must allow only main-branch repository OIDC tokens")

triggers = mapping(workflow.get("on"), "workflow triggers")
require(triggers.get("schedule") == [{"cron": "35 */4 * * *"}], "metric-coverage workflow must use only the reviewed post-synthetic UTC schedule")
require(triggers.get("workflow_dispatch") == {}, "metric-coverage workflow must permit manual dispatch without free-form inputs")
require(workflow.get("permissions") == {"contents": "read", "id-token": "write"}, "metric-coverage workflow must use only repository-read and OIDC permissions")
require(workflow.get("concurrency") == {"group": "platform-shell-staging-metric-coverage", "cancel-in-progress": "false"}, "metric-coverage workflow must retain its non-overlapping concurrency policy")
require(workflow.get("env") == {"AWS_REGION": "eu-west-1", "AWS_ROLE_ARN": "arn:aws:iam::337159794548:role/github-platform-shell-staging-metric-coverage"}, "metric-coverage workflow must use only the declared target region and separate role")
jobs = mapping(workflow.get("jobs"), "workflow jobs")
require(set(jobs) == {"verify-coverage"}, "metric-coverage workflow must contain only the bounded coverage job")
job = mapping(jobs.get("verify-coverage"), "verify-coverage job")
require(job.get("if") == "${{ github.ref == 'refs/heads/main' }}", "metric-coverage job must fail closed outside main")
require(job.get("runs-on") == "ubuntu-latest" and job.get("timeout-minutes") == "5", "metric-coverage job must use the reviewed runner and five-minute bound")
require("environment" not in job, "metric-coverage job must not reuse the deployment environment")
steps = job.get("steps")
if not isinstance(steps, list):
    failures.append("metric-coverage job must declare ordered steps")
    steps = []
checkout = named_step(steps, "Check out repository")
require(checkout.get("uses") == "actions/checkout@v4" and checkout.get("with") == {"persist-credentials": "false"}, "metric-coverage checkout must use the reviewed credential-free action")
main_guard = named_step(steps, "Enforce remote-main source")
require("GITHUB_REF" in str(main_guard.get("run")) and "refs/heads/main" in str(main_guard.get("run")), "metric-coverage workflow must retain its shell-level main-source guard")
node = named_step(steps, "Set up Node")
require(node.get("uses") == "actions/setup-node@v4" and node.get("with") == {"node-version": "22"}, "metric-coverage workflow must use the reviewed Node 22 runtime")
python = named_step(steps, "Set up Python")
require(python.get("uses") == "actions/setup-python@v5" and python.get("with") == {"python-version": "3.11"}, "metric-coverage workflow must use the reviewed Python runtime")
install = named_step(steps, "Install script dependencies")
require(install.get("run") == "python -m pip install --disable-pip-version-check PyYAML==6.0.2", "metric-coverage workflow must install only its fixed parser dependency")
validate = named_step(steps, "Validate fixed metric-coverage policy locally")
require(validate.get("run") == "npm run platform:shell:metric-coverage -- --validate", "metric-coverage workflow must validate policy before credentials")
credentials = named_step(steps, "Configure coverage AWS credentials")
require(credentials.get("uses") == "aws-actions/configure-aws-credentials@v4" and credentials.get("with") == {"role-to-assume": "${{ env.AWS_ROLE_ARN }}", "aws-region": "${{ env.AWS_REGION }}"}, "metric-coverage workflow must assume only its declared role and region")
run = named_step(steps, "Verify metric coverage and notify only on concern")
require(run.get("run") == expected_execution_policy["command"], "metric-coverage workflow must run only the exact bounded coverage command")
step_names = [step.get("name") for step in steps if isinstance(step, dict)]
required_order = ["Validate fixed metric-coverage policy locally", "Configure coverage AWS credentials", "Verify metric coverage and notify only on concern"]
require(all(name in step_names for name in required_order) and [step_names.index(name) for name in required_order] == sorted(step_names.index(name) for name in required_order), "metric-coverage validation, OIDC configuration, and live query must occur in that order")

scripts = mapping(package.get("scripts"), "package scripts")
require(scripts.get("platform:shell:metric-coverage") == "bash scripts/04.deploy/run-platform-shell-metric-coverage/script.sh", "package script must expose the governed metric-coverage command")
require(scripts.get("platform:shell:metric-coverage:check") == "bash scripts/04.deploy/run-platform-shell-metric-coverage/smoke-test.sh", "package script must expose the metric-coverage local check")
if not COMMAND_PATH.is_file():
    failures.append("metric-coverage command source is missing")
else:
    command_source = COMMAND_PATH.read_text(encoding="utf-8")
    require("secretsmanager" not in command_source.lower(), "metric-coverage command must not read secrets")
    require("platform-smoke" in command_source and "promql" in command_source.lower() and "sns" in command_source.lower(), "metric-coverage command must retain its reviewed target query and fixed notification boundary")

if failures:
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    raise SystemExit(1)

print("Platform-shell metric-coverage static policy check passed.")
PY
