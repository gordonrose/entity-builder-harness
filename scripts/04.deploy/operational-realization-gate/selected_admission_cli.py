#!/usr/bin/env python3
"""Strict public entry point for source-only selected release admission compilation."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-admission-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compile immutable selected baseline/candidate admission requests without release or operation authority.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py
import argparse
import json
from pathlib import Path
import sys

import release_compiler as release
import selected_admission as admission

sys.dont_write_bytecode = True
SAFE_CODES = frozenset((
    "arguments-invalid", "admission-authority-unavailable", "admission-baseline-invalid",
    "admission-candidate-invalid", "admission-immutable-release-rebound",
    "admission-operation-binding-invalid", "admission-result-invalid", "admission-schema-invalid",
    "admission-schema-unreadable", "admission-dependency-unavailable",
))


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
    parser.add_argument("--selected-admission", action="store_true", required=True)
    for name in ("baseline-result", "blueprint", "source-root", "source-revision", "image-digest", "release-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def load_compiler():
    directory = Path(__file__).resolve().parents[1] / "release-control"
    sys.path.insert(0, str(directory))
    try:
        import selected_blueprint
        return selected_blueprint
    except Exception:
        raise CliFailure("admission-dependency-unavailable") from None
    finally:
        sys.path.remove(str(directory))


def failure(code):
    return {
        "schema": "selected-admission-error/v1", "scope": "selected-staging-admission", "verdict": "failed",
        "authorized": False, "release_eligibility": "blocked", "operation_authorization": "blocked",
        "qualification_verdict": "blocked",
        "findings": [{"code": code if isinstance(code, str) and code in SAFE_CODES else "admission-result-invalid"}],
    }


def main(argv=None):
    try:
        args = arguments(list(sys.argv[1:] if argv is None else argv))
        compiler = load_compiler()
        baseline = release.load_document(args.baseline_result, "admission-baseline-invalid")
        blueprint = compiler.release.load_document(args.blueprint, "admission-candidate-invalid")
        candidate = compiler.compile_blueprint(Path(args.source_root), blueprint, args.source_revision,
                                               args.image_digest, args.release_id)
        result = admission.compile_admission(baseline, candidate)
        admission.validate_result(result)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as error:
        code = getattr(error, "code", "admission-result-invalid")
        print(json.dumps(failure(code), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
