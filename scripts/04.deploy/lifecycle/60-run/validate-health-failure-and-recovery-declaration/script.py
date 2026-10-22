#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-health-failure-and-recovery-declaration.implementation
#   version: 4
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Fail closed when individual workloads lack type-appropriate safe health, completion, recovery, proof, or binding facts.
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
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


SAFE_DIAGNOSTIC = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
SAFE_RELATIVE_PATH = re.compile(r"^(?!/)(?!.*://)[A-Za-z0-9._/-]+$")
SAFE_SOURCE_REFERENCE = re.compile(r"^(?!/)(?!.*://)[A-Za-z0-9._/#-]+$")
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


def timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


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


def validate_v2(contract: dict[str, Any], source: Path | None, binding: dict[str, Any] | None) -> list[str]:
    codes: list[str] = []
    health = contract.get("health_recovery")
    workloads = health.get("workloads") if isinstance(health, dict) else None
    if not isinstance(workloads, list) or not workloads:
        return ["workloads-missing"]
    required = (contract.get("dependencies") or {}).get("required", [])
    if not isinstance(required, list) or not all(non_empty(item) for item in required):
        codes.append("scope-dependencies-invalid"); required=[]
    binding_items = (binding or {}).get("workloads", [])
    if binding is not None and not isinstance(binding_items, list):
        codes.append("workload-binding-inventory-invalid")
        binding_items = []
    bindings = {
        item.get("id"): item
        for item in binding_items
        if isinstance(item, dict) and non_empty(item.get("id"))
    }
    if binding is not None and len(bindings) != len(binding_items):
        codes.append("workload-binding-inventory-invalid")
    identities: list[str] = []
    known_types = {"long-running-server", "continuous-worker", "run-to-completion-task"}
    for workload in workloads:
        item = mapping(workload, "workload-entry-invalid", codes)
        if item is None: continue
        identity, kind = item.get("id"), item.get("workload_type")
        if not non_empty(identity): codes.append("workload-id-invalid"); continue
        identities.append(identity)
        if kind not in known_types: codes.append("workload-type-invalid"); continue
        check_not_applicable(item, kind, codes)
        bind = item.get("binding")
        if not non_empty(bind): codes.append("workload-binding-missing")
        elif binding is not None:
            bound = bindings.get(bind)
            if bound is None or bound.get("workload_type") != kind:
                codes.append("workload-binding-type-mismatch")
            elif kind == "long-running-server" and bound.get("runtime_class") != "service":
                codes.append("workload-binding-runtime-class-mismatch")
            elif kind == "run-to-completion-task" and bound.get("runtime_class") != "task":
                codes.append("workload-binding-runtime-class-mismatch")
            elif kind == "continuous-worker" and bound.get("runtime_class") not in {"service", "task"}:
                codes.append("workload-binding-runtime-class-mismatch")
            check_workload_execution(bound, codes)
        if kind == "long-running-server":
            live=check_operation(item.get("liveness"), "liveness", codes); ready=check_operation(item.get("readiness"), "readiness", codes)
            if live and ready and live.get("path") == ready.get("path"): codes.append("liveness-and-readiness-not-distinct")
            if ready is not None and (not isinstance(ready.get("depends_on"), list) or set(ready.get("depends_on", [])) != set(required)): codes.append("readiness-dependencies-invalid")
            check_v2_startup(item, codes); check_v2_dependencies(item, required, codes); check_v2_recovery(item, codes); check_v2_release(item, codes); check_v2_proof(item, "live_recovery", source, codes)
        elif kind == "continuous-worker":
            check_v2_startup(item, codes); check_v2_dependencies(item, required, codes); check_v2_recovery(item, codes); check_v2_release(item, codes); check_v2_proof(item, "live_recovery", source, codes)
            progress=mapping(item.get("progress_health"), "worker-progress-health-missing", codes)
            if progress is not None and (
                not non_empty(progress.get("mechanism"))
                or not isinstance(progress.get("maximum_silence_seconds"), int)
                or progress["maximum_silence_seconds"] <= 0
            ): codes.append("worker-progress-health-invalid")
            shutdown=mapping(item.get("shutdown"), "worker-shutdown-missing", codes)
            interrupted=mapping(item.get("interrupted_work"), "worker-interrupted-work-missing", codes)
            if shutdown is not None and shutdown.get("policy") not in {"stop-intake-and-finish-safe-work", "stop-intake-and-abandon-idempotent-work"}: codes.append("worker-shutdown-invalid")
            if interrupted is not None and interrupted.get("policy") not in {"do-not-replay-uncertain-work", "resume-idempotent-work-only"}: codes.append("worker-interrupted-work-invalid")
        else:
            completion=mapping(item.get("completion"), "task-completion-missing", codes)
            if completion is not None:
                success=mapping(completion.get("success"), "task-success-criteria-missing", codes)
                interruption=mapping(completion.get("interruption"), "task-interruption-handling-missing", codes)
                if not isinstance(completion.get("deadline_seconds"), int) or completion["deadline_seconds"] <= 0: codes.append("task-deadline-invalid")
                if success is not None and (success.get("exit_code") != 0 or not safe_code(success.get("result_code"))): codes.append("task-success-criteria-invalid")
                if interruption is not None and interruption.get("policy") not in {"stop-and-escalate", "safe-to-retry-idempotent-only"}: codes.append("task-interruption-handling-invalid")
                if completion.get("retry_policy") not in {"no-automatic-retries", "bounded-idempotent-retry"}: codes.append("task-retry-policy-invalid")
            if not isinstance(item.get("required_workloads"), list) or not all(non_empty(value) for value in item.get("required_workloads", [])): codes.append("task-required-workloads-invalid")
            check_v2_proof(item, "completion", source, codes)
    if len(identities) != len(set(identities)): codes.append("workload-id-invalid")
    all_ids=set(identities)
    for item in workloads:
        if isinstance(item, dict) and item.get("workload_type") == "run-to-completion-task" and not set(item.get("required_workloads", [])).issubset(all_ids - {item.get("id")}): codes.append("task-required-workload-invalid")
    if binding is not None and set(bindings) != {item.get("binding") for item in workloads if isinstance(item, dict)}: codes.append("workload-binding-inventory-mismatch")
    return list(dict.fromkeys(codes))


