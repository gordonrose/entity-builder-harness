"""Compile inert fixtures with the verified toolchain; never execute emitted code."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-typescript-observer
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify genuine compiler resolution, diagnostics, emissions and rejected observation boundaries.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


DIRECTORY = Path(__file__).resolve().parent
DRIVER = DIRECTORY / "typescript_observer.mjs"
FIXTURES = DIRECTORY / "fixtures/local-builds/compiler"


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class TypeScriptObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node = os.environ.get("RELEASE_CONTROL_NODE")
        typescript = os.environ.get("RELEASE_CONTROL_TYPESCRIPT_ROOT")
        if not node or not typescript:
            if os.environ.get("RELEASE_CONTROL_REQUIRE_TYPESCRIPT_TESTS") == "1":
                raise RuntimeError("Locked compiler fixture toolchain was not supplied")
            raise unittest.SkipTest("Genuine compiler fixtures require the verified local Node/TypeScript toolchain")
        cls.node = Path(node).resolve(strict=True)
        cls.typescript = Path(typescript).resolve(strict=True)
        if not cls.node.is_file() or not (cls.typescript / "lib/typescript.js").is_file():
            raise RuntimeError("Locked compiler fixture toolchain is incomplete")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="typescript-observer-fixture-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / "snapshot"
        shutil.copytree(FIXTURES / "positive", self.root)
        shutil.copytree(self.typescript, self.root / "node_modules/typescript")
        self.receipt = self.directory / "observation.json"

    def config(self, **changes):
        target = self.root / "tsconfig.json"
        document = json.loads(target.read_text())
        document["compilerOptions"].update(changes)
        target.write_text(json.dumps(document))

    def invoke(self, config="tsconfig.json", extra=()):
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.directory), "LANG": "C.UTF-8"}
        command = [str(self.node), str(DRIVER), "--root", str(self.root), "--config", config,
                   "--output", str(self.receipt), *extra]
        completed = subprocess.run(command, cwd=self.root, env=env, text=True,
                                   capture_output=True, timeout=45, check=False)
        self.assertEqual(completed.stderr, "", completed.stderr)
        status = json.loads(completed.stdout)
        result = json.loads(self.receipt.read_text()) if self.receipt.exists() else None
        return completed.returncode, status, result

    def passed(self, **kwargs):
        code, status, result = self.invoke(**kwargs)
        self.assertEqual(code, 0, result or status)
        self.assertEqual(status["verdict"], "passed")
        self.assertEqual(result["verdict"], "passed")
        self.assertEqual(result["findings"], [])
        return result

    def rejected(self, finding=None, **kwargs):
        code, status, result = self.invoke(**kwargs)
        self.assertEqual(code, 1, result or status)
        self.assertEqual(status["verdict"], "failed")
        if finding:
            codes = [row["code"] for row in result["findings"]] if result else [status.get("code")]
            self.assertIn(finding, codes)
        return result

    def test_real_compiler_emits_expected_javascript_and_actual_hashes(self):
        result = self.passed()
        self.assertEqual(result["node_version"], "22.23.3")
        self.assertEqual(result["typescript_version"], "5.9.3")
        self.assertEqual({row["path"] for row in result["outputs"]},
                         {".cache/output/index.js", ".cache/output/math.js"})
        for row in result["outputs"]:
            raw = (self.root / row["path"]).read_bytes()
            self.assertEqual(row["digest"], digest(raw))
            self.assertEqual(row["bytes"], len(raw))
        self.assertIn('require("./math")', (self.root / ".cache/output/index.js").read_text())

    def test_actual_inputs_include_config_compiler_package_and_default_libraries(self):
        result = self.passed()
        paths = {row["path"] for row in result["inputs"]}
        self.assertTrue({"tsconfig.json", "src/index.ts", "src/math.ts",
                         "node_modules/typescript/lib/typescript.js", "node_modules/typescript/package.json",
                         "node_modules/typescript/lib/lib.es2022.full.d.ts"}.issubset(paths))
        for row in result["inputs"]:
            self.assertEqual(row["digest"], digest((self.root / row["path"]).read_bytes()))

    def test_relative_import_resolution_is_observed(self):
        result = self.passed()
        record = next(row for row in result["resolutions"] if row["from"] == "src/index.ts")
        self.assertEqual(record, {"from": "src/index.ts", "specifier_digest": digest(b"./math"),
                                  "mode": "default", "resolved_path": "src/math.ts", "is_external": False})

    def test_observation_digest_uses_canonical_json(self):
        result = self.passed()
        observed = result.pop("observation_digest")
        raw = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        self.assertEqual(observed, digest(raw))

    def test_genuine_type_error_fails_without_emission_or_source_excerpt(self):
        (self.root / "src/index.ts").write_bytes((FIXTURES / "negative/src/index.ts").read_bytes())
        result = self.rejected()
        self.assertTrue(any(row["code"] == 2322 for row in result["diagnostics"]))
        self.assertEqual(result["outputs"], [])
        self.assertNotIn("deliberate-type-error", self.receipt.read_text())

    def test_no_emit_retains_typecheck_semantics(self):
        self.config(noEmit=True)
        result = self.passed()
        self.assertTrue(result["no_emit"])
        self.assertEqual(result["outputs"], [])

    def test_no_emit_still_fails_a_type_error(self):
        self.config(noEmit=True)
        (self.root / "src/index.ts").write_text('export const broken: number = "wrong";')
        result = self.rejected()
        self.assertTrue(any(row["code"] == 2322 for row in result["diagnostics"]))
        self.assertEqual(result["outputs"], [])

    def test_no_emit_on_error_false_preserves_failure_and_real_emissions(self):
        self.config(noEmitOnError=False)
        (self.root / "src/index.ts").write_text('export const broken: number = "wrong";')
        result = self.rejected()
        self.assertTrue(result["outputs"])
        self.assertTrue(any(row["code"] == 2322 for row in result["diagnostics"]))

    def test_missing_dependency_is_a_real_compiler_diagnostic(self):
        (self.root / "src/index.ts").write_text('export { absent } from "missing-external-package";')
        result = self.rejected()
        self.assertTrue(any(row["code"] == 2307 for row in result["diagnostics"]))
        self.assertTrue(any(row["resolved_path"] is None for row in result["resolutions"]))
        self.assertEqual(result["outputs"], [])

    def test_jsonc_extends_and_paths_use_compiler_semantics(self):
        original = json.loads((self.root / "tsconfig.json").read_text())
        original["compilerOptions"].update(baseUrl=".", paths={"fixture-math": ["src/math.ts"]})
        (self.root / "base.json").write_text(json.dumps(original))
        (self.root / "tsconfig.json").write_text('{ // real JSONC parsing\n"extends":"./base.json",}\n')
        (self.root / "src/index.ts").write_text('export { twice } from "fixture-math";')
        result = self.passed()
        self.assertIn("base.json", {row["path"] for row in result["inputs"]})
        self.assertTrue(any(row["resolved_path"] == "src/math.ts" for row in result["resolutions"]))

    def test_nodenext_preserves_import_and_require_export_conditions(self):
        dependency = self.root / "node_modules/conditional-fixture"
        dependency.mkdir()
        (dependency / "package.json").write_text(json.dumps({"name": "conditional-fixture", "version": "1.0.0",
            "exports": {".": {"import": "./import.d.ts", "require": "./require.d.ts"}}}))
        (dependency / "import.d.ts").write_text('export const selected: "import";')
        (dependency / "require.d.ts").write_text('export const selected: "require";')
        for extension, expected in (("mts", "import"), ("cts", "require")):
            (self.root / ("src/conditional." + extension)).write_text(
                'import { selected } from "conditional-fixture"; export const value: "' + expected + '" = selected;')
        document = json.loads((self.root / "tsconfig.json").read_text())
        document["compilerOptions"].update(module="NodeNext", moduleResolution="NodeNext")
        document["include"] = ["src/**/*"]
        (self.root / "tsconfig.json").write_text(json.dumps(document))
        result = self.passed()
        rows = [row for row in result["resolutions"] if row["from"].startswith("src/conditional.")]
        self.assertEqual({(row["mode"], row["resolved_path"]) for row in rows},
                         {("import", "node_modules/conditional-fixture/import.d.ts"),
                          ("require", "node_modules/conditional-fixture/require.d.ts")})

    def test_node10_baseurl_builtin_probes_preserve_ambient_resolution(self):
        # The selected runtime builds use Node10, despite the separately
        # covered NodeNext import/require conditions above.
        self.config(baseUrl=".")
        (self.root / "src/node-builtins.d.ts").write_text(
            'declare module "node:crypto" { export function randomUUID(): string; }')
        (self.root / "src/index.ts").write_text(
            'import { randomUUID } from "node:crypto"; export const createId = randomUUID;')
        result = self.passed()
        self.assertIn("src/node-builtins.d.ts", {row["path"] for row in result["inputs"]})
        self.assertTrue(any(row["specifier_digest"] == digest(b"node:crypto")
                            for row in result["resolutions"]))
        self.assertFalse(any(":" in row["path"] for row in result["inputs"]))

    def test_explicit_unsafe_source_name_still_fails_before_reading(self):
        source = self.root / "src/node:private.ts"
        source.write_text('export const secret = "do-not-read-this-explicit-source";')
        document = json.loads((self.root / "tsconfig.json").read_text())
        document.pop("include", None)
        document["files"] = ["src/node:private.ts"]
        (self.root / "tsconfig.json").write_text(json.dumps(document))
        result = self.rejected("observer-input-path-unsafe")
        self.assertEqual(result["outputs"], [])
        self.assertNotIn("do-not-read-this-explicit-source", self.receipt.read_text())

    def test_fifo_input_is_rejected_without_reading_or_hanging(self):
        os.mkfifo(self.root / "src/pipe.ts")
        self.rejected("observer-input-kind-unsupported")

    def test_oversized_source_is_rejected_before_compilation(self):
        (self.root / "src/large.ts").write_bytes(b" " * (16 * 1024 * 1024 + 1))
        self.rejected("observer-limit-exceeded")

    def test_declaration_and_buildinfo_are_observed_outside_declaration_directory(self):
        self.config(composite=True, declaration=True, emitDeclarationOnly=True)
        result = self.passed()
        self.assertEqual({row["path"] for row in result["outputs"]},
                         {".cache/output/index.d.ts", ".cache/output/math.d.ts", ".cache/tsconfig.tsbuildinfo"})

    def test_source_maps_are_actual_outputs(self):
        self.config(sourceMap=True)
        result = self.passed()
        self.assertEqual(len(result["outputs"]), 4)
        self.assertTrue(any(row["path"].endswith(".js.map") for row in result["outputs"]))

    def test_output_escape_is_rejected_before_writing_outside_snapshot(self):
        self.config(outDir="../escaped-output")
        self.rejected("observer-output-path-unsafe")
        self.assertFalse((self.directory / "escaped-output").exists())

    def test_output_outside_cache_is_rejected(self):
        self.config(outDir="src")
        self.rejected()
        self.assertFalse((self.root / "src/index.js").exists())

    def test_preexisting_emitted_output_is_never_overwritten(self):
        output = self.root / ".cache/output/index.js"
        output.parent.mkdir(parents=True)
        output.write_text("preserve-existing-output")
        self.rejected("observer-output-exists")
        self.assertEqual(output.read_text(), "preserve-existing-output")

    def test_prior_incremental_cache_cannot_be_reused(self):
        self.config(composite=True, declaration=True, emitDeclarationOnly=True)
        self.passed()
        self.receipt = self.directory / "second-observation.json"
        self.rejected("observer-prior-output-input")

    def test_symlinked_output_directory_is_rejected(self):
        outside = self.directory / "outside"
        outside.mkdir()
        (self.root / ".cache").symlink_to(outside, target_is_directory=True)
        self.rejected()
        self.assertEqual(list(outside.iterdir()), [])

    def test_source_symlink_escaping_snapshot_is_rejected(self):
        outside = self.directory / "private.ts"
        outside.write_text('export const secret = "never-echo-this-private-value";')
        (self.root / "src/escape.ts").symlink_to(outside)
        self.rejected("observer-input-link-unsafe")
        self.assertNotIn("never-echo-this-private-value", self.receipt.read_text())

    def test_internal_workspace_link_uses_actual_source_input(self):
        workspace = self.root / "packages/math"
        workspace.mkdir(parents=True)
        (workspace / "package.json").write_text('{"name":"fixture-math","version":"1.0.0","types":"index.ts"}')
        (workspace / "index.ts").write_text("export const twice = (n: number) => n * 2;")
        (self.root / "node_modules/fixture-math").symlink_to("../packages/math")
        self.config(rootDir=".")
        (self.root / "src/index.ts").write_text('export { twice } from "fixture-math";')
        result = self.passed()
        self.assertTrue(any(row["resolved_path"] == "packages/math/index.ts" for row in result["resolutions"]))
        self.assertIn("packages/math/package.json", {row["path"] for row in result["inputs"]})

    def test_changed_inputs_change_observation_identity(self):
        first = self.passed()
        # A fresh output tree is required; preserve the first tree for comparison.
        (self.root / ".cache").rename(self.directory / "first-output")
        (self.root / "src/math.ts").write_text("export const twice = (n: number) => n * 3;")
        self.receipt = self.directory / "second-observation.json"
        second = self.passed()
        self.assertNotEqual(first["observation_digest"], second["observation_digest"])

    def test_configuration_without_inputs_reports_safe_compiler_diagnostic(self):
        (self.root / "tsconfig.json").write_text('{"files":[]}')
        result = self.rejected()
        self.assertTrue(result["diagnostics"])
        self.assertEqual(result["outputs"], [])

    def test_invalid_configuration_does_not_expose_raw_text(self):
        (self.root / "tsconfig.json").write_text('{"private-example": "do-not-copy-me" broken')
        result = self.rejected()
        self.assertTrue(result["diagnostics"])
        self.assertNotIn("do-not-copy-me", self.receipt.read_text())

    def test_unreviewed_compiler_plugin_is_rejected(self):
        self.config(plugins=[{"name": "must-not-execute"}])
        self.rejected("observer-project-feature-unsupported")

    def test_wrong_typescript_package_version_is_rejected_before_loading(self):
        package = self.root / "node_modules/typescript/package.json"
        document = json.loads(package.read_text())
        document["version"] = "0.0.0"
        package.write_text(json.dumps(document))
        self.rejected("observer-typescript-version-unsupported")

    def test_missing_compiler_package_fails_safely(self):
        compiler = self.root / "node_modules/typescript/lib/typescript.js"
        compiler.rename(compiler.with_suffix(".hidden"))
        self.rejected("observer-typescript-unavailable")

    def test_duplicate_cli_options_are_rejected(self):
        self.rejected("observer-arguments-invalid", extra=("--config", "tsconfig.json"))

    def test_configuration_path_traversal_is_rejected(self):
        self.rejected("observer-arguments-invalid", config="../tsconfig.json")

    def test_receipt_cannot_overwrite_an_existing_file(self):
        self.receipt.write_text("preserve-evidence")
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.directory)}
        completed = subprocess.run([str(self.node), str(DRIVER), "--root", str(self.root),
                                    "--config", "tsconfig.json", "--output", str(self.receipt)],
                                   env=env, text=True, capture_output=True, timeout=15, check=False)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(json.loads(completed.stdout)["code"], "observer-receipt-exists")
        self.assertEqual(self.receipt.read_text(), "preserve-evidence")


if __name__ == "__main__":
    unittest.main()
