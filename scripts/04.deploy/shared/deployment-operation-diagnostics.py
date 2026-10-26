#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.shared.deployment-operation-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.diagnostics
#   disciplines: [security, sre, agentic]
#   kind: script
#   purpose: Construct and validate safe retained deployment-operation reports and bounded CloudFormation failure classifications.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [writes-files]
#   used_by:
#   - id: deploy.shared.safe-command-diagnostics
#     path: scripts/04.deploy/shared/safe-command-diagnostics.sh
"""Build, validate, and safely classify retained deployment-operation diagnostics.

This module deliberately accepts provider response bodies only long enough to
classify a small allowlisted fact set. Callers must never print or persist the
raw response supplied to the classifier.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

SCHEMA = "deploy/deployment-operation-diagnostic/v1"
STAGES = {"target-alignment", "build", "package", "deploy", "run", "acceptance"}
OUTCOMES = {"rejected", "failed", "pending", "unknown"}
DECISIONS = {
    "observe-current-operation",
    "inspect-retained-evidence",
    "correct-and-create-new-operation",
    "stop-and-escalate",
    "retry-read-only-observation",
}
COLLECTION = {"collected", "unavailable", "failed"}
FACT_KEYS = {
    "artifact_identity", "change_set_id", "provider_status", "property_path",
    "resource_logical_id", "resource_type",
}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{1,95}$")
OPERATION = re.compile(r"^[a-z][a-z0-9-]{2,159}$")
CODE = re.compile(r"^(?:[a-z][a-z0-9-]{2,159}|[A-Z][A-Z0-9_]{2,159})$")
SAFE_FACT = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/=-]{0,191}$")
PROPERTY_PATH = re.compile(r"(?:Properties|Parameters)(?:\.[A-Za-z][A-Za-z0-9_]*)+")
EVIDENCE = re.compile(r"^(?:github-actions-artifact|github-actions-run|receipt-path|provider-operation):[A-Za-z0-9._:/=-]{1,240}$")
UNSAFE = re.compile(
    r"(?:https?://|arn:aws:|\b\d{12}\b|\b(?:password|secret|token|credential|authorization)\b|bearer\s|@)",
    re.IGNORECASE,
)


class DiagnosticFailure(Exception):
    def __init__(self, *codes: str):
        self.codes = tuple(dict.fromkeys(codes))
        super().__init__(", ".join(self.codes))


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_identifier(value: object, *, field: str, pattern: re.Pattern[str] = IDENTIFIER) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value) or UNSAFE.search(value):
        raise DiagnosticFailure(f"{field}-invalid")
    return value


def _safe_evidence(value: object) -> str:
    if not isinstance(value, str) or not EVIDENCE.fullmatch(value) or UNSAFE.search(value):
        raise DiagnosticFailure("evidence-reference-invalid")
    return value


def _timestamp(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise DiagnosticFailure(f"{field}-invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise DiagnosticFailure(f"{field}-invalid") from error
    if parsed.tzinfo is None:
        raise DiagnosticFailure(f"{field}-invalid")
    return value


def _facts(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict) or set(value).difference(FACT_KEYS):
        raise DiagnosticFailure("facts-invalid")
    facts: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(item, str) or not SAFE_FACT.fullmatch(item) or UNSAFE.search(item):
            raise DiagnosticFailure("facts-invalid")
        if key == "property_path" and not PROPERTY_PATH.fullmatch(item):
            raise DiagnosticFailure("facts-invalid")
        facts[key] = item
    return facts


def validate(report: object) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise DiagnosticFailure("report-invalid")
    required = {
        "schema", "target", "scope", "operation_id", "stage", "observed_at",
        "original_failure", "operation_outcome", "classification", "evidence",
        "next_action", "collection",
    }
    allowed = required | {"facts"}
    if set(report) != required and set(report) != allowed:
        raise DiagnosticFailure("report-fields-invalid")
    if report.get("schema") != SCHEMA:
        raise DiagnosticFailure("report-schema-invalid")
    _safe_identifier(report.get("target"), field="target")
    _safe_identifier(report.get("scope"), field="scope")
    _safe_identifier(report.get("operation_id"), field="operation-id", pattern=OPERATION)
    if report.get("stage") not in STAGES:
        raise DiagnosticFailure("stage-invalid")
    _timestamp(report.get("observed_at"), "observed-at")

    original = report.get("original_failure")
    if not isinstance(original, dict) or set(original) != {"code", "exit_status"}:
        raise DiagnosticFailure("original-failure-invalid")
    _safe_identifier(original.get("code"), field="original-failure-code", pattern=CODE)
    if not isinstance(original.get("exit_status"), int) or isinstance(original.get("exit_status"), bool) or original["exit_status"] < 1 or original["exit_status"] > 255:
        raise DiagnosticFailure("original-failure-exit-status-invalid")

    outcome = report.get("operation_outcome")
    if outcome not in OUTCOMES:
        raise DiagnosticFailure("operation-outcome-invalid")
    classification = report.get("classification")
    if not isinstance(classification, dict) or set(classification) != {"code"}:
        raise DiagnosticFailure("classification-invalid")
    _safe_identifier(classification.get("code"), field="classification-code", pattern=CODE)

    evidence = report.get("evidence")
    if not isinstance(evidence, dict) or set(evidence) != {"reference"}:
        raise DiagnosticFailure("evidence-invalid")
    _safe_evidence(evidence.get("reference"))

    action = report.get("next_action")
    if not isinstance(action, dict) or set(action) != {"decision"} or action.get("decision") not in DECISIONS:
        raise DiagnosticFailure("next-action-invalid")
    if outcome == "unknown" and action["decision"] not in {"observe-current-operation", "inspect-retained-evidence", "stop-and-escalate"}:
        raise DiagnosticFailure("unknown-outcome-retry-invalid")

    collection = report.get("collection")
    if not isinstance(collection, dict) or set(collection) != {"status"} or collection.get("status") not in COLLECTION:
        raise DiagnosticFailure("collection-invalid")
    _facts(report.get("facts"))
    return report


def build_report(
    *, target: str, scope: str, operation_id: str, stage: str,
    original_code: str, exit_status: int, outcome: str, classification: str,
    evidence_reference: str, next_decision: str, collection_status: str = "collected",
    facts: dict[str, str] | None = None, observed_at: str | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "target": target,
        "scope": scope,
        "operation_id": operation_id,
        "stage": stage,
        "observed_at": observed_at or now(),
        "original_failure": {"code": original_code, "exit_status": exit_status},
        "operation_outcome": outcome,
        "classification": {"code": classification},
        "evidence": {"reference": evidence_reference},
        "next_action": {"decision": next_decision},
        "collection": {"status": collection_status},
    }
    if facts:
        report["facts"] = facts
    return validate(report)


def write_report(path: Path, report: dict[str, Any]) -> None:
    """Atomically write a validated report. Caller selects a governed retained path."""
    validate(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(report, handle, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def classify_aws_error(code: object) -> str:
    """Map an existing safe provider adapter code to a safe generic category."""
    if code == "aws-access-denied":
        return "provider-access-denied"
    if code == "aws-resource-missing":
        return "provider-resource-missing"
    if code == "aws-command-timeout":
        return "provider-observation-timeout"
    return "provider-details-unavailable"


def _reason_classification(reason: object) -> str:
    text = reason.lower() if isinstance(reason, str) else ""
    if "accessdenied" in text or "not authorized" in text or "access denied" in text:
        return "provider-access-denied"
    if "does not exist" in text or "not found" in text or "notfound" in text:
        return "provider-resource-missing"
    if "property" in text and ("validation" in text or "invalid" in text):
        return "provider-property-rejection"
    if "validationerror" in text or "validation error" in text:
        return "provider-property-rejection"
    return "provider-details-unavailable"


def _event_facts(event: object) -> dict[str, str]:
    if not isinstance(event, dict):
        return {}
    facts: dict[str, str] = {}
    mapping = {
        "LogicalResourceId": "resource_logical_id",
        "ResourceType": "resource_type",
        "ResourceStatus": "provider_status",
    }
    for source, target in mapping.items():
        value = event.get(source)
        if isinstance(value, str) and SAFE_FACT.fullmatch(value) and not UNSAFE.search(value):
            facts[target] = value
    reason = event.get("ResourceStatusReason")
    if isinstance(reason, str):
        match = PROPERTY_PATH.search(reason)
        if match:
            facts["property_path"] = match.group(0)
    return facts


def classify_cloudformation_failure(change_set: object, events: object) -> tuple[str, dict[str, str], str]:
    """Classify a named change set and bounded stack events without retaining raw text."""
    change = change_set if isinstance(change_set, dict) else {}
    classification = _reason_classification(change.get("StatusReason"))
    facts: dict[str, str] = {}
    status = change.get("Status")
    if isinstance(status, str) and SAFE_FACT.fullmatch(status):
        facts["provider_status"] = status
    if isinstance(events, list):
        for event in events[:50]:
            if not isinstance(event, dict):
                continue
            event_classification = _reason_classification(event.get("ResourceStatusReason"))
            if event_classification != "provider-details-unavailable":
                classification = event_classification
                facts.update(_event_facts(event))
                break
            resource_status = event.get("ResourceStatus")
            if classification == "provider-details-unavailable" and isinstance(resource_status, str) and resource_status.endswith("FAILED"):
                facts.update(_event_facts(event))
    outcome = "rejected" if change.get("Status") == "FAILED" else "pending" if change.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"} else "unknown"
    return classification, facts, outcome


def collect_cloudformation_failure(
    provider: Callable[..., tuple[bool, object | None, str]], *, stack_name: str,
    change_set_name: str,
) -> tuple[str, dict[str, str], str, str]:
    """Make only safe, read-only observations for a named failed change set.

    The provider function is the controller's existing governed AWS adapter.
    A failed collection returns an unknown outcome and preserves the original
    provider code as a *safe* classification, never raw stderr.
    """
    ok, change, code = provider(
        "cloudformation", "describe-change-set", "--stack-name", stack_name,
        "--change-set-name", change_set_name,
    )
    if not ok:
        return classify_aws_error(code), {}, "unknown", "failed"
    events_ok, event_response, _ = provider(
        "cloudformation", "describe-stack-events", "--stack-name", stack_name,
    )
    events = event_response.get("StackEvents") if events_ok and isinstance(event_response, dict) else []
    classification, facts, outcome = classify_cloudformation_failure(change, events)
    return classification, facts, outcome, "collected" if events_ok else "unavailable"


def _cli() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="command", required=True)
    validate_parser = sub.add_parser("validate", add_help=False)
    validate_parser.add_argument("--report", required=True, type=Path)
    record = sub.add_parser("record", add_help=False)
    record.add_argument("--target", required=True)
    record.add_argument("--scope", required=True)
    record.add_argument("--operation-id", required=True)
    record.add_argument("--stage", required=True)
    record.add_argument("--original-code", required=True)
    record.add_argument("--exit-status", required=True, type=int)
    record.add_argument("--outcome", required=True)
    record.add_argument("--classification", required=True)
    record.add_argument("--evidence-reference", required=True)
    record.add_argument("--next-decision", required=True)
    record.add_argument("--collection-status", default="collected")
    record.add_argument("--fact", action="append", default=[])
    record.add_argument("--report", required=True, type=Path)
    args, unknown = parser.parse_known_args()
    if unknown:
        raise DiagnosticFailure("arguments-invalid")
    if args.command == "validate":
        try:
            validate(json.loads(args.report.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as error:
            raise DiagnosticFailure("report-unreadable") from error
        print(json.dumps({"schema": "deploy/deployment-operation-diagnostic-validation/v1", "verdict": "passed", "report": str(args.report)}, sort_keys=True))
        return 0
    facts: dict[str, str] = {}
    for pair in args.fact:
        key, separator, value = pair.partition("=")
        if not separator or key in facts:
            raise DiagnosticFailure("facts-invalid")
        facts[key] = value
    report = build_report(
        target=args.target, scope=args.scope, operation_id=args.operation_id,
        stage=args.stage, original_code=args.original_code, exit_status=args.exit_status,
        outcome=args.outcome, classification=args.classification,
        evidence_reference=args.evidence_reference, next_decision=args.next_decision,
        collection_status=args.collection_status, facts=facts or None,
    )
    write_report(args.report, report)
    print(json.dumps({"schema": "deploy/deployment-operation-diagnostic-validation/v1", "verdict": "recorded", "operation_id": args.operation_id}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_cli())
    except DiagnosticFailure as error:
        print(json.dumps({"schema": "deploy/deployment-operation-diagnostic-validation/v1", "verdict": "failed", "findings": [{"code": code} for code in error.codes]}, sort_keys=True))
        raise SystemExit(1)
