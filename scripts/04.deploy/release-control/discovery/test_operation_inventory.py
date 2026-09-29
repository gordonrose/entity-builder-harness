#!/usr/bin/env python3
"""Mutation and boundary tests for observed operation source inputs."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.operation-inventory-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove operation argument and source membership freshness with conservative unresolved boundaries.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import operation_inventory as operations
from caller_inventory import discover_callers
from source_inventory import SourceFailure, canonical, digest


class OperationInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="operation-inventory-test-")
        self.root = Path(self.temp.name)
        self.workflow = ".github/workflows/check.yml"
        self.put(self.workflow, {"jobs": {"check": {"steps": [{"run": "npm run check"}, {"uses": "actions/checkout@v4"}]}}})
        self.package = {"scripts": {"check": "tsc -p platform/test/tsconfig.json && node scripts/check.mjs"}}
        self.put("package.json", self.package)
        self.put("scripts/check.mjs", 'import { value } from "./dependency.mjs";\nconsole.log(value);\n')
        self.put("scripts/dependency.mjs", "export const value = 1;\n")
        self.config = {"include": ["src/**/*.ts"]}
        self.put("platform/test/tsconfig.json", self.config)
        self.put("platform/test/src/index.ts", 'import { value } from "./value.js"; export { value };\n')
        self.put("platform/test/src/value.ts", "export const value = 1;\n")

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value))
        return target

    def inventory(self, graph=None):
        return operations.discover_operations(self.root, self.workflow, graph)

    def codes(self, inventory=None):
        return {item["code"] for item in (inventory or self.inventory())["findings"]}

    def paths(self, inventory=None):
        return {item["path"] for item in (inventory or self.inventory())["sources"]}

    def test_deterministic_positive_has_exact_selected_subjects_and_bindings(self):
        result = self.inventory()
        self.assertEqual(result, self.inventory())
        self.assertEqual({row["kind"] for row in result["subjects"]}, {"script", "tool", "action"})
        self.assertEqual(len(result["subjects"]), 3)
        self.assertIn("scripts/dependency.mjs", self.paths(result))
        self.assertIn("platform/test/src/value.ts", self.paths(result))
        self.assertEqual(result["inventory_digest"], digest(canonical({key: value for key, value in result.items() if key != "inventory_digest"})))
        graph = discover_callers(self.root, self.workflow)
        for subject in result["subjects"]:
            self.assertEqual(subject["invocation_ids"], sorted(edge["id"] for edge in graph["edges"] if edge["callee_id"] == subject["id"]))
        self.assertTrue({"script-semantics-unresolved", "tool-semantics-unresolved", "action-implementation-unresolved"} <= self.codes(result))

    def test_all_rows_are_bound_to_reachable_sources(self):
        result = self.inventory()
        source_ids = {row["id"] for row in result["sources"]}
        for subject in result["subjects"]:
            reached = {subject["source_id"]}
            previous = set()
            while previous != reached:
                previous = set(reached)
                reached.update(row["to_source_id"] for row in result["dependencies"] if row["subject_id"] == subject["id"] and row["from_source_id"] in reached)
            self.assertTrue(reached <= source_ids)
            self.assertTrue(all(row["source_id"] in reached for row in result["observations"] if row["subject_id"] == subject["id"]))

    def test_changed_dependency_changes_inventory_without_changing_caller_graph(self):
        before = self.inventory()
        self.put("scripts/dependency.mjs", "export const value = 2;\n")
        after = self.inventory()
        self.assertEqual(before["graph_digest"], after["graph_digest"])
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])

    def test_new_include_member_changes_inventory(self):
        before = self.inventory()
        self.put("platform/test/src/new.ts", "export const added = true;\n")
        after = self.inventory()
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])
        self.assertIn("platform/test/src/new.ts", self.paths(after))

    def test_new_import_is_discovered(self):
        before = self.inventory()
        self.put("scripts/another.mjs", "export const another = 1;\n")
        self.put("scripts/dependency.mjs", 'export { another } from "./another.mjs";\n')
        after = self.inventory()
        self.assertIn("scripts/another.mjs", self.paths(after))
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])

    def test_new_argument_variant_changes_invocation_observations(self):
        before = self.inventory()
        self.package["scripts"]["check"] += " --json"
        self.put("package.json", self.package)
        after = self.inventory()
        self.assertNotEqual([row for row in before["observations"] if row["kind"] == "invocation"], [row for row in after["observations"] if row["kind"] == "invocation"])

    def test_missing_import_is_explicit(self):
        (self.root / "scripts/dependency.mjs").unlink()
        self.assertIn("operation-input-missing", self.codes())

    def test_import_cycle_does_not_recurse_forever(self):
        self.put("scripts/dependency.mjs", 'import "./check.mjs";\n')
        self.assertIn("operation-dependency-cycle", self.codes())

    def test_dynamic_import_retains_unresolved_finding(self):
        self.put("scripts/check.mjs", "const name = process.argv[2]; await import(name);\n")
        self.assertIn("dynamic-input-unresolved", self.codes())

    def test_external_import_retains_unresolved_finding(self):
        self.put("scripts/check.mjs", 'import "external-library";\n')
        self.assertIn("external-import-unresolved", self.codes())

    def test_builtin_import_is_observed(self):
        self.put("scripts/check.mjs", 'import fs from "node:fs";\n')
        self.assertIn("literal-import", {row["kind"] for row in self.inventory()["observations"]})

    def test_relative_import_escape_is_rejected(self):
        self.put("scripts/check.mjs", 'import "../../outside.mjs";\n')
        self.assertIn("operation-path-unsafe", self.codes())

    def test_generated_output_is_never_read(self):
        self.put("scripts/check.mjs", 'import "../.cache/generated.mjs";\n')
        self.put(".cache/generated.mjs", "PRIVATE_SENTINEL")
        result = self.inventory()
        self.assertIn("generated-input-unresolved", self.codes(result))
        self.assertNotIn(".cache/generated.mjs", self.paths(result))
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_symlink_import_is_rejected_without_following(self):
        (self.root / "scripts/dependency.mjs").unlink()
        (self.root / "scripts/dependency.mjs").symlink_to("/etc/passwd")
        result = self.inventory()
        self.assertIn("operation-input-unreadable", self.codes(result))
        self.assertNotIn("root:", json.dumps(result))

    def test_symlink_parent_is_rejected(self):
        (self.root / "scripts/link").symlink_to("/etc", target_is_directory=True)
        self.put("scripts/check.mjs", 'import "./link/passwd";\n')
        self.assertIn("operation-input-unreadable", self.codes())

    def test_include_symlink_is_explicit(self):
        (self.root / "platform/test/src/link.ts").symlink_to("/etc/passwd")
        self.assertIn("operation-input-unreadable", self.codes())

    def test_config_extends_and_explicit_files_are_bound(self):
        self.config = {"extends": "./base.json", "files": ["src/index.ts"]}
        self.put("platform/test/tsconfig.json", self.config)
        self.put("platform/test/base.json", {"include": ["src/value.ts"]})
        result = self.inventory()
        self.assertIn("platform/test/base.json", self.paths(result))
        self.assertIn("config-extends", {row["kind"] for row in result["dependencies"]})

    def test_config_cycle_is_explicit(self):
        self.put("platform/test/tsconfig.json", {"extends": "./tsconfig.json", "include": []})
        self.assertIn("operation-dependency-cycle", self.codes())

    def test_config_unsupported_glob_is_explicit(self):
        self.put("platform/test/tsconfig.json", {"include": ["src/[ab].ts"]})
        self.assertIn("operation-path-unsafe", self.codes())

    def test_config_path_alias_and_reference_remain_unresolved(self):
        self.put("platform/test/tsconfig.json", {"compilerOptions": {"paths": {"@x": ["src/index.ts"]}}, "references": [{"path": "../other"}], "include": ["src/**/*.ts"]})
        self.assertIn("build-resolution-unresolved", self.codes())

    def test_external_extends_is_unsupported(self):
        self.put("platform/test/tsconfig.json", {"extends": "external-package/config", "include": []})
        self.assertIn("build-config-unsupported", self.codes())

    def test_malformed_config_fails_closed(self):
        self.put("platform/test/tsconfig.json", '{"include": [], "include": []}')
        self.assertIn("build-config-invalid", self.codes())

    def test_no_include_is_not_claimed_complete(self):
        self.put("platform/test/tsconfig.json", {})
        self.assertIn("build-default-membership-unresolved", self.codes())

    def test_unknown_tool_args_are_unresolved(self):
        self.package["scripts"]["check"] = "tsc --build platform/test/tsconfig.json"
        self.put("package.json", self.package)
        self.assertIn("tool-arguments-unsupported", self.codes())

    def test_shell_literal_child_and_python_embedded_path_are_bound(self):
        self.package["scripts"]["check"] = "bash scripts/check.sh"
        self.put("package.json", self.package)
        self.put("scripts/check.sh", 'python3 - <<\'PY\'\nfrom pathlib import Path\np = Path("infra/data.json")\nPY\nbash scripts/child.sh\n')
        self.put("scripts/child.sh", "echo safe\n")
        self.put("infra/data.json", {})
        result = self.inventory()
        self.assertIn("infra/data.json", self.paths(result))
        self.assertIn("scripts/child.sh", self.paths(result))
        self.assertIn("dynamic-input-unresolved", self.codes(result))

    def test_local_python_import_is_bound_without_importing(self):
        self.package["scripts"]["check"] = "python3 scripts/check.py"
        self.put("package.json", self.package)
        self.put("scripts/check.py", "import helper\n")
        self.put("scripts/helper.py", "raise RuntimeError('DO_NOT_IMPORT')\n")
        self.assertIn("scripts/helper.py", self.paths())

    def test_no_source_execution(self):
        sentinel = self.root / "executed"
        self.put("scripts/check.mjs", f'import fs from "node:fs"; fs.writeFileSync({json.dumps(str(sentinel))}, "executed");\n')
        self.inventory()
        self.assertFalse(sentinel.exists())

    def test_output_does_not_echo_arguments_or_literal_values(self):
        self.package["scripts"]["check"] += " --secret VALUE_SENTINEL"
        self.put("package.json", self.package)
        self.assertNotIn("VALUE_SENTINEL", json.dumps(self.inventory()))

    def test_fresh_graph_optimization_preserves_result(self):
        graph = discover_callers(self.root, self.workflow)
        self.assertEqual(self.inventory(), self.inventory(graph))

    def test_stale_graph_produces_explicit_finding(self):
        graph = discover_callers(self.root, self.workflow)
        self.put("scripts/check.mjs", "console.log('changed');\n")
        with self.assertRaisesRegex(SourceFailure, "^operation-graph-stale$"):
            self.inventory(graph)

    def test_limit_exhaustion_is_explicit(self):
        with patch.object(operations, "MAX_FILES", 1):
            with self.assertRaisesRegex(SourceFailure, "^operation-limit-exceeded$"):
                self.inventory()

    def test_depth_exhaustion_rejects_incomplete_inventory(self):
        with patch.object(operations, "MAX_DEPTH", 0):
            with self.assertRaisesRegex(SourceFailure, "^operation-limit-exceeded$"):
                self.inventory()

    def test_broad_include_pruning_is_explicit(self):
        self.put("platform/test/src/node_modules/hidden.ts", "PRIVATE_SENTINEL")
        result = self.inventory()
        self.assertIn("generated-input-unresolved", self.codes(result))
        self.assertNotIn("platform/test/src/node_modules/hidden.ts", self.paths(result))

    def test_ambiguous_import_binds_every_existing_candidate(self):
        self.put("platform/test/src/value.js", "export const value = 3;")
        before = self.inventory()
        self.assertIn("import-resolution-ambiguous", self.codes(before))
        self.assertIn("platform/test/src/value.js", self.paths(before))
        self.put("platform/test/src/value.js", "export const value = 4;")
        self.assertNotEqual(before["inventory_digest"], self.inventory()["inventory_digest"])

    def test_empty_stale_graph_is_rejected(self):
        self.put(self.workflow, {"jobs": {"check": {"steps": [{"run": "echo $DYNAMIC"}]}}})
        graph = discover_callers(self.root, self.workflow)
        self.put(self.workflow, {"jobs": {"check": {"steps": [{"uses": "actions/checkout@v4"}]}}})
        with self.assertRaisesRegex(SourceFailure, "^operation-graph-stale$"):
            self.inventory(graph)

    def test_dotenv_variant_is_not_read_or_hashed(self):
        self.put("scripts/check.mjs", 'const input = "docs/.env.production";')
        self.put("docs/.env.production", "PRIVATE_SENTINEL")
        result = self.inventory()
        self.assertIn("generated-input-unresolved", self.codes(result))
        self.assertNotIn("docs/.env.production", self.paths(result))
        self.assertNotIn(digest(b"PRIVATE_SENTINEL"), json.dumps(result))

    def test_dotenv_directory_is_not_walked(self):
        self.put("platform/test/src/.env.production/private.ts", "PRIVATE_SENTINEL")
        result = self.inventory()
        self.assertIn("generated-input-unresolved", self.codes(result))
        self.assertNotIn("platform/test/src/.env.production/private.ts", self.paths(result))

    def test_aggregate_byte_exhaustion_rejects_inventory(self):
        with patch.object(operations, "MAX_TOTAL_BYTES", 1):
            with self.assertRaisesRegex(SourceFailure, "^operation-limit-exceeded$"):
                self.inventory()

    def test_single_file_byte_exhaustion_rejects_inventory(self):
        self.put("scripts/dependency.mjs", "x" * (2 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(SourceFailure, "^operation-limit-exceeded$"):
            self.inventory()


if __name__ == "__main__":
    unittest.main()
