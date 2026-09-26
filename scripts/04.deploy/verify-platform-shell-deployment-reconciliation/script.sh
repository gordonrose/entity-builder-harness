#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-deployment-reconciliation
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Statically verify the fail-closed Kanbien staging deployment reconciliation policy, workflow, and IAM sources.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-deployment-reconciliation-policy-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 - <<'PY'
import json
from pathlib import Path
import sys

try:
    import yaml
except ImportError as error:
    raise SystemExit("ERROR: PyYAML is required. Install PyYAML==6.0.2 before this check.") from error


def yaml_file(path):
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def json_file(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition, message):
    if not condition:
        failures.append(message)


failures = []
profile = yaml_file("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
workflow = yaml_file(".github/workflows/reconcile-platform-shell-staging.yml")
policy = json_file("infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json")
trust = json_file("infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-trust.json")
scripts = json_file("package.json")["scripts"]

reconciliation = profile.get("deployment", {}).get("reconciliation", {})
expected_config = {
    "status": "source-defined-pending-live-role-deployment",
    "command": "npm run platform:shell:deployment-reconciliation",
    "policy_check": "npm run platform:shell:deployment-reconciliation:policy-check",
    "modes": {"continuous": "scheduled-read-only-verification-of-declared-live-controls", "pre_foundation_change_set": "required-immediately-before-any-foundation-change-set-execution"},
    "workflow": ".github/workflows/reconcile-platform-shell-staging.yml",
    "schedule_cron_utc": "15 */4 * * *",
    "execution_identity": "github-platform-shell-staging-reconciliation",
    "role_arn": "arn:aws:iam::337159794548:role/github-platform-shell-staging-reconciliation",
    "role_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json",
    "trust_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-trust.json",
    "output_policy": "safe-check-identifiers-and-verdicts-only-no-provider-response-secret-endpoint-or-resource-content",
    "fail_closed": True,
}
for key, expected in expected_config.items():
    require(reconciliation.get(key) == expected, f"reconciliation.{key} must retain the reviewed value")
scope = reconciliation.get("foundation_change_set_scope", {})
require(isinstance(scope, dict) and len(scope.get("additions", [])) == 22, "reconciliation must enumerate exactly 22 approved additions")
require(scope.get("modifications") == [{"logical_id": "AlarmTopicPolicy", "resource_type": "AWS::SNS::TopicPolicy", "replacement": False}], "reconciliation must permit only the reviewed non-replacement topic-policy modification")
require(profile.get("operations", {}).get("budget", {}).get("name") == "kanbien-staging-platform-shell-monthly", "operations must use the canonical live platform-shell budget name")
require(profile.get("persistence", {}).get("relational_reference", {}).get("operations", {}).get("cost", {}).get("existing_tag_scoped_budget") == "kanbien-staging-platform-shell-monthly", "relational reference must use the canonical live platform-shell budget name")

expected_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "VerifyDeclaredFoundationAndArtifactStacks", "Effect": "Allow", "Action": ["cloudformation:DescribeStacks", "cloudformation:DetectStackDrift"], "Resource": ["arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-staging-platform-shell-deployment-artifacts/*", "arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-staging-platform-shell-foundation/*"]},
        {"Sid": "VerifyDeclaredArtifactBucketControls", "Effect": "Allow", "Action": ["s3:GetBucketEncryption", "s3:GetBucketLifecycleConfiguration", "s3:GetBucketOwnershipControls", "s3:GetBucketPolicyStatus", "s3:GetBucketPublicAccessBlock"], "Resource": "arn:aws:s3:::kanbien-staging-platform-shell-cfn-artifacts-337159794548"},
        {"Sid": "VerifyDeclaredPlatformShellBudget", "Effect": "Allow", "Action": "budgets:ViewBudget", "Resource": "arn:aws:budgets::337159794548:budget/kanbien-staging-platform-shell-monthly"},
        {"Sid": "VerifyCallerAccountOnly", "Effect": "Allow", "Action": "sts:GetCallerIdentity", "Resource": "*"},
    ],
}
require(policy == expected_policy, "reconciliation IAM policy must retain exactly the reviewed read-only permissions")
expected_trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Federated": "arn:aws:iam::337159794548:oidc-provider/token.actions.githubusercontent.com"}, "Action": "sts:AssumeRoleWithWebIdentity", "Condition": {"StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com", "token.actions.githubusercontent.com:repository": "gordonrose/entity-builder-harness", "token.actions.githubusercontent.com:ref": "refs/heads/main"}, "StringLike": {"token.actions.githubusercontent.com:sub": "repo:gordonrose/entity-builder-harness:ref:refs/heads/main"}}}]}
require(trust == expected_trust, "reconciliation GitHub trust policy must allow only this repository main branch")

