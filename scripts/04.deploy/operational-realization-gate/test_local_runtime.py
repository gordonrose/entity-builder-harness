#!/usr/bin/env python3
"""Test source-free runtime preparation with an injected, bounded executor."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-local-runtime-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject source fallback and stale or tampered runtime payloads before accepting local observations.
#   portability: {class: internal, targets: [entity-builder]}
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
import local_runtime as runtime
import package_exports as exports
import local_build_contracts as contracts
import release_compiler
from test_package_exports import fixture as export_fixture
from source_inventory import SourceFailure, canonical, digest

REPO = Path(__file__).resolve().parents[3]


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="local-runtime-test-")
        self.root = Path(self.temp.name) / "source"
        self.compiled = Path(self.temp.name) / "compiled"
        self.root.mkdir()
        self.compiled.mkdir()
        self.configuration = "platform/server/tsconfig.runtime-test.json"
        self.calls = []
        self.closure = {"source_root": self.root, "node_path": "/pinned/bin/node",
                        "external_modules_root": self.root / "node_modules", "external_modules": [],
                        "workspace_links": [], "source_inventory_digest": digest(b"source-inventory"),
                        "external_modules_digest": digest(canonical([])), "external_files": []}
        (self.root / "node_modules").mkdir()
        self.generator_fixture()

    def tearDown(self):
        self.temp.cleanup()

    def put(self, root, path, value):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value.encode() if type(value) is str else value)
        return target

    def reseal_observation(self):
        self.observation['outputs'].sort(key=lambda row: row['path'])
        self.observation['emission_map']['entries'].sort(key=lambda row: row['output_path'])
        exports.seal(self.observation,'observation_digest')
        self.closure['compiler_observation']=self.observation

    def add_compiled(self,relative,raw='// inert fixture\n'):
        source=relative[:-3]+'.ts'
        source_file=self.put(self.root,source,'export {};\n')
        self.observation['inputs'].append({'kind':'repository','path':source,'digest':digest(source_file.read_bytes()),'bytes':source_file.stat().st_size})
        output=self.put(self.compiled,self.output+'/'+relative,raw)
        self.observation['outputs'].append({'path':self.output+'/'+relative,'digest':digest(output.read_bytes()),'bytes':output.stat().st_size})
        self.observation['emission_map']['entries'].append({'output_path':self.output+'/'+relative,'source_paths':[source],'kind':'javascript'})
        self.reseal_observation()

    def generator_fixture(self, configuration=None):
        if configuration:
            self.configuration = configuration
        self.output, self.kind = runtime.CONFIGURATIONS[self.configuration]
        self.entry = runtime.artifacts.CONFIG_GENERATORS[self.configuration]
        self.put(self.root,self.entry,(REPO/self.entry).read_bytes())
        self.put(self.root,exports.SHARED_HELPER,(REPO/exports.SHARED_HELPER).read_bytes())
        self.observation=export_fixture(self.root,self.configuration)
        for row in self.observation['outputs']:
            self.put(self.compiled,row['path'],(self.root/row['path']).read_bytes())
        self.main_output='packages/core/src/index.js'
        self.test_path = None
        if self.kind == "runtime-test-runner":
            folder = "platform/server" if self.configuration.startswith("platform/") else "products/kanbien-platform"
            self.test_path = folder + "/tests/example-runtime.test.js"
            self.add_compiled(self.test_path)
        self.reseal_observation()

    def dependency(self, name="external", main="index.js", files=None):
        base = "node_modules/" + name
        values = {"package.json": json.dumps({"name": name, "version": "1.0.0", "main": main}), "index.js": "exports.value = 1;"}
        values.update(files or {})
        self.closure["external_modules"].append({"path": base, "name": name, "version": "1.0.0"})
        for path, value in values.items():
            target = self.put(self.root, base + "/" + path, value)
            self.closure["external_files"].append({"path": base + "/" + path, "digest": digest(target.read_bytes()), "bytes": target.stat().st_size})
        self.closure["external_files"].sort(key=lambda row: row["path"])
        self.closure["external_modules_digest"] = digest(canonical(self.closure["external_files"]))

    def execute(self, argv, cwd, env):
        self.calls.append((argv, cwd, env))
        self.assertEqual(["/pinned/bin/node", exports.RUNTIME_DRIVER], argv)
        self.assertEqual((cwd/exports.RUNTIME_DRIVER).read_bytes(),exports.driver_bytes(self.configuration))
        self.assertEqual((cwd/self.entry).read_bytes(),(self.root/self.entry).read_bytes())
        self.assertEqual((cwd/exports.SHARED_HELPER).read_bytes(),(self.root/exports.SHARED_HELPER).read_bytes())
        self.assertFalse(any(path.suffix == ".ts" for path in cwd.rglob("*")))
        self.assertEqual({"PATH", "HOME", "LANG", "TZ"}, set(env))
        projection=json.loads((cwd/exports.PROJECTION_INPUT).read_bytes())
        self.assertEqual(projection['compiler_observation_digest'],self.observation['observation_digest'])
        for relative,raw in exports.generated_files(projection).items():
            self.put(cwd,self.output+'/'+relative,raw)
        return {"returncode": 0, "stdout": b"private output that must not be exposed", "stderr": b""}

    def run_local(self, execute=None):
        return runtime.run_runtime(self.configuration, self.compiled, self.closure, execute or self.execute)

    def failure(self, code, execute=None):
        with self.assertRaisesRegex(SourceFailure, "^" + code + "$"):
            self.run_local(execute)

    def test_runtime_receipt_binds_source_compiler_dependency_and_observed_files(self):
        self.dependency()
        result = self.run_local()
        self.assertEqual("local-workspace-runtime-observation/v1", result["schema"])
        self.assertFalse(result["authorized"])
        self.assertEqual("blocked", result["qualification_verdict"])
        self.assertEqual(1, result["executed_runner_count"])
        self.assertEqual([self.test_path], result["selected_runtime_tests"])
        self.assertEqual(6, len(result["artifact_files"]))
        self.assertEqual(result['execution_driver_digest'],digest(exports.driver_bytes(self.configuration)))
        self.assertEqual(result['workspace_exports']['compiler_observation_digest'],self.observation['observation_digest'])
        self.assertEqual(result['generator_helpers'],[{'path':exports.SHARED_HELPER,'digest':digest((self.root/exports.SHARED_HELPER).read_bytes())}])
        self.assertEqual(result["receipt_digest"], digest(canonical({key: value for key, value in result.items() if key != "receipt_digest"})))
        self.assertNotIn("private output", json.dumps(result))
        self.assertFalse(self.calls[0][1].exists())

    def test_modern_receipt_binds_full_artifact_union_and_fresh_helper_source(self):
        result=self.run_local()
        contracts.runtime(result)
        contracts.runtime_compiler_binding(result,self.observation)
        sources=[{'path':path,'digest':digest((self.root/path).read_bytes())} for path in (self.entry,exports.SHARED_HELPER)]
        contracts.runtime_source_binding(result,sources)
        sources[-1]['digest']=digest(b'changed helper')
        with self.assertRaisesRegex(release_compiler.ReleaseFailure,'local-build-runtime-generator-binding-invalid'):
            contracts.runtime_source_binding(result,sources)

    def test_rehashed_hidden_runtime_artifact_cannot_enter_compiler_generated_union(self):
        result=self.run_local()
        result['artifact_files'].append({'path':'node_modules/hidden/index.js','digest':digest(b'hidden'),'bytes':6})
        exports.seal(result,'receipt_digest')
        with self.assertRaisesRegex(release_compiler.ReleaseFailure,'local-build-runtime-compiler-binding-invalid'):
            contracts.runtime_compiler_binding(result,self.observation)

    def test_image_preparation_does_not_claim_test_execution(self):
        self.generator_fixture("platform/server/tsconfig.image.json")
        result = self.run_local()
        self.assertEqual("image-shim-generator", result["kind"])
        self.assertEqual(0, result["executed_runner_count"])
        self.assertEqual([], result["selected_runtime_tests"])

    def test_product_runner_selects_only_own_immediate_tests(self):
        self.generator_fixture("products/kanbien-platform/tsconfig.runtime-test.json")
        self.add_compiled("platform/server/tests/other-runtime.test.js")
        self.add_compiled("products/kanbien-platform/tests/nested/other-runtime.test.js")
        self.assertEqual([self.test_path], self.run_local()["selected_runtime_tests"])

    def test_unknown_configuration_never_executes(self):
        self.configuration = "untrusted/tsconfig.json"
        self.failure("local-runtime-configuration-unsupported")
        self.assertEqual([], self.calls)

    def test_unpinned_relative_node_rejects(self):
        self.closure["node_path"] = "node"
        self.failure("local-runtime-toolchain-invalid")

    def test_invalid_closure_digest_rejects(self):
        self.closure["source_inventory_digest"] = "unknown"
        self.failure("local-runtime-closure-invalid")

    def test_changed_generator_helper_rejects_before_execution(self):
        path = self.root / self.entry
        path.write_text(path.read_text().replace('prepareWorkspaceRuntime(', 'changedWorkspaceRuntime('))
        self.failure("local-runtime-generator-unsupported")
        self.assertEqual([], self.calls)

    def test_changed_shared_helper_rejects_before_execution(self):
        path=self.root/exports.SHARED_HELPER
        path.write_bytes(path.read_bytes()+b'\n// changed helper\n')
        self.failure('local-runtime-helper-unsupported')
        self.assertEqual([],self.calls)

    def test_missing_or_legacy_observation_never_executes(self):
        for observed in (None,{'schema':'local-typescript-observation/v1'}):
            with self.subTest(observed=observed):
                self.closure['compiler_observation']=observed
                self.failure('local-runtime-emission-required')
                self.assertEqual([],self.calls)

    def test_projection_or_private_driver_mutation_is_rejected(self):
        for target in (exports.PROJECTION_INPUT,exports.RUNTIME_DRIVER,exports.SHARED_HELPER):
            def mutate(argv,cwd,env):
                result=self.execute(argv,cwd,env)
                self.put(cwd,target,'changed')
                return result
            with self.subTest(target=target):self.failure('local-runtime-generator-changed',mutate)

    def test_changed_generator_root_rejects(self):
        path = self.root / self.entry
        path.write_text(path.read_text().replace(self.output, ".cache/other"))
        self.failure("local-runtime-generator-unsupported")

    def test_executable_typescript_in_compiled_output_rejects(self):
        self.put(self.compiled, self.output + "/src/index.ts", "export {};")
        self.failure("package-export-remainder-mismatch")

    def test_preexisting_shim_dependency_directory_rejects(self):
        self.put(self.compiled, self.output + "/node_modules/evil/index.js", "evil")
        self.failure("package-export-remainder-mismatch")

    def test_missing_shim_target_rejects_before_execution(self):
        (self.compiled / self.output / self.main_output).unlink()
        self.failure("package-export-compiler-bytes-invalid")
        self.assertEqual([], self.calls)

    def test_empty_runtime_membership_rejects(self):
        (self.compiled / self.output / self.test_path).unlink()
        target=self.output+'/'+self.test_path
        self.observation['outputs']=[row for row in self.observation['outputs'] if row['path']!=target]
        self.observation['emission_map']['entries']=[row for row in self.observation['emission_map']['entries'] if row['output_path']!=target]
        self.reseal_observation()
        self.failure("local-runtime-tests-empty")

    def test_compiled_symlink_rejects(self):
        (self.compiled / self.output / "escape.js").symlink_to(self.root / self.entry)
        self.failure("artifact-file-kind-unsupported")

    def test_external_typescript_entry_rejects(self):
        self.dependency(main="source.ts", files={"source.ts": "export {};"})
        self.failure("local-runtime-source-fallback")

    def test_external_declaration_types_and_compiler_are_not_copied(self):
        self.dependency(files={"index.d.ts": "export {};", "package.json": json.dumps({"name": "external", "exports": {"types": "./index.d.ts", "default": "./index.js"}})})
        self.dependency("typescript")
        self.dependency("@types/node")
        def inspect(argv, cwd, env):
            self.assertFalse((cwd / "node_modules/typescript").exists())
            self.assertFalse((cwd / "node_modules/@types").exists())
            return self.execute(argv, cwd, env)
        self.run_local(inspect)

    def test_workspace_links_and_bin_links_are_not_copied(self):
        (self.root / "node_modules/workspace").symlink_to(self.root)
        (self.root / "node_modules/.bin").mkdir()
        (self.root / "node_modules/.bin/command").symlink_to(self.root / self.entry)
        self.closure["workspace_links"] = ["node_modules/workspace"]
        def inspect(argv, cwd, env):
            self.assertFalse((cwd / "node_modules/workspace").exists())
            self.assertFalse((cwd / "node_modules/.bin").exists())
            return self.execute(argv, cwd, env)
        self.run_local(inspect)

    def test_external_package_symlink_rejects(self):
        (self.root / "node_modules/external").symlink_to(self.root)
        self.closure["external_modules"] = [{"path": "node_modules/external", "name": "external", "version": "1.0.0"}]
        self.failure("local-runtime-input-invalid")

    def test_external_internal_symlink_rejects(self):
        self.dependency()
        (self.root / "node_modules/external/escape").symlink_to(self.root)
        self.failure("local-runtime-dependency-kind")

    def test_external_fifo_rejects_without_hanging(self):
        self.dependency()
        os.mkfifo(self.root / "node_modules/external/fifo")
        self.failure("local-runtime-dependency-kind")

    def test_external_bytes_mismatch_rejects_before_execution(self):
        self.dependency()
        (self.root / "node_modules/external/index.js").write_text("stale")
        self.failure("local-runtime-dependency-stale")

    def test_missing_external_file_rejects_before_execution(self):
        self.dependency()
        (self.root / "node_modules/external/index.js").unlink()
        self.failure("local-runtime-dependency-stale")

    def test_dependency_digest_mismatch_rejects(self):
        self.closure["external_modules_digest"] = digest(b"different")
        self.failure("local-runtime-dependency-stale")

    def test_dependency_hard_limit_rejects(self):
        self.dependency()
        with patch.object(runtime, "MAX_DEPENDENCY_BYTES", 1):
            self.failure("local-runtime-dependency-limit")

    def test_command_failure_does_not_return_success_receipt(self):
        self.failure("local-runtime-command-failed", lambda *_: {"returncode": 1, "stdout": b"secret", "stderr": b"secret"})

    def test_timeout_does_not_return_success_receipt(self):
        def timeout(*_):
            raise TimeoutError("private detail")
        self.failure("local-runtime-timeout", timeout)

    def test_executor_exception_is_safely_normalized(self):
        def error(*_):
            raise ValueError("private detail")
        self.failure("local-runtime-execution-failed", error)

    def test_invalid_executor_result_rejects(self):
        self.failure("local-runtime-executor-result-invalid", lambda *_: {"returncode": False, "stdout": b"", "stderr": b""})

    def test_output_limit_does_not_return_success_receipt(self):
        with patch.object(runtime, "MAX_COMMAND_OUTPUT_BYTES", 1):
            self.failure("local-runtime-output-limit")

    def test_compiled_bytes_modified_by_runtime_rejects(self):
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(cwd, self.output + "/" + self.main_output, "changed")
            return result
        self.failure("local-runtime-artifact-changed", mutate)

    def test_wrong_generated_shim_bytes_rejects(self):
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(cwd, self.output + "/node_modules/@fixture/core/index.js", "wrong")
            return result
        self.failure("local-runtime-artifact-changed", mutate)

    def test_added_runtime_test_after_execution_rejects(self):
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(cwd, self.output + "/platform/server/tests/stale-runtime.test.js", "stale")
            return result
        self.failure("local-runtime-artifact-changed", mutate)

    def test_unexpected_file_outside_artifact_rejects(self):
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(cwd, "repo/source.ts", "fallback")
            return result
        self.failure("local-runtime-unexpected-file", mutate)

    def test_runtime_generator_mutation_rejects(self):
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(cwd, self.entry, "changed")
            return result
        self.failure("local-runtime-generator-changed", mutate)

    def test_copied_dependency_mutation_rejects(self):
        self.dependency()
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(cwd, "node_modules/external/index.js", "changed")
            return result
        self.failure("local-runtime-dependency-stale", mutate)

    def test_source_generator_changes_during_execution_rejects(self):
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(self.root, self.entry, "changed")
            return result
        self.failure("local-runtime-source-changed", mutate)

    def test_original_compiler_output_changes_during_execution_rejects(self):
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(self.compiled, self.output + "/" + self.main_output, "changed")
            return result
        self.failure("local-runtime-compiler-artifact-changed", mutate)

    def test_original_dependency_changes_during_execution_rejects(self):
        self.dependency()
        def mutate(argv, cwd, env):
            result = self.execute(argv, cwd, env)
            self.put(self.root, "node_modules/external/index.js", "changed")
            return result
        self.failure("local-runtime-dependency-stale", mutate)


if __name__ == "__main__":
    unittest.main()
