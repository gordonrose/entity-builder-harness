"""Selected baseline/candidate binding has complete gates but never source authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.selected-admission
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Prove selected admission bindings, source-only refusal and public wrapper safety.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.selected-admission
#     path: scripts/04.deploy/operational-realization-gate/selected_admission.py
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
sys.path.insert(0, str(DIRECTORY))
import selected_admission as admission
import selected_admission_cli as cli

BLUEPRINT = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/target-release-blueprint.v1.yml"
REVISION = "a" * 40
IMAGE = "sha256:" + "b" * 64
SENTINEL = "SENSITIVE-ADMISSION-INPUT-MUST-NOT-ESCAPE"


class SelectedAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = cli.load_compiler()
        document = compiler.release.load_document(BLUEPRINT)
        cls.baseline = compiler.compile_blueprint(ROOT, document, REVISION, IMAGE, "staging-admission-baseline")
        cls.candidate = compiler.compile_blueprint(ROOT, document, REVISION, IMAGE, "staging-admission-candidate")
        cls.result = admission.compile_admission(cls.baseline, cls.candidate)

    def reject(self, callback, *args, **kwargs):
        with self.assertRaises(admission.AdmissionFailure):
            callback(*args, **kwargs)

    def test_real_selected_graph_generates_closed_requests_for_every_operation(self):
        result = self.result
        self.assertEqual((result["schema"], result["scope"], result["verdict"]),
                         ("selected-admission-result/v1", "selected-staging-admission", "compiled"))
        self.assertFalse(result["authorized"])
        self.assertEqual((result["release_eligibility"], result["operation_authorization"], result["qualification_verdict"]),
                         ("blocked", "blocked", "blocked"))
        self.assertEqual(17, len(result["acceptance"]))
        self.assertEqual(tuple(admission.GATES), tuple(row["gate"] for row in result["acceptance"]))
        self.assertEqual(13, len(result["operation_requests"]))
        self.assertEqual({row["operation_id"] for row in result["operation_requests"]},
                         {row["operation_id"] for row in self.candidate["compiled_release"]["operation_graph"]})
        self.assertNotEqual(result["baseline"]["release_digest"], result["candidate"]["release_digest"])
        self.assertEqual([{"code": "admission-evidence-unavailable"}, {"code": "admission-authority-unavailable"}], result["findings"])

    def test_result_rejects_unsafe_fields_mutable_bindings_and_gate_damage(self):
        changes = (
            lambda value: value.update(secret=SENTINEL),
            lambda value: value["candidate"].update(source_revision="main"),
            lambda value: value["acceptance"].pop(),
            lambda value: value["acceptance"].reverse(),
            lambda value: value["operation_requests"][0].update(authority_status="approved"),
            lambda value: value["operation_requests"][0].update(candidate_release_digest="sha256:" + "f" * 64),
        )
        for change in changes:
            with self.subTest(change=change):
                value = deepcopy(self.result)
                change(value)
                if "result_digest" in value:
                    value["result_digest"] = admission.digest({key: row for key, row in value.items() if key != "result_digest"})
                self.reject(admission.validate_result, value)

    def test_same_release_id_cannot_bind_different_content(self):
        baseline = deepcopy(self.baseline["compiled_release"])
        candidate = deepcopy(self.candidate["compiled_release"])
        candidate["acceptance_matrix"][0]["bindings"]["release_id"] = baseline["acceptance_matrix"][0]["bindings"]["release_id"]
        candidate["acceptance_matrix"][0]["bindings"]["release_digest"] = "sha256:" + "e" * 64
        with patch.object(admission, "_source_result", side_effect=(baseline, candidate)):
            self.reject(admission.compile_admission, self.baseline, self.candidate)

    def test_compiled_source_result_or_boolean_cannot_authorize_execution(self):
        self.reject(admission.require_execution_authority, self.result)
        for value in (True, {"authorized": False}, self.candidate):
            with self.subTest(value=type(value).__name__):
                self.reject(admission.require_execution_authority, value)

    def test_invalid_selected_source_result_is_rejected_without_echo(self):
        value = deepcopy(self.candidate)
        value["compiled_release"]["acceptance_matrix"][0]["verdict"] = "passed"
        self.reject(admission.compile_admission, self.baseline, value)

    def invoke_cli(self, argv):
        output, error = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            status = cli.main(argv)
        self.assertEqual("", error.getvalue())
        self.assertNotIn(SENTINEL, output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())
        return status, json.loads(output.getvalue())

    def test_cli_rejects_duplicate_missing_and_mixed_modes_before_source_read(self):
        args = ["--selected-admission", "--baseline-result", SENTINEL, "--blueprint", SENTINEL,
                "--source-root", SENTINEL, "--source-revision", REVISION, "--image-digest", IMAGE,
                "--release-id", "selected-admission-test", "--json"]
        variants = (args + ["--release-id", "duplicate"], args[:-3] + ["--json"], args + ["--selected-readiness"],
                    [item.replace("--source-revision", "--source-rev") for item in args])
        with patch.object(cli, "load_compiler") as loader:
            for argv in variants:
                with self.subTest(argv=argv):
                    status, result = self.invoke_cli(argv)
                    self.assertEqual(1, status)
                    self.assertEqual("selected-admission-error/v1", result["schema"])
                    self.assertFalse(result["authorized"])
            loader.assert_not_called()

    def test_cli_compiles_candidate_against_saved_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            baseline_path = Path(temporary) / "baseline.json"
            baseline_path.write_text(json.dumps(self.baseline), encoding="utf-8")
            argv = ["--selected-admission", "--baseline-result", str(baseline_path), "--blueprint", str(BLUEPRINT),
                    "--source-root", str(ROOT), "--source-revision", REVISION, "--image-digest", IMAGE,
                    "--release-id", "staging-admission-candidate", "--json"]
            status, result = self.invoke_cli(argv)
        self.assertEqual(0, status)
        self.assertEqual(self.result, result)

    def test_existing_gate_dispatches_only_the_selected_admission_mode(self):
        command = subprocess.run([sys.executable, str(DIRECTORY / "script.py"), "--selected-admission"],
                                 cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(1, command.returncode)
        self.assertEqual("", command.stderr)
        result = json.loads(command.stdout)
        self.assertEqual("selected-admission-error/v1", result["schema"])
        self.assertEqual("arguments-invalid", result["findings"][0]["code"])

    def test_common_guard_rejects_admission_for_every_authority_purpose(self):
        import result_consumption as consumption
        for purpose in ("source-analysis", "release-eligibility", "operation-authorization"):
            with self.subTest(purpose=purpose):
                decision = consumption.consume_result(self.result, purpose, self.result)
                self.assertEqual("rejected", decision["verdict"])
                self.assertFalse(decision["authorized"])
                self.assertEqual("blocked", decision["release_eligibility"])
                self.assertEqual("blocked", decision["operation_authorization"])

if __name__ == "__main__":
    unittest.main()
