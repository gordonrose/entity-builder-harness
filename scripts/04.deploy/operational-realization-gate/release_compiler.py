#!/usr/bin/env python3
"""Compile source release obligations through the existing realization gate."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-release-compiler
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate immutable release definitions and compile seventeen safe acceptance obligations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import yaml
from jsonschema import Draft202012Validator

import script as realization


SCHEMA_DIR = Path(__file__).resolve().parents[3] / "infra/04.deploy/contracts/release-control/v1"
SCHEMA_FILES = {
    "release-definition/v1": "release-definition.schema.yml",
    "release-acceptance-matrix/v1": "acceptance-matrix.schema.yml",
}
RESULT_SCHEMA = "release-control-result/v1"
MAX_BYTES = 1024 * 1024
MAX_DEPTH = 32
MAX_NODES = 20000
BINDINGS = (
    "release_id", "target_id", "source_revision", "target_composition_revision",
    "artifact_digests", "environment_contract_revision", "evidence_policy_revision",
    "realization_contract_digest",
)


class ReleaseFailure(Exception):
    """A fixed diagnostic code, never an input value or parser exception."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


class StrictLoader(yaml.SafeLoader):
    """Reject duplicate keys and aliases instead of accepting ambiguous input."""

    def compose_node(self, parent, index):
        event = self.peek_event()
        if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None):
            raise ReleaseFailure("document-alias-unsupported")
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise ReleaseFailure("document-key-invalid")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def bounded_json(value, *, max_nodes=MAX_NODES):
    """Check in-memory callers too, before recursive validators see the data."""
    stack = [(value, 0)]
    containers = set()
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if count > max_nodes or depth > MAX_DEPTH:
            raise ReleaseFailure("document-limit-exceeded")
        if type(item) in (dict, list):
            if id(item) in containers:
                raise ReleaseFailure("document-alias-unsupported")
            containers.add(id(item))
            if isinstance(item, dict):
                if any(type(key) is not str for key in item):
                    raise ReleaseFailure("document-key-invalid")
                stack.extend((key, depth + 1) for key in item)
                stack.extend((entry, depth + 1) for entry in item.values())
            else:
                stack.extend((entry, depth + 1) for entry in item)
        elif type(item) is str:
            if len(item) > 16384 or any(ord(char) < 32 for char in item):
                raise ReleaseFailure("document-string-invalid")
        elif type(item) is int:
            if abs(item) > 2**63 - 1:
                raise ReleaseFailure("document-number-invalid")
        elif item is not None and type(item) is not bool:
            raise ReleaseFailure("document-type-invalid")


def load_document(path, code="release-definition-unreadable"):
    try:
        path = Path(path)
        if not path.is_file():
            raise ReleaseFailure(code)
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ReleaseFailure("document-limit-exceeded")
        value = yaml.load(raw.decode("utf-8"), Loader=StrictLoader)
        bounded_json(value)
        if not isinstance(value, dict):
            raise ReleaseFailure(code)
        return value
    except ReleaseFailure:
        raise
    except (OSError, ValueError, yaml.YAMLError, RecursionError):
        raise ReleaseFailure(code) from None


def digest_document(document):
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_schemas(schema_dir):
    schemas = {}
    for version, filename in SCHEMA_FILES.items():
        schema = load_document(Path(schema_dir) / filename, "schema-unreadable")
        # Schemas are local source inputs. Never resolve a remote schema reference.
        stack = [schema]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                if "$dynamicRef" in item or ("$ref" in item and not str(item["$ref"]).startswith("#/")):
                    raise ReleaseFailure("schema-reference-unsupported")
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
        expected_id = "urn:release-control:" + ("release-definition:v1" if version == "release-definition/v1" else "acceptance-matrix:v1")
        properties = schema.get("properties", {})
        version_property = properties.get("schema", {}) if isinstance(properties, dict) else {}
        if (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
                or schema.get("$id") != expected_id
                or not isinstance(version_property, dict) or version_property.get("const") != version):
            raise ReleaseFailure("schema-version-unsupported")
        try:
            Draft202012Validator.check_schema(schema)
        except Exception:
            raise ReleaseFailure("schema-invalid") from None
        schemas[version] = schema
    return schemas


