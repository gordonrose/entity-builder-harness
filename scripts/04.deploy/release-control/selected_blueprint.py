#!/usr/bin/env python3
"""Bind the selected staging blueprint to actual repository source, without effects."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-release-blueprint
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compile a source-bound selected staging blueprint through the existing neutral release compiler.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.release-blueprint-cli
#     path: scripts/04.deploy/operational-realization-gate/blueprint_cli.py

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

import yaml
from jsonschema import Draft202012Validator

GATE = Path(__file__).resolve().parents[1] / "operational-realization-gate"
if str(GATE) not in sys.path:
    sys.path.insert(0, str(GATE))
import container_profiles as profiles
import release_compiler as release

TARGET = "infra/04.deploy/03.product/targets/kanbien/staging/"
PROFILE = TARGET + "target-profile.yml"
FOUNDATION = TARGET + "cloudformation/foundation.yml"
SCHEMA_FILE = "selected-release-blueprint.schema.yml"
RESULT_SCHEMA = "selected-release-blueprint-result/v1"
SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
REVISION = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
SAFE_ID = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
ALLOWED_ROOTS = ("infra/", "scripts/", "platform/", "products/", "packages/",
                 "apps/", ".github/", ".agentic/")
FORBIDDEN_PARTS = {".git", ".aws", ".env", "node_modules", "credentials", "secrets"}


def fail(code):
    raise release.ReleaseFailure(code)


def safe_path(path):
    return (type(path) is str and len(path) <= 1024
            and re.fullmatch(r"[A-Za-z0-9_./@+-]+", path)
            and all(part not in {"", ".", ".."} | FORBIDDEN_PARTS
                    and not part.startswith(".env.") for part in path.split("/"))
            and (path in {"package.json", "package-lock.json"}
                 or path.startswith(ALLOWED_ROOTS)))


class TargetLoader(yaml.BaseLoader):
    """Read existing inert YAML aliases without allowing duplicate keys or tags."""

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if type(key) is not str or key in result or key == "<<":
                fail("blueprint-source-key-invalid")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def bounded_source(value):
    # The existing target profile has repeated scalar-label aliases. Preserve its
    # syntax without weakening the strict blueprint/neutral-contract loaders.
    stack = [(value, 0, frozenset())]
    count = 0
    while stack:
        item, depth, parents = stack.pop()
        count += 1
        if count > 30000 or depth > 32:
            fail("blueprint-source-limit")
        if type(item) in (dict, list):
            if id(item) in parents:
                fail("blueprint-source-cycle")
            parents = parents | {id(item)}
            values = item.values() if type(item) is dict else item
            stack.extend((child, depth + 1, parents) for child in values)
        elif type(item) is not str:
            fail("blueprint-source-type-invalid")
    return value


def source_document(text, template=False):
    try:
        value = yaml.load(text, Loader=profiles._Loader if template else TargetLoader)
        return bounded_source(value)
    except release.ReleaseFailure:
        raise
    except Exception:
        fail("blueprint-source-document-invalid")


def neutral_document(text):
    try:
        value = yaml.load(text, Loader=release.StrictLoader)
        release.bounded_json(value)
        if type(value) is not dict:
            fail("blueprint-document-invalid")
        return value
    except release.ReleaseFailure:
        raise
    except Exception:
        fail("blueprint-document-invalid")


class SourceSnapshot:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.sources = {}
        self.text = {}

    def read(self, path):
        if not safe_path(path):
            fail("blueprint-source-path-invalid")
        text, digest = profiles._read(self.root, path)
        if path in self.sources and self.sources[path] != digest:
            fail("blueprint-source-changed")
        self.sources[path], self.text[path] = digest, text
        return text

    def verify(self):
        for path, expected in list(self.sources.items()):
            if profiles._read(self.root, path)[1] != expected:
                fail("blueprint-source-changed")

    def rows(self):
        return [{"path": path, "digest": digest}
                for path, digest in sorted(self.sources.items())]


def validate_blueprint(document):
    release.bounded_json(document)
    schema = release.load_document(release.SCHEMA_DIR / SCHEMA_FILE, "blueprint-schema-unreadable")
    if (schema.get("$id") != "urn:release-control:selected-release-blueprint:v1"
            or schema.get("properties", {}).get("schema") != {"const": "selected-release-blueprint/v1"}):
        fail("blueprint-schema-version-invalid")
    pending = [schema]
    while pending:
        value = pending.pop()
        if type(value) is dict:
            if any(key in value for key in ("$dynamicRef", "$recursiveRef")):
                fail("blueprint-schema-reference-invalid")
            if "$ref" in value and not str(value["$ref"]).startswith("#/"):
                fail("blueprint-schema-reference-invalid")
            pending.extend(value.values())
        elif type(value) is list:
            pending.extend(value)
    try:
        Draft202012Validator.check_schema(schema)
        if next(Draft202012Validator(schema).iter_errors(document), None):
            fail("blueprint-invalid")
    except release.ReleaseFailure:
        raise
    except Exception:
        fail("blueprint-schema-invalid")
    return release.digest_document(schema)


def required_sources(snapshot, target):
    required = {PROFILE, TARGET + "deploy-readiness.yml", profiles.DOCKERFILE,
                profiles.TEMPLATE, FOUNDATION, "package.json", "package-lock.json"}
    source = target["source"]
    if (target["client"]["id"] != "kanbien" or target["environment"]["id"] != "staging"
            or target["deployment"]["mutation_authorized_by_profile"] != "false"
            or source["deployable_ref"] != "refs/heads/main"
            or source["workflow"]["approval"] != "github-environment-manual"
            or target["artifacts"]["image"]["local_builds"] != "smoke-only-not-deployable"):
        fail("blueprint-target-policy-mismatch")
    required.add(source["workflow"]["path"])
    required.update(source["oidc"][key] for key in ("trust_policy", "permission_policy"))
    fragments = source_document(snapshot.read(FOUNDATION))["fragments"]
    if type(fragments) is not list or not fragments:
        fail("blueprint-foundation-invalid")
    for fragment in fragments:
        required.add(TARGET + "cloudformation/" + fragment)
    return required


def task_bindings(template):
    result = {}
    for name, resource in template["Resources"].items():
        if resource.get("Type") != "AWS::ECS::TaskDefinition":
            continue
        task = resource["Properties"]
        for container in task["ContainerDefinitions"]:
            key = "task-" + name + "-" + container["Name"]
            result[key] = (task, container)
    return result


def projection_rows(blueprint, discovered, tasks, contract):
    by_profile = {row["id"]: row for row in discovered}
    operations = blueprint["operations"]
    op_ids = [op["operation_id"] for op in operations]
    source_ids = [op["source_profile"] for op in operations]
    if (len(set(op_ids)) != len(op_ids) or len(set(source_ids)) != len(source_ids)
            or set(source_ids) != set(by_profile) - {"image-default"}):
        fail("blueprint-operation-coverage-invalid")
    by_op = {op["operation_id"]: op for op in operations}
    default = by_op.get(blueprint["image_default_operation"])
    if default is None or by_profile[default["source_profile"]]["command"] != by_profile["image-default"]["command"]:
        fail("blueprint-image-default-invalid")
    identities = {item["id"]: item for item in contract["identities"]}
    artifacts = {item["id"]: item for item in contract["artifacts"]}
    projection = []
    for op in operations:
        source = by_profile[op["source_profile"]]
        task, container = tasks[op["source_profile"]]
        identity = identities.get(op["acting_identity"], {})
        for field, key in (("source_task_role_reference_digest", "TaskRoleArn"),
                           ("source_execution_role_reference_digest", "ExecutionRoleArn")):
            if key not in task or identity.get(field) != release.digest_document(task[key]):
                fail("blueprint-identity-binding-mismatch")
        if (artifacts.get(op["artifact_id"], {}).get("entrypoint") != op["command_ref"]
                or artifacts.get(op["artifact_id"], {}).get("source_command_digest") != release.digest_document(source["command"])):
            fail("blueprint-command-binding-mismatch")
        if (source["image_scope"] == "external" and "image_digest" not in source
                or source["kind"] == "finite-task" and op["operation_profile"] not in {"finite-job", "migration", "restore", "queue-consumer"}
                or source["kind"] == "service" and op["operation_profile"] not in {"service-rollout", "queue-consumer", "inspection"}):
            fail("blueprint-profile-binding-mismatch")
        projection.append({"operation_id": op["operation_id"], "source_profile": source["id"],
            "source_digest": source["source_digest"],
            "command_digest": release.digest_document(source["command"]),
            "identity_digest": release.digest_document({"task": task["TaskRoleArn"], "execution": task["ExecutionRoleArn"]}),
            "configuration_digest": release.digest_document(container),
            "execution_group_digest": release.digest_document(task),
            "command_qualification": "pending", "image_scope": source["image_scope"]})
    return projection


def validate_neutral_output(contract):
    """Reject uninterpreted fields and non-symbolic text before returning a contract."""
    fields = {
        "artifacts": {"id", "entrypoint", "assertions", "immutable_reference", "immutable_reference_mode", "source_command_digest"},
        "identities": {"id", "permissions", "source_task_role_reference_digest", "source_execution_role_reference_digest"},
        "configuration_inputs": {"id", "required_fields", "optional_fields", "sensitivity"},
        "connections": {"id", "source", "destination", "transport_security"},
        "state_stores": {"id", "semantics"},
        "async_channels": {"id", "producer", "consumers", "delivery", "acknowledgement", "idempotency_boundary"},
        "observability_profiles": {"id", "required_facts"},
        "recovery_plans": {"id", "entry_condition", "cleanup", "rollback"},
        "execution_units": {"id", "artifact", "identity", "configuration_inputs", "connections", "state_stores", "async_channels", "observability_profile", "recovery_plan"},
        "edges": {"from", "to", "purpose"},
        "assumptions": {"id", "statement", "required_proof", "actual_proof"},
        "gates": {"id", "prerequisites", "may_mutate_live_target", "evidence"},
    }
    if set(contract) != set(fields) | {"schema", "id", "version", "provider_boundary", "lifecycle", "change_shape"}:
        fail("blueprint-contract-fields-invalid")
    for group, allowed in fields.items():
        if any(set(row) - allowed for row in contract[group]):
            fail("blueprint-contract-fields-invalid")
    lifecycle = contract["lifecycle"]
    if (set(lifecycle) != {"states", "terminal_states", "transitions", "retry"}
            or set(lifecycle["retry"]) != {"mode", "requires_new_label", "maximum_attempts", "permitted_from"}
            or any(set(row) != {"from", "to"} for row in lifecycle["transitions"])
            or set(contract["change_shape"]) != {"reviewed_change_summary_required", "allowed_operation_classes", "forbidden_operation_classes"}):
        fail("blueprint-contract-fields-invalid")
    values = [contract]
    while values:
        item = values.pop()
        if type(item) is dict:
            values.extend(item.values())
        elif type(item) is list:
            values.extend(item)
        elif type(item) is str and not (re.fullmatch(r"[a-z][a-z0-9-]{0,159}", item)
                or SHA.fullmatch(item) or item == "operational-realization-contract/v1"):
            fail("blueprint-contract-value-invalid")


def compile_blueprint(root, blueprint, source_revision, image_digest, release_id):
    """Produce bound planning obligations; image/source identity claims need later evidence."""
    schema_digest = validate_blueprint(blueprint)
    if (type(source_revision) is not str or not REVISION.fullmatch(source_revision)
            or type(image_digest) is not str or not SHA.fullmatch(image_digest)
            or type(release_id) is not str or not SAFE_ID.fullmatch(release_id)):
        fail("blueprint-release-binding-invalid")
    snapshot = SourceSnapshot(root)
    bindings = blueprint["source_bindings"]
    paths = [item["path"] for item in bindings]
    if len(paths) != len(set(paths)):
        fail("blueprint-source-binding-duplicate")
    for item in bindings:
        snapshot.read(item["path"])
        if snapshot.sources[item["path"]] != item["digest"]:
            fail("blueprint-source-binding-stale")
    target = source_document(snapshot.read(PROFILE))
    if not required_sources(snapshot, target).issubset(paths):
        fail("blueprint-source-coverage-incomplete")
    owner = re.sub(r"[^a-z0-9]+", "-", target["operations"]["owner"].lower()).strip("-")
    if owner != blueprint["owner"]:
        fail("blueprint-owner-mismatch")
    contract = neutral_document(snapshot.read(blueprint["realization_contract"]))
    policy = neutral_document(snapshot.read(blueprint["acceptance_policy"]))
    discovered = profiles.discover(snapshot.root)
    for item in discovered:
        if snapshot.sources.get(item["source_path"]) != item["source_digest"]:
            fail("blueprint-source-changed")
        if item["image_scope"] == "product":
            for command in item["command"]:
                source_path = command.removeprefix(".cache/platform-shell-image-build/").removesuffix(".js") + ".ts"
                if source_path not in paths:
                    fail("blueprint-command-source-missing")
    tasks = task_bindings(source_document(snapshot.read(profiles.TEMPLATE), template=True))
    projection = projection_rows(blueprint, discovered, tasks, contract)
    operations = [{key: deepcopy(value) for key, value in op.items() if key != "source_profile"}
                  for op in blueprint["operations"]]
    by_profile = {item["id"]: item for item in discovered}
    artifacts = [{"artifact_id": op["artifact_id"],
                  "digest": image_digest if by_profile[op["source_profile"]]["image_scope"] == "product"
                  else by_profile[op["source_profile"]]["image_digest"]}
                 for op in blueprint["operations"]]
    implementation = [Path(__file__), GATE / "blueprint_cli.py", GATE / "release_compiler.py",
                      GATE / "script.py", GATE / "script.sh", GATE / "container_profiles.py"]
    implementation_bytes = {file: file.read_bytes() for file in implementation}
    implementation_digest = release.digest_document([
        {"name": file.name, "digest": "sha256:" + hashlib.sha256(data).hexdigest()}
        for file, data in implementation_bytes.items()])
    definition = {"schema": "release-definition/v1", "release_id": release_id,
        "source_revision": source_revision,
        "target_composition_revision": release.digest_document({"blueprint": blueprint, "sources": snapshot.rows(),
            "implementation_digest": implementation_digest, "blueprint_schema_digest": schema_digest}),
        "artifact_digests": artifacts, "target_id": blueprint["target_id"], "risk_tier": blueprint["risk_tier"],
        "operation_graph": operations, "environment_contract_revision": snapshot.sources[PROFILE],
        "acceptance_matrix": policy, "evidence_policy_revision": release.digest_document(policy),
        "realization_contract_digest": release.digest_document(contract)}
    compiled = release.compile_release(definition, contract)
    validate_neutral_output(contract)
    snapshot.verify()
    if any(file.read_bytes() != data for file, data in implementation_bytes.items()):
        fail("blueprint-implementation-changed")
    result = {"schema": RESULT_SCHEMA, "scope": "selected-release-blueprint", "verdict": "compiled",
        "authorized": False, "release_eligibility": "blocked", "operation_authorization": "blocked",
        "qualification_verdict": "blocked", "policy_review": "required", "identity_proof": "pending",
        "source_revision_status": "declared", "artifact_identity_status": "declared",
        "blueprint_digest": release.digest_document(blueprint), "blueprint_schema_digest": schema_digest,
        "implementation_digest": implementation_digest, "source_bindings": snapshot.rows(),
        "operation_projection": projection, "definition": definition,
        "realization_contract": contract, "compiled_release": compiled,
        "constraints": ["official-main-publication-required", "local-image-not-deployable",
                        "explicit-target-operation-approval-required", "all-seventeen-gates-retained",
                        "inherited-sidecar-command-proof-pending", "target-facts-not-observed"],
        "findings": []}
    result["result_digest"] = release.digest_document(result)
    return result
