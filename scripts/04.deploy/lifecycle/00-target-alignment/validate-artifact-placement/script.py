#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.validate-artifact-placement
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [agentic, architecture]
#   kind: script
#   purpose: Validate the canonical path and clear name selected for a new deployment artifact before it is added or moved.
#   portability: { class: reusable, targets: [entity-builder] }
#   used_by:
#   - id: deploy.standards.deployment-artifact-placement-and-naming
#     path: .agentic/04.deploy/standards/deployment-artifact-placement-and-naming.md
#   effects: [read-only]

"""Validate canonical path shapes for future deployment artifacts.

This command intentionally validates a proposed path, rather than scanning the
whole repository: existing paths remain valid until their governed migration.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import PurePosixPath


KIND_PATTERNS = {
    "target-profile": r"^infra/04\.deploy/03\.product/targets/[a-z0-9-]+/00-target/target-profile\.yml$",
    "foundation-declaration": r"^infra/04\.deploy/03\.product/targets/[a-z0-9-]+/10-foundation/[a-z0-9-]+\.yml$",
    "scope-declaration": r"^infra/04\.deploy/03\.product/targets/[a-z0-9-]+/20-scopes/[a-z0-9-]+/00-declaration/[a-z0-9-]+-contract\.yml$",
    "workload-binding": r"^infra/04\.deploy/03\.product/targets/[a-z0-9-]+/20-scopes/[a-z0-9-]+/10-workload-binding/[a-z0-9-]+-binding\.yml$",
    "alignment-contract": r"^infra/04\.deploy/03\.product/targets/[a-z0-9-]+/20-scopes/[a-z0-9-]+/20-alignment/[a-z0-9-]+-alignment-contract\.yml$",
    "release-evidence": r"^infra/04\.deploy/03\.product/targets/[a-z0-9-]+/20-scopes/[a-z0-9-]+/30-release-evidence/(accepted-release|rehearsals/[a-z0-9-]+-\d{4}-\d{2}-\d{2})\.yml$",
    "provider-template": r"^infra/04\.deploy/03\.product/targets/[a-z0-9-]+/30-provider-realization/[a-z0-9-]+/cloudformation/[a-z0-9-]+\.yml$",
    "package-custody-declaration": r"^infra/04\.deploy/03\.product/targets/[a-z0-9-]+/40-package-custody/[a-z0-9-]+/[a-z0-9.-]+\.yml$",
    "generic-workflow": r"^\.agentic/04\.deploy/(00-target-alignment|10-development|20-build|30-test|40-package|50-deploy|60-run)/workflows/[a-z0-9]+(?:-[a-z0-9]+)*\.md$",
    "generic-standard": r"^\.agentic/04\.deploy/(00-target-alignment|10-development|20-build|30-test|40-package|50-deploy|60-run)/standards/[a-z0-9]+(?:-[a-z0-9]+)*\.md$",
    "generic-schema": r"^\.agentic/04\.deploy/(00-target-alignment|10-development|20-build|30-test|40-package|50-deploy|60-run)/schemas/[a-z0-9]+(?:-[a-z0-9]+)*\.v[0-9]+\.schema\.yml$",
    "aws-target-workflow": r"^\.agentic/aws/(00-target-alignment|10-development|20-build|30-test|40-package|50-deploy|60-run)/workflows/targets/[a-z0-9-]+/20-scopes/[a-z0-9-]+/[a-z0-9]+(?:-[a-z0-9]+)*\.md$",
    "lifecycle-script": r"^scripts/04\.deploy/lifecycle/(00-target-alignment|10-development|20-build|30-test|40-package|50-deploy|60-run)(?:/targets/[a-z0-9-]+/[a-z0-9-]+)?/[a-z0-9]+(?:-[a-z0-9]+)*/script\.(?:sh|py)$",
}


def verdict(path: str, kind: str) -> tuple[bool, str]:
    if path.startswith("/") or ".." in PurePosixPath(path).parts:
        return False, "path-must-be-repository-relative"
    if re.fullmatch(KIND_PATTERNS[kind], path):
        return True, "placement-and-name-valid"
    return False, "path-does-not-match-canonical-placement-for-kind"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=sorted(KIND_PATTERNS), required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    ok, code = verdict(args.path, args.kind)
    report = {
        "schema": "deploy/artifact-placement-report/v1",
        "kind": args.kind,
        "path": args.path,
        "verdict": "passed" if ok else "failed",
        "findings": [] if ok else [{"code": code}],
    }
    print(json.dumps(report, sort_keys=True) if args.json else f"{report['verdict']}: {code}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
