# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.diagnostics.runtime-contract-reader
#   version: 1
#   status: active
#   created_on: "2026-10-27"
#   updated_on: "2026-10-31"
#   layer: 06.shared
#   domain: diagnostics
#   disciplines: [architecture, security, sre]
#   kind: code
#   purpose: Validate code-exported diagnostic records without duplicating capability vocabularies in Python.
#   portability: { class: source-only, targets: [] }
#   used_by:
#   - id: repo.diagnostics.coverage
#     path: scripts/repo/diagnostic-coverage/script.sh
"""Strict reader for the core closed schema subset. Errors never echo input."""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TARGET_CATALOG = ROOT / "infra/04.deploy/03.product/entrypoints/contracts/diagnostics.v1.json"
PERSISTENCE_CATALOG = ROOT / "platform/persistence/contracts/diagnostics.v1.json"
SECURITY_CATALOG = ROOT / "platform/security/contracts/diagnostics.v1.json"
OBSERVABILITY_CATALOG = ROOT / "platform/observability/contracts/diagnostics.v1.json"
HEALTH_CATALOG = ROOT / "platform/health/contracts/diagnostics.v1.json"
CORE_CATALOG = ROOT / "packages/core/contracts/diagnostics.v1.json"
CONFIG_CATALOG = ROOT / "platform/config/contracts/diagnostics.v1.json"
CONTRACT_CATALOG = ROOT / "platform/contracts/contracts/diagnostics.v1.json"
PLATFORM_TARGET_CATALOG = ROOT / "infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-diagnostics.v1.json"
SERVER_CATALOG = ROOT / "platform/server/contracts/diagnostics.v1.json"
WORKER_CATALOG = ROOT / "platform/workers/contracts/diagnostics.v1.json"
RUNTIME_CATALOG = ROOT / "platform/runtime/contracts/diagnostics.v1.json"
SMOKE_CATALOG = ROOT / "apps/platform-smoke/contracts/diagnostics.v1.json"
ACCEPTANCE_CATALOG = ROOT / "infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-acceptance-diagnostics.v1.json"
DELIVERY_CATALOG = ROOT / "infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-delivery-diagnostics.v1.json"
PERSISTENCE_TASK_OPERATION_CATALOG = ROOT / "infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-persistence-operation-diagnostics.v1.json"
PLATFORM_POSTGRESQL_OPERATION_CATALOG = ROOT / "infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-postgresql-operation-diagnostics.v1.json"

class DiagnosticContractError(ValueError):
    pass

def persistence_definitions() -> list[dict[str, Any]]:
    return json.loads(PERSISTENCE_CATALOG.read_text(encoding="utf-8"))["catalog"]["definitions"]

def persistence_operation_definitions() -> list[dict[str, Any]]:
    """Select the exported operation contract, not every persistence concern.

    Configuration has a different detail contract. Failure classification is
    not a family discriminator: operational trust failures are configuration
    failures too. Vocabulary and versions remain owned by the runtime export.
    """
    operation_fields = {"phase", "classification", "codeStatus", "operation", "effect"}
    return [definition for definition in persistence_definitions()
            if operation_fields <= definition["detail"].get("properties", {}).keys()]

def persistence_vocabulary(field: str) -> set[str]:
    return set(persistence_operation_definitions()[0]["detail"]["properties"][field]["values"])

def copy_detail(schema: dict[str, Any], value: Any, budget: list[int], depth: int = 0) -> Any:
    budget[0] -= 1
    if budget[0] < 0 or depth > 8:
        raise DiagnosticContractError("diagnostic-detail-limit")
    kind = schema.get("type")
    if kind == "enum" and isinstance(value, str) and value in schema["values"]:
        return value
    if kind == "boolean" and type(value) is bool:
        return value
    if kind in {"integer", "number"} and type(value) in {int, float} and schema["minimum"] <= value <= schema["maximum"]:
        if kind == "integer" and abs(value) <= 9007199254740991 and value == int(value):
            return int(value)
        if kind == "number" and math.isfinite(float(value)):
            return float(value)
    if kind == "array" and type(value) is list and schema["minItems"] <= len(value) <= schema["maxItems"]:
        return [copy_detail(schema["items"], item, budget, depth + 1) for item in value]
    if kind == "object" and type(value) is dict:
        properties = schema["properties"]
        optional = schema.get("optional", [])
        if not set(value) <= set(properties) or not set(properties).difference(optional) <= set(value):
            raise DiagnosticContractError("diagnostic-detail-fields-invalid")
        return {key: copy_detail(child, value[key], budget, depth + 1) for key, child in properties.items() if key in value}
    raise DiagnosticContractError("diagnostic-detail-invalid")

