#!/usr/bin/env python3
"""Assess only the fixed Kanbien staging Service stack before its Stage 6 deployment."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.assess-platform-shell-service-drift
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Refresh a fixed administrator-only Service-stack drift verdict before the isolated PostgreSQL Stage 6 change set.
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


PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SCHEMA = "deploy/platform-shell-service-active-drift-evidence/v1"
MAX_POLLS = 36


class AssessmentError(Exception):
    """Represent a stable safe failure without retaining provider content."""


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assess the one reviewed Kanbien staging Service stack.")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--execute-approved-active-service-drift-assessment", action="store_true")
    parser.add_argument("--evidence-file")
    parser.add_argument("--target-profile", default=PROFILE)
    parser.add_argument("--aws-cli", default="aws")
    parser.add_argument("--json", action="store_true")
    value = parser.parse_args()
    if value.validate == value.execute_approved_active_service_drift_assessment:
        parser.error("choose exactly one of --validate or --execute-approved-active-service-drift-assessment")
    if value.validate and value.evidence_file:
        parser.error("--evidence-file is valid only for an active assessment")
    if not value.validate:
        if not value.evidence_file:
            parser.error("--evidence-file is required for an active assessment")
        path = Path(value.evidence_file)
        if not path.is_absolute() or path.parent != Path("/tmp") or path.exists():
            parser.error("--evidence-file must be a new direct child of /tmp")
    return value


def mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AssessmentError(code)
    return value


def text(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise AssessmentError(code)
    return value


def load_policy(path: Path) -> dict[str, str]:
    try:
        import yaml
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exception:
        raise AssessmentError("reviewed-source-unreadable") from exception
    root = mapping(document, "reviewed-source-invalid")
    cloud = mapping(root.get("cloud"), "cloud-policy-missing")
    deployment = mapping(root.get("deployment"), "deployment-policy-missing")
    cloudformation = mapping(deployment.get("cloudformation"), "cloudformation-policy-missing")
    reconciliation = mapping(deployment.get("reconciliation"), "reconciliation-policy-missing")
    drift = mapping(reconciliation.get("drift_evidence"), "drift-evidence-policy-missing")
    control = mapping(drift.get("service_active_assessment"), "service-active-assessment-policy-missing")
    expected = {
        "status": "approved-administrator-only-service-drift-assessment",
        "command": "npm run platform:shell:service-active-drift-assessment -- --execute-approved-active-service-drift-assessment --evidence-file /tmp/new-safe-evidence.json --json",
        "execution_identity": "target-profile-administrator-only-not-github",
        "scope": "service-stack-only-detect-and-status-poll-no-resource-detail-read-or-mutation",
        "allowed_operations": ["sts:GetCallerIdentity", "cloudformation:DescribeStacks", "cloudformation:DetectStackDrift", "cloudformation:DescribeStackDriftDetectionStatus"],
        "success_condition": "detection-complete-and-service-stack-in-sync",
        "output_policy": "safe-check-identifiers-and-verdicts-only-no-detection-id-provider-response-resource-detail-or-property-values",
        "maximum_evidence_age_seconds": 900,
    }
    if control != expected:
        raise AssessmentError("service-active-assessment-policy-not-reviewed")
    account = text(cloud.get("account_id"), "account-id-missing")
    region = text(cloud.get("region"), "region-missing")
    aws_profile = text(cloud.get("profile"), "aws-profile-missing")
    stack = text(cloudformation.get("service_stack"), "service-stack-missing")
    if (account, region, aws_profile, stack) != ("337159794548", "eu-west-1", "kanbien-dev", "kanbien-staging-platform-shell-service"):
        raise AssessmentError("target-policy-not-reviewed")
    return {"account": account, "region": region, "profile": aws_profile, "stack": stack}


def aws(value: argparse.Namespace, policy: dict[str, str], command: list[str], failure: str) -> Any:
    try:
        output = subprocess.run([value.aws_cli, *command, "--profile", policy["profile"], "--region", policy["region"], "--output", "json"], capture_output=True, check=True, text=True, timeout=20)
        return json.loads(output.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exception:
        raise AssessmentError(failure) from exception


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AssessmentError(code)


def execute(value: argparse.Namespace, policy: dict[str, str]) -> None:
    require(aws(value, policy, ["sts", "get-caller-identity", "--query", "Account"], "aws-account-verification-unavailable") == policy["account"], "aws-account-mismatch")
    require(aws(value, policy, ["cloudformation", "describe-stacks", "--stack-name", policy["stack"], "--query", "Stacks[0].StackStatus"], "service-stack-verification-unavailable") == "UPDATE_COMPLETE", "service-stack-not-ready")
    started = aws(value, policy, ["cloudformation", "detect-stack-drift", "--stack-name", policy["stack"]], "service-drift-assessment-start-unavailable")
    detection = started.get("StackDriftDetectionId") if isinstance(started, dict) else None
    if not isinstance(detection, str) or not detection:
        raise AssessmentError("service-drift-assessment-start-invalid")
    for _ in range(MAX_POLLS):
        status = aws(value, policy, ["cloudformation", "describe-stack-drift-detection-status", "--stack-drift-detection-id", detection, "--query", "{detection:DetectionStatus,stack:StackDriftStatus}"], "service-drift-assessment-status-unavailable")
        if not isinstance(status, dict) or status.get("detection") in {"DETECTION_FAILED", "DETECTION_CANCELLED"}:
            raise AssessmentError("service-drift-assessment-failed")
        if status.get("detection") != "DETECTION_COMPLETE":
            time.sleep(5)
            continue
        require(status.get("stack") == "IN_SYNC", "service-stack-drifted")
        Path(value.evidence_file).write_text(json.dumps({"schema": SCHEMA, "target": "kanbien/staging", "issued_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "account_id": policy["account"], "region": policy["region"], "service_stack": policy["stack"], "classification": "in-sync"}, sort_keys=True) + "\n", encoding="utf-8")
        Path(value.evidence_file).chmod(0o600)
        return
    raise AssessmentError("service-drift-assessment-timeout")


def main() -> int:
    value = arguments()
    checks: list[dict[str, str]] = []
    try:
        policy = load_policy(Path(value.target_profile))
        checks.append({"id": "source-policy", "verdict": "passed"})
        if not value.validate:
            execute(value, policy)
            checks.extend([{"id": "aws-account", "verdict": "passed"}, {"id": "service-stack", "verdict": "passed"}, {"id": "service-active-drift-assessment", "verdict": "passed"}])
        print(json.dumps({"schema": SCHEMA, "target": "kanbien/staging", "verdict": "passed", "checks": checks}, sort_keys=True))
        return 0
    except AssessmentError as exception:
        checks.append({"id": str(exception), "verdict": "blocked"})
        print(json.dumps({"schema": SCHEMA, "target": "kanbien/staging", "verdict": "blocked", "checks": checks}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
