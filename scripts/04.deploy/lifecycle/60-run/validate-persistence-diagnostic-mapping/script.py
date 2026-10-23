#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-persistence-diagnostic-mapping.implementation
#   version: 3
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.persistence-diagnostics
#   disciplines: [security, sre, agentic]
#   kind: script
#   purpose: Fail closed when a scope omits, weakens, or makes unsafe its persistence diagnostic mapping.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.validate-persistence-diagnostic-mapping
#     path: scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.sh
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

CODE = re.compile(r"^persistence\.[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*$")
KNOWN_CODES = frozenset({
    "persistence.transport-unavailable", "persistence.trust-validation-failed",
    "persistence.credential-rejected", "persistence.runtime-permission-denied",
    "persistence.capacity-exhausted", "persistence.schema-incompatible",
    "persistence.operation-timed-out", "persistence.outcome-uncertain",
    "persistence.unclassified-failure",
})
STAGES = frozenset({"configuration", "startup", "readiness", "request", "migration", "candidate-deployment", "update", "retirement", "recovery", "image-rollback", "database-restore"})
RETRYABILITY = frozenset({"bounded-retry", "target-correction-required", "no-automatic-retry", "stop-and-escalate"})
EFFECTS = {
    "long-running-server": frozenset({"startup-exit", "not-ready", "bounded-reconnect", "request-uncertain-reconcile-before-retry", "stop-and-escalate"}),
    "continuous-worker": frozenset({"bounded-retry", "stop-and-escalate", "failed-completion"}),
    "run-to-completion-task": frozenset({"failed-completion", "block-release-require-fresh-state-observation", "stop-and-escalate"}),
}
RECORD_FIELDS = frozenset({"code", "stage", "effect", "retryability", "safe_summary", "next_check"})
NEXT_CHECKS = frozenset({
    "inspect-declared-target-alignment-evidence",
    "inspect-governed-scope-configuration",
    "observe-persistence-state-before-replay",
    "collect-governed-provider-observation",
})


def load(path: Path) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return value if isinstance(value, dict) else None


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add(codes: list[str], code: str) -> None:
    if code not in codes:
        codes.append(code)


def persistence_dependencies(contract: dict[str, Any], codes: list[str]) -> list[str] | None:
    dependencies = contract.get("dependencies")
    declared = dependencies.get("persistence") if isinstance(dependencies, dict) else None
    if not isinstance(declared, list) or not all(text(value) for value in declared) or len(declared) != len(set(declared)):
        add(codes, "persistence-diagnostics-dependency-classification-invalid")
        return None
    required = dependencies.get("required") if isinstance(dependencies, dict) else None
    if not isinstance(required, list) or not set(declared).issubset(set(value for value in required if text(value))):
        add(codes, "persistence-diagnostics-dependency-classification-invalid")
        return None
    return declared


def persistence_workload_usage(contract: dict[str, Any]) -> set[str]:
    health = contract.get("health_recovery")
    workloads = health.get("workloads") if isinstance(health, dict) else []
    if not isinstance(workloads, list):
        return {"malformed-health-workloads"}
    used: set[str] = set()
    for workload in workloads:
        if not isinstance(workload, dict):
            continue
        migration = workload.get("migration_execution")
        if migration is not None:
            if isinstance(migration, dict) and text(migration.get("dependency")):
                used.add(migration["dependency"])
            else:
                used.add("malformed-migration-execution")
        mediated = workload.get("server_mediated_dependency_proof")
        if mediated is not None:
            if isinstance(mediated, dict) and text(mediated.get("dependency")):
                used.add(mediated["dependency"])
            else:
                used.add("malformed-server-mediated-dependency-proof")
        if workload.get("persistence_writes") is True:
            used.add("declared-persistence-write")
    return used


def health_workloads(contract: dict[str, Any], codes: list[str]) -> dict[str, dict[str, Any]]:
    health = contract.get("health_recovery")
    workloads = health.get("workloads") if isinstance(health, dict) else None
    if not isinstance(workloads, list):
        add(codes, "persistence-diagnostics-health-recovery-missing")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for workload in workloads:
        workload_type = workload.get("workload_type") if isinstance(workload, dict) else None
        if not isinstance(workload, dict) or not text(workload.get("id")) or not isinstance(workload_type, str) or workload_type not in EFFECTS:
            add(codes, "persistence-diagnostics-health-workload-invalid")
            continue
        workload_id = workload["id"]
        if workload_id in result:
            add(codes, "persistence-diagnostics-health-workload-duplicate")
        result[workload_id] = workload
    return result


