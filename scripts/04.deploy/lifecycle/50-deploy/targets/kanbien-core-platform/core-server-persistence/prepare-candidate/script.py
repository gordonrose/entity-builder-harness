#!/usr/bin/env python3
"""Inspect only the fixed persistence candidate target before change-set creation."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION, ACCOUNT = "kanbien-dev", "eu-west-1", "337159794548"
FOUNDATION = "kanbien-core-platform-foundation"
STACK = "kanbien-core-platform-core-server-persistence"
REPOSITORY = "kanbien-core-platform/core-server"
EXPECTED = {
    "candidate": "kanbien-core-server-persistence-candidate",
    "package": "kanbien-core-server-persistence-image",
    "program": "kanbien-core-server-persistence",
}
REQUIRED_FOUNDATION = {
    "VpcId", "PrivateSubnetIds", "ClusterArn", "VerifierSecurityGroupId", "LogGroupName", "RepositoryUri", "ServiceDiscoveryArn",
}
INTERFACE_SERVICES = {
    f"com.amazonaws.{REGION}.ecr.dkr",
    f"com.amazonaws.{REGION}.ecr.api",
    f"com.amazonaws.{REGION}.logs",
}
AWS_CONNECT_TIMEOUT_SECONDS = 5
AWS_READ_TIMEOUT_SECONDS = 20
AWS_PROCESS_TIMEOUT_SECONDS = 30


def aws(*parts: str) -> tuple[bool, Any, str]:
    try:
        result = subprocess.run(
            [
                "aws", *parts,
                "--cli-connect-timeout", str(AWS_CONNECT_TIMEOUT_SECONDS),
                "--cli-read-timeout", str(AWS_READ_TIMEOUT_SECONDS),
                "--profile", PROFILE, "--region", REGION, "--output", "json",
            ],
            capture_output=True, text=True, timeout=AWS_PROCESS_TIMEOUT_SECONDS, env={**os.environ, "AWS_PAGER": ""},
        )
    except subprocess.TimeoutExpired:
        # A lost provider response is never permission to repeat an operation.
        # Callers must reconcile the named target state before another mutation.
        return False, None, "aws-command-timeout"
    if result.returncode:
        lowered = result.stderr.lower()
        if "accessdenied" in lowered or "not authorized" in lowered:
            return False, None, "aws-access-denied"
        # CloudFormation describes an absent named change set with the
        # service-specific ``ChangeSetNotFoundException`` token.  That is a
        # normal create-or-reconcile lifecycle state, not an opaque provider
        # failure; callers still reconcile the exact named change set before
        # creating it.  Keep this classification narrow so unrelated AWS
        # failures cannot be treated as safely absent resources.
        if "changesetnotfound" in lowered or "does not exist" in lowered or "not found" in lowered:
            return False, None, "aws-resource-missing"
        return False, None, "aws-command-failed"
    try:
        # AWS accepts several mutation requests with no response body. The
        # caller must reconcile the named provider operation, never retry an
        # acknowledged operation because an empty success body was misread.
        return True, {} if not result.stdout.strip() else json.loads(result.stdout), "ok"
    except json.JSONDecodeError:
        return False, None, "aws-response-invalid"


def report(verdict: str, codes: list[str], facts: dict[str, Any] | None = None) -> int:
    value: dict[str, Any] = {
        "schema": "deploy/persistence-candidate-preparation-report/v1",
        "target": "kanbien-core-platform",
        "scope": "core-server-persistence",
        "verdict": verdict,
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
    }
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "prepared" else 1


def validate_receipt(path: Path) -> dict[str, Any] | None:
    command = [
        "bash", str(ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"),
        "--receipt", str(path), "--expected-target", "kanbien-core-platform",
        "--expected-candidate", EXPECTED["candidate"], "--expected-package-contract", EXPECTED["package"],
        "--expected-program", EXPECTED["program"], "--json",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def declaration_covered() -> bool:
    """Offline coverage is compulsory before provider observation or mutation."""
    checker = ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py"
    contract = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
    try:
        checked = subprocess.run([sys.executable, "-B", str(checker), "--scope-contract", str(contract), "--root", str(ROOT), "--json"], capture_output=True, text=True, timeout=30)
        value = json.loads(checked.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return False
    return checked.returncode == 0 and isinstance(value, dict) and value.get("verdict") == "covered" and value.get("findings") == []


def foundation_outputs() -> tuple[dict[str, str] | None, str]:
    ok, data, code = aws("cloudformation", "describe-stacks", "--stack-name", FOUNDATION)
    stacks = data.get("Stacks") if ok and isinstance(data, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        return None, code if not ok else "foundation-outputs-unavailable"
    outputs = {
        item.get("OutputKey"): item.get("OutputValue")
        for item in stacks[0].get("Outputs", [])
        if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)
    }
    if not REQUIRED_FOUNDATION <= outputs.keys() or any(not outputs[name] for name in REQUIRED_FOUNDATION):
        return None, "foundation-outputs-unavailable"
    return outputs, "ok"


def infrastructure_parameters(outputs: dict[str, str]) -> tuple[dict[str, str] | None, str]:
    ok, vpcs, code = aws("ec2", "describe-vpcs", "--vpc-ids", outputs["VpcId"])
    items = vpcs.get("Vpcs") if ok and isinstance(vpcs, dict) else None
    cidr = items[0].get("CidrBlock") if isinstance(items, list) and len(items) == 1 and isinstance(items[0], dict) else None
    if not isinstance(cidr, str):
        return None, code if not ok else "persistence-vpc-cidr-unavailable"
    ok, service, code = aws("servicediscovery", "get-service", "--id", outputs.get("ServiceDiscoveryArn", "").rsplit("/", 1)[-1])
    namespace = service.get("Service", {}).get("DnsConfig", {}).get("NamespaceId") if ok and isinstance(service, dict) else None
    if not isinstance(namespace, str) or not namespace.startswith("ns-"):
        return None, code if not ok else "persistence-namespace-unavailable"
    ok, endpoints, code = aws("ec2", "describe-vpc-endpoints", "--filters", f"Name=vpc-id,Values={outputs['VpcId']}")
    endpoint_items = endpoints.get("VpcEndpoints") if ok and isinstance(endpoints, dict) else None
    selected = [
        endpoint for endpoint in endpoint_items or []
        if isinstance(endpoint, dict) and endpoint.get("ServiceName") in INTERFACE_SERVICES and endpoint.get("State") == "available"
    ]
    if len(selected) != 3 or {item.get("ServiceName") for item in selected} != INTERFACE_SERVICES:
        return None, "persistence-private-startup-endpoints-unavailable"
    if any(item.get("VpcId") != outputs["VpcId"] or item.get("VpcEndpointType") != "Interface" or item.get("PrivateDnsEnabled") is not True for item in selected):
        return None, "persistence-private-startup-endpoint-posture-invalid"
    if any(not isinstance(item.get("Groups"), list) or len(item["Groups"]) != 1 or not isinstance(item["Groups"][0], dict) for item in selected):
        return None, "persistence-endpoint-security-group-unavailable"
    group_sets = {(item["Groups"][0].get("GroupId"),) for item in selected}
    if len(group_sets) != 1 or len(next(iter(group_sets))) != 1 or not next(iter(group_sets))[0]:
        return None, "persistence-endpoint-security-group-unavailable"
    ok, prefix_lists, code = aws("ec2", "describe-managed-prefix-lists", "--filters", f"Name=prefix-list-name,Values=com.amazonaws.{REGION}.s3")
    lists = prefix_lists.get("PrefixLists") if ok and isinstance(prefix_lists, dict) else None
    prefix_ids = [item.get("PrefixListId") for item in lists or [] if isinstance(item, dict) and isinstance(item.get("PrefixListId"), str)]
    if len(prefix_ids) != 1:
        return None, code if not ok else "persistence-artifact-object-store-route-unavailable"
    return {
        "VpcId": outputs["VpcId"], "VpcCidr": cidr, "PrivateSubnetIds": outputs["PrivateSubnetIds"],
        "ClusterArn": outputs["ClusterArn"], "NamespaceId": namespace,
        "EndpointSecurityGroupId": next(iter(group_sets))[0], "VerifierSecurityGroupId": outputs["VerifierSecurityGroupId"],
        "S3ArtifactPrefixListId": prefix_ids[0], "LogGroupName": outputs["LogGroupName"],
    }, "ok"


def change_name_matches(value: object, expected: str) -> bool:
    return value == expected or (isinstance(value, str) and value.startswith("arn:aws:cloudformation:") and value.split(":changeSet/", 1)[-1].split("/", 1)[0] == expected)


def observe_update(name: str, expected_parameters: dict, review) -> tuple[str, str]:
    """Observe one named UPDATE; never create, execute, wait on, or replace it."""
    ok, change, code = aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok or not isinstance(change, dict):
        return "uncertain", code if not ok else "persistence-update-observation-invalid"
    if not change_name_matches(change.get("ChangeSetName"), name):
        return "blocked", "persistence-update-change-set-identity-invalid"
    if change.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}:
        return "pending", "persistence-update-review-pending"
    if change.get("Status") in {"FAILED", "DELETE_COMPLETE", "DELETE_FAILED"}:
        return "failed", "persistence-update-change-set-failed"
    if not review(change):
        return "blocked", "persistence-update-change-set-review-invalid"
    execution = change.get("ExecutionStatus")
    if execution in {"AVAILABLE", "EXECUTE_IN_PROGRESS"}:
        return "pending", "persistence-update-execution-pending"
    if execution != "EXECUTE_COMPLETE":
        return "uncertain", "persistence-update-execution-state-unknown"
    ok, observed, code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = observed.get("Stacks") if ok and isinstance(observed, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        return "uncertain", "persistence-update-stack-observation-uncertain"
    stack = stacks[0]
    status = stack.get("StackStatus")
    if status in {"UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS", "UPDATE_ROLLBACK_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"}:
        return "pending", "persistence-update-stack-pending"
    if status in {"UPDATE_FAILED", "UPDATE_ROLLBACK_FAILED", "UPDATE_ROLLBACK_COMPLETE", "DELETE_COMPLETE"}:
        return "failed", "persistence-update-stack-failed"
    params = {item.get("ParameterKey"): item.get("ParameterValue") for item in stack.get("Parameters", []) if isinstance(item, dict)}
    if status != "UPDATE_COMPLETE" or any(params.get(key) != value for key, value in expected_parameters.items()):
        return "uncertain", "persistence-update-completion-identity-unproven"
    return "complete", "persistence-update-operation-complete"


def candidate_parameters(outputs: dict, infrastructure: dict, receipt: dict) -> dict[str, str]:
    """One provider-owned mapping is shared by CREATE and its execution review."""
    # All executable programs in the template are part of one qualified image
    # release.  Keep these bindings together so either CREATE or UPDATE cannot
    # accidentally retain an obsolete support-program image while moving the
    # server or restoration verifier to the candidate digest.
    return {**infrastructure, "ImageRepositoryArn": f"arn:aws:ecr:{REGION}:{ACCOUNT}:repository/kanbien-core-platform/core-server", "ImageRepositoryUri": outputs["RepositoryUri"], "ImageDigest": receipt["image_digest"], "SupportImageDigest": receipt["image_digest"], "RestoreVerifierImageDigest": receipt["image_digest"], "SourceRevision": receipt["source_revision"]}


def candidate_runnable_manifest(receipt: dict[str, Any]) -> tuple[str | None, str]:
    digest = receipt.get("image_digest")
    if not isinstance(digest, str):
        return None, "package-custody-receipt-invalid"
    ok, image, code = aws("ecr", "batch-get-image", "--repository-name", REPOSITORY, "--image-ids", f"imageDigest={digest}", "--accepted-media-types", "application/vnd.oci.image.index.v1+json")
    images = image.get("images") if ok and isinstance(image, dict) else None
    if not isinstance(images, list) or len(images) != 1 or not isinstance(images[0], dict) or not isinstance(images[0].get("imageManifest"), str):
        return None, code if not ok else "persistence-candidate-image-index-unavailable"
    try:
        manifests = json.loads(images[0]["imageManifest"]).get("manifests", [])
    except (json.JSONDecodeError, AttributeError):
        return None, "persistence-candidate-image-index-invalid"
    if not isinstance(manifests, list):
        return None, "persistence-candidate-image-index-invalid"
    children = [
        item.get("digest") for item in manifests if isinstance(item, dict)
        and item.get("mediaType") == "application/vnd.oci.image.manifest.v1+json"
        and item.get("platform") == {"architecture": "amd64", "os": "linux"}
        and isinstance(item.get("digest"), str)
    ]
    if len(children) != 1:
        return None, "persistence-candidate-runnable-manifest-unavailable"
    return children[0], "ok"


def candidate_image(receipt: dict[str, Any]) -> tuple[bool, str]:
    digest, code = candidate_runnable_manifest(receipt)
    if digest is None:
        return False, code
    ok, scan, code = aws("ecr", "describe-image-scan-findings", "--repository-name", REPOSITORY, "--image-id", f"imageDigest={digest}", "--max-results", "1")
    status = scan.get("imageScanStatus", {}).get("status") if ok and isinstance(scan, dict) else None
    findings = scan.get("imageScanFindings", {}).get("findingSeverityCounts", {}) if ok and isinstance(scan, dict) else None
    if status != "COMPLETE" or not isinstance(findings, dict):
        return False, code if not ok else "persistence-candidate-image-scan-unavailable"
    if findings.get("CRITICAL", 0) or findings.get("HIGH", 0):
        return False, "persistence-candidate-image-scan-not-clean"
    return True, "ok"


def live_budget() -> tuple[bool, str]:
    ok, budget, code = aws("budgets", "describe-budget", "--account-id", ACCOUNT, "--budget-name", "kanbien-core-platform-monthly")
    value = budget.get("Budget") if ok and isinstance(budget, dict) else None
    limit = value.get("BudgetLimit", {}) if isinstance(value, dict) else {}
    filters = value.get("CostFilters", {}) if isinstance(value, dict) else {}
    target = filters.get("TagKeyValue") if isinstance(filters, dict) else None
    try:
        amount = Decimal(str(limit.get("Amount"))) if isinstance(limit, dict) else None
    except (InvalidOperation, ValueError):
        amount = None
    valid_amount = amount == Decimal("100") and isinstance(limit, dict) and limit.get("Unit") == "USD"
    valid_filter = isinstance(target, list) and target == ["user:Target$kanbien-core-platform"]
    return (True, "ok") if valid_amount and valid_filter else (False, code if not ok else "target-budget-live-configuration-invalid")


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None:
        return report("blocked", ["persistence-candidate-preparation-arguments-invalid"])
    receipt = validate_receipt(args.receipt)
    if receipt is None:
        return report("blocked", ["package-custody-receipt-invalid"])
    if not declaration_covered():
        return report("blocked", ["persistence-declaration-coverage-gap"])
    codes: list[str] = []
    outputs, code = foundation_outputs()
    if outputs is None:
        codes.append(code)
        return report("blocked", codes)
    params, code = infrastructure_parameters(outputs)
    if params is None:
        codes.append(code)
    image_ok, code = candidate_image(receipt)
    if not image_ok:
        codes.append(code)
    budget_ok, code = live_budget()
    if not budget_ok:
        codes.append(code)
    template = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
    ok, _, code = aws("cloudformation", "validate-template", "--template-body", f"file://{template}")
    if not ok:
        codes.append(code)
    if codes:
        return report("blocked", codes)
    return report("prepared", [], {
        "candidate_image_digest": receipt["image_digest"], "candidate_source_revision": receipt["source_revision"],
        "foundation": "available", "private_startup_connectivity": "available", "target_budget": "verified-live",
    })


if __name__ == "__main__":
    raise SystemExit(main())
