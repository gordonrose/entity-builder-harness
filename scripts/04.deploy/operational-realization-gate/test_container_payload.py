"""Check payload export bindings and production dependency boundaries."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.container-payload
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject unverified, stale, source-bearing and non-production container payloads.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import container_payload as payload
from local_build_sandbox import LocalBuildFailure, canonical, digest
import local_runtime as runtime
import test_local_runtime as fixtures


class PayloadTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="container-payload-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "source"
        self.root.mkdir()
        self.destination = self.base / "payload"
        self.lock = {"lockfileVersion": 3, "packages": {
            "": {}, "node_modules/runtime": {"version": "1.0.0"},
            "node_modules/devonly": {"version": "1.0.0", "dev": True}}}
        self.closure = {"external": [{"path": "node_modules/" + name, "name": name, "version": "1.0.0"}
                                     for name in ("runtime", "devonly")]}
        self.production = [{"path": "node_modules/runtime", "name": "runtime", "version": "1.0.0"}]
        self.artifact = {"src/main.js": b"exports.main = 1;"}
        self.dependencies = {"node_modules/runtime/package.json": b'{"name":"runtime"}',
                             "node_modules/runtime/index.js": b"exports.value=1;",
                             "node_modules/devonly/package.json": b'{"name":"devonly"}'}
        self.exported = {**{payload.OUTPUT_ROOT + "/" + path: raw for path, raw in self.artifact.items()},
                         **self.dependencies}
        self.result = {"verdict": "passed", "source_digest": digest(canonical([])), "runner_digest": digest(b"runner"),
                       "builds": [{"configuration": payload.CONFIGURATION,
                                   "runtime": {"kind": "image-shim-generator", "returncode": 0,
                                               "artifact_files": runtime.fingerprint(self.artifact),
                                               "copied_dependency_digest": runtime.file_set_digest(self.dependencies)}}]}
        self.certificate = (Path(__file__).resolve().parents[3] / payload.CERTIFICATE_SOURCE).read_bytes()

    def packages(self):
        return payload.production_packages(json.dumps(self.lock).encode(), self.closure)

    def select(self):
        return payload.select_files(self.exported, self.result, self.production, self.certificate)

    def failure(self, code, callback):
        with self.assertRaisesRegex(LocalBuildFailure, "^container-payload-" + code + "$"):
            callback()

    def test_production_flags_retain_runtime_and_omit_dev(self):
        self.assertEqual(self.production, self.packages())

    def test_production_dependency_on_dev_only_rejects(self):
        self.lock["packages"]["node_modules/runtime"]["dependencies"] = {"devonly": "1.0.0"}
        self.failure("production-closure-incomplete", self.packages)

    def test_missing_required_dependency_rejects(self):
        self.lock["packages"]["node_modules/runtime"]["dependencies"] = {"missing": "1.0.0"}
        self.failure("production-closure-incomplete", self.packages)

    def test_root_production_dependency_cannot_be_marked_dev(self):
        self.lock["packages"][""]["dependencies"] = {"devonly": "1.0.0"}
        self.failure("production-closure-incomplete", self.packages)

    def test_workspace_production_dependency_cannot_be_marked_dev(self):
        self.lock["packages"]["packages/app"] = {"dependencies": {"devonly": "1.0.0"}}
        self.failure("production-closure-incomplete", self.packages)

    def test_workspace_production_dependency_can_use_workspace_link(self):
        self.lock["packages"]["packages/app"] = {"dependencies": {"@fixture/shared": "1.0.0"}}
        self.lock["packages"]["node_modules/@fixture/shared"] = {"link": True, "resolved": "packages/shared"}
        self.assertEqual(self.production, self.packages())

    def test_missing_optional_locked_dependency_rejects(self):
        self.lock["packages"]["node_modules/runtime"]["optionalDependencies"] = {"missing": "1.0.0"}
        self.failure("production-closure-incomplete", self.packages)

    def test_absent_explicit_optional_peer_is_supported(self):
        row = self.lock["packages"]["node_modules/runtime"]
        row.update(peerDependencies={"native": "1.0.0"}, peerDependenciesMeta={"native": {"optional": True}})
        self.assertEqual(self.production, self.packages())

    def test_present_dev_only_optional_peer_rejects(self):
        row = self.lock["packages"]["node_modules/runtime"]
        row.update(peerDependencies={"devonly": "1.0.0"}, peerDependenciesMeta={"devonly": {"optional": True}})
        self.failure("production-closure-incomplete", self.packages)

    def test_string_dev_flag_rejects(self):
        self.lock["packages"]["node_modules/runtime"]["dev"] = "false"
        self.failure("production-flags-unsupported", self.packages)

    def test_dev_optional_ambiguity_rejects(self):
        self.lock["packages"]["node_modules/runtime"]["devOptional"] = True
        self.failure("production-flags-unsupported", self.packages)

    def test_changed_lock_version_rejects(self):
        self.lock["packages"]["node_modules/runtime"]["version"] = "2.0.0"
        self.failure("production-flags-unsupported", self.packages)

    def test_no_production_package_rejects(self):
        self.lock["packages"]["node_modules/runtime"]["dev"] = True
        self.failure("production-closure-empty", self.packages)

    def test_typescript_cannot_become_production_dependency(self):
        self.lock["packages"]["node_modules/typescript"] = {"version": "1.0.0"}
        self.closure["external"].append({"path": "node_modules/typescript", "name": "typescript", "version": "1.0.0"})
        self.failure("production-source-fallback", self.packages)

    def test_export_selects_exact_runtime_and_production_files(self):
        files, dependency_digest, excluded = self.select()
        self.assertEqual({payload.OUTPUT_ROOT + "/src/main.js", "node_modules/runtime/package.json",
                          "node_modules/runtime/index.js", payload.CERTIFICATE_TARGET}, set(files))
        self.assertEqual(digest(canonical(runtime.fingerprint({path: raw for path, raw in files.items()
                                                              if path.startswith("node_modules/")}))), dependency_digest)
        self.assertEqual(runtime.fingerprint({"node_modules/devonly/package.json": self.dependencies["node_modules/devonly/package.json"]}), excluded)

    def test_retained_and_excluded_fingerprints_bind_complete_verified_runtime_dependencies(self):
        files, _, excluded = self.select()
        retained = runtime.fingerprint({path: raw for path, raw in files.items() if path.startswith("node_modules/")})
        combined = sorted(retained + excluded, key=lambda row: row["path"])
        self.assertEqual(self.result["builds"][0]["runtime"]["copied_dependency_digest"], digest(canonical(combined)))
        self.assertFalse({row["path"] for row in retained} & {row["path"] for row in excluded})

    def test_omitting_excluded_fingerprint_changes_runtime_dependency_binding(self):
        files, _, excluded = self.select()
        self.assertTrue(excluded)
        retained = runtime.fingerprint({path: raw for path, raw in files.items() if path.startswith("node_modules/")})
        self.assertNotEqual(self.result["builds"][0]["runtime"]["copied_dependency_digest"], digest(canonical(retained)))

    def test_tampered_compiler_output_rejects(self):
        self.exported[payload.OUTPUT_ROOT + "/src/main.js"] = b"changed"
        self.failure("export-binding-invalid", self.select)

    def test_missing_generated_shim_rejects(self):
        self.result["builds"][0]["runtime"]["artifact_files"].append({"path": "node_modules/shim/index.js", "digest": digest(b"shim"), "bytes": 4})
        self.failure("export-binding-invalid", self.select)

    def test_extra_source_file_outside_artifact_rejects(self):
        self.exported["platform/server/src/main.ts"] = b"secret source"
        self.failure("export-binding-invalid", self.select)

    def test_changed_external_dependency_rejects(self):
        self.exported["node_modules/runtime/index.js"] = b"changed"
        self.failure("export-binding-invalid", self.select)

    def test_even_dev_only_export_tampering_rejects(self):
        self.exported["node_modules/devonly/package.json"] = b"changed"
        self.failure("export-binding-invalid", self.select)

    def test_missing_production_manifest_rejects(self):
        self.production.append({"path": "node_modules/missing", "name": "missing", "version": "1.0.0"})
        self.failure("production-package-missing", self.select)

    def test_source_fallback_rejects_even_when_bound(self):
        self.exported[payload.OUTPUT_ROOT + "/src/main.ts"] = b"source"
        self.result["builds"][0]["runtime"]["artifact_files"] = runtime.fingerprint({**self.artifact, "src/main.ts": b"source"})
        self.failure("source-fallback", self.select)

    def test_failed_build_cannot_export(self):
        self.result["verdict"] = "failed"
        self.failure("build-failed", self.select)

    def test_other_configuration_cannot_export(self):
        self.result["builds"][0]["configuration"] = "platform/server/tsconfig.runtime-test.json"
        self.failure("runtime-invalid", self.select)

    def test_missing_runtime_cannot_export(self):
        self.result["builds"][0]["runtime"] = None
        self.failure("runtime-invalid", self.select)

    def test_new_destination_must_be_outside_source_under_scratch(self):
        self.assertEqual(self.destination, payload.checked_destination(self.destination, self.base, self.root))
        self.failure("destination-invalid", lambda: payload.checked_destination(self.root / "payload", self.base, self.root))
        self.failure("destination-invalid", lambda: payload.checked_destination(self.base.parent / "payload", self.base, self.root))

    def test_existing_destination_is_preserved(self):
        self.destination.mkdir()
        (self.destination / "keep").write_text("untouched")
        self.failure("destination-invalid", lambda: payload.checked_destination(self.destination, self.base, self.root))
        self.assertEqual("untouched", (self.destination / "keep").read_text())

    def test_symlink_destination_is_rejected(self):
        self.destination.symlink_to(self.root, target_is_directory=True)
        self.failure("destination-invalid", lambda: payload.checked_destination(self.destination, self.base, self.root))

    def test_certificate_accepts_public_chain(self):
        target = self.root / payload.CERTIFICATE_SOURCE
        target.parent.mkdir(parents=True)
        target.write_bytes(self.certificate)
        self.assertEqual(self.certificate, payload.certificate(self.root))

    def test_certificate_rejects_private_key_or_unstructured_bytes(self):
        target = self.root / payload.CERTIFICATE_SOURCE
        target.parent.mkdir(parents=True)
        target.write_bytes(b"-----BEGIN PRIVATE KEY-----\nprivate\n-----END PRIVATE KEY-----\n")
        self.failure("certificate-invalid", lambda: payload.certificate(self.root))

    def test_certificate_symlink_is_never_followed(self):
        target = self.root / payload.CERTIFICATE_SOURCE
        target.parent.mkdir(parents=True)
        other = self.base / "public.crt"
        other.write_bytes(self.certificate)
        target.symlink_to(other)
        with self.assertRaises(OSError):
            payload.certificate(self.root)

    def mock_prepare(self, *, failed=False, changed_certificate=False):
        def build(root, cache, selected, scratch, artifact_export):
            self.assertEqual((payload.CONFIGURATION,), selected)
            if failed:
                return {"verdict": "failed"}
            artifact_export.mkdir()
            runtime.write_files(artifact_export, self.exported)
            return deepcopy(self.result)
        contexts = [patch.object(payload.local_build, "run", side_effect=build),
                    patch.object(payload.tools, "inspect_project", return_value=self.closure),
                    patch.object(payload.tools, "_read", return_value=json.dumps(self.lock).encode()),
                    patch.object(payload, "source_manifest", return_value=[]),
                    patch.object(payload.local_build, "implementation_digest", return_value=self.result["runner_digest"]),
                    patch.object(payload, "certificate", side_effect=[self.certificate, b"changed"] if changed_certificate else None,
                                 return_value=self.certificate)]
        from contextlib import ExitStack
        with ExitStack() as stack:
            for context in contexts:
                stack.enter_context(context)
            return payload.prepare(self.root, self.base, self.base, self.destination)

    def test_prepare_emits_manifest_for_new_exclusive_payload(self):
        result = self.mock_prepare()
        actual = runtime.artifacts.artifact_files(self.destination)
        self.assertEqual(runtime.fingerprint(actual), result["files"])
        self.assertEqual(digest(canonical(result["files"])), result["payload_digest"])
        self.assertEqual(self.production, result["production_dependencies"])
        retained = [row for row in result["files"] if row["path"].startswith("node_modules/")]
        self.assertEqual(self.result["builds"][0]["runtime"]["copied_dependency_digest"],
                         digest(canonical(sorted(retained + result["excluded_dependency_files"], key=lambda row: row["path"]))))
        self.assertEqual(payload.CERTIFICATE_SOURCE, result["certificate"]["source_path"])

    def test_prepare_failed_build_leaves_no_payload(self):
        self.failure("build-failed", lambda: self.mock_prepare(failed=True))
        self.assertFalse(self.destination.exists())

    def test_prepare_changed_public_certificate_leaves_no_payload(self):
        self.failure("source-changed", lambda: self.mock_prepare(changed_certificate=True))
        self.assertFalse(self.destination.exists())


class RuntimeExportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.LocalRuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.fixture.generator_fixture(payload.CONFIGURATION)
        self.fixture.dependency()
        self.export = self.fixture.root.parent / "export"

    def run_export(self, execute=None):
        f = self.fixture
        return runtime.run_runtime(f.configuration, f.compiled, f.closure, execute or f.execute, export_root=self.export)

    def test_image_export_contains_verified_bytes_and_no_generator(self):
        receipt = self.run_export()
        files = runtime.artifacts.artifact_files(self.export)
        compiled = {path[len(payload.OUTPUT_ROOT) + 1:]: raw for path, raw in files.items()
                    if path.startswith(payload.OUTPUT_ROOT + "/")}
        self.assertEqual(receipt["artifact_files"], runtime.fingerprint(compiled))
        self.assertNotIn(self.fixture.entry, files)
        self.assertIn("node_modules/external/index.js", files)

    def test_failed_generator_does_not_export(self):
        with self.assertRaisesRegex(runtime.SourceFailure, "local-runtime-command-failed"):
            self.run_export(lambda *args: {"returncode": 1, "stdout": b"", "stderr": b""})
        self.assertFalse(self.export.exists())

    def test_tampered_runtime_does_not_export(self):
        def execute(*args):
            result = self.fixture.execute(*args)
            (args[1] / self.fixture.output / "src/index.js").write_text("changed")
            return result
        with self.assertRaisesRegex(runtime.SourceFailure, "local-runtime-artifact-changed"):
            self.run_export(execute)
        self.assertFalse(self.export.exists())

    def test_export_rejects_other_runtime_configuration(self):
        self.fixture.generator_fixture("platform/server/tsconfig.runtime-test.json")
        with self.assertRaisesRegex(runtime.SourceFailure, "local-runtime-export-invalid"):
            self.run_export()

    def test_export_rejects_existing_destination(self):
        self.export.mkdir()
        with self.assertRaisesRegex(runtime.SourceFailure, "local-runtime-export-invalid"):
            self.run_export()
        self.assertEqual([], list(self.export.iterdir()))


if __name__ == "__main__":
    unittest.main()
