#!/usr/bin/env python3
"""Fail closed when the declared Kanbien staging deployment state is not live."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.reconcile-platform-shell-staging
#   version: 4
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
from datetime import datetime, timezone
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
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
AWS_MAX_ATTEMPTS = 3
AWS_RETRY_BACKOFF_SECONDS = (1, 2)


class ReconciliationError(Exception):
    """Represent one bounded failure without exposing a provider payload."""


def parse_arguments() -> argparse.Namespace:
    """Accept only a static check, a recurring check, or a reviewed pre-change-set check."""

    parser = argparse.ArgumentParser(description="Safely reconcile the declared Kanbien staging deployment state.")
    parser.add_argument("--validate", action="store_true", help="Validate source only; make no AWS call.")
    parser.add_argument("--mode", choices=("continuous", "pre-foundation-change-set", "role-policy-alignment"), default="continuous")
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
    if arguments.mode != "pre-foundation-change-set" and arguments.foundation_change_set:
        parser.error("--foundation-change-set is permitted only for pre-foundation-change-set mode")
    if arguments.mode == "role-policy-alignment" and not arguments.validate and arguments.aws_credential_source != "target-profile":
        parser.error("role-policy-alignment requires the declared administrator target-profile credentials")
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
    drift_evidence = mapping(reconciliation.get("drift_evidence"), "drift-evidence-policy-missing")
    live_role_policy_alignment = mapping(reconciliation.get("live_role_policy_alignment"), "live-role-policy-alignment-missing")
    expected_drift_evidence = {
        "strategy": "separate-target-scoped-detector",
        "github_role_may_start_detection": False,
        "github_role_evidence": "fresh-in-sync-stack-summary-only",
        "maximum_evidence_age_seconds": 21600,
        "resource_read_contract": "infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/resource-read-contract.yml",
        "detector_deployment_status": "source-planned-not-deployed",
        "operational_coverage": "blocked-pending-reviewed-detector-role-workload-cost-and-live-proof",
    }
    if drift_evidence != expected_drift_evidence:
        raise ReconciliationError("drift-evidence-policy-not-reviewed")
    expected_live_role_policy_alignment = {
        "role_name": "github-platform-shell-staging-reconciliation",
        "inline_policy_name": "ReadDeclaredStagingControls",
        "desired_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json",
        "status": "source-defined-live-application-required",
        "command": "npm run platform:shell:deployment-reconciliation:role-policy-alignment",
        "required_before_foundation_change_set_execution": True,
        "output_policy": "safe-check-identifier-and-verdict-only-no-live-policy-content",
    }
    if live_role_policy_alignment != expected_live_role_policy_alignment:
        raise ReconciliationError("live-role-policy-alignment-not-reviewed")
    if reconciliation != {
        "status": "source-implemented-live-role-alignment-and-detector-pending",
        "command": "npm run platform:shell:deployment-reconciliation",
        "policy_check": "npm run platform:shell:deployment-reconciliation:policy-check",
        "modes": {
            "continuous": "scheduled-read-only-verification-of-declared-live-controls",
            "pre_foundation_change_set": "required-immediately-before-any-foundation-change-set-execution",
            "role_policy_alignment": "admin-only-source-to-live-inline-policy-comparison",
        },
        "workflow": ".github/workflows/reconcile-platform-shell-staging.yml",
        "schedule_cron_utc": "15 */4 * * *",
        "execution_identity": "github-platform-shell-staging-reconciliation",
        "role_arn": f"arn:aws:iam::{account_id}:role/github-platform-shell-staging-reconciliation",
        "role_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json",
        "trust_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-trust.json",
        "output_policy": "safe-check-identifiers-and-verdicts-only-no-provider-response-secret-endpoint-or-resource-content",
        "fail_closed": True,
        "drift_evidence": expected_drift_evidence,
        "live_role_policy_alignment": expected_live_role_policy_alignment,
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
        "maximum_drift_evidence_age_seconds": expected_drift_evidence["maximum_evidence_age_seconds"],
        "reconciliation_role_name": expected_live_role_policy_alignment["role_name"],
        "reconciliation_inline_policy_name": expected_live_role_policy_alignment["inline_policy_name"],
        "reconciliation_policy_source": expected_live_role_policy_alignment["desired_policy_source"],
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


def check_stack_drift_evidence(arguments: argparse.Namespace, policy: dict[str, Any], stack: str, check_id: str) -> None:
    """Require fresh passive IN_SYNC evidence without giving GitHub an active detector permission."""

    payload = run_aws(
        arguments,
        policy,
        ["cloudformation", "describe-stacks", "--stack-name", stack, "--query", "Stacks[0].DriftInformation.{status:StackDriftStatus,checked:LastCheckTimestamp}"],
        f"{check_id}-summary-unavailable",
    )
    if not isinstance(payload, dict):
        raise ReconciliationError(check_id)
    if payload.get("status") != "IN_SYNC":
        raise ReconciliationError(check_id)
    try:
        checked_at = datetime.fromisoformat(str(payload.get("checked")).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exception:
        raise ReconciliationError(f"{check_id}-evidence-missing") from exception
    age_seconds = (datetime.now(timezone.utc) - checked_at).total_seconds()
    if age_seconds < 0 or age_seconds > policy["maximum_drift_evidence_age_seconds"]:
        raise ReconciliationError(f"{check_id}-evidence-stale")


def check_reconciliation_live_role_policy(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Require the administrator pre-change identity to prove the role matches reviewed source."""

    source_path = REPOSITORY_ROOT / policy["reconciliation_policy_source"]
    try:
        with source_path.open(encoding="utf-8") as handle:
            desired_policy = json.load(handle)
    except (OSError, json.JSONDecodeError) as exception:
        raise ReconciliationError("reconciliation-role-policy-source-unreadable") from exception
    live_policy = run_aws(
        arguments,
        policy,
        [
            "iam",
            "get-role-policy",
            "--role-name",
            policy["reconciliation_role_name"],
            "--policy-name",
            policy["reconciliation_inline_policy_name"],
            "--query",
            "PolicyDocument",
        ],
        "reconciliation-live-role-policy-unavailable",
    )
    require(live_policy == desired_policy, "reconciliation-live-role-policy")


