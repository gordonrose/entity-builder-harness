#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.shared.deployment-operation-diagnostics
#   version: 2
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-31"
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
import importlib.util
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
COLLECTION_OBSERVATIONS = {"complete", "empty", "unrecognized", "malformed", "incomplete", "unavailable", "failed"}
def runtime_contract():
    path = Path(__file__).resolve().parents[2] / "repo/diagnostic-coverage/runtime_contract.py"
    spec = importlib.util.spec_from_file_location("diagnostic_runtime_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("diagnostic-contract-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

EXECUTION_PHASES = runtime_contract().persistence_vocabulary("phase")
CODE_STATUSES = runtime_contract().persistence_vocabulary("codeStatus")
FAILURE_CLASSIFICATIONS = runtime_contract().persistence_vocabulary("classification")


def validate_runtime_diagnostic(value: object, operation: str | None = None, *, allow_core_source: bool = False) -> dict[str, Any]:
    """Read the executable contract export; never maintain a second vocabulary."""
    try:
        contract = runtime_contract()
        return contract.validate_operation_record(value, operation, allow_core_source=allow_core_source) if operation else contract.validate_configuration_record(value)
    except Exception as error:
        raise DiagnosticFailure("diagnostic-record-invalid") from error

def validate_related_diagnostics(value: object, primary: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return runtime_contract().validate_related_records(value, primary)
    except Exception as error:
        raise DiagnosticFailure("diagnostic-related-invalid") from error


def validate_persistence_task_failure(value: object, expected_task: str) -> dict[str, Any]:
    """Private task evidence has its own explicit source and observation ports.

    Historical configuration/native/verifier readers are deliberately unchanged.
    Every complete source bundle retains its own primary and eight companions.
    """
    try:
        contract = runtime_contract()
        limits = contract.persistence_task_failure_contract()
        required = {"schema", "task", "verdict", "code", "observations"}
        optional = {"diagnostic", "related_diagnostics", "source_bundles", "overflow"}
        if (type(value) is not dict or not required <= set(value) or set(value) - required - optional
                or type(expected_task) is not str or expected_task not in limits["codes"]
                or value["schema"] != limits["schema"] or value["task"] != expected_task
                or value["verdict"] != "rejected" or type(value["code"]) is not str
                or value["code"] not in limits["codes"][expected_task]
                or type(value["observations"]) is not list or len(value["observations"]) > limits["maxObservations"]):
            raise ValueError()
        result = {key: value[key] for key in ("schema", "task", "verdict", "code")}
        result["observations"] = [contract.validate_persistence_task_observation(item, expected_task) for item in value["observations"]]

        def source_bundle(bundle: object) -> dict[str, Any]:
            if type(bundle) is not dict or "diagnostic" not in bundle or set(bundle) - {"diagnostic", "related_diagnostics"}:
                raise ValueError()
            checked = {"diagnostic": contract.validate_persistence_task_source(bundle["diagnostic"], expected_task)}
            if "related_diagnostics" in bundle:
                checked["related_diagnostics"] = contract.validate_related_records(bundle["related_diagnostics"], checked["diagnostic"])
            return checked

        root_source = {key: value[key] for key in ("diagnostic", "related_diagnostics") if key in value}
        selected = []
        if root_source:
            root_source = source_bundle(root_source)
            result.update(root_source)
            selected.append(root_source)
        if "source_bundles" in value:
            bundles = value["source_bundles"]
            if type(bundles) is not list or len(bundles) > limits["maxSourceBundles"] or bundles and not root_source:
                raise ValueError()
            result["source_bundles"] = []
            for raw in bundles:
                checked = source_bundle(raw)
                if checked in selected:
                    raise ValueError()
                selected.append(checked)
                result["source_bundles"].append(checked)
        if "overflow" in value:
            overflow = value["overflow"]
            if (type(overflow) is not dict or set(overflow) != {"observations", "source_bundles"}
                    or any(type(item) is not int or not 0 <= item <= limits["maxOverflowCount"] for item in overflow.values())
                    or not any(overflow.values())):
                raise ValueError()
            result["overflow"] = dict(overflow)
        return result
    except Exception as error:
        raise DiagnosticFailure("persistence-task-failure-invalid") from error


def collect_persistence_task_failure(response: object, expected_task: str) -> tuple[dict[str, Any] | None, str]:
    """Reduce one bounded observation of the already identified task stream.

    A malformed/unrelated message is not authority to discard selected evidence
    or accept the failed task. No pagination, retry, or provider call lives here.
    """
    events = response.get("events") if type(response) is dict else None
    if type(events) is not list:
        return None, "malformed"
    state = "incomplete" if len(events) >= 100 else "complete" if events else "empty"
    limits = runtime_contract().persistence_task_failure_contract()
    selected = None
    for event in events[:100]:
        try:
            if type(event) is not dict or type(event.get("message")) is not str:
                raise ValueError()
            value = json.loads(event["message"])
            if type(value) is not dict or value.get("schema") != limits["schema"]:
                continue
            checked = validate_persistence_task_failure(value, expected_task)
        except Exception:
            if state != "incomplete":
                state = "malformed"
            continue
        if selected is None:
            selected = checked
            continue
        candidate = {**selected, "observations": list(selected["observations"])}
        bundles = [{key: selected[key] for key in ("diagnostic", "related_diagnostics") if key in selected}]
        bundles = [item for item in bundles if item] + list(selected.get("source_bundles", []))
        counts = dict(selected.get("overflow", {"observations": 0, "source_bundles": 0}))
        try:
            def omitted(kind: str, count: int) -> None:
                if counts[kind] + count > limits["maxOverflowCount"]:
                    raise OverflowError()
                counts[kind] += count

            for kind, count in checked.get("overflow", {}).items():
                omitted(kind, count)
            for record in checked["observations"]:
                if len(candidate["observations"]) < limits["maxObservations"]:
                    candidate["observations"].append(record)
                else:
                    omitted("observations", 1)
            incoming = [{key: checked[key] for key in ("diagnostic", "related_diagnostics") if key in checked}]
            for bundle in [item for item in incoming if item] + checked.get("source_bundles", []):
                if bundle in bundles:
                    continue
                if len(bundles) < 1 + limits["maxSourceBundles"]:
                    bundles.append(bundle)
                else:
                    omitted("source_bundles", 1)
            if bundles:
                candidate.update(bundles[0])
                if len(bundles) > 1 or "source_bundles" in candidate:
                    candidate["source_bundles"] = bundles[1:]
            if any(counts.values()):
                candidate["overflow"] = counts
            selected = candidate
        except OverflowError:
            # Earlier valid facts remain truthful; no wrapped/saturated count
            # or newly guessed evidence is substituted for this failed merge.
            state = "incomplete"
    return selected, state


def validate_persistence_controller_checkpoint(value: object, command: str) -> dict[str, Any] | None:
    """Select independent facts from the four actual bounded caller ports.

    This is not a generic report reader. A bad identity never erases unrelated
    valid source evidence, and a bad source never blesses or erases an identity.
    """
    prefix = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/"
    ports = {
        prefix + "run-administration/script.sh": ("deploy/persistence-administration-report/v1", "administration"),
        prefix + "verify-candidate/script.sh": ("deploy/private-persistence-verification-report/v1", "verification"),
        prefix + "rehearse-server-replacement/script.sh": ("deploy/persistence-server-replacement-report/v1", None),
        prefix + "rehearse-runtime-credential-lifecycle/script.sh": ("deploy/persistence-runtime-identity-lifecycle-report/v1", None),
    }
    port = ports.get(command)
    if (port is None or type(value) is not dict or value.get("schema") != port[0]
            or value.get("target") != "kanbien-core-platform" or value.get("scope") != "core-server-persistence"
            or type(value.get("verdict")) is not str
            or value["verdict"] not in {"accepted", "prepared", "replaced", "pending", "failed", "uncertain", "blocked"}):
        return None
    raw = value.get("facts") if type(value.get("facts")) is dict else {}
    facts: dict[str, Any] = {}
    task_arn = re.compile(r"arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/[0-9a-f]{32}")
    receipt = re.compile(r"infra/04\.deploy/03\.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts/[A-Za-z0-9_-][A-Za-z0-9_.-]*\.json")
    for key in ("verifier_task", "original_task", "replacement_task", "task_arn"):
        item = raw.get(key)
        if type(item) is str and task_arn.fullmatch(item):
            facts[key] = item
    for key, pattern in (("operation_id", r"kp-[0-9a-f]{32}"), ("administration_task", r"[0-9a-f]{32}")):
        item = raw.get(key)
        if type(item) is str and re.fullmatch(pattern, item):
            facts[key] = item
    for key in ("proof_receipt", "unready_verifier_receipt", "ready_verifier_receipt"):
        item = raw.get(key)
        if type(item) is str and receipt.fullmatch(item) and ".." not in item.rsplit("/", 1)[-1]:
            facts[key] = item
    for key in ("recovery_boundary", "completed_at"):
        if key in raw:
            try:
                facts[key] = _timestamp(raw[key], key)
            except DiagnosticFailure:
                pass
    if raw.get("evidence_reuse") in ("historical-completion", "fresh-terminal-observation"):
        facts["evidence_reuse"] = raw["evidence_reuse"]
    if raw.get("mode") in ("create", "read", "cleanup", "health-ready", "health-unready"):
        facts["mode"] = raw["mode"]
    if raw.get("operation") in ("revoke-runtime", "restore-runtime"):
        facts["operation"] = raw["operation"]
    if type(raw.get("task_log_observation")) is str and raw["task_log_observation"] in COLLECTION_OBSERVATIONS:
        facts["task_log_observation"] = raw["task_log_observation"]
    if port[1] is not None:
        if "diagnostic" in raw:
            try:
                facts["diagnostic"] = runtime_contract().validate_persistence_task_source(raw["diagnostic"], port[1])
                if "related_diagnostics" in raw:
                    facts["related_diagnostics"] = validate_related_diagnostics(raw["related_diagnostics"], facts["diagnostic"])
            except Exception:
                pass
        if "task_failure" in raw:
            try:
                facts["task_failure"] = validate_persistence_task_failure(raw["task_failure"], port[1])
            except DiagnosticFailure:
                pass
    if port[0] == "deploy/persistence-runtime-identity-lifecycle-report/v1":
        child = raw.get("child_checkpoint")
        if type(child) is dict and type(child.get("command")) is str and child["command"] in ports and child["command"] != command:
            nested = validate_persistence_controller_checkpoint(child, child["command"])
            if nested is not None:
                facts["child_checkpoint"] = {"command": child["command"], **nested}
        operations = raw.get("verifier_operations")
        if type(operations) is dict:
            selected = {}
            for mode in ("create", "read", "cleanup", "health-ready", "health-unready"):
                if mode in operations:
                    nested = validate_persistence_controller_checkpoint({"schema": ports[prefix + "verify-candidate/script.sh"][0], "target": value["target"], "scope": value["scope"], "verdict": "accepted", "facts": operations[mode]}, prefix + "verify-candidate/script.sh")
                    if nested and nested["facts"]:
                        selected[mode] = nested["facts"]
            if selected:
                facts["verifier_operations"] = selected
    return {"schema": port[0], "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": value["verdict"], "facts": facts}
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


def validate_execution(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"phase", "elapsed_ms", "code_status", "classification"}:
        raise DiagnosticFailure("execution-fields-invalid")
    if not all(isinstance(value.get(key),str) and value[key] in vocabulary for key,vocabulary in (("phase",EXECUTION_PHASES),("code_status",CODE_STATUSES),("classification",FAILURE_CLASSIFICATIONS))):
        raise DiagnosticFailure("execution-vocabulary-invalid")
    elapsed = value.get("elapsed_ms")
    if elapsed is not None and (type(elapsed) is not int or not 0 <= elapsed <= 3_600_000):
        raise DiagnosticFailure("execution-timing-invalid")
    if value["phase"] == "unknown" and elapsed is not None:
        raise DiagnosticFailure("execution-unknown-timing-invalid")
    if value["code_status"] == "recognized" and value["classification"] in {"unknown", "authentication_material_invalid"}:
        raise DiagnosticFailure("execution-code-classification-invalid")
    if value["code_status"] != "recognized" and value["classification"] not in {"unknown", "authentication_material_invalid"}:
        raise DiagnosticFailure("execution-code-classification-invalid")
    return value


def validate_verifier_result(value: object) -> dict[str, Any]:
    """Explicit reader for historical envelopes and closed v2 observations."""
    if not isinstance(value, dict):
        raise DiagnosticFailure("verifier-result-invalid")
    if set(value) == {"verdict", "code"}:
        verdicts = {"accepted", "rejected"}
    else:
        if value.get("schema") != "deploy/persistence-restore-verifier-result/v2" or not {"schema", "verdict", "code"} <= set(value) or set(value) - {"schema", "verdict", "code", "execution", "diagnostic", "related_diagnostics"}:
            raise DiagnosticFailure("verifier-result-fields-invalid")
        verdicts = {"accepted", "rejected", "diagnosed", "diagnostic-failed"}
    if not isinstance(value.get("verdict"), str) or value["verdict"] not in verdicts:
        raise DiagnosticFailure("verifier-result-verdict-invalid")
    _safe_identifier(value.get("code"), field="verifier-result-code", pattern=CODE)
    if "execution" in value:
        if value["verdict"] in {"accepted", "diagnosed"}:
            raise DiagnosticFailure("verifier-success-failure-observation-invalid")
        validate_execution(value["execution"])
    if "diagnostic" in value:
        if value["verdict"] in {"accepted", "diagnosed"}:
            raise DiagnosticFailure("verifier-success-failure-observation-invalid")
        if value["code"] != "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID" and "execution" not in value:
            raise DiagnosticFailure("verifier-diagnostic-outcome-mismatch")
        primary = validate_runtime_diagnostic(value["diagnostic"], None if value["code"] == "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID" else "restore_verification", allow_core_source=True)
        if "execution" in value and primary["code"].startswith("persistence.") and {"phase", "classification", "codeStatus"} <= primary["detail"].keys():
            expected = {"phase": primary["detail"].get("phase"), "classification": primary["detail"].get("classification"), "code_status": primary["detail"].get("codeStatus")}
            if any(value["execution"].get(key) != item for key, item in expected.items()):
                raise DiagnosticFailure("verifier-diagnostic-execution-mismatch")
    if "related_diagnostics" in value:
        if "execution" not in value or "diagnostic" not in value or value["verdict"] in {"accepted", "diagnosed"}:
            raise DiagnosticFailure("verifier-related-outcome-mismatch")
        validate_related_diagnostics(value["related_diagnostics"], value["diagnostic"])
    return value


def validate(report: object) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise DiagnosticFailure("report-invalid")
    required = {
        "schema", "target", "scope", "operation_id", "stage", "observed_at",
        "original_failure", "operation_outcome", "classification", "evidence",
        "next_action", "collection",
    }
    allowed = required | {"facts", "execution", "diagnostic", "related_diagnostics", "task_failure"}
    if not required <= set(report) or set(report) - allowed:
        raise DiagnosticFailure("report-fields-invalid")
    if report.get("schema") != SCHEMA:
        raise DiagnosticFailure("report-schema-invalid")
    if "task_failure" in report:
        task_failure = report["task_failure"]
        validate_persistence_task_failure(task_failure, task_failure.get("task") if type(task_failure) is dict else None)
    if "diagnostic" in report:
        runtime_contract().validate_selected_record(report["diagnostic"])
    if "related_diagnostics" in report:
        if "diagnostic" not in report:
            raise DiagnosticFailure("diagnostic-related-primary-missing")
        validate_related_diagnostics(report["related_diagnostics"], report["diagnostic"])
    _safe_identifier(report.get("target"), field="target")
    _safe_identifier(report.get("scope"), field="scope")
    _safe_identifier(report.get("operation_id"), field="operation-id", pattern=OPERATION)
    if not isinstance(report.get("stage"),str) or report["stage"] not in STAGES:
        raise DiagnosticFailure("stage-invalid")
    _timestamp(report.get("observed_at"), "observed-at")

    original = report.get("original_failure")
    if not isinstance(original, dict) or set(original) != {"code", "exit_status"}:
        raise DiagnosticFailure("original-failure-invalid")
    _safe_identifier(original.get("code"), field="original-failure-code", pattern=CODE)
    if not isinstance(original.get("exit_status"), int) or isinstance(original.get("exit_status"), bool) or original["exit_status"] < 1 or original["exit_status"] > 255:
        raise DiagnosticFailure("original-failure-exit-status-invalid")

    outcome = report.get("operation_outcome")
    if not isinstance(outcome,str) or outcome not in OUTCOMES:
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
    if not isinstance(action, dict) or set(action) != {"decision"} or (not isinstance(action.get("decision"),str) or action["decision"] not in DECISIONS):
        raise DiagnosticFailure("next-action-invalid")
    if outcome == "unknown" and action["decision"] not in {"observe-current-operation", "inspect-retained-evidence", "stop-and-escalate"}:
        raise DiagnosticFailure("unknown-outcome-retry-invalid")

    collection = report.get("collection")
    if not isinstance(collection, dict) or "status" not in collection or set(collection) - {"status", "observation", "attempts", "task_observation", "task_attempts"} or (not isinstance(collection.get("status"),str) or collection["status"] not in COLLECTION):
        raise DiagnosticFailure("collection-invalid")
    if "observation" in collection and (not isinstance(collection["observation"],str) or collection["observation"] not in COLLECTION_OBSERVATIONS):
        raise DiagnosticFailure("collection-observation-invalid")
    if "attempts" in collection and (type(collection["attempts"]) is not int or not 1 <= collection["attempts"] <= 3):
        raise DiagnosticFailure("collection-attempts-invalid")
    if "task_observation" in collection and (not isinstance(collection["task_observation"],str) or collection["task_observation"] not in COLLECTION_OBSERVATIONS):
        raise DiagnosticFailure("collection-task-observation-invalid")
    if "task_attempts" in collection and (type(collection["task_attempts"]) is not int or not 1 <= collection["task_attempts"] <= 3):
        raise DiagnosticFailure("collection-task-attempts-invalid")
    if "execution" in report:
        validate_execution(report["execution"])
    _facts(report.get("facts"))
    return report


def build_report(
    *, target: str, scope: str, operation_id: str, stage: str,
    original_code: str, exit_status: int, outcome: str, classification: str,
    evidence_reference: str, next_decision: str, collection_status: str = "collected",
    facts: dict[str, str] | None = None, observed_at: str | None = None,
    execution: dict[str, Any] | None = None, collection_observation: str | None = None,
    collection_attempts: int | None = None, task_observation: str | None = None, task_attempts: int | None = None,
    diagnostic: dict[str, Any] | None = None,
    related_diagnostics: list[dict[str, Any]] | None = None,
    task_failure: dict[str, Any] | None = None,
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
    if collection_observation is not None:
        report["collection"]["observation"] = collection_observation
    if collection_attempts is not None:
        report["collection"]["attempts"] = collection_attempts
    if task_observation is not None:
        report["collection"]["task_observation"] = task_observation
    if task_attempts is not None:
        report["collection"]["task_attempts"] = task_attempts
    if execution is not None:
        report["execution"] = execution
    if diagnostic is not None:
        report["diagnostic"] = runtime_contract().validate_selected_record(diagnostic)
    if related_diagnostics is not None:
        report["related_diagnostics"] = validate_related_diagnostics(related_diagnostics, diagnostic)
    if task_failure is not None:
        report["task_failure"] = validate_persistence_task_failure(task_failure, task_failure.get("task") if type(task_failure) is dict else None)
    if facts:
        report["facts"] = facts
    return validate(report)


def write_report(path: Path, report: dict[str, Any], *, exclusive: bool = False) -> None:
    """Atomically write a validated report. Caller selects a governed retained path."""
    validate(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(report, handle, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    try:
        if exclusive:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


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
    """Only the named change set establishes this operation's cause/status.

    The existing event observation has no positive change-set correlation.
    Historical stack events therefore cannot supply or override these facts.
    """
    change = change_set if isinstance(change_set, dict) else {}
    reason = change.get("StatusReason")
    classification = _reason_classification(reason)
    facts: dict[str, str] = {}
    if isinstance(reason, str):
        match = PROPERTY_PATH.search(reason)
        if match:
            facts["property_path"] = match.group(0)
    status = change.get("Status")
    if isinstance(status, str) and status in {"CREATE_PENDING", "CREATE_IN_PROGRESS", "CREATE_COMPLETE", "DELETE_PENDING", "DELETE_IN_PROGRESS", "DELETE_COMPLETE", "DELETE_FAILED", "FAILED"}:
        facts["provider_status"] = status
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


class DiagnosticArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        # argparse's message can contain rejected arguments or numeric values.
        self.exit(2, "ERROR: deployment-operation-diagnostic-arguments-invalid\n")


def _cli() -> int:
    parser = DiagnosticArgumentParser(add_help=False)
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
    record.add_argument("--collection-observation")
    record.add_argument("--collection-attempts", type=int)
    record.add_argument("--task-log-observation")
    record.add_argument("--task-log-attempts", type=int)
    record.add_argument("--execution-phase")
    record.add_argument("--execution-elapsed-ms", type=int)
    record.add_argument("--execution-code-status")
    record.add_argument("--execution-classification")
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
        collection_observation=args.collection_observation, collection_attempts=args.collection_attempts, task_observation=args.task_log_observation, task_attempts=args.task_log_attempts,
        execution={"phase": args.execution_phase, "elapsed_ms": args.execution_elapsed_ms,
                   "code_status": args.execution_code_status, "classification": args.execution_classification}
                  if any(value is not None for value in (args.execution_phase, args.execution_elapsed_ms, args.execution_code_status, args.execution_classification)) else None,
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
    except (OSError, UnicodeError):
        print(json.dumps({"schema": "deploy/deployment-operation-diagnostic-validation/v1", "verdict": "failed", "findings": [{"code": "diagnostic-report-write-failed"}]}, sort_keys=True))
        raise SystemExit(1)
