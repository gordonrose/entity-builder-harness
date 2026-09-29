#!/usr/bin/env python3
"""Verify fresh operation contracts and consumption through the public gate."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operation-contracts-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject stale, omitted and unsafe operation contracts through the public command.
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
import caller_coverage
import operation_contracts
import operation_contracts_cli
from caller_inventory import discover_callers
from operation_inventory import discover_operations

WORKFLOW = ".github/workflows/check.yml"
SENTINEL = "SENTINEL-SENSITIVE-DO-NOT-PRINT"


class OperationContractsCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="source-operations-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / "source"
        shutil.copytree(DIRECTORY / "fixtures/source-operations/cli-source", self.source)
        self.graph = discover_callers(self.source, WORKFLOW)
        self.review = caller_coverage.make_review(self.graph)
        for binding in self.review["bindings"]:
            binding["review_status"] = "reviewed"
            binding["operation_profile"] = "finite-job"
        self.inventory = discover_operations(self.source, WORKFLOW, graph=self.graph)
        self.contracts = operation_contracts.make_contracts(self.inventory, self.graph, self.review)
        for binding in self.contracts["bindings"]:
            binding["review_status"] = "reviewed"
        self.review_path = self.base / "caller-review.json"
        self.contracts_path = self.base / "contracts.json"
        self.review_path.write_text(json.dumps(self.review))
        self.contracts_path.write_text(json.dumps(self.contracts))
        self.common = ["--operations", "--source-root", str(self.source), "--workflow", WORKFLOW]
        self.args = [*self.common, "--caller-review", str(self.review_path),
                     "--operation-contracts", str(self.contracts_path)]

    def command(self, args):
        return subprocess.run(["bash", str(DIRECTORY / "script.sh"), *args],
                              cwd=ROOT, capture_output=True, text=True, check=False)

    def result(self, args=None, status=1):
        process = self.command(self.args if args is None else args)
        self.assertEqual(process.returncode, status, process.stdout + process.stderr)
        self.assertEqual(process.stderr, "")
        self.assertNotIn(SENTINEL, process.stdout)
        self.assertNotIn("Traceback", process.stdout)
        return json.loads(process.stdout)

    def test_fresh_operation_contracts_are_complete_but_unqualified(self):
        result = self.result(status=0)
        self.assertEqual(result["contracts_verdict"], "complete")
        self.assertEqual(result["source_closure"], "blocked")
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertIs(result["authorized"], False)
        self.assertTrue(result["source_findings"])

    def test_discovery_reports_opaque_boundaries_and_template_stays_pending(self):
        inventory = self.result(self.common)
        self.assertEqual(inventory["schema"], "source-operation-inventory/v1")
        self.assertEqual(inventory, self.inventory)
        template = self.result([*self.common, "--caller-review", str(self.review_path),
                                "--operation-template"])
        self.assertTrue(all(b["review_status"] == "pending" for b in template["bindings"]))
        self.contracts_path.write_text(json.dumps(template))
        result = self.result()
        self.assertEqual(result["contracts_verdict"], "incomplete")

    def test_discovery_uses_the_same_strict_schema_boundary_as_compilation(self):
        original = operation_contracts.release.load_document(
            operation_contracts.SCHEMA_DIR / "source-operation-inventory.schema.yml")
        for mutation in ({"additionalProperties": True},
                         {"$recursiveRef": "https://invalid.example/" + SENTINEL}):
            directory = self.base / "schema"
            directory.mkdir(exist_ok=True)
            (directory / "source-operation-inventory.schema.yml").write_text(
                json.dumps(dict(original, **mutation)))
            output = StringIO()
            with patch.object(operation_contracts, "SCHEMA_DIR", directory), redirect_stdout(output):
                status = operation_contracts_cli.main(self.common)
            self.assertEqual(status, 1)
            self.assertNotIn(SENTINEL, output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["contracts_verdict"], "incomplete")

    def test_changed_local_imported_source_invalidates_saved_contract(self):
        (self.source / "scripts/04.deploy/dependency.mjs").write_text('export const value = "changed";\n')
        self.assertEqual(self.result()["contracts_verdict"], "incomplete")

    def test_new_dependency_invalidates_saved_contract(self):
        (self.source / "scripts/04.deploy/additional.mjs").write_text("export const additional = 2;\n")
        with (self.source / "scripts/04.deploy/task.mjs").open("a") as stream:
            stream.write('import "./additional.mjs";\n')
        self.assertEqual(self.result()["contracts_verdict"], "incomplete")

    def test_new_argument_variant_invalidates_prior_caller_and_operation_contracts(self):
        package = json.loads((self.source / "package.json").read_text())
        package["scripts"]["verify"] += " --unexpected"
        (self.source / "package.json").write_text(json.dumps(package))
        self.assertEqual(self.result()["contracts_verdict"], "incomplete")

    def test_action_input_change_invalidates_contract(self):
        path = self.source / WORKFLOW
        path.write_text(path.read_text().replace("persist-credentials: false", "persist-credentials: true"))
        self.assertEqual(self.result()["contracts_verdict"], "incomplete")

    def test_omitted_or_duplicate_binding_cannot_complete(self):
        for bindings in (self.contracts["bindings"][1:],
                         [*self.contracts["bindings"], self.contracts["bindings"][0]]):
            document = copy.deepcopy(self.contracts)
            document["bindings"] = bindings
            self.contracts_path.write_text(json.dumps(document))
            self.assertEqual(self.result()["contracts_verdict"], "incomplete")

    def test_unknown_fields_and_duplicate_keys_fail_without_echo(self):
        document = copy.deepcopy(self.contracts)
        document["token"] = SENTINEL
        for payload in (json.dumps(document), '{"schema":"a","schema":"b","token":"' + SENTINEL + '"}'):
            self.contracts_path.write_text(payload)
            self.assertEqual(self.result()["contracts_verdict"], "incomplete")

    def test_missing_or_pending_caller_review_cannot_create_contract_success(self):
        self.review_path.unlink()
        self.assertEqual(self.result()["contracts_verdict"], "incomplete")
        self.review["bindings"][0]["review_status"] = "pending"
        self.review_path.write_text(json.dumps(self.review))
        self.assertEqual(self.result()["contracts_verdict"], "incomplete")

    def test_mixed_missing_or_unsafe_arguments_fail_closed(self):
        for args in ([*self.common, "--operation-contracts", str(self.contracts_path)],
                     [*self.common, "--caller-review", str(self.review_path)],
                     [*self.args, "--operation-template"], [*self.args, "--coverage"],
                     [*self.args, "--source-root", str(self.source)],
                     [*self.args, "--token", SENTINEL]):
            self.assertEqual(self.result(args)["contracts_verdict"], "incomplete")

    def test_operation_result_consumption_requires_fresh_source_and_never_authority(self):
        result = self.result(status=0)
        saved = self.base / "result.json"
        saved.write_text(json.dumps(result))
        for purpose in ("source-analysis", "release-eligibility", "operation-authorization"):
            decision = self.result(["--consume-result", str(saved), "--purpose", purpose, "--", *self.args],
                                   status=0 if purpose == "source-analysis" else 1)
            self.assertEqual(decision["verdict"], "accepted" if purpose == "source-analysis" else "rejected")
            self.assertIs(decision["authorized"], False)
        (self.source / "scripts/04.deploy/dependency.mjs").write_text("export const changed = 4;\n")
        decision = self.result(["--consume-result", str(saved), "--purpose", "source-analysis", "--", *self.args])
        self.assertEqual(decision["verdict"], "rejected")

    def test_forged_operation_success_and_templates_are_rejected_by_consumer(self):
        saved = self.base / "result.json"
        result = self.result(status=0)
        for mutation in ({"authorized": True}, {"source_closure": "closed"},
                         {"qualification_verdict": "passed"}, {"token": SENTINEL}):
            saved.write_text(json.dumps(dict(result, **mutation)))
            decision = self.result(["--consume-result", str(saved), "--purpose", "source-analysis", "--", *self.args])
            self.assertEqual(decision["verdict"], "rejected")
        saved.write_text(json.dumps(result))
        decision = self.result(["--consume-result", str(saved), "--purpose", "source-analysis", "--",
                                *self.common, "--caller-review", str(self.review_path), "--operation-template"])
        self.assertEqual(decision["verdict"], "rejected")


if __name__ == "__main__":
    unittest.main()
