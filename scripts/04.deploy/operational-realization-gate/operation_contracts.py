#!/usr/bin/env python3
"""Bind source operation contracts without qualifying their runtime behavior."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-operation-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reconcile independent script and action inventories with reviewed source obligations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import hashlib
from pathlib import Path

from jsonschema import Draft202012Validator

import caller_coverage as callers
import release_compiler as release
import source_coverage as coverage

OperationFailure = coverage.CoverageFailure
SCHEMA_DIR = release.SCHEMA_DIR
EVIDENCE_RULES = ["source-semantics", "exact-artifact", "supply-chain", "authority", "recovery"]
EVIDENCE_STAGES = [(3, "source-semantics"), (6, "exact-artifact"), (7, "supply-chain"),
                   (8, "authority"), (15, "recovery")]
MAX_INVENTORY_NODES = 100000


def validate_schema(name, document):
    """Require versioned closed local schemas before inspecting untrusted data."""
    if name == "source-operation-inventory":
        release.bounded_json(document, max_nodes=MAX_INVENTORY_NODES)
    else:
        release.bounded_json(document)
    schema = release.load_document(SCHEMA_DIR / (name + ".schema.yml"), "operation-schema-unreadable")
    properties = schema.get("properties")
    if (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("$id") != "urn:release-control:" + name + ":v1"
            or schema.get("type") != "object" or not isinstance(properties, dict)
            or properties.get("schema") != {"const": name + "/v1"}):
        raise OperationFailure("operation-schema-version-invalid")
    pending = [schema]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if any(key in item for key in ("$ref", "$dynamicRef", "$recursiveRef")):
                raise OperationFailure("operation-schema-reference-unsupported")
            if item.get("type") == "object" or "properties" in item:
                required, properties = item.get("required"), item.get("properties")
                if (item.get("type") != "object" or item.get("additionalProperties") is not False
                        or not isinstance(required, list) or any(type(key) is not str for key in required)
                        or not isinstance(properties, dict) or set(required) != set(properties)):
                    raise OperationFailure("operation-schema-open")
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    try:
        Draft202012Validator.check_schema(schema)
        if next(Draft202012Validator(schema).iter_errors(document), None):
            raise OperationFailure(name + "-invalid")
    except OperationFailure:
        raise
    except Exception:
        raise OperationFailure("operation-schema-invalid") from None
    return release.digest_document(schema)


def selected_subjects(nodes):
    """Derive the scope from the caller graph, independently of declarations."""
    result = {}
    for node_id, node in nodes.items():
        if node["kind"] == "script-entrypoint":
            result[node_id] = "script"
        elif node["kind"] == "tool-command":
            result[node_id] = "tool"
        elif node["kind"] == "workflow-step" and "caller-workflow-action-unresolved" in node["issues"]:
            result[node_id] = "action"
    return result


def checked_inventory(inventory, graph):
    """Validate structure and bindings; only fresh collection establishes provenance."""
    schema_digest = validate_schema("source-operation-inventory", inventory)
    release.bounded_json(graph)
    _, nodes, edges = callers.checked_graph(graph)
    if release.digest_document({key: value for key, value in inventory.items()
                                if key != "inventory_digest"}) != inventory["inventory_digest"]:
        raise OperationFailure("operation-inventory-digest-invalid")
    if inventory["graph_digest"] != graph["graph_digest"]:
        raise OperationFailure("operation-inventory-graph-stale")
    sources = coverage.unique(inventory["sources"], "id")
    coverage.unique(inventory["sources"], "path")
    subjects = coverage.unique(inventory["subjects"], "id")
    observations = coverage.unique(inventory["observations"], "id")
    dependencies = coverage.unique(inventory["dependencies"], "id")
    if any(sources.get(item["id"]) != item for item in graph["sources"]):
        raise OperationFailure("operation-inventory-source-stale")
    selected = selected_subjects(nodes)
    if set(subjects) != set(selected):
        raise OperationFailure("operation-subject-coverage-incomplete")
    incoming = {subject: {edge["id"] for edge in edges.values() if edge["callee_id"] == subject}
                for subject in subjects}
    for subject_id, subject in subjects.items():
        if (subject["kind"] != selected[subject_id]
                or subject["source_id"] != nodes[subject_id]["source_id"]
                or subject["detail_digest"] != nodes[subject_id]["detail_digest"]):
            raise OperationFailure("operation-subject-binding-invalid")
        if set(subject["invocation_ids"]) != incoming[subject_id]:
            raise OperationFailure("operation-invocation-coverage-incomplete")
    for dependency in dependencies.values():
        if (dependency["subject_id"] not in subjects or dependency["from_source_id"] not in sources
                or dependency["to_source_id"] not in sources):
            raise OperationFailure("operation-dependency-reference-invalid")
    reached = {}
    for subject_id, subject in subjects.items():
        adjacency = {}
        for dependency in dependencies.values():
            if dependency["subject_id"] == subject_id:
                adjacency.setdefault(dependency["from_source_id"], set()).add(dependency["to_source_id"])
        visited, pending = set(), [subject["source_id"]]
        while pending:
            source_id = pending.pop()
            if source_id not in visited:
                visited.add(source_id)
                pending.extend(adjacency.get(source_id, set()) - visited)
        reached[subject_id] = visited
        if any(source_id not in visited for source_id in adjacency):
            raise OperationFailure("operation-dependency-unreachable")
    for observation in observations.values():
        if (observation["subject_id"] not in subjects
                or observation["source_id"] not in reached[observation["subject_id"]]):
            raise OperationFailure("operation-observation-reference-invalid")
    graph_sources = {item["id"] for item in graph["sources"]}
    if set(sources) - graph_sources - set().union(*reached.values()):
        raise OperationFailure("operation-source-unreachable")
    if any(finding["subject_id"] not in subjects for finding in inventory["findings"]):
        raise OperationFailure("operation-finding-reference-invalid")
    return schema_digest, subjects, observations, dependencies


def checked_callers(graph, review):
    release.bounded_json(review)
    result = callers.compile_callers(graph, review)
    if result["accounting_verdict"] != "accounted":
        raise OperationFailure("operation-caller-accounting-incomplete")
    return result


def make_contracts(inventory, graph, caller_review):
    """Create an explicit pending review, never approve declarations automatically."""
    _, subjects, observations, dependencies = checked_inventory(inventory, graph)
    caller_result = checked_callers(graph, caller_review)
    caller_bindings = {item["node_id"]: item for item in caller_review["bindings"]}
    bindings = []
    for subject_id, subject in sorted(subjects.items()):
        caller = caller_bindings[subject_id]
        bindings.append({
            "subject_id": subject_id, "owner": caller["owner"], "operation_id": caller["operation_id"],
            "operation_profile": caller["operation_profile"], "review_status": "pending",
            "invocation_ids": sorted(subject["invocation_ids"]),
            "observation_ids": sorted(item["id"] for item in observations.values() if item["subject_id"] == subject_id),
            "dependency_ids": sorted(item["id"] for item in dependencies.values() if item["subject_id"] == subject_id),
            "argument_policy": "observed-variants-only", "unobserved_arguments": "blocked",
            "completion_rule": "profile-specific-verification-required", "failure_state": "blocked",
            "recovery_route": "reviewed-recovery-required", "evidence_rules": list(EVIDENCE_RULES),
        })
    result = {"schema": "source-operation-contracts/v1", "inventory_digest": inventory["inventory_digest"],
              "graph_digest": graph["graph_digest"], "caller_accounting_digest": caller_result["accounting_digest"],
              "target_id": caller_review["target_id"], "bindings": bindings}
    validate_schema("source-operation-contracts", result)
    return result


def compile_operations(inventory, graph, caller_review, contracts):
    """Account for source contracts; all runtime and semantic proof remains required."""
    inventory_schema_digest, subjects, observations, dependencies = checked_inventory(inventory, graph)
    caller_result = checked_callers(graph, caller_review)
    contract_schema_digest = validate_schema("source-operation-contracts", contracts)
    bindings = coverage.unique(contracts["bindings"], "subject_id")
    coverage.unique(contracts["bindings"], "operation_id")
    caller_bindings = {item["node_id"]: item for item in caller_review["bindings"]}
    root = graph["entrypoint"]["node_id"]
    problems = set()
    if (contracts["inventory_digest"] != inventory["inventory_digest"]
            or contracts["graph_digest"] != graph["graph_digest"]
            or contracts["caller_accounting_digest"] != caller_result["accounting_digest"]
            or contracts["target_id"] != caller_review["target_id"]):
        problems.add(("operation-contracts-stale", root))
    if set(bindings) != set(subjects):
        problems.add(("operation-contract-coverage-incomplete", root))
    for subject_id, binding in bindings.items():
        if subject_id not in subjects:
            continue
        subject, caller = subjects[subject_id], caller_bindings[subject_id]
        if any(binding[field] != caller[field] for field in ("owner", "operation_id", "operation_profile")):
            problems.add(("operation-caller-binding-mismatch", subject_id))
        if binding["review_status"] != "reviewed":
            problems.add(("operation-contract-review-required", subject_id))
        for field, expected in (
            ("invocation_ids", set(subject["invocation_ids"])),
            ("observation_ids", {item["id"] for item in observations.values() if item["subject_id"] == subject_id}),
            ("dependency_ids", {item["id"] for item in dependencies.values() if item["subject_id"] == subject_id}),
        ):
            if set(binding[field]) != expected:
                problems.add(("operation-" + field.replace("_ids", "").replace("_", "-") + "-coverage-incomplete", subject_id))
    source_findings = {(item["code"], item["subject_id"]) for item in caller_result["source_findings"]}
    source_findings.update((item["code"], item["subject_id"]) for item in inventory["findings"])
    obligations = []
    if not problems:
        for subject_id, binding in sorted(bindings.items()):
            obligations.append({
                "subject_id": subject_id, "operation_id": binding["operation_id"], "owner": binding["owner"],
                "operation_profile": binding["operation_profile"], "profile_basis": "reviewed-source-declaration",
                "argument_policy": "observed-variants-only", "unobserved_arguments": "blocked",
                "source_closure": "blocked", "qualification": "pending",
                "required_evidence": [{"stage": stage, "proof": proof} for stage, proof in EVIDENCE_STAGES],
            })
    policy_revision = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result = {
        "schema": "source-operation-result/v1", "scope": "operation-contracts", "authorized": False,
        "contracts_verdict": "incomplete" if problems else "complete", "source_closure": "blocked",
        "qualification_verdict": "blocked", "target_id": caller_review["target_id"],
        "inventory_digest": inventory["inventory_digest"], "graph_digest": graph["graph_digest"],
        "caller_accounting_digest": caller_result["accounting_digest"], "policy_revision": policy_revision,
        "counts": {"subjects": len(subjects), "invocations": sum(len(item["invocation_ids"]) for item in subjects.values()),
                   "observations": len(observations), "dependencies": len(dependencies)},
        "obligations": obligations,
        "findings": [{"code": code, "subject_id": subject} for code, subject in sorted(problems)],
        "source_findings": [{"code": code, "subject_id": subject} for code, subject in sorted(source_findings)],
    }
    if not problems:
        result["contracts_digest"] = release.digest_document({
            "inventory": inventory["inventory_digest"], "contracts": contracts,
            "caller_accounting": caller_result["accounting_digest"],
            "schema_digests": [inventory_schema_digest, contract_schema_digest], "policy_revision": policy_revision,
        })
    return result
