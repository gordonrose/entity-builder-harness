#!/usr/bin/env python3
"""Verify current adoption work never inherits approvals or deletion authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-adoption-migration
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Preserve every source delta and ownership proposal while rejecting approval promotion and stale bindings.
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
import adoption_migration as migration
import source_coverage as coverage
from source_inventory import discover


class AdoptionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='adoption-migration-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'package.json').write_text('{}')
        self.path = self.root / 'scripts/04.deploy/fixture.py'
        self.path.parent.mkdir(parents=True)
        self.path.write_text('def fixture(): return 0\n')
        self.inventory = discover(self.root)
        self.prior = coverage.make_ledger(self.inventory)

    def result(self, inventory=None, prior=None):
        return migration.migrate_adoption(inventory or self.inventory, prior or self.prior)

    def test_unchanged_rows_are_all_pending_and_inputs_unchanged(self):
        before = copy.deepcopy((self.inventory, self.prior))
        result = self.result()
        self.assertEqual(result['counts'], {'added': 0, 'changed': 0, 'unchanged': 2, 'removed': 0})
        self.assertTrue(all(x['review_status'] == 'pending' for x in result['candidate']['entries']))
        self.assertEqual(before, (self.inventory, self.prior))

    def test_added_source_is_pending_with_intake_owner(self):
        (self.path.parent / 'new.py').write_text('def added(): return 0\n')
        result = self.result(inventory=discover(self.root))
        self.assertEqual(result['counts']['added'], 1)
        added = next(x['source_id'] for x in result['changes'] if x['change'] == 'added')
        row = next(x for x in result['candidate']['entries'] if x['source_id'] == added)
        self.assertEqual(row['owner'], 'release-control-programme')
        self.assertEqual(row['review_status'], 'pending')

    def test_changed_source_preserves_proposed_owner_without_review(self):
        for row in self.prior['entries']:
            row.update(owner='application-team', review_status='reviewed')
        self.path.write_text('def fixture(): return 1\n')
        result = self.result(inventory=discover(self.root))
        self.assertEqual(result['counts']['changed'], 1)
        self.assertTrue(all(x['owner'] == 'application-team' and x['review_status'] == 'pending' for x in result['candidate']['entries']))

    def test_removed_source_is_retained_in_delta_without_retirement(self):
        self.path.unlink()
        result = self.result(inventory=discover(self.root))
        row = next(x for x in result['changes'] if x['change'] == 'removed')
        self.assertIsNone(row['current_digest'])
        self.assertIsNotNone(row['previous_digest'])
        self.assertFalse(result['retirement_authorized'])
        self.assertFalse(result['deletion_authorized'])
        self.assertEqual(len(self.prior['entries']), 2)

    def test_previous_review_never_carries_even_for_unchanged_source(self):
        for row in self.prior['entries']:
            row['review_status'] = 'reviewed'
        result = self.result()
        self.assertEqual(result['review_verdict'], 'pending')
        self.assertTrue(all(x['review_status'] == 'pending' for x in result['candidate']['entries']))

    def test_retirement_and_test_only_proposals_remain_pending(self):
        for disposition in ('retire', 'historical', 'test-only'):
            with self.subTest(disposition=disposition):
                prior = copy.deepcopy(self.prior)
                for row in prior['entries']:
                    row.update(disposition=disposition, review_status='reviewed')
                result = self.result(prior=prior)
                self.assertTrue(all(x['disposition'] == disposition and x['review_status'] == 'pending' for x in result['candidate']['entries']))
                self.assertFalse(result['retirement_authorized'])

    def test_duplicate_previous_source_is_rejected(self):
        self.prior['entries'].append(copy.deepcopy(self.prior['entries'][0]))
        with self.assertRaises(coverage.CoverageFailure):
            self.result()

    def test_malformed_previous_owner_cannot_leak_in_error(self):
        self.prior['entries'][0]['owner'] = 'SENTINEL-DO-NOT-PRINT\nsecret'
        with self.assertRaises(coverage.CoverageFailure) as context:
            self.result()
        self.assertNotIn('SENTINEL', str(context.exception))

    def test_inventory_tampering_is_rejected(self):
        self.inventory['sources'][0]['digest'] = 'sha256:' + 'a' * 64
        with self.assertRaisesRegex(coverage.CoverageFailure, 'inventory-digest-invalid'):
            self.result()

    def test_embedded_candidate_schema_forbids_reviewed_row(self):
        result = self.result()
        result['candidate']['entries'][0]['review_status'] = 'reviewed'
        with self.assertRaises(coverage.CoverageFailure):
            coverage.validate_schema('source-adoption-migration', result)

    def test_result_schema_forbids_authority(self):
        for field in ('authorized', 'retirement_authorized', 'deletion_authorized'):
            result = self.result()
            result[field] = True
            with self.subTest(field=field), self.assertRaises(coverage.CoverageFailure):
                coverage.validate_schema('source-adoption-migration', result)

    def test_migration_has_exact_candidate_and_prior_bindings(self):
        result = self.result()
        self.assertEqual(result['candidate_digest'], migration.release.digest_document(result['candidate']))
        self.assertEqual(result['prior_ledger_digest'], migration.release.digest_document(self.prior))
        self.assertEqual(result['result_digest'], migration.release.digest_document({k: v for k, v in result.items() if k != 'result_digest'}))

    def test_helper_and_output_schema_bytes_are_bound(self):
        before = migration.policy_revision()
        original = Path.read_text
        for name in ('source-adoption-migration.schema.yml', 'release_compiler.py'):
            def changed(path, *args, **kwargs):
                text = original(path, *args, **kwargs)
                return text + '\n' if path.name == name else text
            with self.subTest(name=name), patch.object(Path, 'read_text', changed):
                self.assertNotEqual(before, migration.policy_revision())

    def test_policy_change_during_migration_is_rejected(self):
        old = migration.policy_revision()
        with patch.object(migration, 'policy_revision', side_effect=[old, 'sha256:' + 'a' * 64]):
            with self.assertRaisesRegex(coverage.CoverageFailure, 'adoption-policy-changed'):
                self.result()

    def test_no_files_are_written_or_sources_executed(self):
        before = sorted((str(p.relative_to(self.root)), p.read_bytes()) for p in self.root.rglob('*') if p.is_file())
        self.result()
        after = sorted((str(p.relative_to(self.root)), p.read_bytes()) for p in self.root.rglob('*') if p.is_file())
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
