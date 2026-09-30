#!/usr/bin/env python3
"""Direct preparation emits only freshly checked normalized output."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-package-exports-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Refuse unsafe normalized output, source drift, arbitrary executable selectors and unbounded observer I/O.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import package_exports as exports
import package_exports_cli as cli
from test_package_exports import fixture, put, SERVER, SENTINEL


class PackageExportsCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='package-export-cli-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        observation = fixture(self.root)
        observation["output_mode"] = "verify-existing"
        exports.seal(observation, "observation_digest")
        self.observation = observation
        self.projection = exports.prepare_projection(self.root, observation, self.root)[0]
        self.arguments = ['--prepare-existing', '--source-root', str(self.root), '--configuration', SERVER]

    def invoke(self, document=None, arguments=None, error=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(cli, 'prepare', side_effect=error, return_value=(self.projection if document is None else document, self.observation)), redirect_stdout(stdout), redirect_stderr(stderr):
            status = cli.main(self.arguments if arguments is None else arguments)
        self.assertEqual(stderr.getvalue(), '')
        self.assertNotIn(SENTINEL, stdout.getvalue())
        return status, json.loads(stdout.getvalue())

    def test_normalized_projection_is_revalidated_immediately_before_emission(self):
        status, document = self.invoke()
        self.assertEqual(status, 0)
        self.assertEqual(document, self.projection)

    def test_rehashed_extra_fields_and_authority_are_not_printed(self):
        for field, value in [('extra', SENTINEL), ('authorized', True), ('scope', SENTINEL)]:
            with self.subTest(field=field):
                changed = deepcopy(self.projection); changed[field] = value; exports.seal(changed, 'projection_digest')
                self.assertEqual(self.invoke(changed)[0], 1)

    def test_rehashed_invented_or_dropped_declarations_are_refused(self):
        for kind in ('name', 'subpath', 'drop', 'alias'):
            changed = deepcopy(self.projection)
            if kind == 'name': changed['entries'][0]['package_name'] = '@invented/package'
            elif kind == 'subpath': changed['entries'][0]['subpath'] = './invented'
            elif kind == 'drop': changed['entries'].pop()
            else: changed['entries'][0]['kind'] = 'executable-alias'
            exports.seal(changed, 'projection_digest')
            self.assertEqual(self.invoke(changed)[0], 1)

    def test_bad_digest_and_stale_policy_are_refused(self):
        for field in ('projection_digest', 'policy_revision'):
            changed = deepcopy(self.projection); changed[field] = 'sha256:' + 'a' * 64
            if field != 'projection_digest': exports.seal(changed, 'projection_digest')
            self.assertEqual(self.invoke(changed)[0], 1)

    def test_current_source_change_refuses_self_consistent_old_result(self):
        put(self.root, 'packages/core/src/index.ts', SENTINEL)
        self.assertEqual(self.invoke()[0], 1)

    def test_current_compiler_output_change_refuses_old_result(self):
        put(self.root, self.projection['output_root'] + '/' + self.projection['entries'][0]['output_path'], SENTINEL)
        self.assertEqual(self.invoke()[0], 1)

    def test_argument_and_executable_selectors_fail_safely(self):
        for extra in (['--node', SENTINEL], ['--projection', SENTINEL], ['--configuration', SENTINEL], ['--unknown', SENTINEL], ['--prepare-existing']):
            self.assertEqual(self.invoke(arguments=self.arguments + extra)[0], 1)

    def test_error_messages_do_not_echo_exceptions_or_input(self):
        self.assertEqual(self.invoke(error=RuntimeError(SENTINEL))[0], 1)

    def test_observer_reader_refuses_symlink_fifo_and_oversize(self):
        path = self.root / 'receipt.json'
        path.symlink_to(self.root / 'package.json')
        with self.assertRaises(Exception): cli.read_observation(path)
        path.unlink(); os.mkfifo(path)
        with self.assertRaises(Exception): cli.read_observation(path)
        path.unlink()
        with path.open('wb') as stream: stream.truncate(16 * 1024 * 1024 + 1)
        with self.assertRaises(Exception): cli.read_observation(path)

    def test_subprocess_output_and_time_are_bounded(self):
        descriptor = os.open('/dev/null', os.O_RDONLY)
        try:
            for program in ('print("x"*70000)', 'import sys;sys.stderr.write("x")', 'import time;time.sleep(3)'):
                with self.assertRaises(Exception): cli.bounded_run([sys.executable, '-c', program], self.root, descriptor, timeout=0.3)
            cli.bounded_run([sys.executable, '-c', 'pass'], self.root, descriptor, timeout=2)
        finally: os.close(descriptor)

    def test_plain_python_invocation_cannot_choose_an_arbitrary_node_binary(self):
        with self.assertRaises(Exception): cli.invoking_node()


if __name__ == '__main__':
    unittest.main()
