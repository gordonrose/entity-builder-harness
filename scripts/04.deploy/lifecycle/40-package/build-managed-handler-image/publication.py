#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.scheduling.immutable-publication
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [security, sre]
#   kind: script
#   purpose: Select one declared scheduling image for the existing protected-main immutable publication owner.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-scheduling
#     path: .github/workflows/publish-kanbien-core-platform-scheduling.yml
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts/04.deploy/shared/provider-adapters/aws"))
from ecr_publication import Binding, Publisher

def binding(program):
    if not isinstance(program, str) or not re.fullmatch(r"kanbien-(?:core-server-persistence|entity-smoke)-scheduling-(?:dispatch|worker)", program):
        raise ValueError("scheduling-publication-program-invalid")
    entity = program.startswith("kanbien-entity-smoke-")
    scope = "entity-smoke" if entity else "core-server-persistence"
    purpose = program.rsplit("-", 1)[1]
    return Binding(
        source_repository="gordonrose/entity-builder-harness", workflow="publish-kanbien-core-platform-scheduling.yml",
        target="kanbien-core-platform", scope=scope, account="337159794548", region="eu-west-1",
        repository="kanbien-core-platform/" + ("entity-smoke" if entity else "core-server"),
        role="github-kanbien-core-platform-entity-smoke-publisher" if entity else "github-kanbien-core-platform-delivery",
        local_image=program + ":qualification", tag_prefix=program, artifact_stem=program, error_prefix="SCHEDULING",
        configuration=(("scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py",
            "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/scheduling.yml", scope + "." + purpose),),
    ).checked()

if __name__ == "__main__":
    try: selected = binding(os.environ.get("SCHEDULING_PROGRAM"))
    except ValueError:
        print('{"verdict":"failed","code":"scheduling-publication-program-invalid"}')
        raise SystemExit(2)
    raise SystemExit(Publisher(ROOT, selected).execute())
