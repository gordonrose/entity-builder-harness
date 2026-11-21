#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.release-proof-policy
#   version: 1
#   status: active
#   created_on: "2026-11-19"
#   updated_on: "2026-11-21"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Compare declared immutable recovery inputs without treating historical qualification as current release health.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.compiler.acceptance-route
#     path: scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py
import hashlib
from datetime import timedelta
import json
from pathlib import Path
import re
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[5]
BINDINGS = ("configuration_contract_sha256", "permission_contract_sha256",
            "dependency_incarnation_sha256")


def observation_expired(stopped_at, current_time, timestamp):
    """Shared observation-renewal boundary; collection cannot restamp age."""
    return timestamp(current_time) - timestamp(stopped_at) > timedelta(seconds=900)


def observation_renewal_id(original):
    """One deterministic replacement identity, never an unbounded retry count."""
    return hashlib.sha256((original + ":preflight-renewal-1").encode()).hexdigest()[:24]


def failed_observation_id(original, terminal, expected, *, dependent_reserved):
    """One replacement of a checked failed read-only observation, never replay.

    The provider owner validates the original journal, terminal evidence and
    read-only request before supplying these bindings. A success, uncertain
    outcome, different identity or already-started dependent work cannot enter.
    The caller always supplies the original identity, not the replacement.
    """
    require(isinstance(original, str) and bool(original)
        and isinstance(terminal, dict) and isinstance(expected, dict)
        and set(expected) == {"operation_id", "request_sha256", "source_revision",
            "image_digest", "workload", "operation", "proof_label_sha256"}
        and set(terminal) == set(expected) | {"task_arn", "task_definition", "exit_code", "stopped_at", "failure_basis"}
        and all(isinstance(value, str) and value and terminal.get(key) == value
                for key, value in expected.items())
        and expected["operation"] in {"preflight", "ready"}
        and type(terminal.get("exit_code")) is int and terminal["exit_code"] != 0
        and terminal.get("failure_basis") in {"validated-failure-report", "nonzero-exit"},
        "observation-recovery-terminal-required")
    require(dependent_reserved is False, "observation-recovery-dependent-already-reserved")
    return hashlib.sha256((original + ":terminal-observation-recovery-1").encode()).hexdigest()[:24]


class PolicyFailure(ValueError):
    def __init__(self, code, item=None):
        super().__init__(code)
        self.code, self.item = code, item


def require(value, code, item=None):
    if not value:
        raise PolicyFailure(code, item)


def recovery_input_paths(value):
    require(isinstance(value, list) and bool(value) and len(value) <= 128
            and all(isinstance(path, str) and re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", path)
                    and all(part not in {".", ".."} for part in path.split("/")) for path in value)
            and len(value) == len(set(value)), "acceptance-recovery-input-paths-invalid")
    return sorted(value)


def recovery_input_tree(source_revision, paths, *, root=None):
    """Hash actual Git objects, including additions, removals and file modes."""
    require(isinstance(source_revision, str) and re.fullmatch(r"[a-f0-9]{40}", source_revision),
            "acceptance-recovery-input-source-invalid")
    paths = recovery_input_paths(paths)
    try:
        completed = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "--full-tree", source_revision, "--",
             *[":(literal)" + path for path in paths]],
            cwd=ROOT if root is None else root, capture_output=True, check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        raise PolicyFailure("acceptance-recovery-inputs-unavailable") from None
    require(completed.returncode == 0 and len(completed.stdout) <= 16 * 1024 * 1024,
            "acceptance-recovery-inputs-unavailable")
    # Individually absent selectors still detect later additions (e.g. lockfiles).
    require(bool(completed.stdout) and completed.stdout.endswith(b"\0"),
            "acceptance-recovery-inputs-empty")
    return "sha256:" + hashlib.sha256(completed.stdout).hexdigest()


def recovery_applicability(previous, candidate, paths, *, root=None, additional_bindings=()):
    """Callers first validate accepted custody; equality alone is not acceptance."""
    fields = (*BINDINGS, *additional_bindings)
    require(isinstance(previous, dict) and isinstance(candidate, dict)
            and all(isinstance(previous.get(key), str) and previous[key]
                    and previous[key] == candidate.get(key) for key in fields),
            "acceptance-recovery-binding-changed")
    require(all(re.fullmatch(r"sha256:[a-f0-9]{64}", previous[key]) for key in BINDINGS),
            "acceptance-recovery-binding-changed")
    paths = recovery_input_paths(paths)
    before = recovery_input_tree(previous.get("source_revision"), paths, root=root)
    after = recovery_input_tree(candidate.get("source_revision"), paths, root=root)
    require(before == after, "acceptance-recovery-requalification-required")
    return {"schema": "deploy/recovery-applicability/v1",
            "predecessor_source": previous["source_revision"], "candidate_source": candidate["source_revision"],
            "input_paths": paths, "inputs_sha256": before}


