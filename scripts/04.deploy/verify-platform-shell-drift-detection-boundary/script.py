#!/usr/bin/env python3
"""Validate the Kanbien staging CloudFormation drift-detection identity boundary."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-drift-detection-boundary
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Fail source validation when a drift-detection dependency or GitHub identity boundary is ambiguous.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-drift-detection-boundary-check
#     path: package.json

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

try:
    import yaml
except ImportError as exception:
    raise SystemExit("ERROR: PyYAML is required. Install PyYAML==6.0.2 before this check.") from exception


ROOT = Path(__file__).resolve().parents[3]
MATRIX_PATH = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/resource-read-contract.yml"
PROFILE_PATH = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
POLICY_PATH = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json"
RECONCILIATION_PATH = ROOT / "scripts/04.deploy/reconcile-platform-shell-staging/script.py"


class CloudFormationLoader(yaml.SafeLoader):
    """Load CloudFormation source while retaining intrinsic values as inert maps."""


def intrinsic(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node) -> dict[str, Any]:
    """Construct an intrinsic without interpreting it during this static source check."""

    if isinstance(node, yaml.ScalarNode):
        value: Any = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
    else:
        value = loader.construct_mapping(node)
    return {f"!{tag_suffix}": value}


CloudFormationLoader.add_multi_constructor("!", intrinsic)


def load_yaml(path: Path, loader: type[yaml.SafeLoader] = yaml.SafeLoader) -> dict[str, Any]:
    """Read one reviewed YAML object and reject any other root shape."""

    try:
        with path.open(encoding="utf-8") as handle:
            value = yaml.load(handle, Loader=loader)
    except (OSError, yaml.YAMLError) as exception:
        raise ValueError(f"cannot read {path.relative_to(ROOT)}") from exception
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must be a YAML object")
    return value


def resource_types(path: Path) -> set[str]:
    """Return only CloudFormation resource types, never parameter type annotations."""

    document = load_yaml(path, CloudFormationLoader)
    resources = document.get("Resources", {})
    if not isinstance(resources, dict):
        raise ValueError(f"{path.relative_to(ROOT)} Resources must be an object")
    types: set[str] = set()
    for logical_id, definition in resources.items():
        if not isinstance(logical_id, str) or not isinstance(definition, dict):
            raise ValueError(f"{path.relative_to(ROOT)} contains an invalid resource")
        resource_type = definition.get("Type")
        if not isinstance(resource_type, str) or not resource_type.startswith("AWS::"):
            raise ValueError(f"{path.relative_to(ROOT)} resource {logical_id} has no AWS resource type")
        types.add(resource_type)
    return types


def policy_actions(policy: dict[str, Any]) -> set[str]:
    """Collect actions so a passive role cannot accidentally receive an active scan permission."""

    statements = policy.get("Statement")
    if not isinstance(statements, list):
        raise ValueError("reconciliation policy must contain a Statement list")
    actions: set[str] = set()
    for statement in statements:
        if not isinstance(statement, dict) or statement.get("Effect") != "Allow":
            raise ValueError("reconciliation policy must contain only reviewed Allow statements")
        declared = statement.get("Action")
        values = [declared] if isinstance(declared, str) else declared
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise ValueError("reconciliation policy actions must be strings")
        actions.update(values)
    return actions


def main() -> int:
    """Report every source boundary violation together, without making an AWS call."""

    failures: list[str] = []
    try:
        matrix = load_yaml(MATRIX_PATH)
        profile = load_yaml(PROFILE_PATH)
        with POLICY_PATH.open(encoding="utf-8") as handle:
            policy = json.load(handle)
    except (OSError, ValueError, json.JSONDecodeError) as exception:
        print(f"ERROR: {exception}", file=sys.stderr)
        return 1

    if matrix.get("schema") != "deploy/cloudformation-drift-resource-read-contract/v1":
        failures.append("drift resource-read contract schema is not reviewed")
    if matrix.get("target") != "kanbien/staging":
        failures.append("drift resource-read contract must apply only to kanbien/staging")
    if matrix.get("status") != "inventory-complete-provider-read-analysis-pending":
        failures.append("drift resource-read contract status is not the reviewed staged value")

    sources = matrix.get("template_sources")
    if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        failures.append("drift resource-read contract must enumerate template sources")
        sources = []
    source_paths = [ROOT / item for item in sources]
    if len(set(sources)) != len(sources):
        failures.append("drift resource-read contract must not duplicate template sources")
    for source in source_paths:
        if not source.is_file():
            failures.append(f"drift resource-read contract source is missing: {source.relative_to(ROOT)}")

    discovered: set[str] = set()
    for source in source_paths:
        if source.is_file():
            try:
                discovered.update(resource_types(source))
            except ValueError as exception:
                failures.append(str(exception))

    entries = matrix.get("resource_types")
    if not isinstance(entries, dict) or not all(isinstance(key, str) for key in entries):
        failures.append("drift resource-read contract must map resource types")
        entries = {}
    declared = set(entries)
    missing = sorted(discovered - declared)
    stale = sorted(declared - discovered)
    if missing:
        failures.append(f"unclassified drift resource types: {', '.join(missing)}")
    if stale:
        failures.append(f"stale drift resource types: {', '.join(stale)}")
    for resource_type, entry in entries.items():
        if not isinstance(entry, dict):
            failures.append(f"{resource_type} drift entry must be an object")
            continue
        if not isinstance(entry.get("service_owner"), str) or not entry["service_owner"]:
            failures.append(f"{resource_type} must name its AWS service owner")
        if entry.get("analysis_status") != "provider-read-analysis-required":
            failures.append(f"{resource_type} must remain blocked pending provider-read analysis")

    approval_rule = matrix.get("approval_rule")
    if not isinstance(approval_rule, dict) or approval_rule.get("detector_policy_may_be_created_only_when") != "every-resource-type-has-an-authoritative-provider-read-analysis":
        failures.append("drift resource-read contract must block detector-policy creation before analysis")
    elif approval_rule.get("current_safety_posture") != "no-detector-policy-no-detector-role-no-detector-workload":
        failures.append("drift resource-read contract must not claim an undeployed detector is live")

    reconciliation = profile.get("deployment", {}).get("reconciliation", {})
    expected_drift_evidence = {
        "strategy": "separate-target-scoped-detector",
        "github_role_may_start_detection": False,
        "github_role_evidence": "fresh-in-sync-stack-summary-only",
        "maximum_evidence_age_seconds": 21600,
        "resource_read_contract": "infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/resource-read-contract.yml",
        "detector_deployment_status": "source-planned-not-deployed",
        "operational_coverage": "blocked-pending-reviewed-detector-role-workload-cost-and-live-proof",
    }
    if not isinstance(reconciliation, dict) or reconciliation.get("drift_evidence") != expected_drift_evidence:
        failures.append("target profile must retain the reviewed separate drift-detection boundary")

    try:
        actions = policy_actions(policy)
    except ValueError as exception:
        failures.append(str(exception))
        actions = set()
    prohibited = {
        "cloudformation:DetectStackDrift",
        "cloudformation:DetectStackResourceDrift",
        "cloudformation:BatchDescribeTypeConfigurations",
        "cloudformation:*",
        "*",
    }
    unexpected = sorted(actions & prohibited)
    if unexpected:
        failures.append(f"GitHub reconciliation role must remain passive; prohibited actions: {', '.join(unexpected)}")
    if "cloudformation:DescribeStacks" not in actions:
        failures.append("GitHub reconciliation role must retain scoped stack-summary reads")

    source = RECONCILIATION_PATH.read_text(encoding="utf-8").lower()
    if "detect-stack-drift" in source or "detect-stack-resource-drift" in source:
        failures.append("reconciliation command must not start active CloudFormation drift detection")
    for required in ("lastchecktimestamp", "maximum_evidence_age_seconds", "evidence-stale"):
        if required not in source:
            failures.append(f"reconciliation command must retain passive drift evidence control: {required}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print("Platform-shell drift-detection boundary check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
