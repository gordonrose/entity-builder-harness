#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.build-platform-shell-image
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - agentic
#   - sre
#   kind: script
#   purpose: Build the platform shell container image from the governed infra image boundary.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - network
#   - writes-files
#   used_by:
#   - id: deploy.script.build-platform-shell-image.readme
#     path: scripts/04.deploy/build-platform-shell-image/README.md
#   - id: deploy.script.smoke-test-platform-shell-image
#     path: scripts/04.deploy/smoke-test-platform-shell-image/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -z "${DOCKER_CONFIG:-}" ]; then
  export DOCKER_CONFIG="$ROOT/.cache/04.deploy/docker-config"
fi
mkdir -p "$DOCKER_CONFIG"

TAG="entity-builder-harness/03.product/platform-shell:local"
BASE_IMAGE="node:22-bookworm-slim"
REQUIRE_DIGEST_BASE=false
NO_CACHE=false
DOCKERFILE="infra/04.deploy/03.product/image/Dockerfile"
DOCKERIGNORE="infra/04.deploy/03.product/image/Dockerfile.dockerignore"
CONTEXT="$ROOT"

usage() {
  cat <<'EOF'
Usage:
  build-platform-shell-image/script.sh [--tag <tag>] [--base-image <image>] [--require-digest-base] [--no-cache]

Builds the local platform shell image from:
  infra/04.deploy/03.product/image/Dockerfile

The command builds a local image only. It does not publish, deploy, call AWS,
or mutate GitHub.
EOF
}

require_value() {
  local flag="$1"
  if [ "$#" -lt 2 ] || [ -z "${2:-}" ] || [[ "${2:-}" == --* ]]; then
    echo "ERROR: $flag requires a value." >&2
    exit 2
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --tag)
      require_value "$1" "${2:-}"
      TAG="$2"
      shift 2
      ;;
    --base-image)
      require_value "$1" "${2:-}"
      BASE_IMAGE="$2"
      shift 2
      ;;
    --require-digest-base)
      REQUIRE_DIGEST_BASE=true
      shift
      ;;
    --no-cache)
      NO_CACHE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

find_engine() {
  if command -v docker >/dev/null 2>&1; then
    printf '%s\n' docker
    return
  fi
  echo "ERROR: docker is required for this image build wrapper." >&2
  exit 1
}

ENGINE="$(find_engine)"

if [ "$REQUIRE_DIGEST_BASE" = true ] && [[ "$BASE_IMAGE" != *@sha256:* ]]; then
  echo "ERROR: --require-digest-base requires --base-image pinned by digest." >&2
  exit 1
fi

if ! "$ENGINE" info >/dev/null 2>&1; then
  echo "ERROR: container engine is not running or not reachable: $ENGINE" >&2
  exit 1
fi

bash scripts/04.deploy/validate-container-boundaries/script.sh >/dev/null

if [ ! -f "$DOCKERIGNORE" ]; then
  echo "ERROR: expected Dockerfile-specific ignore file is missing: $DOCKERIGNORE" >&2
  exit 1
fi

COMMIT_SHA="$(git rev-parse HEAD)"

BUILD_ARGS=(
  build
  --file "$DOCKERFILE"
  --tag "$TAG"
  --label "org.opencontainers.image.revision=$COMMIT_SHA"
  --label "org.opencontainers.image.source=entity-builder-harness"
  --build-arg "NODE_IMAGE=$BASE_IMAGE"
  --build-arg "SOURCE_COMMIT_SHA=$COMMIT_SHA"
)

if [ "$NO_CACHE" = true ]; then
  BUILD_ARGS+=(--no-cache)
fi

BUILD_ARGS+=("$CONTEXT")

"$ENGINE" "${BUILD_ARGS[@]}"

echo "Built platform shell image: $TAG"
echo "Dockerfile: $DOCKERFILE"
echo "Build context: $CONTEXT"
echo "Effective ignore file: $DOCKERIGNORE"
