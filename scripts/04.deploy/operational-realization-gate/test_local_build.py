"""Reject false local build proof, unsafe execution settings and stale bytes."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.local-build
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise safe local build contracts, artifact bindings and isolation command construction.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import copy
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
sys.path.insert(0, str(DIRECTORY.parent / "release-control/discovery"))
import local_build
import local_build_contracts as contracts
import local_build_sandbox as sandbox
import release_compiler as release
import result_consumption

HASH = "sha256:" + "a" * 64


def seal(value, field):
    value[field] = release.digest_document({k: v for k, v in value.items() if k != field})
    return value


def observation():
    return seal({"schema": "local-typescript-observation/v1", "configuration": "src/tsconfig.json",
                 "node_version": "22.23.3", "typescript_version": "5.9.3", "verdict": "passed",
                 "no_emit": False, "emit_skipped": False,
                 "inputs": [{"kind": "repository", "path": "src/tsconfig.json", "digest": HASH, "bytes": 1},
                            {"kind": "dependency", "path": "node_modules/typescript/lib/typescript.js", "digest": HASH, "bytes": 1}],
                 "resolutions": [], "outputs": [{"path": ".cache/a.js", "digest": HASH, "bytes": 1}],
                 "diagnostics": [], "findings": []}, "observation_digest")


class ContractTests(unittest.TestCase):
    def reject(self, edit):
        value = observation()
        edit(value)
        seal(value, "observation_digest")
        with self.assertRaises(release.ReleaseFailure):
            contracts.observation(value)

    def test_valid_observed_compilation(self):
        self.assertEqual(contracts.observation(observation())["verdict"], "passed")

    def test_noemit_pass_preserves_no_outputs(self):
        value = observation()
        value.update(no_emit=True, emit_skipped=True, outputs=[])
        self.assertEqual(contracts.observation(seal(value, "observation_digest"))["outputs"], [])

    def test_unknown_fields_rejected(self):
        self.reject(lambda v: v.update(raw="SENSITIVE-LOCAL-SENTINEL"))

    def test_wrong_node_rejected(self):
        self.reject(lambda v: v.update(node_version="22.22.1"))

    def test_wrong_typescript_rejected(self):
        self.reject(lambda v: v.update(typescript_version="5.8.0"))

    def test_duplicate_inputs_rejected(self):
        self.reject(lambda v: v["inputs"].append(v["inputs"][0]))

    def test_output_escape_rejected(self):
        self.reject(lambda v: v["outputs"][0].update(path=".cache/../secret"))

    def test_absolute_output_rejected(self):
        self.reject(lambda v: v["outputs"][0].update(path="/tmp/leak"))

    def test_unbound_compiler_rejected(self):
        self.reject(lambda v: v["inputs"].pop())

    def test_noemit_outputs_rejected(self):
        self.reject(lambda v: v.update(no_emit=True))

    def test_error_cannot_pass(self):
        self.reject(lambda v: v["diagnostics"].append({"phase": "program", "category": "error", "code": 2322,
                                                     "path": "src/a.ts", "line": 1, "column": 2}))

    def test_failed_diagnostic_is_safe(self):
        value = observation()
        value.update(verdict="failed", emit_skipped=True, outputs=[])
        value["diagnostics"] = [{"phase": "program", "category": "error", "code": 2322,
                                "path": "src/a.ts", "line": 1, "column": 2}]
        contracts.observation(seal(value, "observation_digest"))

    def test_digest_tamper_rejected(self):
        value = observation()
        value["outputs"][0]["bytes"] = 2
        with self.assertRaises(release.ReleaseFailure):
            contracts.observation(value)

    def test_failed_without_reason_rejected(self):
        self.reject(lambda v: v.update(verdict="failed"))

    def test_source_producer_does_not_accept_local_build(self):
        with self.assertRaises(release.ReleaseFailure):
            result_consumption.validate_success({"schema": "local-build-result/v1", "authorized": False})


class FilesystemTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="local-build-contract-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "source"
        self.root.mkdir()
        for name in sandbox.SOURCE_ROOTS:
            (self.root / name).mkdir(parents=True)
        for name in sandbox.SOURCE_FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("{}")
        (self.root / "packages/a.ts").write_text("export const a = 1;")

    def test_source_copy_binds_original_bytes(self):
        manifest = sandbox.source_manifest(self.root, self.base / "copy")
        self.assertEqual(manifest, sandbox.source_manifest(self.base / "copy"))

    def test_source_change_changes_manifest(self):
        first = sandbox.source_manifest(self.root)
        (self.root / "packages/a.ts").write_text("export const a = 2;")
        self.assertNotEqual(first, sandbox.source_manifest(self.root))

    def test_private_files_not_copied(self):
        (self.root / "packages/.env.json").write_text("SENSITIVE-LOCAL-SENTINEL")
        (self.root / "packages/secrets").mkdir()
        (self.root / "packages/secrets/keys.json").write_text("SENSITIVE-LOCAL-SENTINEL")
        rows = sandbox.source_manifest(self.root, self.base / "copy")
        self.assertFalse(any(".env" in r["path"] or "secrets/" in r["path"] for r in rows))

    def test_link_source_rejected(self):
        (self.root / "packages/b.ts").symlink_to(self.root / "package.json")
        with self.assertRaises(sandbox.LocalBuildFailure):
            sandbox.source_manifest(self.root)

    def test_fifo_source_rejected(self):
        os.mkfifo(self.root / "packages/b.ts")
        with self.assertRaises(sandbox.LocalBuildFailure):
            sandbox.source_manifest(self.root)

    def test_source_limit_rejected(self):
        with patch.object(sandbox, "MAX_SOURCE_FILES", 1):
            with self.assertRaises(sandbox.LocalBuildFailure):
                sandbox.source_manifest(self.root)

    def test_npm_configuration_rejected(self):
        (self.root / ".npmrc").write_text("script-shell=/bin/true")
        with self.assertRaises(sandbox.LocalBuildFailure):
            sandbox.source_manifest(self.root)

    def test_observed_input_mismatch_rejected(self):
        with self.assertRaises(sandbox.LocalBuildFailure):
            local_build.check_observed_files(self.root, observation(), [])

    def test_output_tampering_rejected(self):
        (self.root / ".cache").mkdir()
        (self.root / ".cache/a.js").write_text("tampered")
        observed = observation()
        with self.assertRaises(sandbox.LocalBuildFailure):
            local_build.check_observed_files(self.root, observed, observed["inputs"])

    def test_unobserved_extra_output_rejected(self):
        (self.root / ".cache").mkdir()
        (self.root / ".cache/a.js").write_bytes(b"x")
        (self.root / ".cache/extra.js").write_bytes(b"x")
        observed = observation()
        observed["outputs"][0]["digest"] = sandbox.digest(b"x")
        with self.assertRaises(sandbox.LocalBuildFailure):
            local_build.check_observed_files(self.root, observed, observed["inputs"])

    def test_sandbox_has_no_checkout_home_or_ambient_env(self):
        runner = sandbox.Sandbox(self.base, self.base)
        with patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "SENSITIVE-LOCAL-SENTINEL", "NODE_OPTIONS": "bad"}):
            command = runner.command([str(self.base / "bin/node"), "--version"], self.root, {})
        text = " ".join(command)
        self.assertNotIn("SENSITIVE", text)
        self.assertIn("--unshare-net", command)
        self.assertIn("--clearenv", command)
        self.assertIn("--disable-userns", command)
        self.assertIn("--cap-drop", command)
        self.assertNotIn("/home", command)

    def test_sensitive_environment_rejected(self):
        runner = sandbox.Sandbox(self.base, self.base)
        with self.assertRaises(sandbox.LocalBuildFailure):
            runner.command(["/usr/bin/true"], self.root, {"AWS_ACCESS_KEY_ID": "SENSITIVE"})

    def test_persistent_scratch_is_required(self):
        with self.assertRaisesRegex(sandbox.LocalBuildFailure, "scratch-required"):
            local_build.run(self.root, self.base)

    def test_scratch_cannot_be_inside_checkout(self):
        with self.assertRaisesRegex(sandbox.LocalBuildFailure, "scratch-invalid"):
            local_build.run(self.root, self.base, scratch_root=self.root)

    def test_duplicate_observation_keys_rejected(self):
        with self.assertRaises(sandbox.LocalBuildFailure):
            local_build.unique_pairs([("verdict", "failed"), ("verdict", "passed")])

    def test_compiler_inputs_are_readonly_with_one_writable_output(self):
        runner = sandbox.Sandbox(self.base, self.base, writable=[".cache"])
        command = runner.command(["/usr/bin/true"], self.root, {})
        groups = [command[i:i+3] for i in range(len(command)-2)]
        self.assertIn(["--ro-bind", str(self.root), "/work"], groups)
        self.assertIn(["--bind", str(self.root / ".cache"), "/work/.cache"], groups)
        self.assertNotIn(["--bind", str(self.root), "/work"], groups)

    def test_writable_escape_rejected(self):
        runner = sandbox.Sandbox(self.base, self.base, writable=[".cache/../../escape"])
        with self.assertRaises(sandbox.LocalBuildFailure):
            runner.command(["/usr/bin/true"], self.root, {})

    def test_local_results_cannot_grant_release_eligibility(self):
        decision = result_consumption.consume_result({"schema": "local-build-result/v1"}, "release-eligibility")
        self.assertFalse(decision["authorized"])
        self.assertEqual(decision["release_eligibility"], "blocked")
        self.assertEqual(decision["findings"][0]["code"], "source-result-authority-unavailable")

    def test_local_results_cannot_grant_operation_authority(self):
        decision = result_consumption.consume_result({"schema": "local-build-result/v1"}, "operation-authorization")
        self.assertFalse(decision["authorized"])
        self.assertEqual(decision["operation_authorization"], "blocked")
        self.assertEqual(decision["findings"][0]["code"], "source-result-authority-unavailable")

    def test_cli_does_not_echo_unsafe_arguments(self):
        output = StringIO()
        with redirect_stdout(output):
            code = local_build.main(["--raw", "SENSITIVE-LOCAL-SENTINEL"])
        self.assertEqual(code, 1)
        self.assertNotIn("SENSITIVE", output.getvalue())
        self.assertFalse(json.loads(output.getvalue())["authorized"])


if __name__ == "__main__":
    unittest.main()
