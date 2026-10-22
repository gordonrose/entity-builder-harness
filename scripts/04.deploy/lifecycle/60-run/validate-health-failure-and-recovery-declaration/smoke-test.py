#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-health-failure-and-recovery-declaration.fixtures
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Exercise provider-neutral server, worker, task, binding, and completion-freshness health/recovery fixtures.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.validate-health-failure-and-recovery-declaration
#     path: scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/smoke-test.sh
"""Focused fixtures for workload-type-aware health/recovery validation."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
CHECK = ROOT / "scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.sh"
CONTRACT = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml"
BINDING = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/10-workload-binding/workload-binding.yml"


def read(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def run(contract: dict[str, Any], binding: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "20-scopes" / "fixture"
        declaration = root / "00-declaration" / "declaration-contract.yml"
        workload_binding = root / "10-workload-binding" / "workload-binding.yml"
        evidence = root / "30-release-evidence" / "rehearsals" / "accepted.yml"
        declaration.parent.mkdir(parents=True)
        workload_binding.parent.mkdir(parents=True)
        evidence.parent.mkdir(parents=True)
        evidence.write_text("schema: fixture/evidence/v1\n", encoding="utf-8")
        yaml.safe_dump(contract, declaration.open("w", encoding="utf-8"), sort_keys=False)
        yaml.safe_dump(binding, workload_binding.open("w", encoding="utf-8"), sort_keys=False)
        result = subprocess.run(
            [str(CHECK), "--scope-contract", str(declaration), "--workload-binding", str(workload_binding), "--json"],
            check=False,
            capture_output=True,
            text=True,
        )
    return result.returncode, json.loads(result.stdout)


def expect_failure(contract: dict[str, Any], binding: dict[str, Any], code: str) -> None:
    status, report = run(contract, binding)
    if status == 0 or code not in {item["code"] for item in report["findings"]}:
        raise AssertionError(f"expected {code}, received {report}")


def worker_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    contract = {
        "schema": "deploy/target-scope-contract/v1",
        "id": "fixture-worker",
        "dependencies": {"required": [], "optional": []},
        "health_recovery": {
            "declaration_schema": "deploy/health-failure-and-recovery-declaration/v2",
            "workloads": [{
                "id": "worker",
                "workload_type": "continuous-worker",
                "binding": "worker-task",
                "startup_failure": {"invalid_required_configuration": {"result": "process-exits", "diagnostic_code": "CONFIGURATION_INVALID"}},
                "dependency_failures": [],
                "progress_health": {"mechanism": "safe-heartbeat-counter", "maximum_silence_seconds": 60},
                "shutdown": {"policy": "stop-intake-and-finish-safe-work"},
                "interrupted_work": {"policy": "resume-idempotent-work-only"},
                "automatic_workload_recovery": {"owner": "orchestrator", "unhealthy_workload": "replace", "prohibited_automatic_actions": ["replay-uncertain-operation"]},
                "release_recovery": {"strategy": "restore-prior-accepted-immutable-release", "automatic_restore": "prohibited", "verification": "repeat-declared-health-and-meaningful-operation"},
                "proof": {
                    "local": {"status": "passed", "command": "scripts/04.deploy/local-proof/script.sh"},
                    "package": {"status": "passed", "command": "scripts/04.deploy/package-proof/script.sh"},
                    "live_recovery": {"status": "planned", "owner": "platform-runtime", "follow_up": "run-governed-recovery", "review_before": "release-acceptance"},
                },
            }],
        },
    }
    binding = {"workloads": [{
        "id": "worker-task",
        "workload_type": "continuous-worker",
        "runtime_class": "task",
        "execution": {
            "kind": "compiled-entrypoint",
            "source_reference": "platform/workers/src/worker.main.ts",
            "command_description": "node artifacts/worker.main.js",
        },
    }]}
    return contract, binding


def legacy_server_contract() -> dict[str, Any]:
    return {
        "schema": "deploy/target-scope-contract/v1",
        "id": "fixture-legacy-server",
        "dependencies": {"required": [], "optional": []},
        "health_recovery": {
            "declaration_schema": "deploy/health-recovery-declaration/v1",
            "liveness": {"path": "/livez", "expected_status": 200},
            "readiness": {"path": "/readyz", "expected_status": 200, "depends_on": []},
            "startup_failure": {"invalid_required_configuration": {"result": "process-exits", "diagnostic_code": "CONFIGURATION_INVALID"}},
            "dependency_failures": [],
            "automatic_workload_recovery": {"owner": "orchestrator", "unhealthy_workload": "replace", "prohibited_automatic_actions": ["replay-uncertain-operation"]},
            "release_recovery": {"strategy": "restore-prior-accepted-immutable-release", "automatic_restore": "prohibited", "verification": "repeat-declared-health-and-meaningful-operation"},
            "proof": {
                "local": {"status": "passed", "command": "scripts/04.deploy/local-proof/script.sh"},
                "package": {"status": "passed", "command": "scripts/04.deploy/package-proof/script.sh"},
                "live_recovery": {"status": "planned", "owner": "platform-runtime", "follow_up": "run-governed-recovery", "review_before": "release-acceptance"},
            },
        },
    }


def main() -> int:
    source_contract, source_binding = read(CONTRACT), read(BINDING)
    direct = subprocess.run([str(CHECK), "--scope-contract", str(CONTRACT), "--workload-binding", str(BINDING), "--json"], check=False, capture_output=True, text=True)
    if direct.returncode != 0:
        raise AssertionError(f"accepted bootstrap declaration failed: {direct.stdout}")

    worker, worker_binding = worker_contract()
    status, report = run(worker, worker_binding)
    if status != 0 or report["verdict"] != "passed":
        raise AssertionError(f"valid worker fixture failed: {report}")

    unknown = copy.deepcopy(source_contract)
    unknown["health_recovery"]["workloads"][0]["workload_type"] = "unknown"
    expect_failure(unknown, source_binding, "workload-type-invalid")

    missing = copy.deepcopy(source_contract)
    del missing["health_recovery"]["workloads"][1]["completion"]
    expect_failure(missing, source_binding, "task-completion-missing")

    missing_server_health = copy.deepcopy(source_contract)
    del missing_server_health["health_recovery"]["workloads"][0]["readiness"]
    expect_failure(missing_server_health, source_binding, "readiness-missing")

    empty_startup = copy.deepcopy(source_contract)
    empty_startup["health_recovery"]["workloads"][0]["startup_failure"] = {}
    expect_failure(empty_startup, source_binding, "startup-invalid-configuration-missing")

    empty_recovery = copy.deepcopy(source_contract)
    empty_recovery["health_recovery"]["workloads"][0]["automatic_workload_recovery"] = {}
    expect_failure(empty_recovery, source_binding, "automatic-workload-recovery-invalid")

    empty_local_proof = copy.deepcopy(source_contract)
    empty_local_proof["health_recovery"]["workloads"][0]["proof"]["local"] = {}
    expect_failure(empty_local_proof, source_binding, "proof-local-invalid")

    empty_completion = copy.deepcopy(source_contract)
    empty_completion["health_recovery"]["workloads"][1]["completion"] = {}
    expect_failure(empty_completion, source_binding, "task-success-criteria-missing")

    empty_worker_progress, worker_binding = worker_contract()
    empty_worker_progress["health_recovery"]["workloads"][0]["progress_health"] = {}
    expect_failure(empty_worker_progress, worker_binding, "worker-progress-health-invalid")

    empty_worker_shutdown, worker_binding = worker_contract()
    empty_worker_shutdown["health_recovery"]["workloads"][0]["shutdown"] = {}
    expect_failure(empty_worker_shutdown, worker_binding, "worker-shutdown-invalid")

    empty_worker_interrupted, worker_binding = worker_contract()
    empty_worker_interrupted["health_recovery"]["workloads"][0]["interrupted_work"] = {}
    expect_failure(empty_worker_interrupted, worker_binding, "worker-interrupted-work-invalid")

    empty_legacy_startup = legacy_server_contract()
    empty_legacy_startup["health_recovery"]["startup_failure"] = {}
    expect_failure(empty_legacy_startup, {}, "startup-invalid-configuration-missing")

    mismatch = copy.deepcopy(source_binding)
    mismatch["workloads"][1]["workload_type"] = "continuous-worker"
    expect_failure(source_contract, mismatch, "workload-binding-type-mismatch")

    runtime_class_mismatch = copy.deepcopy(source_binding)
    runtime_class_mismatch["workloads"][0]["runtime_class"] = "task"
    expect_failure(source_contract, runtime_class_mismatch, "workload-binding-runtime-class-mismatch")

    missing_execution = copy.deepcopy(source_binding)
    del missing_execution["workloads"][0]["execution"]
    expect_failure(source_contract, missing_execution, "workload-execution-missing")

    stale = copy.deepcopy(source_contract)
    stale["health_recovery"]["workloads"][1]["proof"]["completion"]["observed_at"] = "2026-10-21T15:55:41Z"
    expect_failure(stale, source_binding, "proof-completion-stale")

    unsuitable = copy.deepcopy(source_contract)
    unsuitable["health_recovery"]["workloads"][1]["proof"]["completion"]["exit_code"] = 1
    expect_failure(unsuitable, source_binding, "proof-completion-result-invalid")

    type_change = copy.deepcopy(source_contract)
    type_change_binding = copy.deepcopy(source_binding)
    type_change["health_recovery"]["workloads"][1]["workload_type"] = "continuous-worker"
    type_change_binding["workloads"][1]["workload_type"] = "continuous-worker"
    expect_failure(type_change, type_change_binding, "worker-progress-health-missing")

    print("Health, failure, and recovery declaration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
