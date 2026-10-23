#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-secret-dependency-declaration.implementation
#   version: 5
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.secret-management
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Fail closed when a scope omits or weakens its non-secret dependency credential declaration.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.workflow.declare-secret-dependency
#     path: .agentic/04.deploy/00-target-alignment/workflows/declare-secret-dependency.md

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


CONFIG_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]*$")
FIELD_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
DIAGNOSTIC = re.compile(r"^[A-Z][A-Z0-9_]*$")
ACCESS_TYPES = {"runtime", "migration", "administrative"}
SERVER_OR_WORKER_TYPES = {"long-running-server", "continuous-worker"}
COMPLETION_TASK_TYPE = "run-to-completion-task"
UNSAFE_CONFIGURATION_KEYS = {
    "secret-value", "secret-values", "password", "passwords", "token",
    "tokens", "credential", "credentials", "connection-string",
    "connection-url", "database-url",
}
PROHIBITED_VALUE_PATTERNS = (
    re.compile(r"arn:aws(?:-[a-z]+)?:secretsmanager:", re.IGNORECASE),
    re.compile(r"(?:postgres|postgresql|mysql|mongodb)://[^\s]+", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|token|secret|credential)\s*=", re.IGNORECASE),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def load(path: Path) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return value if isinstance(value, dict) else None


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalized_key(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def contains_unsafe_value(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in PROHIBITED_VALUE_PATTERNS)
    if isinstance(value, list):
        return any(contains_unsafe_value(item) for item in value)
    if isinstance(value, dict):
        return any(
            (isinstance(key, str) and normalized_key(key) in UNSAFE_CONFIGURATION_KEYS)
            or contains_unsafe_value(item)
            for key, item in value.items()
        )
    return False


def text_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return None
    return value


def invalid_entry(entry: Any, workload_types: dict[str, str], declared_dependencies: set[str]) -> str | None:
    required = {
        "id", "dependency", "purpose", "owner", "authorised_workloads", "access_class",
        "injection_name", "target_reference_id", "expected_fields", "delivery",
        "access_grant", "rotation", "revocation", "retirement",
        "failure_behaviour", "safe_diagnostics",
    }
    if not isinstance(entry, dict) or set(entry) != required:
        return "secret-dependency-fields-invalid"
    if not all(text(entry[key]) for key in ("id", "dependency", "purpose", "owner", "injection_name", "target_reference_id")):
        return "secret-dependency-fields-invalid"
    if (
        IDENTIFIER.fullmatch(entry["id"]) is None
        or IDENTIFIER.fullmatch(entry["dependency"]) is None
        or IDENTIFIER.fullmatch(entry["target_reference_id"]) is None
        or entry["dependency"] not in declared_dependencies
    ):
        return "secret-dependency-reference-invalid"
    if CONFIG_NAME.fullmatch(entry["injection_name"]) is None:
        return "secret-dependency-injection-name-invalid"
    workloads = text_list(entry["authorised_workloads"])
    if workloads is None or not workloads or len(workloads) != len(set(workloads)) or any(item not in workload_types for item in workloads):
        return "secret-dependency-workload-invalid"
    access_class = entry["access_class"]
    if not isinstance(access_class, str) or access_class not in ACCESS_TYPES:
        return "secret-dependency-access-class-invalid"
    selected_types = {workload_types[item] for item in workloads}
    if access_class in {"migration", "administrative"} and selected_types != {COMPLETION_TASK_TYPE}:
        return "secret-dependency-access-class-workload-mismatch"
    if selected_types - SERVER_OR_WORKER_TYPES and selected_types != {COMPLETION_TASK_TYPE}:
        return "secret-dependency-workload-invalid"
    fields = text_list(entry["expected_fields"])
    if fields is None or not fields or len(fields) != len(set(fields)) or any(FIELD_NAME.fullmatch(field) is None for field in fields):
        return "secret-dependency-expected-fields-invalid"
    delivery, access_grant, rotation, revocation, retirement, failure, diagnostics = (
        entry["delivery"], entry["access_grant"], entry["rotation"], entry["revocation"],
        entry["retirement"], entry["failure_behaviour"], entry["safe_diagnostics"],
    )
    if not isinstance(delivery, dict) or delivery != {"method": "target-secret-store-injection", "phase": "workload-startup"}:
        return "secret-dependency-delivery-invalid"
    if (
        not isinstance(access_grant, dict)
        or set(access_grant) != {"owner", "policy", "privilege_boundary", "proof_requirement"}
        or not text(access_grant.get("owner"))
        or not text(access_grant.get("policy"))
        or access_grant.get("privilege_boundary") != "declared-access-class-boundary-not-effective-privilege-proof"
        or access_grant.get("proof_requirement") != "provider-binding-and-effective-access-observation-required"
    ):
        return "secret-dependency-access-grant-invalid"
    if (
        not isinstance(rotation, dict)
        or set(rotation) != {"owner", "policy", "application_behavior", "completed_task_behavior"}
        or not text(rotation.get("owner"))
        or not text(rotation.get("policy"))
        or rotation.get("application_behavior") != "replacement-required"
        or rotation.get("completed_task_behavior") != "no-replay"
    ):
        return "secret-dependency-rotation-invalid"
    if (
        not isinstance(revocation, dict)
        or set(revocation) != {"owner", "policy", "condition", "workload_effect", "proof_requirement"}
        or any(not text(revocation.get(key)) for key in ("owner", "policy", "condition"))
        or revocation.get("workload_effect") != "block-new-start-and-stop-active-authorised-workloads"
        or revocation.get("proof_requirement") != "delivery-and-dependency-access-denied-observation-required"
    ):
        return "secret-dependency-revocation-invalid"
    if not isinstance(retirement, dict) or set(retirement) != {"owner", "policy", "condition"} or any(not text(retirement.get(key)) for key in ("owner", "policy", "condition")):
        return "secret-dependency-retirement-invalid"
    if not isinstance(diagnostics, dict) or set(diagnostics) != {"unavailable", "invalid_shape", "credential_rejected", "access_denied"} or any(not isinstance(value, str) or DIAGNOSTIC.fullmatch(value) is None for value in diagnostics.values()):
        return "secret-dependency-diagnostics-invalid"
    if selected_types <= SERVER_OR_WORKER_TYPES:
        expected = {
            "startup": {"unavailable": "process-exits", "invalid_shape": "process-exits"},
            "readiness": {"unavailable": "block-readiness", "invalid_shape": "block-readiness"},
        }
        if failure != expected:
            return "secret-dependency-failure-behaviour-invalid"
    else:
        if not isinstance(failure, dict) or set(failure) != {"completion"}:
            return "secret-dependency-failure-behaviour-invalid"
        completion = failure["completion"]
        if not isinstance(completion, dict) or set(completion) != {"unavailable", "invalid_shape"}:
            return "secret-dependency-failure-behaviour-invalid"
        for concern in ("unavailable", "invalid_shape"):
            result = completion[concern]
            if not isinstance(result, dict) or result != {"outcome": "unsuccessful-completion", "diagnostic_code": diagnostics[concern]}:
                return "secret-dependency-failure-behaviour-invalid"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--scope-contract", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    codes: list[str] = ["secret-dependency-arguments-invalid"] if unknown else []
    document = load(args.scope_contract)
    if document is None:
        codes.append("scope-contract-unreadable")
    else:
        configuration = document.get("configuration")
        health = document.get("health_recovery")
        if not isinstance(configuration, dict):
            codes.append("secret-dependency-configuration-missing")
        elif any(isinstance(key, str) and normalized_key(key) in UNSAFE_CONFIGURATION_KEYS for key in configuration):
            codes.append("secret-dependency-unsafe-configuration-field")
        elif contains_unsafe_value(configuration):
            codes.append("secret-dependency-unsafe-value-or-reference")
        elif "secret_dependencies" not in configuration or not isinstance(configuration.get("secret_dependencies"), list) or not isinstance(configuration.get("secret_names"), list):
            codes.append("secret-dependency-declaration-missing")
        elif not isinstance(health, dict) or not isinstance(health.get("workloads"), list):
            codes.append("secret-dependency-workloads-missing")
        else:
            workload_types = {
                item.get("id"): item.get("workload_type")
                for item in health["workloads"]
                if isinstance(item, dict) and text(item.get("id")) and text(item.get("workload_type"))
            }
            dependencies = document.get("dependencies")
            required_dependencies = dependencies.get("required") if isinstance(dependencies, dict) else None
            optional_dependencies = dependencies.get("optional") if isinstance(dependencies, dict) else None
            if (
                not isinstance(required_dependencies, list)
                or not isinstance(optional_dependencies, list)
                or not all(text(item) for item in [*required_dependencies, *optional_dependencies])
            ):
                codes.append("secret-dependency-scope-dependencies-invalid")
                required_dependencies, optional_dependencies = [], []
            declared_dependencies = set(required_dependencies) | set(optional_dependencies)
            server_mediated_verifiers = {
                item.get("id"): item["server_mediated_dependency_proof"].get("dependency")
                for item in health["workloads"]
                if isinstance(item, dict)
                and text(item.get("id"))
                and isinstance(item.get("server_mediated_dependency_proof"), dict)
                and text(item["server_mediated_dependency_proof"].get("dependency"))
            }
            migration_executors = {
                item.get("id"): item["migration_execution"].get("dependency")
                for item in health["workloads"]
                if isinstance(item, dict)
                and text(item.get("id"))
                and isinstance(item.get("migration_execution"), dict)
                and text(item["migration_execution"].get("dependency"))
            }
            entries = configuration["secret_dependencies"]
            names = text_list(configuration["secret_names"])
            if names is None or len(names) != len(set(names)) or any(CONFIG_NAME.fullmatch(name) is None for name in names):
                codes.append("secret-dependency-names-invalid")
            entry_ids: set[str] = set()
            injection_names: set[str] = set()
            valid_entries: list[dict[str, Any]] = []
            for entry in entries:
                code = invalid_entry(entry, workload_types, declared_dependencies)
                if code:
                    codes.append(code)
                    continue
                valid_entries.append(entry)
                entry_ids.add(entry["id"])
                injection_names.add(entry["injection_name"])
                if any(
                    verifier_dependency == entry["dependency"] and verifier_id in entry["authorised_workloads"]
                    for verifier_id, verifier_dependency in server_mediated_verifiers.items()
                ):
                    codes.append("server-mediated-verifier-direct-secret-prohibited")
            if len(entry_ids) != len(entries) or len(injection_names) != len(entries):
                codes.append("secret-dependency-identity-duplicate")
            reference_entries: dict[str, list[dict[str, Any]]] = {}
            for entry in valid_entries:
                reference_entries.setdefault(entry["target_reference_id"], []).append(entry)
            for shared in reference_entries.values():
                if len(shared) < 2:
                    continue
                first = shared[0]
                workload_sets = [set(entry["authorised_workloads"]) for entry in shared]
                same_runtime_shape = all(
                    entry["access_class"] == "runtime"
                    and entry["dependency"] == first["dependency"]
                    and entry["expected_fields"] == first["expected_fields"]
                    for entry in shared
                )
                disjoint_workloads = all(not left.intersection(right) for index, left in enumerate(workload_sets) for right in workload_sets[index + 1:])
                if not same_runtime_shape or not disjoint_workloads:
                    codes.append("secret-dependency-shared-reference-invalid")
            if names is None or set(names) != injection_names:
                codes.append("secret-dependency-names-mismatch")
            for workload_id, dependency in migration_executors.items():
                if not any(
                    entry.get("access_class") == "migration"
                    and entry.get("dependency") == dependency
                    and workload_id in entry.get("authorised_workloads", [])
                    for entry in valid_entries
                ):
                    codes.append("migration-executor-credential-missing")
    report = {
        "schema": "deploy/secret-dependency-declaration-report/v1",
        "scope_contract": str(args.scope_contract),
        "verdict": "passed" if not codes else "failed",
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not codes else 1


if __name__ == "__main__":
    raise SystemExit(main())
