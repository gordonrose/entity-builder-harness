#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.provider.aws.response-classification
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Classify AWS CLI errors by operation-specific service codes without retaining raw responses.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
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
    ("budgets", "describe-budget"): {"NotFoundException"},
    ("logs", "filter-log-events"): {"ResourceNotFoundException"},
    ("logs", "get-log-events"): {"ResourceNotFoundException"},
}


def classify_error(service: str, operation: str, stderr: str) -> str:
    """Never let an unknown error containing 'not found' authorize creation."""
    match = re.search(r"An error occurred \(([A-Za-z0-9]+)\) when calling the [A-Za-z0-9]+ operation:", stderr)
    code = match.group(1) if match else None
    if code in {"AccessDenied", "AccessDeniedException", "UnauthorizedOperation", "UnrecognizedClientException", "InvalidClientTokenId", "ExpiredToken", "ExpiredTokenException"}:
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
