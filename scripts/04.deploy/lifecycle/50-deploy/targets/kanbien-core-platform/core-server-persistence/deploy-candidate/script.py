#!/usr/bin/env python3
"""Execute only the exact reviewed persistence CREATE change set."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
ALLOWED_TYPES = {
    "AWS::EC2::SecurityGroup", "AWS::EC2::SecurityGroupIngress", "AWS::EC2::SecurityGroupEgress", "AWS::EC2::VPCEndpoint",
    "AWS::RDS::DBSubnetGroup", "AWS::RDS::DBInstance", "AWS::SecretsManager::Secret", "AWS::ServiceDiscovery::Service",
    "AWS::IAM::Role", "AWS::ECS::TaskDefinition", "AWS::ECS::Service",
}


def controls():
    path = ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"
    spec = importlib.util.spec_from_file_location("persistence_prepare", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value = {"schema": "deploy/persistence-deployment-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "stack": STACK, "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "deployed-awaiting-migration" else 1


def reviewable(change: object, stack_status: object, expected: str, digest: str, revision: str) -> bool:
    if not isinstance(change, dict) or stack_status not in {None, "REVIEW_IN_PROGRESS"}:
        return False
    if expected not in str(change.get("ChangeSetName", "")) or change.get("Status") != "CREATE_COMPLETE":
        return False
    if change.get("ChangeSetType") not in {None, "CREATE"}:
        return False
    parameters = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    if parameters.get("ImageDigest") != digest or parameters.get("SourceRevision") != revision:
        return False
    types = {item.get("ResourceChange", {}).get("ResourceType") for item in change.get("Changes", []) if isinstance(item, dict)}
    return bool(types) and types <= ALLOWED_TYPES


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--approved-change-set")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None or not isinstance(args.approved_change_set, str):
        return report("blocked", "persistence-deployment-arguments-invalid")
    module = controls()
    receipt = module.validate_receipt(args.receipt)
    if receipt is None:
        return report("blocked", "package-custody-receipt-invalid")
    expected = f"kanbien-core-platform-persistence-create-{receipt['image_digest'][7:19]}"
    if args.approved_change_set != expected:
        return report("blocked", "approved-change-set-does-not-match-qualified-digest")
    # Re-inspect the live prerequisites immediately before the only stack mutation.
    outputs, code = module.foundation_outputs()
    if outputs is None:
        return report("blocked", code)
    if module.infrastructure_parameters(outputs)[0] is None:
        return report("blocked", "persistence-private-startup-connectivity-not-proven")
    if not module.candidate_image(receipt)[0] or not module.live_budget()[0]:
        return report("blocked", "persistence-candidate-preconditions-not-proven")
    ok, change, code = module.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", expected)
    if not ok:
        return report("blocked", code)
    ok, stack, code = module.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stack_status = stack.get("Stacks", [{}])[0].get("StackStatus") if ok and isinstance(stack, dict) else None
    if not ok and code != "aws-resource-missing":
        return report("blocked", code)
    if not reviewable(change, stack_status, expected, receipt["image_digest"], receipt["source_revision"]):
        return report("blocked", "persistence-change-set-not-reviewable")
    ok, _, code = module.aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", expected)
    if not ok:
        return report("blocked", code)
    waited = subprocess.run(["aws", "cloudformation", "wait", "stack-create-complete", "--stack-name", STACK, "--profile", module.PROFILE, "--region", module.REGION], capture_output=True, text=True)
    if waited.returncode:
        return report("blocked", "persistence-stack-not-create-complete")
    return report("deployed-awaiting-migration", "persistence-create-change-set-executed", facts={"candidate_image_digest": receipt["image_digest"], "candidate_source_revision": receipt["source_revision"]})


if __name__ == "__main__":
    raise SystemExit(main())