def binding_ids(binding: dict[str, Any], codes: list[str]) -> set[str]:
    workloads = binding.get("workloads")
    if not isinstance(workloads, list):
        add(codes, "persistence-diagnostics-binding-missing")
        return set()
    ids: set[str] = set()
    for workload in workloads:
        if not isinstance(workload, dict) or not text(workload.get("id")):
            add(codes, "persistence-diagnostics-binding-invalid")
            continue
        ids.add(workload["id"])
    return ids


def validate_not_applicable(contract: dict[str, Any], mapping: dict[str, Any], codes: list[str]) -> None:
    if not text(mapping.get("reason")):
        add(codes, "persistence-diagnostics-not-applicable-reason-missing")
    excludes = contract.get("excludes")
    if not isinstance(excludes, list) or "persistence" not in excludes:
        add(codes, "persistence-diagnostics-not-applicable-not-excluded")
    declared = persistence_dependencies(contract, codes)
    if declared:
        add(codes, "persistence-diagnostics-not-applicable-required-dependency")
    if persistence_workload_usage(contract):
        add(codes, "persistence-diagnostics-not-applicable-workload-usage")
    if set(mapping) - {"status", "reason"}:
        add(codes, "persistence-diagnostics-not-applicable-extra-fields")


def validate_entry(entry: Any, workload: dict[str, Any], codes: list[str]) -> str | None:
    if not isinstance(entry, dict):
        add(codes, "persistence-diagnostic-record-invalid")
        return None
    required = ("code", "stage", "effect", "retryability", "safe_summary", "next_check")
    if any(not text(entry.get(key)) for key in required):
        add(codes, "persistence-diagnostic-record-fields-missing")
        return None
    if set(entry) != RECORD_FIELDS:
        add(codes, "persistence-diagnostic-record-fields-unsupported")
    code = entry["code"]
    if CODE.fullmatch(code) is None or code not in KNOWN_CODES:
        add(codes, "persistence-diagnostic-code-invalid")
    if entry["stage"] not in STAGES:
        add(codes, "persistence-diagnostic-stage-invalid")
    workload_type = workload["workload_type"]
    if entry["effect"] not in EFFECTS[workload_type]:
        add(codes, "persistence-diagnostic-effect-invalid")
    if entry["retryability"] not in RETRYABILITY:
        add(codes, "persistence-diagnostic-retryability-invalid")
    if entry["safe_summary"] != f"PERSISTENCE_DIAGNOSTIC_OBSERVED:{code}":
        add(codes, "persistence-diagnostic-safe-summary-invalid")
    if entry["next_check"] not in NEXT_CHECKS:
        add(codes, "persistence-diagnostic-next-check-invalid")
    if code == "persistence.unclassified-failure" and (entry["effect"] != "stop-and-escalate" or entry["retryability"] != "stop-and-escalate"):
        add(codes, "persistence-diagnostic-unclassified-fallback-invalid")
    migration = workload.get("migration_execution")
    if isinstance(migration, dict) and code in {"persistence.operation-timed-out", "persistence.outcome-uncertain"}:
        if entry["effect"] != "block-release-require-fresh-state-observation" or entry["retryability"] != "no-automatic-retry" or entry["next_check"] != "observe-persistence-state-before-replay":
            add(codes, "persistence-diagnostic-migration-uncertain-outcome-invalid")
    elif code == "persistence.outcome-uncertain" and entry["retryability"] == "bounded-retry":
        add(codes, "persistence-diagnostic-uncertain-retry-invalid")
    if workload_type == "long-running-server" and code == "persistence.transport-unavailable":
        if entry["effect"] not in {"not-ready", "bounded-reconnect"} or entry["retryability"] != "bounded-retry":
            add(codes, "persistence-diagnostic-server-dependency-behaviour-invalid")
    if workload_type == "long-running-server" and code == "persistence.trust-validation-failed":
        if entry["effect"] != "not-ready" or entry["retryability"] != "target-correction-required":
            add(codes, "persistence-diagnostic-server-trust-behaviour-invalid")
    if workload_type == "long-running-server" and code == "persistence.outcome-uncertain":
        if entry["effect"] != "request-uncertain-reconcile-before-retry" or entry["retryability"] != "no-automatic-retry":
            add(codes, "persistence-diagnostic-server-uncertain-write-invalid")
    return code


