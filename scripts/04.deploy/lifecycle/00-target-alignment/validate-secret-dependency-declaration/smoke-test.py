#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-secret-dependency-declaration
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.secret-management
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Exercise valid and invalid portable secret dependency declaration shapes without secret values or provider calls.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.validate-secret-dependency-declaration.wrapper
#     path: scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/smoke-test.sh
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
CHECK = ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.sh"
SOURCE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml"
TEMPLATE = ROOT / ".agentic/04.deploy/00-target-alignment/schemas/secret-dependency-contract.v1.template.yml"


def run(path: Path) -> tuple[int, dict[str, Any]]:
    result = subprocess.run([str(CHECK), "--scope-contract", str(path), "--json"], capture_output=True, text=True, check=False)
    return result.returncode, json.loads(result.stdout)


def expect_failure(value: dict[str, Any], code: str, directory: Path) -> None:
    path = directory / f"{code}.yml"
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    status, report = run(path)
    assert status != 0 and code in {item["code"] for item in report["findings"]}, report


def expect_pass(value: dict[str, Any], directory: Path, name: str) -> None:
    path = directory / f"{name}.yml"
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    status, report = run(path)
    assert status == 0 and report["verdict"] == "passed", report


def workload(identifier: str, workload_type: str) -> dict[str, str]:
    return {"id": identifier, "workload_type": workload_type}


def server_failure() -> dict[str, Any]:
    return {
        "startup": {"unavailable": "process-exits", "invalid_shape": "process-exits"},
        "readiness": {"unavailable": "block-readiness", "invalid_shape": "block-readiness"},
    }


def completion_failure() -> dict[str, Any]:
    return {
        "completion": {
            "unavailable": {"outcome": "unsuccessful-completion", "diagnostic_code": "DEPENDENCY_SECRET_UNAVAILABLE"},
            "invalid_shape": {"outcome": "unsuccessful-completion", "diagnostic_code": "DEPENDENCY_SECRET_SHAPE_INVALID"},
        },
    }


def secret_entry(identifier: str, access_class: str, authorised_workloads: list[str], failure: dict[str, Any]) -> dict[str, Any]:
    injection = f"{identifier.upper().replace('-', '_')}_SECRET_JSON"
    return {
        "id": identifier,
        "purpose": "authenticate-declared-workload-to-declared-dependency",
        "owner": "persistence-platform",
        "authorised_workloads": authorised_workloads,
        "access_class": access_class,
        "injection_name": injection,
        "target_reference_id": identifier,
        "expected_fields": ["username", "password"],
        "delivery": {"method": "target-secret-store-injection", "phase": "workload-startup"},
        "rotation": {"owner": "persistence-platform", "policy": "governed-rotation", "application_behavior": "replacement-required"},
        "retirement": {"owner": "persistence-platform", "policy": "governed-revocation-and-removal", "condition": "after-dependent-workload-retirement"},
        "failure_behaviour": failure,
        "safe_diagnostics": {"unavailable": "DEPENDENCY_SECRET_UNAVAILABLE", "invalid_shape": "DEPENDENCY_SECRET_SHAPE_INVALID", "credential_rejected": "DEPENDENCY_CREDENTIAL_REJECTED", "access_denied": "DEPENDENCY_ACCESS_DENIED"},
    }


def scope_with(baseline: dict[str, Any], workloads: list[dict[str, str]], entries: list[dict[str, Any]]) -> dict[str, Any]:
    value = copy.deepcopy(baseline)
    value["health_recovery"]["workloads"] = workloads
    value["configuration"]["secret_dependencies"] = entries
    value["configuration"]["secret_names"] = [entry["injection_name"] for entry in entries]
    return value


