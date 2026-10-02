"""Statically account for every selected legacy caller and its shared guard."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.selected-effect-caller-guard
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: test
#   purpose: Reject a selected caller whose provider path is not preceded by the shared receipt boundary.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "scripts/04.deploy/operational-realization-gate"
CALLERS = {
    ROOT / "scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py":
        ("require_selected_effect_control()", "return execute(policy)"),
    ROOT / "scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py":
        ("require_selected_effect_control(parsed)", "execute_bootstrap_recovery(policy)",
         "execute_recovery_continuation(policy)", "diagnose_bootstrap_recovery(policy)", "execute(policy)"),
}


class SelectedEffectCallerGuardTests(unittest.TestCase):
    def test_every_selected_legacy_provider_path_has_one_shared_guard_first(self):
        for path, required in CALLERS.items():
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                guard = text.index(required[0], text.index("def main"))
                for provider_call in required[1:]:
                    self.assertLess(guard, text.index(provider_call, text.index("def main")))

    def test_only_the_documented_source_route_command_is_exposed(self):
        result = subprocess.run(
            [sys.executable, "-B", str(GATE / "selected_effect_control_cli.py"),
             "--selected-effect-route", "--route", "candidate-execution-preflight", "--mode", "execute", "--json"],
            cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)
        self.assertIn('"operation_authorization": "blocked"', result.stdout)
        self.assertNotIn("aws", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()

