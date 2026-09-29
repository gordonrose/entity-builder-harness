#!/usr/bin/env python3
"""Exercise release compilation, its trust boundaries, and command compatibility."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-release-compiler
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify immutable release bindings, complete ordered acceptance gates, and safe local compilation.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
sys.path.insert(0, str(DIRECTORY))
import release_compiler as compiler


GATES = (
    "scope-risk", "acceptance-contract", "source-contracts", "unit-contract-tests",
    "integration-tests", "exact-artifact-tests", "supply-chain-proof",
    "iac-static-validation", "change-set-review", "drift-dependency-preflight",
    "candidate-runtime-proof", "per-task-live-preflight", "controlled-state-change",
    "post-change-verification", "rollback-recovery", "evidence-retention",
    "continuous-operation",
)
ROW_FIELDS = (
    "gate", "owner", "acting_identity", "operation_profile", "command_ref",
    "operation_ids", "evidence_requirements", "invalidated_by", "failure_state",
    "recovery_route", "cleanup_route", "verdict",
)
SENTINEL = "SENTINEL-SENSITIVE-DO-NOT-PRINT"
FIXTURE = DIRECTORY / "fixtures" / "valid-release.yml"
CONTRACT = DIRECTORY / "fixtures" / "valid-contract.yml"


class ReleaseCompilerTests(unittest.TestCase):
    def setUp(self):
        self.release = compiler.load_document(FIXTURE)
        self.contract = compiler.load_document(CONTRACT)

    def compile(self, document=None, contract=None, **kwargs):
        return compiler.compile_release(
            self.release if document is None else document,
            self.contract if contract is None else contract,
            **kwargs,
        )

    def assert_rejected(self, document=None, contract=None, code=None, **kwargs):
        with self.assertRaises(compiler.ReleaseFailure) as caught:
            self.compile(document, contract, **kwargs)
        self.assertNotIn(SENTINEL, str(caught.exception))
        if code is not None:
            self.assertEqual(caught.exception.code, code)

    def command(self, arguments, compatibility=False):
        executable = (
            [sys.executable, str(ROOT / "scripts/04.deploy/release-control/compiler.py")]
            if compatibility else ["bash", str(DIRECTORY / "script.sh")]
        )
        return subprocess.run(executable + list(arguments), cwd=ROOT, text=True,
                              capture_output=True, check=False)

    def assert_safe_command_failure(self, arguments, compatibility=False):
        result = self.command(arguments, compatibility)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(SENTINEL, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["verdict"], "failed")
        self.assertTrue(output["findings"])
        return output

    def test_complete_deterministic_compilation_binds_every_stage(self):
        original_release, original_contract = copy.deepcopy(self.release), copy.deepcopy(self.contract)
        result = self.compile()
        self.assertEqual(result, self.compile())
        self.assertEqual(self.release, original_release)
        self.assertEqual(self.contract, original_contract)
        self.assertEqual(result["schema"], "release-control-result/v1")
        self.assertEqual(result["scope"], "release-definition")
        self.assertEqual(result["verdict"], "compiled")
        self.assertIs(result["authorized"], False)
        self.assertEqual(result["findings"], [])
        self.assertEqual(set(result["schema_digests"]),
                         {"release-definition/v1", "release-acceptance-matrix/v1"})
        self.assertEqual(result["release_digest"], compiler.digest_document({
            "definition": self.release, "schema_digests": result["schema_digests"],
        }))
        self.assertEqual(len(result["acceptance_matrix"]), 17)
        for index, row in enumerate(result["acceptance_matrix"]):
            with self.subTest(gate=GATES[index]):
                self.assertEqual(row["gate"], GATES[index])
                self.assertEqual(row["stage"], index + 1)
                self.assertEqual(row["prerequisites"], list(GATES[:index]))
                self.assertEqual(row["verdict"], "not-started")
                self.assertEqual(row["bindings"]["release_digest"], result["release_digest"])
                for key in ("release_id", "source_revision", "target_composition_revision",
                            "target_id", "artifact_digests", "environment_contract_revision",
                            "evidence_policy_revision", "realization_contract_digest"):
                    self.assertEqual(row["bindings"][key], self.release[key])

    def test_canonical_digest_uses_json_not_yaml_presentation(self):
        value = {"z": "é", "a": [2, 1]}
        serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        expected = "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.assertEqual(compiler.digest_document(value), expected)
        self.assertEqual(compiler.digest_document(value), compiler.digest_document({"a": [2, 1], "z": "é"}))

    def test_missing_release_bindings_are_rejected(self):
        for field in self.release:
            with self.subTest(field=field):
                document = copy.deepcopy(self.release)
                del document[field]
                self.assert_rejected(document)

    def test_immutable_binding_values_are_required(self):
        invalid_values = {
            "source_revision": ["main", "short-sha", "a" * 39, True],
            "target_composition_revision": ["latest", "sha256:abc", ""],
            "environment_contract_revision": ["latest", "sha256:abc", None],
            "evidence_policy_revision": ["latest", "sha256:abc", {}],
            "realization_contract_digest": ["latest", "sha256:" + "b" * 64],
        }
        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    document = copy.deepcopy(self.release)
                    document[field] = value
                    self.assert_rejected(document)
        for value in ("latest", "sha256:abc", "sha256:" + "b" * 64, True):
            with self.subTest(artifact_digest=value):
                document = copy.deepcopy(self.release)
                document["artifact_digests"][0]["digest"] = value
                self.assert_rejected(document)

    def test_all_gates_and_order_are_mandatory(self):
        for index in range(17):
            with self.subTest(missing_gate=GATES[index]):
                document = copy.deepcopy(self.release)
                del document["acceptance_matrix"]["rows"][index]
                self.assert_rejected(document)
        document = copy.deepcopy(self.release)
        document["acceptance_matrix"]["rows"].append(copy.deepcopy(document["acceptance_matrix"]["rows"][-1]))
        self.assert_rejected(document)
        document = copy.deepcopy(self.release)
        document["acceptance_matrix"]["rows"][1] = copy.deepcopy(document["acceptance_matrix"]["rows"][0])
        self.assert_rejected(document)
        document = copy.deepcopy(self.release)
        document["acceptance_matrix"]["rows"][0:2] = reversed(document["acceptance_matrix"]["rows"][0:2])
        self.assert_rejected(document)

    def test_every_stage_requires_its_full_operational_contract(self):
        for index, gate in enumerate(GATES):
            for field in ROW_FIELDS:
                with self.subTest(gate=gate, missing=field):
                    document = copy.deepcopy(self.release)
                    del document["acceptance_matrix"]["rows"][index][field]
                    self.assert_rejected(document)

    def test_empty_row_values_and_evidence_rules_are_rejected(self):
        for field in ROW_FIELDS:
            with self.subTest(empty=field):
                document = copy.deepcopy(self.release)
                row = document["acceptance_matrix"]["rows"][0]
                row[field] = [] if isinstance(row[field], list) else ""
                self.assert_rejected(document)
        for field in self.release["acceptance_matrix"]["rows"][0]["evidence_requirements"][0]:
            with self.subTest(missing_evidence_rule=field):
                document = copy.deepcopy(self.release)
                del document["acceptance_matrix"]["rows"][0]["evidence_requirements"][0][field]
                self.assert_rejected(document)
        for value in (True, 0, -1, "86400", 1.5):
            with self.subTest(max_age_seconds=value):
                document = copy.deepcopy(self.release)
                document["acceptance_matrix"]["rows"][0]["evidence_requirements"][0]["max_age_seconds"] = value
                self.assert_rejected(document)

    def test_source_definition_cannot_assert_runtime_proof_or_exemption(self):
        for index, gate in enumerate(GATES):
            for verdict in ("not-applicable", "passed", "approved", "validated", "running", "failed", "expired", "cleaned-up"):
                with self.subTest(gate=gate, verdict=verdict):
                    document = copy.deepcopy(self.release)
                    document["acceptance_matrix"]["rows"][index]["verdict"] = verdict
                    expected_code = None
                    if verdict == "not-applicable":
                        expected_code = "applicability-unsupported"
                    elif verdict in {"passed", "failed", "expired"}:
                        expected_code = "evidence-verdict-unsupported"
                    self.assert_rejected(document, code=expected_code)
        document = copy.deepcopy(self.release)
        row = document["acceptance_matrix"]["rows"][0]
        row.update(verdict="not-applicable", compiler_applicability_result="declared",
                   discovery_facts=["claimed-absent"], independent_review="self-approved")
        self.assert_rejected(document)

    def test_operation_graph_and_matrix_references_are_bound(self):
        for field in ("execution_unit", "artifact_id", "acting_identity", "command_ref"):
            with self.subTest(operation_field=field):
                document = copy.deepcopy(self.release)
                document["operation_graph"][0][field] = "undeclared-binding"
                self.assert_rejected(document)
        for field in ("acting_identity", "operation_profile", "command_ref", "recovery_route", "cleanup_route"):
            with self.subTest(row_field=field):
                document = copy.deepcopy(self.release)
                document["acceptance_matrix"]["rows"][0][field] = "undeclared-binding"
                self.assert_rejected(document)
        for values in ([], ["missing-operation"], ["delivery-operation", "delivery-operation"]):
            with self.subTest(operation_ids=values):
                document = copy.deepcopy(self.release)
                document["acceptance_matrix"]["rows"][0]["operation_ids"] = values
                self.assert_rejected(document)

    def test_artifact_and_operation_coverage_cannot_be_missing_or_duplicated(self):
        for field in ("artifact_digests", "operation_graph"):
            for mutation in ("empty", "duplicate", "extra"):
                with self.subTest(field=field, mutation=mutation):
                    document = copy.deepcopy(self.release)
                    if mutation == "empty":
                        document[field] = []
                    else:
                        duplicate = copy.deepcopy(document[field][0])
                        if mutation == "extra":
                            duplicate["artifact_id" if field == "artifact_digests" else "operation_id"] = "undeclared-extra"
                        document[field].append(duplicate)
                    self.assert_rejected(document)

    def two_operation_release(self):
        document, contract = copy.deepcopy(self.release), copy.deepcopy(self.contract)
        unit = copy.deepcopy(contract["execution_units"][0])
        unit["id"] = "delivery-auxiliary"
        unit["connections"] = ["auxiliary-connection"]
        contract["execution_units"].append(unit)
        connection = copy.deepcopy(contract["connections"][0])
        connection.update(id="auxiliary-connection", source="delivery-auxiliary")
        contract["connections"].append(connection)
        for edge in list(contract["edges"]):
            if edge["from"] == "delivery-worker":
                duplicate = dict(edge, **{"from": "delivery-auxiliary"})
                if duplicate["to"] == "delivery-connection":
                    duplicate["to"] = "auxiliary-connection"
                contract["edges"].append(duplicate)
        contract["edges"].append({"from": "auxiliary-connection", "to": "delivery-store", "purpose": "reaches-state"})
        contract["async_channels"][0]["consumers"].append("delivery-auxiliary")
        contract["edges"].append({"from": "delivery-channel", "to": "delivery-auxiliary", "purpose": "delivers-work"})
        operation = copy.deepcopy(document["operation_graph"][0])
        operation.update(operation_id="delivery-auxiliary-operation", execution_unit="delivery-auxiliary", depends_on=["delivery-operation"])
        document["operation_graph"].append(operation)
        for row in document["acceptance_matrix"]["rows"]:
            row["operation_ids"].append("delivery-auxiliary-operation")
        document["realization_contract_digest"] = compiler.digest_document(contract)
        return document, contract

    def test_ordered_dependency_graph_accepts_multiple_bound_operations(self):
        document, contract = self.two_operation_release()
        self.assertEqual(self.compile(document, contract)["verdict"], "compiled")

    def heterogeneous_release(self):
        document, contract = self.two_operation_release()
        artifact = copy.deepcopy(contract["artifacts"][0])
        artifact.update(id="auxiliary-artifact", entrypoint="auxiliary-entrypoint",
                        immutable_reference="sha256:" + "b" * 64)
        contract["artifacts"].append(artifact)
        identity = copy.deepcopy(contract["identities"][0])
        identity["id"] = "auxiliary-identity"
        contract["identities"].append(identity)
        contract["execution_units"][1].update(artifact="auxiliary-artifact", identity="auxiliary-identity")
        for edge in contract["edges"]:
            if edge["from"] == "delivery-auxiliary":
                if edge["to"] == "delivery-artifact":
                    edge["to"] = "auxiliary-artifact"
                elif edge["to"] == "delivery-identity":
                    edge["to"] = "auxiliary-identity"
        document["operation_graph"][1].update(
            artifact_id="auxiliary-artifact", acting_identity="auxiliary-identity",
            command_ref="auxiliary-entrypoint", operation_profile="finite-job",
        )
        document["artifact_digests"].append({"artifact_id": "auxiliary-artifact", "digest": artifact["immutable_reference"]})
        for row in document["acceptance_matrix"]["rows"]:
            row["operation_overrides"] = [{
                "operation_id": "delivery-auxiliary-operation",
                "acting_identity": "auxiliary-identity",
                "operation_profile": "finite-job",
                "command_ref": "auxiliary-entrypoint",
                "evidence_requirements": copy.deepcopy(row["evidence_requirements"]),
                "recovery_route": row["recovery_route"],
                "cleanup_route": row["cleanup_route"],
            }]
        document["realization_contract_digest"] = compiler.digest_document(contract)
        return document, contract

    def test_each_stage_covers_every_operation_with_bound_profile_overrides(self):
        document, contract = self.heterogeneous_release()
        result = self.compile(document, contract)
        for row in result["acceptance_matrix"]:
            with self.subTest(gate=row["gate"]):
                bindings = {item["operation_id"]: item for item in row["operation_bindings"]}
                self.assertEqual(set(bindings), {"delivery-operation", "delivery-auxiliary-operation"})
                self.assertEqual(bindings["delivery-operation"]["operation_profile"], "queue-consumer")
                auxiliary = bindings["delivery-auxiliary-operation"]
                self.assertEqual(auxiliary["operation_profile"], "finite-job")
                self.assertEqual(auxiliary["execution_unit"], "delivery-auxiliary")
                self.assertEqual(auxiliary["artifact_id"], "auxiliary-artifact")
                self.assertEqual(auxiliary["artifact_digest"], "sha256:" + "b" * 64)
                self.assertEqual(auxiliary["acting_identity"], "auxiliary-identity")
                self.assertEqual(auxiliary["command_ref"], "auxiliary-entrypoint")
        for index, gate in enumerate(GATES):
            with self.subTest(missing_operation_at=gate):
                document, contract = self.two_operation_release()
                document["acceptance_matrix"]["rows"][index]["operation_ids"].pop()
                self.assert_rejected(document, contract)

    def test_overrides_require_unique_declared_and_accurate_operation_bindings(self):
        for mutation in ("duplicate", "undeclared", "incorrect-command", "unsafe-value", "no-default-operation"):
            with self.subTest(mutation=mutation):
                document, contract = self.heterogeneous_release()
                row = document["acceptance_matrix"]["rows"][0]
                override = row["operation_overrides"][0]
                if mutation == "duplicate":
                    row["operation_overrides"].append(copy.deepcopy(override))
                elif mutation == "undeclared":
                    override["operation_id"] = "missing-operation"
                elif mutation == "incorrect-command":
                    override["command_ref"] = "wrong-entrypoint"
                elif mutation == "unsafe-value":
                    override["secret_value"] = SENTINEL
                else:
                    default_override = {key: copy.deepcopy(row[key]) for key in (
                        "acting_identity", "operation_profile", "command_ref",
                        "evidence_requirements", "recovery_route", "cleanup_route")}
                    default_override["operation_id"] = "delivery-operation"
                    row["operation_overrides"].append(default_override)
                self.assert_rejected(document, contract)

    def test_stage_evidence_cannot_be_downgraded_to_declarations(self):
        for index in range(3, 17):
            for overridden in (False, True):
                with self.subTest(gate=GATES[index], overridden=overridden):
                    if overridden:
                        document, contract = self.heterogeneous_release()
                        evidence = document["acceptance_matrix"]["rows"][index]["operation_overrides"][0]["evidence_requirements"]
                    else:
                        document, contract = copy.deepcopy(self.release), self.contract
                        evidence = document["acceptance_matrix"]["rows"][index]["evidence_requirements"]
                    evidence[0]["proof_level"] = "declared"
                    self.assert_rejected(document, contract)

    def test_continuous_operation_requires_an_observation_window(self):
        for overridden in (False, True):
            for value in (None, 0, -1, True):
                with self.subTest(overridden=overridden, window=value):
                    if overridden:
                        document, contract = self.heterogeneous_release()
                        evidence = document["acceptance_matrix"]["rows"][16]["operation_overrides"][0]["evidence_requirements"][0]
                    else:
                        document, contract = copy.deepcopy(self.release), self.contract
                        evidence = document["acceptance_matrix"]["rows"][16]["evidence_requirements"][0]
                    if value is None:
                        del evidence["observation_window_seconds"]
                    else:
                        evidence["observation_window_seconds"] = value
                    self.assert_rejected(document, contract)

    def test_stage_evidence_requires_an_appropriate_environment(self):
        invalid_environments = {
            3: "candidate", 4: "source", 5: "source", 6: "target", 7: "target",
            8: "source", 9: "source", 10: "target", 11: "candidate",
            12: "candidate", 13: "candidate", 14: "source", 15: "source", 16: "source",
        }
        for index, environment in invalid_environments.items():
            for overridden in (False, True):
                with self.subTest(gate=GATES[index], overridden=overridden):
                    if overridden:
                        document, contract = self.heterogeneous_release()
                        evidence = document["acceptance_matrix"]["rows"][index]["operation_overrides"][0]["evidence_requirements"]
                    else:
                        document, contract = copy.deepcopy(self.release), self.contract
                        evidence = document["acceptance_matrix"]["rows"][index]["evidence_requirements"]
                    evidence[0]["environment"] = environment
                    self.assert_rejected(document, contract)

    def test_dependency_graph_rejects_missing_self_duplicate_forward_and_cycle(self):
        for dependencies in (["missing-operation"], ["delivery-operation"]):
            with self.subTest(dependencies=dependencies):
                document = copy.deepcopy(self.release)
                document["operation_graph"][0]["depends_on"] = dependencies
                self.assert_rejected(document)
        for mutation in ("duplicate", "forward", "cycle"):
            with self.subTest(mutation=mutation):
                document, contract = self.two_operation_release()
                if mutation == "duplicate":
                    document["operation_graph"][1]["depends_on"] *= 2
                else:
                    document["operation_graph"][0]["depends_on"] = ["delivery-auxiliary-operation"]
                    if mutation == "forward":
                        document["operation_graph"][1]["depends_on"] = []
                self.assert_rejected(document, contract)

    def test_realization_contract_is_validated_even_with_matching_digest(self):
        for mutation in ("missing-unit", "undeclared-edge", "unsafe-retry"):
            with self.subTest(mutation=mutation):
                document, contract = copy.deepcopy(self.release), copy.deepcopy(self.contract)
                if mutation == "missing-unit":
                    contract["execution_units"] = []
                elif mutation == "undeclared-edge":
                    contract["edges"].pop(0)
                else:
                    contract["lifecycle"]["retry"]["mode"] = "automatic"
                document["realization_contract_digest"] = compiler.digest_document(contract)
                self.assert_rejected(document, contract)

    def test_same_release_identity_cannot_be_rebound(self):
        self.assertEqual(self.compile(baseline=copy.deepcopy(self.release))["verdict"], "compiled")
        mutations = (
            ("source_revision", "b" * 40),
            ("target_composition_revision", "sha256:" + "f" * 64),
            ("target_id", "different-target"),
            ("environment_contract_revision", "sha256:" + "b" * 64),
            ("evidence_policy_revision", "sha256:" + "b" * 64),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                document = copy.deepcopy(self.release)
                document[field] = value
                self.assert_rejected(document, baseline=self.release, code="immutable-release-rebound")
        document = copy.deepcopy(self.release)
        document["acceptance_matrix"]["rows"][0]["owner"] = "another-owner"
        self.assert_rejected(document, baseline=self.release, code="immutable-release-rebound")
        document["release_id"] = "next-delivery-release"
        self.assertEqual(self.compile(document, baseline=self.release)["verdict"], "compiled")
        baseline = copy.deepcopy(self.release)
        del baseline["source_revision"]
        self.assert_rejected(baseline=baseline)

    def test_unknown_and_sensitive_fields_are_rejected_at_every_depth(self):
        paths = ((), ("artifact_digests", 0), ("operation_graph", 0),
                 ("acceptance_matrix",), ("acceptance_matrix", "rows", 0),
                 ("acceptance_matrix", "rows", 0, "evidence_requirements", 0))
        for path in paths:
            for field in ("unrecognized_field", "secret_value", "raw_provider_response"):
                with self.subTest(path=path, field=field):
                    document = copy.deepcopy(self.release)
                    target = document
                    for step in path:
                        target = target[step]
                    target[field] = SENTINEL
                    self.assert_rejected(document)

    def test_unsafe_and_provider_specific_identifier_values_are_rejected(self):
        for value in (SENTINEL, "https://private.example/path", "aws-release", "arn:aws:secret", "../outside", "line\nbreak"):
            with self.subTest(value=value):
                document = copy.deepcopy(self.release)
                document["release_id"] = value
                self.assert_rejected(document)

    def test_versioned_schema_files_are_authoritative_and_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            schema_dir = Path(temporary) / "schemas"
            shutil.copytree(compiler.SCHEMA_DIR, schema_dir)
            self.assertEqual(self.compile(schema_dir=schema_dir)["verdict"], "compiled")
            path = schema_dir / "release-definition.schema.yml"
            schema = yaml.safe_load(path.read_text(encoding="utf-8"))
            schema["required"].append("new-required-binding")
            path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
            self.assert_rejected(schema_dir=schema_dir)
            path.unlink()
            self.assert_rejected(schema_dir=schema_dir)
        for path in (("schema",), ("acceptance_matrix", "schema")):
            with self.subTest(version=path):
                document = copy.deepcopy(self.release)
                if len(path) == 1:
                    document[path[0]] = "release-definition/v99"
                else:
                    document[path[0]][path[1]] = "release-acceptance-matrix/v99"
                self.assert_rejected(document)

    def test_matrix_schema_is_loaded_and_remote_references_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            schema_dir = Path(temporary) / "schemas"
            shutil.copytree(compiler.SCHEMA_DIR, schema_dir)
            path = schema_dir / "acceptance-matrix.schema.yml"
            original = yaml.safe_load(path.read_text(encoding="utf-8"))
            schema = copy.deepcopy(original)
            schema["properties"]["rows"]["maxItems"] = 16
            path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
            self.assert_rejected(schema_dir=schema_dir)
            schema = copy.deepcopy(original)
            schema["$schema"] = "unsupported-schema-version"
            path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
            self.assert_rejected(schema_dir=schema_dir)
            schema = copy.deepcopy(original)
            schema["$ref"] = "https://example.invalid/" + SENTINEL
            path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
            self.assert_rejected(schema_dir=schema_dir)

    def test_runtime_bound_legacy_artifact_requires_release_digest(self):
        contract = copy.deepcopy(self.contract)
        del contract["artifacts"][0]["immutable_reference"]
        contract["artifacts"][0]["immutable_reference_mode"] = "runtime-bound-sha256"
        document = copy.deepcopy(self.release)
        document["realization_contract_digest"] = compiler.digest_document(contract)
        self.assertEqual(self.compile(document, contract)["verdict"], "compiled")
        document["artifact_digests"][0]["digest"] = "latest"
        self.assert_rejected(document, contract)

    def test_checked_in_negative_mutations_fail_closed(self):
        fixture = compiler.load_document(DIRECTORY / "fixtures" / "release-negative-cases.yml")
        self.assertEqual(fixture["base_fixture"], "valid-release.yml")
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                document = copy.deepcopy(self.release)
                target = document
                for step in case["path"][:-1]:
                    target = target[step]
                key = case["path"][-1]
                if case["operation"] == "remove":
                    del target[key]
                else:
                    self.assertEqual(case["operation"], "set")
                    target[key] = case["value"]
                self.assert_rejected(document, code=case.get("expected_code"))

    def test_document_loader_rejects_ambiguous_or_unbounded_input(self):
        invalid_documents = (
            "release_id: first\nrelease_id: second\n",
            '{"release_id":"first","release_id":"second"}',
            "first: &shared {field: value}\nsecond: *shared\n",
            "cycle: &cycle [*cycle]\n",
            "---\nfirst: document\n---\nsecond: document\n",
            "invalid: [" + SENTINEL,
            "value: " + "[" * 200 + "0" + "]" * 200,
            "#" * (1024 * 1024 + 1),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "document.yml"
            for index, content in enumerate(invalid_documents):
                with self.subTest(document=index):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(compiler.ReleaseFailure) as caught:
                        compiler.load_document(path)
                    self.assertNotIn(SENTINEL, str(caught.exception))
            path.write_bytes(b"\xff\xfe\x00")
            with self.assertRaises(compiler.ReleaseFailure):
                compiler.load_document(path)
            with self.assertRaises(compiler.ReleaseFailure):
                compiler.load_document(Path(temporary) / SENTINEL)

    def test_public_and_compatibility_commands_produce_identical_results(self):
        expected = self.compile()
        commands = (
            (["--release", str(FIXTURE), "--contract", str(CONTRACT), "--json"], False),
            ([str(FIXTURE), "--contract", str(CONTRACT)], True),
            (["--release", str(FIXTURE), "--contract", str(CONTRACT)], True),
            (["--release", str(FIXTURE), "--contract", str(CONTRACT), "--baseline-release", str(FIXTURE)], False),
        )
        for arguments, compatibility in commands:
            with self.subTest(arguments=arguments, compatibility=compatibility):
                result = self.command(arguments, compatibility)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(json.loads(result.stdout), expected)

    def test_public_commands_reject_unsafe_documents_without_echo(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / (SENTINEL + ".yml")
            document = copy.deepcopy(self.release)
            document["secret_value"] = SENTINEL
            path.write_text(yaml.safe_dump(document), encoding="utf-8")
            for compatibility in (False, True):
                with self.subTest(compatibility=compatibility):
                    self.assert_safe_command_failure(["--release", str(path), "--contract", str(CONTRACT)], compatibility)
            path.write_text("invalid: [" + SENTINEL, encoding="utf-8")
            self.assert_safe_command_failure(["--release", str(path), "--contract", str(CONTRACT)])

    def test_public_commands_reject_invalid_arguments_without_echo(self):
        arguments = ["--release", str(FIXTURE), "--contract", str(CONTRACT)]
        for suffix in (["--unknown-option", SENTINEL], ["--through", SENTINEL],
                       ["--validate-contract"], ["--facts", SENTINEL],
                       ["--release", SENTINEL], ["--baseline-release"],
                       ["--release=" + SENTINEL]):
            with self.subTest(suffix=suffix):
                self.assert_safe_command_failure(arguments + suffix)
        self.assert_safe_command_failure(["--release", SENTINEL, "--contract", str(CONTRACT)])
        self.assert_safe_command_failure(["--release", str(FIXTURE)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
