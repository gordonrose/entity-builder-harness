#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection
#   version: 8
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-29"
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

# Historical focused callers use SelectionTests.method, including recursive
# isolation tests. Default execution never discovers this compatibility class.
class SelectionTests(mechanics_test.SelectionTests, repository_contracts_test.RepositoryContractTests):
    pass

if __name__ == '__main__':
    if len(sys.argv) == 1:
        root = Path(__file__).resolve().parents[3]
        raise SystemExit(subprocess.call(['bash', 'scripts/repo/check-selection/smoke-test.sh'], cwd=root))
    if sys.argv[1] == '--suite':
        if len(sys.argv) != 3 or sys.argv[2] not in {'mechanics', 'repository-contracts'}:
            raise SystemExit('Usage: smoke-test.py --suite mechanics|repository-contracts')
        module = mechanics_test if sys.argv[2] == 'mechanics' else repository_contracts_test
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
    unittest.main(verbosity=2)
