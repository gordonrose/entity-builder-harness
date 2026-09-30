#!/usr/bin/env python3
"""Consume recomputed source analysis without establishing release authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-result-consumption
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject snapshot-only success and prohibit source results from granting execution authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import hashlib
from pathlib import Path
import re

from jsonschema import Draft202012Validator

import release_compiler as release

SCHEMA_DIR = release.SCHEMA_DIR
SCHEMA_FILE = "source-result-consumption.schema.yml"
SCHEMA_VERSION = "source-result-consumption/v1"
PURPOSES = {"source-analysis", "release-eligibility", "operation-authorization"}
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
ConsumptionFailure = release.ReleaseFailure

# These are producer output contracts, not release pass states. Every successful
# output is matched in full to a fresh, trusted producer invocation before use.
PRODUCERS = {
    "estate-caller-reconciliation/v1": {
        "scope": "structural-caller-reconciliation", "verdict_field": "structural_verdict",
        "success": "accounted", "closed_contract": "estate-caller-reconciliation",
    },
    "source-operation-result/v1": {
        "scope": "operation-contracts", "verdict_field": "contracts_verdict", "success": "complete",
        "required": {"source_closure", "qualification_verdict", "target_id", "inventory_digest",
                     "graph_digest", "caller_accounting_digest", "policy_revision", "counts",
                     "obligations", "source_findings", "contracts_digest"},
        "optional": set(), "digests": {"inventory_digest", "graph_digest", "caller_accounting_digest",
                                      "policy_revision", "contracts_digest"},
    },
    "release-control-result/v1": {
        "scope": "release-definition", "verdict_field": "verdict", "success": "compiled",
        "required": {"release_digest", "schema_digests", "operation_graph", "risk_tier", "acceptance_matrix"},
        "optional": set(), "digests": {"release_digest"}, "rows": "acceptance_matrix",
    },
    "source-coverage-result/v1": {
        "scope": "source-coverage", "verdict_field": "verdict", "success": "covered",
        "required": {"inventory_digest", "coverage_digest", "policy_revision", "acceptance_obligations"},
        "optional": {"compiled_release", "caller_reconciliation"},
        "digests": {"inventory_digest", "coverage_digest", "policy_revision"}, "rows": "acceptance_obligations",
    },
    "source-triage-result/v1": {
        "scope": "finding-triage", "verdict_field": "classification_verdict", "success": "complete",
        "required": {"inventory_digest", "collector_revision", "policy_revision", "coverage_verdict", "counts"},
        "optional": set(), "digests": {"inventory_digest", "collector_revision", "policy_revision"},
    },
    "source-caller-result/v1": {
        "scope": "caller-accounting", "verdict_field": "accounting_verdict", "success": "accounted",
        "required": {"qualification_verdict", "target_id", "graph_digest", "policy_revision",
                     "subject_count", "edge_count", "obligations", "source_findings", "accounting_digest"},
        "optional": set(), "digests": {"graph_digest", "policy_revision", "accounting_digest"},
    },
}


def load_contract(schema_dir=SCHEMA_DIR):
    """Load a local, closed contract; never resolve schema references."""
    schema = release.load_document(Path(schema_dir) / SCHEMA_FILE, "consumption-schema-unreadable")
    pending = [schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if any(key in value for key in ("$ref", "$dynamicRef", "$recursiveRef")):
                raise ConsumptionFailure("consumption-schema-reference-unsupported")
            if value.get("type") == "object" and value.get("additionalProperties") is not False:
                raise ConsumptionFailure("consumption-schema-open")
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    constants = {
        "schema": SCHEMA_VERSION, "scope": "source-result-consumption", "authorized": False,
        "release_eligibility": "blocked", "operation_authorization": "blocked",
    }
    if (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("$id") != "urn:release-control:source-result-consumption:v1"
            or schema.get("type") != "object" or not isinstance(properties, dict)
            or not isinstance(required, list)
            or not set(constants).issubset(required)
            or any(properties.get(key) != {"const": value} for key, value in constants.items())):
        raise ConsumptionFailure("consumption-schema-version-or-authority-invalid")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception:
        raise ConsumptionFailure("consumption-schema-invalid") from None
    return schema


def validate_estate_success(result):
    """Apply the full closed producer contract and its source-only invariants.

    The producer has separate source and boundary findings, not the generic
    findings field used by older receipts. A checksum alone is never evidence:
    consume_result still requires a complete match with a fresh producer run.
    """
    schema = release.load_document(SCHEMA_DIR / "estate-caller-reconciliation.schema.yml",
                                   "source-result-invalid")
    constants = {"schema": "estate-caller-reconciliation/v1",
                 "scope": "structural-caller-reconciliation", "authorized": False,
                 "release_eligibility": "blocked", "operation_authorization": "blocked",
                 "qualification_verdict": "blocked", "review_verdict": "not-evaluated"}
    if (schema.get("$id") != "urn:release-control:estate-caller-reconciliation:v1"
            or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("type") != "object"
            or not set(constants) <= set(schema.get("required", []))
            or any(schema.get("properties", {}).get(key) != {"const": value}
                   for key, value in constants.items())):
        raise ConsumptionFailure("source-result-invalid")
    stack = [schema]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if (any(key in item for key in ("$ref", "$dynamicRef", "$recursiveRef"))
                    or item.get("type") == "object" and item.get("additionalProperties") is not False):
                raise ConsumptionFailure("source-result-invalid")
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    Draft202012Validator.check_schema(schema)
    if next(Draft202012Validator(schema).iter_errors(result), None):
        raise ConsumptionFailure("source-result-invalid")
    raw = {(row["code"], row["source_id"]) for row in result["raw_source_findings"]}
    resolved = {(row["code"], row["source_id"]) for row in result["resolved_source_findings"]}
    remaining = {(row["code"], row["source_id"]) for row in result["remaining_source_findings"]}
    observations = result["resolved_observations"]
    if (result["boundary_findings"] or remaining or raw != resolved
            or any(code != "opaque-executable" for code, _ in resolved)
            or len({row["observation_id"] for row in observations}) != len(observations)
            or len({row["node_id"] for row in observations}) != len(observations)
            or result["roots"] > result["nodes"] or len(observations) > result["nodes"]
            or resolved and not observations
            or release.digest_document({key: value for key, value in result.items()
                                        if key != "result_digest"}) != result["result_digest"]):
        raise ConsumptionFailure("source-result-invalid")


def validate_success(result):
    """Check safe top-level semantics before comparing all nested source data."""
    release.bounded_json(result)
    if not isinstance(result, dict):
        raise ConsumptionFailure("source-result-invalid")
    if result.get("schema") == "source-adoption-migration/v1":
        raise ConsumptionFailure("source-result-proposal-unconsumable")
    if not isinstance(result.get("schema"), str) or result["schema"] not in PRODUCERS:
        raise ConsumptionFailure("source-result-producer-unsupported")
    producer = PRODUCERS[result["schema"]]
    if result.get("scope") != producer["scope"]:
        raise ConsumptionFailure("source-result-invalid")
    if result.get("authorized") is not False:
        raise ConsumptionFailure("source-result-authority-invalid")
    if result.get(producer["verdict_field"]) != producer["success"]:
        raise ConsumptionFailure("source-result-analysis-unsuccessful")
    if producer.get("closed_contract") == "estate-caller-reconciliation":
        validate_estate_success(result)
        return producer
    required = {"schema", "scope", "authorized", "findings", producer["verdict_field"]} | producer["required"]
    if not required <= result.keys() or result.keys() - required - producer["optional"]:
        raise ConsumptionFailure("source-result-invalid")
    if result["findings"] != []:
        raise ConsumptionFailure("source-result-invalid")
    if any(not isinstance(result[key], str) or not DIGEST.fullmatch(result[key]) for key in producer["digests"]):
        raise ConsumptionFailure("source-result-invalid")
    if "rows" in producer:
        rows = result[producer["rows"]]
        if (not isinstance(rows, list) or len(rows) != 17
                or any(not isinstance(row, dict) or type(row.get("stage")) is not int
                       or row["stage"] != index for index, row in enumerate(rows, 1))):
            raise ConsumptionFailure("source-result-invalid")
    if result["schema"] == "source-operation-result/v1":
        counts = result["counts"]
        if (result["source_closure"] != "blocked" or result["qualification_verdict"] != "blocked"
                or not isinstance(counts, dict) or set(counts) != {"subjects", "invocations", "observations", "dependencies"}
                or any(type(value) is not int or value < 0 for value in counts.values())
                or counts["subjects"] < 1 or not isinstance(result["obligations"], list)
                or len(result["obligations"]) != counts["subjects"]
                or not isinstance(result["source_findings"], list)
                or any(not isinstance(row, dict) or row.get("qualification") != "pending"
                       for row in result["obligations"])):
            raise ConsumptionFailure("source-result-invalid")
    elif result["schema"] == "release-control-result/v1":
        if (not isinstance(result["operation_graph"], list) or not result["operation_graph"]
                or not isinstance(result["schema_digests"], dict)
                or set(result["schema_digests"]) != {"release-definition/v1", "release-acceptance-matrix/v1"}
                or any(not isinstance(value, str) or not DIGEST.fullmatch(value)
                       for value in result["schema_digests"].values())
                or any(row.get("verdict") != "not-started" for row in result["acceptance_matrix"])):
            raise ConsumptionFailure("source-result-invalid")
    elif result["schema"] == "source-coverage-result/v1":
        if any(not isinstance(row.get("assertions"), list) or not row["assertions"]
               for row in result["acceptance_obligations"]):
            raise ConsumptionFailure("source-result-invalid")
        if "compiled_release" in result:
            if (not isinstance(result["compiled_release"], dict)
                    or result["compiled_release"].get("schema") != "release-control-result/v1"):
                raise ConsumptionFailure("source-result-invalid")
            validate_success(result["compiled_release"])
        if "caller_reconciliation" in result:
            caller_result = result["caller_reconciliation"]
            if (not isinstance(caller_result, dict)
                    or caller_result.get("schema") != "estate-caller-reconciliation/v1"
                    or caller_result.get("inventory_digest") != result["inventory_digest"]):
                raise ConsumptionFailure("source-result-invalid")
            validate_success(caller_result)
    elif result["schema"] == "source-triage-result/v1":
        counts = result["counts"]
        names = {"sources", "source_findings", "entries", "classified_findings"}
        if (not isinstance(counts, dict) or set(counts) != names | {"by_route"}
                or any(type(counts[name]) is not int or counts[name] < 0 for name in names)
                or counts["source_findings"] != counts["entries"]
                or counts["source_findings"] != counts["classified_findings"]
                or not isinstance(counts["by_route"], dict)
                or set(counts["by_route"]) != {"phase-2-source", "phase-3-artifact", "phase-5-provider"}
                or any(type(count) is not int or count < 0 for count in counts["by_route"].values())
                or sum(counts["by_route"].values()) != counts["classified_findings"]
                or result["coverage_verdict"] != ("blocked" if counts["source_findings"] else "clear-source-findings")):
            raise ConsumptionFailure("source-result-invalid")
    elif result["schema"] == "source-caller-result/v1":
        if (result["qualification_verdict"] != "blocked"
                or type(result["subject_count"]) is not int or result["subject_count"] < 1
                or type(result["edge_count"]) is not int or result["edge_count"] < 0
                or not isinstance(result["source_findings"], list)
                or not isinstance(result["obligations"], list)
                or len(result["obligations"]) != result["subject_count"]
                or any(not isinstance(row, dict) or row.get("qualification") != "pending"
                       for row in result["obligations"])):
            raise ConsumptionFailure("source-result-invalid")
    return producer


def initial_decision(purpose, schema):
    """Build only fixed metadata; do not copy producer strings into diagnostics."""
    normalized_purpose = purpose if isinstance(purpose, str) and purpose in PURPOSES else "unsupported"
    return {
        "schema": SCHEMA_VERSION, "scope": "source-result-consumption",
        "purpose": normalized_purpose, "verdict": "rejected", "authorized": False,
        "release_eligibility": "blocked", "operation_authorization": "blocked",
        "contract_digest": release.digest_document(schema),
        "policy_revision": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "findings": [],
    }


def checked_decision(decision, schema):
    try:
        release.bounded_json(decision)
        if next(Draft202012Validator(schema).iter_errors(decision), None):
            raise ConsumptionFailure("consumption-decision-invalid")
    except ConsumptionFailure:
        raise
    except Exception:
        raise ConsumptionFailure("consumption-decision-invalid") from None
    return decision


def reject_result(code, purpose="source-analysis", schema_dir=SCHEMA_DIR):
    """Safe public-wrapper rejection; schema failure propagates without input."""
    schema = load_contract(schema_dir)
    decision = initial_decision(purpose, schema)
    allowed = set(schema["properties"]["findings"]["items"]["properties"]["code"]["enum"])
    decision["findings"] = [{"code": code if isinstance(code, str) and code in allowed else "source-result-invalid"}]
    return checked_decision(decision, schema)


def consume_result(result, purpose, expected_result=None, schema_dir=SCHEMA_DIR):
    """Return source acceptance only after comparison with trusted recomputation.

    expected_result MUST come directly from a producer rerun against current
    source inputs, inside the caller's trust boundary. It is not another snapshot,
    a signature, runtime evidence, or a new release eligibility engine. Public
    command wrappers must never expose an expected-result file argument.
    """
    schema = load_contract(schema_dir)
    decision = initial_decision(purpose, schema)
    normalized_purpose = decision["purpose"]
    try:
        if normalized_purpose == "unsupported":
            raise ConsumptionFailure("source-result-purpose-unsupported")
        if normalized_purpose != "source-analysis":
            raise ConsumptionFailure("source-result-authority-unavailable")
        producer = validate_success(result)
        if expected_result is None:
            raise ConsumptionFailure("source-result-recomputation-required")
        try:
            validate_success(expected_result)
        except Exception:
            raise ConsumptionFailure("source-result-recomputation-invalid") from None
        # Canonical hashing uses JSON bytes, avoiding Python bool/int equality.
        if release.digest_document(result) != release.digest_document(expected_result):
            raise ConsumptionFailure("source-result-snapshot-mismatch")
        decision.update({
            "verdict": "accepted", "source_result_digest": release.digest_document(result),
            "source_result": {"schema": result["schema"], "scope": producer["scope"],
                              "analysis_verdict": producer["success"], "qualification_status": "not-established"},
        })
    except ConsumptionFailure as error:
        allowed = set(schema["properties"]["findings"]["items"]["properties"]["code"]["enum"])
        code = error.code if error.code in allowed else "source-result-invalid"
        decision["findings"] = [{"code": code}]
    except Exception:
        decision["findings"] = [{"code": "source-result-invalid"}]
    return checked_decision(decision, schema)
