#!/usr/bin/env python3
"""Execute the real shared Node renderer with compiler-shaped local fixtures."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.workspace-runtime-projection
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject saved projection bypasses, hidden files, special files and altered repeated runtime generation.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import package_exports as exports
import local_build_contracts as contracts
from test_package_exports import fixture, put, IMAGE, SERVER, PRODUCT, SENTINEL
from source_inventory import canonical, digest

ROOT = Path(__file__).resolve().parents[3]
NODE = shutil.which('node')


class WorkspaceRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='workspace-runtime-node-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.configuration = IMAGE
        self.observation = self.prepare(IMAGE)

    def prepare(self, configuration):
        observation = fixture(self.root, configuration)
        paths = [exports.SHARED_HELPER, contracts.RUNTIME_LAYOUTS[configuration][2]]
        for relative in paths:
            put(self.root, relative, (ROOT / relative).read_bytes())
        if configuration != IMAGE:
            outroot, _kind, _generator, testroot = contracts.RUNTIME_LAYOUTS[configuration]
            source = testroot + '/fixture-runtime.test.ts'
            source_row = put(self.root, source, 'export {};\n')
            output = put(self.root, outroot + '/' + testroot + '/fixture-runtime.test.js',
                         "if(require('@fixture/core').value!==1)process.exit(7);\n")
            observation['inputs'].append({'kind': 'repository', **source_row})
            observation['outputs'].append(output)
            observation['outputs'].sort(key=lambda row: row['path'])
            observation['emission_map']['entries'].append({'output_path': output['path'], 'source_paths': [source], 'kind': 'javascript'})
            observation['emission_map']['entries'].sort(key=lambda row: row['output_path'])
            exports.seal(observation, 'observation_digest')
        return observation

    def projection(self):
        return exports.prepare_projection(self.root, self.observation, self.root)[0]

    def run_driver(self, projection=None):
        projection = self.projection() if projection is None else projection
        put(self.root, exports.PROJECTION_INPUT, canonical(projection) + b'\n')
        put(self.root, exports.RUNTIME_DRIVER, exports.driver_bytes(self.configuration))
        return subprocess.run([NODE, exports.RUNTIME_DRIVER], cwd=self.root, capture_output=True, timeout=15)

    def assert_blocked(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(SENTINEL.encode(), result.stdout + result.stderr)

    def test_real_renderer_matches_python_bytes_and_accepts_exact_repeat(self):
        projection = self.projection()
        for _ in range(2):
            result = self.run_driver(projection)
            self.assertEqual(result.returncode, 0, result.stderr)
        for relative, raw in exports.generated_files(projection).items():
            self.assertEqual((self.root / projection['output_root'] / relative).read_bytes(), raw)

    def test_all_three_public_generators_refuse_saved_projection_flags_before_preparation(self):
        for configuration in (IMAGE, SERVER, PRODUCT):
            with self.subTest(configuration=configuration):
                self.prepare(configuration)
                generator = contracts.RUNTIME_LAYOUTS[configuration][2]
                result = subprocess.run([NODE, generator, '--projection', SENTINEL], cwd=self.root, capture_output=True, timeout=15)
                self.assert_blocked(result)
                self.assertIn(b'workspace-export-preparation-failed', result.stderr)

    def test_both_real_test_runners_resolve_freshly_generated_package(self):
        for configuration in (SERVER, PRODUCT):
            with self.subTest(configuration=configuration):
                self.configuration = configuration
                self.observation = self.prepare(configuration)
                result = self.run_driver()
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_source_only_projection_file_does_not_select_internal_route(self):
        projection = self.projection()
        put(self.root, exports.PROJECTION_INPUT, canonical(projection))
        # No Python observer exists in the fixture; a public caller must attempt
        # fresh preparation and fail, never consume this otherwise valid file.
        result = subprocess.run([NODE, contracts.RUNTIME_LAYOUTS[IMAGE][2]], cwd=self.root, capture_output=True, timeout=15)
        self.assert_blocked(result)
        self.assertFalse((self.root / projection['output_root'] / 'node_modules').exists())

    def test_extra_generated_file_blocks_before_any_new_write(self):
        projection = self.projection()
        put(self.root, projection['output_root'] + '/node_modules/hidden/index.js', SENTINEL)
        self.assert_blocked(self.run_driver(projection))
        self.assertFalse((self.root / projection['output_root'] / 'node_modules/@fixture').exists())

    def test_altered_repeat_shim_is_not_overwritten(self):
        projection = self.projection()
        self.assertEqual(self.run_driver(projection).returncode, 0)
        relative = next(iter(exports.generated_files(projection)))
        target = self.root / projection['output_root'] / relative
        target.write_text(SENTINEL)
        self.assert_blocked(self.run_driver(projection))
        self.assertEqual(target.read_text(), SENTINEL)

    def test_partial_previous_generation_is_not_silently_repaired(self):
        projection = self.projection()
        relative, raw = next(iter(exports.generated_files(projection).items()))
        put(self.root, projection['output_root'] + '/' + relative, raw)
        self.assert_blocked(self.run_driver(projection))

    def test_rehashed_unsafe_authority_extra_field_and_reserved_subpaths_block(self):
        projection = self.projection()
        for field, value in [('authorized', True), ('private_extra', SENTINEL)]:
            with self.subTest(field=field):
                changed = deepcopy(projection); changed[field] = value
                exports.seal(changed, 'projection_digest')
                self.assert_blocked(self.run_driver(changed))
        for subpath in ('./package.json', './package.json/deeper', './a/index.js/deeper', './node_modules', './a/NoDe_MoDuLeS/deeper'):
            changed = deepcopy(projection); changed['entries'][0]['subpath'] = subpath
            exports.seal(changed, 'projection_digest')
            self.assert_blocked(self.run_driver(changed))
        self.assertFalse((self.root / projection['output_root'] / 'node_modules').exists())

    def test_stale_output_bytes_refuse_saved_internally_passed_projection(self):
        projection = self.projection()
        put(self.root, projection['output_root'] + '/' + projection['entries'][0]['output_path'], SENTINEL)
        self.assert_blocked(self.run_driver(projection))

    def test_symlink_and_fifo_output_refused_without_blocking(self):
        projection = self.projection()
        target = self.root / projection['output_root'] / projection['entries'][0]['output_path']
        original = target.read_bytes(); target.unlink()
        target.symlink_to(self.root / 'package.json')
        self.assert_blocked(self.run_driver(projection)); target.unlink()
        os.mkfifo(target)
        self.assert_blocked(self.run_driver(projection)); target.unlink(); target.write_bytes(original)

    def test_symlinked_parent_output_directory_refused(self):
        projection = self.projection()
        target = self.root / projection['output_root']
        moved = target.with_name(target.name + '-actual'); target.rename(moved); target.symlink_to(moved)
        self.assert_blocked(self.run_driver(projection))

    def test_unrecognized_driver_generator_pair_cannot_execute_arbitrary_code(self):
        projection = self.projection()
        put(self.root, exports.PROJECTION_INPUT, canonical(projection))
        driver = exports.driver_bytes(IMAGE).replace(contracts.RUNTIME_LAYOUTS[IMAGE][2].encode(), SENTINEL.encode())
        put(self.root, exports.RUNTIME_DRIVER, driver)
        result = subprocess.run([NODE, exports.RUNTIME_DRIVER], cwd=self.root, capture_output=True, timeout=15)
        self.assert_blocked(result)


if __name__ == '__main__':
    unittest.main()
