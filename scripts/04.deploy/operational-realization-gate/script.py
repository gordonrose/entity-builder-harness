#!/usr/bin/env python3
"""Compile a provider-neutral Operational Realization Contract into safe results."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-gate
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Fail closed on incomplete provider-neutral realization contracts and normalized evidence.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: harness.workflow.operational-realization-gate
#     path: .agentic/01.harness/workflows/operational-realization-gate.md

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

import yaml


RESULT_SCHEMA = "operational-realization-gate-result/v1"
CONTRACT_SCHEMA = "operational-realization-contract/v1"
FACTS_SCHEMA = "operational-realization-normalized-facts/v1"
CHANGE_SCHEMA = "operational-realization-normalized-change-summary/v1"
GATE_ORDER = (
    "source",
    "artifact",
    "semantic-integration",
    "live-read",
    "change-set",
    "execution-preflight",
    "controlled-execution",
    "recovery",
)
PROOF_RANK = {
    "declared": 1,
    "locally-proven": 2,
    "live-read-proven": 3,
    "live-execution-proven": 4,
}
COMPONENTS = {
    "artifacts": ("artifact",),
    "identities": ("identity",),
    "configuration_inputs": ("configuration",),
    "connections": ("connection",),
    "state_stores": ("state-store",),
    "async_channels": ("async-channel",),
    "observability_profiles": ("observability-profile",),
    "recovery_plans": ("recovery-plan",),
    "execution_units": ("execution-unit",),
}
UNIT_REFERENCES = {
    "artifact": "artifacts",
    "identity": "identities",
    "configuration_inputs": "configuration_inputs",
    "connections": "connections",
    "state_stores": "state_stores",
    "async_channels": "async_channels",
    "observability_profile": "observability_profiles",
    "recovery_plan": "recovery_plans",
}
SENSITIVE_VALUE_KEYS = {"value", "content", "secret_value", "token_value", "password_value", "raw"}
UNSAFE_CONTRACT_KEYS = re.compile(r"^(secret|token|password|authorization|header|body|endpoint|connection[-_]string|credential)$", re.IGNORECASE)
# This boundary vocabulary is only a reject-list. It is not an SDK, resource
# model, import, or adapter dependency; provider adapters live outside this core.
PROVIDER_LEAKAGE = re.compile(
    r"\b(aws|azure|oracle|cloudformation|resource-manager|arm-template|"
    r"ec2|ecs|rds|sqs|eventbridge|cognito|iam|azure-resource|oci)\b",
    flags=re.IGNORECASE,
)
SAFE_ID = re.compile(r"^[a-z][a-z0-9-]{2,127}$")


class ContractFailure(Exception):
    """An expected safe validation failure with no provider data."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--contract")
    parser.add_argument("--facts")
    parser.add_argument("--change-summary")
    parser.add_argument("--through", choices=GATE_ORDER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help", action="store_true")
    parsed, unknown = parser.parse_known_args()
    if parsed.help:
        print("Usage: script.py --contract <provider-neutral-contract.yml> [--facts <normalized-facts.yml>] [--change-summary <normalized-change-summary.yml>] [--json]")
        raise SystemExit(0)
    if unknown or not parsed.contract:
        raise ContractFailure("arguments-invalid")
    return parsed


def safe_mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractFailure(code)
    return value


def safe_list(value: Any, code: str, non_empty: bool = True) -> list[Any]:
    if not isinstance(value, list) or (non_empty and not value):
        raise ContractFailure(code)
    return value


def safe_string(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractFailure(code)
    return value


def load_yaml(path_text: str, code: str) -> dict[str, Any]:
    try:
        path = Path(path_text)
        source = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as error:  # Do not disclose path, parser, or provider detail.
        raise ContractFailure(code) from error
    return safe_mapping(source, code)


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def reject_provider_leakage(value: Any) -> None:
    if any(PROVIDER_LEAKAGE.search(item) for item in strings(value)):
        raise ContractFailure("provider-specific-leakage")


def reject_unsafe_value_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if UNSAFE_CONTRACT_KEYS.fullmatch(str(key)):
                raise ContractFailure("unsafe-value-field-declared")
            reject_unsafe_value_fields(item)
    elif isinstance(value, list):
        for item in value:
            reject_unsafe_value_fields(item)


def ids(contract: dict[str, Any]) -> tuple[dict[str, set[str]], dict[str, str]]:
    groups: dict[str, set[str]] = {}
    kinds: dict[str, str] = {}
    for field, (kind,) in COMPONENTS.items():
        values = safe_list(contract.get(field), f"{field}-missing")
        group: set[str] = set()
        for item in values:
            component = safe_mapping(item, f"{field}-entry-invalid")
            identifier = safe_string(component.get("id"), f"{field}-id-missing")
            if not SAFE_ID.fullmatch(identifier) or identifier in group or identifier in kinds:
                raise ContractFailure("component-id-invalid-or-duplicate")
            group.add(identifier)
            kinds[identifier] = kind
        groups[field] = group
    return groups, kinds


def validate_configuration_shapes(contract: dict[str, Any]) -> None:
    for item in safe_list(contract.get("configuration_inputs"), "configuration-inputs-missing"):
        config = safe_mapping(item, "configuration-input-invalid")
        if not isinstance(config.get("required_fields"), list) or not isinstance(config.get("optional_fields"), list):
            raise ContractFailure("configuration-shape-missing")
        if config.get("sensitivity") not in {"public", "internal", "secret-reference-only"}:
            raise ContractFailure("configuration-sensitivity-invalid")
        for key in config:
            if key in SENSITIVE_VALUE_KEYS:
                raise ContractFailure("configuration-contains-value")


def validate_component_content(contract: dict[str, Any]) -> None:
    for item in safe_list(contract.get("artifacts"), "artifacts-missing"):
        artifact = safe_mapping(item, "artifact-invalid")
        safe_string(artifact.get("immutable_reference"), "artifact-immutable-reference-missing")
        safe_string(artifact.get("entrypoint"), "artifact-entrypoint-missing")
        safe_list(artifact.get("assertions"), "artifact-assertions-missing")
    for item in safe_list(contract.get("identities"), "identities-missing"):
        identity = safe_mapping(item, "identity-invalid")
        listed_ids(identity.get("permissions"), "identity-permissions-missing")
    for item in safe_list(contract.get("state_stores"), "state-stores-missing"):
        store = safe_mapping(item, "state-store-invalid")
        listed_ids(store.get("semantics"), "state-store-semantics-missing")
    for item in safe_list(contract.get("observability_profiles"), "observability-profiles-missing"):
        profile = safe_mapping(item, "observability-profile-invalid")
        listed_ids(profile.get("required_facts"), "observability-required-facts-missing")
    for item in safe_list(contract.get("recovery_plans"), "recovery-plans-missing"):
        recovery = safe_mapping(item, "recovery-plan-invalid")
        safe_string(recovery.get("cleanup"), "recovery-cleanup-missing")
        safe_string(recovery.get("rollback"), "recovery-rollback-missing")


def edge_set(contract: dict[str, Any], known: dict[str, str]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for item in safe_list(contract.get("edges"), "edges-missing"):
        edge = safe_mapping(item, "edge-invalid")
        source = safe_string(edge.get("from"), "edge-source-missing")
        destination = safe_string(edge.get("to"), "edge-destination-missing")
        safe_string(edge.get("purpose"), "edge-purpose-missing")
        if source not in known or destination not in known or source == destination:
            raise ContractFailure("edge-references-undeclared-node")
        if (source, destination) in result:
            raise ContractFailure("edge-duplicate")
        result.add((source, destination))
    return result


def listed_ids(value: Any, code: str) -> list[str]:
    entries = safe_list(value, code)
    if not all(isinstance(entry, str) and entry for entry in entries):
        raise ContractFailure(code)
    return entries


def validate_execution_graph(contract: dict[str, Any], groups: dict[str, set[str]], known: dict[str, str]) -> None:
    edges = edge_set(contract, known)
    for item in safe_list(contract.get("execution_units"), "execution-units-missing"):
        unit = safe_mapping(item, "execution-unit-invalid")
        unit_id = safe_string(unit.get("id"), "execution-unit-id-missing")
        for field, group_name in UNIT_REFERENCES.items():
            raw = unit.get(field)
            references = listed_ids(raw, f"execution-unit-{field}-missing") if field.endswith("s") else [safe_string(raw, f"execution-unit-{field}-missing")]
            for reference in references:
                if reference not in groups[group_name]:
                    raise ContractFailure("execution-unit-references-undeclared-component")
                if (unit_id, reference) not in edges:
                    raise ContractFailure("undeclared-dependency-edge")
    for item in safe_list(contract.get("connections"), "connections-missing"):
        connection = safe_mapping(item, "connection-invalid")
        source = safe_string(connection.get("source"), "connection-source-missing")
        destination = safe_string(connection.get("destination"), "connection-destination-missing")
        if source not in known or destination not in known:
            raise ContractFailure("connection-references-undeclared-node")
        if connection.get("transport_security") not in {"verified", "not-applicable"}:
            raise ContractFailure("connection-security-invalid")
    for item in safe_list(contract.get("async_channels"), "async-channels-missing"):
        channel = safe_mapping(item, "async-channel-invalid")
        if channel.get("delivery") not in {"at-least-once", "at-most-once", "exactly-once-by-contract"}:
            raise ContractFailure("async-delivery-invalid")
        if channel.get("acknowledgement") != "after-durable-completion" or not isinstance(channel.get("idempotency_boundary"), str):
            raise ContractFailure("async-durability-boundary-missing")


def validate_lifecycle(contract: dict[str, Any]) -> None:
    lifecycle = safe_mapping(contract.get("lifecycle"), "lifecycle-missing")
    states = set(listed_ids(lifecycle.get("states"), "lifecycle-states-missing"))
    terminals = set(listed_ids(lifecycle.get("terminal_states"), "lifecycle-terminal-states-missing"))
    if not {"prepared", "running", "succeeded", "failed", "stopped"}.issubset(states) or not {"succeeded", "failed", "stopped"}.issubset(terminals):
        raise ContractFailure("lifecycle-required-states-missing")
    if not terminals.issubset(states):
        raise ContractFailure("lifecycle-terminal-state-invalid")
    for item in safe_list(lifecycle.get("transitions"), "lifecycle-transitions-missing"):
        transition = safe_mapping(item, "lifecycle-transition-invalid")
        source = safe_string(transition.get("from"), "lifecycle-transition-source-missing")
        destination = safe_string(transition.get("to"), "lifecycle-transition-destination-missing")
        if source not in states or destination not in states or source in terminals:
            raise ContractFailure("unsafe-lifecycle-transition")
    retry = safe_mapping(lifecycle.get("retry"), "retry-policy-missing")
    if retry.get("mode") != "reviewed-recovery-only" or retry.get("requires_new_label") is not True:
        raise ContractFailure("unsafe-retry-policy")
    if not isinstance(retry.get("maximum_attempts"), int) or retry["maximum_attempts"] < 1:
        raise ContractFailure("retry-maximum-attempts-invalid")
    if set(listed_ids(retry.get("permitted_from"), "retry-permitted-from-missing")) - {"failed", "stopped"}:
        raise ContractFailure("unsafe-retry-policy")


def validate_assumptions(contract: dict[str, Any]) -> None:
    known_ids: set[str] = set()
    for item in safe_list(contract.get("assumptions"), "assumptions-missing"):
        assumption = safe_mapping(item, "assumption-invalid")
        identifier = safe_string(assumption.get("id"), "assumption-id-missing")
        if not SAFE_ID.fullmatch(identifier) or identifier in known_ids:
            raise ContractFailure("assumption-id-invalid-or-duplicate")
        known_ids.add(identifier)
        safe_string(assumption.get("statement"), "assumption-statement-missing")
        required = assumption.get("required_proof")
        actual = assumption.get("actual_proof")
        if required not in PROOF_RANK or actual not in PROOF_RANK:
            raise ContractFailure("assumption-proof-unknown")
        if PROOF_RANK[actual] < PROOF_RANK[required]:
            raise ContractFailure("assumption-proof-insufficient")


def validate_change_shape(contract: dict[str, Any]) -> None:
    shape = safe_mapping(contract.get("change_shape"), "change-shape-missing")
    if shape.get("reviewed_change_summary_required") is not True:
        raise ContractFailure("change-summary-not-required")
    allowed = set(listed_ids(shape.get("allowed_operation_classes"), "change-shape-allowed-missing"))
    forbidden = set(listed_ids(shape.get("forbidden_operation_classes"), "change-shape-forbidden-missing"))
    if not allowed or allowed & forbidden or not {"delete", "replace", "broaden-permission"}.issubset(forbidden):
        raise ContractFailure("change-shape-invalid")


def validate_gates(contract: dict[str, Any]) -> None:
    gates = safe_list(contract.get("gates"), "gates-missing")
    if len(gates) != len(GATE_ORDER):
        raise ContractFailure("gate-sequence-invalid")
    for index, item in enumerate(gates):
        gate = safe_mapping(item, "gate-invalid")
        if gate.get("id") != GATE_ORDER[index] or not isinstance(gate.get("evidence"), list) or not gate["evidence"]:
            raise ContractFailure("gate-sequence-invalid")
        if gate.get("prerequisites") != list(GATE_ORDER[:index]):
            raise ContractFailure("gate-prerequisites-invalid")
        expects_mutation = index >= GATE_ORDER.index("controlled-execution")
        if gate.get("may_mutate_live_target") is not expects_mutation:
            raise ContractFailure("gate-mutation-boundary-invalid")


def validate_contract(contract: dict[str, Any]) -> str:
    reject_provider_leakage(contract)
    reject_unsafe_value_fields(contract)
    if contract.get("schema") != CONTRACT_SCHEMA or contract.get("provider_boundary") != "normalized-facts-only":
        raise ContractFailure("contract-schema-or-boundary-invalid")
    identifier = safe_string(contract.get("id"), "contract-id-missing")
    if not SAFE_ID.fullmatch(identifier) or not isinstance(contract.get("version"), int) or contract["version"] < 1:
        raise ContractFailure("contract-id-or-version-invalid")
    groups, known = ids(contract)
    validate_configuration_shapes(contract)
    validate_component_content(contract)
    validate_execution_graph(contract, groups, known)
    validate_lifecycle(contract)
    validate_change_shape(contract)
    validate_assumptions(contract)
    validate_gates(contract)
    return identifier


def validate_facts(facts: dict[str, Any], contract_id: str, through: str) -> None:
    reject_provider_leakage(facts)
    if facts.get("schema") != FACTS_SCHEMA or facts.get("contract_id") != contract_id:
        raise ContractFailure("normalized-facts-schema-or-contract-invalid")
    evidence = safe_list(facts.get("gate_evidence"), "normalized-facts-evidence-missing")
    actual: dict[str, str] = {}
    for item in evidence:
        entry = safe_mapping(item, "normalized-facts-entry-invalid")
        gate = safe_string(entry.get("gate"), "normalized-facts-gate-missing")
        verdict = safe_string(entry.get("verdict"), "normalized-facts-verdict-missing")
        if gate not in GATE_ORDER or verdict not in {"passed", "failed"} or gate in actual:
            raise ContractFailure("normalized-facts-entry-invalid")
        actual[gate] = verdict
    required = GATE_ORDER[:GATE_ORDER.index(through) + 1]
    if not set(required).issubset(actual) or any(actual[gate] != "passed" for gate in required):
        raise ContractFailure("prerequisite-evidence-incomplete")


def validate_change_summary(summary: dict[str, Any], contract: dict[str, Any], contract_id: str) -> None:
    reject_provider_leakage(summary)
    if summary.get("schema") != CHANGE_SCHEMA or summary.get("contract_id") != contract_id:
        raise ContractFailure("normalized-change-summary-schema-or-contract-invalid")
    counts = safe_mapping(summary.get("operation_counts"), "normalized-change-summary-counts-missing")
    if not all(isinstance(value, int) and value >= 0 for value in counts.values()):
        raise ContractFailure("normalized-change-summary-counts-invalid")
    shape = safe_mapping(contract["change_shape"], "change-shape-missing")
    allowed = set(shape["allowed_operation_classes"])
    forbidden = set(shape["forbidden_operation_classes"])
    if any(operation not in allowed | forbidden for operation, count in counts.items() if count):
        raise ContractFailure("normalized-change-summary-operation-undeclared")
    if any(counts.get(operation, 0) for operation in forbidden):
        raise ContractFailure("normalized-change-summary-forbidden-operation")


def emit(contract_id: str, verdict: str, codes: list[str]) -> None:
    print(json.dumps({"schema": RESULT_SCHEMA, "contract_id": contract_id, "verdict": verdict, "findings": [{"code": code} for code in codes]}, sort_keys=True))


def main() -> int:
    contract_id = "unavailable"
    try:
        args = arguments()
        contract = load_yaml(args.contract, "contract-unreadable")
        contract_id = validate_contract(contract)
        through = args.through or "recovery"
        if args.facts:
            validate_facts(load_yaml(args.facts, "normalized-facts-unreadable"), contract_id, through)
        elif args.through:
            raise ContractFailure("normalized-facts-required-for-gate")
        if GATE_ORDER.index(through) >= GATE_ORDER.index("change-set") and args.facts and not args.change_summary:
            raise ContractFailure("normalized-change-summary-required-for-gate")
        if args.change_summary:
            validate_change_summary(load_yaml(args.change_summary, "normalized-change-summary-unreadable"), contract, contract_id)
        emit(contract_id, "passed", [])
        return 0
    except ContractFailure as error:
        emit(contract_id, "failed", [error.code])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
