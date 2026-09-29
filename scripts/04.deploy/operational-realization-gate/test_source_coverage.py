#!/usr/bin/env python3
"""Mutation tests for independently discovered, source-only release coverage."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-source-coverage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify independent source discovery, adoption, coverage, scoped obligations and fail-closed mutations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
sys.path.insert(0, str(DIRECTORY))
sys.path.insert(0, str(ROOT / "scripts/04.deploy/release-control/discovery"))
import source_coverage as coverage
import source_inventory as discovery

FIXTURE = DIRECTORY / "fixtures/source-coverage"
SENTINEL = "SENTINEL-SENSITIVE-DO-NOT-PRINT"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
EXECUTABLES = {
    "container", "script-entrypoint", "source-entrypoint", "package-command",
    "package-bin", "workflow-step", "workflow-service",
}
BINDINGS = {
    "command-binding": "command", "configuration-binding": "configuration",
    "secret-binding": "secret", "identity-binding": "identity",
}
GATES = (
    "scope-risk", "acceptance-contract", "source-contracts", "unit-contract-tests",
    "integration-tests", "exact-artifact-tests", "supply-chain-proof",
    "iac-static-validation", "change-set-review", "drift-dependency-preflight",
    "candidate-runtime-proof", "per-task-live-preflight", "controlled-state-change",
    "post-change-verification", "rollback-recovery", "evidence-retention",
    "continuous-operation",
)


def fixture_composition(inventory):
    """Declare the baseline once; subsequent source mutations keep it frozen."""
    observations = inventory["observations"]
    executable = [item for item in observations if item["kind"] in EXECUTABLES]
    operations, artifacts, subject_operations = [], [], {}
    for index, item in enumerate(executable):
        operation_id, artifact_id = f"operation-{index}", f"artifact-{index}"
        operations.append({
            "id": operation_id, "execution_unit": f"execution-{index}",
            "operation_profile": "service-rollout" if index == 0 else "finite-job",
            "artifact_id": artifact_id, "observation_ids": [item["id"]],
            "resource_access": [],
        })
        artifacts.append({"id": artifact_id, "kind": "container-image", "digest": DIGEST_A,
                          "observation_ids": [item["id"]]})
        subject_operations[item["subject_id"]] = operation_id
        subject_operations[item["id"]] = operation_id
    resources = []
    for index, item in enumerate(observations):
        if item["kind"] not in {"resource", "external-dependency"}:
            continue
        external = item["kind"] == "external-dependency"
        resource_id = f"resource-{index}"
        resources.append({
            "id": resource_id, "provider_boundary": "warehouse-provider" if external else "host-provider",
            "owner": "warehouse-team" if external else "application-team",
            "management": "external" if external else "managed",
            "permitted_effects": ["inspect", "consume"] if external else ["inspect", "create", "update"],
            "cleanup_owner": "external" if external else "release",
            "authority_revision": DIGEST_B, "observation_ids": [item["id"]],
        })
        for operation in operations:
            operation["resource_access"].append({"resource_id": resource_id,
                                                  "effect": "consume" if external else "inspect"})
    bindings = []
    for item in observations:
        if item["kind"] in BINDINGS:
            parent = next((candidate for candidate in observations if candidate["id"] == item["subject_id"]), None)
            operation_ids = ([operation["id"] for operation in operations] if parent and parent["kind"] == "resource"
                             else [subject_operations.get(item["subject_id"], operations[0]["id"])])
            for operation_id in operation_ids:
                bindings.append({"observation_id": item["id"], "operation_id": operation_id,
                                 "kind": BINDINGS[item["kind"]]})
        elif item["kind"] in {"image-command", "package-export"}:
            artifacts[0]["observation_ids"].append(item["id"])
    return {"schema": "release-source-composition/v1", "target_id": "sandbox/delivery",
            "inventory_digest": inventory["inventory_digest"], "artifacts": artifacts,
            "operations": operations, "resources": resources, "bindings": bindings}


class SourceCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="release-source-coverage-")
        self.addCleanup(self.temporary.cleanup)
        self.source_root = Path(self.temporary.name) / "source"
        shutil.copytree(FIXTURE, self.source_root)
        self.inventory = discovery.discover(self.source_root)
        self.composition = fixture_composition(self.inventory)
        self.ledger = coverage.make_ledger(self.inventory)
        self.review_ledger(self.ledger)

    @staticmethod
    def review_ledger(ledger):
        for entry in ledger["entries"]:
            entry["review_status"] = "reviewed"

    def compile(self, inventory=None, composition=None, ledger=None, **kwargs):
        return coverage.compile_coverage(
            self.inventory if inventory is None else inventory,
            self.composition if composition is None else composition,
            self.ledger if ledger is None else ledger,
            as_of="2026-09-28", **kwargs,
        )

    def assert_blocked(self, inventory=None, composition=None, ledger=None, **kwargs):
        try:
            result = self.compile(inventory, composition, ledger, **kwargs)
        except coverage.CoverageFailure as error:
            self.assertTrue(error.code)
            self.assertNotIn(SENTINEL, str(error))
            return None
        self.assertEqual(result["verdict"], "blocked")
        self.assertIs(result["authorized"], False)
        self.assertTrue(result["findings"])
        self.assertNotIn(SENTINEL, json.dumps(result))
        return result

    def task_document(self):
        return json.loads((self.source_root / "infra/04.deploy/tasks.json").read_text())

    def write_tasks(self, document):
        (self.source_root / "infra/04.deploy/tasks.json").write_text(json.dumps(document))

    def command(self, *arguments):
        return subprocess.run(["bash", str(DIRECTORY / "script.sh"), *map(str, arguments)],
                              cwd=ROOT, capture_output=True, text=True, check=False)

    def write_inputs(self):
        composition_file = Path(self.temporary.name) / "composition.json"
        ledger_file = Path(self.temporary.name) / "ledger.json"
        composition_file.write_text(json.dumps(self.composition))
        ledger_file.write_text(json.dumps(self.ledger))
        return composition_file, ledger_file

    def test_static_fixture_is_discovered_without_execution_or_findings(self):
        self.assertEqual(self.inventory["schema"], "source-inventory/v1")
        self.assertEqual(self.inventory["findings"], [])
        self.assertEqual(self.inventory, discovery.discover(self.source_root))
        kinds = [item["kind"] for item in self.inventory["observations"]]
        self.assertEqual(kinds.count("container"), 2)
        for kind in ("resource", "command-binding", "configuration-binding", "secret-binding", "identity-binding"):
            self.assertIn(kind, kinds)
        self.assertNotIn("query.js", json.dumps(self.inventory))
        self.assertNotIn("synthetic-credential-reference", json.dumps(self.inventory))
        self.assertNotIn("synthetic-task-identity-reference", json.dumps(self.inventory))

    def test_reviewed_complete_composition_is_deterministic_and_unauthorized(self):
        originals = copy.deepcopy((self.inventory, self.composition, self.ledger))
        result = self.compile()
        self.assertEqual(result["verdict"], "covered")
        self.assertIs(result["authorized"], False)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result, self.compile())
        self.assertEqual((self.inventory, self.composition, self.ledger), originals)
        rows = result["acceptance_obligations"]
        self.assertEqual(len(rows), 17)
        self.assertEqual([row["stage"] for row in rows], list(range(1, 18)))
        self.assertEqual([row["gate"] for row in rows], list(GATES))
        self.assertTrue(all(row["assertions"] for row in rows))

    def test_every_operation_has_distinct_obligations_at_operation_scoped_gates(self):
        result = self.compile()
        expected_operations = {operation["id"] for operation in self.composition["operations"]}
        for row in result["acceptance_obligations"]:
            if row["stage"] not in {5, 6, 11, 12, 13, 14, 15, 17}:
                continue
            with self.subTest(gate=row["gate"]):
                assertions = [item for item in row["assertions"] if item["scope"] == "operation"]
                self.assertEqual({item["subject_id"] for item in assertions}, expected_operations)
                self.assertEqual(len(assertions), len(expected_operations))
                self.assertTrue(all(item["applicability"] == "required" for item in assertions))
                self.assertEqual(len({item["id"] for item in assertions}), len(assertions))
                for assertion in assertions:
                    operation = next(item for item in self.composition["operations"]
                                     if item["id"] == assertion["subject_id"])
                    self.assertEqual(assertion["operation_profile"], operation["operation_profile"])
                    self.assertEqual(assertion["artifact_id"], operation["artifact_id"])
                    self.assertTrue(assertion["basis_observation_ids"])
                    self.assertEqual(assertion["rule_version"], "source-coverage/v1")
                    self.assertTrue(assertion["evidence"]["proof_levels"])
                    self.assertTrue(assertion["evidence"]["environments"])
                    self.assertEqual(set(assertion["invalidated_by"]),
                                     {"inventory", "composition", "ledger", "policy"})

    def test_external_reference_has_scoped_applicability_without_waiving_a_gate(self):
        result = self.compile()
        dependencies = {resource["id"] for resource in self.composition["resources"]
                        if resource["management"] == "external"}
        self.assertTrue(dependencies)
        self.assertEqual(len(result["acceptance_obligations"]), 17)
        for row in result["acceptance_obligations"]:
            if row["stage"] not in {8, 9, 10}:
                continue
            assertions = [item for item in row["assertions"] if item["scope"] == "dependency"]
            self.assertEqual({item["subject_id"] for item in assertions}, dependencies)
            for assertion in assertions:
                self.assertEqual(assertion["provider_boundary"], "warehouse-provider")
                self.assertTrue(assertion["basis_observation_ids"])
                if row["stage"] in {8, 9} and assertion["rule"] != "dependency-access-authority":
                    self.assertEqual(assertion["applicability"], "not-applicable")
                    self.assertEqual(assertion["rule"], "external-reference-no-managed-effect")
                else:
                    self.assertEqual(assertion["applicability"], "required")

    def test_external_consumption_cannot_authorize_mutation_or_cleanup(self):
        for effect in ("create", "update", "delete", "cleanup"):
            with self.subTest(effect=effect):
                composition = copy.deepcopy(self.composition)
                resource = next(item for item in composition["resources"] if item["management"] == "external")
                access = next(item for item in composition["operations"][0]["resource_access"]
                              if item["resource_id"] == resource["id"])
                access["effect"] = effect
                self.assert_blocked(composition=composition)
                resource["permitted_effects"].append(effect)
                self.assert_blocked(composition=composition)
        composition = copy.deepcopy(self.composition)
        next(item for item in composition["resources"] if item["management"] == "external")["cleanup_owner"] = "release"
        self.assert_blocked(composition=composition)

    def test_declared_dependency_must_be_bound_to_every_source_parent_consumer(self):
        for missing in ("all", "one-operation"):
            with self.subTest(missing=missing):
                composition = copy.deepcopy(self.composition)
                external = {item["id"] for item in composition["resources"] if item["management"] == "external"}
                affected = composition["operations"] if missing == "all" else composition["operations"][:1]
                for operation in affected:
                    operation["resource_access"] = [item for item in operation["resource_access"]
                                                    if item["resource_id"] not in external]
                self.assert_blocked(composition=composition)

    def test_resource_ownership_cannot_be_relabeled_to_evade_authority(self):
        for management in ("managed", "external"):
            with self.subTest(management=management):
                composition = copy.deepcopy(self.composition)
                resource = next(item for item in composition["resources"] if item["management"] != management)
                resource["management"] = management
                resource["cleanup_owner"] = "external" if management == "external" else "release"
                resource["permitted_effects"] = ["inspect", "consume"]
                self.assert_blocked(composition=composition)

    def test_container_cannot_be_relabelled_provider_native_to_skip_artifact_proof(self):
        composition = copy.deepcopy(self.composition)
        composition["artifacts"][0]["kind"] = "provider-definition"
        self.assert_blocked(composition=composition)

    def test_authority_and_profile_changes_invalidate_coverage_digest(self):
        baseline = self.compile()
        for mutation in ("authority", "profile", "artifact"):
            with self.subTest(mutation=mutation):
                composition = copy.deepcopy(self.composition)
                if mutation == "authority":
                    composition["resources"][0]["authority_revision"] = DIGEST_A
                elif mutation == "profile":
                    composition["operations"][0]["operation_profile"] = "finite-job"
                else:
                    composition["artifacts"][0]["digest"] = DIGEST_B
                result = self.compile(composition=composition)
                self.assertEqual(result["verdict"], "covered")
                self.assertNotEqual(result["coverage_digest"], baseline["coverage_digest"])

    def test_temporary_compatibility_requires_future_expiry_and_replacement(self):
        ledger = copy.deepcopy(self.ledger)
        entry = ledger["entries"][0]
        entry["disposition"] = "temporary-compatible"
        self.assert_blocked(ledger=ledger)
        entry["replacement_profile"] = "finite-job"
        entry["expires_on"] = "2026-09-29"
        self.assertEqual(self.compile(ledger=ledger)["verdict"], "covered")
        for expiry in ("2026-09-27", "2026-09-28", "2026-02-31", "no-expiry"):
            with self.subTest(expiry=expiry):
                entry["expires_on"] = expiry
                self.assert_blocked(ledger=ledger)

    def test_adoption_template_is_pending_and_cannot_self_approve(self):
        template = coverage.make_ledger(self.inventory)
        self.assertEqual(template["schema"], "source-adoption-ledger/v1")
        self.assertTrue(template["entries"])
        self.assertTrue(all(entry["review_status"] == "pending" for entry in template["entries"]))
        self.assert_blocked(ledger=template)

    def test_missing_or_duplicate_adoption_entries_fail_closed(self):
        for mutation in ("missing", "duplicate", "digest"):
            with self.subTest(mutation=mutation):
                ledger = copy.deepcopy(self.ledger)
                if mutation == "missing":
                    ledger["entries"].pop()
                elif mutation == "duplicate":
                    ledger["entries"].append(copy.deepcopy(ledger["entries"][0]))
                else:
                    ledger["entries"][0]["source_digest"] = DIGEST_B
                self.assert_blocked(ledger=ledger)

    def test_disposition_cannot_hide_a_runtime_source(self):
        task_source = next(source["id"] for source in self.inventory["sources"]
                           if source["path"].endswith("tasks.json"))
        for disposition in ("test-only", "historical", "retire"):
            with self.subTest(disposition=disposition):
                ledger = copy.deepcopy(self.ledger)
                next(entry for entry in ledger["entries"] if entry["source_id"] == task_source)["disposition"] = disposition
                self.assert_blocked(ledger=ledger)

    def test_hidden_sidecar_is_detected_even_when_old_declarations_agree(self):
        document = self.task_document()
        containers = document["Resources"]["QueryAndLoadTask"]["Properties"]["ContainerDefinitions"]
        containers.append({"Name": "unlisted-sidecar", "Image": "synthetic-sidecar-image",
                           "Command": ["node", "hidden.js"]})
        self.write_tasks(document)
        inventory = discovery.discover(self.source_root)
        self.assertNotEqual(inventory["inventory_digest"], self.inventory["inventory_digest"])
        self.assert_blocked(inventory=inventory)
        # Fresh source reviews and a refreshed digest still cannot authorize an
        # executable absent from the otherwise internally consistent declaration.
        ledger = coverage.make_ledger(inventory)
        self.review_ledger(ledger)
        composition = copy.deepcopy(self.composition)
        composition["inventory_digest"] = inventory["inventory_digest"]
        self.assert_blocked(inventory=inventory, composition=composition, ledger=ledger)

    def test_undeclared_package_command_is_independently_detected(self):
        manifest = self.source_root / "package.json"
        document = json.loads(manifest.read_text())
        document["scripts"] = {"load-hidden": "node hidden.js"}
        manifest.write_text(json.dumps(document))
        inventory = discovery.discover(self.source_root)
        self.assertIn("package-command", {item["kind"] for item in inventory["observations"]})
        self.assert_blocked(inventory=inventory)

    def test_new_script_entrypoint_is_independently_detected(self):
        script = self.source_root / "scripts/04.deploy/hidden/script.sh"
        script.parent.mkdir(parents=True)
        script.write_text("#!/usr/bin/env bash\nexit 0\n")
        inventory = discovery.discover(self.source_root)
        self.assertIn("script-entrypoint", {item["kind"] for item in inventory["observations"]})
        self.assert_blocked(inventory=inventory)

    def test_missing_secret_binding_is_rejected(self):
        composition = copy.deepcopy(self.composition)
        binding = next(item for item in composition["bindings"] if item["kind"] == "secret")
        composition["bindings"].remove(binding)
        self.assert_blocked(composition=composition)

    def test_sibling_operation_cannot_claim_another_container_binding(self):
        composition = copy.deepcopy(self.composition)
        binding = next(item for item in composition["bindings"] if item["kind"] == "command")
        binding["operation_id"] = next(operation["id"] for operation in composition["operations"]
                                        if operation["id"] != binding["operation_id"])
        self.assert_blocked(composition=composition)

    def test_each_discovered_operation_requires_one_unique_owner(self):
        for mutation in ("omitted", "shared", "unbacked"):
            with self.subTest(mutation=mutation):
                composition = copy.deepcopy(self.composition)
                if mutation == "omitted":
                    composition["operations"].pop()
                elif mutation == "shared":
                    composition["operations"][1]["observation_ids"] += composition["operations"][0]["observation_ids"]
                else:
                    composition["operations"][0]["observation_ids"] = [DIGEST_B]
                self.assert_blocked(composition=composition)

    def test_two_containers_cannot_be_collapsed_into_one_operation(self):
        composition = copy.deepcopy(self.composition)
        first, second = composition["operations"]
        first["observation_ids"] += second["observation_ids"]
        composition["operations"] = [first]
        composition["artifacts"][0]["observation_ids"] += composition["artifacts"][1]["observation_ids"]
        composition["artifacts"] = composition["artifacts"][:1]
        for binding in composition["bindings"]:
            binding["operation_id"] = first["id"]
        unique_bindings = {json.dumps(item, sort_keys=True): item for item in composition["bindings"]}
        composition["bindings"] = list(unique_bindings.values())
        self.assert_blocked(composition=composition)

    def test_artifact_from_sibling_operation_cannot_replace_its_own_binding(self):
        composition = copy.deepcopy(self.composition)
        composition["operations"][0]["artifact_id"], composition["operations"][1]["artifact_id"] = (
            composition["operations"][1]["artifact_id"], composition["operations"][0]["artifact_id"])
        self.assert_blocked(composition=composition)

    def test_unknown_duplicate_or_wrong_kind_binding_is_rejected(self):
        for mutation in ("unknown", "duplicate", "wrong-kind"):
            with self.subTest(mutation=mutation):
                composition = copy.deepcopy(self.composition)
                if mutation == "unknown":
                    composition["bindings"][0]["observation_id"] = DIGEST_B
                elif mutation == "duplicate":
                    composition["bindings"].append(copy.deepcopy(composition["bindings"][0]))
                else:
                    composition["bindings"][0]["kind"] = "dependency"
                self.assert_blocked(composition=composition)

    def test_artifact_and_resource_dangling_references_are_rejected(self):
        for mutation in ("artifact", "resource", "unreferenced-artifact"):
            with self.subTest(mutation=mutation):
                composition = copy.deepcopy(self.composition)
                if mutation == "artifact":
                    composition["operations"][0]["artifact_id"] = "missing-artifact"
                elif mutation == "resource":
                    composition["operations"][0]["resource_access"].append({"resource_id": "missing-resource", "effect": "inspect"})
                else:
                    artifact = copy.deepcopy(composition["artifacts"][0])
                    artifact["id"] = "unused-artifact"
                    composition["artifacts"].append(artifact)
                self.assert_blocked(composition=composition)

    def test_inventory_tampering_and_unknown_fields_fail_closed(self):
        for section in ("sources", "observations", "findings"):
            with self.subTest(section=section):
                inventory = copy.deepcopy(self.inventory)
                if section == "findings":
                    inventory["findings"].append({"code": "unreviewed-input", "source_id": inventory["sources"][0]["id"]})
                else:
                    inventory[section].pop()
                self.assert_blocked(inventory=inventory)
        for name in ("inventory", "composition", "ledger"):
            with self.subTest(unsafe_document=name):
                document = copy.deepcopy(getattr(self, name))
                document["password"] = SENTINEL
                self.assert_blocked(**{name: document})

    def test_changed_command_or_configuration_invalidates_source_evidence(self):
        for field in ("Command", "Environment"):
            with self.subTest(field=field):
                document = self.task_document()
                container = document["Resources"]["QueryAndLoadTask"]["Properties"]["ContainerDefinitions"][0]
                if field == "Command":
                    container[field] = ["node", "changed.js"]
                else:
                    container[field][0]["Value"] = "changed-reference"
                self.write_tasks(document)
                inventory = discovery.discover(self.source_root)
                self.assertNotEqual(inventory["inventory_digest"], self.inventory["inventory_digest"])
                self.assert_blocked(inventory=inventory)

    def test_opaque_source_and_symlink_cannot_be_approved_by_ledger(self):
        for mutation in ("dynamic-source", "symlink"):
            with self.subTest(mutation=mutation):
                path = self.source_root / "infra/04.deploy/unsupported.ts"
                if path.exists() or path.is_symlink():
                    path.unlink()
                if mutation == "dynamic-source":
                    path.write_text("export const infrastructure = buildUnknownResources();\n")
                else:
                    path.symlink_to(Path(self.temporary.name) / "outside.json")
                inventory = discovery.discover(self.source_root)
                self.assertTrue(inventory["findings"])
                ledger = coverage.make_ledger(inventory)
                self.review_ledger(ledger)
                composition = copy.deepcopy(self.composition)
                composition["inventory_digest"] = inventory["inventory_digest"]
                self.assert_blocked(inventory=inventory, composition=composition, ledger=ledger)

    def test_safe_output_does_not_include_discovered_values(self):
        document = self.task_document()
        container = document["Resources"]["QueryAndLoadTask"]["Properties"]["ContainerDefinitions"][0]
        container["Environment"][0]["Value"] = SENTINEL
        self.write_tasks(document)
        inventory = discovery.discover(self.source_root)
        self.assertNotIn(SENTINEL, json.dumps(inventory))
        self.assert_blocked(inventory=inventory)
        result = self.command("--discover", "--source-root", self.source_root)
        self.assertNotIn(SENTINEL, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertIn("schema", json.loads(result.stdout))

    def release_inputs(self):
        # Reuse the established independently validated heterogeneous release
        # fixture builder; discovery and coverage declarations stay separate.
        from test_release_compiler import ReleaseCompilerTests
        fixtures = ReleaseCompilerTests(methodName="runTest")
        fixtures.setUp()
        document, contract = fixtures.heterogeneous_release()
        composition = copy.deepcopy(self.composition)
        operation_ids = {}
        for operation, release_operation, artifact, release_artifact in zip(
                composition["operations"], document["operation_graph"],
                composition["artifacts"], document["artifact_digests"]):
            operation_ids[operation["id"]] = release_operation["operation_id"]
            operation.update(id=release_operation["operation_id"],
                             execution_unit=release_operation["execution_unit"],
                             operation_profile=release_operation["operation_profile"],
                             artifact_id=release_operation["artifact_id"])
            artifact.update(id=release_artifact["artifact_id"], digest=release_artifact["digest"])
        for binding in composition["bindings"]:
            binding["operation_id"] = operation_ids[binding["operation_id"]]
        document["target_composition_revision"] = coverage.release.digest_document(composition)
        return composition, document, contract

    def test_coverage_integrates_with_existing_release_without_granting_authority(self):
        composition, document, contract = self.release_inputs()
        result = self.compile(composition=composition, release_document=document, contract=contract)
        self.assertEqual(result["verdict"], "covered")
        self.assertIs(result["authorized"], False)
        compiled = result["compiled_release"]
        self.assertEqual(compiled["verdict"], "compiled")
        self.assertIs(compiled["authorized"], False)
        self.assertEqual(len(compiled["acceptance_matrix"]), 17)
        self.assertTrue(all(row["verdict"] == "not-started" for row in compiled["acceptance_matrix"]))

    def test_release_cannot_bind_different_composition_or_operation_profiles(self):
        for mutation in ("composition-digest", "target", "profile", "unit", "artifact-digest"):
            with self.subTest(mutation=mutation):
                composition, document, contract = self.release_inputs()
                if mutation == "composition-digest":
                    document["target_composition_revision"] = DIGEST_A
                elif mutation == "target":
                    composition["target_id"] = "sandbox/different"
                elif mutation == "profile":
                    composition["operations"][0]["operation_profile"] = "inspection"
                elif mutation == "unit":
                    composition["operations"][0]["execution_unit"] = "different-execution"
                else:
                    composition["artifacts"][0]["digest"] = DIGEST_B
                if mutation != "composition-digest":
                    document["target_composition_revision"] = coverage.release.digest_document(composition)
                self.assert_blocked(composition=composition, release_document=document, contract=contract)

    def test_versioned_coverage_schemas_are_loaded_and_fail_closed(self):
        for schema_name in ("source-inventory", "source-composition", "source-adoption-ledger"):
            for mutation in ("missing", "wrong-version", "remote-reference"):
                with self.subTest(schema=schema_name, mutation=mutation):
                    with tempfile.TemporaryDirectory(prefix="coverage-schema-") as temp:
                        schemas = Path(temp)
                        for source in coverage.SCHEMA_DIR.glob("*.schema.yml"):
                            shutil.copyfile(source, schemas / source.name)
                        filename = schemas / (schema_name + ".schema.yml")
                        if mutation == "missing":
                            filename.unlink()
                        else:
                            document = yaml.safe_load(filename.read_text())
                            document["$id" if mutation == "wrong-version" else "$ref"] = (
                                "urn:untrusted:v2" if mutation == "wrong-version" else "https://invalid.example/schema")
                            filename.write_text(yaml.safe_dump(document))
                        with patch.object(coverage, "SCHEMA_DIR", schemas):
                            with self.assertRaises(coverage.release.ReleaseFailure):
                                self.compile()

    def test_applicability_and_evidence_cannot_be_injected_by_composition(self):
        for field, value in (("applicability", "not-applicable"), ("verdict", "passed"),
                             ("evidence", {"result": "success"}), ("authorized", True)):
            with self.subTest(field=field):
                composition = copy.deepcopy(self.composition)
                composition["operations"][0][field] = value
                self.assert_blocked(composition=composition)

    def test_cli_discovery_and_pending_ledger_are_structured(self):
        result = self.command("--discover", "--source-root", self.source_root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.inventory)
        result = self.command("--discover", "--source-root", self.source_root, "--ledger-template")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), coverage.make_ledger(self.inventory))

    def test_cli_rejects_ambiguous_modes_and_missing_inputs_safely(self):
        for arguments in (
                ("--coverage", "--source-root", self.source_root),
                ("--discover", "--coverage", "--source-root", self.source_root),
                ("--discover", "--source-root", self.source_root, "--source-root", self.source_root),
                ("--discover", "--source-root", self.source_root, "--password", SENTINEL)):
            with self.subTest(arguments=arguments[:-1]):
                result = self.command(*arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn(SENTINEL, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output["verdict"], "failed")
                self.assertIs(output["authorized"], False)

    def test_cli_coverage_recollects_sources_and_rejects_stale_inputs(self):
        composition_file, ledger_file = self.write_inputs()
        arguments = ("--coverage", "--source-root", self.source_root,
                     "--composition", composition_file, "--adoption-ledger", ledger_file)
        result = self.command(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "covered")
        document = self.task_document()
        document["Resources"]["HiddenTask"] = {"Type": "AWS::ECS::TaskDefinition", "Properties": {
            "ContainerDefinitions": [{"Name": "hidden", "Image": "hidden-image", "Command": ["hidden"]}]}}
        self.write_tasks(document)
        result = self.command(*arguments)
        self.assertNotEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertIn(output["verdict"], {"blocked", "failed"})
        self.assertIs(output["authorized"], False)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
