#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.runnable-program-build-validation
#   version: 2
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: testing
#   disciplines: [architecture, security]
#   kind: test
#   purpose: Prove actual generic contract enforcement invokes only the fixed read-only declaration reader and preserves legacy contracts.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.runnable-program-contract
#     path: scripts/04.deploy/lifecycle/20-build/runnable-program-contract/smoke-test.sh

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import yaml

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('program_contract', HERE / 'script.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


class BuildValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='program-contract-build-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.document = yaml.safe_load((HERE / 'fixtures/valid-contract.yml').read_text())
        self.legacy = yaml.safe_load((HERE / 'fixtures/valid-contract.yml').read_text())
        program = self.document['runnable_programs'][0]
        program.update(build={'kind': 'workspace-typescript', 'typescript_project': 'project.json'},
                       source_entrypoint='program.ts',
                       approved_dependencies=['application'], observed_dependencies=['application'], forbidden_dependencies=[])
        self.document['dependency_bindings'] = {'application': {'workspace_package': '@different/ledger'}}
        self.put('package.json', {'workspaces': ['packages/*']})
        self.put('packages/ledger/package.json', {'name': '@different/ledger', 'exports': {'.': './src/index.ts'}})
        self.put('packages/ledger/src/index.ts', 'export const value = 1;\n')
        self.put('project.json', {'include': ['packages/ledger/src']})
        self.put('program.ts', 'export const handler = async () => true;\n')
        self.save()

    def put(self, path, value):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value if isinstance(value, str) else json.dumps(value))

    def save(self):
        (self.root / 'program.yml').write_text(yaml.safe_dump(self.document, sort_keys=False))

    def command(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'script.py'), '--contract', 'program.yml', '--json'],
                                cwd=self.root, capture_output=True, text=True, check=False)
        self.assertEqual(result.stderr, '')
        return result.returncode, json.loads(result.stdout)

    def test_actual_renamed_contract_uses_manifest_closure_and_does_not_compile(self):
        before = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        code, report = self.command()
        self.assertEqual((code, report['verdict']), (0, 'passed'))
        self.assertEqual(before, {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})
        self.put('packages/other/package.json', {'name': '@different/other', 'exports': {'.': './src/index.ts'}})
        self.put('packages/other/src/index.ts', 'export const value = 2;')
        self.put('packages/ledger/package.json', {'name': '@different/ledger', 'exports': {'.': './src/index.ts'}, 'dependencies': {'@different/other': '0.0.0'}})
        code, report = self.command()
        self.assertEqual(code, 1)
        self.assertEqual(report['findings'], [{'code': 'workspace-dependency-not-approved'}])
        self.document['dependency_bindings']['other'] = {'workspace_package': '@different/other'}
        self.document['runnable_programs'][0]['approved_dependencies'].append('other')
        self.save()
        self.assertEqual(self.command()[0], 0)
        (self.root / 'packages/other/src/index.ts').unlink()
        self.assertEqual(self.command()[1]['findings'], [{'code': 'workspace-export-source-missing'}])

    def test_fixed_reader_call_and_safe_native_failure_boundaries(self):
        calls = []
        def run(argv, **options):
            calls.append((argv, options))
            return SimpleNamespace(returncode=0, stdout=json.dumps({'programId': 'generic-server', 'inputs': {}}))
        C.validate_declared_builds(self.document, str(self.root / 'program.yml'), root=self.root, run=run)
        self.assertEqual(calls, [(['node', str(HERE / 'build-inputs.mjs'), '--program', 'generic-server', '--contract', 'program.yml'],
                                  {'cwd': self.root, 'capture_output': True, 'text': True, 'timeout': 30, 'check': False})])
        for failure in (OSError('PRIVATE_CANARY'), subprocess.TimeoutExpired('PRIVATE_CANARY', 30), UnicodeError('PRIVATE_CANARY')):
            def fail(*args, **kwargs): raise failure
            with self.assertRaises(C.ContractFailure) as outcome:
                C.validate_declared_builds(self.document, str(self.root / 'program.yml'), root=self.root, run=fail)
            self.assertEqual(outcome.exception.codes, ('program-build-observation-unavailable',))
        for response in (SimpleNamespace(returncode=1, stdout='{"error":"PRIVATE_CANARY"}'),
                         SimpleNamespace(returncode=0, stdout='{"programId":"foreign","inputs":{}}')):
            with self.assertRaises(C.ContractFailure) as outcome:
                C.validate_declared_builds(self.document, str(self.root / 'program.yml'), root=self.root, run=lambda *a, **k: response)
            self.assertNotIn('PRIVATE_CANARY', str(outcome.exception))

    def test_legacy_contract_does_not_invoke_node_and_new_incomplete_fields_do_not_bypass(self):
        C.validate_declared_builds(self.legacy, '/does/not/exist', run=lambda *a, **k: self.fail('legacy launched reader'))
        self.document['dependency_bindings']['application'] = {'workspace_package': 'PRIVATE_CANARY'}
        self.save()
        code, report = self.command()
        self.assertEqual(code, 1)
        self.assertNotIn('PRIVATE_CANARY', json.dumps(report))
        self.assertEqual(report['findings'], [{'code': 'program-build-binding-invalid'}])
        del self.document['runnable_programs'][0]['build']
        self.save()
        self.assertEqual(self.command()[1]['findings'], [{'code': 'program-build-declaration-invalid'}])


if __name__ == '__main__':
    unittest.main(verbosity=2)
