#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.postgresql-version
#   version: 1
#   status: draft
#   created_on: "2026-11-16"
#   updated_on: "2026-11-16"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, sre]
#   kind: script
#   purpose: Separate declared PostgreSQL major compatibility from exact disposable qualification versions.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.consolidate-core-platform-deployment-routes
#     path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
"""Compatibility is not qualification evidence; callers must still run SQL proofs."""
import argparse
import importlib.util
import json
from pathlib import Path
import re


class VersionFailure(ValueError):
    def __init__(self, reason):
        self.code = "postgresql-version-" + reason
        super().__init__(self.code)


def major(value):
    if type(value) is not int or not 10 <= value <= 99:
        raise VersionFailure("major-invalid")
    return value


def version(value):
    # RDS may append its dated patch suffix. Do not accept arbitrary prefixes,
    # prereleases or pre-10 PostgreSQL's different version-number scheme.
    match = re.fullmatch(r"([1-9][0-9])\.(0|[1-9][0-9]{0,3})(?:-rds\.[0-9]{8})?", value) if isinstance(value, str) else None
    if match is None:
        raise VersionFailure("observation-invalid")
    return int(match[1]), int(match[2])


def compatible(observed, expected_major):
    expected_major = major(expected_major)
    if version(observed)[0] != expected_major:
        raise VersionFailure("major-incompatible")
    return observed


def configuration(document):
    declaration = document.get("postgresql") if isinstance(document, dict) else None
    if not isinstance(declaration, dict) or set(declaration) != {"compatible_major", "qualification_image"}:
        raise VersionFailure("declaration-invalid")
    supported = major(declaration["compatible_major"])
    image = declaration["qualification_image"]
    match = re.fullmatch(r"postgres:([1-9][0-9]\.(?:0|[1-9][0-9]{0,3}))-bookworm", image) if isinstance(image, str) else None
    if match is None:
        raise VersionFailure("qualification-image-invalid")
    exact = compatible(match[1], supported)
    _, minor = version(exact)
    return {**declaration, "qualification_version": exact,
            "server_version_num": str(supported * 10000 + minor),
            "data_directory": f"/var/lib/postgresql/{supported}/docker" if supported >= 18 else "/var/lib/postgresql/data"}


def read(path):
    # Reuse the existing duplicate-safe YAML reader; no second YAML dialect.
    parser_path = Path(__file__).with_name("provider-adapters") / "aws/cloudformation-template.py"
    spec = importlib.util.spec_from_file_location("postgresql_contract_document", parser_path)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    try:
        return configuration(parser.template(Path(path).read_text(encoding="utf-8")))
    except VersionFailure:
        raise
    except (OSError, UnicodeError, ValueError):
        raise VersionFailure("source-invalid") from None


def main():
    parser = argparse.ArgumentParser()
    parser.error = lambda _message: parser.exit(2, '{"verdict":"failed","code":"postgresql-version-arguments-invalid"}\n')
    parser.add_argument("--contract", required=True)
    parser.add_argument("--shell-values", action="store_true")
    args = parser.parse_args()
    result = read(args.contract)
    if args.shell_values:
        print("\t".join(result[key] for key in ("qualification_image", "server_version_num", "data_directory")))
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (VersionFailure, OSError, ImportError) as failure:
        print(json.dumps({"verdict": "failed", "code": failure.code if isinstance(failure, VersionFailure) else "postgresql-version-source-invalid"}))
        raise SystemExit(1)