def recovery_requirements(previous, candidate, paths, *, root=None, additional_bindings=()):
    """Select proof obligations, never certify that those obligations passed.

    The accepted-history owner validates custody before calling. Record identity
    and database incarnation cannot be changed by a recovery rehearsal; changed
    code/configuration requires fresh evidence instead of an equality waiver.
    """
    require(isinstance(previous, dict) and isinstance(candidate, dict),
            "acceptance-recovery-binding-invalid")
    for field in BINDINGS:
        require(all(isinstance(value.get(field), str)
                    and re.fullmatch(r"sha256:[a-f0-9]{64}", value[field])
                    for value in (previous, candidate)), "acceptance-recovery-binding-invalid", field)
    for field in ("dependency_incarnation_sha256", *additional_bindings):
        require(isinstance(previous.get(field), str) and bool(previous[field])
                and previous[field] == candidate.get(field), "acceptance-recovery-binding-changed", field)
    paths = recovery_input_paths(paths)
    before = recovery_input_tree(previous.get("source_revision"), paths, root=root)
    after = recovery_input_tree(candidate.get("source_revision"), paths, root=root)
    changes = [field for field in BINDINGS if previous[field] != candidate[field]]
    if before != after:
        changes.append("recovery_inputs")
    return {"schema": "deploy/recovery-requirements/v1",
            "mode": "requalify" if changes else "reuse",
            "predecessor_source": previous["source_revision"],
            "candidate_source": candidate["source_revision"], "input_paths": paths,
            "predecessor_inputs_sha256": before, "candidate_inputs_sha256": after,
            "changed_bindings": changes}


def contract_at(source, path, root):
    """Read a regular immutable contract, never a working-tree substitute."""
    recovery_input_paths([path])
    require(isinstance(source, str) and re.fullmatch(r"[a-f0-9]{40}", source),
            "acceptance-rollback-source-invalid")
    try:
        entry = subprocess.run(["git", "ls-tree", "-z", source, "--", ":(literal)" + path],
            cwd=root, capture_output=True, timeout=30)
        require(entry.returncode == 0 and re.fullmatch(
            rb"100644 blob [a-f0-9]{40}\t" + re.escape(path.encode()) + b"\x00", entry.stdout),
            "acceptance-rollback-contract-unavailable")
        blob = subprocess.run(["git", "show", source + ":" + path], cwd=root,
            capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        raise PolicyFailure("acceptance-rollback-contract-unavailable") from None
    require(blob.returncode == 0 and 0 < len(blob.stdout) <= 1024 * 1024,
            "acceptance-rollback-contract-unavailable")
    return blob.stdout


def rollback_applicability(previous, candidate, configuration_path, permission_path, schema_paths, *, root=None):
    """Reuse accepted compatibility only for an image-only, unchanged target.

    The caller owns accepted custody, package identity and image-only execution.
    This is a comparison, not fresh live proof or permission to apply migrations.
    """
    root = ROOT if root is None else root
    require(isinstance(previous, dict) and isinstance(candidate, dict)
        and all(isinstance(value.get(key), str) and re.fullmatch(r"sha256:[a-f0-9]{64}", value[key])
                for value in (previous, candidate) for key in BINDINGS),
        "acceptance-rollback-binding-invalid")
    require(previous["dependency_incarnation_sha256"] == candidate["dependency_incarnation_sha256"],
            "acceptance-rollback-incarnation-changed")
    class UniqueLoader(yaml.SafeLoader): pass
    def mapping(loader, node):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=True)
            if not isinstance(key, str) or key in result: raise ValueError("ambiguous mapping")
            result[key] = loader.construct_object(value_node, deep=True)
        return result
    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    configurations = []
    for value in (previous, candidate):
        raw = contract_at(value.get("source_revision"), configuration_path, root)
        require("sha256:" + hashlib.sha256(raw).hexdigest() == value["configuration_contract_sha256"],
                "acceptance-rollback-contract-hash-mismatch")
        try:
            document = yaml.load(raw, Loader=UniqueLoader)
            require(isinstance(document, dict) and all(isinstance(key, str) for key in document),
                    "acceptance-rollback-configuration-invalid")
            # This one named section selects tests; it cannot change runtime
            # configuration. No caller-supplied ignore list is accepted.
            document = {key: item for key, item in document.items() if key != "change_impact"}
            configurations.append(json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False))
        except (ValueError, TypeError, RecursionError, yaml.YAMLError):
            raise PolicyFailure("acceptance-rollback-configuration-invalid") from None
        permission = contract_at(value["source_revision"], permission_path, root)
        require("sha256:" + hashlib.sha256(permission).hexdigest() == value["permission_contract_sha256"],
                "acceptance-rollback-contract-hash-mismatch")
    require(configurations[0] == configurations[1]
        and previous["permission_contract_sha256"] == candidate["permission_contract_sha256"],
        "acceptance-rollback-fresh-compatibility-required")
    paths = recovery_input_paths(schema_paths)
    for path in paths:
        # These are existing schema authorities, not optional future lockfiles.
        recovery_input_tree(previous["source_revision"], [path], root=root)
    # Include the permission contract so an empty schema set cannot hide an
    # absent repository. Git tree identity includes additions/removals/modes.
    inputs = sorted(set([permission_path, *paths]))
    before = recovery_input_tree(previous["source_revision"], inputs, root=root)
    after = recovery_input_tree(candidate["source_revision"], inputs, root=root)
    require(before == after, "acceptance-rollback-fresh-compatibility-required")
    return {"schema": "deploy/accepted-rollback-applicability/v1",
            "predecessor_source": previous["source_revision"], "candidate_source": candidate["source_revision"],
            "configuration_path": configuration_path, "permission_path": permission_path,
            "schema_input_paths": paths, "inputs_sha256": before,
            "predecessor_configuration_sha256": previous["configuration_contract_sha256"],
            "configuration_sha256": candidate["configuration_contract_sha256"],
            "dependency_incarnation_sha256": candidate["dependency_incarnation_sha256"]}


