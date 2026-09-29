#!/usr/bin/env python3
"""Discover build inputs or compare a local artifact through the realization gate."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-build-contracts-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Recompute workspace build inputs and bind local artifact membership without execution or release authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

import json
from pathlib import Path
import re
import sys

import release_compiler as release
import build_contracts
from source_inventory import SourceFailure

DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


def failure(code):
    return {"schema": "source-build-result/v1", "scope": "build-accounting",
            "authorized": False, "verdict": "incomplete", "source_closure": "blocked",
            "qualification_verdict": "blocked", "findings": [{"code": code}]}


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        options = [value.split("=", 1)[0] for value in argv if value.startswith("--")]
        if len(options) != len(set(options)):
            raise release.ReleaseFailure("arguments-invalid")
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument("--builds", action="store_true", required=True)
        parser.add_argument("--source-root", required=True)
        parser.add_argument("--workflow", required=True)
        parser.add_argument("--build-id")
        parser.add_argument("--artifact-root")
        parser.add_argument("--expect-inventory-digest")
        parser.add_argument("--expect-artifact-digest")
        parser.add_argument("--json", action="store_true")
        args = parser.parse_args(argv)
        if bool(args.build_id) != bool(args.artifact_root):
            raise release.ReleaseFailure("arguments-invalid")
        if args.expect_artifact_digest and not args.artifact_root:
            raise release.ReleaseFailure("arguments-invalid")
        for value in (args.build_id, args.expect_inventory_digest, args.expect_artifact_digest):
            if value is not None and not DIGEST.fullmatch(value):
                raise release.ReleaseFailure("arguments-invalid")
        from build_inventory import discover_builds
        root = Path(args.source_root)
        inventory = build_contracts.checked_inventory(discover_builds(root, args.workflow))
        if args.expect_inventory_digest and args.expect_inventory_digest != inventory["inventory_digest"]:
            raise release.ReleaseFailure("build-inventory-stale")
        if args.artifact_root:
            from build_artifacts import bind_artifact
            result = bind_artifact(root, inventory, args.build_id, Path(args.artifact_root))
            build_contracts.validate_schema("source-build-artifact", result)
            if args.expect_artifact_digest and args.expect_artifact_digest != result["artifact_digest"]:
                raise release.ReleaseFailure("build-artifact-stale")
            status = 0 if result["artifact_verdict"] == "complete" else 1
        else:
            result = inventory
            status = 1 if inventory["findings"] or not inventory["builds"] else 0
    except release.ReleaseFailure as error:
        result, status = failure(error.code), 1
    except SourceFailure:
        result, status = failure("build-discovery-failed"), 1
    except Exception:
        result, status = failure("build-accounting-failed"), 1
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())

