#!/usr/bin/env python3
"""Account for discovered caller subjects without qualifying their behavior."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-caller-coverage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reconcile source-bound caller graphs and reviewed operation profiles.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from pathlib import Path
import hashlib

import source_coverage as coverage
import release_compiler as release

CallerFailure = coverage.CoverageFailure
validate_schema = coverage.validate_schema


def checked_graph(graph):
    schema_digest = validate_schema("caller-inventory", graph)
    if release.digest_document({key: value for key, value in graph.items() if key != "graph_digest"}) != graph["graph_digest"]:
        raise CallerFailure("caller-graph-digest-invalid")
    sources = coverage.unique(graph["sources"], "id")
    nodes = coverage.unique(graph["nodes"], "id")
    edges = coverage.unique(graph["edges"], "id")
    root = graph["entrypoint"]["node_id"]
    if root not in nodes or nodes[root]["kind"] != "workflow":
        raise CallerFailure("caller-graph-root-invalid")
    if any(node["source_id"] not in sources for node in nodes.values()):
        raise CallerFailure("caller-graph-source-invalid")
    if sources[nodes[root]["source_id"]]["path"] != graph["entrypoint"]["path"]:
        raise CallerFailure("caller-graph-root-invalid")
    adjacency = {node_id: set() for node_id in nodes}
    for edge in edges.values():
        if edge["caller_id"] not in nodes or edge["callee_id"] not in nodes:
            raise CallerFailure("caller-graph-edge-invalid")
        adjacency[edge["caller_id"]].add(edge["callee_id"])
    reached, pending = set(), [root]
    while pending:
        node_id = pending.pop()
        if node_id not in reached:
            reached.add(node_id)
            pending.extend(adjacency[node_id] - reached)
    if reached != set(nodes):
        raise CallerFailure("caller-graph-unreachable-subject")
    if any(finding["subject_id"] not in nodes for finding in graph["findings"]):
        raise CallerFailure("caller-graph-finding-invalid")
    # The public CLI recollects independently; this API is not evidence admission.
    return schema_digest, nodes, edges


def make_review(graph, target_id="sandbox/delivery"):
    checked_graph(graph)
    result = {
        "schema": "source-caller-review/v1", "graph_digest": graph["graph_digest"], "target_id": target_id,
        "bindings": [{"node_id": node["id"], "operation_id": "caller-" + node["id"][7:39],
                      "owner": "release-control-programme", "operation_profile": "unclassified",
                      "review_status": "pending"} for node in graph["nodes"]],
        "edge_ids": sorted(edge["id"] for edge in graph["edges"]),
    }
    validate_schema("source-caller-review", result)
    return result


def compile_callers(graph, review):
    graph_schema_digest, nodes, edges = checked_graph(graph)
    review_schema_digest = validate_schema("source-caller-review", review)
    release.bounded_json(review)
    bindings = coverage.unique(review["bindings"], "node_id")
    coverage.unique(review["bindings"], "operation_id")
    problems = set()
    if review["graph_digest"] != graph["graph_digest"]:
        problems.add(("caller-review-stale", graph["entrypoint"]["node_id"]))
    if set(bindings) != set(nodes):
        problems.add(("caller-subject-coverage-incomplete", graph["entrypoint"]["node_id"]))
    if set(review["edge_ids"]) != set(edges):
        problems.add(("caller-edge-coverage-incomplete", graph["entrypoint"]["node_id"]))
    for node_id, binding in bindings.items():
        if binding["review_status"] != "reviewed":
            problems.add(("caller-review-required", node_id))
        if binding["operation_profile"] == "unclassified":
            problems.add(("caller-profile-unclassified", node_id))
    source_findings = {(item["code"], item["subject_id"]) for item in graph["findings"]}
    source_findings.update((code, node_id) for node_id, node in nodes.items() for code in node["issues"])
    # Source review assigns obligations. It cannot admit an execution receipt.
    obligations = []
    if not problems:
        for node_id, binding in sorted(bindings.items()):
            obligations.append({
                "subject_id": node_id, "operation_id": binding["operation_id"], "owner": binding["owner"],
                "operation_profile": binding["operation_profile"], "profile_basis": "reviewed-source-declaration",
                "source_closure": "unresolved" if any(subject == node_id for code, subject in source_findings) else "literal-invocations-accounted",
                "required_gate": 2, "required_proof": "independent-caller-and-operation-coverage",
                "qualification": "pending", "later_release_stages": list(range(3, 18)),
            })
    policy_revision = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result = {
        "schema": "source-caller-result/v1", "scope": "caller-accounting", "authorized": False,
        "accounting_verdict": "incomplete" if problems else "accounted", "qualification_verdict": "blocked",
        "target_id": review["target_id"],
        "graph_digest": graph["graph_digest"], "policy_revision": policy_revision,
        "subject_count": len(nodes), "edge_count": len(edges), "obligations": obligations,
        "findings": [{"code": code, "subject_id": subject} for code, subject in sorted(problems)],
        "source_findings": [{"code": code, "subject_id": subject} for code, subject in sorted(source_findings)],
    }
    if not problems:
        result["accounting_digest"] = release.digest_document({"graph": graph["graph_digest"], "review": review,
            "schema_digests": [graph_schema_digest, review_schema_digest], "policy_revision": policy_revision})
    return result
