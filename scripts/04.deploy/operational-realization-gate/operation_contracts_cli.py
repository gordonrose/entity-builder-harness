#!/usr/bin/env python3
"""Expose operation source accounting through the existing realization gate."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-operation-contracts-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Recollect selected operation dependencies and reconcile source contracts without execution authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

import json
from pathlib import Path
import sys

import release_compiler as release
import source_coverage
import operation_contracts
from caller_inventory import discover_callers
from operation_inventory import discover_operations
from source_inventory import SourceFailure


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        options = [value.split("=", 1)[0] for value in argv if value.startswith("--")]
        if len(options) != len(set(options)):
            raise release.ReleaseFailure("arguments-invalid")
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument("--operations", action="store_true", required=True)
        parser.add_argument("--source-root", required=True)
        parser.add_argument("--workflow", required=True)
        parser.add_argument("--caller-review")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--operation-contracts")
        mode.add_argument("--operation-template", action="store_true")
        parser.add_argument("--json", action="store_true")
        args = parser.parse_args(argv)
        if bool(args.caller_review) != bool(args.operation_contracts or args.operation_template):
            raise release.ReleaseFailure("arguments-invalid")
        root = Path(args.source_root)
        graph = discover_callers(root, args.workflow)
        inventory = discover_operations(root, args.workflow, graph=graph)
        if args.operation_contracts or args.operation_template:
            review = release.load_document(args.caller_review, "operation-caller-review-unreadable")
            if args.operation_template:
                result = operation_contracts.make_contracts(inventory, graph, review)
                status = 1  # Generated declarations are pending, never approvals.
            else:
                contracts = release.load_document(args.operation_contracts, "operation-contracts-unreadable")
                result = operation_contracts.compile_operations(inventory, graph, review, contracts)
                status = 0 if result["contracts_verdict"] == "complete" else 1
        else:
            operation_contracts.validate_schema("source-operation-inventory", inventory)
            result = inventory
            status = 1 if inventory["findings"] else 0
    except release.ReleaseFailure as error:
        result = failure(error.code)
        status = 1
    except SourceFailure:
        result = failure("operation-source-discovery-failed")
        status = 1
    except Exception:
        result = failure("operation-contracts-failed")
        status = 1
    print(json.dumps(result, sort_keys=True))
    return status


def failure(code):
    return {"schema": "source-operation-result/v1", "scope": "operation-contracts",
            "authorized": False, "contracts_verdict": "incomplete",
            "source_closure": "blocked", "qualification_verdict": "blocked",
            "findings": [{"code": code}]}


if __name__ == "__main__":
    raise SystemExit(main())
