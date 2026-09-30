#!/usr/bin/env python3
"""Fresh estate analysis and pending adoption proposals through the existing gate."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-estate-caller-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Expose bounded estate reconciliation and pending adoption migration without execution authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ERROR_CODES = frozenset({"arguments-invalid", "dependency-unavailable", "source-analysis-failed",
                         "adoption-ledger-unreadable", "adoption-migration-failed"})


class ArgumentFailure(Exception):
    """No argparse usage, source argument, or exception text may escape."""


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentFailure() from None


def reject(code):
    # Fixed fallback also works with unavailable or corrupt helper/schema files.
    # It asserts no schema digest, validated receipt, or executable authority.
    return {"schema": "estate-caller-error/v1", "scope": "estate-source-analysis",
            "verdict": "blocked", "authorized": False, "release_eligibility": "blocked",
            "operation_authorization": "blocked", "qualification_verdict": "blocked",
            "findings": [{"code": code if code in ERROR_CODES else "dependency-unavailable"}]}


def main(argv=None):
    code = "source-analysis-failed"
    try:
        arguments = list(sys.argv[1:] if argv is None else argv)
        options = [arg.split("=", 1)[0] for arg in arguments if arg.startswith("--")]
        if len(options) != len(set(options)):
            raise ArgumentFailure()
        parser = SafeParser(add_help=False, allow_abbrev=False)
        modes = parser.add_mutually_exclusive_group(required=True)
        modes.add_argument("--estate-callers", action="store_true")
        modes.add_argument("--adoption-migration", action="store_true")
        parser.add_argument("--source-root", required=True)
        parser.add_argument("--previous-adoption-ledger")
        parser.add_argument("--json", action="store_true")
        args = parser.parse_args(arguments)
        if bool(args.previous_adoption_ledger) != args.adoption_migration:
            raise ArgumentFailure()
        # Imports remain inside the rejection boundary; no missing helper can
        # print a traceback or accidentally fall through to a different mode.
        code = "dependency-unavailable"
        import source_coverage as coverage
        import release_compiler as release
        error_schema_digest = coverage.validate_schema("estate-caller-error", reject(code))
        if args.estate_callers:
            from estate_caller_coverage import reconcile_estate
            code = "source-analysis-failed"
            if not Path(args.source_root).is_dir():
                raise RuntimeError()
            result = reconcile_estate(Path(args.source_root))
            status = 0 if result["structural_verdict"] == "accounted" else 1
        else:
            from adoption_migration import migrate_adoption
            code = "adoption-ledger-unreadable"
            previous = release.load_document(args.previous_adoption_ledger, code)
            code = "adoption-migration-failed"
            if not Path(args.source_root).is_dir():
                raise RuntimeError()
            inventory = coverage.discover(Path(args.source_root))
            result = migrate_adoption(inventory, previous)
            # The CLI accepts files, not an already trusted snapshot. Check both
            # inputs again before returning a proposal bound to this collection.
            if (release.digest_document(previous) != release.digest_document(
                    release.load_document(args.previous_adoption_ledger, code))
                    or coverage.discover(Path(args.source_root))["inventory_digest"] != inventory["inventory_digest"]):
                raise RuntimeError()
            status = 1  # An all-pending proposal never signals completed review.
        # Enforce the selected output contract again at the public boundary.
        # Helper output is never printed merely because the call returned.
        release.bounded_json(result)
        coverage.validate_schema("estate-caller-reconciliation" if args.estate_callers
                                 else "source-adoption-migration", result)
        if (result["authorized"] is not False
                or result["release_eligibility"] != "blocked"
                or result["operation_authorization"] != "blocked"
                or release.digest_document({key: value for key, value in result.items()
                                            if key != "result_digest"}) != result["result_digest"]):
            raise RuntimeError()
        code = "dependency-unavailable"
        if coverage.validate_schema("estate-caller-error", reject(code)) != error_schema_digest:
            raise RuntimeError()
    except ArgumentFailure:
        result, status = reject("arguments-invalid"), 1
    except (ImportError, SyntaxError):
        result, status = reject("dependency-unavailable"), 1
    except Exception:
        result, status = reject(code), 1
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