def validate_shape(document, schemas):
    bounded_json(document)
    if not isinstance(document, dict) or document.get("schema") != "release-definition/v1":
        raise ReleaseFailure("release-schema-unsupported")
    try:
        realization.reject_unsafe_value_fields(document)
        realization.reject_provider_leakage(document)
    except realization.ContractFailure as error:
        raise ReleaseFailure(error.code) from None
    for version, value in (
        ("release-definition/v1", document),
        ("release-acceptance-matrix/v1", document.get("acceptance_matrix")),
    ):
        try:
            invalid = next(Draft202012Validator(schemas[version]).iter_errors(value), None)
        except Exception:
            raise ReleaseFailure("schema-invalid") from None
        if invalid is not None:
            raise ReleaseFailure("release-definition-invalid" if version == "release-definition/v1" else "acceptance-matrix-invalid")
    for row in document["acceptance_matrix"]["rows"]:
        if row["verdict"] == "not-applicable":
            raise ReleaseFailure("applicability-unsupported")
        if row["verdict"] != "not-started":
            raise ReleaseFailure("evidence-verdict-unsupported")


def indexed(items, key, code):
    result = {item[key]: item for item in items}
    if len(result) != len(items):
        raise ReleaseFailure(code)
    return result


def validate_bindings(document, contract):
    bounded_json(contract)
    if not isinstance(contract, dict):
        raise ReleaseFailure("realization-contract-invalid")
    try:
        realization.validate_contract(contract)
    except (realization.ContractFailure, KeyError, TypeError, ValueError):
        raise ReleaseFailure("realization-contract-invalid") from None
    if digest_document(contract) != document["realization_contract_digest"]:
        raise ReleaseFailure("realization-contract-binding-mismatch")
    artifacts = indexed(document["artifact_digests"], "artifact_id", "artifact-binding-duplicate")
    declared_artifacts = {item["id"]: item for item in contract["artifacts"]}
    if set(artifacts) != set(declared_artifacts):
        raise ReleaseFailure("artifact-binding-incomplete")
    for name, item in declared_artifacts.items():
        if "immutable_reference" in item and item["immutable_reference"] != artifacts[name]["digest"]:
            raise ReleaseFailure("artifact-binding-mismatch")
    units = {item["id"]: item for item in contract["execution_units"]}
    recovery = {item["id"]: item for item in contract["recovery_plans"]}
    operations = indexed(document["operation_graph"], "operation_id", "operation-duplicate")
    if {item["execution_unit"] for item in operations.values()} != set(units):
        raise ReleaseFailure("execution-unit-coverage-invalid")
    preceding = set()
    for operation_id, operation in operations.items():
        if not set(operation["depends_on"]).issubset(preceding):
            raise ReleaseFailure("operation-dependency-invalid")
        preceding.add(operation_id)
        unit = units[operation["execution_unit"]]
        artifact = declared_artifacts[unit["artifact"]]
        if (operation["artifact_id"] != unit["artifact"]
                or operation["acting_identity"] != unit["identity"]
                or operation["command_ref"] != artifact["entrypoint"]):
            raise ReleaseFailure("operation-binding-mismatch")
    stage_bindings = {}
    for row in document["acceptance_matrix"]["rows"]:
        selected = row["operation_ids"]
        if set(selected) != set(operations):
            # Until independent applicability exists, omission is an exemption.
            raise ReleaseFailure("gate-operation-coverage-incomplete")
        overrides = indexed(row.get("operation_overrides", []), "operation_id", "operation-override-duplicate")
        if not set(overrides) < set(operations):
            raise ReleaseFailure("operation-override-invalid")
        normalized = []
        for operation_id in selected:
            operation = operations[operation_id]
            requirement = overrides.get(operation_id, row)
            route = recovery[units[operation["execution_unit"]]["recovery_plan"]]
            if (any(requirement[field] != operation[field] for field in ("acting_identity", "operation_profile", "command_ref"))
                    or requirement["recovery_route"] != route["id"] or requirement["cleanup_route"] != route["cleanup"]):
                raise ReleaseFailure("gate-operation-binding-mismatch")
            indexed(requirement["evidence_requirements"], "check_id", "evidence-rule-duplicate")
            binding = {key: deepcopy(requirement[key]) for key in (
                "acting_identity", "operation_profile", "command_ref", "evidence_requirements",
                "recovery_route", "cleanup_route",
            )}
            binding.update(operation_id=operation_id, execution_unit=operation["execution_unit"],
                           artifact_id=operation["artifact_id"], artifact_digest=artifacts[operation["artifact_id"]]["digest"])
            normalized.append(binding)
        stage_bindings[row["gate"]] = normalized
    return stage_bindings


