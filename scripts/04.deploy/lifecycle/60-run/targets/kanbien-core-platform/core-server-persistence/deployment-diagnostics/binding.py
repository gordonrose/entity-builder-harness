#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.binding.kanbien-core-platform.core-server-persistence.diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-11-23"
#   updated_on: "2026-11-23"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.diagnostics
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind Core Server Persistence task evidence and controller checkpoints to retained shared deployment-operation diagnostics.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py
#   - id: deploy.test.kanbien-core-platform.core-server-persistence-diagnostics-binding
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/deployment-diagnostics/tests/binding-test.py
#   effects: [read-only]
"""Target-owned diagnostics for Core Server Persistence runtime evidence.

The shared deployment diagnostics module owns generic report mechanics. This
binding owns only the target's task evidence, controller checkpoints, and its
extension to the generic report shape. It is loaded directly by target scripts,
not registered in a global catalogue.
"""
from __future__ import annotations

import importlib.util
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[8]


@lru_cache(maxsize=1)
def shared():
    """Load the one retained generic report implementation."""
    path = ROOT / "scripts/04.deploy/shared/deployment-operation-diagnostics.py"
    spec = importlib.util.spec_from_file_location("shared_deployment_operation_diagnostics", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


DiagnosticFailure = shared().DiagnosticFailure


def validate_persistence_task_failure(value: object, expected_task: str) -> dict[str, Any]:
    """Validate bounded, target-owned evidence from a failed persistence task."""
    try:
        contract = shared().runtime_contract()
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
    """Reduce a bounded observation of an already identified persistence task."""
    events = response.get("events") if type(response) is dict else None
    if type(events) is not list:
        return None, "malformed"
    state = "incomplete" if len(events) >= 100 else "complete" if events else "empty"
    limits = shared().runtime_contract().persistence_task_failure_contract()
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
            state = "incomplete"
    return selected, state


def validate_persistence_controller_checkpoint(value: object, command: str) -> dict[str, Any] | None:
    """Select safe facts from the four bounded Core Server Persistence ports."""
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
                facts[key] = shared()._timestamp(raw[key], key)
            except DiagnosticFailure:
                pass
    if raw.get("evidence_reuse") in ("historical-completion", "fresh-terminal-observation"):
        facts["evidence_reuse"] = raw["evidence_reuse"]
    if raw.get("mode") in ("create", "read", "cleanup", "health-ready", "health-unready"):
        facts["mode"] = raw["mode"]
    if raw.get("operation") in ("revoke-runtime", "restore-runtime"):
        facts["operation"] = raw["operation"]
    if type(raw.get("task_log_observation")) is str and raw["task_log_observation"] in shared().COLLECTION_OBSERVATIONS:
        facts["task_log_observation"] = raw["task_log_observation"]
    if port[1] is not None:
        if "diagnostic" in raw:
            try:
                facts["diagnostic"] = shared().runtime_contract().validate_persistence_task_source(raw["diagnostic"], port[1])
                if "related_diagnostics" in raw:
                    facts["related_diagnostics"] = shared().validate_related_diagnostics(raw["related_diagnostics"], facts["diagnostic"])
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


def validate_verifier_result(value: object) -> dict[str, Any]:
    """Read historical and current Core Server Persistence verifier envelopes."""
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
    shared()._safe_identifier(value.get("code"), field="verifier-result-code", pattern=shared().CODE)
    if "execution" in value:
        if value["verdict"] in {"accepted", "diagnosed"}:
            raise DiagnosticFailure("verifier-success-failure-observation-invalid")
        shared().validate_execution(value["execution"])
    if "diagnostic" in value:
        if value["verdict"] in {"accepted", "diagnosed"}:
            raise DiagnosticFailure("verifier-success-failure-observation-invalid")
        if value["code"] != "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID" and "execution" not in value:
            raise DiagnosticFailure("verifier-diagnostic-outcome-mismatch")
        primary = shared().validate_runtime_diagnostic(value["diagnostic"], None if value["code"] == "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID" else "restore_verification", allow_core_source=True)
        if "execution" in value and primary["code"].startswith("persistence.") and {"phase", "classification", "codeStatus"} <= primary["detail"].keys():
            expected = {"phase": primary["detail"].get("phase"), "classification": primary["detail"].get("classification"), "code_status": primary["detail"].get("codeStatus")}
            if any(value["execution"].get(key) != item for key, item in expected.items()):
                raise DiagnosticFailure("verifier-diagnostic-execution-mismatch")
    if "related_diagnostics" in value:
        if "execution" not in value or "diagnostic" not in value or value["verdict"] in {"accepted", "diagnosed"}:
            raise DiagnosticFailure("verifier-related-outcome-mismatch")
        shared().validate_related_diagnostics(value["related_diagnostics"], value["diagnostic"])
    return value


def _validate_task_failure_extension(value: object) -> dict[str, Any]:
    expected_task = value.get("task") if type(value) is dict else None
    return validate_persistence_task_failure(value, expected_task)


def report_extension_validators() -> dict[str, Callable[[object], Any]]:
    """Return this target's only allowed extension to a generic report."""
    return {"task_failure": _validate_task_failure_extension}
