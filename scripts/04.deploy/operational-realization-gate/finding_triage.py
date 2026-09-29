#!/usr/bin/env python3
"""Assign bounded source findings to open work; never resolve or waive them."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-finding-triage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate complete revision-bound finding intake without suppressing coverage blockers.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import hashlib
from pathlib import Path

import source_coverage as coverage
import release_compiler as release


ROUTES = ("phase-2-source", "phase-3-artifact", "phase-5-provider")
POLICY = {
    "opaque-executable": ("phase-2-source", "trace-command-callers"),
    "opaque-export-target": ("phase-2-source", "trace-package-entrypoint"),
    "resource-type-unsupported": ("phase-2-source", "extend-resource-source-grammar"),
    "source-alias-unsupported": ("phase-2-source", "support-source-yaml-grammar"),
    "workflow-action-unresolved": ("phase-2-source", "trace-workflow-action"),
    "image-command-unsupported": ("phase-2-source", "extend-image-command-grammar"),
    "container-image-unresolved": ("phase-2-source", "resolve-image-source-binding"),
    "container-command-inherited": ("phase-3-artifact", "inspect-final-artifact-command"),
    "image-entrypoint-inherited": ("phase-3-artifact", "inspect-final-artifact-command"),
    "opaque-image-build": ("phase-3-artifact", "qualify-image-build"),
}
UNKNOWN = ("phase-2-source", "investigate-source-grammar")


def inventory_findings(inventory):
    """Internal collector input only; public commands must recollect the tree."""
    coverage.validate_schema("source-inventory", inventory)
    if release.digest_document({key: value for key, value in inventory.items()
                                if key != "inventory_digest"}) != inventory["inventory_digest"]:
        raise coverage.CoverageFailure("inventory-digest-invalid")
    sources = coverage.unique(inventory["sources"], "id")
    observations = coverage.unique(inventory["observations"], "id")
    findings = {(item["source_id"], item["code"]) for item in inventory["findings"]}
    for observed in observations.values():
        if observed["source_id"] not in sources or observed["subject_id"] not in observations:
            raise coverage.CoverageFailure("triage-inventory-reference-invalid")
        findings.update((observed["source_id"], code) for code in observed["issues"])
    if any(source_id not in sources for source_id, _ in findings):
        raise coverage.CoverageFailure("triage-inventory-reference-invalid")
    return sources, findings


def policy_revision():
    """Bind routing implementation, route table and loaded closed schema."""
    try:
        module_digest = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError:
        raise coverage.CoverageFailure("triage-policy-unreadable") from None
    schema = release.load_document(coverage.SCHEMA_DIR / "source-finding-triage.schema.yml",
                                   "triage-schema-unreadable")
    return release.digest_document({"module_digest": module_digest, "routing": POLICY,
                                    "unknown": UNKNOWN, "schema_digest": release.digest_document(schema)})


def make_triage(inventory):
    """Generate open intake work, not human approval or completed proof."""
    sources, findings = inventory_findings(inventory)
    result = {
        "schema": "source-finding-triage/v1",
        "inventory_digest": inventory["inventory_digest"],
        "collector_revision": inventory["collector_revision"],
        "policy_revision": policy_revision(),
        "entries": [{
            "source_id": source_id, "source_digest": sources[source_id]["digest"], "code": code,
            "intake_owner": "release-control-programme", "route": POLICY.get(code, UNKNOWN)[0],
            "next_action": POLICY.get(code, UNKNOWN)[1], "status": "open",
        } for source_id, code in sorted(findings)],
    }
    release.bounded_json(result)
    coverage.validate_schema("source-finding-triage", result)
    return result


def compile_triage(inventory, triage):
    """Classify current findings; all original source blockers remain in force."""
    release.bounded_json(triage)
    coverage.validate_schema("source-finding-triage", triage)
    sources, expected = inventory_findings(inventory)
    current_policy = policy_revision()
    diagnostics = set()

    def issue(code, source_id=None):
        diagnostics.add((code, source_id or ""))

    if triage["inventory_digest"] != inventory["inventory_digest"]:
        issue("triage-inventory-stale")
    if triage["collector_revision"] != inventory["collector_revision"]:
        issue("triage-collector-stale")
    if triage["policy_revision"] != current_policy:
        issue("triage-policy-stale")
    entries = {}
    duplicate_pairs = set()
    for entry in triage["entries"]:
        pair = (entry["source_id"], entry["code"])
        if pair in entries:
            issue("triage-finding-duplicate", entry["source_id"])
            duplicate_pairs.add(pair)
        entries[pair] = entry
    for source_id, _ in expected - entries.keys():
        issue("triage-finding-missing", source_id)
    for source_id, _ in entries.keys() - expected:
        issue("triage-finding-unknown", source_id)

    classified = set()
    route_counts = {route: 0 for route in ROUTES}
    for pair in sorted(expected & entries.keys()):
        source_id, code = pair
        entry = entries[pair]
        valid = pair not in duplicate_pairs
        if entry["source_digest"] != sources[source_id]["digest"]:
            issue("triage-source-stale", source_id)
            valid = False
        if code not in POLICY:
            issue("triage-code-policy-unsupported", source_id)
            valid = False
        if (entry["route"], entry["next_action"]) != POLICY.get(code, UNKNOWN):
            issue("triage-route-policy-mismatch", source_id)
            valid = False
        if valid:
            classified.add(pair)
            route_counts[entry["route"]] += 1
    return {
        "schema": "source-triage-result/v1", "scope": "finding-triage", "authorized": False,
        "inventory_digest": inventory["inventory_digest"],
        "collector_revision": inventory["collector_revision"], "policy_revision": current_policy,
        "classification_verdict": "incomplete" if diagnostics else "complete",
        "coverage_verdict": "blocked" if expected else "clear-source-findings",
        "counts": {"sources": len(sources), "source_findings": len(expected),
                   "entries": len(triage["entries"]), "classified_findings": len(classified),
                   "by_route": route_counts},
        "findings": [{"code": code, **({"source_id": source_id} if source_id else {})}
                     for code, source_id in sorted(diagnostics)],
    }
