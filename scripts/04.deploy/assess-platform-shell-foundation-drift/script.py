#!/usr/bin/env python3
"""Classify one bounded Foundation drift assessment without exposing provider values."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.assess-platform-shell-foundation-drift
#   version: 2
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Run one explicit administrator-only Foundation assessment and distinguish the reviewed PostgreSQL egress correction from unexpected drift.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
from typing import Any


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
ACTIVE_CONTRACT = "infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/administrator-active-foundation-assessment-contract.yml"
SAFE_SCHEMA = "deploy/platform-shell-foundation-active-drift-assessment-result/v2"
EVIDENCE_SCHEMA = "deploy/platform-shell-foundation-known-drift-evidence/v1"
MAX_POLL_ATTEMPTS = 36
POLL_INTERVAL_SECONDS = 5


class AssessmentError(Exception):
    """Represent one stable, safe assessment failure without provider detail."""

    def __init__(self, code: str, failure_class: str | None = None):
        super().__init__(code)
        self.failure_class = failure_class


class UnexpectedDrift(AssessmentError):
    """Carry only the approved structural facts needed to distinguish unknown drift."""

    def __init__(self, changes: list[dict[str, Any]]) -> None:
        super().__init__("unexpected-foundation-drift")
        self.changes = changes


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely classify the reviewed Kanbien staging Foundation drift.")
    parser.add_argument("--validate", action="store_true", help="Validate reviewed source only; make no AWS call.")
    parser.add_argument("--execute-approved-active-foundation-drift-assessment", action="store_true")
    parser.add_argument("--evidence-file", help="New /tmp path for a safe, short-lived assessment evidence record.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE)
    parser.add_argument("--aws-cli", default="aws")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--json", action="store_true", help="Emit only safe check identifiers, verdicts, and approved structural classification facts.")
    arguments = parser.parse_args()
    if not 1 <= arguments.timeout_seconds <= 120:
        parser.error("--timeout-seconds must be between 1 and 120")
    if not arguments.validate and not arguments.execute_approved_active_foundation_drift_assessment:
        parser.error("--execute-approved-active-foundation-drift-assessment is required for an AWS assessment")
    if arguments.validate and (arguments.execute_approved_active_foundation_drift_assessment or arguments.evidence_file):
        parser.error("--validate cannot be combined with execution options")
    if not arguments.validate:
        if not arguments.evidence_file:
            parser.error("--evidence-file is required for an AWS assessment")
        evidence_path = Path(arguments.evidence_file)
        if not evidence_path.is_absolute() or evidence_path.parent != Path("/tmp") or evidence_path.exists():
            parser.error("--evidence-file must be a new direct child of /tmp")
    return arguments


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
        with path.open(encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except Exception as exception:  # pragma: no cover - reduced to stable safe failure
        raise AssessmentError("reviewed-source-unreadable") from exception
    if not isinstance(value, dict):
        raise AssessmentError("reviewed-source-invalid")
    return value


def mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AssessmentError(code)
    return value


def text(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise AssessmentError(code)
    return value


def policy(profile: dict[str, Any]) -> dict[str, str]:
    cloud = mapping(profile.get("cloud"), "cloud-policy-missing")
    deployment = mapping(profile.get("deployment"), "deployment-policy-missing")
    cloudformation = mapping(deployment.get("cloudformation"), "cloudformation-policy-missing")
    reconciliation = mapping(deployment.get("reconciliation"), "reconciliation-policy-missing")
    drift_evidence = mapping(reconciliation.get("drift_evidence"), "drift-evidence-policy-missing")
    active = mapping(drift_evidence.get("administrator_active_assessment"), "active-drift-assessment-policy-missing")
    account = text(cloud.get("account_id"), "account-id-missing")
    region = text(cloud.get("region"), "region-missing")
    aws_profile = text(cloud.get("profile"), "aws-profile-missing")
    foundation_stack = text(cloudformation.get("foundation_stack"), "foundation-stack-missing")
    if account != "337159794548" or region != "eu-west-1" or aws_profile != "kanbien-dev" or foundation_stack != "kanbien-staging-platform-shell-foundation":
        raise AssessmentError("target-policy-not-reviewed")
    expected_active = {
        "status": "approved-administrator-only-foundation-drift-classification",
        "command": "npm run platform:shell:foundation-active-drift-assessment -- --execute-approved-active-foundation-drift-assessment --evidence-file /tmp/new-safe-evidence.json --json",
        "execution_identity": "target-profile-administrator-only-not-github",
        "scope": "foundation-stack-only-structural-drift-classification-no-resource-policy-role-or-workload-change",
        "allowed_operations": [
            "cloudformation:DetectStackDrift",
            "cloudformation:DescribeStackDriftDetectionStatus",
            "cloudformation:DescribeStackResourceDrifts",
            "cloudformation:DescribeStacks",
            "rds:DescribeDBInstances",
            "rds:DescribeDBParameters",
        ],
        "success_condition": "detection-complete-and-in-sync-or-only-known-relational-database-egress-property-addition-plus-declared-tls-normalization-and-effective-tls-required",
        "output_policy": "safe-check-identifiers-verdicts-and-safe-subprocess-failure-class-and-only-logical-resource-type-and-change-category-no-detection-id-provider-response-physical-id-or-property-values",
    }
    if active != expected_active or drift_evidence.get("administrator_active_assessment_contract") != ACTIVE_CONTRACT:
        raise AssessmentError("active-drift-assessment-policy-not-reviewed")
    return {"account": account, "region": region, "aws_profile": aws_profile, "foundation_stack": foundation_stack}


def verify_contract(contract: dict[str, Any], current_policy: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    expected = {
        "schema": "deploy/cloudformation-administrator-active-foundation-assessment-contract/v2",
        "target": "kanbien/staging",
        "status": "active",
        "identity": "target-profile-administrator",
        "identity_boundary": "existing-administrator-profile-only-no-github-role-policy-or-workload-change",
        "stack_name": current_policy["foundation_stack"],
        "stack_scope": "foundation-stack-only",
        "execution_gate": "explicit-current-chat-approval-and-stable-stack-preflight",
        "assessment_sequence": "detect-then-wait-for-completion-then-read-structural-resource-drift-only-if-drifted",
        "output_policy": "safe-check-identifiers-verdicts-and-safe-subprocess-failure-class-and-only-logical-resource-type-and-change-category-no-detection-id-provider-response-physical-id-or-property-values",
    }
    if any(contract.get(key) != value for key, value in expected.items()):
        raise AssessmentError("active-drift-assessment-contract-invalid")
    expected_signatures = [
        {
            "logical_resource_id": "RelationalDatabaseSecurityGroup",
            "resource_type": "AWS::EC2::SecurityGroup",
            "resource_drift_status": "MODIFIED",
            "property_path": "/SecurityGroupEgress",
            "change_categories": ["ADD", "NOT_EQUAL"],
        },
        {
            "logical_resource_id": "RelationalDatabaseParameterGroup",
            "resource_type": "AWS::RDS::DBParameterGroup",
            "resource_drift_status": "MODIFIED",
            "property_paths": ["/Parameters", "/Parameters/rds.force_ssl"],
            "change_categories": ["REMOVE"],
        },
    ]
    if contract.get("known_remediation_signatures") != expected_signatures:
        raise AssessmentError("known-remediation-signature-not-reviewed")
    expected_tls = {
        "fixed_database_identifier": "kanbien-staging-platform-relational",
        "required_parameter_name": "rds.force_ssl",
        "required_parameter_value": "1",
        "safe_verdict": "required",
    }
    if contract.get("effective_tls") != expected_tls:
        raise AssessmentError("effective-tls-policy-not-reviewed")
    operations = contract.get("operations")
    expected_operations = {
        ("aws-account", "sts:get-caller-identity", "sts:GetCallerIdentity"),
        ("foundation-stack", "cloudformation:describe-stacks", "cloudformation:DescribeStacks"),
        ("foundation-active-drift-assessment", "cloudformation:detect-stack-drift", "cloudformation:DetectStackDrift"),
        ("foundation-active-drift-assessment", "cloudformation:describe-stack-drift-detection-status", "cloudformation:DescribeStackDriftDetectionStatus"),
        ("foundation-drift-classification", "cloudformation:describe-stack-resource-drifts", "cloudformation:DescribeStackResourceDrifts"),
        ("relational-tls-effective-state", "rds:describe-db-instances", "rds:DescribeDBInstances"),
        ("relational-tls-effective-state", "rds:describe-db-parameters", "rds:DescribeDBParameters"),
    }
    actual_operations = {
        (item.get("check_id"), item.get("cli_operation"), item.get("iam_action"))
        for item in operations if isinstance(item, dict)
    } if isinstance(operations, list) else set()
    if actual_operations != expected_operations:
        raise AssessmentError("active-drift-assessment-operations-not-reviewed")
    prohibited = contract.get("prohibited")
    if not isinstance(prohibited, list) or "property-expected-or-actual-value-output" not in prohibited or "parameter-value-or-unrelated-parameter-name-output" not in prohibited or "change-set-or-stack-mutation" not in prohibited:
        raise AssessmentError("active-drift-assessment-prohibitions-not-reviewed")
    return expected_signatures, expected_tls


def run_aws(arguments: argparse.Namespace, current_policy: dict[str, str], command: list[str], failure: str) -> Any:
    invocation = [arguments.aws_cli, *command, "--profile", current_policy["aws_profile"], "--region", current_policy["region"], "--output", "json"]
    try:
        completed = subprocess.run(invocation, check=True, capture_output=True, text=True, timeout=arguments.timeout_seconds)
        return json.loads(completed.stdout)
    except subprocess.TimeoutExpired as exception:
        raise AssessmentError(failure, "timeout") from exception
    except subprocess.CalledProcessError as exception:
        raise AssessmentError(failure, "nonzero-exit") from exception
    except json.JSONDecodeError as exception:
        raise AssessmentError(failure, "invalid-json") from exception
    except OSError as exception:
        raise AssessmentError(failure, "process-start-failure") from exception


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AssessmentError(code)


def check_identity(arguments: argparse.Namespace, current_policy: dict[str, str]) -> None:
    account = run_aws(arguments, current_policy, ["sts", "get-caller-identity", "--query", "Account"], "aws-account-verification-unavailable")
    require(account == current_policy["account"], "aws-account-mismatch")


def check_foundation(arguments: argparse.Namespace, current_policy: dict[str, str]) -> None:
    status = run_aws(arguments, current_policy, ["cloudformation", "describe-stacks", "--stack-name", current_policy["foundation_stack"], "--query", "Stacks[0].StackStatus"], "foundation-stack-verification-unavailable")
    require(status == "UPDATE_COMPLETE", "foundation-stack-not-ready")


def classify_known(records: Any, signatures: list[dict[str, Any]]) -> list[dict[str, str]] | None:
    """Match only the declared structural signatures; keep property paths private."""

    if not isinstance(records, list) or not 1 <= len(records) <= len(signatures):
        return None
    changes: list[dict[str, str]] = []
    unmatched = list(signatures)
    for record in records:
        if not isinstance(record, dict):
            return None
        differences = record.get("differences")
        if not isinstance(differences, list) or len(differences) != 1 or not isinstance(differences[0], dict):
            return None
        difference = differences[0]
        matched: dict[str, Any] | None = None
        for signature in unmatched:
            permitted_paths = signature.get("property_paths", [signature.get("property_path")])
            if record.get("logical") == signature["logical_resource_id"] and record.get("type") == signature["resource_type"] and record.get("status") == signature["resource_drift_status"] and isinstance(difference.get("path"), str) and isinstance(permitted_paths, list) and any(isinstance(path, str) and difference["path"].startswith(path) for path in permitted_paths) and difference.get("category") in signature["change_categories"]:
                matched = signature
                break
        if matched is None:
            return None
        unmatched.remove(matched)
        changes.append({"logical_resource_id": record["logical"], "resource_type": record["type"], "change_category": str(difference["category"]).lower()})
    changes = sorted(changes, key=lambda item: item["logical_resource_id"])
    if not any(item["logical_resource_id"] == "RelationalDatabaseParameterGroup" for item in changes):
        return None
    return changes


def safe_structural_changes(records: Any) -> list[dict[str, Any]]:
    """Reduce provider output to the three explicitly approved classification facts."""

    if not isinstance(records, list):
        return []
    changes: list[dict[str, Any]] = []
    for record in records[:20]:
        if not isinstance(record, dict):
            continue
        logical = record.get("logical")
        resource_type = record.get("type")
        differences = record.get("differences")
        categories = sorted({item.get("category").lower() for item in differences if isinstance(item, dict) and isinstance(item.get("category"), str) and item.get("category") in {"ADD", "REMOVE", "NOT_EQUAL"}}) if isinstance(differences, list) else []
        if isinstance(logical, str) and isinstance(resource_type, str) and categories:
            changes.append({"logical_resource_id": logical, "resource_type": resource_type, "change_categories": categories})
    return changes


def check_effective_tls(arguments: argparse.Namespace, current_policy: dict[str, str], tls: dict[str, str]) -> None:
    """Read one allowlisted parameter and collapse its value to a safe verdict."""

    parameter_group = run_aws(
        arguments,
        current_policy,
        ["rds", "describe-db-instances", "--db-instance-identifier", tls["fixed_database_identifier"], "--query", "DBInstances[0].DBParameterGroups[0].DBParameterGroupName"],
        "relational-tls-instance-lookup-unavailable",
    )
    if not isinstance(parameter_group, str) or not parameter_group:
        raise AssessmentError("relational-tls-instance-lookup-invalid")
    value = run_aws(
        arguments,
        current_policy,
        ["rds", "describe-db-parameters", "--db-parameter-group-name", parameter_group, "--query", f"Parameters[?ParameterName==`{tls['required_parameter_name']}`].ParameterValue | [0]"],
        "relational-tls-parameter-verification-unavailable",
    )
    require(value == tls["required_parameter_value"], "relational-tls-not-required")


def assess_and_classify(arguments: argparse.Namespace, current_policy: dict[str, str], signatures: list[dict[str, Any]], tls: dict[str, str]) -> tuple[str, list[dict[str, str]] | None]:
    started = run_aws(arguments, current_policy, ["cloudformation", "detect-stack-drift", "--stack-name", current_policy["foundation_stack"]], "foundation-drift-assessment-start-unavailable")
    detection_id = started.get("StackDriftDetectionId") if isinstance(started, dict) else None
    if not isinstance(detection_id, str) or not detection_id:
        raise AssessmentError("foundation-drift-assessment-start-invalid")
    for _ in range(MAX_POLL_ATTEMPTS):
        status = run_aws(arguments, current_policy, ["cloudformation", "describe-stack-drift-detection-status", "--stack-drift-detection-id", detection_id, "--query", "{detection:DetectionStatus,stack:StackDriftStatus}"], "foundation-drift-assessment-status-unavailable")
        if not isinstance(status, dict):
            raise AssessmentError("foundation-drift-assessment-status-invalid")
        if status.get("detection") in {"DETECTION_FAILED", "DETECTION_CANCELLED"}:
            raise AssessmentError("foundation-drift-assessment-failed")
        if status.get("detection") != "DETECTION_COMPLETE":
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        if status.get("stack") == "IN_SYNC":
            return "in-sync", None
        if status.get("stack") != "DRIFTED":
            raise AssessmentError("foundation-drift-assessment-status-invalid")
        records = run_aws(
            arguments,
            current_policy,
            [
                "cloudformation", "describe-stack-resource-drifts", "--stack-name", current_policy["foundation_stack"],
                "--stack-resource-drift-status-filters", "MODIFIED",
                "--query", "StackResourceDrifts[].{logical:LogicalResourceId,type:ResourceType,status:StackResourceDriftStatus,differences:PropertyDifferences[].{path:PropertyPath,category:DifferenceType}}",
            ],
            "foundation-drift-classification-unavailable",
        )
        known = classify_known(records, signatures)
        if known is None:
            raise UnexpectedDrift(safe_structural_changes(records))
        check_effective_tls(arguments, current_policy, tls)
        return "known-remediation-required", known
    raise AssessmentError("foundation-drift-assessment-timeout")


def write_evidence(path: Path, current_policy: dict[str, str], classification: str, safe_changes: list[dict[str, str]] | None) -> None:
    document: dict[str, Any] = {
        "schema": EVIDENCE_SCHEMA,
        "target": "kanbien/staging",
        "issued_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "account_id": current_policy["account"],
        "region": current_policy["region"],
        "foundation_stack": current_policy["foundation_stack"],
        "classification": classification,
    }
    if safe_changes is not None:
        document["known_changes"] = safe_changes
        document["tls_enforcement"] = "required"
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def main() -> int:
    arguments = parse_arguments()
    checks: list[dict[str, str]] = []
    try:
        current_policy = policy(load_yaml(Path(arguments.target_profile)))
        signatures, tls = verify_contract(load_yaml(Path(ACTIVE_CONTRACT)), current_policy)
        checks.append({"id": "source-policy", "verdict": "passed"})
        classification = "source-only"
        safe_changes: list[dict[str, str]] | None = None
        if not arguments.validate:
            check_identity(arguments, current_policy)
            checks.append({"id": "aws-account", "verdict": "passed"})
            check_foundation(arguments, current_policy)
            checks.append({"id": "foundation-stack", "verdict": "passed"})
            classification, safe_changes = assess_and_classify(arguments, current_policy, signatures, tls)
            checks.append({"id": "foundation-active-drift-assessment", "verdict": "passed"})
            checks.append({"id": "foundation-drift-classification", "verdict": classification})
            write_evidence(Path(arguments.evidence_file), current_policy, classification, safe_changes)
        output: dict[str, Any] = {"schema": SAFE_SCHEMA, "target": "kanbien/staging", "verdict": "passed", "classification": classification, "checks": checks}
        if safe_changes is not None:
            output["known_changes"] = safe_changes
            output["tls_enforcement"] = "required"
        print(json.dumps(output, sort_keys=True))
        return 0
    except UnexpectedDrift as exception:
        checks.append({"id": str(exception), "verdict": "failed"})
        print(json.dumps({"schema": SAFE_SCHEMA, "target": "kanbien/staging", "verdict": "failed", "classification": "unexpected", "checks": checks, "unexpected_changes": exception.changes}, sort_keys=True))
        return 1
    except AssessmentError as exception:
        check = {"id": str(exception), "verdict": "failed"}
        if exception.failure_class is not None:
            check["failure_class"] = exception.failure_class
        checks.append(check)
        print(json.dumps({"schema": SAFE_SCHEMA, "target": "kanbien/staging", "verdict": "failed", "checks": checks}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
