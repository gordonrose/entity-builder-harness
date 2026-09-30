#!/usr/bin/env python3
"""Strict source-only public entrypoint for the selected release blueprint."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-blueprint-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compile a selected source blueprint through the existing gate with fixed safe diagnostics.
#   portability: {class: internal, targets: [kanbien/staging]}
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

RESULT_SCHEMA = "selected-release-blueprint-result/v1"
ERROR_SCHEMA = "selected-release-blueprint-error/v1"
SAFE_CODES = frozenset({
    "arguments-invalid", "blueprint-unreadable", "blueprint-dependency-unavailable",
    "blueprint-compilation-failed", "blueprint-result-invalid",
    "document-alias-unsupported", "document-key-invalid", "document-limit-exceeded",
    "document-string-invalid", "document-number-invalid", "document-type-invalid",
    "blueprint-command-binding-mismatch", "blueprint-command-source-missing",
    "blueprint-contract-fields-invalid", "blueprint-contract-value-invalid",
    "blueprint-document-invalid", "blueprint-foundation-invalid",
    "blueprint-identity-binding-mismatch", "blueprint-image-default-invalid",
    "blueprint-implementation-changed", "blueprint-invalid",
    "blueprint-operation-coverage-invalid", "blueprint-owner-mismatch",
    "blueprint-profile-binding-mismatch", "blueprint-release-binding-invalid",
    "blueprint-schema-unreadable", "blueprint-schema-invalid",
    "blueprint-schema-reference-invalid", "blueprint-schema-version-invalid",
    "blueprint-source-binding-duplicate", "blueprint-source-binding-stale",
    "blueprint-source-changed", "blueprint-source-coverage-incomplete",
    "blueprint-source-cycle", "blueprint-source-document-invalid",
    "blueprint-source-key-invalid", "blueprint-source-limit",
    "blueprint-source-path-invalid", "blueprint-source-type-invalid",
    "blueprint-target-policy-mismatch",
})
RESULT_FIELDS = frozenset({
    "schema", "scope", "verdict", "authorized", "release_eligibility",
    "operation_authorization", "qualification_verdict", "policy_review", "identity_proof",
    "source_revision_status", "artifact_identity_status", "blueprint_digest",
    "blueprint_schema_digest", "implementation_digest", "source_bindings",
    "operation_projection", "definition", "realization_contract", "compiled_release",
    "constraints", "findings", "result_digest",
})


class CliFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise CliFailure("arguments-invalid")


def arguments(argv):
    options = [entry.split("=", 1)[0] for entry in argv if entry.startswith("--")]
    if len(options) != len(set(options)):
        raise CliFailure("arguments-invalid")
    parser = SafeParser(add_help=False, allow_abbrev=False)
    for name in ("blueprint", "source-root", "source-revision", "image-digest", "release-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def load_compiler():
    # Only the maintained sibling module location supplies target parsing.
    directory = Path(__file__).resolve().parents[1] / "release-control"
    sys.path.insert(0, str(directory))
    try:
        import selected_blueprint
        return selected_blueprint
    except Exception:
        raise CliFailure("blueprint-dependency-unavailable") from None
    finally:
        sys.path.remove(str(directory))


def validate_result(result, compiler):
    if type(result) is not dict or set(result) != RESULT_FIELDS:
        raise CliFailure("blueprint-result-invalid")
    expected = {"schema": RESULT_SCHEMA, "scope": "selected-release-blueprint",
                "verdict": "compiled", "authorized": False,
                "release_eligibility": "blocked", "operation_authorization": "blocked",
                "qualification_verdict": "blocked", "policy_review": "required",
                "identity_proof": "pending", "source_revision_status": "declared",
                "artifact_identity_status": "declared", "findings": []}
    if any(type(result[key]) is not type(value) or result[key] != value for key, value in expected.items()):
        raise CliFailure("blueprint-result-invalid")
    compiler.release.bounded_json(result)
    source_fields = {"path", "digest"}
    projection_fields = {"operation_id", "source_profile", "source_digest", "command_digest",
                         "identity_digest", "configuration_digest", "execution_group_digest", "command_qualification", "image_scope"}
    if (type(result["source_bindings"]) is not list
            or any(type(row) is not dict or set(row) != source_fields
                   or not compiler.safe_path(row["path"])
                   or type(row["digest"]) is not str or not compiler.SHA.fullmatch(row["digest"])
                   for row in result["source_bindings"])
            or type(result["operation_projection"]) is not list
            or any(type(row) is not dict or set(row) != projection_fields
                   or any(type(row[field]) is not str or not compiler.SHA.fullmatch(row[field])
                          for field in ("source_digest", "command_digest", "identity_digest",
                                        "configuration_digest", "execution_group_digest"))
                   or row["command_qualification"] != "pending"
                   or row["image_scope"] not in {"product", "external"}
                   for row in result["operation_projection"])):
        raise CliFailure("blueprint-result-invalid")
    compiler.validate_neutral_output(result["realization_contract"])
    if (compiler.release.digest_document({key: value for key, value in result.items() if key != "result_digest"}) != result["result_digest"]
            or compiler.release.compile_release(result["definition"], result["realization_contract"]) != result["compiled_release"]):
        raise CliFailure("blueprint-result-invalid")
    return result


def failure(code):
    return {"schema": ERROR_SCHEMA, "scope": "selected-release-blueprint", "verdict": "failed",
            "authorized": False, "release_eligibility": "blocked",
            "operation_authorization": "blocked", "qualification_verdict": "blocked",
            "findings": [{"code": code if type(code) is str and code in SAFE_CODES else "blueprint-compilation-failed"}]}


def main(argv=None):
    try:
        args = arguments(list(sys.argv[1:] if argv is None else argv))
        compiler = load_compiler()
        document = compiler.release.load_document(args.blueprint, "blueprint-unreadable")
        result = compiler.compile_blueprint(Path(args.source_root), document,
                                            args.source_revision, args.image_digest, args.release_id)
        result = validate_result(result, compiler)
        rendered = json.dumps(result, sort_keys=True)
    except Exception as error:
        # Neither argparse text, paths, source content nor unexpected internals escape.
        result = failure(getattr(error, "code", "blueprint-compilation-failed"))
        rendered = json.dumps(result, sort_keys=True)
    print(rendered)
    return 0 if result["verdict"] == "compiled" else 1


if __name__ == "__main__":
    raise SystemExit(main())
