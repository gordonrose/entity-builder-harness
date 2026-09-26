#!/usr/bin/env python3
"""Fail closed when the declared Kanbien staging deployment state is not live."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.reconcile-platform-shell-staging
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Safely reconcile declared Kanbien staging controls before mutation and on a recurring read-only cadence.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network
#   used_by:
#   - id: package.script.platform-shell-deployment-reconciliation
#     path: package.json

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import subprocess
import sys
import time
from collections.abc import Callable
from typing import Any


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SAFE_SCHEMA = "deploy/platform-shell-reconciliation-result/v1"
DRIFT_WAIT_SECONDS = 60
AWS_MAX_ATTEMPTS = 3
AWS_RETRY_BACKOFF_SECONDS = (1, 2)


class ReconciliationError(Exception):
    """Represent one bounded failure without exposing a provider payload."""


def parse_arguments() -> argparse.Namespace:
    """Accept only a static check, a recurring check, or a reviewed pre-change-set check."""

    parser = argparse.ArgumentParser(description="Safely reconcile the declared Kanbien staging deployment state.")
    parser.add_argument("--validate", action="store_true", help="Validate source only; make no AWS call.")
    parser.add_argument("--mode", choices=("continuous", "pre-foundation-change-set"), default="continuous")
    parser.add_argument("--foundation-change-set", help="The reviewed Foundation change-set name, required only for pre-foundation-change-set mode.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE)
    parser.add_argument("--aws-cli", default="aws")
    parser.add_argument("--aws-credential-source", choices=("target-profile", "environment"), default="target-profile")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--json", action="store_true", help="Emit only the safe structured reconciliation verdict.")
    arguments = parser.parse_args()
    if not 1 <= arguments.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 1 and 30")
    if arguments.validate and arguments.foundation_change_set:
        parser.error("--validate cannot inspect a change set")
    if arguments.mode == "pre-foundation-change-set" and not arguments.validate and not arguments.foundation_change_set:
        parser.error("--foundation-change-set is required for pre-foundation-change-set mode")
    if arguments.mode == "continuous" and arguments.foundation_change_set:
        parser.error("--foundation-change-set is permitted only for pre-foundation-change-set mode")
    return arguments


def load_yaml(path: Path) -> dict[str, Any]:
    """Load one reviewed target profile and reject any malformed source."""

    try:
        import yaml
    except ImportError as exception:
        raise ReconciliationError("source-parser-unavailable") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise ReconciliationError("target-profile-unreadable") from exception
    if not isinstance(document, dict):
        raise ReconciliationError("target-profile-invalid")
    return document


def mapping(value: Any, code: str) -> dict[str, Any]:
    """Require a map rather than adopting a default for deployment control data."""

    if not isinstance(value, dict):
        raise ReconciliationError(code)
    return value


def text(value: Any, code: str) -> str:
    """Require one non-empty trusted source string."""

    if not isinstance(value, str) or not value:
        raise ReconciliationError(code)
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract exactly the small set of non-secret controls that can be reconciled."""

    cloud = mapping(profile.get("cloud"), "cloud-policy-missing")
    deployment = mapping(profile.get("deployment"), "deployment-policy-missing")
    cloudformation = mapping(deployment.get("cloudformation"), "cloudformation-policy-missing")
    reconciliation = mapping(deployment.get("reconciliation"), "reconciliation-policy-missing")
    operations = mapping(profile.get("operations"), "operations-policy-missing")
    budget = mapping(operations.get("budget"), "budget-policy-missing")
    allocation = mapping(budget.get("cost_allocation"), "budget-allocation-policy-missing")
    account_id = text(cloud.get("account_id"), "account-id-missing")
    region = text(cloud.get("region"), "region-missing")
    aws_profile = text(cloud.get("profile"), "aws-profile-missing")
    foundation_stack = text(cloudformation.get("foundation_stack"), "foundation-stack-missing")
    artifact_stack = text(cloudformation.get("deployment_artifact_store_stack"), "artifact-stack-missing")
    artifact_bucket = text(cloudformation.get("deployment_artifact_bucket_name"), "artifact-bucket-missing")
    if not account_id.isdigit() or len(account_id) != 12 or region != "eu-west-1":
        raise ReconciliationError("target-account-or-region-invalid")
    if reconciliation != {
        "status": "source-defined-pending-live-role-deployment",
        "command": "npm run platform:shell:deployment-reconciliation",
        "policy_check": "npm run platform:shell:deployment-reconciliation:policy-check",
        "modes": {
            "continuous": "scheduled-read-only-verification-of-declared-live-controls",
            "pre_foundation_change_set": "required-immediately-before-any-foundation-change-set-execution",
        },
        "workflow": ".github/workflows/reconcile-platform-shell-staging.yml",
        "schedule_cron_utc": "15 */4 * * *",
        "execution_identity": "github-platform-shell-staging-reconciliation",
        "role_arn": f"arn:aws:iam::{account_id}:role/github-platform-shell-staging-reconciliation",
        "role_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json",
        "trust_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-trust.json",
        "output_policy": "safe-check-identifiers-and-verdicts-only-no-provider-response-secret-endpoint-or-resource-content",
        "fail_closed": True,
        "foundation_change_set_scope": reconciliation.get("foundation_change_set_scope"),
    }:
        raise ReconciliationError("reconciliation-policy-not-reviewed")
    if budget.get("name") != "kanbien-staging-platform-shell-monthly" or budget.get("amount_usd") != 25 or budget.get("period") != "monthly":
        raise ReconciliationError("budget-policy-not-reviewed")
    if allocation != {
        "resource_tag_key": "service",
        "resource_tag_value": "platform-shell",
        "billing_report_dimension": "user:service",
        "activation_status": allocation.get("activation_status"),
        "live_configuration_proof": allocation.get("live_configuration_proof"),
        "budget_proof_requirement": allocation.get("budget_proof_requirement"),
    }:
        raise ReconciliationError("budget-allocation-policy-not-reviewed")
    scope = mapping(reconciliation.get("foundation_change_set_scope"), "change-set-scope-missing")
    additions = scope.get("additions")
    modifications = scope.get("modifications")
    if not isinstance(additions, list) or not isinstance(modifications, list) or len(additions) != 22 or len(modifications) != 1:
        raise ReconciliationError("change-set-scope-invalid")
    expected_additions = {
        ("RelationalBootstrapTaskRole", "AWS::IAM::Role"),
        ("RelationalDatabaseConnectionsHighAlarm", "AWS::CloudWatch::Alarm"),
        ("RelationalDatabaseCpuHighAlarm", "AWS::CloudWatch::Alarm"),
        ("RelationalDatabaseEgressFromRelay", "AWS::EC2::SecurityGroupEgress"),
        ("RelationalDatabaseEgressFromServer", "AWS::EC2::SecurityGroupEgress"),
        ("RelationalDatabaseEgressFromWorker", "AWS::EC2::SecurityGroupEgress"),
        ("RelationalDatabaseEventSubscription", "AWS::RDS::EventSubscription"),
        ("RelationalDatabaseFreeStorageLowAlarm", "AWS::CloudWatch::Alarm"),
        ("RelationalDatabaseIngressFromRelay", "AWS::EC2::SecurityGroupIngress"),
        ("RelationalDatabaseIngressFromServer", "AWS::EC2::SecurityGroupIngress"),
        ("RelationalDatabaseIngressFromWorker", "AWS::EC2::SecurityGroupIngress"),
        ("RelationalDatabaseParameterGroup", "AWS::RDS::DBParameterGroup"),
        ("RelationalDatabaseSecurityGroup", "AWS::EC2::SecurityGroup"),
        ("RelationalDatabaseSubnetGroup", "AWS::RDS::DBSubnetGroup"),
        ("RelationalDatabase", "AWS::RDS::DBInstance"),
        ("RelationalMigrationSecretAttachment", "AWS::SecretsManager::SecretTargetAttachment"),
        ("RelationalMigrationSecret", "AWS::SecretsManager::Secret"),
        ("RelationalMigrationTaskRole", "AWS::IAM::Role"),
        ("RelationalRuntimeSecretAttachment", "AWS::SecretsManager::SecretTargetAttachment"),
        ("RelationalRuntimeSecret", "AWS::SecretsManager::Secret"),
        ("RelationalRuntimeTaskRole", "AWS::IAM::Role"),
        ("RelationalTargetConfiguration", "AWS::SSM::Parameter"),
    }
    declared_additions = {(item.get("logical_id"), item.get("resource_type")) for item in additions if isinstance(item, dict)}
    declared_modifications = {(item.get("logical_id"), item.get("resource_type"), item.get("replacement")) for item in modifications if isinstance(item, dict)}
    if declared_additions != expected_additions or declared_modifications != {("AlarmTopicPolicy", "AWS::SNS::TopicPolicy", False)}:
        raise ReconciliationError("change-set-scope-not-reviewed")
    return {
        "account_id": account_id,
        "region": region,
        "aws_profile": aws_profile,
        "artifact_stack": artifact_stack,
        "artifact_bucket": artifact_bucket,
        "foundation_stack": foundation_stack,
        "budget_name": budget["name"],
        "budget_arn": f"arn:aws:budgets::{account_id}:budget/{budget['name']}",
        "expected_changes": {
            *( ("Add", logical_id, resource_type, None) for logical_id, resource_type in expected_additions ),
            ("Modify", "AlarmTopicPolicy", "AWS::SNS::TopicPolicy", False),
        },
    }


