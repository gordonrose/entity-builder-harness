#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-health-failure-and-recovery-declaration.fixtures
#   version: 3
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-25"
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


def dependency_server_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    contract, binding = read(CONTRACT), read(BINDING)
    contract["id"] = "fixture-persistence-server"
    contract["dependencies"] = {"required": ["persistence"], "optional": []}
    server = contract["health_recovery"]["workloads"][0]
    server["proof"]["live_recovery"]["evidence_reference"] = "../30-release-evidence/rehearsals/accepted.yml"
    contract["health_recovery"]["workloads"][1]["proof"]["completion"]["evidence_reference"] = "../30-release-evidence/rehearsals/accepted.yml"
    server["readiness"]["depends_on"] = ["persistence"]
    server["dependency_failures"] = [{
        "dependency": "persistence",
        "unavailable": {"result": "not-ready", "diagnostic_code": "PERSISTENCE_DEPENDENCY_UNAVAILABLE"},
    }]
    server["health_signal_mapping"] = {
        "provider_replacement_signal": "liveness",
        "dependency_readiness_effect": "block-candidate-acceptance",
        "candidate_acceptance_signals": ["liveness", "readiness"],
    }
    binding["workloads"][0]["health_signal_mapping"] = copy.deepcopy(server["health_signal_mapping"])
    return contract, binding


def server_mediated_verifier(contract: dict[str, Any]) -> None:
    contract["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"] = {
        "dependency": "persistence",
        "target_workload": "core-server",
        "route_access": "private-application-route-only",
        "direct_dependency_credentials": "prohibited",
        "direct_dependency_network": "prohibited",
        "direct_dependency_connection_limit": 0,
        "proof_steps": [
            "create-and-commit-synthetic-record-through-target-workload",
            "replace-target-workload",
            "read-original-record-through-replacement-workload",
        ],
        "acceptance_record": {
            "identity": "stable-synthetic-acceptance-record",
            "equivalent_repeat": "return-original-record-without-duplicate",
            "concurrent_create": "exactly-one-record-preserve-original-facts",
            "conflicting_reuse": "reject-conflict-preserve-original-facts",
            "lost_response_after_commit": "reconcile-original-record-before-retry",
        },
        "cleanup": {
            "owner": "persistence-platform",
            "retention": "until-replacement-and-restore-proof-accepted",
            "abandoned_verifier_policy": "retain-for-governed-cleanup",
            "route": "server-mediated-governed-cleanup",
            "outcome": "delete-synthetic-record-only-after-retention",
        },
    }


