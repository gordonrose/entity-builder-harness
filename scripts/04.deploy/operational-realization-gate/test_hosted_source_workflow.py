"""Verify the prepared hosted source-validation workflow stays pinned and source-only."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.release-control-hosted-source-workflow
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines: [security, sre]
#   kind: test
#   purpose: Prevent workflow drift from the reviewed immutable source-validation command and permissions.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/release-control-source-validation.yml"


class HostedSourceWorkflowTests(unittest.TestCase):
    def test_pinned_actions_read_only_permission_and_supported_clean_command(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request: {}", text)
        self.assertIn("workflow_dispatch: {}", text)
        self.assertIn("contents: read", text)
        self.assertIn("timeout-minutes: 20", text)
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", text)
        self.assertIn("actions/setup-node@820762786026740c76f36085b0efc47a31fe5020", text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", text)
        self.assertIn('python-version: "3.14.4"', text)
        self.assertIn('node-version: "22.23.3"', text)
        self.assertIn("bash scripts/04.deploy/operational-realization-gate/verify-clean-environment.sh --python python3", text)
        self.assertNotIn("aws ", text)
        self.assertNotIn("id-token: write", text)
        self.assertNotIn("secrets.", text)


if __name__ == "__main__":
    unittest.main()

