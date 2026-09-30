#!/usr/bin/env python3
"""Mutation tests for fresh aggregate roots and complete literal dispatch grammar."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.release-control-estate-caller-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject missing callers, conflated lifecycle contexts, unsafe dispatch and stale source bindings.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import estate_caller_inventory as estate
from caller_inventory import discover_callers

FIXTURE = Path(__file__).parents[2] / 'operational-realization-gate/fixtures/estate-callers/sources.json'
WRAPPER = 'scripts/04.deploy/check/script.sh'
CHILD = 'scripts/04.deploy/check/script.py'
WORKFLOW = '.github/workflows/check.yml'


class EstateCallerInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='estate-callers-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = json.loads(FIXTURE.read_text())['files']
        for path, value in self.fixture.items():
            self.put(path, value)

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value))
        return target

    def graph(self):
        return estate.discover_estate_callers(self.root)

    def codes(self, graph):
        return {row['code'] for row in graph['findings'] + graph['diagnostics']}

    def proof_paths(self, graph):
        nodes = {row['id']: row for row in graph['nodes']}
        sources = {row['id']: row['path'] for row in graph['sources']}
        return [sources[nodes[row['node_id']]['source_id']] for row in graph['structural_proofs']]

    def body(self, name):
        sid = estate.digest(b'package.json')
        return estate.digest(estate.canonical([sid, 'package-command', ['scripts', name]]))

    def test_fixture_accounts_for_all_roots_without_claiming_children(self):
        graph = self.graph()
        self.assertEqual(len(graph['root_bindings']), 4)
        self.assertEqual(len(graph['structural_proofs']), 4)
        self.assertEqual(self.proof_paths(graph).count('package.json'), 3)
        self.assertIn(WRAPPER, self.proof_paths(graph))
        self.assertNotIn(CHILD, self.proof_paths(graph))
        self.assertIn('caller-script-body-unresolved', self.codes(graph))
        self.assertEqual(graph['diagnostics'], [])

    def test_collection_is_deterministic_and_does_not_execute_source(self):
        self.put(CHILD, 'raise RuntimeError("SENTINEL-DO-NOT-PRINT")\n')
        graph = self.graph()
        self.assertEqual(graph, self.graph())
        self.assertNotIn('SENTINEL-DO-NOT-PRINT', json.dumps(graph))

    def test_all_root_commands_discovered_even_without_workflow_callers(self):
        (self.root / WORKFLOW).unlink()
        package = copy.deepcopy(self.fixture['package.json'])
        package['scripts']['unused'] = 'python3 scripts/04.deploy/unused.py'
        self.put('package.json', package)
        self.put('scripts/04.deploy/unused.py', 'def unused(): pass\n')
        graph = self.graph()
        self.assertEqual(len(graph['root_bindings']), 4)
        self.assertIn('scripts/04.deploy/unused.py', {row['path'] for row in graph['sources']})

    def test_new_workflow_is_independently_discovered(self):
        before = self.graph()
        self.put('.github/workflows/new.yaml', self.fixture[WORKFLOW])
        after = self.graph()
        self.assertEqual(len(after['root_bindings']), len(before['root_bindings']) + 1)
        self.assertNotEqual(before['graph_digest'], after['graph_digest'])

    def test_automatic_and_explicit_hooks_have_distinct_contexts(self):
        package = copy.deepcopy(self.fixture['package.json'])
        package['scripts']['preprecheck'] = 'echo earlier'
        self.put('package.json', package)
        graph = self.graph()
        contexts = [row for row in graph['invocations'] if row['command_node_id'] == self.body('precheck')]
        self.assertEqual({row['lifecycle'] for row in contexts}, {False, True})
        false_node = next(row['node_id'] for row in contexts if not row['lifecycle'])
        true_node = next(row['node_id'] for row in contexts if row['lifecycle'])
        self.assertFalse(any(edge['caller_id'] == false_node and edge['kind'] != 'invokes' for edge in graph['edges']))
        self.assertTrue(any(edge['caller_id'] == true_node and edge['kind'] == 'npm-pre' for edge in graph['edges']))

    def test_pre_and_post_edges_target_automatic_contexts(self):
        graph = self.graph()
        contexts = {row['node_id']: row for row in graph['invocations']}
        hooks = [edge for edge in graph['edges'] if edge['kind'] in {'npm-pre', 'npm-post'}]
        self.assertEqual(len(hooks), 2)
        self.assertTrue(all(contexts[edge['caller_id']]['lifecycle'] and not contexts[edge['callee_id']]['lifecycle'] for edge in hooks))

    def test_script_body_is_shared_without_merging_invocation_context(self):
        graph = self.graph()
        self.assertEqual(sum(node['id'] == self.body('precheck') for node in graph['nodes']), 1)
        self.assertEqual(sum(row['command_node_id'] == self.body('precheck') for row in graph['invocations']), 2)

    def test_added_hook_invalidates_graph_and_is_linked(self):
        first = self.graph()
        package = copy.deepcopy(self.fixture['package.json'])
        package['scripts']['prepostcheck'] = 'echo extra'
        self.put('package.json', package)
        second = self.graph()
        self.assertNotEqual(first['graph_digest'], second['graph_digest'])
        self.assertIn(self.body('prepostcheck'), {node['id'] for node in second['nodes']})

    def test_npm_configuration_blocks_package_body_proof(self):
        self.put('.npmrc', 'script-shell=SENTINEL-DO-NOT-PRINT\n')
        graph = self.graph()
        self.assertFalse(graph['structural_proofs'])
        self.assertIn('caller-context-unsupported', self.codes(graph))
        self.assertNotIn('SENTINEL-DO-NOT-PRINT', json.dumps(graph))

    def test_unknown_arguments_context_is_not_silently_resolved(self):
        document = copy.deepcopy(self.fixture[WORKFLOW])
        document['jobs']['check']['steps'][0]['run'] = 'npm run check -- --extra value'
        self.put(WORKFLOW, document)
        self.assertIn('caller-arguments-unsupported', self.codes(self.graph()))

    def test_workflow_cwd_and_environment_remain_blocking(self):
        for key, value in [('working-directory', 'elsewhere'), ('env', {'PATH': 'SENTINEL-DO-NOT-PRINT'})]:
            with self.subTest(key=key):
                document = copy.deepcopy(self.fixture[WORKFLOW])
                document['jobs']['check']['steps'][0][key] = value
                self.put(WORKFLOW, document)
                graph = self.graph()
                self.assertIn('caller-context-unsupported', self.codes(graph))
                self.assertNotIn('SENTINEL-DO-NOT-PRINT', json.dumps(graph))

    def test_pinned_action_remains_unqualified(self):
        document = copy.deepcopy(self.fixture[WORKFLOW])
        document['jobs']['check']['steps'].append({'uses': 'actions/checkout@' + 'a' * 40})
        self.put(WORKFLOW, document)
        self.assertIn('caller-workflow-action-unresolved', self.codes(self.graph()))

    def test_extra_wrapper_command_prevents_whole_body_proof(self):
        self.put(WRAPPER, self.fixture[WRAPPER] + 'echo hidden\n')
        self.assertNotIn(WRAPPER, self.proof_paths(self.graph()))

    def test_changed_dispatch_target_is_bound_and_missing_target_stays_blocked(self):
        before = self.graph()
        self.put(WRAPPER, self.fixture[WRAPPER].replace(CHILD, 'scripts/04.deploy/missing.py'))
        after = self.graph()
        self.assertNotEqual(before['graph_digest'], after['graph_digest'])
        self.assertIn('caller-path-missing', self.codes(after))
        self.assertIn('scripts/04.deploy/missing.py', {row['path'] for row in after['sources']})

    def test_non_ascii_or_control_whitespace_cannot_forge_dispatch(self):
        for separator in ['\u00a0', '\u2028', '\v', '\f', '\r', '\x7f']:
            with self.subTest(separator=repr(separator)):
                self.put(WRAPPER, self.fixture[WRAPPER].replace('cd "$ROOT"', separator + 'cd "$ROOT"'))
                self.assertNotIn(WRAPPER, self.proof_paths(self.graph()))

    def test_non_ascii_package_command_cannot_forge_command_edges(self):
        package = copy.deepcopy(self.fixture['package.json'])
        package['scripts']['check'] = 'echo before\u2028bash ' + WRAPPER
        self.put('package.json', package)
        graph = self.graph()
        self.assertIn('caller-command-encoding-unsupported', self.codes(graph))
        self.assertNotIn(self.body('check'), {row['node_id'] for row in graph['structural_proofs']})

    def test_interpreter_substitution_does_not_inherit_bash_proof(self):
        package = copy.deepcopy(self.fixture['package.json'])
        package['scripts']['alternate'] = 'node ' + WRAPPER
        self.put('package.json', package)
        self.assertNotIn(WRAPPER, self.proof_paths(self.graph()))

    def test_arbitrary_python_and_test_filenames_are_not_resolved(self):
        self.put('scripts/04.deploy/test_hidden.py', 'def main(): return 0\n')
        graph = self.graph()
        self.assertNotIn('scripts/04.deploy/test_hidden.py', self.proof_paths(graph))
        self.assertNotIn(CHILD, self.proof_paths(graph))

    def test_cycles_remain_findings(self):
        self.put('package.json', {'scripts': {'check': 'npm run other', 'other': 'npm run check'}})
        self.assertIn('caller-cycle', self.codes(self.graph()))

    def test_symlink_target_is_not_followed(self):
        target = self.root / CHILD
        target.unlink()
        target.symlink_to('/etc/passwd')
        self.assertIn('caller-path-unreadable', self.codes(self.graph()))

    def test_source_mutation_during_collection_prevents_all_proofs(self):
        original = estate.discover
        calls = 0
        def changing(root):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.put(CHILD, 'def changed(): pass\n')
            return original(root)
        with patch.object(estate, 'discover', side_effect=changing):
            graph = self.graph()
        self.assertIn('estate-caller-source-changed', self.codes(graph))
        self.assertEqual(graph['structural_proofs'], [])

    def test_npm_config_appearance_during_collection_prevents_all_proofs(self):
        original = estate.discover
        calls = 0
        def changing(root):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.put('.npmrc', 'ignore-scripts=true\n')
            return original(root)
        with patch.object(estate, 'discover', side_effect=changing):
            graph = self.graph()
        self.assertIn('estate-caller-source-changed', self.codes(graph))
        self.assertEqual(graph['structural_proofs'], [])

    def test_helper_change_during_collection_prevents_all_proofs(self):
        real = estate.revision()
        with patch.object(estate, 'revision', side_effect=[real, 'sha256:' + 'a' * 64, 'sha256:' + 'a' * 64]):
            graph = self.graph()
        self.assertIn('estate-caller-collector-changed', self.codes(graph))
        self.assertEqual(graph['structural_proofs'], [])

    def test_root_limit_retains_explicit_failure_without_partial_proof(self):
        with patch.object(estate, 'MAX_ROOTS', 1):
            graph = self.graph()
        self.assertIn('estate-caller-limit-exceeded', self.codes(graph))
        self.assertEqual(graph['structural_proofs'], [])

    def test_old_selected_workflow_shape_remains_compatible(self):
        graph = discover_callers(self.root, WORKFLOW)
        self.assertEqual(graph['schema'], 'caller-inventory/v1')
        self.assertIn('entrypoint', graph)
        self.assertNotIn('root_bindings', graph)

    def test_new_collector_helper_bytes_change_revision(self):
        old = estate.revision()
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw + b'\n# changed\n' if path.name == 'estate_caller_inventory.py' else raw
        with patch.object(Path, 'read_bytes', changed):
            self.assertNotEqual(old, estate.revision())


if __name__ == '__main__':
    unittest.main()