def main() -> int:
    baseline = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    assert isinstance(baseline, dict)
    status, report = run(SOURCE)
    assert status == 0 and report["verdict"] == "passed", report
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        template = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
        assert isinstance(template, dict)
        template_scope = copy.deepcopy(baseline)
        template_scope["configuration"] = template["configuration"]
        template_scope["health_recovery"]["workloads"] = [workload("example-server", "long-running-server")]
        expect_pass(template_scope, directory, "template")

        runtime_task = scope_with(
            baseline,
            [workload("persistence-verifier", "run-to-completion-task")],
            [secret_entry("verifier-runtime-credential", "runtime", ["persistence-verifier"], completion_failure())],
        )
        expect_pass(runtime_task, directory, "runtime-task")

        shared_runtime = scope_with(
            baseline,
            [workload("core-server", "long-running-server"), workload("core-worker", "continuous-worker")],
            [secret_entry("shared-runtime-credential", "runtime", ["core-server", "core-worker"], server_failure())],
        )
        expect_pass(shared_runtime, directory, "shared-server-worker-runtime")
        for access_class in ("migration", "administrative"):
            privileged_shared = copy.deepcopy(shared_runtime)
            privileged_shared["configuration"]["secret_dependencies"][0]["access_class"] = access_class
            expect_failure(privileged_shared, "secret-dependency-access-class-workload-mismatch", directory)
        mixed_lifecycles = copy.deepcopy(shared_runtime)
        mixed_lifecycles["health_recovery"]["workloads"].append(workload("persistence-verifier", "run-to-completion-task"))
        mixed_lifecycles["configuration"]["secret_dependencies"][0]["authorised_workloads"].append("persistence-verifier")
        expect_failure(mixed_lifecycles, "secret-dependency-workload-invalid", directory)

        privileged_tasks = scope_with(
            baseline,
            [workload("persistence-migration", "run-to-completion-task"), workload("persistence-admin", "run-to-completion-task")],
            [
                secret_entry("migration-credential", "migration", ["persistence-migration"], completion_failure()),
                secret_entry("administrative-credential", "administrative", ["persistence-admin"], completion_failure()),
            ],
        )
        expect_pass(privileged_tasks, directory, "privileged-tasks")

        missing = copy.deepcopy(baseline)
        missing["configuration"].pop("secret_dependencies")
        expect_failure(missing, "secret-dependency-declaration-missing", directory)
        mismatch = copy.deepcopy(baseline)
        mismatch["configuration"]["secret_names"] = ["EXAMPLE_RUNTIME_SECRET_JSON"]
        expect_failure(mismatch, "secret-dependency-names-mismatch", directory)
        migration_server = scope_with(
            baseline, [workload("core-server", "long-running-server")],
            [secret_entry("migration-credential", "migration", ["core-server"], server_failure())],
        )
        expect_failure(migration_server, "secret-dependency-access-class-workload-mismatch", directory)
        administrative_worker = scope_with(
            baseline, [workload("core-worker", "continuous-worker")],
            [secret_entry("administrative-credential", "administrative", ["core-worker"], server_failure())],
        )
        expect_failure(administrative_worker, "secret-dependency-access-class-workload-mismatch", directory)
        task_readiness = copy.deepcopy(runtime_task)
        task_readiness["configuration"]["secret_dependencies"][0]["failure_behaviour"] = server_failure()
        expect_failure(task_readiness, "secret-dependency-failure-behaviour-invalid", directory)
        unsupported_refresh = copy.deepcopy(runtime_task)
        unsupported_refresh["configuration"]["secret_dependencies"][0]["rotation"]["application_behavior"] = "live-refresh-proven"
        expect_failure(unsupported_refresh, "secret-dependency-rotation-invalid", directory)
        unsafe_purpose = copy.deepcopy(runtime_task)
        unsafe_purpose["configuration"]["secret_dependencies"][0]["purpose"] = "use postgresql://synthetic-user:synthetic-password@database.example/test"
        expect_failure(unsafe_purpose, "secret-dependency-unsafe-value-or-reference", directory)
        unsafe_configuration = copy.deepcopy(runtime_task)
        unsafe_configuration["configuration"]["secret_values"] = {"synthetic": "not-allowed"}
        expect_failure(unsafe_configuration, "secret-dependency-unsafe-configuration-field", directory)
        unsafe_entry_field = copy.deepcopy(runtime_task)
        unsafe_entry_field["configuration"]["secret_dependencies"][0]["password"] = "synthetic-not-a-real-secret"
        expect_failure(unsafe_entry_field, "secret-dependency-unsafe-value-or-reference", directory)
        unsafe_policy = copy.deepcopy(runtime_task)
        unsafe_policy["configuration"]["secret_dependencies"][0]["rotation"]["policy"] = "arn:aws:secretsmanager:eu-west-1:111122223333:secret:synthetic"
        expect_failure(unsafe_policy, "secret-dependency-unsafe-value-or-reference", directory)
        unsafe_numeric_key = copy.deepcopy(runtime_task)
        unsafe_numeric_key["configuration"][7] = {"note": "postgresql://synthetic-user:synthetic-password@database.example/test"}
        expect_failure(unsafe_numeric_key, "secret-dependency-unsafe-value-or-reference", directory)
        unsafe_nested_key = copy.deepcopy(runtime_task)
        unsafe_nested_key["configuration"]["notes"] = {None: [{"token": "synthetic-only"}]}
        expect_failure(unsafe_nested_key, "secret-dependency-unsafe-value-or-reference", directory)
        for access_class in ([], {}):
            malformed_access_class = copy.deepcopy(runtime_task)
            malformed_access_class["configuration"]["secret_dependencies"][0]["access_class"] = access_class
            expect_failure(malformed_access_class, "secret-dependency-access-class-invalid", directory)
        malformed_names = copy.deepcopy(runtime_task)
        malformed_names["configuration"]["secret_names"] = [{"name": "NOT_A_NAME"}]
        expect_failure(malformed_names, "secret-dependency-names-invalid", directory)
        malformed_workloads = copy.deepcopy(runtime_task)
        malformed_workloads["configuration"]["secret_dependencies"][0]["authorised_workloads"] = [{"id": "persistence-verifier"}]
        expect_failure(malformed_workloads, "secret-dependency-workload-invalid", directory)
        malformed_fields = copy.deepcopy(runtime_task)
        malformed_fields["configuration"]["secret_dependencies"][0]["expected_fields"] = ["username", {"field": "password"}]
        expect_failure(malformed_fields, "secret-dependency-expected-fields-invalid", directory)
    print("Secret dependency declaration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
