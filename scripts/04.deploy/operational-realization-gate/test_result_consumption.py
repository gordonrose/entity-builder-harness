#!/usr/bin/env python3
"""Source success never conveys qualification or operation authorization."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-result-consumption
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify recomputed source-result consumption, malformed snapshots and authority rejection.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import result_consumption as consumption
import release_compiler as release
import source_coverage as coverage
import estate_caller_coverage as estate
import finding_triage as triage
import caller_coverage as callers
import caller_inventory
from test_source_coverage import fixture_composition

SENTINEL = "SENSITIVE-INPUT-NEVER-ECHO"
CHANGED = "sha256:" + "a" * 64


class ResultConsumptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="release-result-consumption-")
        cls.addClassCleanup(temporary.cleanup)
        root = Path(temporary.name) / "source"
        shutil.copytree(DIRECTORY / "fixtures/source-coverage", root)
        inventory = coverage.discover(root)
        ledger = coverage.make_ledger(inventory)
        for entry in ledger["entries"]:
            entry["review_status"] = "reviewed"
        cls.results = {
            "release": release.compile_release(
                release.load_document(DIRECTORY / "fixtures/valid-release.yml"),
                release.load_document(DIRECTORY / "fixtures/valid-contract.yml")),
            "coverage": coverage.compile_coverage(inventory, fixture_composition(inventory), ledger,
                                                  as_of="2026-09-29"),
        }
        cls.results["coverage-estate"] = coverage.compile_coverage(
            inventory, fixture_composition(inventory), ledger, as_of="2026-09-29", source_root=root)
        estate_root = Path(temporary.name) / "estate-source"
        estate_root.mkdir()
        (estate_root / "package.json").write_text('{"name":"estate-fixture"}')
        cls.results["estate"] = estate.reconcile_estate(estate_root)
        (root / "package.json").write_text(json.dumps({
            "name": "fixture", "scripts": {"deploy": "bash scripts/04.deploy/deploy.sh"},
        }))
        scripts = root / "scripts/04.deploy"
        scripts.mkdir(parents=True)
        (scripts / "deploy.sh").write_text("#!/usr/bin/env bash\necho synthetic\n")
        workflows = root / ".github/workflows"
        workflows.mkdir(parents=True)
        (workflows / "staging.yml").write_text(
            "name: Fixture\non: workflow_dispatch\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: npm run deploy\n")
        inventory = coverage.discover(root)
        cls.results["triage"] = triage.compile_triage(inventory, triage.make_triage(inventory))
        graph = caller_inventory.discover_callers(root, ".github/workflows/staging.yml")
        review = callers.make_review(graph)
        for binding in review["bindings"]:
            binding["review_status"] = "reviewed"
            binding["operation_profile"] = "inspection"
        cls.results["callers"] = callers.compile_callers(graph, review)
        cls.schema = consumption.load_contract()

    def consume(self, name="release", result=None, purpose="source-analysis", expected=None):
        original = self.results[name]
        return consumption.consume_result(
            deepcopy(original) if result is None else result, purpose,
            expected_result=deepcopy(original) if expected is None else expected)

    def assert_rejected(self, decision, code=None):
        self.assertEqual("rejected", decision["verdict"])
        self.assertIs(False, decision["authorized"])
        self.assertEqual("blocked", decision["release_eligibility"])
        self.assertEqual("blocked", decision["operation_authorization"])
        self.assertNotIn("source_result", decision)
        self.assertNotIn("source_result_digest", decision)
        self.assertNotIn(SENTINEL, json.dumps(decision))
        self.assertTrue(decision["findings"])
        if code:
            self.assertEqual([{"code": code}], decision["findings"])
        Draft202012Validator(self.schema).validate(decision)

    def test_all_real_producer_successes_are_source_only(self):
        for name in self.results:
            with self.subTest(producer=name):
                decision = self.consume(name)
                self.assertEqual("accepted", decision["verdict"], decision)
                self.assertIs(False, decision["authorized"])
                self.assertEqual("blocked", decision["release_eligibility"])
                self.assertEqual("blocked", decision["operation_authorization"])
                self.assertEqual("not-established", decision["source_result"]["qualification_status"])
                self.assertEqual(release.digest_document(self.results[name]), decision["source_result_digest"])
                self.assertEqual([], decision["findings"])
                Draft202012Validator(self.schema).validate(decision)

    def test_complete_triage_preserves_its_blocked_coverage(self):
        self.assertEqual("complete", self.results["triage"]["classification_verdict"])
        self.assertEqual("blocked", self.results["triage"]["coverage_verdict"])
        self.assertGreater(self.results["triage"]["counts"]["source_findings"], 0)
        self.assertEqual("accepted", self.consume("triage")["verdict"])
        self.assert_rejected(self.consume("triage", purpose="release-eligibility"),
                             "source-result-authority-unavailable")

    def test_accounted_callers_preserve_blocked_qualification(self):
        self.assertEqual("accounted", self.results["callers"]["accounting_verdict"])
        self.assertEqual("blocked", self.results["callers"]["qualification_verdict"])
        self.assertTrue(self.results["callers"]["source_findings"])
        self.assert_rejected(self.consume("callers", purpose="operation-authorization"),
                             "source-result-authority-unavailable")

    def test_all_authority_purposes_reject_every_producer(self):
        for purpose in ("release-eligibility", "operation-authorization"):
            for name in self.results:
                with self.subTest(purpose=purpose, producer=name):
                    self.assert_rejected(self.consume(name, purpose=purpose),
                                         "source-result-authority-unavailable")

    def test_unknown_or_unsafe_purpose_is_never_echoed(self):
        for purpose in (SENTINEL, "", None, [], {}):
            with self.subTest(purpose=type(purpose).__name__):
                self.assert_rejected(self.consume(purpose=purpose), "source-result-purpose-unsupported")

    def test_snapshot_alone_never_establishes_source_success(self):
        for name, result in self.results.items():
            with self.subTest(producer=name):
                self.assert_rejected(consumption.consume_result(result, "source-analysis"),
                                     "source-result-recomputation-required")

    def test_exact_canonical_match_accepts_json_key_reordering(self):
        result = self.results["release"]
        reordered = {key: deepcopy(result[key]) for key in reversed(list(result))}
        self.assertEqual("accepted", self.consume(result=reordered)["verdict"])

    def test_consumer_does_not_mutate_producer_result(self):
        result = deepcopy(self.results["release"])
        before = deepcopy(result)
        consumption.consume_result(result, "source-analysis", expected_result=deepcopy(result))
        self.assertEqual(before, result)

    def test_authority_field_must_exist_and_be_boolean_false(self):
        for name in self.results:
            for value in (True, 0, None, "false"):
                with self.subTest(producer=name, value=repr(value)):
                    result = deepcopy(self.results[name])
                    result["authorized"] = value
                    self.assert_rejected(self.consume(name, result), "source-result-authority-invalid")
            result = deepcopy(self.results[name])
            del result["authorized"]
            self.assert_rejected(self.consume(name, result), "source-result-authority-invalid")

    def test_unknown_schema_version_and_wrong_scope_reject(self):
        for field, value, code in (
                ("schema", "release-control-result/v2", "source-result-producer-unsupported"),
                ("schema", SENTINEL, "source-result-producer-unsupported"),
                ("schema", [], "source-result-producer-unsupported"),
                ("scope", "operation-authorization", "source-result-invalid"),
                ("scope", SENTINEL, "source-result-invalid")):
            result = deepcopy(self.results["release"])
            result[field] = value
            self.assert_rejected(self.consume(result=result), code)

    def test_unknown_top_level_fields_cannot_be_smuggled(self):
        result = deepcopy(self.results["release"])
        result["credentials"] = SENTINEL
        self.assert_rejected(self.consume(result=result), "source-result-invalid")

    def test_nested_snapshot_mutation_is_rejected_without_echo(self):
        result = deepcopy(self.results["release"])
        result["acceptance_matrix"][0]["owner"] = SENTINEL
        self.assert_rejected(self.consume(result=result), "source-result-snapshot-mismatch")

    def test_changed_source_digest_invalidates_saved_result(self):
        for name, field in (("release", "release_digest"), ("coverage", "inventory_digest"),
                            ("triage", "inventory_digest"), ("callers", "graph_digest")):
            with self.subTest(producer=name):
                expected = deepcopy(self.results[name])
                expected[field] = CHANGED
                self.assert_rejected(self.consume(name, expected=expected), "source-result-snapshot-mismatch")

    def test_missing_required_producer_field_is_malformed(self):
        for name, field in (("release", "operation_graph"), ("coverage", "coverage_digest"),
                            ("triage", "counts"), ("callers", "accounting_digest")):
            result = deepcopy(self.results[name])
            del result[field]
            self.assert_rejected(self.consume(name, result), "source-result-invalid")

    def test_blocked_and_failed_analysis_cannot_be_consumed_as_success(self):
        for name, field, value in (("release", "verdict", "failed"),
                                    ("coverage", "verdict", "blocked"),
                                    ("triage", "classification_verdict", "incomplete"),
                                    ("callers", "accounting_verdict", "incomplete")):
            result = deepcopy(self.results[name])
            result[field] = value
            self.assert_rejected(self.consume(name, result), "source-result-analysis-unsuccessful")

    def test_forged_success_cannot_override_fresh_failure(self):
        expected = deepcopy(self.results["triage"])
        expected["classification_verdict"] = "incomplete"
        expected["findings"] = [{"code": "triage-finding-missing"}]
        self.assert_rejected(self.consume("triage", expected=expected), "source-result-recomputation-invalid")

    def test_forged_passed_release_rows_are_rejected(self):
        result = deepcopy(self.results["release"])
        result["acceptance_matrix"][0]["verdict"] = "passed"
        self.assert_rejected(self.consume(result=result), "source-result-invalid")

    def test_missing_or_out_of_order_stages_are_rejected(self):
        for name, rows in (("release", "acceptance_matrix"), ("coverage", "acceptance_obligations")):
            for mutation in ("missing", "reordered", "boolean-stage"):
                result = deepcopy(self.results[name])
                if mutation == "missing":
                    result[rows].pop()
                elif mutation == "reordered":
                    result[rows].reverse()
                else:
                    result[rows][0]["stage"] = True
                self.assert_rejected(self.consume(name, result), "source-result-invalid")

    def test_false_caller_qualification_is_rejected(self):
        result = deepcopy(self.results["callers"])
        result["qualification_verdict"] = "qualified"
        self.assert_rejected(self.consume("callers", result), "source-result-invalid")
        result = deepcopy(self.results["callers"])
        result["obligations"][0]["qualification"] = "qualified"
        self.assert_rejected(self.consume("callers", result), "source-result-invalid")

    def test_false_clear_triage_coverage_is_rejected(self):
        result = deepcopy(self.results["triage"])
        result["coverage_verdict"] = "clear-source-findings"
        self.assert_rejected(self.consume("triage", result), "source-result-invalid")

    def test_coverage_cannot_embed_an_authorized_release(self):
        result = deepcopy(self.results["coverage"])
        result["compiled_release"] = deepcopy(self.results["release"])
        result["compiled_release"]["authorized"] = True
        self.assert_rejected(self.consume("coverage", result), "source-result-authority-invalid")

    def test_cyclic_oversized_non_json_and_unsafe_values_fail_safely(self):
        cyclic = {}
        cyclic["loop"] = cyclic
        for result in (cyclic, "x" * 16385, {"bad": float("nan")}, None, [], {"bad": SENTINEL + "\n"}):
            with self.subTest(kind=type(result).__name__):
                self.assert_rejected(self.consume(result=result if result is not None else {"bad": None}))

    def test_nonboolean_zero_authority_does_not_match_false(self):
        result = deepcopy(self.results["callers"])
        result["authorized"] = 0
        self.assert_rejected(self.consume("callers", result), "source-result-authority-invalid")

    def test_null_result_rejects_without_raw_input(self):
        self.assert_rejected(consumption.consume_result(None, "source-analysis", self.results["release"]),
                             "source-result-invalid")

    def test_public_wrapper_rejections_are_closed_and_safe(self):
        for code in ("arguments-invalid", "source-result-unreadable", "producer-recompute-failed"):
            self.assert_rejected(consumption.reject_result(code), code)
        self.assert_rejected(consumption.reject_result(SENTINEL), "source-result-invalid")

    def test_contract_rejects_authority_malformed_output_and_unknown_fields(self):
        valid = self.consume("triage")
        for field, value in (("authorized", True), ("release_eligibility", "eligible"),
                             ("operation_authorization", "authorized"), ("unexpected", SENTINEL)):
            altered = deepcopy(valid)
            altered[field] = value
            self.assertTrue(list(Draft202012Validator(self.schema).iter_errors(altered)))
        altered = deepcopy(valid)
        del altered["authorized"]
        self.assertTrue(list(Draft202012Validator(self.schema).iter_errors(altered)))

    def test_contract_binds_acceptance_to_source_analysis(self):
        valid = self.consume()
        valid["purpose"] = "release-eligibility"
        self.assertTrue(list(Draft202012Validator(self.schema).iter_errors(valid)))

    def test_contract_binds_producer_scope_and_success_vocabulary(self):
        valid = self.consume("triage")
        valid["source_result"]["scope"] = "release-definition"
        self.assertTrue(list(Draft202012Validator(self.schema).iter_errors(valid)))

    def test_contract_requires_digest_and_summary_for_acceptance(self):
        valid = self.consume()
        for field in ("source_result", "source_result_digest"):
            altered = deepcopy(valid)
            del altered[field]
            self.assertTrue(list(Draft202012Validator(self.schema).iter_errors(altered)))

    def test_estate_success_retains_every_authority_boundary(self):
        result = self.results["estate"]
        self.assertEqual(result["structural_verdict"], "accounted")
        self.assertEqual(result["remaining_source_findings"], [])
        self.assertEqual(result["boundary_findings"], [])
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertEqual(result["review_verdict"], "not-evaluated")
        self.assertNotIn("findings", result)
        self.assertEqual(self.consume("estate")["source_result"]["scope"], "structural-caller-reconciliation")

    def test_blocked_estate_is_not_consumable(self):
        result = deepcopy(self.results["estate"])
        result["structural_verdict"] = "blocked"
        self.assert_rejected(self.consume("estate", result), "source-result-analysis-unsuccessful")

    def test_estate_closed_contract_rejects_nested_and_authority_mutations(self):
        for field, value in (("roots", True), ("qualification_verdict", "qualified"),
                             ("review_verdict", "reviewed"), ("release_eligibility", "eligible"),
                             ("operation_authorization", "authorized"), ("findings", []),
                             ("boundary_findings", [{"code": "unknown-tool-boundary", "subject_id": CHANGED}]),
                             ("remaining_source_findings", [{"code": "opaque-executable", "source_id": CHANGED}]),
                             ("resolved_observations", [{"observation_id": CHANGED, "node_id": CHANGED,
                                "rule": "literal-package-command/v1", "proof_digest": CHANGED, "secret": SENTINEL}])):
            with self.subTest(field=field):
                result = deepcopy(self.results["estate"])
                result[field] = value
                result["result_digest"] = release.digest_document({k: v for k, v in result.items() if k != "result_digest"})
                self.assert_rejected(self.consume("estate", result), "source-result-invalid")

    def test_estate_checksum_does_not_replace_fresh_recomputation(self):
        result = deepcopy(self.results["estate"])
        result["graph_digest"] = CHANGED
        result["result_digest"] = release.digest_document({k: v for k, v in result.items() if k != "result_digest"})
        self.assert_rejected(self.consume("estate", result), "source-result-snapshot-mismatch")
        self.assert_rejected(consumption.consume_result(result, "source-analysis"), "source-result-recomputation-required")

    def test_estate_wrong_result_digest_is_rejected(self):
        result = deepcopy(self.results["estate"])
        result["result_digest"] = CHANGED
        self.assert_rejected(self.consume("estate", result), "source-result-invalid")

    def test_estate_accounted_verdict_cannot_hide_source_findings(self):
        result = deepcopy(self.results["estate"])
        result["raw_source_findings"] = [{"code": "unsupported-resource", "source_id": CHANGED}]
        result["result_digest"] = release.digest_document({k: v for k, v in result.items() if k != "result_digest"})
        self.assert_rejected(self.consume("estate", result), "source-result-invalid")
        result["resolved_source_findings"] = deepcopy(result["raw_source_findings"])
        result["result_digest"] = release.digest_document({k: v for k, v in result.items() if k != "result_digest"})
        self.assert_rejected(self.consume("estate", result), "source-result-invalid")

    def test_coverage_legacy_and_nested_estate_success_remain_compatible(self):
        self.assertNotIn("caller_reconciliation", self.results["coverage"])
        self.assertIn("caller_reconciliation", self.results["coverage-estate"])
        self.assertEqual(self.consume("coverage")["verdict"], "accepted")
        self.assertEqual(self.consume("coverage-estate")["verdict"], "accepted")

    def test_coverage_nested_estate_requires_same_inventory(self):
        result = deepcopy(self.results["coverage-estate"])
        nested = result["caller_reconciliation"]
        nested["inventory_digest"] = CHANGED
        nested["result_digest"] = release.digest_document({k: v for k, v in nested.items() if k != "result_digest"})
        self.assert_rejected(self.consume("coverage-estate", result), "source-result-invalid")

    def test_coverage_nested_estate_requires_accounted_closed_receipt(self):
        for field, value, code in (("structural_verdict", "blocked", "source-result-analysis-unsuccessful"),
                                   ("authorized", True, "source-result-authority-invalid"),
                                   ("result_digest", CHANGED, "source-result-invalid"),
                                   ("secret", SENTINEL, "source-result-invalid")):
            result = deepcopy(self.results["coverage-estate"])
            result["caller_reconciliation"][field] = value
            self.assert_rejected(self.consume("coverage-estate", result), code)

    def test_proposed_adoption_is_unconsumable_regardless_of_claimed_review(self):
        for verdict in ("pending", "reviewed", "accounted"):
            proposal = {"schema": "source-adoption-migration/v1", "review_verdict": verdict}
            self.assert_rejected(consumption.consume_result(proposal, "source-analysis", proposal),
                                 "source-result-proposal-unconsumable")

    def test_missing_open_or_referenced_estate_schema_is_rejected(self):
        original = release.load_document
        schema_path = consumption.SCHEMA_DIR / "estate-caller-reconciliation.schema.yml"
        for mutation in ("missing", "open", "reference", "weaken-authority"):
            def changed(path, *args, **kwargs):
                document = original(path, *args, **kwargs)
                if Path(path) == schema_path:
                    if mutation == "missing":
                        raise OSError(SENTINEL)
                    if mutation == "open":
                        document["additionalProperties"] = True
                    elif mutation == "reference":
                        document["$ref"] = "https://example.invalid/" + SENTINEL
                    else:
                        document["properties"]["qualification_verdict"] = {"type": "string"}
                return document
            with self.subTest(mutation=mutation), patch.object(release, "load_document", side_effect=changed):
                self.assert_rejected(self.consume("estate"), "source-result-invalid")

    def schema_mutation(self, mutate, expected_code):
        schema = deepcopy(self.schema)
        mutate(schema)
        with tempfile.TemporaryDirectory(prefix="release-consumption-schema-") as directory:
            (Path(directory) / consumption.SCHEMA_FILE).write_text(json.dumps(schema))
            with self.assertRaisesRegex(release.ReleaseFailure, expected_code) as caught:
                consumption.consume_result(self.results["release"], "source-analysis",
                                           self.results["release"], schema_dir=directory)
            self.assertNotIn(SENTINEL, str(caught.exception))

    def test_missing_schema_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="release-consumption-schema-") as directory:
            with self.assertRaisesRegex(release.ReleaseFailure, "consumption-schema-unreadable"):
                consumption.consume_result(self.results["release"], "source-analysis",
                                           self.results["release"], schema_dir=directory)

    def test_changed_schema_version_fails_closed(self):
        self.schema_mutation(lambda doc: doc.update({"$id": "urn:release-control:source-result-consumption:v2"}),
                             "consumption-schema-version-or-authority-invalid")
        self.schema_mutation(lambda doc: doc["properties"]["schema"].update({"const": "source-result-consumption/v2"}),
                             "consumption-schema-version-or-authority-invalid")

    def test_schema_cannot_omit_or_weaken_authority(self):
        self.schema_mutation(lambda doc: doc["required"].remove("authorized"),
                             "consumption-schema-version-or-authority-invalid")
        self.schema_mutation(lambda doc: doc["properties"].pop("authorized"),
                             "consumption-schema-version-or-authority-invalid")
        self.schema_mutation(lambda doc: doc["properties"]["authorized"].update({"const": True}),
                             "consumption-schema-version-or-authority-invalid")

    def test_schema_references_are_never_resolved(self):
        for key in ("$ref", "$dynamicRef", "$recursiveRef"):
            for value in ("https://example.invalid/" + SENTINEL, "#/properties/purpose"):
                self.schema_mutation(lambda doc, key=key, value=value: doc.update({key: value}),
                                     "consumption-schema-reference-unsupported")

    def test_open_schema_objects_fail_closed(self):
        self.schema_mutation(lambda doc: doc.update({"additionalProperties": True}), "consumption-schema-open")
        self.schema_mutation(lambda doc: doc["properties"]["source_result"].update({"additionalProperties": True}),
                             "consumption-schema-open")


if __name__ == "__main__":
    unittest.main()