def check_not_applicable(item: dict[str, Any], kind: str, codes: list[str]) -> None:
    declarations = item.get("not_applicable", [])
    if not isinstance(declarations, list):
        codes.append("workload-not-applicable-invalid")
        return
    allowed = {
        "long-running-server": {
            "worker-progress-health", "worker-shutdown", "worker-interrupted-work",
            "task-completion", "task-interruption-handling", "task-retry-policy",
        },
        "continuous-worker": {
            "http-liveness", "http-readiness", "task-completion",
            "task-interruption-handling", "task-retry-policy",
        },
        "run-to-completion-task": {
            "http-liveness", "http-readiness", "worker-progress-health",
            "worker-shutdown", "worker-interrupted-work", "automatic-replacement",
        },
    }[kind]
    concerns: list[str] = []
    for declaration in declarations:
        entry = mapping(declaration, "workload-not-applicable-invalid", codes)
        if entry is None:
            continue
        concern = entry.get("concern")
        concerns.append(concern if isinstance(concern, str) else "")
        if concern not in allowed or not non_empty(entry.get("workload_type_basis")) or not non_empty(entry.get("scope_basis")):
            codes.append("workload-not-applicable-invalid")
    if len(concerns) != len(set(concerns)):
        codes.append("workload-not-applicable-invalid")


def check_workload_execution(binding: dict[str, Any], codes: list[str]) -> None:
    """Require a safe trace from a workload binding to the code it executes."""
    execution = mapping(binding.get("execution"), "workload-execution-missing", codes)
    if execution is None:
        return
    if execution.get("kind") not in {"compiled-entrypoint", "inline-command"}:
        codes.append("workload-execution-kind-invalid")
    if not isinstance(execution.get("source_reference"), str) or SAFE_SOURCE_REFERENCE.fullmatch(execution["source_reference"]) is None:
        codes.append("workload-execution-source-invalid")
    if not non_empty(execution.get("command_description")):
        codes.append("workload-execution-command-invalid")

def check_v2_startup(item: dict[str, Any], codes: list[str]) -> None:
    startup = mapping(item.get("startup_failure"), "startup-failure-missing", codes)
    if startup is None:
        return
    invalid = mapping(startup.get("invalid_required_configuration"), "startup-invalid-configuration-missing", codes)
    if invalid is not None and (
        invalid.get("result") not in {"process-exits", "not-ready"}
        or not safe_code(invalid.get("diagnostic_code"))
    ):
        codes.append("startup-invalid-configuration-invalid")


def check_v2_dependencies(item: dict[str, Any], required: list[Any], codes: list[str]) -> None:
    failures = item.get("dependency_failures")
    if not isinstance(failures, list):
        codes.append("dependency-failures-invalid")
        return
    names: set[str] = set()
    for failure in failures:
        entry = mapping(failure, "dependency-failure-entry-invalid", codes)
        if entry is None:
            continue
        unavailable = mapping(entry.get("unavailable"), "dependency-unavailable-behaviour-missing", codes)
        if non_empty(entry.get("dependency")):
            names.add(entry["dependency"])
        else:
            codes.append("dependency-failure-name-invalid")
        if unavailable is not None and (
            unavailable.get("result") not in {"not-ready", "degraded", "fail-request"}
            or not safe_code(unavailable.get("diagnostic_code"))
        ):
            codes.append("dependency-unavailable-invalid")
    if not set(required).issubset(names):
        codes.append("dependency-failure-missing-for-declared-dependency")
    if not names.issubset(set(required)):
        codes.append("dependency-failure-for-undeclared-dependency")


