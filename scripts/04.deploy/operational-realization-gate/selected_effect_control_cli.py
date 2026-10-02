#!/usr/bin/env python3
"""Public source-only route compiler for the selected effect boundary."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-effect-control-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compile the one supported selected source route and state its missing live receipts.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
import argparse
import json
from pathlib import Path
import sys

import release_compiler as release
import selected_effect_control as control

SAFE_CODES = {
    "arguments-invalid",
    "selected-effect-route-invalid",
    "selected-effect-admission-invalid",
    "selected-effect-admission-binding-invalid",
    "selected-control-plane-unavailable",
}


class CliFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CliFailure("arguments-invalid")


def arguments(argv):
    flags = [item.split("=", 1)[0] for item in argv if item.startswith("--")]
    if len(flags) != len(set(flags)):
        raise CliFailure("arguments-invalid")
    parser = Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--selected-effect-route", action="store_true", required=True)
    parser.add_argument("--route", required=True, choices=sorted(control.ROUTES))
    parser.add_argument("--mode", required=True)
    parser.add_argument("--admission-result")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def failure(code):
    return {
        "schema": "selected-effect-route-error/v1",
        "scope": "selected-staging-effect-route",
        "authorized": False,
        "release_eligibility": "blocked",
        "operation_authorization": "blocked",
        "findings": [{"code": code if code in SAFE_CODES else "selected-effect-route-invalid"}],
    }


def main(argv=None):
    try:
        parsed = arguments(list(sys.argv[1:] if argv is None else argv))
        admission_result = (release.load_document(Path(parsed.admission_result), "selected-effect-admission-invalid")
                            if parsed.admission_result else None)
        print(json.dumps(control.source_route(parsed.route, parsed.mode, admission_result), sort_keys=True))
        return 0
    except Exception as error:
        print(json.dumps(failure(getattr(error, "code", "selected-effect-route-invalid")), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

