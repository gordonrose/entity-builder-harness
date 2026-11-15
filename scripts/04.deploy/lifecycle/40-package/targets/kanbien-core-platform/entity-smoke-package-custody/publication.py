#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.immutable-publication
#   version: 3
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reserve one qualified feature image publication and reconcile an immutable tag without replaying a push.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str((ROOT / "scripts/04.deploy/shared/provider-adapters/aws/ecr_publication.py").parent))
from ecr_publication import Binding, Publisher

CONFIGURATION = (
    ("scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py", "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke.yml", "entity-smoke-server,entity-smoke-migration,entity-smoke-administration,entity-smoke-verifier,entity-smoke-database-proof"),
    ("scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py", "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke-isolated-restore.yml", "entity-smoke-restore-reader"),
)

PUBLISHER = Publisher(ROOT, Binding(
    source_repository="gordonrose/entity-builder-harness",
    workflow="publish-kanbien-core-platform-entity-smoke.yml",
    target="kanbien-core-platform", scope="entity-smoke",
    account="337159794548", region="eu-west-1",
    repository="kanbien-core-platform/entity-smoke", role="github-kanbien-core-platform-entity-smoke-publisher",
    local_image="kanbien-entity-smoke:qualification", tag_prefix="entity-smoke",
    artifact_stem="entity-smoke", error_prefix="ENTITY_SMOKE",
    configuration=CONFIGURATION,
))

if __name__ == "__main__":
    raise SystemExit(PUBLISHER.execute())