def check_v2_recovery(item: dict[str, Any], codes: list[str]) -> None:
    recovery = mapping(item.get("automatic_workload_recovery"), "automatic-workload-recovery-missing", codes)
    if recovery is not None and (
        not non_empty(recovery.get("owner"))
        or recovery.get("unhealthy_workload") not in {"replace", "stop-and-escalate"}
        or not isinstance(recovery.get("prohibited_automatic_actions"), list)
        or "replay-uncertain-operation" not in recovery["prohibited_automatic_actions"]
    ):
        codes.append("automatic-workload-recovery-invalid")


def check_v2_release(item: dict[str, Any], codes: list[str]) -> None:
    recovery = mapping(item.get("release_recovery"), "release-recovery-missing", codes)
    if recovery is not None and (
        recovery.get("strategy") != "restore-prior-accepted-immutable-release"
        or recovery.get("automatic_restore") != "prohibited"
        or recovery.get("verification") != "repeat-declared-health-and-meaningful-operation"
    ):
        codes.append("release-recovery-invalid")


def check_v2_proof(item: dict[str, Any], terminal: str, source: Path | None, codes: list[str]) -> None:
    proof = mapping(item.get("proof"), "workload-proof-missing", codes)
    if proof is None:
        return
    for name in ("local", "package"):
        part = mapping(proof.get(name), f"proof-{name}-missing", codes)
        if part is not None and (
            part.get("status") not in PROOF_STATUSES or not safe_path(part.get("command"))
        ):
            codes.append(f"proof-{name}-invalid")
    final = mapping(proof.get(terminal), f"proof-{terminal}-missing", codes)
    if final is None or final.get("status") not in PROOF_STATUSES:
        codes.append(f"proof-{terminal}-invalid")
        return
    if final["status"] == "passed":
        if not safe_path(final.get("evidence_reference")): codes.append(f"proof-{terminal}-evidence-invalid")
        elif source is not None and not (source.parent / final["evidence_reference"]).is_file(): codes.append(f"proof-{terminal}-evidence-not-found")
        if terminal == "completion" and (final.get("exit_code") != 0 or not safe_code(final.get("result_code"))): codes.append("proof-completion-result-invalid")
        if terminal == "completion":
            observed = timestamp(final.get("observed_at"))
            fresh_after = timestamp(final.get("fresh_after"))
            if observed is None or fresh_after is None:
                codes.append("proof-completion-freshness-invalid")
            elif observed < fresh_after:
                codes.append("proof-completion-stale")
    elif any(
        not non_empty(final.get(field))
        for field in (
            ("owner", "follow_up", "review_before")
            if final["status"] == "planned"
            else ("reason", "owner", "follow_up", "review_before")
        )
    ):
        codes.append(f"proof-{terminal}-deferment-invalid")

def validate(contract: dict[str, Any], source_path: Path | None = None, binding: dict[str, Any] | None = None) -> list[str]:
    codes: list[str] = []
    declaration = mapping(contract.get("health_recovery"), "health-recovery-declaration-missing", codes)
    if declaration is None:
        return codes
    if declaration.get("declaration_schema") == "deploy/health-failure-and-recovery-declaration/v2": return validate_v2(contract, source_path, binding)
    if declaration.get("declaration_schema") != "deploy/health-recovery-declaration/v1":
        codes.append("health-recovery-schema-invalid")

    liveness = check_operation(declaration.get("liveness"), "liveness", codes)
    readiness = check_operation(declaration.get("readiness"), "readiness", codes)
    if liveness and readiness and liveness.get("path") == readiness.get("path"):
        codes.append("liveness-and-readiness-not-distinct")
    if readiness is not None and not isinstance(readiness.get("depends_on"), list) or readiness is not None and not all(non_empty(item) for item in readiness.get("depends_on", [])):
        codes.append("readiness-dependencies-invalid")

    startup = mapping(declaration.get("startup_failure"), "startup-failure-missing", codes)
    invalid_config = (
        mapping(startup.get("invalid_required_configuration"), "startup-invalid-configuration-missing", codes)
        if startup is not None
        else None
    )
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
    parser.add_argument("--workload-binding", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.help:
        print("Usage: script.py --scope-contract <path> [--workload-binding <path>] [--json]")
        return 0
    if unknown or args.scope_contract is None:
        codes = ["arguments-invalid"]
        contract_id = None
    else:
        try:
            contract = load_contract(args.scope_contract)
            contract_id = contract.get("id") if isinstance(contract.get("id"), str) else None
            binding = load_contract(args.workload_binding) if args.workload_binding else None
            codes = validate(contract, args.scope_contract, binding)
        except ValueError as error:
            contract_id = None
            codes = [str(error)]
    report = {"schema": "deploy/health-failure-and-recovery-validation-report/v2", "scope_contract": contract_id, "verdict": "passed" if not codes else "failed", "findings": [{"code": code} for code in codes]}
    print(json.dumps(report, sort_keys=True))
    return 0 if not codes else 1


if __name__ == "__main__":
    raise SystemExit(main())
