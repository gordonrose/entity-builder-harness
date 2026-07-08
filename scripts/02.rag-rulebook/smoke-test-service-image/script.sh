#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.smoke-test-service-image
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#   - agentic
#   - architecture
#   - sre
#   kind: script
#   purpose: Smoke test the RAG/rulebook service container image with hardened runtime, health, version, and context query checks.
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
#   - id: rag-rulebook.script.smoke-test-service-image.readme
#     path: scripts/02.rag-rulebook/smoke-test-service-image/README.md
#   - id: rag-rulebook.script.build-service-image
#     path: scripts/02.rag-rulebook/build-service-image/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

ENGINE="docker"
PORT="${RAG_IMAGE_SMOKE_PORT:-39452}"
ALLOW_SKIP=false
TAG="entity-builder-harness/02.rag-rulebook/rag-rulebook-service:smoke"
RUNTIME_DIR=".cache/02.rag-rulebook-image-smoke"
CONTAINER_NAME="rag-rulebook-service-smoke-$$"
TOKEN="smoke-token-$$"

usage() {
  cat <<'EOF'
Usage:
  smoke-test-service-image/script.sh [--port <port>] [--allow-skip-without-engine]

Builds and runs the RAG/rulebook service image locally, then verifies:
  GET  /health
  GET  /version
  POST /context/query
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
    --engine)
      echo "ERROR: --engine is not supported; this MSP image smoke test uses docker only." >&2
      exit 2
      ;;
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
  rm -rf "$RUNTIME_DIR"
}
trap cleanup EXIT

rm -rf "$RUNTIME_DIR"

bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir "$RUNTIME_DIR" \
  --pretty >/dev/null

bash scripts/02.rag-rulebook/build-service-image/script.sh \
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
  --env RAG_ALLOW_NON_LOOPBACK=1 \
  --env RAG_SERVICE_TOKEN="$TOKEN" \
  --env RAG_REPO_ROOT=/app \
  --env RAG_RUNTIME_DIR="$RUNTIME_DIR" \
  --volume "$ROOT/$RUNTIME_DIR:/app/$RUNTIME_DIR:ro" \
  "$TAG" >/dev/null

node - "$PORT" "$TOKEN" <<'NODE'
const [port, token] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;

async function waitForHealth() {
  const deadline = Date.now() + 20000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${base}/health`);
      if (response.status === 200) {
        const body = await response.json();
        if (body.status === "ready") return;
      }
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw lastError || new Error("container service did not become healthy");
}

async function main() {
  await waitForHealth();

  const version = await fetch(`${base}/version`).then((response) => response.json());
  if (version.service !== "rag-rulebook-service") {
    throw new Error(`unexpected service name: ${version.service}`);
  }

  const unauthorized = await fetch(`${base}/context/query`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ requestText: "Check authorization." }),
  });
  if (unauthorized.status !== 401) {
    throw new Error(`expected unauthorized query to return 401, got ${unauthorized.status}`);
  }

  const query = await fetch(`${base}/context/query`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      requestText: "Given my architecture, how should I run the RAG rulebook service?",
      session: {
        layer: "02.rag-rulebook",
        mode: "discovery",
        workflow: ".agentic/02.rag-rulebook/workflows/default.md",
      },
      maxChunks: 6,
      format: "compact",
    }),
  });

  if (query.status !== 200) {
    throw new Error(`query failed with status ${query.status}: ${await query.text()}`);
  }

  const packet = await query.json();
  if (packet.schema !== "rag-rulebook/context-packet-compact/v1") {
    throw new Error(`unexpected packet schema: ${packet.schema}`);
  }
  if (!packet.packet_summary || packet.packet_summary.selected_chunk_count < 1) {
    throw new Error("query returned no selected chunks");
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
NODE

echo "RAG/rulebook service image smoke test passed."
