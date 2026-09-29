#!/usr/bin/env python3
"""Exercise result consumption through the actual public command."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-result-consumption-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove source results require fresh recomputation and cannot become release authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import copy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
sys.path.insert(0, str(DIRECTORY))
import source_coverage
import finding_triage
import result_consumption_cli as cli
import caller_coverage
import caller_inventory
from test_source_coverage import fixture_composition

SENTINEL = "SENTINEL-SENSITIVE-DO-NOT-PRINT"


class ResultConsumptionCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="source-result-consumer-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / "source"
        self.source.mkdir()
        (self.source / "package.json").write_text('{"name":"consumer-fixture","private":true}')
        self.script = self.source / "scripts/04.deploy/task.py"
        self.script.parent.mkdir(parents=True)
        self.script.write_text("print('fixture')\n")
        inventory = source_coverage.discover(self.source)
        triage = finding_triage.make_triage(inventory)
        self.triage_path = self.base / "triage.json"
        self.triage_path.write_text(json.dumps(triage))
        self.result = finding_triage.compile_triage(inventory, triage)
        self.result_path = self.base / "result.json"
        self.result_path.write_text(json.dumps(self.result))
        self.producer = ["--triage", "--source-root", str(self.source),
                         "--finding-triage", str(self.triage_path)]

    def command(self, arguments):
        return subprocess.run(["bash", str(DIRECTORY / "script.sh"), *arguments],
                              cwd=ROOT, capture_output=True, text=True, check=False)

    def consume(self, purpose="source-analysis", producer=None):
        return self.command(["--consume-result", str(self.result_path), "--purpose", purpose,
                             "--", *(self.producer if producer is None else producer)])

    def assert_decision(self, result, accepted=False):
        self.assertEqual(result.returncode, 0 if accepted else 1, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertNotIn(SENTINEL, result.stdout)
        self.assertNotIn("Traceback", result.stdout)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["schema"], "source-result-consumption/v1")
        self.assertEqual(decision["verdict"], "accepted" if accepted else "rejected")
        self.assertIs(decision["authorized"], False)
        self.assertEqual(decision["release_eligibility"], "blocked")
        self.assertEqual(decision["operation_authorization"], "blocked")
        return decision

    def test_exit_zero_triage_can_be_consumed_as_fresh_analysis(self):
        original = self.command(self.producer)
        self.assertEqual(original.returncode, 0)
        self.assertEqual(json.loads(original.stdout)["coverage_verdict"], "blocked")
        self.assert_decision(self.consume(), accepted=True)

    def test_exit_zero_triage_cannot_be_used_as_authority(self):
        for purpose in ("release-eligibility", "operation-authorization"):
            with self.subTest(purpose=purpose):
                self.assert_decision(self.consume(purpose))

    def test_authority_rejection_does_not_recompute_or_read_input(self):
        load_document = cli.release.load_document

        def only_contract(path, *args, **kwargs):
            self.assertEqual(Path(path), cli.consumption.SCHEMA_DIR / cli.consumption.SCHEMA_FILE)
            return load_document(path, *args, **kwargs)

        output = StringIO()
        with patch.object(cli, "recompute", side_effect=AssertionError("must not run")), \
             patch.object(cli.release, "load_document", side_effect=only_contract) as reads, \
             redirect_stdout(output):
            self.assertEqual(cli.main(["--consume-result", SENTINEL, "--purpose",
                                      "operation-authorization", "--", "--triage"]), 1)
        self.assertEqual(reads.call_count, 1)
        decision = json.loads(output.getvalue())
        self.assertEqual(decision["findings"], [{"code": "source-result-authority-unavailable"}])
        self.assertEqual(decision["verdict"], "rejected")
        self.assertIs(decision["authorized"], False)
        self.assertIn("contract_digest", decision)
        self.assertNotIn(SENTINEL, output.getvalue())

    def test_successful_coverage_can_be_consumed_only_as_current_analysis(self):
        source = self.base / "coverage-source"
        shutil.copytree(DIRECTORY / "fixtures/source-coverage", source)
        inventory = source_coverage.discover(source)
        composition = fixture_composition(inventory)
        ledger = source_coverage.make_ledger(inventory)
        for entry in ledger["entries"]:
            entry["review_status"] = "reviewed"
        composition_path = self.base / "composition.json"
        ledger_path = self.base / "ledger.json"
        composition_path.write_text(json.dumps(composition))
        ledger_path.write_text(json.dumps(ledger))
        producer = ["--coverage", "--source-root", str(source), "--composition", str(composition_path),
                    "--adoption-ledger", str(ledger_path)]
        original = self.command(producer)
        self.assertEqual(original.returncode, 0, original.stdout + original.stderr)
        self.assertEqual(json.loads(original.stdout)["verdict"], "covered")
        self.result_path.write_text(original.stdout)
        decision = self.assert_decision(self.consume(producer=producer), accepted=True)
        self.assertEqual(decision["source_result"]["scope"], "source-coverage")
        self.assert_decision(self.consume("operation-authorization", producer))

    def test_accounted_callers_can_be_consumed_with_qualification_still_blocked(self):
        workflow = ".github/workflows/staging.yml"
        path = self.source / workflow
        path.parent.mkdir(parents=True)
        path.write_text("name: Fixture\non: workflow_dispatch\njobs:\n  inspect:\n"
                        "    runs-on: ubuntu-latest\n    steps:\n"
                        "      - run: python3 scripts/04.deploy/task.py\n")
        graph = caller_inventory.discover_callers(self.source, workflow)
        review = caller_coverage.make_review(graph)
        for binding in review["bindings"]:
            binding["review_status"] = "reviewed"
            binding["operation_profile"] = "inspection"
        review_path = self.base / "caller-review.json"
        review_path.write_text(json.dumps(review))
        producer = ["--callers", "--source-root", str(self.source), "--workflow", workflow,
                    "--caller-review", str(review_path)]
        original = self.command(producer)
        self.assertEqual(original.returncode, 0, original.stdout + original.stderr)
        result = json.loads(original.stdout)
        self.assertEqual(result["accounting_verdict"], "accounted")
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertTrue(result["source_findings"])
        self.result_path.write_text(original.stdout)
        decision = self.assert_decision(self.consume(producer=producer), accepted=True)
        self.assertEqual(decision["source_result"]["scope"], "caller-accounting")
        self.assert_decision(self.consume("release-eligibility", producer))

    def test_changed_source_invalidates_saved_analysis(self):
        self.script.write_text("print('changed-source')\n")
        self.assert_decision(self.consume())

    def test_incomplete_current_review_invalidates_saved_analysis(self):
        review = json.loads(self.triage_path.read_text())
        review["entries"].pop()
        self.triage_path.write_text(json.dumps(review))
        self.assert_decision(self.consume())

    def test_unavailable_contract_never_claims_acceptance(self):
        with patch.object(cli.consumption, "load_contract", side_effect=ValueError(SENTINEL)):
            decision = cli.reject_safely("arguments-invalid", "source-analysis")
        self.assertEqual(decision["verdict"], "rejected")
        self.assertIs(decision["authorized"], False)
        self.assertNotIn("contract_digest", decision)
        self.assertNotIn(SENTINEL, json.dumps(decision))

    def test_forged_success_and_unsafe_fields_are_rejected(self):
        for mutation in ({"authorized": True}, {"coverage_verdict": "clear-source-findings"},
                         {"token": SENTINEL}, {"schema": "source-triage-result/v2"}):
            forged = copy.deepcopy(self.result)
            forged.update(mutation)
            self.result_path.write_text(json.dumps(forged))
            with self.subTest(fields=list(mutation)):
                self.assert_decision(self.consume())

    def test_strict_saved_document_loading_never_echoes_input(self):
        for data in ('{"schema":"a","schema":"b","token":"' + SENTINEL + '"}',
                     "value: &alias " + SENTINEL + "\ncopy: *alias\n"):
            self.result_path.write_text(data)
            self.assert_decision(self.consume())

    def test_templates_and_legacy_runtime_are_not_analysis_receipts(self):
        for producer in (["--discover", "--source-root", str(self.source)],
                         ["--triage", "--source-root", str(self.source)],
                         ["--callers", "--source-root", str(self.source), "--review-template"],
                         ["--contract", str(DIRECTORY / "fixtures/valid-contract.yml"),
                          "--validate-contract"]):
            with self.subTest(mode=producer[0]):
                self.assert_decision(self.consume(producer=producer))

    def test_arguments_cannot_supply_expected_result_or_replace_purpose(self):
        base = ["--consume-result", str(self.result_path), "--purpose", "source-analysis"]
        for args in (base,
                     base + ["--expected-result", str(self.result_path), "--", *self.producer],
                     base + ["--purpose", "source-analysis", "--", *self.producer],
                     base + ["--", "--consume-result", str(self.result_path)],
                     base + ["--", *self.producer, "--", SENTINEL],
                     ["--consume-result", str(self.result_path), "--purpose", SENTINEL,
                      "--", *self.producer]):
            with self.subTest(arguments=len(args)):
                self.assert_decision(self.command(args))

    def test_ordinary_release_compilation_keeps_interface_and_guard(self):
        producer = ["--release", str(DIRECTORY / "fixtures/valid-release.yml"),
                    "--contract", str(DIRECTORY / "fixtures/valid-contract.yml")]
        original = self.command(producer)
        self.assertEqual(original.returncode, 0)
        self.assertEqual(json.loads(original.stdout)["verdict"], "compiled")
        self.result_path.write_text(original.stdout)
        self.assert_decision(self.consume(producer=producer), accepted=True)
        self.assert_decision(self.consume("release-eligibility", producer))


if __name__ == "__main__":
    unittest.main()
