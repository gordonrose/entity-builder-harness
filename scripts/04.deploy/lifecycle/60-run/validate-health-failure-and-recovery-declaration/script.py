#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-health-failure-and-recovery-declaration.implementation
#   version: 2
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Fail closed when an embedded scope health, safe-failure, recovery, or proof declaration is missing, unsafe, or refers to absent passed evidence.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.workflow.verify-health-failure-and-recovery
#     path: .agentic/04.deploy/60-run/workflows/verify-health-failure-and-recovery.md
"""Validate the provider-neutral health_recovery block in a scope contract."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


SAFE_DIAGNOSTIC = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
SAFE_RELATIVE_PATH = re.compile(r"^(?!/)(?!.*://)[A-Za-z0-9._/-]+$")
PROOF_STATUSES = {"passed", "planned", "deferred"}


def load_contract(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError("scope-contract-unreadable") from error
    if not isinstance(value, dict):
        raise ValueError("scope-contract-invalid")
    return value


def mapping(value: Any, code: str, codes: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        codes.append(code)
        return None
    return value


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def safe_code(value: Any) -> bool:
    return isinstance(value, str) and SAFE_DIAGNOSTIC.fullmatch(value) is not None


def safe_path(value: Any) -> bool:
    return isinstance(value, str) and SAFE_RELATIVE_PATH.fullmatch(value) is not None


def check_operation(value: Any, name: str, codes: list[str]) -> dict[str, Any] | None:
    operation = mapping(value, f"{name}-missing", codes)
    if operation is None:
        return None
    if not isinstance(operation.get("path"), str) or not operation["path"].startswith("/"):
        codes.append(f"{name}-path-invalid")
    if not isinstance(operation.get("expected_status"), int) or not 200 <= operation["expected_status"] < 400:
        codes.append(f"{name}-expected-status-invalid")
    return operation


def check_proof(value: Any, name: str, codes: list[str]) -> None:
    proof = mapping(value, f"proof-{name}-missing", codes)
    if proof is None:
        return
    status = proof.get("status")
    if status not in PROOF_STATUSES:
        codes.append(f"proof-{name}-status-invalid")
    if name in {"local", "package"}:
        if not safe_path(proof.get("command")):
            codes.append(f"proof-{name}-command-invalid")
    elif status == "passed":
        if not safe_path(proof.get("evidence_reference")):
            codes.append("proof-live-recovery-evidence-invalid")
    elif status in {"planned", "deferred"}:
        required_fields = ("owner", "follow_up", "review_before")
        if status == "deferred":
            required_fields = ("reason", *required_fields)
        for field in required_fields:
            if not non_empty(proof.get(field)):
                codes.append(f"proof-live-recovery-{field}-missing")


def validate(contract: dict[str, Any], source_path: Path | None = None) -> list[str]:
    codes: list[str] = []
    declaration = mapping(contract.get("health_recovery"), "health-recovery-declaration-missing", codes)
    if declaration is None:
        return codes
    if declaration.get("declaration_schema") != "deploy/health-recovery-declaration/v1":
        codes.append("health-recovery-schema-invalid")

    liveness = check_operation(declaration.get("liveness"), "liveness", codes)
    readiness = check_operation(declaration.get("readiness"), "readiness", codes)
    if liveness and readiness and liveness.get("path") == readiness.get("path"):
        codes.append("liveness-and-readiness-not-distinct")
    if readiness is not None and not isinstance(readiness.get("depends_on"), list) or readiness is not None and not all(non_empty(item) for item in readiness.get("depends_on", [])):
        codes.append("readiness-dependencies-invalid")

    startup = mapping(declaration.get("startup_failure"), "startup-failure-missing", codes)
    invalid_config = startup and mapping(startup.get("invalid_required_configuration"), "startup-invalid-configuration-missing", codes)
    if invalid_config is not None:
        if invalid_config.get("result") not in {"process-exits", "not-ready"}:
            codes.append("startup-invalid-configuration-result-invalid")
        if not safe_code(invalid_config.get("diagnostic_code")):
            codes.append("startup-invalid-configuration-diagnostic-invalid")

    failures = declaration.get("dependency_failures")
    if not isinstance(failures, list):
        codes.append("dependency-failures-invalid")
    else:
        for item in failures:
            entry = mapping(item, "dependency-failure-entry-invalid", codes)
            if entry is None:
                continue
            unavailable = mapping(entry.get("unavailable"), "dependency-unavailable-behaviour-missing", codes)
            if not non_empty(entry.get("dependency")):
                codes.append("dependency-failure-name-invalid")
            if unavailable is not None:
                if unavailable.get("result") not in {"not-ready", "degraded", "fail-request"}:
                    codes.append("dependency-unavailable-result-invalid")
                if not safe_code(unavailable.get("diagnostic_code")):
                    codes.append("dependency-unavailable-diagnostic-invalid")
    declared_dependencies = contract.get("dependencies")
    if not isinstance(declared_dependencies, dict):
        codes.append("scope-dependencies-invalid")
    else:
        required = declared_dependencies.get("required")
        optional = declared_dependencies.get("optional")
        if not isinstance(required, list) or not isinstance(optional, list) or not all(non_empty(item) for item in [*required, *optional]):
            codes.append("scope-dependencies-invalid")
        elif isinstance(failures, list):
            failure_names = {item.get("dependency") for item in failures if isinstance(item, dict) and non_empty(item.get("dependency"))}
            declared_names = set(required) | set(optional)
            if not set(required).issubset(failure_names):
                codes.append("dependency-failure-missing-for-declared-dependency")
            if not failure_names.issubset(declared_names):
                codes.append("dependency-failure-for-undeclared-dependency")
            if readiness is not None and isinstance(readiness.get("depends_on"), list) and not set(readiness["depends_on"]).issubset(declared_names):
                codes.append("readiness-dependency-not-declared")

    workload_recovery = mapping(declaration.get("automatic_workload_recovery"), "automatic-workload-recovery-missing", codes)
    if workload_recovery is not None:
        if not non_empty(workload_recovery.get("owner")):
            codes.append("automatic-workload-recovery-owner-missing")
        if workload_recovery.get("unhealthy_workload") not in {"replace", "stop-and-escalate"}:
            codes.append("automatic-workload-recovery-action-invalid")
        prohibited = workload_recovery.get("prohibited_automatic_actions")
        if not isinstance(prohibited, list) or "replay-uncertain-operation" not in prohibited:
            codes.append("automatic-workload-recovery-replay-boundary-missing")

    release_recovery = mapping(declaration.get("release_recovery"), "release-recovery-missing", codes)
    if release_recovery is not None:
        if release_recovery.get("strategy") != "restore-prior-accepted-immutable-release":
            codes.append("release-recovery-strategy-invalid")
        if release_recovery.get("automatic_restore") != "prohibited":
            codes.append("release-recovery-automatic-restore-invalid")
        if release_recovery.get("verification") != "repeat-declared-health-and-meaningful-operation":
            codes.append("release-recovery-verification-invalid")

    proof = mapping(declaration.get("proof"), "health-recovery-proof-missing", codes)
    if proof is not None:
        check_proof(proof.get("local"), "local", codes)
        check_proof(proof.get("package"), "package", codes)
        check_proof(proof.get("live_recovery"), "live_recovery", codes)
        live = proof.get("live_recovery")
        if source_path is not None and isinstance(live, dict) and live.get("status") == "passed" and safe_path(live.get("evidence_reference")):
            if not (source_path.parent / live["evidence_reference"]).is_file():
                codes.append("proof-live-recovery-evidence-not-found")
    return list(dict.fromkeys(codes))


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--scope-contract", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.help:
        print("Usage: script.py --scope-contract <path> [--json]")
        return 0
    if unknown or args.scope_contract is None:
        codes = ["arguments-invalid"]
        contract_id = None
    else:
        try:
            contract = load_contract(args.scope_contract)
            contract_id = contract.get("id") if isinstance(contract.get("id"), str) else None
            codes = validate(contract, args.scope_contract)
        except ValueError as error:
            contract_id = None
            codes = [str(error)]
    report = {"schema": "deploy/health-failure-and-recovery-validation-report/v1", "scope_contract": contract_id, "verdict": "passed" if not codes else "failed", "findings": [{"code": code} for code in codes]}
    print(json.dumps(report, sort_keys=True))
    return 0 if not codes else 1


if __name__ == "__main__":
    raise SystemExit(main())
