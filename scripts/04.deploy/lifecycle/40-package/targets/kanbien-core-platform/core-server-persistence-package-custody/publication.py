#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.core-server-persistence.immutable-publication
#   version: 2
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reserve one qualified persistence image publication and reconcile an immutable tag without replaying a push.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.consolidate-core-platform-deployment-routes
#     path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str((ROOT / "scripts/04.deploy/shared/provider-adapters/aws/ecr_publication.py").parent))
from ecr_publication import Binding, Publisher

CONFIGURATION = (
    ("scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py", "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml", "core-server-persistence,persistence-migration,persistence-administration,private-persistence-verifier,persistence-restoration-verifier"),
)

PUBLISHER = Publisher(ROOT, Binding(
    source_repository="gordonrose/entity-builder-harness",
    workflow="publish-kanbien-core-platform-core-server-persistence.yml",
    pipeline="core-server-persistence-package-custody",
    target="kanbien-core-platform", scope="core-server-persistence",
    account="337159794548", region="eu-west-1",
    repository="kanbien-core-platform/core-server", role="github-kanbien-core-platform-delivery",
    local_image="kanbien-core-server-persistence:qualification", tag_prefix="persistence",
    artifact_stem="core-server-persistence", error_prefix="PERSISTENCE",
    configuration=CONFIGURATION,
))

if __name__ == "__main__":
    raise SystemExit(PUBLISHER.execute())