def validate_record(value: Any, catalog_path: Path = TARGET_CATALOG) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {"schema", "code", "definitionVersion", "detail"} or value.get("schema") != "core/diagnostic-record/v1":
        raise DiagnosticContractError("diagnostic-record-fields-invalid")
    version = value.get("definitionVersion")
    if type(version) not in {int, float} or not 1 <= version <= 9007199254740991 or version != int(version):
        raise DiagnosticContractError("diagnostic-record-version-invalid")
    contract = json.loads(catalog_path.read_text(encoding="utf-8"))
    if contract.get("schema") != "core/diagnostic-catalog-export/v1":
        raise DiagnosticContractError("diagnostic-catalog-invalid")
    matches = [definition for definition in contract["catalog"]["definitions"] if definition["code"] == value["code"] and definition["version"] == value["definitionVersion"]]
    if len(matches) != 1:
        raise DiagnosticContractError("diagnostic-definition-unknown")
    detail = copy_detail(matches[0]["detail"], value["detail"], [512])
    record = {"schema": value["schema"], "code": value["code"], "definitionVersion": matches[0]["version"], "detail": detail}
    if len(json.dumps(record, separators=(",", ":"), ensure_ascii=False).encode("utf-16-le")) // 2 > 16384:
        raise DiagnosticContractError("diagnostic-record-limit")
    return record

def validate_selected_record(value: Any) -> dict[str, Any]:
    """Explicit current composition contracts; operation-specific readers stay narrow."""
    for catalog in (TARGET_CATALOG, PERSISTENCE_CATALOG, SECURITY_CATALOG, OBSERVABILITY_CATALOG, HEALTH_CATALOG,
                    CORE_CATALOG, CONFIG_CATALOG, CONTRACT_CATALOG, PLATFORM_TARGET_CATALOG,
                    SERVER_CATALOG, WORKER_CATALOG, RUNTIME_CATALOG, SMOKE_CATALOG, ACCEPTANCE_CATALOG, DELIVERY_CATALOG,
                    PLATFORM_POSTGRESQL_OPERATION_CATALOG):
        try:
            return validate_record(value, catalog)
        except DiagnosticContractError:
            pass
    raise DiagnosticContractError("diagnostic-definition-unknown")

def persistence_task_failure_contract() -> dict[str, Any]:
    """Private delivery bounds/result codes remain owned by the TS export."""
    try:
        exported = json.loads(PERSISTENCE_TASK_OPERATION_CATALOG.read_text(encoding="utf-8"))
        value = exported["delivery"]["taskFailure"]
        if (exported.get("schema") != "core/diagnostic-catalog-export/v1" or type(value) is not dict
                or set(value) != {"schema", "maxObservations", "maxSourceBundles", "maxOverflowCount", "codes"}
                or value["schema"] != "deploy/persistence-task-failure/v1"
                or type(value["maxObservations"]) is not int or not 1 <= value["maxObservations"] <= 100
                or type(value["maxSourceBundles"]) is not int or not 1 <= value["maxSourceBundles"] <= 100
                or type(value["maxOverflowCount"]) is not int or not 1 <= value["maxOverflowCount"] <= 9007199254740991
                or type(value["codes"]) is not dict or set(value["codes"]) != {"administration", "verification"}):
            raise DiagnosticContractError("diagnostic-task-contract-invalid")
        for codes in value["codes"].values():
            if type(codes) is not list or not 1 <= len(codes) <= 64 or not all(type(code) is str for code in codes) or len(set(codes)) != len(codes):
                raise DiagnosticContractError("diagnostic-task-contract-invalid")
        return value
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise DiagnosticContractError("diagnostic-task-contract-invalid") from error

