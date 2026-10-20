#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.build-core-server-image
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Qualify the core-server compiled payload, then build its local-only candidate image without publishing or selecting a target.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - network
#   - writes-files
#   used_by:
#   - id: deploy.command.smoke-test-core-server-image
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TAG="entity-builder-harness/04.deploy/kanbien-core-server:local"
ALLOW_SKIP=false
NO_CACHE=false

usage() {
  cat <<'EOF'
Usage: build-core-server-image/script.sh [--tag <tag>] [--no-cache] [--allow-skip-without-engine]

Qualifies the declared core-server program and builds a local image only. It
does not publish an image, use cloud credentials, select a target, or deploy.
EOF
}

require_value() {
  if [[ "$#" -lt 2 || -z "${2:-}" || "${2:-}" == --* ]]; then
    printf 'ERROR: %s requires a value.\n' "$1" >&2
    exit 2
  fi
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --tag)
      require_value "$1" "${2:-}"
      TAG="$2"
      shift 2
      ;;
    --no-cache)
      NO_CACHE=true
      shift
      ;;
    --allow-skip-without-engine)
      ALLOW_SKIP=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'ERROR: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh \
  --contract infra/04.deploy/03.product/entrypoints/runnable-program-index.yml --json >/dev/null
bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh --json >/dev/null
bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/build.sh --out-dir "$TEMPORARY_DIRECTORY/artifacts"
node scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs \
  --compiled-root "$TEMPORARY_DIRECTORY/artifacts"
python3 scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py \
  --compiled-root "$TEMPORARY_DIRECTORY/artifacts" --json

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  if [[ "$ALLOW_SKIP" == true ]]; then
    printf '%s\n' 'SKIP: core-server payload qualification passed; container engine is unavailable.'
    exit 0
  fi
  printf '%s\n' 'ERROR: core-server payload qualification passed, but Docker is required to build the image.' >&2
  exit 1
fi

BUILD_ARGS=(
  build
  --file infra/04.deploy/03.product/image/core-server/Dockerfile
  --tag "$TAG"
  --label "org.opencontainers.image.revision=$(git rev-parse HEAD)"
  --label 'org.opencontainers.image.source=entity-builder-harness'
  --build-arg 'BUILD_NODE_IMAGE=node:22-bookworm-slim'
  --build-arg 'RUNTIME_NODE_IMAGE=node:22-bookworm-slim'
  --build-arg "SOURCE_COMMIT_SHA=$(git rev-parse HEAD)"
)
if [[ "$NO_CACHE" == true ]]; then
  BUILD_ARGS+=(--no-cache)
fi
BUILD_ARGS+=("$ROOT")
docker "${BUILD_ARGS[@]}"
printf 'Built local core-server image: %s\n' "$TAG"
