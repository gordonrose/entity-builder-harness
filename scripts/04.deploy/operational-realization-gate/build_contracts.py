#!/usr/bin/env python3
"""Validate bounded build observations using closed local versioned contracts."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-build-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate independently collected build inputs and local artifact accounting without granting authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from jsonschema import Draft202012Validator

import release_compiler as release
import source_coverage

SCHEMA_DIR = release.SCHEMA_DIR
MAX_INTERNAL_NODES = 500000
NAMES = {"qualified-image-handoff", "source-build-inventory", "source-build-artifact", "local-typescript-observation", "local-typescript-emission-observation",
         "local-runtime-observation", "local-workspace-runtime-observation", "local-build-result", "local-container-lock", "local-container-result",
         "finite-job-profile", "finite-job-result", "dependency-effect-profile", "dependency-effect-result",
         "artifact-admission-policy", "artifact-admission-result", "artifact-verifier-lock", "artifact-scan-predicate", "artifact-verifier-conformance", "artifact-admission-error", "operation-control", "operation-journal", "operation-evidence",
         "control-store-conformance", "control-store-error", "estate-caller-inventory",
         "estate-caller-reconciliation", "estate-caller-error", "finite-recovery-attempt",
         "finite-recovery-observation", "finite-recovery-result", "finite-recovery-conformance",
         "finite-recovery-error", "finite-recovery-image-lock", "candidate-lifecycle-attempt", "candidate-lifecycle-observation", "operation-action-record"}


def validate_schema(name, document):
    # These larger observations only originate in bounded local collectors.
    # Public input documents retain the release loader's existing size limits.
    if name not in NAMES:
        raise release.ReleaseFailure("build-schema-unsupported")
    release.bounded_json(document, max_nodes=MAX_INTERNAL_NODES)
    schema = release.load_document(SCHEMA_DIR / (name + ".schema.yml"),
                                   "build-schema-unreadable")
    if (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("$id") != "urn:release-control:" + name + ":v1"
            or schema.get("type") != "object"
            or schema.get("properties", {}).get("schema") != {"const": name + "/v1"}):
        raise release.ReleaseFailure("build-schema-version-invalid")
    pending = [schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if any(key in value for key in ("$ref", "$dynamicRef", "$recursiveRef")):
                raise release.ReleaseFailure("build-schema-reference-unsupported")
            if value.get("type") == "object" or "properties" in value:
                fields, required = value.get("properties"), value.get("required")
                if (value.get("type") != "object" or value.get("additionalProperties") is not False
                        or not isinstance(fields, dict) or not isinstance(required, list)
                        or any(type(key) is not str for key in required)
                        or len(set(required)) != len(required) or set(required) != set(fields)):
                    raise release.ReleaseFailure("build-schema-open")
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    try:
        Draft202012Validator.check_schema(schema)
        if next(Draft202012Validator(schema).iter_errors(document), None):
            raise release.ReleaseFailure(name + "-invalid")
    except release.ReleaseFailure:
        raise
    except Exception:
        raise release.ReleaseFailure("build-schema-invalid") from None
    return release.digest_document(schema)


def checked_inventory(inventory):
    validate_schema("source-build-inventory", inventory)
    if release.digest_document({key: value for key, value in inventory.items()
                                if key != "inventory_digest"}) != inventory["inventory_digest"]:
        raise release.ReleaseFailure("build-inventory-digest-invalid")
    sources = source_coverage.unique(inventory["sources"], "id")
    source_coverage.unique(inventory["sources"], "path")
    builds = source_coverage.unique(inventory["builds"], "id")
    source_coverage.unique(inventory["bindings"], "id")
    source_coverage.unique(inventory["edges"], "id")
    for build in builds.values():
        if (build["source_id"] not in sources or build["config_source_id"] not in sources
                or any(item not in sources for item in build["root_source_ids"])
                or any(item not in sources for item in build["workspace_source_ids"])):
            raise release.ReleaseFailure("build-source-reference-invalid")
        paths = [item["path"] for item in build["expected_outputs"]]
        if len(set(paths)) != len(paths):
            raise release.ReleaseFailure("build-output-duplicate")
        if any(item["source_id"] not in sources for item in build["expected_outputs"]):
            raise release.ReleaseFailure("build-source-reference-invalid")
    for row in inventory["bindings"]:
        if row["build_id"] not in builds or row["source_id"] not in sources:
            raise release.ReleaseFailure("build-binding-reference-invalid")
    for row in inventory["edges"]:
        if (row["build_id"] not in builds or row["from_source_id"] not in sources
                or row["to_source_id"] not in sources):
            raise release.ReleaseFailure("build-edge-reference-invalid")
    for row in inventory["findings"]:
        if row["build_id"] not in builds:
            raise release.ReleaseFailure("build-finding-reference-invalid")
    findings = [(row["build_id"], row["code"]) for row in inventory["findings"]]
    if len(set(findings)) != len(findings):
        raise release.ReleaseFailure("build-finding-duplicate")
    return inventory
