#!/usr/bin/env python3
"""Mutation tests for source-only workspace-aware build observations."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.build-inventory-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify local build dependency observation freshness and fail-closed unsupported boundaries.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import build_inventory as builds
from caller_inventory import discover_callers
from source_inventory import SourceFailure, canonical, digest


class BuildInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="build-inventory-test-")
        self.root = Path(self.temp.name)
        self.workflow = ".github/workflows/check.yml"
        self.put(self.workflow, {"jobs": {"check": {"steps": [{"run": "npm run check"}]}}})
        self.package = {"scripts": {"check": "tsc -p platform/test/tsconfig.json"}, "workspaces": ["packages/*"]}
        self.put("package.json", self.package)
        self.put("package-lock.json", {"lockfileVersion": 3, "packages": {}})
        self.config = {"compilerOptions": {"rootDir": "../..", "outDir": "../../.cache/test",
                       "module": "CommonJS", "moduleResolution": "Bundler", "types": []},
                       "include": ["src/**/*.ts"]}
        self.put("platform/test/tsconfig.json", self.config)
        self.put("platform/test/src/index.ts", 'import { value } from "./value.js"; export { value };')
        self.put("platform/test/src/value.ts", "export const value = 1;")
        self.manifest = {"name": "@example/core", "exports": {".": "./src/index.ts", "./part": "./src/part.ts"}}
        self.put("packages/core/package.json", self.manifest)
        self.put("packages/core/src/index.ts", "export const core = 1;")
        self.put("packages/core/src/part.ts", "export const part = 1;")

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value))
        return target

    def inventory(self, graph=None):
        return builds.discover_builds(self.root, self.workflow, graph)

    def codes(self, result=None):
        return {row["code"] for row in (result or self.inventory())["findings"]}

    def paths(self, result=None):
        return {row["path"] for row in (result or self.inventory())["sources"]}

    def build(self, result=None):
        return (result or self.inventory())["builds"][0]

    def update_config(self):
        self.put("platform/test/tsconfig.json", self.config)

    def test_supported_inputs_deterministic_and_bound(self):
        result = self.inventory()
        self.assertEqual(result, self.inventory())
        self.assertEqual(len(result["builds"]), 1)
        self.assertEqual(self.build(result)["prediction_status"], "bounded")
        self.assertEqual({row["path"] for row in self.build(result)["expected_outputs"]},
                         {"platform/test/src/index.js", "platform/test/src/value.js"})
        self.assertEqual(result["inventory_digest"], digest(canonical({key: value for key, value in result.items() if key != "inventory_digest"})))
        self.assertIn("package-lock.json", self.paths(result))
        self.assertTrue({"build-semantics-unresolved", "exact-artifact-unproven", "toolchain-installation-unproven"} <= self.codes(result))

    def test_workspace_exact_export_is_followed_and_manifest_bound(self):
        self.put("platform/test/src/index.ts", 'export { core } from "@example/core";')
        result = self.inventory()
        self.assertIn("packages/core/src/index.ts", self.paths(result))
        self.assertIn("packages/core/package.json", self.paths(result))
        self.assertEqual(self.build(result)["prediction_status"], "bounded")

    def test_workspace_subpath_export_is_followed(self):
        self.put("platform/test/src/index.ts", 'export { part } from "@example/core/part";')
        self.assertIn("packages/core/src/part.ts", self.paths())

    def test_changed_transitive_source_invalidates_digest(self):
        self.put("platform/test/src/index.ts", 'export { core } from "@example/core";')
        before = self.inventory()
        self.put("packages/core/src/index.ts", "export const core = 2;")
        after = self.inventory()
        self.assertEqual(before["graph_digest"], after["graph_digest"])
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])

    def test_changed_lock_invalidates_inventory(self):
        before = self.inventory()
        self.put("package-lock.json", {"lockfileVersion": 3, "packages": {"node_modules/typescript": {"version": "5.9.3"}}})
        self.assertNotEqual(before["inventory_digest"], self.inventory()["inventory_digest"])

    def test_new_workspace_manifest_invalidates_membership(self):
        before = self.inventory()
        self.put("packages/new/package.json", {"name": "@example/new", "exports": "./src/index.ts"})
        self.assertNotEqual(before["inventory_digest"], self.inventory()["inventory_digest"])

    def test_inherited_paths_use_origin_without_baseurl(self):
        self.put("platform/base.json", {"compilerOptions": {"paths": {"core": ["../packages/core/src/index.ts"]}}})
        self.config["extends"] = "../base.json"
        self.update_config()
        self.put("platform/test/src/index.ts", 'export { core } from "core";')
        self.assertIn("packages/core/src/index.ts", self.paths())

    def test_baseurl_and_wildcard_alias(self):
        self.config["compilerOptions"].update({"baseUrl": "../..", "paths": {"@example/*": ["packages/*/src/index.ts"]}})
        self.update_config()
        self.put("platform/test/src/index.ts", 'export { core } from "@example/core";')
        self.assertIn("packages/core/src/index.ts", self.paths())
        self.assertEqual(self.build()["prediction_status"], "bounded")

    def test_baseurl_local_import(self):
        self.config["compilerOptions"]["baseUrl"] = "../.."
        self.update_config()
        self.put("platform/test/src/index.ts", 'export { core } from "packages/core/src/index";')
        self.assertIn("packages/core/src/index.ts", self.paths())

    def test_scoped_baseurl_fallback_is_unresolved_not_unsafe(self):
        self.config["compilerOptions"]["baseUrl"] = "../.."
        self.update_config()
        self.put("platform/test/src/index.ts", 'import "@example/core";')
        self.assertIn("packages/core/src/index.ts", self.paths())
        self.assertIn("scoped-baseurl-lookup-unresolved", self.codes())
        self.assertNotIn("build-path-unsafe", self.codes())

    def test_child_include_replaces_inherited_include(self):
        self.put("platform/base.json", {"include": ["other/**/*.ts"]})
        self.put("platform/other/ignored.ts", "export const ignored = 1;")
        self.config["extends"] = "../base.json"
        self.update_config()
        self.assertNotIn("platform/other/ignored.ts", self.paths())

    def test_inherited_include_and_output_paths_retain_origin(self):
        self.put("platform/base.json", {"compilerOptions": {"rootDir": ".", "outDir": "../.cache/base"}, "include": ["test/src/**/*.ts"]})
        self.config = {"extends": "../base.json"}
        self.update_config()
        build = self.build()
        self.assertEqual(build["output_root"], ".cache/base")
        self.assertIn("test/src/index.js", {row["path"] for row in build["expected_outputs"]})

    def test_config_cycle_is_unresolved(self):
        self.config["extends"] = "./tsconfig.json"
        self.update_config()
        self.assertIn("config-inheritance-cycle", self.codes())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_config_array_extends_is_unresolved(self):
        self.config["extends"] = ["./base.json"]
        self.update_config()
        self.assertIn("config-extends-unsupported", self.codes())

    def test_noemit_never_predicts_files(self):
        self.config["compilerOptions"]["noEmit"] = True
        self.update_config()
        self.assertEqual(self.build()["output_mode"], "no-emit")
        self.assertEqual(self.build()["expected_outputs"], [])

    def test_declaration_only_never_predicts_javascript(self):
        self.config["compilerOptions"].update({"emitDeclarationOnly": True, "declaration": True})
        self.update_config()
        self.assertEqual(self.build()["output_mode"], "declarations")
        self.assertEqual({row["kind"] for row in self.build()["expected_outputs"]}, {"declaration"})

    def test_declaration_inputs_do_not_predict_outputs(self):
        self.put("platform/test/src/ambient.d.ts", "declare const example: string;")
        self.assertFalse(any("ambient" in row["path"] for row in self.build()["expected_outputs"]))

    def test_runtime_test_output_is_distinguished(self):
        self.put("platform/test/src/example-runtime.test.ts", "export const tested = true;")
        rows = [row for row in self.build()["expected_outputs"] if row["kind"] == "runtime-test"]
        self.assertEqual([row["path"] for row in rows], ["platform/test/src/example-runtime.test.js"])

    def test_missing_relative_import_blocks_prediction(self):
        self.put("platform/test/src/index.ts", 'import "./missing.js";')
        self.assertIn("import-target-unresolved", self.codes())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_conditional_workspace_export_blocks_prediction(self):
        self.manifest["exports"]["."] = {"import": "./src/index.ts"}
        self.put("packages/core/package.json", self.manifest)
        self.put("platform/test/src/index.ts", 'import "@example/core";')
        self.assertIn("workspace-export-unsupported", self.codes())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_node10_does_not_assume_workspace_exports(self):
        self.config["compilerOptions"]["moduleResolution"] = "Node10"
        self.update_config()
        self.put("platform/test/src/index.ts", 'import "@example/core";')
        self.assertIn("workspace-resolution-mode-unresolved", self.codes())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_duplicate_workspace_name_is_unresolved_and_binds_both(self):
        self.put("packages/other/package.json", self.manifest)
        self.assertIn("workspace-name-duplicate", self.codes())
        self.assertIn("packages/other/package.json", self.paths())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_workspace_export_escape_is_rejected(self):
        self.manifest["exports"]["."] = "./../../platform/test/src/index.ts"
        self.put("packages/core/package.json", self.manifest)
        self.put("platform/test/src/index.ts", 'import "@example/core";')
        self.assertIn("workspace-export-unsafe", self.codes())

    def test_symlink_input_never_followed(self):
        self.put("outside/private.ts", "SECRET_SENTINEL")
        (self.root / "platform/test/src/link.ts").symlink_to(self.root / "outside/private.ts")
        result = self.inventory()
        self.assertNotIn("outside/private.ts", self.paths(result))
        self.assertEqual(self.build(result)["prediction_status"], "unresolved")
        self.assertNotIn("SECRET_SENTINEL", json.dumps(result))

    def test_extensionless_secrets_source_is_distinct_from_private_directory(self):
        self.put("platform/test/src/index.ts", 'import "./secrets";')
        self.put("platform/test/src/secrets.ts", "export const describeSecret = true;")
        self.put("platform/test/src/secrets/index.ts", "PRIVATE_SENTINEL")
        result = self.inventory()
        self.assertIn("platform/test/src/secrets.ts", self.paths(result))
        self.assertNotIn("platform/test/src/secrets/index.ts", self.paths(result))
        self.assertNotIn("build-path-unsafe", self.codes(result))
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_dotenv_import_never_read(self):
        self.put("platform/test/src/.env.production", "SECRET_SENTINEL")
        self.put("platform/test/src/index.ts", 'import "./.env.production";')
        result = self.inventory()
        self.assertNotIn("platform/test/src/.env.production", self.paths(result))
        self.assertIn("build-path-unsafe", self.codes(result))

    def test_parent_traversal_outside_root_rejected(self):
        self.put("platform/test/src/index.ts", 'import "../../../../outside.ts";')
        self.assertIn("build-path-unsafe", self.codes())

    def test_all_competing_extension_candidates_are_bound(self):
        self.put("platform/test/src/value.js", "export const value = 2;")
        result = self.inventory()
        self.assertIn("platform/test/src/value.js", self.paths(result))
        self.assertIn("platform/test/src/value.ts", self.paths(result))
        self.assertIn("import-resolution-ambiguous", self.codes(result))
        self.assertEqual(self.build(result)["prediction_status"], "unresolved")

    def test_dotted_extensionless_basename_is_resolved(self):
        self.put("platform/test/src/index.ts", 'export { value } from "./value.types";')
        self.put("platform/test/src/value.types.ts", "export const value = 1;")
        self.assertIn("platform/test/src/value.types.ts", self.paths())

    def test_multiline_and_static_dynamic_imports_are_observed(self):
        self.put("platform/test/src/index.ts", 'import {\\n core\\n} from "@example/core";\\nconst module = import("./value.js");'.replace("\\n", "\n"))
        paths = self.paths()
        self.assertIn("packages/core/src/index.ts", paths)
        self.assertIn("platform/test/src/value.ts", paths)

    def test_long_named_import_list_is_not_silently_omitted(self):
        names = ",".join("item" + str(index) for index in range(150))
        self.put("platform/test/src/index.ts", 'import {' + names + '} from "@example/core";')
        self.assertIn("packages/core/src/index.ts", self.paths())

    def test_unrelated_template_literal_is_not_a_dynamic_import(self):
        self.put("platform/test/src/index.ts", "const text = " + chr(96) + "hello" + chr(96) + ";")
        self.assertNotIn("dynamic-import-unresolved", self.codes())

    def test_comments_do_not_create_imports(self):
        self.put("platform/test/src/index.ts", '// import "./missing";\\n/* export { x } from "external"; */'.replace("\\n", "\n"))
        self.assertNotIn("import-target-unresolved", self.codes())

    def test_dynamic_expression_import_blocks_prediction(self):
        self.put("platform/test/src/index.ts", "const result = import(process.argv[2]);")
        self.assertIn("dynamic-import-unresolved", self.codes())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_unknown_emission_option_blocks_prediction(self):
        self.config["compilerOptions"]["outFile"] = "../../.cache/bundle.js"
        self.update_config()
        self.assertIn("compiler-option-unsupported", self.codes())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_outside_rootdir_is_unresolved(self):
        self.config["compilerOptions"]["rootDir"] = "src"
        self.update_config()
        self.put("platform/test/src/index.ts", 'import "@example/core";')
        self.assertIn("source-outside-rootdir", self.codes())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_new_root_member_changes_inventory(self):
        before = self.inventory()
        self.put("platform/test/src/new.ts", "export const added = true;")
        self.assertNotEqual(before["inventory_digest"], self.inventory()["inventory_digest"])

    def test_stale_graph_is_rejected(self):
        graph = discover_callers(self.root, self.workflow)
        self.package["scripts"]["check"] = "tsc -p platform/test/other.json"
        self.put("package.json", self.package)
        with self.assertRaisesRegex(SourceFailure, "build-graph-stale"):
            self.inventory(graph)

    def test_empty_scope_rejected(self):
        self.package["scripts"]["check"] = "node scripts/check.mjs"
        self.put("scripts/check.mjs", "export const check = true;")
        self.put("package.json", self.package)
        with self.assertRaisesRegex(SourceFailure, "build-scope-empty"):
            self.inventory()

    def test_unsupported_tool_never_silently_omitted(self):
        self.package["scripts"]["check"] += " && vite build"
        self.put("package.json", self.package)
        with self.assertRaisesRegex(SourceFailure, "build-invocation-unsupported"):
            self.inventory()

    def test_hard_budget_never_returns_partial_inventory(self):
        with patch.object(builds, "MAX_FILES", 2):
            with self.assertRaisesRegex(SourceFailure, "build-limit-exceeded"):
                self.inventory()

    def test_token_budget_never_returns_partial_inventory(self):
        with patch.object(builds, "MAX_TOKENS", 2):
            with self.assertRaisesRegex(SourceFailure, "build-limit-exceeded"):
                self.inventory()

    def test_invalid_compiler_option_type_blocks_prediction(self):
        self.config["compilerOptions"]["declaration"] = "false"
        self.update_config()
        self.assertIn("build-config-invalid", self.codes())
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_unused_malformed_paths_entries_block_prediction(self):
        for value in ("bad", [17], [], [""], ["src/**/index.ts"]):
            with self.subTest(value=value):
                self.config["compilerOptions"]["paths"] = {"unused": value}
                self.update_config()
                result = self.inventory()
                self.assertIn("paths-mapping-unsupported", self.codes(result))
                self.assertEqual(self.build(result)["prediction_status"], "unresolved")

    def test_fifo_source_never_blocks_or_reads(self):
        os.mkfifo(self.root / "platform/test/src/pipe.ts")
        self.assertEqual(self.build()["prediction_status"], "unresolved")

    def test_duplicate_json_keys_are_rejected(self):
        self.put("platform/test/tsconfig.json", '{"include":[],"include":["src/**/*.ts"]}')
        self.assertIn("build-document-invalid", self.codes())

    def test_output_is_normalized_without_literal_source_or_specifiers(self):
        self.put("platform/test/src/index.ts", 'const credential = "SENSITIVE_VALUE"; import "https://secret.invalid/token";')
        text = json.dumps(self.inventory())
        self.assertNotIn("SENSITIVE_VALUE", text)
        self.assertNotIn("secret.invalid", text)

    def test_excluded_root_can_remain_imported_dependency(self):
        self.config["exclude"] = ["src/value.ts"]
        self.update_config()
        result = self.inventory()
        source = next(row for row in result["sources"] if row["path"] == "platform/test/src/value.ts")
        self.assertNotIn(source["id"], self.build(result)["root_source_ids"])
        self.assertIn(source["id"], {row["source_id"] for row in self.build(result)["expected_outputs"]})
        self.assertIn("exclude-semantics-unresolved", self.codes(result))

    def test_source_only_scan_creates_no_output_directory(self):
        self.inventory()
        self.assertFalse((self.root / ".cache").exists())


if __name__ == "__main__":
    unittest.main()
