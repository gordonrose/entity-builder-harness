#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.environment-session-controller.immutable-publication
#   version: 1
#   status: draft
#   created_on: "2026-11-28"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind controller publication to the existing immutable-image publisher and its isolated registry.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-environment-session-controller
#     path: .github/workflows/publish-kanbien-core-platform-environment-session-controller.yml
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(ROOT / "scripts/04.deploy/shared/provider-adapters/aws"))
from ecr_publication import Binding, Publisher

PUBLISHER = Publisher(ROOT, Binding(
    source_repository="gordonrose/entity-builder-harness",
    workflow="publish-kanbien-core-platform-environment-session-controller.yml",
    pipeline="environment-session-controller-package-custody",
    target="kanbien-core-platform", scope="environment-sessions",
    account="337159794548", region="eu-west-1",
    repository="kanbien-core-platform/environment-session-controller",
    role="github-kanbien-core-platform-session-publisher",
    local_image="kanbien-environment-session-controller:qualification",
    tag_prefix="session-controller", artifact_stem="environment-session-controller",
    error_prefix="SESSION_CONTROLLER", configuration=(),
))

if __name__ == "__main__":
    raise SystemExit(PUBLISHER.execute())
