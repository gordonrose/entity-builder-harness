#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.build-core-server-persistence-image
#   version: 2
#   status: draft
#   created_on: "2026-10-23"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compile and build only the local PostgreSQL-backed core-server candidate image; it never publishes or deploys.
#   portability: { class: internal, targets: [] }
#   effects: [network, writes-files]
#   used_by:
#   - id: infra.04-deploy.03-product.image.core-server-persistence.contract
#     path: infra/04.deploy/03.product/image/core-server-persistence/image-contract.yml
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TAG="entity-builder-harness/04.deploy/kanbien-core-server-persistence:local"
if [[ $# -eq 2 && "$1" == "--tag" && -n "$2" ]]; then TAG="$2"; elif [[ $# -ne 0 ]]; then printf '%s\n' 'Usage: script.sh [--tag <tag>]' >&2; exit 2; fi
bash scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh --scope-contract infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml --json
python3 scripts/04.deploy/inventory-deploy-control/script.py --delivery --check
bash scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh --target-root infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes --json
bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh --contract infra/04.deploy/03.product/entrypoints/runnable-program-index.yml --json >/dev/null
bash scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh
if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then printf '%s\n' 'ERROR: Docker is required to qualify the persistence candidate image.' >&2; exit 1; fi
docker build --file infra/04.deploy/03.product/image/core-server-persistence/Dockerfile --tag "$TAG" --label "org.opencontainers.image.revision=$(git rev-parse HEAD)" --label 'org.opencontainers.image.source=entity-builder-harness' --build-arg "SOURCE_COMMIT_SHA=$(git rev-parse HEAD)" "$ROOT"
printf 'Built local core-server persistence image: %s\n' "$TAG"
