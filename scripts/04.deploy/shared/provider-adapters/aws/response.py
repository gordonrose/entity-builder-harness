#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.provider.aws.response-classification
#   version: 3
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Classify AWS CLI errors and validate bounded ECS task overrides without retaining raw responses.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.library.aws.cli-invocation
#     path: scripts/04.deploy/shared/provider-adapters/aws/cli.py
#   - id: deploy.library.kanbien-core-platform.persistence-ecs-task-evidence
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/ecs-task-evidence.py
#   - id: deploy.library.entity-smoke.task-control
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-control.py
#   - id: deploy.command.kanbien-core-platform.prepare-core-server-persistence-candidate
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py
"""AWS response semantics only; no credentials, requests, retries or persistence."""
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

# Absence has meaning only at an explicitly supported observation boundary.
MISSING = {
    ("cloudformation", "describe-change-set"): {"ChangeSetNotFound", "ChangeSetNotFoundException"},
    ("rds", "describe-db-instances"): {"DBInstanceNotFound", "DBInstanceNotFoundFault"},
    ("rds", "describe-db-snapshots"): {"DBSnapshotNotFound", "DBSnapshotNotFoundFault"},
    ("iam", "get-role-policy"): {"NoSuchEntity", "NoSuchEntityException"},
    ("iam", "get-role"): {"NoSuchEntity", "NoSuchEntityException"},
    ("ec2", "describe-security-groups"): {"InvalidGroup.NotFound"},
    ("budgets", "describe-budget"): {"NotFoundException"},
    ("logs", "filter-log-events"): {"ResourceNotFoundException"},
    ("logs", "get-log-events"): {"ResourceNotFoundException"},
}


def classify_error(service: str, operation: str, stderr: str) -> str:
    """Never let an unknown error containing 'not found' authorize creation."""
    # The CLI can add this decoration even when AWS_MAX_ATTEMPTS is one.
    match = re.search(r"An error occurred \(([A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)\) when calling the [A-Za-z0-9]+ operation(?: \(reached max retries: [0-9]+\))?:", stderr)
    code = match.group(1) if match else None
    if code in {"ExpiredToken", "ExpiredTokenException"}:
        return "aws-credentials-expired"
    if code in {"AccessDenied", "AccessDeniedException", "UnauthorizedOperation", "UnrecognizedClientException", "InvalidClientTokenId"}:
        return "aws-access-denied"
    if code in MISSING.get((service, operation), set()):
        return "aws-resource-missing"
    # CloudFormation uniquely uses ValidationError for a named absent stack.
    # Anchor the entire message; arbitrary validation failures remain failures.
    if service == "cloudformation" and operation == "describe-stacks" and code == "ValidationError" and match:
        reason = stderr[match.end():].strip()
        if re.fullmatch(r"Stack with id [^\s]+ does not exist", reason):
            return "aws-resource-missing"
    if code in {"ValidationError", "ValidationException", "InvalidParameterValue"} or stderr.startswith("Parameter validation failed:"):
        return "aws-parameter-invalid"
    return "aws-command-failed"


@lru_cache(maxsize=8)
def inventory_covered(root: Path) -> bool:
    """Cheap offline repository reconciliation precedes any supported AWS call."""
    try:
        result=subprocess.run([sys.executable,"-B",str(root/"scripts/04.deploy/inventory-deploy-control/script.py"),"--delivery","--check"],cwd=root,capture_output=True,text=True,timeout=30)
    except (OSError,subprocess.TimeoutExpired):
        return False
    return result.returncode==0


def task_overrides_match(task: object, container_name: str, expected_environment: dict[str, str]) -> bool:
    """An empty inference list is inert; commands, roles and resources stay exact.

    The optional empty inferenceAcceleratorOverrides list is present in captured
    ECS responses. Unknown keys and nonempty/default-looking consequential
    fields are deliberately rejected rather than silently discarded.
    """
    if not isinstance(task, dict):
        return False
    overrides = task.get("overrides")
    if not isinstance(overrides, dict) or set(overrides) - {"containerOverrides", "inferenceAcceleratorOverrides"}:
        return False
    if "inferenceAcceleratorOverrides" in overrides and overrides["inferenceAcceleratorOverrides"] != []:
        return False
    containers = overrides.get("containerOverrides")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        return False
    container = containers[0]
    if set(container) != {"name", "environment"} or container.get("name") != container_name:
        return False
    environment = container.get("environment")
    if not isinstance(environment, list) or len(environment) != len(expected_environment):
        return False
    if not all(isinstance(item, dict) and set(item) == {"name", "value"} and isinstance(item["name"], str) and isinstance(item["value"], str) for item in environment):
        return False
    return {item["name"]: item["value"] for item in environment} == expected_environment
