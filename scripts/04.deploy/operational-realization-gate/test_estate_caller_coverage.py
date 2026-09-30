#!/usr/bin/env python3
"""Reject declaration waivers and stale aggregate caller structural evidence."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-estate-caller-coverage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Keep fresh machine dispatch accounting separate from unreviewed adoption and unknown implementation semantics.
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
import source_coverage as coverage
import estate_caller_coverage as reconcile
import estate_caller_inventory as estate
from source_inventory import discover
from test_source_coverage import fixture_composition

FIXTURE = Path(__file__).parent / 'fixtures/estate-callers/sources.json'


class EstateCallerCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='estate-reconciliation-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.files = json.loads(FIXTURE.read_text())['files']
        for path, value in self.files.items():
            self.put(path, value)
        self.inventory = discover(self.root)
        self.graph = estate.discover_estate_callers(self.root)

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value))
        return target

    def result(self):
        return reconcile.reconcile_estate(self.root, self.inventory)

    def reseal(self, graph):
        graph['graph_digest'] = estate.digest(estate.canonical({k: v for k, v in graph.items() if k != 'graph_digest'}))

    def invalid(self, graph):
        self.reseal(graph)
        with self.assertRaises(coverage.CoverageFailure):
            reconcile._checked_graph(self.inventory, graph)

    def compile(self, reviewed=False, **kwargs):
        composition = fixture_composition(self.inventory)
        ledger = coverage.make_ledger(self.inventory)
        if reviewed:
            for entry in ledger['entries']:
                entry['review_status'] = 'reviewed'
        return coverage.compile_coverage(self.inventory, composition, ledger, source_root=self.root, **kwargs)

    def test_machine_proof_preserves_raw_and_remaining_findings(self):
        result = self.result()
        raw = {(x['code'], x['source_id']) for x in result['raw_source_findings']}
        clear = {(x['code'], x['source_id']) for x in result['resolved_source_findings']}
        pending = {(x['code'], x['source_id']) for x in result['remaining_source_findings']}
        self.assertEqual(raw, clear | pending)
        self.assertFalse(clear & pending)
        self.assertEqual(len(result['resolved_observations']), 4)
        self.assertEqual(len(clear), 2)
        self.assertEqual(result['structural_verdict'], 'blocked')
        self.assertFalse(result['authorized'])
        self.assertEqual(result['release_eligibility'], 'blocked')
        self.assertEqual(result['review_verdict'], 'not-evaluated')

    def test_source_compiler_removes_only_proved_dispatch_issues(self):
        result = self.compile(reviewed=True)
        wrapper = next(x['id'] for x in self.inventory['sources'] if x['path'].endswith('/check/script.sh'))
        child = next(x['id'] for x in self.inventory['sources'] if x['path'].endswith('/check/script.py'))
        pairs = {(x['code'], x['subject_id']) for x in result['findings']}
        self.assertNotIn(('opaque-executable', wrapper), pairs)
        self.assertIn(('opaque-executable', child), pairs)
        self.assertIn('caller-script-body-unresolved', {x['code'] for x in result['findings']})
        self.assertEqual(result['verdict'], 'blocked')
        self.assertFalse(result['authorized'])

    def test_pending_ownership_remains_a_blocker_after_machine_proof(self):
        result = self.compile()
        self.assertIn('adoption-review-required', {x['code'] for x in result['findings']})
        self.assertEqual(len(result['caller_reconciliation']['resolved_observations']), 4)

    def test_marking_every_row_reviewed_does_not_qualify_children(self):
        result = self.compile(reviewed=True)
        self.assertEqual(result['verdict'], 'blocked')
        self.assertIn('opaque-executable', {x['code'] for x in result['findings']})

    def test_false_test_only_label_does_not_exclude_called_code(self):
        composition = fixture_composition(self.inventory)
        ledger = coverage.make_ledger(self.inventory)
        for row in ledger['entries']:
            row.update(review_status='reviewed', disposition='test-only')
        result = coverage.compile_coverage(self.inventory, composition, ledger, source_root=self.root)
        self.assertIn('adoption-exclusion-unproven', {x['code'] for x in result['findings']})

    def test_legacy_compile_without_aggregate_keeps_all_raw_blockers(self):
        result = coverage.compile_coverage(self.inventory, fixture_composition(self.inventory), coverage.make_ledger(self.inventory))
        self.assertNotIn('caller_reconciliation', result)
        self.assertIn('opaque-executable', {x['code'] for x in result['findings']})

    def test_changed_source_invalidates_old_inventory(self):
        self.put('scripts/04.deploy/check/script.py', 'def changed(): return 1\n')
        with self.assertRaisesRegex(coverage.CoverageFailure, 'estate-caller-inventory-stale'):
            self.result()

    def test_self_rehashed_inventory_cannot_waive_actual_source(self):
        inventory = copy.deepcopy(self.inventory)
        inventory['findings'] = []
        for row in inventory['observations']:
            row['issues'] = []
        inventory['inventory_digest'] = estate.digest(estate.canonical({k: v for k, v in inventory.items() if k != 'inventory_digest'}))
        with self.assertRaisesRegex(coverage.CoverageFailure, 'estate-caller-inventory-stale'):
            reconcile.reconcile_estate(self.root, inventory)

    def test_saved_graph_is_not_an_evidence_input(self):
        with self.assertRaises(TypeError):
            reconcile.reconcile_estate(self.root, self.inventory, graph=self.graph)

    def test_omitted_root_rejected_even_if_reachable_through_another_root(self):
        graph = copy.deepcopy(self.graph)
        graph['root_bindings'] = graph['root_bindings'][1:]
        self.invalid(graph)

    def test_duplicate_root_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph['root_bindings'].append(copy.deepcopy(graph['root_bindings'][0]))
        self.invalid(graph)

    def test_missing_or_duplicate_observation_link_rejected(self):
        for change in ('missing', 'duplicate'):
            graph = copy.deepcopy(self.graph)
            if change == 'missing':
                target = graph['structural_proofs'][0]['node_id']
                graph['observation_links'] = [x for x in graph['observation_links'] if x['node_id'] != target]
            else:
                graph['observation_links'].append(copy.deepcopy(graph['observation_links'][0]))
            self.invalid(graph)

    def test_source_join_cannot_substitute_another_file_digest(self):
        graph = copy.deepcopy(self.graph)
        graph['sources'][0]['digest'] = 'sha256:' + 'a' * 64
        self.invalid(graph)

    def test_omitted_proof_outgoing_edge_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph['structural_proofs'][0]['outgoing_edge_ids'] = []
        self.invalid(graph)

    def test_rule_substitution_rejected(self):
        graph = copy.deepcopy(self.graph)
        proof = next(x for x in graph['structural_proofs'] if x['rule'] == 'literal-package-command/v1')
        proof['rule'] = 'python-dispatch/v1'
        self.invalid(graph)

    def test_automatic_hook_cannot_claim_explicit_context(self):
        graph = copy.deepcopy(self.graph)
        row = next(x for x in graph['invocations'] if not x['lifecycle'])
        row['lifecycle'] = True
        self.invalid(graph)

    def test_missing_invocation_context_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph['invocations'].pop()
        self.invalid(graph)

    def test_missing_child_node_rejected(self):
        graph = copy.deepcopy(self.graph)
        outgoing = next(x for x in graph['edges'] if x['caller_id'] == next(p['node_id'] for p in graph['structural_proofs'] if p['rule'] == 'python-dispatch/v1'))
        graph['nodes'] = [x for x in graph['nodes'] if x['id'] != outgoing['callee_id']]
        self.invalid(graph)

    def test_missing_all_root_commands_cannot_be_a_successful_empty_graph(self):
        graph = copy.deepcopy(self.graph)
        for field in ('root_bindings', 'nodes', 'edges', 'sources', 'findings', 'invocations', 'observation_links', 'structural_proofs'):
            graph[field] = []
        self.invalid(graph)

    def test_partial_package_proof_keeps_aggregate_source_finding(self):
        package = copy.deepcopy(self.files['package.json'])
        package['scripts']['opaque'] = 'echo $DYNAMIC'
        self.put('package.json', package)
        inventory = discover(self.root)
        result = reconcile.reconcile_estate(self.root, inventory)
        self.assertIn({'code': 'opaque-executable', 'source_id': estate.digest(b'package.json')}, result['remaining_source_findings'])

    def test_external_unrepresented_implementation_stays_blocking(self):
        package = copy.deepcopy(self.files['package.json'])
        package['scripts']['outside'] = 'bash scripts/01.harness/helper.sh'
        self.put('package.json', package)
        self.put('scripts/01.harness/helper.sh', '#!/usr/bin/env bash\nset -euo pipefail\necho ready\n')
        result = reconcile.reconcile_estate(self.root)
        self.assertIn('estate-caller-subject-unrepresented', {x['code'] for x in result['boundary_findings']})
        self.assertIn('caller-tool-behavior-unresolved', {x['code'] for x in result['boundary_findings']})

    def test_loaded_policy_change_during_collection_is_rejected(self):
        old = reconcile.policy_revision()
        with patch.object(reconcile, 'policy_revision', side_effect=[old, 'sha256:' + 'a' * 64]):
            with self.assertRaisesRegex(coverage.CoverageFailure, 'estate-caller-policy-changed'):
                self.result()

    def test_result_schema_and_shared_validator_are_bound(self):
        old = reconcile.policy_revision()
        original = Path.read_bytes
        for name in ('estate-caller-reconciliation.schema.yml', 'source-inventory.schema.yml', 'release_compiler.py'):
            def changed(path):
                raw = original(path)
                return raw + b'\n' if path.name == name else raw
            with self.subTest(name=name), patch.object(Path, 'read_bytes', changed):
                self.assertNotEqual(old, reconcile.policy_revision())

    def test_schema_cannot_claim_release_authority(self):
        result = self.result()
        result['authorized'] = True
        with self.assertRaises(coverage.CoverageFailure):
            coverage.validate_schema('estate-caller-reconciliation', result)

    def test_empty_package_does_not_invent_operations_or_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'package.json').write_text('{}')
            result = reconcile.reconcile_estate(root)
        self.assertEqual(result['roots'], 0)
        self.assertEqual(result['structural_verdict'], 'accounted')
        self.assertFalse(result['authorized'])
        self.assertEqual(result['qualification_verdict'], 'blocked')


if __name__ == '__main__':
    unittest.main()
