#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.build-service-image
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#   - agentic
#   - architecture
#   - sre
#   kind: script
#   purpose: Build the RAG/rulebook service container image from the governed infra image boundary.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   effects:
#   - network
#   - writes-files
#   used_by:
#   - id: rag-rulebook.script.build-service-image.readme
#     path: scripts/02.rag-rulebook/build-service-image/README.md
#   - id: rag-rulebook.script.smoke-test-service-image
#     path: scripts/02.rag-rulebook/smoke-test-service-image/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

ENGINE="docker"
TAG="entity-builder-harness/02.rag-rulebook/rag-rulebook-service:local"
BASE_IMAGE="node:22-bookworm-slim"
REQUIRE_DIGEST_BASE=false
NO_CACHE=false
DOCKERFILE="infra/04.deploy/02.rag-rulebook/image/Dockerfile"
DOCKERIGNORE="infra/04.deploy/02.rag-rulebook/image/Dockerfile.dockerignore"
CONTEXT="$ROOT"

usage() {
  cat <<'EOF'
Usage:
  build-service-image/script.sh [--tag <tag>] [--base-image <image>] [--require-digest-base] [--no-cache]

Builds the local RAG/rulebook service image from:
  infra/04.deploy/02.rag-rulebook/image/Dockerfile

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
    --engine)
      echo "ERROR: --engine is not supported; this MSP image wrapper uses docker only." >&2
      exit 2
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
    --production)
      echo "ERROR: --production is not supported; use --require-digest-base for the local image guard." >&2
      exit 2
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

echo "Built RAG/rulebook service image: $TAG"
echo "Dockerfile: $DOCKERFILE"
echo "Build context: $CONTEXT"
echo "Effective ignore file: $DOCKERIGNORE"