def validate_requirements(value, predecessor_source, candidate_source):
    fields = {"schema", "mode", "predecessor_source", "candidate_source", "input_paths",
        "predecessor_inputs_sha256", "candidate_inputs_sha256", "changed_bindings"}
    require(isinstance(value, dict) and set(value) == fields
        and value["schema"] == "deploy/recovery-requirements/v1"
        and value["predecessor_source"] == predecessor_source and value["candidate_source"] == candidate_source,
        "acceptance-recovery-applicability-invalid")
    require(recovery_input_paths(value["input_paths"]) == value["input_paths"]
        and all(isinstance(value[k], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", value[k])
            for k in ("predecessor_inputs_sha256", "candidate_inputs_sha256")), "acceptance-recovery-applicability-invalid")
    changes = value["changed_bindings"]
    allowed = ("configuration_contract_sha256", "permission_contract_sha256", "recovery_inputs")
    require(isinstance(changes, list) and all(isinstance(k, str) for k in changes)
        and changes == [k for k in allowed if k in changes]
        and ("recovery_inputs" in changes) == (value["predecessor_inputs_sha256"] != value["candidate_inputs_sha256"])
        and value["mode"] == ("requalify" if changes else "reuse"), "acceptance-recovery-applicability-invalid")
    return value


def prerequisite_references(value, schemas, fingerprint):
    """Compact selected already-validated packets; consumers verify every hash."""
    if isinstance(value, dict):
        if isinstance(value.get("schema"), str) and value["schema"] in schemas:
            return {"schema": "deploy/proof-prerequisite-reference/v1", "packet_sha256": fingerprint(value)}
        return {key: prerequisite_references(item, schemas, fingerprint) for key, item in value.items()}
    if isinstance(value, list): return [prerequisite_references(item, schemas, fingerprint) for item in value]
    return value


def validate_prerequisite_references(value, available):
    """Every compact reference must name an independently checked prior packet."""
    if isinstance(value, dict):
        if value.get("schema") == "deploy/proof-prerequisite-reference/v1":
            require(set(value) == {"schema", "packet_sha256"} and isinstance(value["packet_sha256"], str)
                and value["packet_sha256"] in available, "acceptance-task-prerequisite-mismatch")
        else:
            for item in value.values(): validate_prerequisite_references(item, available)
    elif isinstance(value, list):
        for item in value: validate_prerequisite_references(item, available)


def policy(schema):
    """The existing acceptance schema owns policy, not a second registry."""
    value = schema.get("ordinary_update") if isinstance(schema, dict) else None
    require(isinstance(value, dict)
            and value.get("retained_evidence") == "exact-accepted-predecessor-capability-history"
            and value.get("changed_inputs") == "require-affected-capability-requalification",
            "acceptance-recovery-policy-invalid")
    fresh = value.get("fresh_tasks")
    require(isinstance(fresh, list) and bool(fresh)
            and all(isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9-]*", name) for name in fresh)
            and len(fresh) == len(set(fresh)), "acceptance-recovery-policy-invalid")
    recovery_input_paths(value.get("recovery_input_paths"))
    return value