triggers = workflow.get(True, workflow.get("on"))
require(triggers == {"schedule": [{"cron": "15 */4 * * *"}], "workflow_dispatch": {}}, "reconciliation workflow must retain only the reviewed cadence and manual dispatch")
require(workflow.get("permissions") == {"contents": "read", "id-token": "write"}, "reconciliation workflow must use only read and OIDC permissions")
require(workflow.get("concurrency") == {"group": "platform-shell-staging-reconciliation", "cancel-in-progress": False}, "reconciliation workflow must not overlap")
require(workflow.get("env") == {"AWS_REGION": "eu-west-1", "AWS_ROLE_ARN": "arn:aws:iam::337159794548:role/github-platform-shell-staging-reconciliation"}, "reconciliation workflow must name only the target role")
job = workflow.get("jobs", {}).get("reconcile", {})
require(set(workflow.get("jobs", {})) == {"reconcile"} and job.get("if") == "${{ github.ref == 'refs/heads/main' }}", "reconciliation workflow must contain one main-only job")
require(job.get("runs-on") == "ubuntu-latest" and job.get("timeout-minutes") == 5, "reconciliation workflow must retain the five-minute bound")
steps = job.get("steps", [])
names = [step.get("name") for step in steps if isinstance(step, dict)]
expected_names = ["Check out repository", "Enforce remote-main source", "Set up Node", "Set up Python", "Install script dependencies", "Validate reconciliation policy locally", "Configure reconciliation AWS credentials", "Reconcile declared AWS state"]
require(names == expected_names, "reconciliation workflow must validate source before credentials and run only continuous reconciliation")
if len(steps) == len(expected_names):
    require(steps[0].get("uses") == "actions/checkout@v4" and steps[0].get("with") == {"persist-credentials": False}, "reconciliation checkout must be credential-free")
    require(steps[5].get("run") == "npm run platform:shell:deployment-reconciliation -- --validate --json", "reconciliation source validation command must be fixed")
    require(steps[6].get("uses") == "aws-actions/configure-aws-credentials@v4" and steps[6].get("with") == {"role-to-assume": "${{ env.AWS_ROLE_ARN }}", "aws-region": "${{ env.AWS_REGION }}"}, "reconciliation may assume only its dedicated role")
    require(steps[7].get("run") == "npm run platform:shell:deployment-reconciliation -- --aws-credential-source environment --mode continuous --json", "reconciliation workflow must use only read-only continuous mode")

require(scripts.get("platform:shell:deployment-reconciliation") == "bash scripts/04.deploy/reconcile-platform-shell-staging/script.sh", "package must expose the reconciliation command")
require(scripts.get("platform:shell:deployment-reconciliation:check") == "bash scripts/04.deploy/reconcile-platform-shell-staging/smoke-test.sh", "package must expose the reconciliation local check")
require(scripts.get("platform:shell:deployment-reconciliation:policy-check") == "bash scripts/04.deploy/verify-platform-shell-deployment-reconciliation/script.sh", "package must expose the reconciliation policy check")
source = Path("scripts/04.deploy/reconcile-platform-shell-staging/script.py").read_text(encoding="utf-8").lower()
for prohibited in ("execute-change-set", "create-stack", "update-stack", "delete-stack", "put-object", "put-bucket", "put-budget", "get-secret-value"):
    require(prohibited not in source, f"reconciliation command must not contain {prohibited}")
for required in ("detect-stack-drift", "lastchecktimestamp", "get-bucket-policy-status", "describe-budget", "foundation-change-set-scope"):
    require(required in source, f"reconciliation command must retain {required}")

if failures:
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    raise SystemExit(1)
print("Platform-shell deployment reconciliation static policy check passed.")
PY
