#!/usr/bin/env python3
"""Reject finding intake omissions, stale bindings and false coverage claims."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-finding-triage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove finding classification completeness and preserve independent coverage blockers.
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
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import finding_triage as triage
import source_coverage as coverage
import release_compiler as release
from test_source_coverage import fixture_composition

SENTINEL = "SENSITIVE-MARKER-DO-NOT-ECHO"
CHANGED_DIGEST = "sha256:" + "e" * 64


class FindingTriageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="release-finding-triage-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "source"
        shutil.copytree(DIRECTORY / "fixtures/source-coverage", self.root)
        self.package_path = self.root / "package.json"
        self.package_path.write_text(json.dumps({"name": "fixture", "scripts": {"deploy": "echo " + SENTINEL}}))
        self.tasks_path = self.root / "infra/04.deploy/tasks.json"
        tasks = json.loads(self.tasks_path.read_text())
        del tasks["Resources"]["QueryAndLoadTask"]["Properties"]["ContainerDefinitions"][0]["Command"]
        self.tasks_path.write_text(json.dumps(tasks))
        self.inventory = coverage.discover(self.root)
        self.document = triage.make_triage(self.inventory)

    def compile(self, document=None, inventory=None):
        return triage.compile_triage(self.inventory if inventory is None else inventory,
                                     self.document if document is None else document)

    def assert_incomplete(self, document, code, inventory=None):
        result = self.compile(document, inventory)
        self.assertEqual("incomplete", result["classification_verdict"])
        self.assertEqual("blocked", result["coverage_verdict"])
        self.assertIs(False, result["authorized"])
        self.assertIn(code, {item["code"] for item in result["findings"]})
        self.assertNotIn(SENTINEL, json.dumps(result))
        return result

    @staticmethod
    def rehash(inventory):
        inventory["inventory_digest"] = release.digest_document({key: value for key, value in inventory.items()
                                                                if key != "inventory_digest"})

    def test_complete_deterministic_intake_remains_open_and_blocked(self):
        self.assertEqual(self.document, triage.make_triage(self.inventory))
        self.assertEqual({"open"}, {entry["status"] for entry in self.document["entries"]})
        self.assertEqual({"release-control-programme"}, {entry["intake_owner"] for entry in self.document["entries"]})
        result = self.compile()
        self.assertEqual("complete", result["classification_verdict"])
        self.assertEqual("blocked", result["coverage_verdict"])
        self.assertEqual({"phase-2-source": 1, "phase-3-artifact": 1, "phase-5-provider": 0}, result["counts"]["by_route"])
        self.assertEqual(2, result["counts"]["source_findings"])
        self.assertEqual(2, result["counts"]["classified_findings"])
        self.assertIs(False, result["authorized"])
        self.assertEqual([], result["findings"])
        self.assertNotIn(SENTINEL, json.dumps([self.document, result]))

    def test_no_findings_is_scoped_clearance_without_authority(self):
        self.package_path.write_text('{"name":"fixture"}')
        shutil.copyfile(DIRECTORY / "fixtures/source-coverage/infra/04.deploy/tasks.json", self.tasks_path)
        inventory = coverage.discover(self.root)
        result = self.compile(triage.make_triage(inventory), inventory)
        self.assertEqual("complete", result["classification_verdict"])
        self.assertEqual("clear-source-findings", result["coverage_verdict"])
        self.assertEqual(0, result["counts"]["entries"])
        self.assertIs(False, result["authorized"])

    def test_missing_finding_is_incomplete(self):
        self.document["entries"].pop()
        self.assert_incomplete(self.document, "triage-finding-missing")

    def test_duplicate_identity_with_different_owner_is_incomplete(self):
        duplicate = deepcopy(self.document["entries"][0])
        duplicate["intake_owner"] = "another-intake-team"
        self.document["entries"].append(duplicate)
        result = self.assert_incomplete(self.document, "triage-finding-duplicate")
        self.assertEqual(1, result["counts"]["classified_findings"])

    def test_unknown_finding_cannot_replace_a_current_finding(self):
        self.document["entries"][0]["code"] = "invented-finding"
        result = self.assert_incomplete(self.document, "triage-finding-unknown")
        self.assertIn("triage-finding-missing", {item["code"] for item in result["findings"]})

    def test_unknown_source_cannot_replace_a_current_source(self):
        self.document["entries"][0]["source_id"] = CHANGED_DIGEST
        self.assert_incomplete(self.document, "triage-finding-unknown")

    def test_stale_document_bindings_are_incomplete(self):
        for field, code in (("inventory_digest", "triage-inventory-stale"),
                            ("collector_revision", "triage-collector-stale"),
                            ("policy_revision", "triage-policy-stale")):
            with self.subTest(field=field):
                document = deepcopy(self.document)
                document[field] = CHANGED_DIGEST
                self.assert_incomplete(document, code)

    def test_source_bytes_change_invalidates_intake(self):
        self.package_path.write_text('{"name":"fixture","scripts":{"deploy":"echo changed"}}')
        result = self.assert_incomplete(self.document, "triage-source-stale", coverage.discover(self.root))
        self.assertIn("triage-inventory-stale", {item["code"] for item in result["findings"]})

    def test_inventory_digest_cannot_be_forged(self):
        inventory = deepcopy(self.inventory)
        inventory["inventory_digest"] = CHANGED_DIGEST
        with self.assertRaisesRegex(coverage.CoverageFailure, "inventory-digest-invalid"):
            self.compile(inventory=inventory)

    def test_observation_issues_cannot_be_omitted_from_triage(self):
        inventory = deepcopy(self.inventory)
        inventory["findings"] = []
        self.rehash(inventory)
        document = triage.make_triage(inventory)
        self.assertEqual(2, len(document["entries"]))
        self.assertEqual("complete", self.compile(document, inventory)["classification_verdict"])

    def test_multiple_observations_count_as_one_source_code_pair(self):
        self.package_path.write_text(json.dumps({"name": "fixture", "scripts": {"one": "echo one", "two": "echo two"}}))
        inventory = coverage.discover(self.root)
        result = self.compile(triage.make_triage(inventory), inventory)
        self.assertEqual(2, result["counts"]["source_findings"])

    def test_unrecognized_diagnostic_needs_policy_work(self):
        inventory = deepcopy(self.inventory)
        inventory["findings"].append({"source_id": inventory["sources"][0]["id"], "code": "new-source-grammar"})
        self.rehash(inventory)
        document = triage.make_triage(inventory)
        entry = next(item for item in document["entries"] if item["code"] == "new-source-grammar")
        self.assertEqual(("phase-2-source", "investigate-source-grammar"), (entry["route"], entry["next_action"]))
        self.assert_incomplete(document, "triage-code-policy-unsupported", inventory)

    def test_source_work_cannot_be_deferred_to_provider_phase(self):
        entry = next(item for item in self.document["entries"] if item["code"] == "opaque-executable")
        entry["route"] = "phase-5-provider"
        self.assert_incomplete(self.document, "triage-route-policy-mismatch")

    def test_action_must_match_the_source_diagnostic(self):
        self.document["entries"][0]["next_action"] = "investigate-source-grammar"
        self.assert_incomplete(self.document, "triage-route-policy-mismatch")

    def test_policy_change_invalidates_existing_intake(self):
        with patch.dict(triage.POLICY, {"opaque-executable": ("phase-2-source", "investigate-source-grammar")}):
            self.assert_incomplete(self.document, "triage-policy-stale")

    def test_missing_owner_unsafe_fields_and_resolution_claims_are_rejected(self):
        for key, value in (("intake_owner", "https://" + SENTINEL), ("status", "resolved"),
                           ("command", SENTINEL), ("evidence", SENTINEL)):
            with self.subTest(key=key):
                document = deepcopy(self.document)
                document["entries"][0][key] = value
                with self.assertRaises(coverage.CoverageFailure) as failure:
                    self.compile(document)
                self.assertNotIn(SENTINEL, str(failure.exception))
        del self.document["entries"][0]["intake_owner"]
        with self.assertRaises(coverage.CoverageFailure):
            self.compile()

    def test_wrong_schema_version_is_rejected(self):
        self.document["schema"] = "source-finding-triage/v2"
        with self.assertRaisesRegex(coverage.CoverageFailure, "source-finding-triage-invalid"):
            self.compile()

    def test_alias_and_control_characters_are_rejected_before_validation(self):
        self.document["entries"].append(self.document["entries"][0])
        with self.assertRaisesRegex(release.ReleaseFailure, "document-alias-unsupported"):
            self.compile()
        self.document["entries"].pop()
        self.document["entries"][0]["intake_owner"] = "unsafe\n" + SENTINEL
        with self.assertRaisesRegex(release.ReleaseFailure, "document-string-invalid"):
            self.compile()

    def test_unknown_inventory_references_are_rejected(self):
        inventory = deepcopy(self.inventory)
        inventory["findings"][0]["source_id"] = CHANGED_DIGEST
        self.rehash(inventory)
        with self.assertRaisesRegex(coverage.CoverageFailure, "triage-inventory-reference-invalid"):
            triage.make_triage(inventory)

    def test_complete_triage_does_not_suppress_original_coverage_findings(self):
        self.package_path.write_text('{"name":"fixture"}')
        inventory = coverage.discover(self.root)
        composition = fixture_composition(inventory)
        ledger = coverage.make_ledger(inventory)
        for entry in ledger["entries"]:
            entry["review_status"] = "reviewed"
        before = coverage.compile_coverage(inventory, composition, ledger, as_of="2026-09-29")
        original_inventory = deepcopy(inventory)
        result = self.compile(triage.make_triage(inventory), inventory)
        after = coverage.compile_coverage(inventory, composition, ledger, as_of="2026-09-29")
        self.assertEqual(original_inventory, inventory)
        self.assertEqual("complete", result["classification_verdict"])
        self.assertEqual(before, after)
        self.assertEqual("blocked", after["verdict"])
        self.assertEqual({"container-command-inherited"}, {item["code"] for item in after["findings"]})
        self.assertIs(False, after["authorized"])

    def cli(self, *arguments):
        result = subprocess.run(["bash", str(DIRECTORY / "script.sh"), "--triage", "--source-root", str(self.root),
                                 *arguments], cwd=DIRECTORY.parents[2], capture_output=True, text=True, check=False)
        self.assertEqual("", result.stderr)
        self.assertNotIn(SENTINEL, result.stdout)
        return result.returncode, json.loads(result.stdout)

    def test_cli_generates_open_intake_and_accepts_complete_classification_only(self):
        status, document = self.cli()
        self.assertEqual(1, status)
        self.assertEqual(self.document, document)
        self.assertEqual({"open"}, {item["status"] for item in document["entries"]})
        path = self.root.parent / "intake.json"
        path.write_text(json.dumps(document))
        status, result = self.cli("--finding-triage", str(path))
        self.assertEqual(0, status)
        self.assertEqual("complete", result["classification_verdict"])
        self.assertEqual("blocked", result["coverage_verdict"])
        self.assertIs(False, result["authorized"])

    def test_cli_recollects_source_and_rejects_stale_intake(self):
        path = self.root.parent / "intake.json"
        path.write_text(json.dumps(self.document))
        self.package_path.write_text('{"name":"fixture","scripts":{"deploy":"echo changed"}}')
        status, result = self.cli("--finding-triage", str(path))
        self.assertEqual(1, status)
        self.assertEqual("incomplete", result["classification_verdict"])
        self.assertIn("triage-inventory-stale", {item["code"] for item in result["findings"]})
        self.assertIs(False, result["authorized"])

    def test_cli_rejects_mixed_modes_and_unsafe_fields_without_echo(self):
        status, result = self.cli("--composition", SENTINEL)
        self.assertEqual(1, status)
        self.assertEqual([{ "code": "arguments-invalid"}], result["findings"])
        document = deepcopy(self.document)
        document["entries"][0]["command"] = SENTINEL
        path = self.root.parent / "unsafe.json"
        path.write_text(json.dumps(document))
        status, result = self.cli("--finding-triage", str(path))
        self.assertEqual(1, status)
        self.assertEqual([{ "code": "source-finding-triage-invalid"}], result["findings"])
        self.assertIs(False, result["authorized"])


if __name__ == "__main__":
    unittest.main()
