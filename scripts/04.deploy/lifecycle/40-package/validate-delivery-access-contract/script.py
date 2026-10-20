#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-delivery-access-contract
#   version: 2
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.delivery-access
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Fail closed when a declared delivery pipeline's provider actions, policy-coverage evidence, and workflow steps do not agree.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
REQUIRED_OPERATION_FIELDS = {"id", "workflow_step", "provider_action", "resource_class", "purpose", "proof"}
REQUIRED_COVERAGE_FIELDS = {"schema", "contract", "provider_policy_source", "granted_actions", "verdict"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a delivery access contract using normalized provider-policy coverage.")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--provider-policy-coverage", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def load_mapping(path: Path, error: str) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(error)
    return value


def repository_path(path: Path) -> str | None:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return None


def main() -> int:
    args = parse_args()
    codes: list[str] = []
    try:
        contract = load_mapping(args.contract, "contract-unreadable")
    except (OSError, yaml.YAMLError, ValueError):
        contract = {}
        codes.append("delivery-access-contract-unreadable")

    operations = contract.get("operations") if isinstance(contract, dict) else None
    required_actions: set[str] = set()
    workflow_steps: set[str] = set()
    if (
        contract.get("schema") != "deploy/delivery-access-contract/v1"
        or not isinstance(contract.get("pipeline"), str)
        or not contract.get("pipeline")
        or not isinstance(contract.get("actor"), str)
        or not contract.get("actor")
        or not isinstance(contract.get("provider_policy_source"), str)
        or not contract.get("provider_policy_source")
        or not isinstance(contract.get("workflow"), str)
        or not contract.get("workflow")
        or not isinstance(operations, list)
        or not operations
    ):
        codes.append("delivery-access-contract-invalid")
        operations = []

    for operation in operations:
        if not isinstance(operation, dict) or not REQUIRED_OPERATION_FIELDS.issubset(operation):
            codes.append("delivery-access-operation-invalid")
            continue
        action = operation["provider_action"]
        step = operation["workflow_step"]
        if not isinstance(action, str) or not action or any(character.isspace() for character in action):
            codes.append("delivery-access-action-invalid")
        else:
            required_actions.add(action)
        if not isinstance(step, str) or not step:
            codes.append("delivery-access-workflow-step-invalid")
        else:
            workflow_steps.add(step)

    try:
        coverage = load_mapping(args.provider_policy_coverage, "provider-policy-coverage-unreadable")
        if not REQUIRED_COVERAGE_FIELDS.issubset(coverage) or coverage.get("schema") != "deploy/provider-policy-coverage/v1":
            codes.append("provider-policy-coverage-invalid")
            granted_actions: set[str] = set()
        elif coverage.get("contract") != repository_path(args.contract):
            codes.append("provider-policy-coverage-contract-mismatch")
            granted_actions = set()
        elif coverage.get("provider_policy_source") != contract.get("provider_policy_source"):
            codes.append("provider-policy-coverage-source-mismatch")
            granted_actions = set()
        elif coverage.get("verdict") != "covered":
            codes.append("provider-policy-coverage-failed")
            granted_actions = set()
        elif not isinstance(coverage.get("granted_actions"), list) or not all(isinstance(action, str) and action for action in coverage["granted_actions"]):
            codes.append("provider-policy-coverage-invalid")
            granted_actions = set()
        else:
            granted_actions = set(coverage["granted_actions"])
            if required_actions - granted_actions:
                codes.append("delivery-action-provider-policy-missing")
            if granted_actions - required_actions:
                codes.append("delivery-role-action-unjustified")
    except (OSError, yaml.YAMLError, ValueError):
        codes.append("provider-policy-coverage-unreadable")

    try:
        workflow_text = args.workflow.read_text(encoding="utf-8")
        declared_steps = {
            line.strip()[len("- name: "):]
            for line in workflow_text.splitlines()
            if line.strip().startswith("- name: ")
        }
        if contract.get("workflow") != repository_path(args.workflow):
            codes.append("delivery-access-workflow-source-mismatch")
        if not workflow_steps.issubset(declared_steps):
            codes.append("delivery-access-workflow-step-missing")
    except OSError:
        codes.append("delivery-workflow-unreadable")

    deduplicated = list(dict.fromkeys(codes))
    report = {
        "schema": "deploy/delivery-access-coverage/v1",
        "pipeline": contract.get("pipeline") if isinstance(contract.get("pipeline"), str) else None,
        "verdict": "passed" if not deduplicated else "failed",
        "findings": [{"code": code} for code in deduplicated],
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not deduplicated else 1


if __name__ == "__main__":
    sys.exit(main())