def migration_workload(contract: dict[str, Any], binding: dict[str, Any]) -> None:
    server_mediated_verifier(contract)
    contract["health_recovery"]["workloads"].append({
        "id": "persistence-administration",
        "workload_type": "run-to-completion-task",
        "binding": "persistence-administration-task",
        "required_workloads": [],
        "completion": {
            "deadline_seconds": 300,
            "success": {"exit_code": 0, "result_code": "PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED"},
            "interruption": {"policy": "stop-and-escalate"},
            "retry_policy": "no-automatic-retries",
        },
        "administrative_execution": {
            "dependency": "persistence",
            "credential_access_class": "administrative",
            "runtime_identity_probe": {"dependency": "persistence", "credential_access_class": "runtime", "purpose": "effective-runtime-identity-privilege-proof"},
            "allowed_operations": ["observe-migration-state"],
        },
        "proof": {
            "local": {"status": "passed", "command": "scripts/04.deploy/administration-local-proof/script.sh"},
            "package": {"status": "passed", "command": "scripts/04.deploy/administration-package-proof/script.sh"},
            "completion": {"status": "passed", "evidence_reference": "../30-release-evidence/rehearsals/accepted.yml", "exit_code": 0, "result_code": "PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED", "fresh_after": "2026-10-22T18:40:03Z", "observed_at": "2026-10-22T18:41:22Z"},
        },
    })
    binding["workloads"].append({
        "id": "persistence-administration-task",
        "workload_type": "run-to-completion-task",
        "runtime_class": "task",
        "execution": {"kind": "compiled-entrypoint", "source_reference": "infra/04.deploy/03.product/entrypoints/persistence-administration.main.ts", "command_description": "node artifacts/persistence-administration.main.js"},
    })
    contract["health_recovery"]["workloads"].append({
        "id": "persistence-migration",
        "workload_type": "run-to-completion-task",
        "binding": "persistence-migration-task",
        "required_workloads": [],
        "completion": {
            "deadline_seconds": 300,
            "success": {"exit_code": 0, "result_code": "PERSISTENCE_MIGRATION_APPLIED"},
            "interruption": {"policy": "stop-and-escalate"},
            "retry_policy": "no-automatic-retries",
        },
        "migration_execution": {
            "dependency": "persistence",
            "credential_access_class": "migration",
            "manifest": {"ordering": "strictly-ascending-immutable-identifiers", "checksum": "required-before-execution"},
            "executor": "exactly-one",
            "lock_wait_seconds": 30,
            "execution_timeout_seconds": 240,
            "transaction_boundary": "per-migration-atomic-where-supported",
            "interruption_policy": "do-not-retry-uncertain-outcome",
            "unknown_outcome_policy": "block-release-require-fresh-state-observation",
            "fresh_state_observation": {
                "workload": "persistence-administration",
                "operation": "observe-migration-state",
                "replay_permitted_result": "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED",
                "receipt": "durable-task-receipt-required-before-retry",
            },
            "compatibility_strategy": "expand-deploy-verify-contract-later",
            "replay_handling": {
                "already_applied_checksum_match": "no-op-record-accepted-state",
                "checksum_mismatch": "block-release-require-fresh-state-observation",
                "concurrent_executor": "reject-before-apply",
            },
        },
        "proof": {
            "local": {"status": "passed", "command": "scripts/04.deploy/migration-local-proof/script.sh"},
            "package": {"status": "passed", "command": "scripts/04.deploy/migration-package-proof/script.sh"},
            "completion": {
                "status": "passed",
                "evidence_reference": "../30-release-evidence/rehearsals/accepted.yml",
                "exit_code": 0,
                "result_code": "PERSISTENCE_MIGRATION_APPLIED",
                "fresh_after": "2026-10-22T18:40:03Z",
                "observed_at": "2026-10-22T18:41:22Z",
            },
        },
    })
    binding["workloads"].append({
        "id": "persistence-migration-task",
        "workload_type": "run-to-completion-task",
        "runtime_class": "task",
        "execution": {
            "kind": "compiled-entrypoint",
            "source_reference": "platform/adapters/aws/persistence/postgresql/src/migrations.ts",
            "command_description": "node artifacts/persistence-migration.main.js",
        },
    })
    contract["health_recovery"]["persistence_recovery"] = {
        "server_replacement": {
            "verifier_workload": "private-release-verifier",
            "outcome": "original-record-survives-server-replacement",
            "proof_requirement": "required-before-persistence-scope-acceptance",
        },
        "image_rollback": {
            "predecessor": "persistence-capable-accepted-release",
            "schema_compatibility": "required",
            "permission_contract_compatibility": "required",
            "legacy_permission_facts": "not-an-automatic-rollback-candidate",
            "database_reversal": "prohibited",
            "prohibited_effects": ["re-broaden-runtime-grants", "inject-administrative-credentials-into-ordinary-migration", "restore-migration-history-write", "undo-revocation"],
            "proof_requirement": "required-before-persistence-scope-acceptance",
        },
        "isolated_database_restore": {
            "restore_target": "new-isolated-database",
            "verification": "isolated-application-reads-known-synthetic-record",
            "source_mutation": "prohibited",
            "proof_requirement": "required-before-persistence-scope-acceptance",
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

    missing_signal_mapping = copy.deepcopy(source_contract)
    del missing_signal_mapping["health_recovery"]["workloads"][0]["health_signal_mapping"]
    expect_failure(missing_signal_mapping, source_binding, "health-signal-mapping-missing")

    mismatched_signal_mapping = copy.deepcopy(source_binding)
    mismatched_signal_mapping["workloads"][0]["health_signal_mapping"]["provider_replacement_signal"] = "liveness"
    expect_failure(source_contract, mismatched_signal_mapping, "workload-binding-health-signal-mapping-mismatch")

    persistence_server, persistence_binding = dependency_server_contract()
    status, report = run(persistence_server, persistence_binding)
    if status != 0 or report["verdict"] != "passed":
        raise AssertionError(f"valid dependency-bearing server fixture failed: {report}")

    mediated_verifier = copy.deepcopy(persistence_server)
    server_mediated_verifier(mediated_verifier)
    status, report = run(mediated_verifier, persistence_binding)
    if status != 0 or report["verdict"] != "passed":
        raise AssertionError(f"valid server-mediated verifier fixture failed: {report}")

    migration_contract, migration_binding = dependency_server_contract()
    migration_workload(migration_contract, migration_binding)
    status, report = run(migration_contract, migration_binding)
    if status != 0 or report["verdict"] != "passed":
        raise AssertionError(f"valid migration declaration fixture failed: {report}")

    missing_recovery = copy.deepcopy(migration_contract)
    del missing_recovery["health_recovery"]["persistence_recovery"]
    expect_failure(missing_recovery, migration_binding, "persistence-recovery-missing")

    unsafe_image_rollback = copy.deepcopy(migration_contract)
    unsafe_image_rollback["health_recovery"]["persistence_recovery"]["image_rollback"]["database_reversal"] = "automatic"
    expect_failure(unsafe_image_rollback, migration_binding, "persistence-recovery-image-rollback-invalid")

    unsafe_permission_rollback = copy.deepcopy(migration_contract)
    unsafe_permission_rollback["health_recovery"]["persistence_recovery"]["image_rollback"]["prohibited_effects"] = []
    expect_failure(unsafe_permission_rollback, migration_binding, "persistence-recovery-image-rollback-invalid")

    source_mutating_restore = copy.deepcopy(migration_contract)
    source_mutating_restore["health_recovery"]["persistence_recovery"]["isolated_database_restore"]["source_mutation"] = "allowed"
    expect_failure(source_mutating_restore, migration_binding, "persistence-recovery-isolated-restore-invalid")

    wrong_replacement_verifier = copy.deepcopy(migration_contract)
    wrong_replacement_verifier["health_recovery"]["persistence_recovery"]["server_replacement"]["verifier_workload"] = "core-server"
    expect_failure(wrong_replacement_verifier, migration_binding, "persistence-recovery-server-replacement-invalid")

    concurrent_migration = copy.deepcopy(migration_contract)
    concurrent_migration["health_recovery"]["workloads"][3]["migration_execution"]["executor"] = "multiple"
    expect_failure(concurrent_migration, migration_binding, "migration-execution-executor-invalid")

    missing_lock_bound = copy.deepcopy(migration_contract)
    missing_lock_bound["health_recovery"]["workloads"][3]["migration_execution"]["lock_wait_seconds"] = 0
    expect_failure(missing_lock_bound, migration_binding, "migration-execution-lock-wait-invalid")

    unknown_retry = copy.deepcopy(migration_contract)
    unknown_retry["health_recovery"]["workloads"][3]["migration_execution"]["unknown_outcome_policy"] = "retry-automatically"
    expect_failure(unknown_retry, migration_binding, "migration-execution-unknown-outcome-policy-invalid")

    deadline_shorter_than_execution = copy.deepcopy(migration_contract)
    deadline_shorter_than_execution["health_recovery"]["workloads"][3]["completion"]["deadline_seconds"] = 30
    expect_failure(deadline_shorter_than_execution, migration_binding, "migration-execution-deadline-too-short")

    incompatible_migration = copy.deepcopy(migration_contract)
    incompatible_migration["health_recovery"]["workloads"][3]["migration_execution"]["compatibility_strategy"] = "contract-before-deploy"
    expect_failure(incompatible_migration, migration_binding, "migration-execution-compatibility-invalid")

    missing_replay_handling = copy.deepcopy(migration_contract)
    del missing_replay_handling["health_recovery"]["workloads"][3]["migration_execution"]["replay_handling"]
    expect_failure(missing_replay_handling, migration_binding, "migration-execution-replay-handling-invalid")

    checksum_mismatch_retry = copy.deepcopy(migration_contract)
    checksum_mismatch_retry["health_recovery"]["workloads"][3]["migration_execution"]["replay_handling"]["checksum_mismatch"] = "apply-anyway"
    expect_failure(checksum_mismatch_retry, migration_binding, "migration-execution-replay-handling-invalid")

    already_applied_replay = copy.deepcopy(migration_contract)
    already_applied_replay["health_recovery"]["workloads"][3]["migration_execution"]["replay_handling"]["already_applied_checksum_match"] = "apply-again"
    expect_failure(already_applied_replay, migration_binding, "migration-execution-replay-handling-invalid")

    concurrent_apply = copy.deepcopy(migration_contract)
    concurrent_apply["health_recovery"]["workloads"][3]["migration_execution"]["replay_handling"]["concurrent_executor"] = "wait-and-retry"

    missing_state_observer = copy.deepcopy(migration_contract)
    del missing_state_observer["health_recovery"]["workloads"][3]["migration_execution"]["fresh_state_observation"]
    expect_failure(missing_state_observer, migration_binding, "migration-execution-fresh-state-observation-invalid")

    wrong_state_observer = copy.deepcopy(migration_contract)
    wrong_state_observer["health_recovery"]["workloads"][3]["migration_execution"]["fresh_state_observation"]["workload"] = "private-release-verifier"
    expect_failure(wrong_state_observer, migration_binding, "migration-execution-fresh-state-observation-invalid")
    expect_failure(concurrent_apply, migration_binding, "migration-execution-replay-handling-invalid")

    direct_credentials = copy.deepcopy(mediated_verifier)
    direct_credentials["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["direct_dependency_credentials"] = "allowed"
    expect_failure(direct_credentials, persistence_binding, "server-mediated-dependency-proof-credential-boundary-invalid")

    direct_network = copy.deepcopy(mediated_verifier)
    direct_network["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["direct_dependency_network"] = "allowed"
    expect_failure(direct_network, persistence_binding, "server-mediated-dependency-proof-network-boundary-invalid")

    direct_connection = copy.deepcopy(mediated_verifier)
    direct_connection["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["direct_dependency_connection_limit"] = 1
    expect_failure(direct_connection, persistence_binding, "server-mediated-dependency-proof-connection-limit-invalid")

    missing_target = copy.deepcopy(mediated_verifier)
    missing_target["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["target_workload"] = "not-a-server"
    expect_failure(missing_target, persistence_binding, "server-mediated-dependency-proof-target-invalid")

    broken_sequence = copy.deepcopy(mediated_verifier)
    broken_sequence["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["proof_steps"] = ["read-original-record-through-replacement-workload"]
    expect_failure(broken_sequence, persistence_binding, "server-mediated-dependency-proof-sequence-invalid")

    missing_acceptance_record = copy.deepcopy(mediated_verifier)
    del missing_acceptance_record["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["acceptance_record"]
    expect_failure(missing_acceptance_record, persistence_binding, "server-mediated-dependency-proof-acceptance-record-invalid")

    duplicate_repeat = copy.deepcopy(mediated_verifier)
    duplicate_repeat["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["acceptance_record"]["equivalent_repeat"] = "create-another-record"
    expect_failure(duplicate_repeat, persistence_binding, "server-mediated-dependency-proof-acceptance-record-invalid")

    concurrent_duplicate = copy.deepcopy(mediated_verifier)
    concurrent_duplicate["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["acceptance_record"]["concurrent_create"] = "allow-multiple-records"
    expect_failure(concurrent_duplicate, persistence_binding, "server-mediated-dependency-proof-acceptance-record-invalid")

    conflicting_overwrite = copy.deepcopy(mediated_verifier)
    conflicting_overwrite["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["acceptance_record"]["conflicting_reuse"] = "overwrite-original-facts"
    expect_failure(conflicting_overwrite, persistence_binding, "server-mediated-dependency-proof-acceptance-record-invalid")

    blind_retry = copy.deepcopy(mediated_verifier)
    blind_retry["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["acceptance_record"]["lost_response_after_commit"] = "retry-create-without-reconciliation"
    expect_failure(blind_retry, persistence_binding, "server-mediated-dependency-proof-acceptance-record-invalid")

    premature_cleanup = copy.deepcopy(mediated_verifier)
    premature_cleanup["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["cleanup"]["retention"] = "until-replacement-proof-accepted"
    expect_failure(premature_cleanup, persistence_binding, "server-mediated-dependency-proof-cleanup-invalid")

    direct_cleanup = copy.deepcopy(mediated_verifier)
    direct_cleanup["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["cleanup"]["route"] = "direct-dependency-cleanup"
    expect_failure(direct_cleanup, persistence_binding, "server-mediated-dependency-proof-cleanup-invalid")

    silent_cleanup = copy.deepcopy(mediated_verifier)
    silent_cleanup["health_recovery"]["workloads"][1]["server_mediated_dependency_proof"]["cleanup"]["outcome"] = "delete-before-retention"
    expect_failure(silent_cleanup, persistence_binding, "server-mediated-dependency-proof-cleanup-invalid")

    readiness_replacement = copy.deepcopy(persistence_server)
    readiness_replacement["health_recovery"]["workloads"][0]["health_signal_mapping"]["provider_replacement_signal"] = "readiness"
    readiness_binding = copy.deepcopy(persistence_binding)
    readiness_binding["workloads"][0]["health_signal_mapping"] = copy.deepcopy(readiness_replacement["health_recovery"]["workloads"][0]["health_signal_mapping"])
    expect_failure(readiness_replacement, readiness_binding, "dependency-bearing-replacement-must-use-liveness")

    missing_acceptance = copy.deepcopy(persistence_server)
    missing_acceptance["health_recovery"]["workloads"][0]["health_signal_mapping"]["candidate_acceptance_signals"] = ["readiness"]
    missing_acceptance_binding = copy.deepcopy(persistence_binding)
    missing_acceptance_binding["workloads"][0]["health_signal_mapping"] = copy.deepcopy(missing_acceptance["health_recovery"]["workloads"][0]["health_signal_mapping"])
    expect_failure(missing_acceptance, missing_acceptance_binding, "health-signal-candidate-acceptance-invalid")

    no_bootstrap_basis = copy.deepcopy(source_contract)
    del no_bootstrap_basis["health_recovery"]["workloads"][0]["health_signal_mapping"]["dependency_free_replacement_basis"]
    no_bootstrap_basis_binding = copy.deepcopy(source_binding)
    no_bootstrap_basis_binding["workloads"][0]["health_signal_mapping"] = copy.deepcopy(no_bootstrap_basis["health_recovery"]["workloads"][0]["health_signal_mapping"])
    expect_failure(no_bootstrap_basis, no_bootstrap_basis_binding, "dependency-free-readiness-replacement-basis-missing")

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
