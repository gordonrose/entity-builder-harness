#!/usr/bin/env python3
"""Exercise source operation contract accounting and reject false closure claims."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-operation-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Test source and caller bindings and retain blocked qualification after contract review.
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
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
sys.path.insert(0, str(DIRECTORY.parent / "release-control/discovery"))

import caller_coverage
import caller_inventory
import operation_contracts as operations
import release_compiler as release

WORKFLOW = ".github/workflows/operations.yml"
UNKNOWN = "sha256:" + "a" * 64
SENTINEL = "SENTINEL-SENSITIVE-DO-NOT-PRINT"


def digest(value):
    return release.digest_document(value)


def rehash(inventory):
    inventory["inventory_digest"] = digest({key: value for key, value in inventory.items() if key != "inventory_digest"})


class OperationContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="operation-contracts-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write(WORKFLOW, """name: Operation fixture
on: workflow_dispatch
jobs:
  inspect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run inspect
      - run: python3 scripts/04.deploy/inspect.py --mode strict
      - run: tsc -p apps/sample/tsconfig.json
""")
        self.write("package.json", json.dumps({"name": "operation-fixture", "scripts": {
            "inspect": "python3 scripts/04.deploy/inspect.py --mode readonly"}}))
        self.write("scripts/04.deploy/inspect.py", "import helper\nprint('inspect')\n")
        self.write("scripts/04.deploy/helper.py", "VALUE = 'checked'\n")
        self.write("apps/sample/tsconfig.json", json.dumps({"include": ["src/**/*.ts"]}))
        self.write("apps/sample/src/input.ts", "export const value = 'build input';\n")
        self.graph = caller_inventory.discover_callers(self.root, WORKFLOW)
        self.review = caller_coverage.make_review(self.graph)
        for index, binding in enumerate(self.review["bindings"]):
            binding.update(owner="deployment-team", operation_id=f"reviewed-operation-{index}",
                           operation_profile="inspection", review_status="reviewed")
        self.inventory = self.inventory_fixture()
        self.contracts = operations.make_contracts(self.inventory, self.graph, self.review)
        for binding in self.contracts["bindings"]:
            binding["review_status"] = "reviewed"

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def inventory_fixture(self):
        sources = copy.deepcopy(self.graph["sources"])
        subjects, observations, dependencies = [], [], []
        nodes = {item["id"]: item for item in self.graph["nodes"]}
        for subject_id, kind in operations.selected_subjects(nodes).items():
            node = nodes[subject_id]
            subjects.append({"id": subject_id, "kind": kind, "source_id": node["source_id"],
                             "detail_digest": node["detail_digest"], "invocation_ids": sorted(
                                 edge["id"] for edge in self.graph["edges"] if edge["callee_id"] == subject_id)})
            observations.append({"id": digest([subject_id, "observation"]), "subject_id": subject_id,
                                 "source_id": node["source_id"], "kind": "script-arguments" if kind == "script" else "external-reference",
                                 "locator_digest": digest([subject_id, "locator"]), "detail_digest": digest([subject_id, "detail"])})
            if kind == "script":
                relative = "scripts/04.deploy/helper.py"
                source_id = "sha256:" + hashlib.sha256(relative.encode()).hexdigest()
                sources.append({"id": source_id, "path": relative,
                                "digest": "sha256:" + hashlib.sha256((self.root / relative).read_bytes()).hexdigest()})
                dependencies.append({"id": digest([subject_id, "dependency"]), "subject_id": subject_id,
                                     "from_source_id": node["source_id"], "to_source_id": source_id,
                                     "kind": "python-import", "detail_digest": digest([subject_id, "helper"])})
                observations.append({"id": digest([subject_id, "import-observation"]), "subject_id": subject_id,
                                     "source_id": source_id, "kind": "python-module",
                                     "locator_digest": digest([subject_id, "module-locator"]),
                                     "detail_digest": digest([subject_id, "module-detail"])})
        result = {"schema": "source-operation-inventory/v1", "graph_digest": self.graph["graph_digest"],
                  "collector_revision": digest("operation-fixture-collector"), "sources": sources,
                  "subjects": subjects, "observations": observations, "dependencies": dependencies,
                  "findings": [{"subject_id": subject["id"], "code": "semantic-proof-required"} for subject in subjects]}
        rehash(result)
        return result

    def compile(self, inventory=None, graph=None, review=None, contracts=None):
        return operations.compile_operations(self.inventory if inventory is None else inventory,
                                             self.graph if graph is None else graph,
                                             self.review if review is None else review,
                                             self.contracts if contracts is None else contracts)

    def assert_blocked(self, **arguments):
        try:
            result = self.compile(**arguments)
        except release.ReleaseFailure as error:
            self.assertTrue(error.code)
            self.assertNotIn(SENTINEL, str(error))
            return
        self.assertEqual(result["contracts_verdict"], "incomplete")
        self.assertEqual(result["source_closure"], "blocked")
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertIs(result["authorized"], False)
        self.assertNotIn("contracts_digest", result)
        self.assertEqual(result["obligations"], [])
        self.assertTrue(result["findings"])
        self.assertNotIn(SENTINEL, json.dumps(result))

    def test_template_is_pending_and_exactly_accounts_for_selected_subjects(self):
        template = operations.make_contracts(self.inventory, self.graph, self.review)
        self.assertEqual({item["subject_id"] for item in template["bindings"]},
                         {item["id"] for item in self.inventory["subjects"]})
        self.assertEqual({item["kind"] for item in self.inventory["subjects"]}, {"script", "action", "tool"})
        self.assertTrue(all(item["review_status"] == "pending" for item in template["bindings"]))
        self.assert_blocked(contracts=template)

    def test_complete_contracts_remain_blocked_and_unauthorized(self):
        result = self.compile()
        self.assertEqual(result["schema"], "source-operation-result/v1")
        self.assertEqual(result["contracts_verdict"], "complete")
        self.assertEqual(result["source_closure"], "blocked")
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertIs(result["authorized"], False)
        self.assertEqual(result["findings"], [])
        self.assertTrue(result["contracts_digest"].startswith("sha256:"))
        self.assertEqual(result, self.compile())

    def test_all_required_later_evidence_survives_source_review(self):
        result = self.compile()
        self.assertEqual(len(result["obligations"]), len(self.inventory["subjects"]))
        for obligation in result["obligations"]:
            self.assertEqual(obligation["profile_basis"], "reviewed-source-declaration")
            self.assertEqual(obligation["source_closure"], "blocked")
            self.assertEqual(obligation["qualification"], "pending")
            self.assertEqual(obligation["unobserved_arguments"], "blocked")
            self.assertEqual([(item["stage"], item["proof"]) for item in obligation["required_evidence"]], operations.EVIDENCE_STAGES)

    def test_evidence_stages_match_the_existing_seventeen_gate_matrix(self):
        schema = release.load_document(operations.SCHEMA_DIR / "acceptance-matrix.schema.yml")
        rows = schema["properties"]["rows"]["prefixItems"]
        names = {stage: row["allOf"][1]["properties"]["gate"]["const"] for stage, row in enumerate(rows, 1)}
        expected = {3: "source-contracts", 6: "exact-artifact-tests", 7: "supply-chain-proof",
                    8: "iac-static-validation", 15: "rollback-recovery"}
        self.assertEqual({stage: names[stage] for stage, _ in operations.EVIDENCE_STAGES}, expected)
        self.assertEqual(len(rows), 17)

    def test_graph_and_collector_findings_are_preserved(self):
        expected = {(item["code"], item["subject_id"]) for item in self.graph["findings"] + self.inventory["findings"]}
        expected.update((code, node["id"]) for node in self.graph["nodes"] for code in node["issues"])
        actual = {(item["code"], item["subject_id"]) for item in self.compile()["source_findings"]}
        self.assertEqual(actual, expected)

    def test_compiler_does_not_mutate_inputs(self):
        before = copy.deepcopy((self.inventory, self.graph, self.review, self.contracts))
        self.compile()
        self.assertEqual(before, (self.inventory, self.graph, self.review, self.contracts))

    def test_pending_binding_cannot_complete(self):
        self.contracts["bindings"][0]["review_status"] = "pending"
        self.assert_blocked()

    def test_each_digest_and_target_binding_is_required(self):
        for field in ("inventory_digest", "graph_digest", "caller_accounting_digest", "target_id"):
            with self.subTest(field=field):
                contracts = copy.deepcopy(self.contracts)
                contracts[field] = "sandbox/other" if field == "target_id" else UNKNOWN
                self.assert_blocked(contracts=contracts)

    def test_missing_duplicate_and_unknown_contract_subjects_fail(self):
        for mode in ("missing", "duplicate", "unknown"):
            with self.subTest(mode=mode):
                contracts = copy.deepcopy(self.contracts)
                if mode == "missing":
                    contracts["bindings"].pop()
                elif mode == "duplicate":
                    contracts["bindings"].append(copy.deepcopy(contracts["bindings"][0]))
                else:
                    contracts["bindings"][0]["subject_id"] = UNKNOWN
                self.assert_blocked(contracts=contracts)

    def test_duplicate_operation_ids_cannot_merge_distinct_subjects(self):
        self.contracts["bindings"][1]["operation_id"] = self.contracts["bindings"][0]["operation_id"]
        self.assert_blocked()

    def test_declared_owner_operation_and_profile_must_match_review(self):
        for field, value in (("owner", "other-team"), ("operation_id", "other-operation"), ("operation_profile", "service-rollout")):
            with self.subTest(field=field):
                contracts = copy.deepcopy(self.contracts)
                contracts["bindings"][0][field] = value
                self.assert_blocked(contracts=contracts)

    def test_exact_invocation_observation_and_dependency_sets_required(self):
        for field in ("invocation_ids", "observation_ids", "dependency_ids"):
            for mode in ("missing", "duplicate", "unknown"):
                with self.subTest(field=field, mode=mode):
                    contracts = copy.deepcopy(self.contracts)
                    binding = next(item for item in contracts["bindings"] if item[field])
                    if mode == "missing":
                        binding[field].pop()
                    elif mode == "duplicate":
                        binding[field].append(binding[field][0])
                    else:
                        binding[field].append(UNKNOWN)
                    self.assert_blocked(contracts=contracts)

    def test_observed_argument_variants_cannot_be_collapsed(self):
        binding = next(item for item in self.contracts["bindings"] if len(item["invocation_ids"]) > 1)
        self.assertEqual(len(binding["invocation_ids"]), 2)
        binding["invocation_ids"].pop()
        self.assert_blocked()

    def test_each_required_safety_rule_is_fixed(self):
        for field in ("argument_policy", "unobserved_arguments", "completion_rule", "failure_state", "recovery_route"):
            with self.subTest(field=field):
                contracts = copy.deepcopy(self.contracts)
                contracts["bindings"][0][field] = "allow"
                self.assert_blocked(contracts=contracts)

    def test_all_evidence_rules_required_without_duplicates_or_unsupported_claims(self):
        for mode in ("missing", "duplicate", "unsupported"):
            with self.subTest(mode=mode):
                contracts = copy.deepcopy(self.contracts)
                rules = contracts["bindings"][0]["evidence_rules"]
                if mode == "missing":
                    rules.pop()
                elif mode == "duplicate":
                    rules[-1] = rules[0]
                else:
                    rules[-1] = "not-applicable"
                self.assert_blocked(contracts=contracts)

    def test_unsafe_and_authority_fields_rejected_at_every_object_level(self):
        for value in (self.inventory, self.inventory["subjects"][0], self.inventory["observations"][0],
                      self.inventory["dependencies"][0], self.contracts, self.contracts["bindings"][0]):
            with self.subTest(keys=list(value)):
                value["authorized"] = True
                self.assert_blocked()
                del value["authorized"]
                value["command"] = SENTINEL
                self.assert_blocked()
                del value["command"]

    def test_unsafe_owner_and_raw_command_values_cannot_escape(self):
        for field in ("owner", "operation_id", "operation_profile", "review_status"):
            with self.subTest(field=field):
                contracts = copy.deepcopy(self.contracts)
                contracts["bindings"][0][field] = SENTINEL
                self.assert_blocked(contracts=contracts)

    def test_unsupported_versions_rejected(self):
        for name in ("inventory", "contracts"):
            with self.subTest(name=name):
                document = copy.deepcopy(getattr(self, name))
                document["schema"] = "source-operation-unsupported/v99"
                self.assert_blocked(**{name: document})

    def test_invalid_inventory_digest_is_rejected(self):
        self.inventory["inventory_digest"] = UNKNOWN
        self.assert_blocked()

    def test_inventory_must_bind_the_exact_caller_graph(self):
        self.inventory["graph_digest"] = UNKNOWN
        rehash(self.inventory)
        self.assert_blocked()

    def test_inventory_graph_sources_must_be_complete_and_unchanged(self):
        for mode in ("missing", "changed"):
            with self.subTest(mode=mode):
                inventory = copy.deepcopy(self.inventory)
                if mode == "missing":
                    inventory["sources"].pop(0)
                else:
                    inventory["sources"][0]["digest"] = UNKNOWN
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_missing_unknown_and_duplicate_inventory_subjects_rejected(self):
        for mode in ("missing", "unknown", "duplicate"):
            with self.subTest(mode=mode):
                inventory = copy.deepcopy(self.inventory)
                if mode == "missing":
                    inventory["subjects"].pop()
                elif mode == "unknown":
                    inventory["subjects"][0]["id"] = UNKNOWN
                else:
                    inventory["subjects"].append(copy.deepcopy(inventory["subjects"][0]))
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_subject_kind_source_and_detail_must_match_graph(self):
        for field, value in (("kind", "action"), ("source_id", UNKNOWN), ("detail_digest", UNKNOWN)):
            with self.subTest(field=field):
                inventory = copy.deepcopy(self.inventory)
                item = next(item for item in inventory["subjects"] if item["kind"] == "script")
                item[field] = value
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_subject_incoming_edges_cannot_be_declared_away(self):
        for mode in ("missing", "unknown", "duplicate"):
            with self.subTest(mode=mode):
                inventory = copy.deepcopy(self.inventory)
                item = next(item for item in inventory["subjects"] if len(item["invocation_ids"]) > 1)
                if mode == "missing":
                    item["invocation_ids"].pop()
                else:
                    item["invocation_ids"].append(UNKNOWN if mode == "unknown" else item["invocation_ids"][0])
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_duplicate_source_paths_and_ids_rejected(self):
        for field in ("id", "path"):
            with self.subTest(field=field):
                inventory = copy.deepcopy(self.inventory)
                inventory["sources"][1][field] = inventory["sources"][0][field]
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_source_paths_cannot_escape_or_use_ambiguous_components(self):
        for value in ("/tmp/source", "scripts/../source", "./source", "scripts//source", "scripts/source/", "https://example.invalid/source"):
            with self.subTest(value=value):
                inventory = copy.deepcopy(self.inventory)
                inventory["sources"][0]["path"] = value
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_observation_and_dependency_ids_must_be_unique(self):
        for field in ("observations", "dependencies"):
            with self.subTest(field=field):
                inventory = copy.deepcopy(self.inventory)
                item = copy.deepcopy(inventory[field][0])
                item["detail_digest"] = UNKNOWN
                inventory[field].append(item)
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_unknown_observation_references_are_rejected(self):
        for field in ("source_id", "subject_id"):
            with self.subTest(field=field):
                inventory = copy.deepcopy(self.inventory)
                inventory["observations"][0][field] = UNKNOWN
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_unknown_dependency_references_are_rejected(self):
        for field in ("from_source_id", "to_source_id", "subject_id"):
            with self.subTest(field=field):
                inventory = copy.deepcopy(self.inventory)
                inventory["dependencies"][0][field] = UNKNOWN
                rehash(inventory)
                self.assert_blocked(inventory=inventory)

    def test_detached_dependency_and_observation_sources_cannot_be_added(self):
        inventory = copy.deepcopy(self.inventory)
        dependency = inventory["dependencies"][0]
        dependency["from_source_id"] = dependency["to_source_id"]
        rehash(inventory)
        self.assert_blocked(inventory=inventory)

    def test_unreachable_added_source_is_rejected(self):
        self.inventory["sources"].append({"id": UNKNOWN, "path": "scripts/detached.py", "digest": UNKNOWN})
        rehash(self.inventory)
        self.assert_blocked()

    def test_finding_must_refer_to_a_selected_subject(self):
        self.inventory["findings"][0]["subject_id"] = UNKNOWN
        rehash(self.inventory)
        self.assert_blocked()

    def test_review_with_any_unaccounted_caller_cannot_generate_or_compile_contracts(self):
        self.review["bindings"][0]["review_status"] = "pending"
        self.assert_blocked()
        with self.assertRaisesRegex(release.ReleaseFailure, "operation-caller-accounting-incomplete"):
            operations.make_contracts(self.inventory, self.graph, self.review)

    def test_changed_caller_profile_invalidates_contracts_even_with_reviewed_status(self):
        selected = self.contracts["bindings"][0]["subject_id"]
        next(item for item in self.review["bindings"] if item["node_id"] == selected)["operation_profile"] = "finite-job"
        self.assert_blocked()

    def test_dependency_byte_change_invalidates_previous_contracts(self):
        inventory = copy.deepcopy(self.inventory)
        dependency_id = inventory["dependencies"][0]["to_source_id"]
        next(item for item in inventory["sources"] if item["id"] == dependency_id)["digest"] = UNKNOWN
        rehash(inventory)
        self.assert_blocked(inventory=inventory)

    def test_new_import_dependency_invalidates_previous_contracts(self):
        inventory = copy.deepcopy(self.inventory)
        dependency = copy.deepcopy(inventory["dependencies"][0])
        dependency.update(id=UNKNOWN, to_source_id=UNKNOWN)
        inventory["sources"].append({"id": UNKNOWN, "path": "scripts/added.py", "digest": UNKNOWN})
        inventory["dependencies"].append(dependency)
        rehash(inventory)
        self.assert_blocked(inventory=inventory)

    def test_collector_revision_change_invalidates_previous_contracts(self):
        self.inventory["collector_revision"] = UNKNOWN
        rehash(self.inventory)
        self.assert_blocked()

    def test_alias_cycles_and_control_characters_are_rejected_before_schema_recursion(self):
        contracts = copy.deepcopy(self.contracts)
        contracts["loop"] = contracts
        self.assert_blocked(contracts=contracts)
        contracts = copy.deepcopy(self.contracts)
        contracts["bindings"][0]["owner"] = "owner\nunsafe"
        self.assert_blocked(contracts=contracts)

    def test_missing_schemas_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="operation-schema-") as directory:
            with patch.object(operations, "SCHEMA_DIR", Path(directory)):
                self.assert_blocked()

    def test_large_fresh_inventory_uses_a_separate_explicit_in_memory_budget(self):
        inventory = copy.deepcopy(self.inventory)
        observation = inventory["observations"][0]
        for index in range(1800):
            item = copy.deepcopy(observation)
            item.update(id=digest(["large-id", index]), locator_digest=digest(["large-locator", index]))
            inventory["observations"].append(item)
        rehash(inventory)
        with self.assertRaisesRegex(release.ReleaseFailure, "document-limit-exceeded"):
            release.bounded_json(inventory)
        contracts = operations.make_contracts(inventory, self.graph, self.review)
        for binding in contracts["bindings"]:
            binding["review_status"] = "reviewed"
        self.assertEqual(self.compile(inventory=inventory, contracts=contracts)["contracts_verdict"], "complete")

    def test_in_memory_budget_does_not_widen_default_or_file_loader_limits(self):
        with self.assertRaisesRegex(release.ReleaseFailure, "document-limit-exceeded"):
            release.bounded_json([0] * 20000)
        release.bounded_json([0] * 20000, max_nodes=operations.MAX_INVENTORY_NODES)
        with self.assertRaisesRegex(release.ReleaseFailure, "document-limit-exceeded"):
            release.bounded_json([0] * operations.MAX_INVENTORY_NODES, max_nodes=operations.MAX_INVENTORY_NODES)
        path = self.root / "oversized-inventory.json"
        path.write_text(' ' * (release.MAX_BYTES + 1))
        with self.assertRaisesRegex(release.ReleaseFailure, "document-limit-exceeded"):
            release.load_document(path)

    def test_inventory_budget_aliases_and_oversized_scalars_fail_closed(self):
        for mode in ("budget", "cycle", "scalar"):
            with self.subTest(mode=mode):
                inventory = copy.deepcopy(self.inventory)
                if mode == "budget":
                    inventory["observations"] = [0] * operations.MAX_INVENTORY_NODES
                elif mode == "cycle":
                    inventory["observations"].append(inventory)
                else:
                    inventory["collector_revision"] = "a" * 16385
                self.assert_blocked(inventory=inventory)

    def test_real_collector_inventory_compiles_and_retains_semantic_blocks(self):
        import operation_inventory
        inventory = operation_inventory.discover_operations(self.root, WORKFLOW, self.graph)
        contracts = operations.make_contracts(inventory, self.graph, self.review)
        for binding in contracts["bindings"]:
            binding["review_status"] = "reviewed"
        result = self.compile(inventory=inventory, contracts=contracts)
        self.assertEqual(result["contracts_verdict"], "complete")
        self.assertEqual(result["source_closure"], "blocked")
        self.assertTrue(result["source_findings"])
        self.assertGreater(result["counts"]["dependencies"], 0)

    def test_real_import_byte_change_requires_contract_review_again(self):
        import operation_inventory
        inventory = operation_inventory.discover_operations(self.root, WORKFLOW, self.graph)
        contracts = operations.make_contracts(inventory, self.graph, self.review)
        for binding in contracts["bindings"]:
            binding["review_status"] = "reviewed"
        self.write("scripts/04.deploy/helper.py", "VALUE = 'changed'\n")
        changed = operation_inventory.discover_operations(self.root, WORKFLOW, self.graph)
        self.assertNotEqual(inventory["inventory_digest"], changed["inventory_digest"])
        self.assert_blocked(inventory=changed, contracts=contracts)

    def test_real_caller_argument_change_invalidates_review_and_operation_contracts(self):
        import operation_inventory
        inventory = operation_inventory.discover_operations(self.root, WORKFLOW, self.graph)
        contracts = operations.make_contracts(inventory, self.graph, self.review)
        for binding in contracts["bindings"]:
            binding["review_status"] = "reviewed"
        self.write(WORKFLOW, (self.root / WORKFLOW).read_text().replace("--mode strict", "--mode changed"))
        graph = caller_inventory.discover_callers(self.root, WORKFLOW)
        changed = operation_inventory.discover_operations(self.root, WORKFLOW, graph)
        self.assertNotEqual(graph["graph_digest"], self.graph["graph_digest"])
        self.assert_blocked(inventory=changed, graph=graph, contracts=contracts)
        reviewed = copy.deepcopy(self.review)
        reviewed["graph_digest"] = graph["graph_digest"]
        reviewed["edge_ids"] = sorted(item["id"] for item in graph["edges"])
        self.assertEqual(caller_coverage.compile_callers(graph, reviewed)["accounting_verdict"], "accounted")
        self.assert_blocked(inventory=changed, graph=graph, review=reviewed, contracts=contracts)

    def test_real_build_input_byte_change_requires_contract_review_again(self):
        import operation_inventory
        inventory = operation_inventory.discover_operations(self.root, WORKFLOW, self.graph)
        contracts = operations.make_contracts(inventory, self.graph, self.review)
        for binding in contracts["bindings"]:
            binding["review_status"] = "reviewed"
        self.write("apps/sample/src/input.ts", "export const value = 'changed build input';\n")
        changed = operation_inventory.discover_operations(self.root, WORKFLOW, self.graph)
        self.assertNotEqual(inventory["inventory_digest"], changed["inventory_digest"])
        self.assert_blocked(inventory=changed, contracts=contracts)

    def test_open_wrong_version_and_referenced_schemas_fail_closed(self):
        schema = release.load_document(operations.SCHEMA_DIR / "source-operation-inventory.schema.yml")
        for mode in ("open", "version", "ref", "dynamic", "recursive", "optional", "untyped", "bad-required", "bad-properties"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix="operation-schema-") as directory:
                changed = copy.deepcopy(schema)
                if mode == "open":
                    changed["properties"]["subjects"]["items"]["additionalProperties"] = True
                elif mode == "version":
                    changed["$id"] = "urn:release-control:source-operation-inventory:v99"
                elif mode == "optional":
                    changed["required"].remove("subjects")
                elif mode == "untyped":
                    del changed["properties"]["subjects"]["items"]["type"]
                elif mode == "bad-required":
                    changed["required"] = [{}]
                elif mode == "bad-properties":
                    changed["properties"] = []
                else:
                    changed[{"ref": "$ref", "dynamic": "$dynamicRef", "recursive": "$recursiveRef"}[mode]] = "https://example.invalid/schema"
                (Path(directory) / "source-operation-inventory.schema.yml").write_text(json.dumps(changed))
                with patch.object(operations, "SCHEMA_DIR", Path(directory)):
                    self.assert_blocked()


if __name__ == "__main__":
    unittest.main()
