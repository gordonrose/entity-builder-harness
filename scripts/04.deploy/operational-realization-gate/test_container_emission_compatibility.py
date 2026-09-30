#!/usr/bin/env python3
"""Check historical and actual-emission build receipts through container readers."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.container-emission-compatibility-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Preserve historical container receipts while requiring complete modern compiler and runtime proofs.
#   portability: {class: internal, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import yaml
import local_container_contracts as containers
import local_build_contracts as builds
import package_exports as exports
import release_compiler
from source_inventory import SourceFailure
import test_local_container_contracts as historical
import test_local_runtime as runtime_fixture

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = ROOT / 'infra/04.deploy/contracts/release-control/v1'
OTHER = 'sha256:' + 'd' * 64


def reseal(value):
    row = value['build']['builds'][0]
    exports.seal(row['observation'], 'observation_digest')
    exports.seal(row['runtime'], 'receipt_digest')
    exports.seal(value['build'], 'result_digest')
    exports.seal(value, 'result_digest')
    return value


class ContainerEmissionCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value, profiles = historical.fixture()
        case = runtime_fixture.LocalRuntimeTests()
        case.setUp()
        try:
            case.generator_fixture(containers.CONFIGURATION)
            for profile in profiles:
                if (profile['image_scope'] == 'product'
                        and profile['command'][0] not in {row['path'] for row in case.observation['outputs']}):
                    case.add_compiled(profile['command'][0][len(containers.PREFIX):])
            case.dependency(name='pg')
            runtime = case.run_local()
            observed = deepcopy(case.observation)
            dependencies = deepcopy(case.closure['external_files'])
            production = deepcopy(case.closure['external_modules'])
        finally:
            case.tearDown()
        build = value['build']
        build['build_inventory_digest'] = runtime['source_inventory_digest']
        build['toolchain']['dependency_digest'] = runtime['dependency_tree_digest']
        build['builds'][0].update(observation=observed, runtime=runtime)
        payload = value['payload']
        cert = payload['certificate']
        payload['files'] = sorted(
            [{**row, 'path': containers.PREFIX + row['path']} for row in runtime['artifact_files']]
            + [{'path': containers.CERTIFICATE, 'digest': cert['digest'], 'bytes': cert['bytes']}] + dependencies,
            key=lambda row: row['path'])
        payload['production_dependencies'] = production
        payload['excluded_dependency_files'] = []
        payload['production_dependency_digest'] = containers.digest(dependencies)
        payload['payload_digest'] = containers.digest(payload['files'])
        value['image_payload_digest'] = payload['payload_digest']
        cls.modern = reseal(value)
        cls.profiles = profiles
        cls.production = production

    def setUp(self):
        self.value = deepcopy(self.modern)

    def reject(self, change):
        change(self.value)
        reseal(self.value)
        with self.assertRaises((release_compiler.ReleaseFailure, SourceFailure)):
            containers.validate_result(self.value, self.profiles, self.production)

    def test_historical_container_remains_valid_without_rewriting(self):
        value, profiles = historical.fixture()
        original = deepcopy(value)
        self.assertIs(value, containers.validate_result(value, profiles, value['payload']['production_dependencies']))
        self.assertEqual(original, value)

    def test_modern_compiler_and_runtime_validate_through_existing_container_reader(self):
        original = deepcopy(self.value)
        result = containers.validate_result(self.value, self.profiles, self.production)
        self.assertEqual('local-typescript-emission-observation/v1', result['build']['builds'][0]['observation']['schema'])
        self.assertEqual('local-workspace-runtime-observation/v1', result['build']['builds'][0]['runtime']['schema'])
        self.assertFalse(result['authorized'])
        self.assertEqual('blocked', result['qualification_verdict'])
        self.assertEqual(original, result)

    def test_embedded_build_schema_exactly_matches_authoritative_closed_schema(self):
        container = yaml.safe_load((SCHEMAS / 'local-container-result.schema.yml').read_text())
        expected = yaml.safe_load((SCHEMAS / 'local-build-result.schema.yml').read_text())
        expected.pop('$schema')
        expected.pop('$id')
        self.assertEqual(expected, container['properties']['build'])

    def test_rehashed_unknown_modern_observation_field_rejects(self):
        self.reject(lambda value: value['build']['builds'][0]['observation'].update(raw_output='redacted-fixture'))

    def test_rehashed_missing_actual_emission_map_rejects(self):
        self.reject(lambda value: value['build']['builds'][0]['observation'].pop('emission_map'))

    def test_rehashed_unknown_modern_runtime_field_rejects(self):
        self.reject(lambda value: value['build']['builds'][0]['runtime'].update(raw_output='redacted-fixture'))

    def test_rehashed_modern_runtime_authority_rejects(self):
        self.reject(lambda value: value['build']['builds'][0]['runtime'].update(authorized=True))

    def test_rehashed_wrong_driver_digest_rejects(self):
        self.reject(lambda value: value['build']['builds'][0]['runtime'].update(execution_driver_digest=OTHER))

    def test_rehashed_cross_observation_projection_rejects(self):
        def change(value):
            receipt = value['build']['builds'][0]['runtime']['workspace_exports']
            receipt['compiler_observation_digest'] = OTHER
            exports.seal(receipt, 'receipt_digest')
        self.reject(change)

    def test_rehashed_hidden_artifact_and_matching_payload_rejects(self):
        def change(value):
            hidden = {'path': 'node_modules/hidden/index.js', 'digest': OTHER, 'bytes': 6}
            value['build']['builds'][0]['runtime']['artifact_files'].append(hidden)
            payload = value['payload']
            payload['files'].append({**hidden, 'path': containers.PREFIX + hidden['path']})
            payload['files'].sort(key=lambda row: row['path'])
            payload['payload_digest'] = containers.digest(payload['files'])
            value['image_payload_digest'] = payload['payload_digest']
        self.reject(change)

    def test_rehashed_verify_existing_cannot_claim_locked_build(self):
        self.reject(lambda value: value['build']['builds'][0]['observation'].update(output_mode='verify-existing'))


if __name__ == '__main__':
    unittest.main()
