#!/usr/bin/env python3
"""Inspect only the fixed persistence candidate target before change-set creation."""
from __future__ import annotations

import argparse
import json
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


def aws(*parts: str) -> tuple[bool, Any, str]:
    result = subprocess.run(
        ["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"],
        capture_output=True, text=True,
    )
    if result.returncode:
        lowered = result.stderr.lower()
        if "accessdenied" in lowered or "not authorized" in lowered:
            return False, None, "aws-access-denied"
        if "does not exist" in lowered or "not found" in lowered:
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
    group_sets = {tuple(item.get("Groups", [{}])[0].get("GroupId") for _ in [0]) for item in selected if isinstance(item.get("Groups"), list) and len(item["Groups"]) == 1 and isinstance(item["Groups"][0], dict)}
    if len(group_sets) != 1 or len(next(iter(group_sets))) != 1 or not next(iter(group_sets))[0]:
        return None, "persistence-endpoint-security-group-unavailable"
    return {
        "VpcId": outputs["VpcId"], "VpcCidr": cidr, "PrivateSubnetIds": outputs["PrivateSubnetIds"],
        "ClusterArn": outputs["ClusterArn"], "NamespaceId": namespace,
        "EndpointSecurityGroupId": next(iter(group_sets))[0], "VerifierSecurityGroupId": outputs["VerifierSecurityGroupId"],
        "LogGroupName": outputs["LogGroupName"],
    }, "ok"


def candidate_image(receipt: dict[str, Any]) -> tuple[bool, str]:
    digest = receipt.get("image_digest")
    if not isinstance(digest, str):
        return False, "package-custody-receipt-invalid"
    ok, image, code = aws("ecr", "batch-get-image", "--repository-name", REPOSITORY, "--image-ids", f"imageDigest={digest}", "--accepted-media-types", "application/vnd.oci.image.index.v1+json")
    images = image.get("images") if ok and isinstance(image, dict) else None
    if not isinstance(images, list) or len(images) != 1 or not isinstance(images[0], dict) or not isinstance(images[0].get("imageManifest"), str):
        return False, code if not ok else "persistence-candidate-image-index-unavailable"
    try:
        manifests = json.loads(images[0]["imageManifest"]).get("manifests", [])
    except (json.JSONDecodeError, AttributeError):
        return False, "persistence-candidate-image-index-invalid"
    if not isinstance(manifests, list):
        return False, "persistence-candidate-image-index-invalid"
    children = [
        item.get("digest") for item in manifests if isinstance(item, dict)
        and item.get("mediaType") == "application/vnd.oci.image.manifest.v1+json"
        and item.get("platform") == {"architecture": "amd64", "os": "linux"}
        and isinstance(item.get("digest"), str)
    ]
    if len(children) != 1:
        return False, "persistence-candidate-runnable-manifest-unavailable"
    ok, scan, code = aws("ecr", "describe-image-scan-findings", "--repository-name", REPOSITORY, "--image-id", f"imageDigest={children[0]}", "--max-results", "1")
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
