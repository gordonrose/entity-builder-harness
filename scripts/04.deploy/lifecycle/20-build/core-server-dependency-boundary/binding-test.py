#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-dependency-bindings
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove bootstrap dependency observations follow canonical renamed declarations and reject missing or unsafe evidence.
#   portability: {class: source-only, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.core-server-dependency-boundary
#     path: scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/smoke-test.sh

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("bootstrap_boundary", Path(__file__).with_name("script.py"))
boundary = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = boundary
spec.loader.exec_module(boundary)


class BindingsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.contract = self.root / "program.yml"
        self.root_patch = patch.object(boundary, "ROOT", self.root)
        self.contract_patch = patch.object(boundary, "CONTRACT_PATH", self.contract)
        self.root_patch.start()
        self.contract_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.contract_patch.stop)
        self.write("package.json", {"workspaces": ["packages/*"]})
        self.write("package-lock.json", {"lockfileVersion": 3, "packages": {
            "packages/widget": {"name": "@example/widget"},
            "node_modules/@example/widget": {"link": True, "resolved": "packages/widget"},
        }})
        self.manifest = {"name": "@example/widget", "exports": {"./feature": "./src/custom.ts"}}
        self.write("packages/widget/package.json", self.manifest)
        self.write("packages/widget/src/custom.ts", "export const value = 1;")
        self.write(boundary.SOURCE_ENTRYPOINT, 'import { value } from "@example/widget/feature";')
        self.write("project.json", {})
        self.declaration = {"schema": "deploy/runnable-program-contract/v1",
            "dependency_bindings": {"renamed-widget": {"workspace_package": "@example/widget"}},
            "runnable_programs": [{"id": boundary.PROGRAM_ID,
                "build": {"kind": "workspace-typescript", "typescript_project": "project.json"},
                "approved_dependencies": ["renamed-widget"],
                "observed_dependencies": ["renamed-widget"], "forbidden_dependencies": []}]}
        self.write("program.yml", self.declaration)
        self.output = self.root / "output"
        self.write(Path("output") / boundary.COMPILED_ENTRYPOINT, "// isolated compiled-presence fixture")

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")

    def test_real_reader_follows_renamed_export_and_movement(self):
        facts = boundary.validate(self.output)
        self.assertEqual(facts.package_ids, ("renamed-widget",))
        self.assertEqual(facts.package_names, ("@example/widget",))
        self.manifest["exports"]["./feature"] = "./different/place.ts"
        self.write("packages/widget/package.json", self.manifest)
        self.write("packages/widget/different/place.ts", "export const value = 2;")
        (self.root / "packages/widget/src/custom.ts").unlink()
        self.assertEqual(boundary.validate(self.output), facts)

    def test_approved_dependency_is_not_fabricated_as_observed(self):
        self.write(boundary.SOURCE_ENTRYPOINT, "export const independent = true;")
        with self.assertRaises(boundary.BoundaryFailure) as raised:
            boundary.validate(self.output)
        self.assertEqual(raised.exception.codes, ("declared-observed-dependencies-mismatch",))

    def test_removed_export_does_not_fall_back_to_directory_convention(self):
        self.manifest["exports"] = {".": "./src/custom.ts"}
        self.write("packages/widget/package.json", self.manifest)
        with self.assertRaises(boundary.BoundaryFailure) as raised:
            boundary.validate(self.output)
        self.assertEqual(raised.exception.codes, ("typescript-import-unresolved",))

    def test_foreign_namespace_cannot_hide_behind_an_approved_import(self):
        self.write(boundary.SOURCE_ENTRYPOINT, 'import { value } from "@example/widget/feature";\nimport { secret } from "@different/foreign";')
        with self.assertRaises(boundary.BoundaryFailure) as raised:
            boundary.validate(self.output)
        self.assertEqual(raised.exception.codes, ("dependency-unapproved",))

    def test_actual_node_builtin_names_do_not_need_package_approval(self):
        self.write(boundary.SOURCE_ENTRYPOINT, 'import { value } from "@example/widget/feature";\nimport { randomUUID } from "node:crypto";\nimport { readFileSync } from "fs";')
        self.assertEqual(boundary.validate(self.output).package_ids, ("renamed-widget",))

    def test_external_import_uses_approved_canonical_logical_owner(self):
        self.declaration["dependency_bindings"]["different-driver"] = {"external_packages": ["different-driver"]}
        program = self.declaration["runnable_programs"][0]
        program["approved_dependencies"].append("different-driver")
        program["observed_dependencies"].append("different-driver")
        self.write("program.yml", self.declaration)
        self.write(boundary.SOURCE_ENTRYPOINT, 'import { value } from "@example/widget/feature";\nimport { client } from "different-driver/subpath";')
        self.assertEqual(boundary.validate(self.output).package_ids, ("different-driver", "renamed-widget"))

    def test_malformed_declaration_has_safe_failure_and_no_effects(self):
        self.write("packages/widget/package.json", "private-canary not json")
        before = {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        with self.assertRaises(boundary.BoundaryFailure) as raised:
            boundary.validate(self.output)
        self.assertEqual(raised.exception.codes, ("program-build-inputs-rejected",))
        self.assertNotIn("private-canary", json.dumps(boundary.safe_report("failed", raised.exception.codes)))
        self.assertEqual(before, {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*") if path.is_file()})

    def test_relative_source_outside_repository_is_rejected(self):
        bindings = boundary.declaration_bindings()
        with tempfile.TemporaryDirectory() as outside:
            source = Path(outside) / "outside.ts"
            source.write_text("export const value = 1;")
            target = self.root / "escape.ts"
            target.symlink_to(source)
            self.write(boundary.SOURCE_ENTRYPOINT, 'import { value } from "../../../../escape";')
            with self.assertRaises(boundary.BoundaryFailure) as raised:
                boundary.discover_typescript_graph(bindings)
            self.assertEqual(raised.exception.codes, ("typescript-source-outside-repository",))

    def test_reader_failures_are_bounded_and_do_not_leak_provider_text(self):
        cases = [
            (FileNotFoundError("private-canary"), "program-build-inputs-unavailable"),
            (subprocess.SubprocessError("private-canary"), "program-build-inputs-unavailable"),
            (subprocess.TimeoutExpired("private-canary", 30), "program-build-inputs-timeout"),
            (subprocess.CompletedProcess([], 1, "private-canary", "private-canary"), "program-build-inputs-rejected"),
            (subprocess.CompletedProcess([], 0, "private-canary", ""), "program-build-inputs-invalid"),
            (subprocess.CompletedProcess([], 0, json.dumps({"programId": boundary.PROGRAM_ID, "inputs": [], "workspaceOwners": {}}), ""), "program-build-inputs-invalid"),
        ]
        for outcome, expected in cases:
            with self.subTest(expected=expected):
                with patch.object(boundary.subprocess, "run", side_effect=outcome if isinstance(outcome, Exception) else None,
                                  return_value=outcome) as run:
                    with self.assertRaises(boundary.BoundaryFailure) as raised:
                        boundary.declaration_bindings()
                self.assertEqual(raised.exception.codes, (expected,))
                args, kwargs = run.call_args
                self.assertEqual(args[0], ["node", str(boundary.BUILD_INPUT_READER), "--program", boundary.PROGRAM_ID, "--contract", "program.yml"])
                self.assertEqual(kwargs["timeout"], 30)
                self.assertFalse(kwargs.get("shell", False))
                self.assertEqual(run.call_count, 1)
                self.assertNotIn("private-canary", json.dumps(boundary.safe_report("failed", raised.exception.codes)))


if __name__ == "__main__":
    unittest.main()
