#!/usr/bin/env python3
"""Positive and adversarial local artifact accounting tests; never run builds."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.build-artifacts-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Test exact bounded artifact membership, source freshness and filesystem rejection boundaries.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import build_artifacts as artifacts
from source_inventory import SourceFailure, canonical, digest

REPO = Path(__file__).resolve().parents[4]


class BuildArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="build-artifact-test-")
        self.root = Path(self.temp.name) / "source"
        self.output = Path(self.temp.name) / "artifact"
        self.root.mkdir()
        self.output.mkdir()
        self.sources = {}
        source = self.source("src/index.ts", "export const value = 1;\n")
        config = self.source("tsconfig.json", "{}")
        self.build = {"id": digest(b"build"), "config_source_id": config,
                      "output_mode": "javascript", "prediction_status": "bounded", "output_root": "dist",
                      "expected_outputs": [{"path": "src/index.js", "source_id": source, "kind": "javascript"}]}
        self.put("src/index.js", "exports.value = 1;\n")

    def tearDown(self):
        self.temp.cleanup()

    def source(self, path, raw):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw.encode() if isinstance(raw, str) else raw)
        identity = digest(path.encode())
        self.sources[identity] = {"id": identity, "path": path, "digest": digest(target.read_bytes())}
        return identity

    def put(self, path, raw):
        target = self.output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw.encode() if isinstance(raw, str) else raw)
        return target

    def inventory(self):
        value = {"schema": "source-build-inventory/v1", "sources": sorted(self.sources.values(), key=lambda row: row["id"]),
                 "builds": [deepcopy(self.build)]}
        value["inventory_digest"] = digest(canonical(value))
        return value

    def bind(self, inventory=None):
        return artifacts.bind_artifact(self.root, inventory or self.inventory(), self.build["id"], self.output)

    def failure(self, code):
        with self.assertRaisesRegex(SourceFailure, "^" + code + "$"):
            self.bind()

    def fixture_generator(self, runtime=False):
        """Copy source text as inert data; independently construct expected bytes."""
        path = "platform/server/tests/run-runtime-tests.mjs" if runtime else "scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs"
        config = "platform/server/tsconfig.runtime-test.json" if runtime else "platform/server/tsconfig.image.json"
        raw = (REPO / path).read_text()
        self.build["output_root"] = ".cache/example"
        raw = re.sub(r'^const runtimeRoot = "[^"]+";', 'const runtimeRoot = ".cache/example";', raw, flags=re.M)
        raw = re.sub(r'const coreModules = \[[^\]]*\];', 'const coreModules = [];', raw)
        calls = list(re.finditer(r'^writePackageShim\(.*?^\}\);\n', raw, re.M | re.S))
        for match in reversed(calls):
            raw = raw[:match.start()] + raw[match.end():]
        point = raw.index('const coreModules = [];') + len('const coreModules = [];')
        raw = raw[:point] + '\n\nwritePackageShim("@example/core", {\n  ".": join(runtimeRoot, "src/index.js"),\n});\n' + raw[point:]
        self.source(path, raw)
        self.build["config_source_id"] = self.source(config, "{}")
        self.put("node_modules/@example/core/package.json", json.dumps({"name": "@example/core", "type": "commonjs", "exports": {".": "./index.js"}}, indent=2) + "\n")
        self.put("node_modules/@example/core/index.js", 'module.exports = require("../../../src/index.js");\n')
        if runtime:
            self.add_runtime("platform/server/tests/example-runtime.test.js")
        return path

    def add_runtime(self, path):
        source = self.source(path[:-3] + ".ts", "export {};\n")
        self.build["expected_outputs"].append({"path": path, "source_id": source, "kind": "runtime-test"})
        self.put(path, "// inert compiled test fixture\n")

    def test_positive_digest_records_actual_bytes_without_provenance(self):
        result = self.bind()
        self.assertEqual("complete", result["artifact_verdict"])
        self.assertEqual(result, self.bind())
        self.assertEqual([{"path": "src/index.js", "digest": digest(b"exports.value = 1;\n"), "bytes": 19}], result["files"])
        self.assertFalse(result["authorized"])
        self.assertEqual("unproven", result["provenance"])
        self.assertEqual("blocked", result["qualification_verdict"])
        self.assertEqual("blocked", result["source_closure"])
        self.assertEqual(result["artifact_digest"], digest(canonical({key: value for key, value in result.items() if key != "artifact_digest"})))

    def test_output_bytes_change_invalidates_artifact_identity(self):
        before = self.bind()
        self.put("src/index.js", "exports.value = 2;\n")
        after = self.bind()
        self.assertNotEqual(before["artifact_digest"], after["artifact_digest"])
        self.assertEqual(before["inventory_digest"], after["inventory_digest"])
        self.assertEqual("complete", after["artifact_verdict"])
        self.assertEqual("unproven", after["provenance"])

    def test_missing_output_is_incomplete(self):
        (self.output / "src/index.js").unlink()
        self.assertIn("artifact-output-missing", self.bind()["findings"])

    def test_unexpected_output_is_incomplete(self):
        self.put("src/stale.js", "old")
        result = self.bind()
        self.assertEqual("incomplete", result["artifact_verdict"])
        self.assertIn("artifact-output-unexpected", result["findings"])

    def test_arbitrary_manifest_cannot_declare_extra_files_expected(self):
        self.put("manifest.json", json.dumps({"files": ["src/stale.js"]}))
        self.put("src/stale.js", "old")
        self.assertIn("artifact-output-unexpected", self.bind()["findings"])

    def test_changed_source_rejects_stale_inventory(self):
        inventory = self.inventory()
        (self.root / "src/index.ts").write_text("changed")
        with self.assertRaisesRegex(SourceFailure, "artifact-source-stale"):
            self.bind(inventory)

    def test_missing_source_rejects(self):
        (self.root / "src/index.ts").unlink()
        self.failure("artifact-input-unreadable")

    def test_inventory_mutation_without_digest_rejects(self):
        inventory = self.inventory()
        inventory["builds"][0]["expected_outputs"] = []
        with self.assertRaisesRegex(SourceFailure, "artifact-inventory-invalid"):
            self.bind(inventory)

    def test_unknown_build_rejects(self):
        with self.assertRaisesRegex(SourceFailure, "artifact-build-unknown"):
            artifacts.bind_artifact(self.root, self.inventory(), digest(b"unknown"), self.output)

    def test_duplicate_build_rejects(self):
        inventory = self.inventory()
        inventory["builds"].append(deepcopy(self.build))
        inventory["inventory_digest"] = digest(canonical({key: value for key, value in inventory.items() if key != "inventory_digest"}))
        with self.assertRaisesRegex(SourceFailure, "artifact-inventory-invalid"):
            self.bind(inventory)

    def test_no_emit_build_does_not_demand_or_accept_outputs(self):
        self.build["output_mode"] = "no-emit"
        self.failure("artifact-no-emit-build")

    def test_unresolved_projection_cannot_claim_exact_membership(self):
        self.build["prediction_status"] = "unresolved"
        self.failure("artifact-prediction-unresolved")

    def test_declaration_only_accounting_never_runtime_qualifies(self):
        (self.output / "src/index.js").unlink()
        self.put("src/index.d.ts", "export declare const value = 1;\n")
        self.build["output_mode"] = "declarations"
        self.build["expected_outputs"][0].update(path="src/index.d.ts", kind="declaration")
        result = self.bind()
        self.assertEqual("complete", result["artifact_verdict"])
        self.assertEqual([], result["runtime_tests"])
        self.assertEqual("blocked", result["qualification_verdict"])

    def test_duplicate_expected_path_rejects(self):
        self.build["expected_outputs"].append(deepcopy(self.build["expected_outputs"][0]))
        self.failure("artifact-inventory-invalid")

    def test_foreign_source_mapping_rejects(self):
        self.build["expected_outputs"][0]["source_id"] = digest(b"foreign")
        self.failure("artifact-inventory-invalid")

    def test_source_fallback_path_rejects(self):
        self.put("src/fallback.ts", "export {};")
        self.assertIn("artifact-source-fallback-forbidden", self.bind()["findings"])

    def test_unsafe_expected_path_rejects(self):
        self.build["expected_outputs"][0]["path"] = "../escape.js"
        self.failure("artifact-path-unsafe")

    def test_artifact_symlink_file_rejects(self):
        (self.output / "escape.js").symlink_to(self.root / "src/index.ts")
        self.failure("artifact-file-kind-unsupported")

    def test_artifact_symlink_directory_rejects(self):
        (self.output / "escape").symlink_to(self.root, target_is_directory=True)
        self.failure("artifact-file-kind-unsupported")

    def test_artifact_root_symlink_rejects(self):
        link = Path(self.temp.name) / "linked"
        link.symlink_to(self.output, target_is_directory=True)
        self.output = link
        self.failure("artifact-input-unreadable")

    def test_artifact_ancestor_symlink_rejects(self):
        link = Path(self.temp.name) / "linked"
        link.symlink_to(self.output.parent, target_is_directory=True)
        self.output = link / self.output.name
        self.failure("artifact-input-unreadable")

    def test_source_symlink_rejects(self):
        path = self.root / "src/index.ts"
        path.unlink()
        path.symlink_to(self.output / "src/index.js")
        self.failure("artifact-input-unreadable")

    def test_private_artifact_root_rejects_before_walking(self):
        self.output = Path(self.temp.name) / ".ssh"
        self.output.mkdir()
        (self.output / "id_rsa").write_text("DO-NOT-EXPOSE")
        self.failure("artifact-path-unsafe")

    def test_fifo_rejects_without_opening_or_hanging(self):
        os.mkfifo(self.output / "fifo")
        self.failure("artifact-file-kind-unsupported")

    def test_private_paths_reject_before_content_read(self):
        for name in (".env", ".env.production", ".ENV.LOCAL", "credentials/config", "key.pem", ".npmrc"):
            with self.subTest(name=name):
                target = self.put(name, "DO-NOT-EXPOSE")
                self.failure("artifact-path-unsafe")
                target.unlink()
                if target.parent != self.output:
                    target.parent.rmdir()

    def test_unsafe_filename_rejects_without_exposure(self):
        self.put("unsafe secret=.js", "DO-NOT-EXPOSE")
        self.failure("artifact-path-unsafe")

    def test_file_size_limit_rejects_whole_collection(self):
        with patch.object(artifacts, "MAX_FILE_BYTES", 1):
            self.failure("artifact-limit-exceeded")

    def test_total_size_limit_rejects_whole_collection(self):
        with patch.object(artifacts, "MAX_TOTAL_BYTES", 1):
            self.failure("artifact-limit-exceeded")

    def test_member_limit_rejects_whole_collection(self):
        with patch.object(artifacts, "MAX_FILES", 1):
            self.failure("artifact-inventory-invalid")
        with patch.object(artifacts, "MAX_FILES", 2):
            self.put("extra/x.js", "x")
            self.failure("artifact-limit-exceeded")

    def test_depth_limit_rejects_whole_collection(self):
        with patch.object(artifacts, "MAX_DEPTH", 0):
            self.failure("artifact-limit-exceeded")

    def test_source_generated_shims_match_independent_expected_bytes(self):
        self.fixture_generator()
        result = self.bind()
        self.assertEqual("complete", result["artifact_verdict"])
        self.assertEqual(1, len(result["generator_sources"]))
        self.assertEqual("src/index.js", result["shim_targets"][0]["target_path"])
        self.assertEqual("node_modules/@example/core/index.js", result["shim_targets"][0]["shim_path"])

    def test_missing_generated_shim_rejects(self):
        self.fixture_generator()
        (self.output / "node_modules/@example/core/index.js").unlink()
        self.assertIn("artifact-output-missing", self.bind()["findings"])

    def test_wrong_forwarding_target_rejects(self):
        self.fixture_generator()
        self.put("node_modules/@example/core/index.js", 'module.exports = require("../../../../outside.js");\n')
        self.assertIn("artifact-generated-bytes-mismatch", self.bind()["findings"])

    def test_missing_expected_shim_target_rejects(self):
        self.fixture_generator()
        (self.output / "src/index.js").unlink()
        self.assertIn("artifact-shim-target-missing", self.bind()["findings"])

    def test_manifest_target_escape_rejects(self):
        self.fixture_generator()
        self.put("node_modules/@example/core/package.json", '{"main":"../../../../outside.js"}')
        self.assertIn("artifact-manifest-target-unsafe", self.bind()["findings"])

    def test_manifest_source_fallback_rejects(self):
        self.fixture_generator()
        self.put("node_modules/@example/core/package.json", '{"exports":{".":"./index.ts"}}')
        self.assertIn("artifact-source-fallback-forbidden", self.bind()["findings"])

    def test_manifest_missing_target_rejects(self):
        self.fixture_generator()
        self.put("node_modules/@example/core/package.json", '{"exports":{".":"./missing.js"}}')
        self.assertIn("artifact-manifest-target-missing", self.bind()["findings"])

    def test_manifest_duplicate_key_rejects(self):
        self.fixture_generator()
        self.put("node_modules/@example/core/package.json", '{"main":"./index.js","main":"./other.js"}')
        self.assertIn("artifact-manifest-invalid", self.bind()["findings"])

    def test_changed_helper_is_unsupported_even_if_output_matches(self):
        path = self.fixture_generator()
        self.source(path, (self.root / path).read_text().replace('relativePath.startsWith(".")', 'relativePath.startsWith("..")'))
        self.assertIn("artifact-generator-unsupported", self.bind()["findings"])

    def test_computed_root_cannot_erase_generator_obligation(self):
        path = self.fixture_generator()
        self.source(path, (self.root / path).read_text().replace('".cache/example"', '".cache/" + "example"'))
        self.assertIn("artifact-generator-unsupported", self.bind()["findings"])

    def test_missing_required_generator_is_explicit(self):
        self.build["config_source_id"] = self.source("platform/server/tsconfig.image.json", "{}")
        self.assertIn("artifact-generator-source-missing", self.bind()["findings"])

    def test_conditional_generator_call_is_unsupported(self):
        path = self.fixture_generator()
        self.source(path, (self.root / path).read_text().replace('writePackageShim("@example', 'if (false) {\nwritePackageShim("@example').replace('});\n', '});\n}\n', 1))
        self.assertIn("artifact-generator-unsupported", self.bind()["findings"])

    def test_duplicate_generator_call_is_unsupported(self):
        path = self.fixture_generator()
        raw = (self.root / path).read_text()
        call = re.search(r'^writePackageShim\(.*?^\}\);\n', raw, re.M | re.S).group()
        self.source(path, raw.replace(call, call + call))
        self.assertIn("artifact-generator-unsupported", self.bind()["findings"])

    def test_runtime_membership_matches_immediate_runner_directory(self):
        self.fixture_generator(runtime=True)
        self.add_runtime("platform/server/tests/nested/other-runtime.test.js")
        self.add_runtime("products/other/tests/other-runtime.test.js")
        result = self.bind()
        self.assertEqual("complete", result["artifact_verdict"])
        self.assertEqual(["platform/server/tests/example-runtime.test.js"], result["runtime_tests"])

    def test_stale_runtime_test_member_rejects(self):
        self.fixture_generator(runtime=True)
        self.put("platform/server/tests/stale-runtime.test.js", "old")
        self.assertIn("artifact-runtime-membership-mismatch", self.bind()["findings"])

    def test_missing_runtime_test_member_rejects(self):
        self.fixture_generator(runtime=True)
        (self.output / "platform/server/tests/example-runtime.test.js").unlink()
        self.assertIn("artifact-runtime-membership-mismatch", self.bind()["findings"])

    def test_empty_runtime_selection_rejects(self):
        self.fixture_generator(runtime=True)
        (self.output / "platform/server/tests/example-runtime.test.js").unlink()
        self.build["expected_outputs"] = self.build["expected_outputs"][:1]
        self.assertIn("artifact-runtime-tests-empty", self.bind()["findings"])

    def test_runtime_selector_change_is_unsupported(self):
        path = self.fixture_generator(runtime=True)
        self.source(path, (self.root / path).read_text().replace('endsWith("-runtime.test.js")', 'endsWith(".js")'))
        self.assertIn("artifact-generator-unsupported", self.bind()["findings"])

    def test_all_current_selected_generator_grammars_are_supported(self):
        counts = {"scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs": (54, 35),
                  "platform/server/tests/run-runtime-tests.mjs": (29, 21),
                  "products/kanbien-platform/tests/run-runtime-tests.mjs": (38, 26)}
        for path, expected in counts.items():
            with self.subTest(path=path):
                _, generated, targets, _ = artifacts.literal_generator((REPO / path).read_bytes())
                self.assertEqual(expected, (len(generated), len(targets)))

    def test_result_matches_versioned_closed_schema(self):
        import yaml
        from jsonschema import Draft202012Validator
        schema = yaml.safe_load((REPO / "infra/04.deploy/contracts/release-control/v1/source-build-artifact.schema.yml").read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        result = self.bind()
        self.assertEqual([], list(validator.iter_errors(result)))
        result["authorized"] = True
        self.assertTrue(list(validator.iter_errors(result)))


if __name__ == "__main__":
    unittest.main()