def compile_release(document, contract, baseline=None, schema_dir=SCHEMA_DIR):
    """Return obligations, never runtime evidence or permission to execute."""
    schemas = load_schemas(schema_dir)
    validate_shape(document, schemas)
    if baseline is not None:
        validate_shape(baseline, schemas)
        if baseline["release_id"] == document["release_id"] and digest_document(baseline) != digest_document(document):
            raise ReleaseFailure("immutable-release-rebound")
    stage_bindings = validate_bindings(document, contract)
    schema_digests = {version: digest_document(schema) for version, schema in schemas.items()}
    release_digest = digest_document({"definition": document, "schema_digests": schema_digests})
    bindings = {name: deepcopy(document[name]) for name in BINDINGS}
    bindings["release_digest"] = release_digest
    rows = []
    prior = []
    for stage, row in enumerate(document["acceptance_matrix"]["rows"], 1):
        normalized = deepcopy(row)
        normalized.pop("operation_overrides", None)
        normalized.update(stage=stage, prerequisites=list(prior), bindings=deepcopy(bindings))
        normalized["operation_bindings"] = stage_bindings[row["gate"]]
        rows.append(normalized)
        prior.append(row["gate"])
    return {
        "schema": RESULT_SCHEMA, "scope": "release-definition", "verdict": "compiled",
        "authorized": False, "release_digest": release_digest, "schema_digests": schema_digests,
        "operation_graph": deepcopy(document["operation_graph"]), "risk_tier": document["risk_tier"],
        "acceptance_matrix": rows, "findings": [],
    }


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise ReleaseFailure("arguments-invalid")


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        options = [argument.split("=", 1)[0] for argument in argv if argument.startswith("--")]
        if len(options) != len(set(options)):
            raise ReleaseFailure("arguments-invalid")
        parser = SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument("--release", required=True)
        parser.add_argument("--contract", required=True)
        parser.add_argument("--baseline-release")
        parser.add_argument("--json", action="store_true")
        args = parser.parse_args(argv)
        document = load_document(args.release)
        contract = load_document(args.contract, "realization-contract-unreadable")
        baseline = load_document(args.baseline_release, "baseline-release-unreadable") if args.baseline_release else None
        result = compile_release(document, contract, baseline)
    except ReleaseFailure as error:
        result = {"schema": RESULT_SCHEMA, "scope": "release-definition", "verdict": "failed",
                  "authorized": False, "findings": [{"code": error.code}]}
    except Exception:
        # Parser, dependency and validator internals must never expose input data.
        result = {"schema": RESULT_SCHEMA, "scope": "release-definition", "verdict": "failed",
                  "authorized": False, "findings": [{"code": "release-compilation-failed"}]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verdict"] == "compiled" else 1


if __name__ == "__main__":
    raise SystemExit(main())
