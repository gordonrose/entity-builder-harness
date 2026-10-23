#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-persistence-diagnostic-mapping.implementation
#   version: 3
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.persistence-diagnostics
#   disciplines: [security, sre, agentic]
#   kind: test
#   purpose: Exercise synthetic positive and negative persistence diagnostic mapping fixtures.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.validate-persistence-diagnostic-mapping
#     path: scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/smoke-test.sh
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
VALIDATOR = ROOT / "scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.py"
INVENTORY = ROOT / "scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh"
TARGET_ROOT = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes"
CODES = (
    "persistence.transport-unavailable",
    "persistence.trust-validation-failed",
    "persistence.credential-rejected",
    "persistence.runtime-permission-denied",
    "persistence.capacity-exhausted",
    "persistence.schema-incompatible",
    "persistence.operation-timed-out",
    "persistence.outcome-uncertain",
    "persistence.unclassified-failure",
)


def mappings(workload: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for code in CODES:
        if code == "persistence.unclassified-failure":
            effect, retryability = "stop-and-escalate", "stop-and-escalate"
            next_check = "collect-governed-provider-observation"
        elif workload == "migration" and code in {"persistence.operation-timed-out", "persistence.outcome-uncertain"}:
            effect, retryability = "block-release-require-fresh-state-observation", "no-automatic-retry"
            next_check = "observe-persistence-state-before-replay"
        elif workload == "server" and code == "persistence.outcome-uncertain":
            effect, retryability = "request-uncertain-reconcile-before-retry", "no-automatic-retry"
            next_check = "observe-persistence-state-before-replay"
        elif workload == "server" and code == "persistence.transport-unavailable":
            effect, retryability = "not-ready", "bounded-retry"
            next_check = "inspect-declared-target-alignment-evidence"
        elif workload == "server" and code == "persistence.trust-validation-failed":
            effect, retryability = "not-ready", "target-correction-required"
            next_check = "inspect-governed-scope-configuration"
        elif workload == "server":
            effect, retryability = "not-ready", "target-correction-required"
            next_check = "inspect-declared-target-alignment-evidence"
        elif workload == "verifier" and code == "persistence.outcome-uncertain":
            effect, retryability = "stop-and-escalate", "no-automatic-retry"
            next_check = "observe-persistence-state-before-replay"
        else:
            effect, retryability = "failed-completion", "no-automatic-retry"
            next_check = "inspect-declared-target-alignment-evidence"
        entries.append({
            "code": code,
            "stage": "readiness" if workload == "server" else "migration",
            "effect": effect,
            "retryability": retryability,
            "safe_summary": f"PERSISTENCE_DIAGNOSTIC_OBSERVED:{code}",
            "next_check": next_check,
        })
    return entries


def valid_documents() -> tuple[dict[str, Any], dict[str, Any]]:
    contract: dict[str, Any] = {
        "schema": "deploy/target-scope-contract/v1",
        "target": "test-target",
        "scope": "persistence-proof",
        "dependencies": {"required": ["primary-relational-store"], "optional": [], "excluded": [], "persistence": ["primary-relational-store"]},
        "health_recovery": {
            "workloads": [
                {"id": "core-server", "workload_type": "long-running-server", "binding": "core-server-service", "persistence_writes": True},
                {"id": "persistence-migration", "workload_type": "run-to-completion-task", "binding": "persistence-migration-task", "persistence_writes": True, "migration_execution": {"dependency": "primary-relational-store"}},
                {"id": "persistence-verifier", "workload_type": "run-to-completion-task", "binding": "persistence-verifier-task", "persistence_writes": True},
            ],
        },
        "persistence_diagnostics": {
            "declaration_schema": "deploy/persistence-diagnostic-mapping/v1",
            "status": "declared",
            "dependency": {"id": "primary-relational-store", "required": True},
            "workloads": [
                {"id": "core-server", "mappings": mappings("server")},
                {"id": "persistence-migration", "mappings": mappings("migration")},
                {"id": "persistence-verifier", "mappings": mappings("verifier")},
            ],
        },
    }
    binding = {"workloads": [{"id": "core-server-service"}, {"id": "persistence-migration-task"}, {"id": "persistence-verifier-task"}]}
    return contract, binding


def run(contract: dict[str, Any], binding: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        contract_path, binding_path = root / "contract.yml", root / "binding.yml"
        contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
        binding_path.write_text(yaml.safe_dump(binding), encoding="utf-8")
        result = subprocess.run(["python3", str(VALIDATOR), "--scope-contract", str(contract_path), "--workload-binding", str(binding_path), "--json"], capture_output=True, text=True, check=False)
        return result.returncode, json.loads(result.stdout)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def finding(report: dict[str, Any], code: str) -> bool:
    return code in {item.get("code") for item in report.get("findings", []) if isinstance(item, dict)}


def main() -> None:
    contract, binding = valid_documents()
    status, report = run(contract, binding)
    require(status == 0 and report["verdict"] == "passed", "valid persistence diagnostic mapping must pass")

    no_persistence = copy.deepcopy(contract)
    no_persistence["dependencies"] = {"required": [], "optional": [], "excluded": ["persistence"], "persistence": []}
    no_persistence["excludes"] = ["persistence"]
    no_persistence["health_recovery"]["workloads"] = [
        {"id": "core-server", "workload_type": "long-running-server", "binding": "core-server-service"},
    ]
    no_persistence["persistence_diagnostics"] = {"status": "not-applicable", "reason": "Scope excludes persistence."}
    status, report = run(no_persistence, binding)
    require(status == 0, "justified non-persistence scope must pass")

    write_not_applicable = copy.deepcopy(no_persistence)
    write_not_applicable["health_recovery"]["workloads"][0]["persistence_writes"] = True
    status, report = run(write_not_applicable, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-not-applicable-workload-usage"), "declared persistence writes must reject not-applicable")

    false_not_applicable = copy.deepcopy(contract)
    false_not_applicable["excludes"] = ["persistence"]
    false_not_applicable["persistence_diagnostics"] = {"status": "not-applicable", "reason": "Incorrect fixture claim."}
    status, report = run(false_not_applicable, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-not-applicable-required-dependency") and finding(report, "persistence-diagnostics-not-applicable-workload-usage"), "a typed persistence dependency or migration use must reject not-applicable")

    usage_mismatch = copy.deepcopy(contract)
    usage_mismatch["dependencies"]["required"].append("another-relational-store")
    usage_mismatch["health_recovery"]["workloads"][1]["migration_execution"]["dependency"] = "another-relational-store"
    status, report = run(usage_mismatch, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-workload-usage-mismatch"), "migration use must reference a classified persistence dependency")

    missing = copy.deepcopy(contract)
    del missing["persistence_diagnostics"]
    status, report = run(missing, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-declaration-missing"), "missing mapping must fail")

    malformed_mapping = copy.deepcopy(contract)
    malformed_mapping["persistence_diagnostics"] = True
    status, report = run(malformed_mapping, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-declaration-missing"), "malformed mapping must fail with a structured finding")

    malformed_status = copy.deepcopy(contract)
    malformed_status["persistence_diagnostics"]["status"] = []
    status, report = run(malformed_status, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-declaration-missing"), "malformed status enum must fail without a traceback")

    malformed_workload_type = copy.deepcopy(contract)
    malformed_workload_type["health_recovery"]["workloads"][0]["workload_type"] = []
    status, report = run(malformed_workload_type, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-health-workload-invalid"), "malformed workload type must fail without a traceback")

    empty_dependency = copy.deepcopy(contract)
    empty_dependency["persistence_diagnostics"]["dependency"] = {}
    status, report = run(empty_dependency, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-dependency-invalid"), "empty required dependency object must fail")

    malformed_records = copy.deepcopy(contract)
    malformed_records["persistence_diagnostics"]["workloads"][0]["mappings"] = True
    status, report = run(malformed_records, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-workload-invalid"), "malformed mapping list must fail with a structured finding")

    unsafe = copy.deepcopy(contract)
    unsafe["persistence_diagnostics"]["workloads"][0]["mappings"][0]["safe_summary"] = "postgresql://synthetic-user:synthetic-password@127.0.0.1/test"
    status, report = run(unsafe, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-safe-summary-invalid"), "unsafe diagnostic value must fail")

    hostname = copy.deepcopy(contract)
    hostname["persistence_diagnostics"]["workloads"][0]["mappings"][0]["safe_summary"] = "PERSISTENCE_DIAGNOSTIC_OBSERVED:db.example.invalid"
    status, report = run(hostname, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-safe-summary-invalid"), "hostname-like summary must fail")

    provider_message = copy.deepcopy(contract)
    provider_message["persistence_diagnostics"]["workloads"][0]["mappings"][0]["provider_message"] = "synthetic provider response"
    status, report = run(provider_message, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-record-fields-unsupported"), "unsupported diagnostic fields must fail")

    unknown = copy.deepcopy(contract)
    unknown["persistence_diagnostics"]["workloads"][0]["mappings"][0]["code"] = "persistence.provider-message"
    status, report = run(unknown, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-code-invalid"), "unknown diagnostic code must fail")

    server_retry = copy.deepcopy(contract)
    server_retry["persistence_diagnostics"]["workloads"][0]["mappings"][0]["effect"] = "stop-and-escalate"
    status, report = run(server_retry, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-server-dependency-behaviour-invalid"), "server transport mapping must preserve readiness behaviour")

    trust_retry = copy.deepcopy(contract)
    trust_retry["persistence_diagnostics"]["workloads"][0]["mappings"][1]["retryability"] = "bounded-retry"
    status, report = run(trust_retry, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-server-trust-behaviour-invalid"), "server trust failure must require target correction")

    uncertain = copy.deepcopy(contract)
    for item in uncertain["persistence_diagnostics"]["workloads"][1]["mappings"]:
        if item["code"] == "persistence.outcome-uncertain":
            item["retryability"] = "bounded-retry"
    status, report = run(uncertain, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-migration-uncertain-outcome-invalid"), "uncertain migration must block release without retry")

    timed_out = copy.deepcopy(contract)
    for item in timed_out["persistence_diagnostics"]["workloads"][1]["mappings"]:
        if item["code"] == "persistence.operation-timed-out":
            item["effect"] = "failed-completion"
            item["retryability"] = "bounded-retry"
            item["next_check"] = "inspect-declared-target-alignment-evidence"
    status, report = run(timed_out, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-migration-uncertain-outcome-invalid"), "timed-out migration must block release without retry")

    no_server_uncertainty = copy.deepcopy(contract)
    no_server_uncertainty["persistence_diagnostics"]["workloads"][0]["mappings"] = [item for item in no_server_uncertainty["persistence_diagnostics"]["workloads"][0]["mappings"] if item["code"] != "persistence.outcome-uncertain"]
    status, report = run(no_server_uncertainty, binding)
    require(status != 0 and finding(report, "persistence-diagnostic-code-coverage-incomplete"), "writing server must map an uncertain write outcome")

    incomplete = copy.deepcopy(contract)
    incomplete["persistence_diagnostics"]["workloads"].pop()
    status, report = run(incomplete, binding)
    require(status != 0 and finding(report, "persistence-diagnostics-workload-coverage-incomplete"), "every persistence workload needs a mapping")

    with tempfile.TemporaryDirectory() as temporary:
        copied = Path(temporary) / "20-scopes"
        shutil.copytree(TARGET_ROOT, copied)
        bootstrap = copied / "bootstrap-runtime/00-declaration/declaration-contract.yml"
        document = yaml.safe_load(bootstrap.read_text(encoding="utf-8"))
        del document["persistence_diagnostics"]
        bootstrap.write_text(yaml.safe_dump(document), encoding="utf-8")
        result = subprocess.run([str(INVENTORY), "--target-root", str(copied), "--json"], capture_output=True, text=True, check=False)
        inventory = json.loads(result.stdout)
        require(result.returncode != 0 and finding(inventory, "scope-lifecycle-persistence-diagnostics-invalid"), "active inventory must invoke diagnostic validation")

    print("Persistence diagnostic mapping tests passed.")


if __name__ == "__main__":
    main()
