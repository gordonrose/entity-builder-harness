"""Keep disposable qualification inputs out of the deployable target definition."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.dependency-target-boundary
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: script
#   purpose: Run the existing target policy checker against isolated positive and malicious configuration copies.
#   portability: {class: internal, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
TARGET = Path("infra/04.deploy/03.product/targets/kanbien/staging")
ENTRYPOINTS = Path("infra/04.deploy/03.product/entrypoints")
CHECKER = Path("scripts/04.deploy/verify-platform-shell-postgresql-reference/script.sh")
RENDERER = Path("scripts/04.deploy/render-platform-shell-foundation-template/script.sh")
CERTIFICATE = Path("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt")


class DependencyTargetBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dependency-target-boundary-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                            "HOME": str(self.root), "GIT_CONFIG_NOSYSTEM": "1",
                            "GIT_CONFIG_GLOBAL": "/dev/null", "LC_ALL": "C",
                            "PYTHONDONTWRITEBYTECODE": "1"}
        shutil.copytree(ROOT / TARGET, self.root / TARGET, symlinks=True)
        for relative in (CHECKER, RENDERER, CERTIFICATE,
                         ENTRYPOINTS / "kanbien-platform-postgresql-task.ts",
                         ENTRYPOINTS / "kanbien-platform-postgresql-bootstrap.main.ts",
                         ENTRYPOINTS / "kanbien-platform-postgresql-migration.main.ts"):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        subprocess.run(["git", "init", "--quiet", str(self.root)],
                       env=self.environment, check=True, capture_output=True, timeout=10)

    def check(self):
        return subprocess.run(["bash", str(self.root / CHECKER)], cwd=self.root,
                              env=self.environment, capture_output=True, timeout=30)

    def test_normal_production_target_retains_pinned_ca_and_passes(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertIn(b"static policy check passed", result.stdout)

    def test_target_cannot_enable_local_qualification(self):
        self.inject("RELATIONAL_TLS_CA_MODE: local-qualification-v1")

    def test_target_cannot_supply_local_attempt_binding(self):
        self.inject("RELATIONAL_LOCAL_QUALIFICATION_ID: " + "a" * 32)

    def test_target_cannot_mount_the_local_fixture_ca(self):
        self.inject("qualification_ca: /run/release-control/ca.crt")

    def inject(self, text):
        (self.root / TARGET / "unsafe-qualification.yml").write_text(text + "\n")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"local qualification TLS inputs must never appear", result.stderr)

    def test_production_tls_cannot_be_downgraded(self):
        path = self.root / ENTRYPOINTS / "kanbien-platform-postgresql-task.ts"
        path.write_text(path.read_text().replace('mode: "verify-full"', 'mode: "require"'))
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"pinned RDS CA bundle and verify-full TLS", result.stderr)


if __name__ == "__main__":
    unittest.main()
