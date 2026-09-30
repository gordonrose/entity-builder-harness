"""Closed preflight output contract, never operation completion or authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.relational-task-preflight-contract
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: test
#   purpose: Reject authority, payload and operation drift in the distinct database preflight result.
#   portability: {class: target-specific, targets: [kanbien/staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.run-platform-shell-postgresql-relational-smoke.readme
#     path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/README.md
from pathlib import Path
import unittest
import yaml
from jsonschema import Draft202012Validator
ROOT = Path(__file__).resolve().parents[3]

class PreflightContract(unittest.TestCase):
    def setUp(self):
        schema = yaml.safe_load((ROOT / 'infra/04.deploy/contracts/release-control/v1/relational-task-preflight.schema.yml').read_text())
        Draft202012Validator.check_schema(schema)
        self.validator = Draft202012Validator(schema)
        self.result = {'schema':'relational-task-preflight/v1','scope':'read-only-database-prerequisites','operation':'bootstrap','verdict':'passed','authorized':False}
    def rejects(self, **values):
        self.result.update(values)
        self.assertTrue(list(self.validator.iter_errors(self.result)))
    def test_fixed_pass_and_failure_for_each_operation(self):
        for operation in ('bootstrap','migration','relay','worker','restore-verify'):
            for verdict in ('passed','failed'):
                self.result.update(operation=operation,verdict=verdict)
                self.validator.validate(self.result)
    def test_raw_extra_payload_rejected(self): self.rejects(secret='canary')
    def test_authority_rejected(self): self.rejects(authorized=True)
    def test_unknown_operation_rejected(self): self.rejects(operation='arbitrary-command')
    def test_operation_effect_scope_rejected(self): self.rejects(scope='operation-completed')
    def test_release_qualification_rejected(self): self.rejects(verdict='qualified')
    def test_missing_scope_rejected(self):
        del self.result['scope']
        self.assertTrue(list(self.validator.iter_errors(self.result)))

if __name__ == '__main__': unittest.main()
