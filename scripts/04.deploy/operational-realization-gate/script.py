#!/usr/bin/env python3
"""Compile a provider-neutral Operational Realization Contract into safe results."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-gate
#   version: 3
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
from datetime import datetime, timezone
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
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
FACTS_FIELDS = {"schema", "contract_id", "gate_evidence", "component_evidence"}
RECOVERY_FACTS_FIELDS = FACTS_FIELDS | {"recovery_evidence"}
CHANGE_SUMMARY_FIELDS = {"schema", "contract_id", "check_id", "timestamp", "operation_counts"}


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
    parser.add_argument("--validate-contract", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help", action="store_true")
    parsed, unknown = parser.parse_known_args()
    if parsed.help:
        print("Usage: script.py --contract <provider-neutral-contract.yml> (--validate-contract | --facts <normalized-facts.yml> --through <gate> [--change-summary <normalized-change-summary.yml>]) [--json]")
        raise SystemExit(0)
    if unknown or not parsed.contract or (parsed.validate_contract == bool(parsed.through)):
        raise ContractFailure("arguments-invalid")
    if parsed.validate_contract and (parsed.facts or parsed.change_summary):
        raise ContractFailure("arguments-invalid")
    if parsed.through and not parsed.facts:
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
            if str(key) in SENSITIVE_VALUE_KEYS or UNSAFE_CONTRACT_KEYS.fullmatch(str(key)):
                raise ContractFailure("unsafe-value-field-declared")
            reject_unsafe_value_fields(item)
    elif isinstance(value, list):
        for item in value:
            reject_unsafe_value_fields(item)


def require_exact_keys(value: dict[str, Any], expected: set[str], code: str) -> None:
    if set(value) != expected:
        raise ContractFailure(code)


def safe_identifier(value: Any, code: str) -> str:
    identifier = safe_string(value, code)
    if not SAFE_ID.fullmatch(identifier):
        raise ContractFailure(code)
    return identifier


def safe_timestamp(value: Any, code: str) -> str:
    timestamp = safe_string(value, code)
    if not UTC_TIMESTAMP.fullmatch(timestamp):
        raise ContractFailure(code)
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractFailure(code) from error
    if parsed.tzinfo != timezone.utc:
        raise ContractFailure(code)
    return timestamp


def ids(contract: dict[str, Any]) -> tuple[dict[str, set[str]], dict[str, str]]:
    groups: dict[str, set[str]] = {}
    kinds: dict[str, str] = {}
    for field, (kind,) in COMPONENTS.items():
        values = safe_list(contract.get(field), f"{field}-missing", non_empty=field != "async_channels")
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
        listed_ids(config["required_fields"], "configuration-required-fields-invalid") if config.get("required_fields") else None
        listed_ids(config["optional_fields"], "configuration-optional-fields-invalid") if config.get("optional_fields") else None


def validate_component_content(contract: dict[str, Any]) -> None:
    for item in safe_list(contract.get("artifacts"), "artifacts-missing"):
        artifact = safe_mapping(item, "artifact-invalid")
        has_reference = "immutable_reference" in artifact
        binding_mode = artifact.get("immutable_reference_mode")
        if has_reference:
            if binding_mode is not None:
                raise ContractFailure("artifact-immutable-reference-mode-invalid")
            immutable_reference = safe_string(artifact.get("immutable_reference"), "artifact-immutable-reference-missing")
            algorithm, _, digest = immutable_reference.partition(":")
            if (algorithm, len(digest)) not in {("sha256", 64), ("sha512", 128)} or not re.fullmatch(r"[0-9a-f]+", digest):
                raise ContractFailure("artifact-immutable-reference-invalid")
        elif binding_mode != "runtime-bound-sha256":
            raise ContractFailure("artifact-immutable-reference-mode-invalid")
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
        safe_string(recovery.get("entry_condition"), "recovery-entry-condition-missing")
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


def listed_ids(value: Any, code: str, non_empty: bool = True) -> list[str]:
    entries = safe_list(value, code, non_empty=non_empty)
    if not all(isinstance(entry, str) and entry for entry in entries):
        raise ContractFailure(code)
    return entries


def validate_execution_graph(contract: dict[str, Any], groups: dict[str, set[str]], known: dict[str, str]) -> None:
    edges = edge_set(contract, known)
    connections: dict[str, dict[str, Any]] = {}
    channels: dict[str, dict[str, Any]] = {}
    for item in safe_list(contract.get("connections"), "connections-missing"):
        connection = safe_mapping(item, "connection-invalid")
        connection_id = safe_identifier(connection.get("id"), "connection-id-invalid")
        source = safe_identifier(connection.get("source"), "connection-source-missing")
        destination = safe_identifier(connection.get("destination"), "connection-destination-missing")
        if source not in known or destination not in known:
            raise ContractFailure("connection-references-undeclared-node")
        if known[source] != "execution-unit":
            raise ContractFailure("connection-source-type-invalid")
        if known[destination] not in {"state-store", "async-channel"}:
            raise ContractFailure("connection-destination-type-invalid")
        if (connection_id, destination) not in edges:
            raise ContractFailure("connection-destination-edge-missing")
        if connection.get("transport_security") not in {"verified", "not-applicable"}:
            raise ContractFailure("connection-security-invalid")
        connections[connection_id] = connection
    for item in safe_list(contract.get("async_channels"), "async-channels-missing", non_empty=False):
        channel = safe_mapping(item, "async-channel-invalid")
        channel_id = safe_identifier(channel.get("id"), "async-channel-id-invalid")
        producer = safe_identifier(channel.get("producer"), "async-producer-invalid")
        consumers = listed_ids(channel.get("consumers"), "async-consumers-invalid")
        if producer not in known or known[producer] != "execution-unit":
            raise ContractFailure("async-producer-invalid")
        if any(consumer not in known or known[consumer] != "execution-unit" for consumer in consumers):
            raise ContractFailure("async-consumers-invalid")
        if (producer, channel_id) not in edges or any((channel_id, consumer) not in edges for consumer in consumers):
            raise ContractFailure("async-channel-edge-missing")
        if channel.get("delivery") not in {"at-least-once", "at-most-once", "exactly-once-by-contract"}:
            raise ContractFailure("async-delivery-invalid")
        idempotency_boundary = safe_identifier(channel.get("idempotency_boundary"), "async-durability-boundary-missing")
        if channel.get("acknowledgement") != "after-durable-completion" or idempotency_boundary not in known or known[idempotency_boundary] != "state-store":
            raise ContractFailure("async-durability-boundary-missing")
        channels[channel_id] = channel
    unit_connections: dict[str, set[str]] = {}
    unit_channels: dict[str, set[str]] = {}
    for item in safe_list(contract.get("execution_units"), "execution-units-missing"):
        unit = safe_mapping(item, "execution-unit-invalid")
        unit_id = safe_identifier(unit.get("id"), "execution-unit-id-missing")
        for field, group_name in UNIT_REFERENCES.items():
            raw = unit.get(field)
            references = listed_ids(raw, f"execution-unit-{field}-missing") if field.endswith("s") else [safe_string(raw, f"execution-unit-{field}-missing")]
            for reference in references:
                if reference not in groups[group_name]:
                    raise ContractFailure("execution-unit-references-undeclared-component")
                if (unit_id, reference) not in edges:
                    raise ContractFailure("undeclared-dependency-edge")
        unit_connections[unit_id] = set(listed_ids(unit.get("connections"), "execution-unit-connections-missing"))
        for connection_id in unit_connections[unit_id]:
            if connections[connection_id]["source"] != unit_id:
                raise ContractFailure("execution-unit-connection-source-mismatch")
        # A unit that only prepares, migrates, verifies, or restores state may
        # correctly use no asynchronous channel. Channel participants remain
        # required to bind the channel below; an empty declaration is not an
        # implicit binding.
        unit_channels[unit_id] = set(listed_ids(unit.get("async_channels"), "execution-unit-async-channels-missing", non_empty=False))
        for channel_id in unit_channels[unit_id]:
            if channel_id not in channels:
                raise ContractFailure("execution-unit-references-undeclared-component")
            channel = channels[channel_id]
            is_producer = channel["producer"] == unit_id
            is_consumer = unit_id in channel["consumers"]
            if not is_producer and not is_consumer:
                raise ContractFailure("execution-unit-async-channel-unbound")
            if is_producer and (unit_id, channel_id) not in edges:
                raise ContractFailure("async-channel-edge-missing")
            if is_consumer and (channel_id, unit_id) not in edges:
                raise ContractFailure("async-channel-edge-missing")
    if any(connection_id not in unit_connections[connection["source"]] for connection_id, connection in connections.items()):
        raise ContractFailure("connection-source-unit-binding-missing")
    for channel_id, channel in channels.items():
        if channel_id not in unit_channels[channel["producer"]] or any(channel_id not in unit_channels[consumer] for consumer in channel["consumers"]):
            raise ContractFailure("async-channel-unit-binding-missing")


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


def runtime_bound_artifact_ids(contract: dict[str, Any]) -> set[str]:
    return {
        safe_identifier(item.get("id"), "artifact-id-missing")
        for item in safe_list(contract.get("artifacts"), "artifacts-missing")
        if safe_mapping(item, "artifact-invalid").get("immutable_reference_mode") == "runtime-bound-sha256"
    }


def validate_facts(facts: dict[str, Any], contract: dict[str, Any], contract_id: str, known: dict[str, str], through: str) -> None:
    reject_provider_leakage(facts)
    reject_unsafe_value_fields(facts)
    runtime_bound_artifacts = runtime_bound_artifact_ids(contract)
    expected_fields = RECOVERY_FACTS_FIELDS if through == "recovery" else FACTS_FIELDS
    if runtime_bound_artifacts:
        expected_fields = expected_fields | {"artifact_bindings"}
    require_exact_keys(facts, expected_fields, "normalized-facts-fields-invalid")
    if facts.get("schema") != FACTS_SCHEMA or facts.get("contract_id") != contract_id:
        raise ContractFailure("normalized-facts-schema-or-contract-invalid")
    evidence = safe_list(facts.get("gate_evidence"), "normalized-facts-evidence-missing")
    required = GATE_ORDER[:GATE_ORDER.index(through) + 1]
    if len(evidence) != len(required):
        raise ContractFailure("normalized-facts-evidence-sequence-invalid")
    for index, item in enumerate(evidence):
        entry = safe_mapping(item, "normalized-facts-entry-invalid")
        require_exact_keys(entry, {"gate", "check_id", "timestamp", "verdict"}, "normalized-facts-entry-fields-invalid")
        gate = safe_string(entry.get("gate"), "normalized-facts-gate-missing")
        safe_identifier(entry.get("check_id"), "normalized-facts-check-id-invalid")
        safe_timestamp(entry.get("timestamp"), "normalized-facts-timestamp-invalid")
        if gate != required[index] or entry.get("verdict") != "passed":
            raise ContractFailure("normalized-facts-evidence-sequence-invalid")
    component_evidence = safe_list(facts.get("component_evidence"), "component-evidence-missing")
    observed: set[str] = set()
    for item in component_evidence:
        entry = safe_mapping(item, "component-evidence-entry-invalid")
        require_exact_keys(entry, {"component_id", "component_kind", "check_id", "timestamp", "verdict"}, "component-evidence-entry-fields-invalid")
        component_id = safe_identifier(entry.get("component_id"), "component-evidence-id-invalid")
        if component_id in observed or component_id not in known or entry.get("component_kind") != known[component_id]:
            raise ContractFailure("component-evidence-binding-invalid")
        safe_identifier(entry.get("check_id"), "component-evidence-check-id-invalid")
        safe_timestamp(entry.get("timestamp"), "component-evidence-timestamp-invalid")
        if entry.get("verdict") != "passed":
            raise ContractFailure("component-evidence-verdict-invalid")
        observed.add(component_id)
    if observed != set(known):
        raise ContractFailure("component-evidence-incomplete")
    if runtime_bound_artifacts:
        bindings = safe_list(facts.get("artifact_bindings"), "artifact-bindings-missing")
        bound: set[str] = set()
        for item in bindings:
            binding = safe_mapping(item, "artifact-binding-invalid")
            require_exact_keys(binding, {"component_id", "immutable_reference", "check_id", "timestamp", "verdict"}, "artifact-binding-fields-invalid")
            component_id = safe_identifier(binding.get("component_id"), "artifact-binding-id-invalid")
            immutable_reference = safe_string(binding.get("immutable_reference"), "artifact-binding-reference-invalid")
            algorithm, _, digest = immutable_reference.partition(":")
            if component_id not in runtime_bound_artifacts or component_id in bound or algorithm != "sha256" or len(digest) != 64 or not re.fullmatch(r"[0-9a-f]+", digest):
                raise ContractFailure("artifact-binding-invalid")
            safe_identifier(binding.get("check_id"), "artifact-binding-check-id-invalid")
            safe_timestamp(binding.get("timestamp"), "artifact-binding-timestamp-invalid")
            if binding.get("verdict") != "passed":
                raise ContractFailure("artifact-binding-verdict-invalid")
            bound.add(component_id)
        if bound != runtime_bound_artifacts:
            raise ContractFailure("artifact-binding-incomplete")
    if through == "recovery":
        recovery = safe_mapping(facts.get("recovery_evidence"), "recovery-evidence-missing")
        require_exact_keys(recovery, {"predecessor_attempt_label", "recovery_attempt_label", "predecessor_terminal_state", "check_id", "timestamp", "verdict"}, "recovery-evidence-fields-invalid")
        predecessor = safe_identifier(recovery.get("predecessor_attempt_label"), "recovery-predecessor-label-invalid")
        recovery_label = safe_identifier(recovery.get("recovery_attempt_label"), "recovery-attempt-label-invalid")
        if predecessor == recovery_label:
            raise ContractFailure("recovery-label-not-new")
        if recovery.get("predecessor_terminal_state") not in {"failed", "stopped"}:
            raise ContractFailure("recovery-predecessor-not-terminal")
        safe_identifier(recovery.get("check_id"), "recovery-evidence-check-id-invalid")
        safe_timestamp(recovery.get("timestamp"), "recovery-evidence-timestamp-invalid")
        if recovery.get("verdict") != "passed":
            raise ContractFailure("recovery-evidence-verdict-invalid")


def validate_change_summary(summary: dict[str, Any], contract: dict[str, Any], contract_id: str) -> None:
    reject_provider_leakage(summary)
    reject_unsafe_value_fields(summary)
    require_exact_keys(summary, CHANGE_SUMMARY_FIELDS, "normalized-change-summary-fields-invalid")
    if summary.get("schema") != CHANGE_SCHEMA or summary.get("contract_id") != contract_id:
        raise ContractFailure("normalized-change-summary-schema-or-contract-invalid")
    safe_identifier(summary.get("check_id"), "normalized-change-summary-check-id-invalid")
    safe_timestamp(summary.get("timestamp"), "normalized-change-summary-timestamp-invalid")
    counts = safe_mapping(summary.get("operation_counts"), "normalized-change-summary-counts-missing")
    shape = safe_mapping(contract["change_shape"], "change-shape-missing")
    allowed = set(shape["allowed_operation_classes"])
    forbidden = set(shape["forbidden_operation_classes"])
    if set(counts) != allowed | forbidden or not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in counts.values()):
        raise ContractFailure("normalized-change-summary-counts-invalid")
    if any(operation not in allowed | forbidden for operation, count in counts.items() if count):
        raise ContractFailure("normalized-change-summary-operation-undeclared")
    if any(counts.get(operation, 0) for operation in forbidden):
        raise ContractFailure("normalized-change-summary-forbidden-operation")


def emit(contract_id: str, verdict: str, codes: list[str], scope: str) -> None:
    print(json.dumps({"schema": RESULT_SCHEMA, "contract_id": contract_id, "scope": scope, "verdict": verdict, "findings": [{"code": code} for code in codes]}, sort_keys=True))


def main() -> int:
    if any(argument.split("=", 1)[0] in {"--consume-result", "--purpose"} for argument in sys.argv[1:]):
        sys.dont_write_bytecode = True
        try:
            import result_consumption_cli
        except ImportError:
            print(json.dumps({"schema": "source-result-consumption/v1", "scope": "source-result-consumption",
                              "purpose": "source-analysis", "verdict": "rejected", "authorized": False,
                              "release_eligibility": "blocked", "operation_authorization": "blocked",
                              "findings": [{"code": "compiler-dependency-unavailable"}]}, sort_keys=True))
            return 1
        return result_consumption_cli.main(sys.argv[1:])
    if any(argument.split("=", 1)[0] in {"--builds", "--build-id", "--artifact-root", "--expect-inventory-digest", "--expect-artifact-digest"} for argument in sys.argv[1:]):
        sys.dont_write_bytecode = True
        try:
            import build_contracts_cli
        except ImportError:
            print(json.dumps({"schema": "source-build-result/v1", "scope": "build-accounting",
                              "authorized": False, "verdict": "incomplete",
                              "source_closure": "blocked", "qualification_verdict": "blocked",
                              "findings": [{"code": "compiler-dependency-unavailable"}]}, sort_keys=True))
            return 1
        return build_contracts_cli.main(sys.argv[1:])
    if any(argument.split("=", 1)[0] in {"--operations", "--operation-contracts", "--operation-template"} for argument in sys.argv[1:]):
        sys.dont_write_bytecode = True
        try:
            import operation_contracts_cli
        except ImportError:
            print(json.dumps({"schema": "source-operation-result/v1", "scope": "operation-contracts",
                              "authorized": False, "contracts_verdict": "incomplete",
                              "source_closure": "blocked", "qualification_verdict": "blocked",
                              "findings": [{"code": "compiler-dependency-unavailable"}]}, sort_keys=True))
            return 1
        return operation_contracts_cli.main(sys.argv[1:])
    if any(argument.split("=", 1)[0] in {"--discover", "--coverage", "--composition", "--adoption-ledger", "--source-root", "--ledger-template", "--triage", "--finding-triage", "--callers", "--workflow", "--caller-review", "--review-template"} for argument in sys.argv[1:]):
        sys.dont_write_bytecode = True
        try:
            import source_coverage
        except ImportError:
            print(json.dumps({"schema": "source-coverage-result/v1", "scope": "source-coverage",
                              "verdict": "failed", "authorized": False,
                              "findings": [{"code": "compiler-dependency-unavailable"}]}, sort_keys=True))
            return 1
        return source_coverage.main(sys.argv[1:])
    if any(argument.split("=", 1)[0] in {"--release", "--baseline-release"} for argument in sys.argv[1:]):
        sys.dont_write_bytecode = True
        try:
            import release_compiler
        except ImportError:
            print(json.dumps({"schema": "release-control-result/v1", "scope": "release-definition",
                              "verdict": "failed", "authorized": False,
                              "findings": [{"code": "compiler-dependency-unavailable"}]}, sort_keys=True))
            return 1
        return release_compiler.main(sys.argv[1:])
    contract_id = "unavailable"
    scope = "unavailable"
    try:
        args = arguments()
        contract = load_yaml(args.contract, "contract-unreadable")
        contract_id = validate_contract(contract)
        if args.validate_contract:
            emit(contract_id, "passed", [], "contract")
            return 0
        through = args.through
        scope = through
        groups, known = ids(contract)
        del groups
        validate_facts(load_yaml(args.facts, "normalized-facts-unreadable"), contract, contract_id, known, through)
        if GATE_ORDER.index(through) >= GATE_ORDER.index("change-set") and not args.change_summary:
            raise ContractFailure("normalized-change-summary-required-for-gate")
        if args.change_summary:
            validate_change_summary(load_yaml(args.change_summary, "normalized-change-summary-unreadable"), contract, contract_id)
        emit(contract_id, "passed", [], scope)
        return 0
    except ContractFailure as error:
        emit(contract_id, "failed", [error.code], scope)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
