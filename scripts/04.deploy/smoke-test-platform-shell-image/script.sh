#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.smoke-test-platform-shell-image
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - agentic
#   - sre
#   kind: script
#   purpose: Smoke test the platform shell container image with liveness and readiness checks.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - network
#   - writes-files
#   used_by:
#   - id: deploy.script.smoke-test-platform-shell-image.readme
#     path: scripts/04.deploy/smoke-test-platform-shell-image/README.md
#   - id: deploy.script.build-platform-shell-image
#     path: scripts/04.deploy/build-platform-shell-image/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -z "${DOCKER_CONFIG:-}" ]; then
  export DOCKER_CONFIG="$ROOT/.cache/04.deploy/docker-config"
fi
mkdir -p "$DOCKER_CONFIG"

PORT="${PLATFORM_SHELL_IMAGE_SMOKE_PORT:-39453}"
ALLOW_SKIP=false
TAG="entity-builder-harness/03.product/platform-shell:smoke"
CONTAINER_NAME="platform-shell-smoke-$$"

usage() {
  cat <<'EOF'
Usage:
  smoke-test-platform-shell-image/script.sh [--port <port>] [--allow-skip-without-engine]

Builds and runs the platform shell image locally, then verifies:
  GET /livez
  GET /readyz
EOF
}

require_value() {
  local flag="$1"
  if [ "$#" -lt 2 ] || [ -z "${2:-}" ] || [[ "${2:-}" == --* ]]; then
    echo "ERROR: $flag requires a value." >&2
    exit 2
  fi
}

validate_port() {
  if [[ ! "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "ERROR: --port must be an integer between 1 and 65535." >&2
    exit 2
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --port)
      require_value "$1" "${2:-}"
      PORT="$2"
      shift 2
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
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

validate_port

find_engine() {
  if command -v docker >/dev/null 2>&1; then
    printf '%s\n' docker
    return
  fi
  return 1
}

if ! ENGINE="$(find_engine)"; then
  if [ "$ALLOW_SKIP" = true ]; then
    echo "SKIP: no container engine found."
    exit 0
  fi
  echo "ERROR: docker is required for this image smoke test." >&2
  exit 1
fi

if ! "$ENGINE" info >/dev/null 2>&1; then
  if [ "$ALLOW_SKIP" = true ]; then
    echo "SKIP: container engine is not running or not reachable: $ENGINE"
    exit 0
  fi
  echo "ERROR: container engine is not running or not reachable: $ENGINE" >&2
  exit 1
fi

cleanup() {
  "$ENGINE" rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

bash scripts/04.deploy/build-platform-shell-image/script.sh \
  --tag "$TAG" >/dev/null

"$ENGINE" run \
  --detach \
  --rm \
  --name "$CONTAINER_NAME" \
  --publish "127.0.0.1:${PORT}:3000" \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --env HOST=0.0.0.0 \
  --env PORT=3000 \
  --env PLATFORM_SMOKE_APP_NAME="Platform Shell Image Smoke" \
  "$TAG" >/dev/null

node - "$PORT" <<'NODE'
const [port] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;

async function waitFor(path, expectedStatus, expectedBodyStatus) {
  const deadline = Date.now() + 20000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${base}${path}`);
      if (response.status === expectedStatus) {
        const body = await response.json();
        if (body.status === expectedBodyStatus) return;
      }
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw lastError || new Error(`${path} did not return ${expectedStatus} ${expectedBodyStatus}`);
}

async function main() {
  await waitFor("/livez", 200, "live");
  await waitFor("/readyz", 200, "ready");
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
NODE

echo "Platform shell image smoke test passed."
