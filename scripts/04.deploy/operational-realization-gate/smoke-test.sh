#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-gate
#   version: 3
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove the generic Operational Realization Gate accepts complete graphs and rejects unsafe or provider-coupled contracts.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.deployment-realization-test
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
SCRIPT="scripts/04.deploy/operational-realization-gate/script.sh"
FIXTURES="scripts/04.deploy/operational-realization-gate/fixtures"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

expect_failure() {
  local expected_code="$1"
  shift
  local output
  if output="$("$@" 2>&1)"; then
    echo "ERROR: expected realization gate failure $expected_code" >&2
    exit 1
  fi
  if [[ "$output" != *"\"code\": \"$expected_code\""* ]]; then
    echo "ERROR: realization gate emitted an unexpected unsafe failure" >&2
    exit 1
  fi
}

python3 - <<'PY'
from pathlib import Path
import yaml

source = Path("scripts/04.deploy/operational-realization-gate/script.py").read_text(encoding="utf-8")
compile(source, "operational-realization-gate.py", "exec")
for path in (
    ".agentic/01.harness/templates/operational-realization-contract.v1.template.yml",
    ".agentic/01.harness/templates/operational-realization-contract.v1.schema.yml",
):
    if not isinstance(yaml.safe_load(Path(path).read_text(encoding="utf-8")), dict):
        raise SystemExit("ERROR: realization template/schema must be valid YAML mappings")
schema = yaml.safe_load(Path(".agentic/01.harness/templates/operational-realization-contract.v1.schema.yml").read_text(encoding="utf-8"))
guide = schema.get("companion_guide")
if not isinstance(schema.get("field_guide"), list) or not schema["field_guide"] or not isinstance(guide, str) or not Path(guide).is_file():
    raise SystemExit("ERROR: realization schema must provide a field guide and linked companion guide")
