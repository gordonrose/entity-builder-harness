"""Verify selected candidate and relational callers stop at the shared receipt boundary."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.selected-effect-control
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: test
#   purpose: Prove selected source routes bind declared operations and refuse every effect mode before AWS.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
import json
from pathlib import Path
import subprocess
import sys
import unittest

import selected_admission as admission
import selected_admission_cli as admission_cli
import selected_effect_control as control

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BLUEPRINT = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/target-release-blueprint.v1.yml"
REVISION = "a" * 40
IMAGE = "sha256:" + "b" * 64


class SelectedEffectControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = admission_cli.load_compiler()
        blueprint = compiler.release.load_document(BLUEPRINT)
        baseline = compiler.compile_blueprint(ROOT, blueprint, REVISION, IMAGE, "effect-control-baseline")
        candidate = compiler.compile_blueprint(ROOT, blueprint, REVISION, IMAGE, "effect-control-candidate")
        cls.admission = admission.compile_admission(baseline, candidate)

    def reject(self, callback, *args):
        with self.assertRaises(control.EffectControlFailure) as found:
            callback(*args)
        self.assertIn(found.exception.code, {
            "selected-effect-route-invalid", "selected-live-control-receipt-required",
            "selected-effect-admission-invalid", "selected-effect-admission-binding-invalid",
        })

    def test_candidate_and_relational_routes_bind_only_declared_admission_operations(self):
        candidate = control.source_route("candidate-execution-preflight", "execute", self.admission)
        relational = control.source_route("postgresql-relational-smoke", "execute", self.admission)
        self.assertEqual(["candidate-server"], candidate["operation_ids"])
        self.assertEqual(
            ["bootstrap", "migration", "relational-relay", "relational-worker", "restore-verify"],
            relational["operation_ids"])
        self.assertEqual(self.admission["result_digest"], candidate["admission_digest"])
        self.assertFalse(candidate["authorized"])
        self.assertEqual("blocked", relational["operation_authorization"])

    def test_invalid_mode_tampering_and_source_authority_are_refused(self):
        route = control.source_route("candidate-execution-preflight", "execute")
        route["operation_ids"] = ["bootstrap"]
        self.reject(control.validate_route, route)
        self.reject(control.source_route, "candidate-execution-preflight", "execute-bootstrap-recovery")
        self.reject(control.require_effect_authority, "candidate-execution-preflight", "execute", self.admission)

    def test_every_existing_effect_mode_fails_before_a_provider_call(self):
        cases = (
            ("scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py",
             ("--execute", "--approve-candidate-execution-preflight"), "candidate_execution_preflight"),
            ("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py",
             ("--execute", "--approve-relational-stage6"), "postgresql_relational_smoke"),
            ("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py",
             ("--execute-bootstrap-recovery", "--approve-relational-bootstrap-recovery"),
             "postgresql_relational_bootstrap_recovery"),
            ("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py",
             ("--execute-recovery-continuation", "--approve-relational-recovery-continuation"),
             "postgresql_relational_recovery_continuation"),
            ("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py",
             ("--diagnose-bootstrap-recovery", "--approve-relational-bootstrap-recovery-diagnostic"),
             "postgresql_relational_bootstrap_recovery_diagnostic"),
        )
        for path, arguments, output_key in cases:
            with self.subTest(path=path, arguments=arguments):
                result = subprocess.run([sys.executable, "-B", str(ROOT / path), *arguments],
                                        cwd=ROOT, text=True, capture_output=True, check=False)
                self.assertEqual("", result.stderr)
                self.assertEqual(1, result.returncode)
                payload = json.loads(result.stdout)
                self.assertIn(output_key, payload)
                self.assertNotEqual("passed", payload[output_key])


if __name__ == "__main__":
    unittest.main()

