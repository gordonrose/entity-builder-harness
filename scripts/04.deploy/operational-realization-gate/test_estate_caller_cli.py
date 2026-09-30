#!/usr/bin/env python3
"""Public estate collection stays read-only and migration stays pending."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-estate-caller-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Test fresh estate command routing, strict safe rejection and pending-only adoption migration.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import builtins
from copy import deepcopy
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import source_coverage as coverage
import release_compiler as release
import estate_caller_cli as cli
import estate_caller_coverage as estate
import adoption_migration

SENTINEL = "SENSITIVE-CLI-INPUT-NEVER-ECHO"


class EstateCallerCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="estate-caller-public-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "source"
        self.root.mkdir()
        (self.root / "package.json").write_text('{"name":"fixture","private":true}')
        self.previous = self.base / "ledger.json"
        self.inventory = coverage.discover(self.root)
        ledger = coverage.make_ledger(self.inventory)
        for entry in ledger["entries"]:
            entry["review_status"] = "reviewed"
            entry["owner"] = "fixture-owner"
        self.previous.write_text(json.dumps(ledger))
        self.estate_args = ["--estate-callers", "--source-root", str(self.root)]
        self.migration_args = ["--adoption-migration", "--source-root", str(self.root),
                               "--previous-adoption-ledger", str(self.previous)]

    def invoke(self, args, public=False):
        if public:
            process = subprocess.run(["bash", str(DIRECTORY / "script.sh"), *args],
                                     cwd=DIRECTORY.parents[2], capture_output=True, text=True, check=False)
            code, output, error = process.returncode, process.stdout, process.stderr
        else:
            output, error = StringIO(), StringIO()
            with redirect_stdout(output), redirect_stderr(error):
                code = cli.main(args)
            output, error = output.getvalue(), error.getvalue()
        self.assertEqual(error, "")
        self.assertNotIn(SENTINEL, output)
        self.assertNotIn("Traceback", output)
        result = json.loads(output)
        self.assertIs(result["authorized"], False)
        self.assertEqual(result["release_eligibility"], "blocked")
        self.assertEqual(result["operation_authorization"], "blocked")
        return code, result

    def assert_error(self, args, code="arguments-invalid", public=False):
        status, result = self.invoke(args, public)
        self.assertEqual(status, 1)
        self.assertEqual(result, cli.reject(code))
        schema = release.load_document(release.SCHEMA_DIR / "estate-caller-error.schema.yml")
        Draft202012Validator(schema).validate(result)

    def test_accounted_fixture_is_source_only(self):
        status, result = self.invoke(self.estate_args)
        self.assertEqual(status, 0)
        self.assertEqual(result["structural_verdict"], "accounted")
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertEqual(result["review_verdict"], "not-evaluated")
        coverage.validate_schema("estate-caller-reconciliation", result)

    def test_existing_public_wrapper_dispatches_estate_mode(self):
        status, result = self.invoke(self.estate_args + ["--json"], public=True)
        self.assertEqual(status, 0)
        self.assertEqual(result["schema"], "estate-caller-reconciliation/v1")
        self.assertEqual(result, estate.reconcile_estate(self.root))

    def test_public_pending_proposal_returns_nonzero(self):
        status, result = self.invoke(self.migration_args + ["--json"], public=True)
        self.assertEqual(status, 1)
        self.assertEqual(result["schema"], "source-adoption-migration/v1")
        self.assertEqual(result["review_verdict"], "pending")
        self.assertTrue(result["candidate"]["entries"])
        self.assertTrue(all(row["review_status"] == "pending" for row in result["candidate"]["entries"]))
        self.assertTrue(all(row["owner"] == "fixture-owner" for row in result["candidate"]["entries"]))
        self.assertIs(result["retirement_authorized"], False)
        self.assertIs(result["deletion_authorized"], False)
        coverage.validate_schema("source-adoption-migration", result)

    def test_pending_proposal_never_rewrites_previous_ledger(self):
        before = self.previous.read_bytes()
        self.invoke(self.migration_args)
        self.assertEqual(self.previous.read_bytes(), before)

    def test_unknown_python_child_stays_blocked_and_is_not_run(self):
        path = self.root / "scripts/04.deploy/task.py"
        path.parent.mkdir(parents=True)
        marker = self.base / "must-not-exist"
        path.write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n")
        (self.root / "package.json").write_text(json.dumps({"scripts": {"probe": "python3 scripts/04.deploy/task.py"}}))
        status, result = self.invoke(self.estate_args)
        self.assertEqual(status, 1)
        self.assertEqual(result["structural_verdict"], "blocked")
        self.assertTrue(result["boundary_findings"])
        self.assertFalse(marker.exists())

    def test_strict_modes_required_arguments_duplicates_and_unknown_options(self):
        cases = [[], ["--source-root", str(self.root)], ["--estate-callers"],
                 self.estate_args + ["--adoption-migration"],
                 self.estate_args + ["--estate-callers"],
                 self.estate_args + ["--source-root=" + SENTINEL],
                 self.estate_args + ["--previous-adoption-ledger", str(self.previous)],
                 ["--adoption-migration", "--source-root", str(self.root)],
                 self.estate_args + ["--json", "--json"],
                 self.estate_args + ["--expected-result", SENTINEL],
                 self.estate_args + ["--workflow", SENTINEL],
                 self.estate_args + ["--graph", SENTINEL],
                 self.estate_args + ["--release", SENTINEL],
                 self.estate_args + ["--execute", SENTINEL],
                 self.estate_args + ["--", SENTINEL],
                 ["--estate-callers", "--source-ro", str(self.root)]]
        for args in cases:
            with self.subTest(args_count=len(args)):
                self.assert_error(args)

    def test_public_mode_conflict_is_closed_and_safe(self):
        self.assert_error(self.estate_args + ["--adoption-migration", "--previous-adoption-ledger", SENTINEL], public=True)

    def test_missing_source_is_safe(self):
        self.assert_error(["--estate-callers", "--source-root", str(self.base / SENTINEL)], "source-analysis-failed")

    def test_missing_ledger_is_safe(self):
        self.assert_error(self.migration_args[:-1] + [str(self.base / SENTINEL)], "adoption-ledger-unreadable")

    def test_duplicate_keys_and_yaml_alias_ledger_are_rejected(self):
        for body in ('{"schema":"a","schema":"b","private":"' + SENTINEL + '"}',
                     "value: &anchor " + SENTINEL + "\ncopy: *anchor\n"):
            self.previous.write_text(body)
            self.assert_error(self.migration_args, "adoption-ledger-unreadable")

    def test_invalid_ledger_schema_is_safe(self):
        self.previous.write_text(json.dumps({"private": SENTINEL}))
        self.assert_error(self.migration_args, "adoption-migration-failed")

    def test_changed_ledger_during_migration_rejects_proposal(self):
        original = adoption_migration.migrate_adoption
        def changed(*args):
            result = original(*args)
            self.previous.write_text('{"private":"' + SENTINEL + '"}')
            return result
        with patch.object(adoption_migration, "migrate_adoption", side_effect=changed):
            self.assert_error(self.migration_args, "adoption-migration-failed")

    def test_changed_source_during_migration_rejects_proposal(self):
        original = adoption_migration.migrate_adoption
        def changed(*args):
            result = original(*args)
            (self.root / "package.json").write_text('{"name":"changed"}')
            return result
        with patch.object(adoption_migration, "migrate_adoption", side_effect=changed):
            self.assert_error(self.migration_args, "adoption-migration-failed")

    def assert_mutated_output_rejected(self, migration, field, value):
        if migration:
            original = adoption_migration.migrate_adoption(
                self.inventory, release.load_document(self.previous))
            module, name, args, code = (adoption_migration, "migrate_adoption", self.migration_args,
                                        "adoption-migration-failed")
        else:
            original = estate.reconcile_estate(self.root)
            module, name, args, code = estate, "reconcile_estate", self.estate_args, "source-analysis-failed"
        mutated = deepcopy(original)
        mutated[field] = value
        if field != "result_digest":
            # A valid checksum cannot legitimize unsafe fields or authority.
            mutated["result_digest"] = release.digest_document(
                {key: item for key, item in mutated.items() if key != "result_digest"})
        with patch.object(module, name, return_value=mutated):
            self.assert_error(args, code)

    def test_estate_output_rejects_extra_field_with_valid_checksum(self):
        self.assert_mutated_output_rejected(False, "secret", SENTINEL)

    def test_estate_output_rejects_authority_drift_with_valid_checksum(self):
        for field, value in (("authorized", True), ("authorized", 0),
                             ("release_eligibility", "eligible"), ("operation_authorization", "authorized"),
                             ("qualification_verdict", "qualified")):
            with self.subTest(field=field, value=value):
                self.assert_mutated_output_rejected(False, field, value)

    def test_estate_output_rejects_wrong_self_digest(self):
        self.assert_mutated_output_rejected(False, "result_digest", "sha256:" + "a" * 64)

    def test_migration_output_rejects_extra_field_with_valid_checksum(self):
        self.assert_mutated_output_rejected(True, "secret", SENTINEL)

    def test_migration_output_rejects_authority_drift_with_valid_checksum(self):
        for field, value in (("authorized", True), ("authorized", 0),
                             ("release_eligibility", "eligible"), ("operation_authorization", "authorized"),
                             ("review_verdict", "reviewed"), ("retirement_authorized", True),
                             ("deletion_authorized", True)):
            with self.subTest(field=field, value=value):
                self.assert_mutated_output_rejected(True, field, value)

    def test_migration_output_rejects_wrong_self_digest(self):
        self.assert_mutated_output_rejected(True, "result_digest", "sha256:" + "a" * 64)

    def test_helper_exception_never_echoes_input(self):
        with patch.object(estate, "reconcile_estate", side_effect=RuntimeError(SENTINEL)):
            self.assert_error(self.estate_args, "source-analysis-failed")

    def test_missing_import_uses_schema_independent_rejection(self):
        original = builtins.__import__
        def unavailable(name, *args, **kwargs):
            if name == "estate_caller_coverage":
                raise ImportError(SENTINEL)
            return original(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=unavailable):
            self.assert_error(self.estate_args, "dependency-unavailable")

    def test_missing_and_corrupt_error_contract_fail_closed(self):
        schema_root = self.base / "schemas"
        schema_root.mkdir()
        with patch.object(coverage, "SCHEMA_DIR", schema_root):
            self.assert_error(self.estate_args, "dependency-unavailable")
            (schema_root / "estate-caller-error.schema.yml").write_text(SENTINEL)
            self.assert_error(self.estate_args, "dependency-unavailable")

    def test_error_schema_change_during_execution_rejects_success(self):
        original = coverage.validate_schema
        calls = 0
        def changed(name, value):
            nonlocal calls
            result = original(name, value)
            if name == "estate-caller-error":
                calls += 1
                if calls > 1:
                    return "sha256:" + "a" * 64
            return result
        with patch.object(coverage, "validate_schema", side_effect=changed):
            self.assert_error(self.estate_args, "dependency-unavailable")

    def test_error_schema_rejects_raw_details_and_authority(self):
        schema = release.load_document(release.SCHEMA_DIR / "estate-caller-error.schema.yml")
        for field, value in (("authorized", True), ("details", SENTINEL), ("release_eligibility", "eligible")):
            result = cli.reject("arguments-invalid")
            result[field] = value
            self.assertTrue(list(Draft202012Validator(schema).iter_errors(result)))
        result = cli.reject("arguments-invalid")
        result["findings"][0]["code"] = SENTINEL
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(result)))


if __name__ == "__main__":
    unittest.main()