def validate_persistence_task_observation(value: Any, expected_task: str) -> dict[str, Any]:
    """Task association applies only to own operational observations."""
    if type(expected_task) is not str or expected_task not in persistence_task_failure_contract()["codes"]:
        raise DiagnosticContractError("diagnostic-task-invalid")
    record = validate_record(value, PERSISTENCE_TASK_OPERATION_CATALOG)
    if record["detail"].get("task") != expected_task:
        raise DiagnosticContractError("diagnostic-task-mismatch")
    return record

def validate_persistence_task_source(value: Any, expected_task: str) -> dict[str, Any]:
    """Mirror task TS primary selection without widening historical readers.

    A preserved source retains its own operation. The enclosing task is
    established by its private envelope/observations, never by relabeling it.
    """
    if type(expected_task) is not str or expected_task not in persistence_task_failure_contract()["codes"]:
        raise DiagnosticContractError("diagnostic-task-invalid")
    for catalog in (CORE_CATALOG, PERSISTENCE_CATALOG, TARGET_CATALOG, SECURITY_CATALOG, OBSERVABILITY_CATALOG):
        try:
            return validate_record(value, catalog)
        except DiagnosticContractError:
            pass
    raise DiagnosticContractError("diagnostic-task-source-invalid")

def validate_related_records(value: Any, primary: Any) -> list[dict[str, Any]]:
    """Persistence tasks retain selected Core/Persistence source companions.

    Security peer facts still require the positively classified TLS primary;
    configuration and unrelated security/content records are not companions.
    """
    contract = json.loads(TARGET_CATALOG.read_text(encoding="utf-8"))
    limit = contract["delivery"]["maxRelatedRecords"]
    if type(value) is not list or len(value) > limit:
        raise DiagnosticContractError("diagnostic-related-limit")
    def persistence_source(item: Any) -> dict[str, Any]:
        for catalog in (CORE_CATALOG, PERSISTENCE_CATALOG):
            try:
                return validate_record(item, catalog)
            except DiagnosticContractError:
                pass
        raise DiagnosticContractError("diagnostic-related-family-invalid")
    checked_primary = persistence_source(primary)
    tls_primary = checked_primary["code"] == "persistence.trust-validation-failed" and checked_primary["detail"].get("classification") == "tls_trust_invalid"
    records = []
    for item in value:
        try:
            records.append(persistence_source(item))
        except DiagnosticContractError:
            if not tls_primary:
                raise
            peer = validate_record(item, SECURITY_CATALOG)
            if peer["code"] not in {"security.peer-identity-verification-failed", "security.peer-trust-verification-failed"}:
                raise DiagnosticContractError("diagnostic-related-family-invalid")
            records.append(peer)
    return records

def validate_configuration_record(value: Any) -> dict[str, Any]:
    try:
        return validate_record(value, TARGET_CATALOG)
    except DiagnosticContractError:
        record = validate_record(value, SECURITY_CATALOG)
        if record["detail"].get("phase") != "certificate-content-parsing":
            raise DiagnosticContractError("diagnostic-configuration-family-invalid")
        return record

def validate_operation_record(value: Any, operation: str, *, allow_core_source: bool = False) -> dict[str, Any]:
    try:
        record = validate_record(value, PERSISTENCE_CATALOG)
    except DiagnosticContractError:
        if not allow_core_source:
            raise
        # A preserved source helper does not claim to be the enclosing task.
        # The caller owns that rejection envelope; no provider/native inference
        # is made from the Core source's different operation vocabulary.
        if not any(operation in definition["detail"]["properties"]["operation"]["values"]
                   for definition in persistence_operation_definitions()):
            raise DiagnosticContractError("diagnostic-operation-mismatch")
        return validate_record(value, CORE_CATALOG)
    if record["detail"].get("operation") != operation:
        raise DiagnosticContractError("diagnostic-operation-mismatch")
    return record
