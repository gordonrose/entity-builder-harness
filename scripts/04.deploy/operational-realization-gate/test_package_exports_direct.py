#!/usr/bin/env python3
"""Exercise genuine small compilation followed by the existing direct Node route."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-package-exports-direct
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove direct preparation re-emits with pinned versions and refuses stale or extra artifacts without repairing them.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

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
from test_package_exports import put, SERVER, SENTINEL
import package_exports as exports

ROOT = Path(__file__).resolve().parents[3]


class DirectPackageExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node, typescript = os.environ.get('RELEASE_CONTROL_NODE'), os.environ.get('RELEASE_CONTROL_TYPESCRIPT_ROOT')
        if not node or not typescript:
            if os.environ.get('RELEASE_CONTROL_REQUIRE_TYPESCRIPT_TESTS') == '1':
                raise RuntimeError('Verified compiler fixture toolchain was not supplied')
            raise unittest.SkipTest('Verified Node/TypeScript fixture toolchain is required')
        cls.node, cls.typescript = Path(node).resolve(strict=True), Path(typescript).resolve(strict=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='workspace-direct-compiler-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'source'; self.root.mkdir()
        self.receipt = self.root.parent / 'observation.json'

    def prepare_source(self, *, workspace_link=False):
        for relative in ('scripts/04.deploy/operational-realization-gate', 'scripts/04.deploy/release-control/discovery',
                         'infra/04.deploy/contracts/release-control/v1'):
            for source in (ROOT / relative).iterdir():
                if source.suffix in ('.py', '.mjs', '.yml'):
                    put(self.root, relative + '/' + source.name, source.read_bytes())
        for relative in (exports.SHARED_HELPER, 'platform/server/tests/run-runtime-tests.mjs'):
            put(self.root, relative, (ROOT / relative).read_bytes())
        shutil.copytree(self.typescript, self.root / 'node_modules/typescript')
        put(self.root, 'package.json', {'private': True, 'workspaces': ['packages/*']})
        put(self.root, 'packages/core/package.json', {'name': '@fixture/core', 'exports': {'.': './src/index.ts', './extra': './src/extra.ts'}})
        put(self.root, 'packages/core/src/index.ts', 'export const value = 1;\n')
        put(self.root, 'packages/core/src/extra.ts', 'export const extra = 2;\n')
        put(self.root, 'platform/server/tests/example-runtime.test.ts',
            'import {value} from "@fixture/core"; if(value !== 1) throw new Error("fixture-failed");\n')
        put(self.root, SERVER, {'compilerOptions': {'module': 'CommonJS', 'target': 'ES2022', 'strict': True,
            'rootDir': '../..', 'outDir': '../../.cache/platform-server-runtime', 'baseUrl': '../..',
            'paths': {'@fixture/core': ['packages/core/src/index.ts']}},
            'include': ['../../packages/core/src/**/*.ts', 'tests/example-runtime.test.ts']})
        if workspace_link:
            configuration = json.loads((self.root / SERVER).read_text())
            configuration['compilerOptions'].pop('paths')
            put(self.root, SERVER, configuration)
            manifest = json.loads((self.root / 'packages/core/package.json').read_text())
            manifest['types'] = './src/index.ts'
            put(self.root, 'packages/core/package.json', manifest)
            link = self.root / 'node_modules/@fixture/core'
            link.parent.mkdir(parents=True)
            link.symlink_to('../../packages/core')
        result = subprocess.run([str(self.node), 'scripts/04.deploy/operational-realization-gate/typescript_observer.mjs',
            '--root', str(self.root), '--config', SERVER, '--output', str(self.receipt)], cwd=self.root,
            capture_output=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.output = self.root / '.cache/platform-server-runtime'

    def invoke(self):
        result = subprocess.run([str(self.node), 'platform/server/tests/run-runtime-tests.mjs'], cwd=self.root,
            capture_output=True, timeout=60)
        self.assertNotIn(SENTINEL.encode(), result.stdout + result.stderr)
        return result

    def test_actual_compilation_direct_runtime_and_exact_repeat_pass(self):
        self.prepare_source()
        for _ in range(2):
            result = self.invoke()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.output / 'node_modules/@fixture/core/package.json').is_file())

    def test_genuine_workspace_resolution_keeps_external_flag_and_runs_emitted_package(self):
        self.prepare_source(workspace_link=True)
        observation = json.loads(self.receipt.read_text())
        matches = [row for row in observation['resolutions']
                   if row['specifier_digest'] == exports.digest(b'@fixture/core')]
        self.assertEqual(len(matches), 1)
        self.assertTrue(matches[0]['is_external'])
        self.assertEqual(matches[0]['resolved_path'], 'packages/core/src/index.ts')
        source = next(row for row in observation['inputs'] if row['path'] == matches[0]['resolved_path'])
        self.assertEqual(source['kind'], 'repository')
        projection, receipt = exports.prepare_projection(self.root, observation, self.root)
        self.assertEqual(receipt['selected_exports'], 2)
        self.assertEqual(len(projection['entries']), 2)
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_changed_source_is_not_repaired_or_accepted_against_old_outputs(self):
        self.prepare_source()
        target = self.output / 'packages/core/src/index.js'; before = target.read_bytes()
        put(self.root, 'packages/core/src/index.ts', 'export const value = 9;\n')
        self.assertNotEqual(self.invoke().returncode, 0)
        self.assertEqual(target.read_bytes(), before)

    def test_unknown_leftover_is_not_treated_as_a_prior_generated_shim(self):
        self.prepare_source()
        put(self.output, 'node_modules/hidden/index.js', SENTINEL)
        self.assertNotEqual(self.invoke().returncode, 0)
        self.assertFalse((self.output / 'node_modules/@fixture/core').exists())

    def test_changed_manifest_cannot_reuse_the_old_runtime_map(self):
        self.prepare_source()
        self.assertEqual(self.invoke().returncode, 0)
        put(self.root, 'packages/core/package.json', {'name': '@invented/core', 'exports': {'.': './src/index.ts', './extra': './src/extra.ts'}})
        self.assertNotEqual(self.invoke().returncode, 0)
        self.assertFalse((self.output / 'node_modules/@invented').exists())


if __name__ == '__main__':
    unittest.main()
