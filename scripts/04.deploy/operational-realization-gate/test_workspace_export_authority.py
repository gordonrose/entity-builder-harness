"""Workspace export and emission observations never grant release or operation authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.workspace-export-authority
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Refuse compiler/export receipts and nested build results at the common authority boundary.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh
from copy import deepcopy
import unittest

import local_build_contracts
import result_consumption
from test_local_build_bindings import fixture

SCHEMAS = (
    'source-package-export-inventory/v1',
    'local-workspace-export-projection/v1',
    'local-package-export-reconciliation/v1',
    'local-workspace-runtime-observation/v1',
    'local-typescript-emission-observation/v1',
)


class WorkspaceExportAuthorityTests(unittest.TestCase):
    def assert_refused(self, document, purpose, code):
        decision = result_consumption.consume_result(document, purpose, expected_result=deepcopy(document))
        self.assertEqual(decision['verdict'], 'rejected')
        self.assertIs(decision['authorized'], False)
        self.assertEqual(decision['release_eligibility'], 'blocked')
        self.assertEqual(decision['operation_authorization'], 'blocked')
        self.assertEqual(decision['findings'], [{'code': code}])

    def test_new_schema_identifiers_are_not_registered_source_acceptance_producers(self):
        # Intentionally minimal payloads: refusal must be by producer identity,
        # before missing detail or matching expected bytes can matter.
        for schema in SCHEMAS:
            with self.subTest(schema=schema):
                self.assert_refused({'schema': schema, 'authorized': False}, 'source-analysis',
                                    'source-result-producer-unsupported')

    def test_new_schema_payloads_cannot_grant_any_authority_purpose(self):
        for schema in SCHEMAS:
            for purpose in ('release-eligibility', 'operation-authorization'):
                with self.subTest(schema=schema, purpose=purpose):
                    self.assert_refused({'schema': schema, 'authorized': True, 'verdict': 'passed'}, purpose,
                                        'source-result-authority-unavailable')

    def test_valid_legacy_nested_build_receipt_remains_unconsumable(self):
        document = fixture()
        local_build_contracts.result(document)
        self.assertEqual(document['schema'], 'local-build-result/v1')
        self.assertTrue(document['builds'])
        for purpose in ('source-analysis', 'release-eligibility', 'operation-authorization'):
            with self.subTest(purpose=purpose):
                code = ('source-result-producer-unsupported' if purpose == 'source-analysis'
                        else 'source-result-authority-unavailable')
                self.assert_refused(document, purpose, code)


if __name__ == '__main__':
    unittest.main()
