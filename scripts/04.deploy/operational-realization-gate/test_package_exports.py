#!/usr/bin/env python3
"""Source/export/compiler joins reject fabricated coverage and unsafe projection."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-package-exports
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise compiler-bound exports, alias evidence, explicit nonselection and safe repeat output membership.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).parent
sys.path.insert(0, str(DIRECTORY))
import package_exports as exports
import local_build_contracts as contracts
from package_export_inventory import discover_exports
from source_inventory import canonical, digest

SERVER = 'platform/server/tsconfig.runtime-test.json'
IMAGE = 'platform/server/tsconfig.image.json'
PRODUCT = 'products/kanbien-platform/tsconfig.runtime-test.json'
SENTINEL = 'DO-NOT-ECHO-PRIVATE-CONTENT'


def put(root, path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = content if isinstance(content, bytes) else content.encode() if isinstance(content, str) else canonical(content)
    target.write_bytes(raw)
    return {'path': path, 'digest': digest(raw), 'bytes': len(raw)}


def fixture(root, configuration=SERVER):
    put(root, 'package.json', {'private': True, 'workspaces': ['packages/*', 'platform/*']})
    put(root, 'packages/core/package.json', {'name': '@fixture/core', 'exports': {'.': './src/index.ts', './extra': './src/extra.ts'}})
    sources = [put(root, 'packages/core/src/index.ts', 'export const value = 1;\n'),
               put(root, 'packages/core/src/extra.ts', 'export const extra = 2;\n')]
    put(root, 'packages/outside/package.json', {'name': '@fixture/outside', 'exports': {'.': './src/index.ts'}})
    put(root, 'packages/outside/src/index.ts', 'export const other = 3;\n')
    config = put(root, configuration, {'compilerOptions': {'module': 'CommonJS'}})
    outroot = contracts.RUNTIME_LAYOUTS[configuration][0]
    outputs = [put(root, outroot + '/packages/core/src/index.js', 'exports.value = 1;\n'),
               put(root, outroot + '/packages/core/src/extra.js', 'exports.extra = 2;\n')]
    observation = {'schema': 'local-typescript-emission-observation/v1', 'configuration': configuration,
                   'node_version': '22.23.3', 'typescript_version': '5.9.3', 'verdict': 'passed',
                   'no_emit': False, 'emit_skipped': False,
                   'inputs': [{'kind': 'repository', **row} for row in [config, *sources]] + [
                       {'kind': 'dependency', 'path': 'node_modules/typescript/lib/typescript.js', 'digest': 'sha256:' + 'a' * 64, 'bytes': 1}],
                   'resolutions': [], 'outputs': outputs, 'diagnostics': [], 'findings': [],
                   'output_mode': 'fresh-exclusive', 'existing_remainder': [],
                   'emission_map': {'schema': 'local-typescript-emission-map/v1', 'module_kind': 'commonjs',
                                    'entries': [{'output_path': output['path'], 'source_paths': [source['path']], 'kind': 'javascript'}
                                                for source, output in zip(sources, outputs)]}}
    if configuration == IMAGE:
        alias = exports.SERVER_ALIAS
        put(root, alias['manifest'], {'name': alias['package'], 'exports': {'.': './src/index.ts'}})
        updated = put(root, configuration, {'compilerOptions': {'module': 'CommonJS', 'baseUrl': '../..',
                       'paths': {alias['specifier']: [alias['target']]}}})
        observation['inputs'][0] = {'kind': 'repository', **updated}
        for path, raw in [('platform/server/src/index.ts', 'export const server = 1;\n'),
                          (alias['target'], 'export const main = 2;\n'),
                          (alias['consumer'], 'import {main} from "' + alias['specifier'] + '";\n')]:
            source = put(root, path, raw)
            output = put(root, outroot + '/' + path[:-3] + '.js', 'exports.fixture = 1;\n')
            observation['inputs'].append({'kind': 'repository', **source})
            observation['outputs'].append(output)
            observation['emission_map']['entries'].append({'output_path': output['path'], 'source_paths': [path], 'kind': 'javascript'})
        observation['resolutions'].append({'from': alias['consumer'], 'specifier_digest': digest(alias['specifier'].encode()),
                                          'mode': 'require', 'resolved_path': alias['target'], 'is_external': False})
    observation['outputs'].sort(key=lambda row: row['path'])
    observation['emission_map']['entries'].sort(key=lambda row: row['output_path'])
    return exports.seal(observation, 'observation_digest')


class PackageExportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='package-export-fixture-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.observation = fixture(self.root)
        self.output_root = contracts.RUNTIME_LAYOUTS[SERVER][0]

    def prepare(self):
        return exports.prepare_projection(self.root, self.observation, self.root)

    def rejected(self):
        with self.assertRaises(Exception) as error:
            self.prepare()
        self.assertNotIn(SENTINEL, str(error.exception))

    def reseal(self):
        exports.seal(self.observation, 'observation_digest')

    def test_every_declaration_remains_visible_without_runtime_or_owner_claims(self):
        projection, result = self.prepare()
        self.assertEqual((result['declared_exports'], result['selected_exports'], result['outside_selected_exports']), (3, 2, 1))
        self.assertEqual(result['qualification_verdict'], 'blocked')
        self.assertEqual(result['review_verdict'], 'not-evaluated')
        self.assertEqual(len(projection['entries']), 2)
        self.assertTrue(any(row['code'] == 'opaque-export-target' for row in result['source_findings']))
        exports.check_reconciliation(result)

    def test_collected_names_values_are_hashed_in_public_inventory(self):
        inventory = discover_exports(self.root)
        self.assertNotIn('@fixture', json.dumps(inventory))
        self.assertNotIn('./extra', json.dumps(inventory))
        self.assertEqual(len(inventory['exports']), 3)
        self.assertEqual(len(inventory['manifests']), 2)
        exports.validate('source-package-export-inventory', inventory)

    def test_a_new_literal_export_is_independently_collected(self):
        manifest = {'name': '@fixture/core', 'exports': {'.': './src/index.ts', './extra': './src/extra.ts', './new': './src/new.ts'}}
        put(self.root, 'packages/core/package.json', manifest)
        put(self.root, 'packages/core/src/new.ts', 'export const next = 1;\n')
        inventory = discover_exports(self.root)
        self.assertEqual(len(inventory['exports']), 4)
        _, receipt = self.prepare()
        self.assertEqual(receipt['outside_selected_exports'], 2)

    def test_unemitted_required_export_is_not_treated_as_nonselected(self):
        self.observation['resolutions'].append({'from': 'packages/core/src/index.ts',
            'specifier_digest': digest(b'@fixture/outside'), 'mode': 'require',
            'resolved_path': 'packages/outside/src/index.ts', 'is_external': False})
        self.reseal()
        self.rejected()

    def test_missing_output_for_observed_source_is_blocked(self):
        self.observation['outputs'].pop()
        self.observation['emission_map']['entries'].pop()
        self.reseal()
        self.rejected()

    def test_manifest_conditions_wildcards_arrays_and_noncode_targets_block(self):
        original = (self.root / 'packages/core/package.json').read_bytes()
        for declared in ({'.': {'import': './src/index.ts'}}, {'./*': './src/*.ts'}, ['src/index.ts'], {'.': './data.json'}, {'.': '../outside.ts'}, {'./node_modules': './src/index.ts'}, {'./a/NoDe_MoDuLeS/deeper': './src/index.ts'}):
            with self.subTest(shape=type(declared).__name__):
                put(self.root, 'packages/core/package.json', {'name': '@fixture/core', 'exports': declared})
                self.rejected()
        (self.root / 'packages/core/package.json').write_bytes(original)

    def test_other_package_reference_fields_remain_blocking(self):
        for field in ('main', 'module', 'browser', 'imports', 'bin'):
            document = {'name': '@fixture/core', 'exports': {'.': './src/index.ts'}, field: './src/index.ts'}
            put(self.root, 'packages/core/package.json', document)
            self.rejected()

    def test_duplicate_package_names_are_not_merged(self):
        put(self.root, 'packages/outside/package.json', {'name': '@fixture/core', 'exports': {'.': './src/index.ts'}})
        self.rejected()

    def test_symlinked_export_target_is_rejected(self):
        target = self.root / 'packages/core/src/index.ts'
        target.unlink()
        target.symlink_to(self.root / 'packages/outside/src/index.ts')
        self.rejected()

    def test_stale_source_digest_rejects_otherwise_self_consistent_observation(self):
        put(self.root, 'packages/core/src/index.ts', SENTINEL)
        self.rejected()

    def test_stale_output_bytes_are_rejected(self):
        put(self.root, self.output_root + '/packages/core/src/index.js', SENTINEL)
        self.rejected()

    def test_legacy_mapless_receipt_cannot_supply_new_proof(self):
        self.observation['schema'] = 'local-typescript-observation/v1'
        for key in ('emission_map', 'existing_remainder', 'output_mode'):
            self.observation.pop(key)
        self.reseal()
        self.rejected()

    def test_declaration_only_output_cannot_replace_javascript(self):
        self.observation['emission_map']['entries'][0]['kind'] = 'declaration'
        self.reseal()
        self.rejected()

    def test_ambiguous_bundle_origin_is_not_a_unique_export(self):
        self.observation['emission_map']['entries'][0]['source_paths'].append('packages/core/src/extra.ts')
        self.reseal()
        self.rejected()

    def test_non_commonjs_emission_cannot_feed_require_shims(self):
        self.observation['emission_map']['module_kind'] = 'other'
        self.reseal()
        self.rejected()

    def test_extra_compiler_root_file_is_not_ignored(self):
        put(self.root, self.output_root + '/hidden.js', SENTINEL)
        self.rejected()

    def test_repeat_preparation_requires_exact_freshly_derived_generated_bytes(self):
        projection, _ = self.prepare()
        generated = exports.generated_files(projection)
        for name, raw in generated.items():
            put(self.root, self.output_root + '/' + name, raw)
        self.observation['output_mode'] = 'verify-existing'
        self.observation['existing_remainder'] = [{'path': self.output_root + '/' + row['path'], **{key: value for key, value in row.items() if key != 'path'}} for row in exports.fingerprint(generated)]
        self.reseal()
        again, result = self.prepare()
        self.assertEqual(exports.generated_files(again), generated)
        self.assertEqual(result['selected_exports'], 2)
        put(self.root, self.output_root + '/' + next(iter(generated)), SENTINEL)
        self.rejected()

    def test_reported_extra_files_do_not_become_trusted_generated_files(self):
        extra = put(self.root, self.output_root + '/node_modules/hidden/index.js', SENTINEL)
        self.observation['output_mode'] = 'verify-existing'
        self.observation['existing_remainder'] = [extra]
        self.reseal()
        self.rejected()

    def test_hidden_or_conflicting_projection_fields_are_rejected(self):
        projection, _ = self.prepare()
        projection['secret'] = SENTINEL
        exports.seal(projection, 'projection_digest')
        with self.assertRaises(Exception): exports.generated_files(projection)
        projection.pop('secret')
        projection['entries'].append(deepcopy(projection['entries'][0]))
        exports.seal(projection, 'projection_digest')
        with self.assertRaises(Exception): exports.generated_files(projection)

    def test_projection_cannot_escape_runtime_root(self):
        projection, _ = self.prepare()
        projection['entries'][0]['output_path'] = '../../' + SENTINEL
        exports.seal(projection, 'projection_digest')
        with self.assertRaises(Exception): exports.generated_files(projection)

    def test_reserved_file_subpaths_and_deeper_file_directory_conflicts_are_refused(self):
        projection, _ = self.prepare()
        for subpath in ('./package.json', './package.json/deeper', './a/index.js/deeper', './node_modules', './a/NoDe_MoDuLeS/deeper'):
            changed = deepcopy(projection)
            changed['entries'][0]['subpath'] = subpath
            exports.seal(changed, 'projection_digest')
            with self.assertRaises(Exception): exports.generated_files(changed)

    def test_nonselected_rows_require_both_output_fields_absent(self):
        _, receipt = self.prepare()
        for field in ('output_digest', 'output_path_digest'):
            changed = deepcopy(receipt)
            row = next(row for row in changed['exports'] if row['selection'] == 'outside-selected-compilation')
            row[field] = 'sha256:' + 'a' * 64
            exports.seal(changed, 'receipt_digest')
            with self.assertRaises(Exception): exports.check_reconciliation(changed)

    def test_duplicate_generated_fingerprint_cannot_self_hash_to_valid_receipt(self):
        _, receipt = self.prepare()
        receipt['generated_files'].append(deepcopy(receipt['generated_files'][0]))
        exports.seal(receipt, 'receipt_digest')
        with self.assertRaises(Exception): exports.check_reconciliation(receipt)

    def test_policy_change_during_preparation_invalidates_receipt(self):
        original = exports.policy_revision()
        with patch.object(exports, 'policy_revision', side_effect=[original, 'sha256:' + 'b' * 64]):
            self.rejected()

    def test_image_server_alias_is_distinct_and_bound_to_actual_import(self):
        self.observation = fixture(self.root, IMAGE)
        projection, result = self.prepare()
        self.assertEqual(len(result['aliases']), 1)
        alias = next(row for row in projection['entries'] if row['kind'] == 'executable-alias')
        self.assertEqual((alias['package_name'], alias['subpath']), ('@kanbien/platform-server', './main'))
        self.assertEqual(len(result['aliases'][0]['source_bindings']), 3)
        self.assertEqual(len([row for row in projection['entries'] if row['kind'] == 'package-export']), result['selected_exports'])

    def test_alias_without_real_resolution_is_rejected(self):
        self.observation = fixture(self.root, IMAGE)
        self.observation['resolutions'] = []
        self.reseal(); self.rejected()

    def test_alias_from_unrelated_consumer_cannot_supply_evidence(self):
        self.observation = fixture(self.root, IMAGE)
        self.observation['resolutions'][0]['from'] = 'packages/core/src/index.ts'
        self.reseal(); self.rejected()

    def test_alias_config_drift_rejects_even_with_updated_observation_checksum(self):
        self.observation = fixture(self.root, IMAGE)
        put(self.root, IMAGE, {'compilerOptions': {'module': 'CommonJS', 'paths': {}}})
        self.reseal(); self.rejected()

    def test_manifest_declared_main_uses_declaration_route_not_alias(self):
        self.observation = fixture(self.root, IMAGE)
        alias = exports.SERVER_ALIAS
        put(self.root, alias['manifest'], {'name': alias['package'], 'exports': {'.': './src/index.ts', './main': './src/main.ts'}})
        projection, result = self.prepare()
        self.assertEqual(result['aliases'], [])
        row = next(row for row in projection['entries'] if row['package_name'] == alias['package'] and row['subpath'] == './main')
        self.assertEqual(row['kind'], 'package-export')

    def workspace_resolution(self):
        self.observation['resolutions'].append({'from': 'packages/core/src/index.ts',
            'specifier_digest': digest(b'@fixture/core/extra'), 'mode': 'require',
            'resolved_path': 'packages/core/src/extra.ts', 'is_external': True})
        self.reseal()

    def test_external_classification_with_exact_workspace_origin_is_accepted(self):
        self.workspace_resolution()
        projection, receipt = self.prepare()
        self.assertEqual(receipt['selected_exports'], 2)
        self.assertEqual(len(projection['entries']), 2)
        self.assertTrue(self.observation['resolutions'][0]['is_external'])

    def test_actual_external_package_target_cannot_replace_workspace_origin(self):
        self.workspace_resolution()
        self.observation['resolutions'][0]['resolved_path'] = 'node_modules/other/index.ts'
        self.reseal(); self.rejected()

    def test_external_classification_never_waives_repository_source_or_emission(self):
        self.workspace_resolution()
        original = deepcopy(self.observation)
        for mutation in ('dependency-kind', 'source-digest', 'missing-emission', 'ambiguous-emission'):
            with self.subTest(mutation=mutation):
                self.observation = deepcopy(original)
                source = next(row for row in self.observation['inputs'] if row['path'] == 'packages/core/src/extra.ts')
                emitted = next(row for row in self.observation['emission_map']['entries'] if row['source_paths'] == [source['path']])
                if mutation == 'dependency-kind': source['kind'] = 'dependency'
                elif mutation == 'source-digest': source['digest'] = 'sha256:' + 'f' * 64
                elif mutation == 'missing-emission':
                    self.observation['emission_map']['entries'].remove(emitted)
                    self.observation['outputs'] = [row for row in self.observation['outputs'] if row['path'] != emitted['output_path']]
                else: emitted['source_paths'].append('packages/core/src/index.ts')
                self.reseal(); self.rejected()

    def test_required_resolution_cannot_point_elsewhere(self):
        self.observation['resolutions'].append({'from': 'packages/core/src/index.ts',
            'specifier_digest': digest(b'@fixture/core/extra'), 'mode': 'require',
            'resolved_path': 'packages/outside/src/index.ts', 'is_external': False})
        self.reseal(); self.rejected()


if __name__ == '__main__':
    unittest.main()