def validate_declared(contract: dict[str, Any], binding: dict[str, Any], mapping: dict[str, Any], codes: list[str]) -> None:
    if mapping.get("declaration_schema") != "deploy/persistence-diagnostic-mapping/v1":
        add(codes, "persistence-diagnostics-schema-invalid")
    dependency = mapping.get("dependency")
    dependency_id = dependency.get("id") if isinstance(dependency, dict) else None
    if not isinstance(dependency, dict) or not text(dependency_id) or dependency.get("required") is not True:
        add(codes, "persistence-diagnostics-dependency-invalid")
        dependency_id = None
    declared_dependencies = persistence_dependencies(contract, codes)
    if declared_dependencies is None or dependency_id not in declared_dependencies:
        add(codes, "persistence-diagnostics-required-dependency-mismatch")
    used_dependencies = persistence_workload_usage(contract)
    named_dependencies = used_dependencies - {"declared-persistence-write"}
    if not named_dependencies.issubset(set(declared_dependencies or [])):
        add(codes, "persistence-diagnostics-workload-usage-mismatch")

    health = health_workloads(contract, codes)
    binding_workloads = binding_ids(binding, codes)
    for workload in health.values():
        if workload.get("binding") not in binding_workloads:
            add(codes, "persistence-diagnostics-binding-workload-mismatch")
    declared_workloads = mapping.get("workloads")
    if not isinstance(declared_workloads, list) or not declared_workloads:
        add(codes, "persistence-diagnostics-workloads-missing")
        return
    seen: set[str] = set()
    mapped: set[str] = set()
    for item in declared_workloads:
        if not isinstance(item, dict) or not text(item.get("id")) or not isinstance(item.get("mappings"), list):
            add(codes, "persistence-diagnostics-workload-invalid")
            continue
        workload_id = item["id"]
        if workload_id in seen or workload_id not in health:
            add(codes, "persistence-diagnostics-workload-invalid")
            continue
        seen.add(workload_id)
        mapped.add(workload_id)
        workload = health[workload_id]
        writes = workload.get("persistence_writes")
        if not isinstance(writes, bool):
            add(codes, "persistence-diagnostics-workload-write-declaration-invalid")
            writes = False
        found: set[str] = set()
        for record in item["mappings"]:
            diagnostic_code = validate_entry(record, workload, codes)
            if diagnostic_code is None:
                continue
            if diagnostic_code in found:
                add(codes, "persistence-diagnostic-code-duplicate")
            found.add(diagnostic_code)
        required_codes = KNOWN_CODES if workload["workload_type"] != "long-running-server" or writes else KNOWN_CODES - {"persistence.outcome-uncertain"}
        if found != required_codes:
            add(codes, "persistence-diagnostic-code-coverage-incomplete")
    if mapped != set(health):
        add(codes, "persistence-diagnostics-workload-coverage-incomplete")


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--scope-contract", type=Path, required=True)
    parser.add_argument("--workload-binding", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.help:
        print("Usage: script.py --scope-contract <path> --workload-binding <path> [--json]")
        return 0
    codes: list[str] = []
    if unknown:
        add(codes, "arguments-invalid")
    contract = load(args.scope_contract)
    binding = load(args.workload_binding)
    if contract is None:
        add(codes, "persistence-diagnostics-scope-contract-unreadable")
    if binding is None:
        add(codes, "persistence-diagnostics-workload-binding-unreadable")
    if contract is not None and binding is not None:
        mapping = contract.get("persistence_diagnostics")
        status = mapping.get("status") if isinstance(mapping, dict) else None
        if not isinstance(mapping, dict) or not isinstance(status, str) or status not in {"not-applicable", "declared"}:
            add(codes, "persistence-diagnostics-declaration-missing")
        elif status == "not-applicable":
            validate_not_applicable(contract, mapping, codes)
        else:
            validate_declared(contract, binding, mapping, codes)
    report = {"schema": "deploy/persistence-diagnostic-mapping-report/v1", "scope_contract": str(args.scope_contract), "verdict": "passed" if not codes else "failed", "findings": [{"code": code} for code in codes]}
    print(json.dumps(report, sort_keys=True))
    return 0 if not codes else 1


if __name__ == "__main__":
    raise SystemExit(main())
