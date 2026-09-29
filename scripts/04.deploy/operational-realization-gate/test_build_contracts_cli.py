#!/usr/bin/env python3
"""Exercise build discovery, artifact accounting and authority boundaries publicly."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.build-contracts-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify source and artifact freshness, strict schemas and fail-closed public build commands.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
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
import build_contracts
import build_contracts_cli
import release_compiler as release

WORKFLOW = ".github/workflows/check.yml"
SENTINEL = "SENSITIVE-BUILD-SENTINEL"
DIGEST = "sha256:" + "a" * 64


class BuildContractsCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="build-cli-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.source = self.base / "source"
        self.artifact = self.base / "artifact"
        fixtures = DIRECTORY / "fixtures/source-builds"
        shutil.copytree(fixtures / "source", self.source)
        shutil.copytree(fixtures / "artifact", self.artifact)
        self.args = ["--builds", "--source-root", str(self.source), "--workflow", WORKFLOW]

    def invoke(self, args=None, expected=1):
        process = subprocess.run(["bash", str(DIRECTORY / "script.sh"),
                                  *(self.args if args is None else args)],
                                 cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(process.returncode, expected, process.stdout + process.stderr)
        self.assertEqual(process.stderr, "")
        self.assertNotIn(SENTINEL, process.stdout)
        self.assertNotIn("Traceback", process.stdout)
        return json.loads(process.stdout)

    def inventory(self):
        return self.invoke()

    def artifact_args(self):
        inventory = self.inventory()
        return [*self.args, "--build-id", inventory["builds"][0]["id"],
                "--artifact-root", str(self.artifact)]

    def test_source_discovery_reports_one_build_and_open_qualification(self):
        inventory = self.inventory()
        self.assertEqual(inventory["schema"], "source-build-inventory/v1")
        self.assertEqual(len(inventory["builds"]), 1)
        self.assertTrue(inventory["findings"])
        build_contracts.checked_inventory(inventory)

    def test_local_matching_artifact_is_accounted_without_authority(self):
        result = self.invoke(self.artifact_args(), expected=0)
        self.assertEqual(result["artifact_verdict"], "complete")
        self.assertIs(result["authorized"], False)
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertEqual(result["provenance"], "unproven")

    def test_source_change_rejects_pinned_inventory(self):
        inventory = self.inventory()
        (self.source / "platform/server/src/index.ts").write_text("export const value = 2;\n")
        result = self.invoke([*self.args, "--expect-inventory-digest", inventory["inventory_digest"]])
        self.assertEqual(result["findings"], [{"code": "build-inventory-stale"}])

    def test_lock_change_invalidates_inventory(self):
        before = self.inventory()
        path = self.source / "package-lock.json"
        value = json.loads(path.read_text())
        value["packages"]["node_modules/example"] = {"version": "1.0.0"}
        path.write_text(json.dumps(value))
        self.assertNotEqual(before["inventory_digest"], self.inventory()["inventory_digest"])

    def test_artifact_byte_change_rejects_pinned_artifact(self):
        args = self.artifact_args()
        result = self.invoke(args, expected=0)
        (self.artifact / "index.js").write_text("exports.value = 2;\n")
        rejected = self.invoke([*args, "--expect-artifact-digest", result["artifact_digest"]])
        self.assertEqual(rejected["findings"], [{"code": "build-artifact-stale"}])

    def test_missing_output_cannot_complete(self):
        (self.artifact / "index.js").rename(self.base / "removed.js")
        result = self.invoke(self.artifact_args())
        self.assertEqual(result["artifact_verdict"], "incomplete")

    def test_unexpected_output_cannot_complete(self):
        (self.artifact / "stale.js").write_text("exports.old = true;\n")
        result = self.invoke(self.artifact_args())
        self.assertEqual(result["artifact_verdict"], "incomplete")

    def test_duplicate_and_mixed_modes_reject(self):
        for extra in (["--builds"], ["--operations"], ["--release", SENTINEL],
                      ["--callers"], ["--operation-template"], ["--discover"]):
            self.assertEqual(self.invoke([*self.args, *extra])["verdict"], "incomplete")

    def test_artifact_flags_must_be_paired(self):
        for extra in (["--build-id", DIGEST], ["--artifact-root", SENTINEL],
                      ["--expect-artifact-digest", DIGEST]):
            self.assertEqual(self.invoke([*self.args, *extra])["findings"],
                             [{"code": "arguments-invalid"}])

    def test_bad_digest_and_unknown_build_do_not_echo(self):
        for extra in (["--expect-inventory-digest", SENTINEL],
                      ["--build-id", SENTINEL, "--artifact-root", str(self.artifact)]):
            self.assertEqual(self.invoke([*self.args, *extra])["findings"],
                             [{"code": "arguments-invalid"}])
        self.invoke([*self.args, "--build-id", DIGEST, "--artifact-root", str(self.artifact)])

    def test_unknown_and_missing_arguments_fail_safely(self):
        for args in (["--builds"], [*self.args, "--password", SENTINEL],
                     [*self.args, "--build"], [*self.args, SENTINEL]):
            self.assertEqual(self.invoke(args)["verdict"], "incomplete")

    def test_root_symlink_and_private_artifact_are_rejected(self):
        link = self.base / "linked-artifact"
        link.symlink_to(self.artifact, target_is_directory=True)
        args = self.artifact_args()
        args[-1] = str(link)
        self.invoke(args)
        (self.artifact / ".env.production").write_text(SENTINEL)
        self.invoke(self.artifact_args())

    def test_schema_open_remote_and_version_mutations_fail_closed(self):
        original = release.load_document(build_contracts.SCHEMA_DIR / "source-build-inventory.schema.yml")
        directory = self.base / "schemas"
        directory.mkdir()
        for mutation in ({"additionalProperties": True},
                         {"$recursiveRef": "https://invalid.example/" + SENTINEL},
                         {"$id": "urn:unrecognized"},
                         {"properties": {**original["properties"], "schema": {"const": "wrong/v1"}}}):
            (directory / "source-build-inventory.schema.yml").write_text(
                json.dumps(dict(original, **mutation)))
            output = StringIO()
            with patch.object(build_contracts, "SCHEMA_DIR", directory), redirect_stdout(output):
                status = build_contracts_cli.main(self.args)
            self.assertEqual(status, 1)
            self.assertNotIn(SENTINEL, output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["verdict"], "incomplete")

    def test_missing_schema_fails_safely(self):
        output = StringIO()
        with patch.object(build_contracts, "SCHEMA_DIR", self.base), redirect_stdout(output):
            self.assertEqual(build_contracts_cli.main(self.args), 1)
        self.assertEqual(json.loads(output.getvalue())["findings"],
                         [{"code": "build-schema-unreadable"}])

    def test_inventory_unknown_fields_digest_and_references_reject(self):
        inventory = self.inventory()
        for change in ("field", "digest", "reference"):
            value = copy.deepcopy(inventory)
            if change == "field":
                value["raw_command"] = SENTINEL
            elif change == "digest":
                value["inventory_digest"] = DIGEST
            else:
                value["builds"][0]["config_source_id"] = DIGEST
                value["inventory_digest"] = release.digest_document(
                    {k: v for k, v in value.items() if k != "inventory_digest"})
            with self.assertRaises(release.ReleaseFailure):
                build_contracts.checked_inventory(value)

    def test_build_results_cannot_be_consumed_as_release_or_authority(self):
        saved = self.base / "saved.json"
        saved.write_text(json.dumps(self.invoke(self.artifact_args(), expected=0)))
        for purpose in ("source-analysis", "release-eligibility", "operation-authorization"):
            result = self.invoke(["--consume-result", str(saved), "--purpose", purpose,
                                  "--", *self.artifact_args()])
            self.assertEqual(result["verdict"], "rejected")
            self.assertIs(result["authorized"], False)
            self.assertEqual(result["release_eligibility"], "blocked")

    def test_fresh_digest_is_accepted_for_source_comparison(self):
        inventory = self.inventory()
        result = self.invoke([*self.args, "--expect-inventory-digest", inventory["inventory_digest"]])
        self.assertEqual(inventory, result)

    def test_source_root_symlink_is_rejected(self):
        link = self.base / "linked-source"
        link.symlink_to(self.source, target_is_directory=True)
        args = list(self.args)
        args[2] = str(link)
        self.assertEqual(self.invoke(args)["verdict"], "incomplete")

    def test_foreign_mapping_and_duplicate_build_references_are_rejected(self):
        inventory = self.inventory()
        for change in ("mapping", "build"):
            value = copy.deepcopy(inventory)
            if change == "mapping":
                value["builds"][0]["expected_outputs"][0]["source_id"] = DIGEST
            else:
                value["builds"].append(copy.deepcopy(value["builds"][0]))
            value["inventory_digest"] = release.digest_document(
                {k: v for k, v in value.items() if k != "inventory_digest"})
            with self.assertRaises(release.ReleaseFailure):
                build_contracts.checked_inventory(value)


if __name__ == "__main__":
    unittest.main()
