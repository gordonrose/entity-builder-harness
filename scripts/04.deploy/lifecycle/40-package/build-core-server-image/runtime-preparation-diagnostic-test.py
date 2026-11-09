#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.runtime-preparation-diagnostics
#   version: 2
#   status: active
#   created_on: "2026-10-31"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Exercise actual preparation and payload CLI failures in disposable filesystem roots without compiling or building images.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.core-server-image-payload-fixture
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/payload-fixture-test.sh
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
BASE = "scripts/04.deploy/lifecycle/40-package/"
PREPARERS = {
    "core-server": BASE + "build-core-server-image/prepare-runtime.mjs",
    "core-server-persistence": BASE + "build-core-server-persistence-image/prepare-runtime.mjs",
    "platform-shell": "scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs",
}
CANARY = "PRIVATE_PREPARATION_PATH_CANARY"
spec = importlib.util.spec_from_file_location("payload_checker", ROOT / BASE / "build-core-server-image/verify-payload.py")
payload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(payload)


class PreparationDiagnostics(unittest.TestCase):
    def test_platform_shell_entity_app_shim_uses_compiled_public_root(self):
        with tempfile.TemporaryDirectory(prefix="prepare-entity-app-") as temporary:
            directory = Path(temporary)
            compiled = directory / '.cache/platform-shell-image-build'
            target = compiled / 'apps/entity-smoke/src/index.js'
            target.parent.mkdir(parents=True)
            target.write_text('exports.marker = "compiled-entity";\n')
            self.run_preparer('platform-shell', directory)
            shim = compiled / 'node_modules/@kanbien/app-entity-smoke'
            manifest = json.loads((shim / 'package.json').read_text())
            self.assertEqual(manifest['exports'], {'.': './index.js'})
            probe = 'try { if (require(process.argv[1]).marker !== "compiled-entity") process.exit(2); } catch (error) { process.stdout.write(error.code); process.exit(1); }'
            result = subprocess.run(['node', '-e', probe, str(shim)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            target.unlink()
            missing = subprocess.run(['node', '-e', probe, str(shim)], capture_output=True, text=True)
            self.assertEqual((missing.returncode, missing.stdout), (1, 'MODULE_NOT_FOUND'))

    def test_platform_shell_entity_shim_failures_keep_safe_package_location(self):
        for phase, filename in (('shim-write', 'index.js'), ('manifest-write', 'package.json')):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(prefix='prepare-entity-failure-') as temporary:
                directory = Path(temporary)
                package = directory / '.cache/platform-shell-image-build/node_modules/@kanbien/app-entity-smoke'
                (package / filename).mkdir(parents=True)
                location = {'package': '@kanbien/app-entity-smoke'}
                if phase == 'shim-write': location['export'] = '.'
                self.run_preparer('platform-shell', directory, phase=phase,
                                  effect='earlier-writes-possible', location=location)
                self.assertTrue((package.parent / 'app-platform-smoke/package.json').is_file())

    def run_preparer(self, kind, directory, *, arguments=None, phase=None, effect=None, location=None):
        compiled = directory / CANARY
        args = [] if kind == "platform-shell" else ["--compiled-root", str(compiled)]
        result = subprocess.run(["node", str(ROOT / PREPARERS[kind]), *(args if arguments is None else arguments)], cwd=directory, capture_output=True, text=True, timeout=15)
        self.assertNotIn(CANARY, result.stdout + result.stderr)
        self.assertNotIn("Error:", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0 if phase is None else 1)
        if phase is not None:
            report = json.loads(result.stderr)
            self.assertEqual(report, {"scope": kind + "-runtime-preparation", "verdict": "failed", "code": "runtime-preparation-boundary-failed", "phase": phase, **(location or {}), "effect": effect})
        return compiled

    def stub_exports(self, compiled):
        # These files establish only the real preparer's existing presence
        # predicates; they are deliberately not compiled runtime proof.
        for home in ("packages/core/src", "platform", "infra/04.deploy/03.product/entrypoints"):
            for source in (ROOT / home).rglob("*.ts"):
                target = compiled / source.relative_to(ROOT).with_suffix(".js")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("module.exports = {};\n")

    def test_actual_argument_and_presence_rejections_before_writes(self):
        for kind in ("core-server", "core-server-persistence"):
            for args in ([], ["--private-" + CANARY, CANARY], ["--compiled-root", ""]):
                with self.subTest(kind=kind, args=args), tempfile.TemporaryDirectory(prefix="prepare-arguments-") as temporary:
                    directory = Path(temporary)
                    self.run_preparer(kind, directory, arguments=args, phase="arguments", effect="writes-not-started")
                    self.assertEqual(list(directory.iterdir()), [])
        with tempfile.TemporaryDirectory(prefix="prepare-exports-") as temporary:
            directory = Path(temporary)
            self.run_preparer("core-server-persistence", directory, phase="compiled-entrypoint", effect="writes-not-started", location={"entrypoint": "kanbien-core-server-persistence.main.js"})
            self.assertEqual(list(directory.iterdir()), [])
        with tempfile.TemporaryDirectory(prefix="prepare-required-export-") as temporary:
            directory = Path(temporary)
            compiled = directory / CANARY
            self.stub_exports(compiled)
            (compiled / "packages/core/src/index.js").unlink()
            self.run_preparer("core-server-persistence", directory, phase="compiled-export", effect="writes-not-started", location={"compiledExport": "packages/core/src/index.js"})
            self.assertFalse((compiled / "node_modules").exists())

    def test_actual_directory_and_write_failures_preserve_partial_effect(self):
        for kind in PREPARERS:
            for phase, filename in (("shim-directory", "block-root"), ("shim-write", "index.js"), ("manifest-write", "package.json")):
                with self.subTest(kind=kind, phase=phase), tempfile.TemporaryDirectory(prefix="prepare-native-") as temporary:
                    directory = Path(temporary)
                    compiled = directory / (".cache/platform-shell-image-build" if kind == "platform-shell" else CANARY)
                    self.stub_exports(compiled)
                    if phase == "shim-directory":
                        (compiled / "node_modules").write_text(CANARY)
                    else:
                        blocker = compiled / "node_modules/@kanbien/core" / filename
                        blocker.mkdir(parents=True)
                    location = {"package": "@kanbien/core"}
                    if phase != "manifest-write" and not (kind == "platform-shell" and phase == "shim-directory"):
                        location["export"] = "."
                    self.run_preparer(kind, directory, phase=phase, effect="earlier-writes-possible", location=location)
                    if phase == "manifest-write":
                        self.assertTrue((compiled / "node_modules/@kanbien/core/index.js").is_file())
                    self.assertFalse((compiled / "runtime-payload.json").exists())

    def test_successful_actual_preparation_and_late_wrapper_failure(self):
        for kind in PREPARERS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="prepare-success-") as temporary:
                directory = Path(temporary)
                compiled = directory / (".cache/platform-shell-image-build" if kind == "platform-shell" else CANARY)
                self.stub_exports(compiled)
                self.run_preparer(kind, directory)
                manifest = json.loads((compiled / "node_modules/@kanbien/core/package.json").read_text())
                self.assertEqual(manifest["exports"]["./security"], "./security/index.js")
                self.assertIn("module.exports = require(", (compiled / "node_modules/@kanbien/core/index.js").read_text())
        with tempfile.TemporaryDirectory(prefix="prepare-wrapper-") as temporary:
            directory = Path(temporary)
            compiled = directory / CANARY
            (compiled / "kanbien-core-server.main.js").mkdir(parents=True)
            self.run_preparer("core-server", directory, phase="wrapper-write", effect="earlier-writes-possible", location={"entrypoint": "kanbien-core-server.main.js"})
            self.assertTrue((compiled / "node_modules/@kanbien/core/package.json").is_file())
        for phase, filename in (("payload-manifest-write", "runtime-payload.json"), ("wrapper-write", "kanbien-core-server-persistence.main.js")):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(prefix="prepare-persistence-late-") as temporary:
                directory = Path(temporary)
                compiled = directory / CANARY
                self.stub_exports(compiled)
                (compiled / filename).mkdir()
                self.run_preparer("core-server-persistence", directory, phase=phase, effect="earlier-writes-possible", location={} if phase == "payload-manifest-write" else {"entrypoint": filename})
                self.assertTrue((compiled / "node_modules/@kanbien/core/package.json").is_file())

    def test_actual_payload_cli_and_native_read_boundaries(self):
        checker = ROOT / BASE / "build-core-server-image/verify-payload.py"
        for args in ([], ["--compiled-root"]):
            result = subprocess.run(["python3", "-B", str(checker), *args], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["diagnostics"], [{"code": "payload-check-argument-invalid"}])
            self.assertEqual(result.stderr, "")
        with tempfile.TemporaryDirectory(prefix="payload-native-") as temporary:
            compiled = Path(temporary) / CANARY
            compiled.mkdir()
            (compiled / payload.COMPILED_ENTRYPOINT).write_bytes(b"\xff" + CANARY.encode())
            with self.assertRaises(payload.PayloadFailure) as rejected:
                payload.validate_payload(compiled, {"payload": {"forbidden_dependency_ids": []}})
            self.assertEqual(rejected.exception.codes, ("compiled-payload-unreadable",))
            with patch.object(payload, "IMAGE_CONTRACT", compiled / payload.COMPILED_ENTRYPOINT):
                with self.assertRaises(payload.PayloadFailure) as malformed:
                    payload.validate_source_contracts()
            self.assertEqual(malformed.exception.codes, ("image-contract-invalid",))


if __name__ == "__main__":
    unittest.main()