def run_aws(
    arguments: argparse.Namespace,
    policy: dict[str, Any],
    command: list[str],
    failure_code: str = "aws-verification-unavailable",
) -> Any:
    """Run one fixed AWS operation with small bounded retries and no error-payload output."""

    invocation = [arguments.aws_cli, *command, "--region", policy["region"], "--output", "json"]
    if arguments.aws_credential_source == "target-profile":
        invocation.extend(["--profile", policy["aws_profile"]])
    for attempt in range(AWS_MAX_ATTEMPTS):
        try:
            completed = subprocess.run(invocation, check=True, capture_output=True, text=True, timeout=arguments.timeout_seconds)
            return json.loads(completed.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exception:
            if attempt == AWS_MAX_ATTEMPTS - 1:
                raise ReconciliationError(failure_code) from exception
            time.sleep(AWS_RETRY_BACKOFF_SECONDS[attempt])
    raise AssertionError("bounded AWS verification retry loop did not return")


def require(condition: bool, code: str) -> None:
    """Fail closed with a stable safe result code."""

    if not condition:
        raise ReconciliationError(code)


def run_check(check_id: str, check: Callable[[], None]) -> None:
    """Preserve a safe owning-control identifier when a provider call is unavailable."""

    try:
        check()
    except ReconciliationError as exception:
        if str(exception) == "aws-verification-unavailable":
            raise ReconciliationError(f"{check_id}-verification-unavailable") from exception
        raise


def check_identity(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Verify that credentials are for the one declared AWS account."""

    payload = run_aws(arguments, policy, ["sts", "get-caller-identity"])
    require(payload.get("Account") == policy["account_id"], "aws-account-mismatch")


def check_stack_status(arguments: argparse.Namespace, policy: dict[str, Any], stack: str, expected_status: str, check_id: str) -> None:
    """Require a stable stack state before relying on a target control."""

    payload = run_aws(arguments, policy, ["cloudformation", "describe-stacks", "--stack-name", stack, "--query", "Stacks[0].StackStatus"])
    require(payload == expected_status, check_id)


def check_stack_drift(arguments: argparse.Namespace, policy: dict[str, Any], stack: str, check_id: str) -> None:
    """Request drift detection and require a fresh in-sync stack summary without wildcard IAM."""

    started_at = datetime.now(timezone.utc)
    started = run_aws(
        arguments,
        policy,
        ["cloudformation", "detect-stack-drift", "--stack-name", stack, "--query", "StackDriftDetectionId"],
        f"{check_id}-detection-unavailable",
    )
    detection_id = started if isinstance(started, str) else None
    if not isinstance(detection_id, str) or not detection_id:
        raise ReconciliationError(check_id)
    deadline = time.monotonic() + DRIFT_WAIT_SECONDS
    while time.monotonic() < deadline:
        result = run_aws(
            arguments,
            policy,
            ["cloudformation", "describe-stacks", "--stack-name", stack, "--query", "Stacks[0].DriftInformation.{status:StackDriftStatus,checked:LastCheckTimestamp}"],
            f"{check_id}-summary-unavailable",
        )
        if not isinstance(result, dict):
            raise ReconciliationError(check_id)
        status = result.get("status")
        checked = result.get("checked")
        try:
            checked_at = datetime.fromisoformat(str(checked).replace("Z", "+00:00"))
        except ValueError:
            raise ReconciliationError(check_id)
        if status == "IN_SYNC" and checked_at >= started_at - timedelta(seconds=2):
            return
        if status in ("DRIFTED", "UNKNOWN"):
            raise ReconciliationError(check_id)
        time.sleep(2)
    raise ReconciliationError(check_id)


def check_artifact_bucket(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Verify the private, encrypted template transport control without reading policy content."""

    bucket = policy["artifact_bucket"]
    commands = {
        "public_access": ["s3api", "get-public-access-block", "--bucket", bucket, "--query", "PublicAccessBlockConfiguration"],
        "encryption": ["s3api", "get-bucket-encryption", "--bucket", bucket, "--query", "ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm"],
        "ownership": ["s3api", "get-bucket-ownership-controls", "--bucket", bucket, "--query", "OwnershipControls.Rules[0].ObjectOwnership"],
        "lifecycle": ["s3api", "get-bucket-lifecycle-configuration", "--bucket", bucket, "--query", "Rules"],
        "public_status": ["s3api", "get-bucket-policy-status", "--bucket", bucket, "--query", "PolicyStatus.IsPublic"],
    }
    values = {name: run_aws(arguments, policy, command) for name, command in commands.items()}
    public_access = values["public_access"]
    require(public_access == {"BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True}, "artifact-bucket-public-access-control")
    encryption = values["encryption"]
    require(encryption == "AES256", "artifact-bucket-encryption")
    ownership = values["ownership"]
    require(ownership == "BucketOwnerEnforced", "artifact-bucket-ownership")
    lifecycle = values["lifecycle"]
    require(lifecycle == [{"ID": "expire-reviewed-change-set-templates", "Status": "Enabled", "Filter": {"Prefix": "change-sets/"}, "Expiration": {"Days": 30}, "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 1}}], "artifact-bucket-lifecycle")
    public_status = values["public_status"]
    require(public_status is False, "artifact-bucket-policy-status")


def check_budget(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Require the one declared 25 USD monthly service-tag-scoped budget."""

    payload = run_aws(arguments, policy, ["budgets", "describe-budget", "--account-id", policy["account_id"], "--budget-name", policy["budget_name"], "--query", "Budget.{name:BudgetName,limit:BudgetLimit,period:TimeUnit,type:BudgetType,filters:CostFilters}"])
    try:
        amount = Decimal(str(payload.get("limit", {}).get("Amount")))
    except (AttributeError, InvalidOperation):
        raise ReconciliationError("platform-shell-budget")
    require(
        payload.get("name") == policy["budget_name"]
        and amount == Decimal("25")
        and payload.get("limit", {}).get("Unit") == "USD"
        and payload.get("period") == "MONTHLY"
        and payload.get("type") == "COST"
        and payload.get("filters") == {"TagKeyValue": ["user:service$platform-shell"]},
        "platform-shell-budget",
    )


def check_change_set(arguments: argparse.Namespace, policy: dict[str, Any], change_set: str) -> None:
    """Require exactly the already-reviewed Foundation change-set scope before execution."""

    payload = run_aws(arguments, policy, ["cloudformation", "describe-change-set", "--stack-name", policy["foundation_stack"], "--change-set-name", change_set, "--query", "{status:Status,execution:ExecutionStatus,changes:Changes[].ResourceChange.{action:Action,logicalId:LogicalResourceId,resourceType:ResourceType,replacement:Replacement}}"])
    require(payload.get("status") == "CREATE_COMPLETE" and payload.get("execution") == "AVAILABLE", "foundation-change-set-state")
    changes = payload.get("changes")
    require(isinstance(changes, list), "foundation-change-set-scope")
    actual_changes = set()
    for change in changes:
        if not isinstance(change, dict):
            raise ReconciliationError("foundation-change-set-scope")
        replacement = change.get("replacement")
        normalized_replacement = False if replacement == "False" else None if replacement is None else replacement
        actual_changes.add((change.get("action"), change.get("logicalId"), change.get("resourceType"), normalized_replacement))
    require(actual_changes == policy["expected_changes"] and len(changes) == len(policy["expected_changes"]), "foundation-change-set-scope")


def result(mode: str, checks: list[dict[str, str]], verdict: str) -> dict[str, Any]:
    """Build the sole safe output envelope for local and CI execution."""

    return {"schema": SAFE_SCHEMA, "target": "kanbien/staging", "mode": mode, "verdict": verdict, "checks": checks}


def main() -> int:
    """Validate source, then run each declared non-secret control check in order."""

    arguments = parse_arguments()
    checks: list[dict[str, str]] = []
    try:
        policy = resolve_policy(load_yaml(Path(arguments.target_profile)))
        checks.append({"id": "source-policy", "verdict": "passed"})
        if not arguments.validate:
            core_checks = [
                ("aws-account", lambda: check_identity(arguments, policy)),
                ("artifact-stack-status", lambda: check_stack_status(arguments, policy, policy["artifact_stack"], "CREATE_COMPLETE", "artifact-stack-status")),
                ("foundation-stack-status", lambda: check_stack_status(arguments, policy, policy["foundation_stack"], "UPDATE_COMPLETE", "foundation-stack-status")),
                ("foundation-stack-drift", lambda: check_stack_drift(arguments, policy, policy["foundation_stack"], "foundation-stack-drift")),
                ("artifact-bucket-controls", lambda: check_artifact_bucket(arguments, policy)),
                ("platform-shell-budget", lambda: check_budget(arguments, policy)),
            ]
            if arguments.mode == "continuous":
                core_checks.insert(3, ("artifact-stack-drift", lambda: check_stack_drift(arguments, policy, policy["artifact_stack"], "artifact-stack-drift")))
            for check_id, check in core_checks:
                run_check(check_id, check)
                checks.append({"id": check_id, "verdict": "passed"})
            if arguments.mode == "pre-foundation-change-set":
                run_check(
                    "foundation-change-set-scope",
                    lambda: check_change_set(arguments, policy, arguments.foundation_change_set),
                )
                checks.append({"id": "foundation-change-set-scope", "verdict": "passed"})
        print(json.dumps(result(arguments.mode, checks, "passed"), sort_keys=True))
        return 0
    except ReconciliationError as exception:
        checks.append({"id": str(exception), "verdict": "blocked"})
        print(json.dumps(result(arguments.mode, checks, "blocked"), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