def artifact_bucket_checks(arguments: argparse.Namespace, policy: dict[str, Any]) -> list[tuple[str, Callable[[], None]]]:
    """Return each private artifact-store control as one independently attributable check."""

    bucket = policy["artifact_bucket"]
    return [
        (
            "artifact-bucket-public-access-control",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-public-access-block", "--bucket", bucket, "--query", "PublicAccessBlockConfiguration"])
                == {"BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True},
                "artifact-bucket-public-access-control",
            ),
        ),
        (
            "artifact-bucket-encryption",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-bucket-encryption", "--bucket", bucket, "--query", "ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm"])
                == "AES256",
                "artifact-bucket-encryption",
            ),
        ),
        (
            "artifact-bucket-ownership",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-bucket-ownership-controls", "--bucket", bucket, "--query", "OwnershipControls.Rules[0].ObjectOwnership"])
                == "BucketOwnerEnforced",
                "artifact-bucket-ownership",
            ),
        ),
        (
            "artifact-bucket-lifecycle",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-bucket-lifecycle-configuration", "--bucket", bucket, "--query", "Rules"])
                == [{"ID": "expire-reviewed-change-set-templates", "Status": "Enabled", "Filter": {"Prefix": "change-sets/"}, "Expiration": {"Days": 30}, "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 1}}],
                "artifact-bucket-lifecycle",
            ),
        ),
        (
            "artifact-bucket-policy-status",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-bucket-policy-status", "--bucket", bucket, "--query", "PolicyStatus.IsPublic"])
                is False,
                "artifact-bucket-policy-status",
            ),
        ),
    ]


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
        if not arguments.validate and arguments.mode == "role-policy-alignment":
            run_check(
                "reconciliation-live-role-policy",
                lambda: check_reconciliation_live_role_policy(arguments, policy),
            )
            checks.append({"id": "reconciliation-live-role-policy", "verdict": "passed"})
        elif not arguments.validate:
            core_checks = [
                ("aws-account", lambda: check_identity(arguments, policy)),
                ("artifact-stack-status", lambda: check_stack_status(arguments, policy, policy["artifact_stack"], "CREATE_COMPLETE", "artifact-stack-status")),
                ("artifact-stack-drift-evidence", lambda: check_stack_drift_evidence(arguments, policy, policy["artifact_stack"], "artifact-stack-drift")),
                ("foundation-stack-status", lambda: check_stack_status(arguments, policy, policy["foundation_stack"], "UPDATE_COMPLETE", "foundation-stack-status")),
                ("foundation-stack-drift-evidence", lambda: check_stack_drift_evidence(arguments, policy, policy["foundation_stack"], "foundation-stack-drift")),
                *artifact_bucket_checks(arguments, policy),
                ("platform-shell-budget", lambda: check_budget(arguments, policy)),
            ]
            for check_id, check in core_checks:
                run_check(check_id, check)
                checks.append({"id": check_id, "verdict": "passed"})
            if arguments.mode == "pre-foundation-change-set":
                run_check(
                    "reconciliation-live-role-policy",
                    lambda: check_reconciliation_live_role_policy(arguments, policy),
                )
                checks.append({"id": "reconciliation-live-role-policy", "verdict": "passed"})
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
