#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection
#   version: 11
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-11-25"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: test
#   purpose: Retain complete registered-suite and historical focused Python invocations.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh
from __future__ import annotations
import subprocess
import sys
import unittest
from pathlib import Path
# A spec-based foreign importer does not put this directory on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mechanics_test
import repository_contracts_test
selection = mechanics_test.selection  # Retained known foreign-fixture import surface.

PROMOTION_MECHANICS_TESTS = (
    'test_ci_catalog_only_change_selects_consumers_against_pr_base',
    'test_ci_modes_share_complete_consumer_analysis',
    'test_ci_modes_select_changed_check_contracts',
    'test_ci_modes_apply_consumed_review_ledger_transitions',
    'test_recorded_ci_branch_diff_defers_hygiene_even_when_its_input_changed',
    'test_deferred_check_runs_only_when_explicitly_named',
    'test_cli_selector_change_reuses_unchanged_subject_proof',
)

# Historical focused callers use SelectionTests.method, including recursive
# isolation tests. Default execution never discovers this compatibility class.
class SelectionTests(mechanics_test.SelectionTests, repository_contracts_test.RepositoryContractTests):
    pass

if __name__ == '__main__':
    if len(sys.argv) == 1:
        root = Path(__file__).resolve().parents[3]
        raise SystemExit(subprocess.call(['bash', 'scripts/repo/check-selection/smoke-test.sh'], cwd=root))
    if sys.argv[1] == '--suite':
        if sys.argv[1:] == ['--suite', 'mechanics', '--focus', 'promotion']:
            suite = unittest.TestSuite(
                mechanics_test.SelectionTests(name) for name in PROMOTION_MECHANICS_TESTS)
            raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
        if len(sys.argv) != 3 or sys.argv[2] not in {'mechanics', 'repository-contracts'}:
            raise SystemExit('Usage: smoke-test.py --suite mechanics|repository-contracts [--focus promotion]')
        module = mechanics_test if sys.argv[2] == 'mechanics' else repository_contracts_test
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
    unittest.main(verbosity=2)