PY
contract_output="$(bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --validate-contract --json)"
if [[ "$contract_output" != *'"scope": "contract"'* || "$contract_output" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: explicit contract validation did not pass" >&2
  exit 1
fi

valid_output="$(bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$FIXTURES/valid-normalized-facts.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through recovery --json)"
if [[ "$valid_output" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: valid realization contract did not pass" >&2
  exit 1
fi

python3 - "$FIXTURES/valid-contract.yml" "$FIXTURES/preflight-normalized-facts.yml" "$TEMPORARY_DIRECTORY/runtime-bound-contract.yml" "$TEMPORARY_DIRECTORY/runtime-bound-facts.yml" <<'PY'
from pathlib import Path
import sys
import yaml

contract = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
facts = yaml.safe_load(Path(sys.argv[2]).read_text(encoding="utf-8"))
artifact = contract["artifacts"][0]
artifact.pop("immutable_reference")
artifact["immutable_reference_mode"] = "runtime-bound-sha256"
facts["artifact_bindings"] = [{
    "component_id": "delivery-artifact",
    "immutable_reference": "sha256:" + "b" * 64,
    "check_id": "artifact-binding-check",
    "timestamp": "2026-09-27T00:00:00Z",
    "verdict": "passed",
}]
Path(sys.argv[3]).write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
Path(sys.argv[4]).write_text(yaml.safe_dump(facts, sort_keys=False), encoding="utf-8")
PY
runtime_bound_output="$(bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/runtime-bound-contract.yml" --facts "$TEMPORARY_DIRECTORY/runtime-bound-facts.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through execution-preflight --json)"
if [[ "$runtime_bound_output" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: a runtime-bound candidate artifact must require and accept one safe immutable binding" >&2
  exit 1
fi
sed '/artifact_bindings:/,/verdict: passed/d' "$TEMPORARY_DIRECTORY/runtime-bound-facts.yml" > "$TEMPORARY_DIRECTORY/runtime-bound-facts-missing-binding.yml"
expect_failure "normalized-facts-fields-invalid" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/runtime-bound-contract.yml" --facts "$TEMPORARY_DIRECTORY/runtime-bound-facts-missing-binding.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through execution-preflight --json
sed 's/sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/latest/' "$TEMPORARY_DIRECTORY/runtime-bound-facts.yml" > "$TEMPORARY_DIRECTORY/runtime-bound-facts-mutable-binding.yml"
expect_failure "artifact-binding-invalid" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/runtime-bound-contract.yml" --facts "$TEMPORARY_DIRECTORY/runtime-bound-facts-mutable-binding.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through execution-preflight --json

python3 - "$FIXTURES/valid-contract.yml" "$TEMPORARY_DIRECTORY/no-async-setup.yml" <<'PY'
from pathlib import Path
import sys
import yaml

document = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
document["async_channels"] = []
document["execution_units"][0]["async_channels"] = []
document["edges"] = [
    edge for edge in document["edges"]
    if edge["from"] != "delivery-channel" and edge["to"] != "delivery-channel"
]
document["identities"].append({"id": "setup-identity", "permissions": ["prepare-state"]})
document["configuration_inputs"].append({"id": "setup-configuration", "required_fields": ["configuration-reference"], "optional_fields": [], "sensitivity": "secret-reference-only"})
document["connections"].append({"id": "setup-connection", "source": "setup-runner", "destination": "delivery-store", "transport_security": "verified"})
document["observability_profiles"].append({"id": "setup-observability", "required_facts": ["correlation-id", "outcome-category"]})
document["recovery_plans"].append({"id": "setup-recovery", "entry_condition": "prior-attempt-reached-failed-or-stopped-terminal-state", "cleanup": "reviewed-cleanup", "rollback": "reviewed-rollback"})
document["execution_units"].append({
    "id": "setup-runner",
    "artifact": "delivery-artifact",
    "identity": "setup-identity",
    "configuration_inputs": ["setup-configuration"],
    "connections": ["setup-connection"],
    "state_stores": ["delivery-store"],
    "async_channels": [],
    "observability_profile": "setup-observability",
    "recovery_plan": "setup-recovery",
})
document["edges"].extend([
    {"from": "setup-runner", "to": "delivery-artifact", "purpose": "executes"},
    {"from": "setup-runner", "to": "setup-identity", "purpose": "assumes"},
    {"from": "setup-runner", "to": "setup-configuration", "purpose": "reads-configuration"},
    {"from": "setup-runner", "to": "setup-connection", "purpose": "connects"},
    {"from": "setup-connection", "to": "delivery-store", "purpose": "reaches-state"},
    {"from": "setup-runner", "to": "delivery-store", "purpose": "persists"},
    {"from": "setup-runner", "to": "setup-observability", "purpose": "emits-safe-telemetry"},
    {"from": "setup-runner", "to": "setup-recovery", "purpose": "recovers"},
])
Path(sys.argv[2]).write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
PY
no_async_output="$(bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/no-async-setup.yml" --validate-contract --json)"
if [[ "$no_async_output" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: a non-queue execution unit with an explicit empty channel list must pass" >&2
  exit 1
fi
sed 's/async_channels: \[\]/async_channels: [delivery-channel]/' "$TEMPORARY_DIRECTORY/no-async-setup.yml" > "$TEMPORARY_DIRECTORY/unbound-async-setup.yml"
expect_failure "async_channels-entry-invalid" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/unbound-async-setup.yml" --validate-contract --json

preflight_output="$(bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$FIXTURES/preflight-normalized-facts.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through execution-preflight --json)"
if [[ "$preflight_output" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: complete preflight evidence did not pass before controlled execution" >&2
  exit 1
fi

expect_failure "arguments-invalid" bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --json
expect_failure "assumption-proof-unknown" bash "$SCRIPT" --contract "$FIXTURES/unknown-assumption.yml" --validate-contract --json

sed '/to: delivery-store, purpose: persists/d' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/undeclared-edge.yml"
expect_failure "undeclared-dependency-edge" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/undeclared-edge.yml" --validate-contract --json

sed 's/mode: reviewed-recovery-only/mode: automatic/' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/unsafe-retry.yml"
expect_failure "unsafe-retry-policy" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/unsafe-retry.yml" --validate-contract --json

sed '0,/id: delivery-store/s//id: aws-store/' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/provider-leakage.yml"
expect_failure "provider-specific-leakage" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/provider-leakage.yml" --validate-contract --json

sed '/sensitivity: secret-reference-only/a\    endpoint: unsafe-value' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/unsafe-value.yml"
expect_failure "unsafe-value-field-declared" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/unsafe-value.yml" --validate-contract --json

expect_failure "normalized-change-summary-required-for-gate" bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$FIXTURES/preflight-normalized-facts.yml" --through execution-preflight --json

sed '/contract_id: harmless-delivery-route/a token_value: sentinel' "$FIXTURES/valid-normalized-facts.yml" > "$TEMPORARY_DIRECTORY/unsafe-facts.yml"
expect_failure "unsafe-value-field-declared" bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$TEMPORARY_DIRECTORY/unsafe-facts.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through recovery --json

sed 's/check_id: source-check, //' "$FIXTURES/valid-normalized-facts.yml" > "$TEMPORARY_DIRECTORY/missing-check-id.yml"
expect_failure "normalized-facts-entry-fields-invalid" bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$TEMPORARY_DIRECTORY/missing-check-id.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through recovery --json

sed 's/timestamp: "2026-09-27T00:00:00Z", //' "$FIXTURES/valid-normalized-facts.yml" > "$TEMPORARY_DIRECTORY/missing-timestamp.yml"
expect_failure "normalized-facts-entry-fields-invalid" bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$TEMPORARY_DIRECTORY/missing-timestamp.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through recovery --json

sed '/component_id: delivery-identity/d' "$FIXTURES/valid-normalized-facts.yml" > "$TEMPORARY_DIRECTORY/missing-component-binding.yml"
expect_failure "component-evidence-incomplete" bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$TEMPORARY_DIRECTORY/missing-component-binding.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through recovery --json

sed 's/sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/latest/' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/mutable-artifact.yml"
expect_failure "artifact-immutable-reference-invalid" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/mutable-artifact.yml" --validate-contract --json

sed '/producer: delivery-worker/d' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/async-producer-missing.yml"
expect_failure "async-producer-invalid" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/async-producer-missing.yml" --validate-contract --json

sed '/^execution_units:/,$ s/async_channels: \[delivery-channel\]/async_channels: [missing-channel]/' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/async-channel-undeclared.yml"
expect_failure "execution-unit-references-undeclared-component" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/async-channel-undeclared.yml" --validate-contract --json

sed 's/source: delivery-worker/source: delivery-artifact/' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/connection-source-wrong-kind.yml"
expect_failure "connection-source-type-invalid" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/connection-source-wrong-kind.yml" --validate-contract --json

sed '/from: delivery-connection, to: delivery-store/d' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/connection-destination-edge-missing.yml"
expect_failure "connection-destination-edge-missing" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/connection-destination-edge-missing.yml" --validate-contract --json

sed 's/recovery_attempt_label: recovery-attempt/recovery_attempt_label: prior-attempt/' "$FIXTURES/valid-normalized-facts.yml" > "$TEMPORARY_DIRECTORY/recovery-replay.yml"
expect_failure "recovery-label-not-new" bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$TEMPORARY_DIRECTORY/recovery-replay.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through recovery --json

REALIZATION_SOURCES=(
  scripts/04.deploy/operational-realization-gate/script.py
  scripts/04.deploy/operational-realization-gate/release_compiler.py
  scripts/04.deploy/operational-realization-gate/source_coverage.py
  scripts/04.deploy/operational-realization-gate/caller_coverage.py
  scripts/04.deploy/operational-realization-gate/finding_triage.py
  scripts/04.deploy/operational-realization-gate/result_consumption.py
  scripts/04.deploy/operational-realization-gate/result_consumption_cli.py
  scripts/04.deploy/operational-realization-gate/operation_contracts.py
  scripts/04.deploy/operational-realization-gate/operation_contracts_cli.py
  scripts/04.deploy/operational-realization-gate/build_contracts.py
  scripts/04.deploy/operational-realization-gate/local_build_contracts.py
  scripts/04.deploy/operational-realization-gate/local_container_contracts.py
  scripts/04.deploy/operational-realization-gate/finite_job_contracts.py
  scripts/04.deploy/operational-realization-gate/dependency_effect_contracts.py
  scripts/04.deploy/operational-realization-gate/build_contracts_cli.py
  scripts/04.deploy/release-control/compiler.py
  scripts/04.deploy/release-control/discovery/source_inventory.py
  scripts/04.deploy/release-control/discovery/cloudformation_inventory.py
  scripts/04.deploy/release-control/discovery/caller_inventory.py
  scripts/04.deploy/release-control/discovery/operation_inventory.py
  scripts/04.deploy/release-control/discovery/action_observations.py
  scripts/04.deploy/release-control/discovery/build_inventory.py
  scripts/04.deploy/release-control/discovery/build_artifacts.py
  scripts/04.deploy/release-control/discovery/package_export_inventory.py
  scripts/04.deploy/operational-realization-gate/package_exports.py
)
if grep -Eq -- '(^|[[:space:]])(import|from)[[:space:]]+(platform\.adapters|boto|azure|oci|oracle)' "${REALIZATION_SOURCES[@]}"; then
  echo "ERROR: provider adapter import leaked into generic realization core" >&2
  exit 1
fi
if grep -Eq -- 'subprocess|socket|urllib|requests' "${REALIZATION_SOURCES[@]}"; then
  echo "ERROR: generic realization core must not invoke network or provider tooling" >&2
  exit 1
fi
# A missing/empty suite must fail instead of unittest discovery passing zero tests.
run_unit_suite() {
  PYTHONDONTWRITEBYTECODE=1 python3 - "$1" "$2" <<'PY_SUITE'
from pathlib import Path
import sys
import unittest

root, pattern = sys.argv[1:]
if not (Path(root) / pattern).is_file():
    raise SystemExit("ERROR: required realization test suite is missing")
suite = unittest.defaultTestLoader.discover(root, pattern=pattern)
if suite.countTestCases() == 0:
    raise SystemExit("ERROR: required realization test suite is empty")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
PY_SUITE
}

run_unit_suite scripts/04.deploy/operational-realization-gate 'test_release_compiler.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_selected_blueprint.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_blueprint_cli.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_selected_readiness.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_selected_readiness_cli.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_source_coverage.py'
run_unit_suite scripts/04.deploy/release-control/discovery 'test_source_inventory.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_finding_triage.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_caller_coverage.py'
run_unit_suite scripts/04.deploy/release-control/discovery 'test_caller_inventory.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_result_consumption.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_result_consumption_cli.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_clean_environment.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_validation_workflow.py'
run_unit_suite scripts/04.deploy/release-control/discovery 'test_operation_inventory.py'
run_unit_suite scripts/04.deploy/release-control/discovery 'test_action_observations.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_operation_contracts.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_operation_contracts_cli.py'
run_unit_suite scripts/04.deploy/release-control/discovery 'test_build_inventory.py'
run_unit_suite scripts/04.deploy/release-control/discovery 'test_build_artifacts.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_build_contracts_cli.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_local_build.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_locked_toolchain.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_local_runtime.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_typescript_emissions.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_package_exports.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_package_exports_cli.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_workspace_runtime.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_workspace_export_authority.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_local_build_bindings.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_container_engine.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_container_payload.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_container_profiles.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_local_container_contracts.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_container_emission_compatibility.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_local_container_cli.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_qualified_publication.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_qualified_publication_workflow.py'
run_unit_suite scripts/04.deploy/run-platform-shell-postgresql-relational-smoke 'test_preflight_contract.py'
run_unit_suite scripts/04.deploy/run-platform-shell-postgresql-relational-smoke 'test_task_revision_binding.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_finite_job_contracts.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_finite_job_engine.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_finite_job_conformance.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_dependency_effect_contracts.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_dependency_effect_engine.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_dependency_effects.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_dependency_preflights.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_artifact_admission.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_artifact_verifier.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_artifact_admission_cli.py'
run_unit_suite scripts/04.deploy/release-control/discovery 'test_cloudformation_inventory.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_cloudformation_coverage.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_dependency_target_boundary.py'

run_unit_suite scripts/04.deploy/operational-realization-gate 'test_operation_journal.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_selected_operation.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_selected_store.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_local_control_store.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_control_store_conformance.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_control_store_cli.py'
run_unit_suite scripts/04.deploy/release-control/discovery 'test_estate_caller_inventory.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_estate_caller_coverage.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_adoption_migration.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_estate_caller_cli.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_operation_actions.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_finite_recovery_engine.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_finite_recovery_controller.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_finite_recovery_conformance.py'
run_unit_suite scripts/04.deploy/operational-realization-gate 'test_finite_recovery_cli.py'

echo "Operational Realization Gate local tests passed."
