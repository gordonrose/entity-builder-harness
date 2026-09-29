#!/usr/bin/env python3
"""Consume saved source analysis only after a fresh, local producer comparison."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-result-consumption-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Recompute bounded source analysis before accepting a saved result for that purpose.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import sys

import release_compiler as release
import result_consumption as consumption


def reject_safely(code, purpose):
    try:
        return consumption.reject_result(code, purpose)
    except Exception:
        # No loaded contract means no claim of contract validation.
        return {"schema": "source-result-consumption/v1", "scope": "source-result-consumption",
                "purpose": "source-analysis", "verdict": "rejected", "authorized": False,
                "release_eligibility": "blocked", "operation_authorization": "blocked",
                "findings": [{"code": "consumption-contract-unavailable"}]}


def recompute(arguments):
    """Dispatch only known read-only source producers; never inspected commands."""
    options = {value.split("=", 1)[0] for value in arguments if value.startswith("--")}
    source_modes = options & {"--coverage", "--triage", "--callers", "--operations"}
    if options & {"--consume-result", "--purpose", "--discover", "--ledger-template",
                  "--review-template", "--operation-template", "--expected-result"}:
        raise release.ReleaseFailure("arguments-invalid")
    if source_modes:
        if len(source_modes) != 1:
            raise release.ReleaseFailure("arguments-invalid")
        if "--triage" in options and "--finding-triage" not in options:
            raise release.ReleaseFailure("arguments-invalid")
        if "--callers" in options and "--caller-review" not in options:
            raise release.ReleaseFailure("arguments-invalid")
        if "--operations" in options:
            if "--operation-contracts" not in options or "--caller-review" not in options:
                raise release.ReleaseFailure("arguments-invalid")
            import operation_contracts_cli
            producer = operation_contracts_cli.main
        else:
            import source_coverage
            producer = source_coverage.main
    elif "--release" in options:
        producer = release.main
    else:
        raise release.ReleaseFailure("arguments-invalid")
    output = StringIO()
    # Producers own their strict grammar. Never print their payload on rejection.
    with redirect_stdout(output), redirect_stderr(StringIO()):
        status = producer(arguments)
    if status != 0:
        raise release.ReleaseFailure("producer-recompute-failed")
    return json.loads(output.getvalue())


def main(argv=None):
    purpose = "source-analysis"
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        if argv.count("--") != 1:
            raise release.ReleaseFailure("arguments-invalid")
        separator = argv.index("--")
        consumer_args, producer_args = argv[:separator], argv[separator + 1:]
        options = [value.split("=", 1)[0] for value in consumer_args if value.startswith("--")]
        if len(options) != len(set(options)) or not producer_args:
            raise release.ReleaseFailure("arguments-invalid")
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument("--consume-result", required=True)
        parser.add_argument("--purpose", choices=("source-analysis", "release-eligibility",
                                                 "operation-authorization"), required=True)
        args = parser.parse_args(consumer_args)
        purpose = args.purpose
        if purpose != "source-analysis":
            # No recomputation or source read can turn analysis into authority.
            decision = consumption.consume_result(None, purpose)
        else:
            result = release.load_document(args.consume_result, "source-result-unreadable")
            decision = consumption.consume_result(result, purpose, expected_result=recompute(producer_args))
    except release.ReleaseFailure as error:
        decision = reject_safely(error.code, purpose)
    except Exception:
        decision = reject_safely("producer-recompute-failed", purpose)
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
