#!/usr/bin/env python3
"""Reconcile independent source observations without granting runtime authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-source-coverage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind source inventory, reviewed adoption and composition to scoped release obligations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from jsonschema import Draft202012Validator
import release_compiler as release

DISCOVERY_PATH = Path(__file__).resolve().parent.parent / "release-control/discovery"
sys.path.insert(0, str(DISCOVERY_PATH))
from source_inventory import discover

SCHEMA_DIR = release.SCHEMA_DIR
SCHEMAS = {
    "source-inventory": "source-inventory/v1",
    "source-composition": "release-source-composition/v1",
    "source-adoption-ledger": "source-adoption-ledger/v1",
}
EXECUTABLES = {
    "package-command", "package-bin", "script-entrypoint", "source-entrypoint",
    "workflow-step", "workflow-service", "container",
}
BINDING_KINDS = {
    "command-binding": "command", "configuration-binding": "configuration",
    "secret-binding": "secret", "identity-binding": "identity",
}
ARTIFACT_KINDS = {"image-command", "package-export", "container", "source-entrypoint", "script-entrypoint"}
RULE_VERSION = "source-coverage/v1"


class CoverageFailure(release.ReleaseFailure):
    """Fixed diagnostics shared by source-only command modes."""


def validate_schema(name, document):
    schema = release.load_document(SCHEMA_DIR / (name + ".schema.yml"), "coverage-schema-unreadable")
    if (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("$id") != "urn:release-control:" + name + ":v1"):
        raise CoverageFailure("coverage-schema-version-invalid")
    # This closed source format uses no references, including no remote resolver.
    stack = [schema]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            if "$ref" in value or "$dynamicRef" in value:
                raise CoverageFailure("coverage-schema-reference-unsupported")
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    try:
        Draft202012Validator.check_schema(schema)
        if next(Draft202012Validator(schema).iter_errors(document), None):
            raise CoverageFailure(name + "-invalid")
    except CoverageFailure:
        raise
    except Exception:
        raise CoverageFailure("coverage-schema-invalid") from None
    return release.digest_document(schema)


def unique(items, key):
    result = {item[key]: item for item in items}
    if len(result) != len(items):
        raise CoverageFailure("coverage-duplicate-identity")
    return result


def make_ledger(inventory):
    """Generate review work, never self-approve a discovered source path."""
    validate_schema("source-inventory", inventory)
    return {
        "schema": "source-adoption-ledger/v1", "inventory_digest": inventory["inventory_digest"],
        "entries": [{"source_id": item["id"], "source_digest": item["digest"],
                     "owner": "release-control-programme", "disposition": "migrate",
                     "review_status": "pending"} for item in inventory["sources"]],
    }


def compile_coverage(inventory, composition, ledger, as_of=None, release_document=None, contract=None, source_root=None):
    """Internal API; public commands always collect from the source tree afresh."""
    schema_digests = {name: validate_schema(name, value) for name, value in (
        ("source-inventory", inventory), ("source-composition", composition), ("source-adoption-ledger", ledger),
    )}
    # Declaration strings must never smuggle commands, endpoints or control bytes.
    release.bounded_json(composition)
    release.bounded_json(ledger)
    try:
        today = date.fromisoformat(as_of) if as_of else date.today()
    except (ValueError, TypeError):
        raise CoverageFailure("coverage-date-invalid") from None
    inventory_body = {key: value for key, value in inventory.items() if key != "inventory_digest"}
    if release.digest_document(inventory_body) != inventory["inventory_digest"]:
        raise CoverageFailure("inventory-digest-invalid")
    sources = unique(inventory["sources"], "id")
    observations = unique(inventory["observations"], "id")
    entries = unique(ledger["entries"], "source_id")
    operations = unique(composition["operations"], "id")
    artifacts = unique(composition["artifacts"], "id")
    resources = unique(composition["resources"], "id")
    findings = set()
    caller_reconciliation = None
    resolved_observations, resolved_source_findings = set(), set()
    if source_root is not None:
        # Only a fresh local collection can supply structural resolutions. There
        # is deliberately no uploaded graph/proof argument to this public seam.
        import estate_caller_coverage
        caller_reconciliation = estate_caller_coverage.reconcile_estate(source_root, inventory)
        resolved_observations = {row['observation_id'] for row in caller_reconciliation['resolved_observations']}
        resolved_source_findings = {(row['code'], row['source_id'])
                                    for row in caller_reconciliation['resolved_source_findings']}
        findings.update((row['code'], row['subject_id'])
                        for row in caller_reconciliation['boundary_findings'])

    def issue(code, subject="source-scope"):
        findings.add((code, subject))

    for observed in observations.values():
        if observed["source_id"] not in sources:
            issue("observation-source-unknown", observed["id"])
        if observed["subject_id"] not in observations:
            issue("observation-subject-unknown", observed["id"])
        for code in observed["issues"]:
            if code != 'opaque-executable' or observed['id'] not in resolved_observations:
                issue(code, observed["id"])
    for finding in inventory["findings"]:
        if (finding['code'], finding['source_id']) not in resolved_source_findings:
            issue(finding["code"], finding["source_id"])
    if composition["inventory_digest"] != inventory["inventory_digest"] or ledger["inventory_digest"] != inventory["inventory_digest"]:
        issue("source-snapshot-stale")
    if set(entries) != set(sources):
        issue("adoption-source-coverage-incomplete")
    for source_id, entry in entries.items():
        if source_id not in sources or entry["source_digest"] != sources[source_id]["digest"]:
            issue("adoption-source-stale", source_id)
        if entry["review_status"] != "reviewed":
            issue("adoption-review-required", source_id)
        if entry["disposition"] in {"historical", "retire", "test-only"}:
            # Caller/retirement evidence is not yet a supported source grammar.
            issue("adoption-exclusion-unproven", source_id)
        if entry["disposition"] == "temporary-compatible":
            try:
                expiry = date.fromisoformat(entry.get("expires_on", ""))
                if expiry <= today or "replacement_profile" not in entry:
                    issue("adoption-compatibility-expired", source_id)
            except ValueError:
                issue("adoption-compatibility-expiry-required", source_id)

    operation_observations = {}
    artifact_observations = set()
    resource_observations = {}
    used_artifacts = set()
    for artifact_id, artifact in artifacts.items():
        for observation_id in artifact["observation_ids"]:
            if observation_id not in observations or observations[observation_id]["kind"] not in ARTIFACT_KINDS:
                issue("artifact-source-binding-invalid", artifact_id)
            elif observations[observation_id]["kind"] in {"container", "image-command"} and artifact["kind"] != "container-image":
                issue("artifact-kind-source-mismatch", artifact_id)
            artifact_observations.add(observation_id)
    for operation_id, operation in operations.items():
        if len(operation["observation_ids"]) != 1:
            # Aliases need independently proven caller equivalence, not a declaration.
            issue("operation-executable-coverage-ambiguous", operation_id)
        if operation["artifact_id"] not in artifacts:
            issue("operation-artifact-unknown", operation_id)
        used_artifacts.add(operation["artifact_id"])
        for observation_id in operation["observation_ids"]:
            if observation_id not in observations or observations[observation_id]["kind"] not in EXECUTABLES:
                issue("operation-source-binding-invalid", operation_id)
            if observation_id in operation_observations:
                issue("operation-source-binding-duplicate", observation_id)
            operation_observations[observation_id] = operation_id
        for access in operation["resource_access"]:
            resource = resources.get(access["resource_id"])
            if resource is None or access["effect"] not in resource["permitted_effects"]:
                issue("operation-resource-effect-unpermitted", operation_id)
    if used_artifacts != set(artifacts):
        issue("artifact-operation-coverage-incomplete")
    for resource_id, resource in resources.items():
        expected_kind = "resource" if resource["management"] == "managed" else "external-dependency"
        if resource["management"] == "external":
            if not set(resource["permitted_effects"]) <= {"inspect", "consume"} or resource["cleanup_owner"] != "external":
                issue("external-resource-effect-forbidden", resource_id)
        elif resource["cleanup_owner"] != "release":
            issue("managed-resource-cleanup-unowned", resource_id)
        for observation_id in resource["observation_ids"]:
            if observation_id not in observations or observations[observation_id]["kind"] != expected_kind:
                issue("resource-ownership-source-mismatch", resource_id)
            if observation_id in resource_observations:
                issue("resource-source-binding-duplicate", observation_id)
            resource_observations[observation_id] = resource_id

    bindings = set()
    for binding in composition["bindings"]:
        observation_id = binding["observation_id"]
        operation_id = binding["operation_id"]
        observation = observations.get(observation_id)
        pair = (observation_id, operation_id)
        if pair in bindings:
            issue("composition-binding-duplicate", observation_id)
        bindings.add(pair)
        if operation_id not in operations or observation is None:
            issue("composition-binding-unknown", observation_id)
            continue
        expected = BINDING_KINDS.get(observation["kind"])
        if observation["kind"] in {"image-command", "package-export"}:
            expected = "artifact"
        elif observation["kind"] == "external-dependency":
            expected = "dependency"
        if binding["kind"] != expected:
            issue("composition-binding-kind-mismatch", observation_id)
        parent_operation = operation_observations.get(observation["subject_id"])
        if parent_operation is not None and parent_operation != operation_id:
            issue("composition-binding-subject-mismatch", observation_id)
        parent_resource = resource_observations.get(observation["subject_id"])
        if parent_resource and not any(access["resource_id"] == parent_resource for access in operations[operation_id]["resource_access"]):
            issue("composition-resource-access-missing", observation_id)

    bound_observations = {item[0] for item in bindings}
    for operation_id, operation in operations.items():
        artifact = artifacts.get(operation["artifact_id"])
        if artifact is None:
            continue
        artifact_sources = set(artifact["observation_ids"])
        owned_sources = set(operation["observation_ids"])
        owned_artifact_sources = {item for item in owned_sources
                                  if item in observations and observations[item]["kind"] in ARTIFACT_KINDS}
        explicit_sources = {item["observation_id"] for item in composition["bindings"]
                            if item["operation_id"] == operation_id and item["kind"] == "artifact"}
        if not (owned_artifact_sources | explicit_sources) & artifact_sources:
            issue("operation-artifact-source-mismatch", operation_id)
        if not owned_artifact_sources <= artifact_sources or not explicit_sources <= artifact_sources:
            issue("operation-artifact-source-mismatch", operation_id)
    for observation_id, observation in observations.items():
        kind = observation["kind"]
        if kind in EXECUTABLES and observation_id not in operation_observations:
            issue("executable-undeclared", observation_id)
        elif kind in {"image-command", "package-export"} and observation_id not in artifact_observations and observation_id not in bound_observations:
            issue("artifact-undeclared", observation_id)
        elif kind in {"resource", "external-dependency"} and observation_id not in resource_observations:
            issue("resource-undeclared", observation_id)
        elif kind in BINDING_KINDS and observation_id not in bound_observations:
            issue("configuration-or-authority-binding-undeclared", observation_id)
        if kind in BINDING_KINDS:
            parent_operation = operation_observations.get(observation["subject_id"])
            parent_resource = resource_observations.get(observation["subject_id"])
            required_operations = ({parent_operation} if parent_operation else {
                operation_id for operation_id, operation in operations.items()
                if parent_resource and any(access["resource_id"] == parent_resource for access in operation["resource_access"])
            })
            if not required_operations:
                issue("binding-subject-unresolved", observation_id)
            for operation_id in required_operations:
                if (observation_id, operation_id) not in bindings:
                    issue("operation-binding-coverage-incomplete", observation_id)
        if kind == "external-dependency":
            dependency_resource = resource_observations.get(observation_id)
            parent_resource = resource_observations.get(observation["subject_id"])
            consumers = [operation for operation in operations.values()
                         if parent_resource and any(access["resource_id"] == parent_resource
                                                    for access in operation["resource_access"])]
            if not consumers or not dependency_resource:
                issue("dependency-consumer-unresolved", observation_id)
            for operation in consumers:
                if not any(access["resource_id"] == dependency_resource and access["effect"] == "consume"
                           for access in operation["resource_access"]):
                    issue("operation-dependency-coverage-incomplete", observation_id)
    # The reviewed composition must acknowledge every independently resolved
    # template edge. Acknowledgement never substitutes for provider policy or
    # actual parameter/secret value qualification.
    expected_references = {oid for oid, value in observations.items()
                           if value["kind"] == "infrastructure-reference"}
    declared_references = set(composition.get("infrastructure_references", []))
    for oid in expected_references - declared_references:
        issue("infrastructure-reference-undeclared", oid)
    for oid in declared_references - expected_references:
        issue("infrastructure-reference-unknown", oid)
    for oid in expected_references:
        value = observations[oid]
        target = observations.get(value["target_id"])
        consumer = observations.get(value["subject_id"])
        allowed = {"resource", "infrastructure-symbol"}
        if target is None or consumer is None or target["kind"] not in allowed or consumer["kind"] not in allowed:
            issue("infrastructure-reference-target-invalid", oid)
            continue
        target_kind = "resource" if target["kind"] == "resource" else target.get("symbol_kind")
        permitted = {"ref": {"resource", "parameter", "pseudo-parameter"},
                     "sub": {"resource", "parameter", "pseudo-parameter"},
                     "get-att": {"resource"}, "depends-on": {"resource"},
                     "condition": {"condition"}, "mapping": {"mapping"}}
        if target_kind not in permitted[value["reference_kind"]]:
            issue("infrastructure-reference-target-kind-invalid", oid)
        for endpoint in (target, consumer):
            if endpoint["kind"] == "resource" and endpoint["id"] not in resource_observations:
                issue("infrastructure-reference-resource-undeclared", oid)
    # A container's source-owned resource must be within its declared access graph.
    for observation_id, operation_id in operation_observations.items():
        observed = observations.get(observation_id)
        if observed:
            parent = resource_observations.get(observed["subject_id"])
            if parent and not any(access["resource_id"] == parent for access in operations[operation_id]["resource_access"]):
                issue("composition-resource-access-missing", observation_id)

    compiled_release = None
    if release_document is not None:
        if contract is None:
            raise CoverageFailure("realization-contract-required")
        compiled_release = release.compile_release(release_document, contract)
        if release_document["target_composition_revision"] != release.digest_document(composition) or release_document["target_id"] != composition["target_id"]:
            issue("release-composition-binding-mismatch")
        release_operations = {operation["operation_id"]: operation for operation in release_document["operation_graph"]}
        if set(release_operations) != set(operations):
            issue("release-operation-coverage-mismatch")
        for operation_id in set(operations) & set(release_operations):
            if any(operations[operation_id][key] != release_operations[operation_id][key] for key in ("execution_unit", "operation_profile", "artifact_id")):
                issue("release-operation-binding-mismatch", operation_id)
        release_artifacts = {artifact["artifact_id"]: artifact["digest"] for artifact in release_document["artifact_digests"]}
        if release_artifacts != {key: artifact["digest"] for key, artifact in artifacts.items()}:
            issue("release-artifact-binding-mismatch")

    result = {
        "schema": "source-coverage-result/v1", "scope": "source-coverage", "authorized": False,
        "inventory_digest": inventory["inventory_digest"], "verdict": "blocked" if findings else "covered",
        "findings": [{"code": code, "subject_id": subject} for code, subject in sorted(findings)],
        "acceptance_obligations": [],
    }
    if caller_reconciliation is not None:
        result['caller_reconciliation'] = caller_reconciliation
    if not findings:
        rules = release.load_schemas(SCHEMA_DIR)["release-acceptance-matrix/v1"]
        schema_digests["acceptance-matrix"] = release.digest_document(rules)
        policy_revision = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result["coverage_digest"] = release.digest_document({
            "inventory": inventory["inventory_digest"], "composition": composition, "ledger": ledger,
            "schema_digests": schema_digests, "policy_revision": policy_revision, "as_of": today.isoformat(),
            "release_digest": compiled_release["release_digest"] if compiled_release else None,
            "caller_reconciliation_digest": caller_reconciliation["result_digest"] if caller_reconciliation else None,
        })
        result["policy_revision"] = policy_revision
        result["acceptance_obligations"] = generate_obligations(composition, rules)
        if compiled_release:
            result["compiled_release"] = compiled_release
    return result


def generate_obligations(composition, schema):
    """Structural scope decisions; no receipt admission or gate advancement."""
    rows = []
    all_observations = sorted({item for operation in composition["operations"] for item in operation["observation_ids"]})
    for stage, prefix in enumerate(schema["properties"]["rows"]["prefixItems"], 1):
        properties = prefix["allOf"][1]["properties"]
        gate = properties["gate"]["const"]
        evidence_def = schema["$defs"][properties["evidence_requirements"]["items"]["$ref"].rsplit("/", 1)[1]]
        evidence = {
            "proof_levels": evidence_def["properties"]["proof_level"]["enum"],
            "environments": evidence_def["properties"]["environment"]["enum"],
            "observation_window_required": "observation_window_seconds" in evidence_def.get("required", []),
        }
        assertions = []

        def add(scope, subject, basis, rule, applicability="required", **extra):
            assertion = {"scope": scope, "subject_id": subject, "applicability": applicability,
                         "rule": rule, "rule_version": RULE_VERSION, "basis_observation_ids": sorted(basis),
                         "evidence": deepcopy(evidence), "invalidated_by": ["inventory", "composition", "ledger", "policy"], **extra}
            assertion["id"] = release.digest_document({"gate": gate, "assertion": assertion})
            assertions.append(assertion)

        if stage in {1, 2, 3, 4, 16}:
            add("release", composition["target_id"], all_observations, "release-" + gate)
        elif stage == 7:
            for artifact in composition["artifacts"]:
                add("artifact", artifact["id"], artifact["observation_ids"], "immutable-artifact-supply-chain", artifact_kind=artifact["kind"])
        elif stage in {8, 9, 10}:
            # Release review remains mandatory even when every dependency is external.
            add("release", composition["target_id"], all_observations, "release-" + gate)
            for resource in composition["resources"]:
                external = resource["management"] == "external"
                exempt = external and stage in {8, 9}
                add("dependency" if external else "resource", resource["id"], resource["observation_ids"],
                    "external-reference-no-managed-effect" if exempt else "resource-" + gate,
                    "not-applicable" if exempt else "required", provider_boundary=resource["provider_boundary"])
                if external and stage == 8:
                    add("dependency", resource["id"], resource["observation_ids"],
                        "dependency-access-authority", provider_boundary=resource["provider_boundary"])
        else:
            for operation in composition["operations"]:
                rule = "exact-command-in-artifact" if stage == 6 else operation["operation_profile"] + "-" + gate
                add("operation", operation["id"], operation["observation_ids"], rule,
                    operation_profile=operation["operation_profile"], artifact_id=operation["artifact_id"])
        rows.append({"stage": stage, "gate": gate, "assertions": assertions})
    return rows


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        options = [argument.split("=", 1)[0] for argument in argv if argument.startswith("--")]
        if len(options) != len(set(options)):
            raise CoverageFailure("arguments-invalid")
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--discover", action="store_true")
        mode.add_argument("--coverage", action="store_true")
        mode.add_argument("--triage", action="store_true")
        mode.add_argument("--callers", action="store_true")
        parser.add_argument("--source-root", required=True)
        parser.add_argument("--ledger-template", action="store_true")
        parser.add_argument("--composition")
        parser.add_argument("--adoption-ledger")
        parser.add_argument("--release")
        parser.add_argument("--contract")
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--finding-triage")
        parser.add_argument("--workflow")
        parser.add_argument("--caller-review")
        parser.add_argument("--review-template", action="store_true")
        args = parser.parse_args(argv)
        if not args.triage and args.finding_triage:
            raise CoverageFailure("arguments-invalid")
        if not args.callers and any((args.workflow, args.caller_review, args.review_template)):
            raise CoverageFailure("arguments-invalid")
        if (args.triage or args.callers) and any((args.ledger_template, args.composition, args.adoption_ledger, args.release, args.contract)):
            raise CoverageFailure("arguments-invalid")
        if args.discover and any((args.composition, args.adoption_ledger, args.release, args.contract)):
            raise CoverageFailure("arguments-invalid")
        if args.coverage and (args.ledger_template or not args.composition or not args.adoption_ledger or bool(args.release) != bool(args.contract)):
            raise CoverageFailure("arguments-invalid")
        if args.callers:
            if not args.workflow or (args.caller_review and args.review_template):
                raise CoverageFailure("arguments-invalid")
            from caller_inventory import discover_callers
            import caller_coverage
            graph = discover_callers(Path(args.source_root), args.workflow)
            caller_coverage.checked_graph(graph)
            if args.caller_review:
                result = caller_coverage.compile_callers(graph, release.load_document(args.caller_review))
                status = 0 if result["accounting_verdict"] == "accounted" else 1
            else:
                result = caller_coverage.make_review(graph) if args.review_template else graph
                status = 1 if args.review_template or graph["findings"] else 0
        elif args.triage:
            import finding_triage
            inventory = discover(Path(args.source_root))
            if args.finding_triage:
                result = finding_triage.compile_triage(inventory, release.load_document(args.finding_triage))
                status = 0 if result["classification_verdict"] == "complete" else 1
            else:
                result = finding_triage.make_triage(inventory)
                status = 1 if inventory["findings"] or any(item["issues"] for item in inventory["observations"]) else 0
        elif args.discover:
            inventory = discover(Path(args.source_root))
            result = make_ledger(inventory) if args.ledger_template else inventory
            status = 1 if inventory["findings"] or any(item["issues"] for item in inventory["observations"]) else 0
        else:
            inventory = discover(Path(args.source_root))
            result = compile_coverage(inventory, release.load_document(args.composition), release.load_document(args.adoption_ledger),
                                      release_document=release.load_document(args.release) if args.release else None,
                                      contract=release.load_document(args.contract) if args.contract else None,
                                      source_root=Path(args.source_root))
            status = 0 if result["verdict"] == "covered" else 1
    except release.ReleaseFailure as error:
        result = {"schema": "source-coverage-result/v1", "scope": "source-coverage", "verdict": "failed",
                  "authorized": False, "findings": [{"code": error.code}]}
        status = 1
    except Exception:
        result = {"schema": "source-coverage-result/v1", "scope": "source-coverage", "verdict": "failed",
                  "authorized": False, "findings": [{"code": "source-coverage-failed"}]}
        status = 1
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
