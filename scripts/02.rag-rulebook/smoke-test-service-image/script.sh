#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: rag-rulebook.script.smoke-test-service-image
#   version: 1
#   status: active
#   created_on: "2026-07-01"
#   updated_on: "2026-10-26"
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
CONTAINER_POSSIBLE=false
CACHE_SENTINEL_DIR=""
if [ -z "${DOCKER_CONFIG:-}" ]; then export DOCKER_CONFIG="$ROOT/.cache/04.deploy/docker-config"; fi
mkdir -p "$DOCKER_CONFIG"
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
    exit 77
  fi
  echo "ERROR: docker is required for this image smoke test." >&2
  exit 1
fi

if ! "$ENGINE" info >/dev/null 2>&1; then
  if [ "$ALLOW_SKIP" = true ]; then
    echo "SKIP: container engine is not running or not reachable: $ENGINE"
    exit 77
  fi
  echo "ERROR: container engine is not running or not reachable: $ENGINE" >&2
  exit 1
fi

cleanup() {
  local status=0
  if [ "$CONTAINER_POSSIBLE" = true ]; then
    python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py" --container "$CONTAINER_NAME" || status=$?
  fi
  if [ -n "$CACHE_SENTINEL_DIR" ]; then
    rm -f -- "$CACHE_SENTINEL_DIR/__pycache__/host-sentinel.pyc" "$CACHE_SENTINEL_DIR/host-sentinel.pyc" || status=$?
    rmdir -- "$CACHE_SENTINEL_DIR/__pycache__" "$CACHE_SENTINEL_DIR" || status=$?
    if [ -e "$CACHE_SENTINEL_DIR" ]; then status=1; else CACHE_SENTINEL_DIR=""; fi
  fi
  return "$status"
}
finish() {
  local original=$? cleanup_status=0
  trap - EXIT
  cleanup || cleanup_status=$?
  if [ "$original" -ne 0 ]; then exit "$original"; fi
  exit "$cleanup_status"
}
trap finish EXIT

# These unique disposable files exercise the actual Docker ignore ordering.
# Existing interpreter caches are never modified or removed.
CACHE_SENTINEL_DIR="$(mktemp -d "$ROOT/scripts/02.rag-rulebook/smoke-test-service-image/.cache-sentinel.XXXXXX")"
mkdir "$CACHE_SENTINEL_DIR/__pycache__"
printf 'host-only package-boundary sentinel\n' > "$CACHE_SENTINEL_DIR/__pycache__/host-sentinel.pyc"
printf 'host-only package-boundary sentinel\n' > "$CACHE_SENTINEL_DIR/host-sentinel.pyc"

bash scripts/02.rag-rulebook/build-service-image/script.sh \
  --tag "$TAG"

IMAGE_ID="$("$ENGINE" image inspect --format '{{.Id}}' "$TAG")"
if [[ ! "$IMAGE_ID" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "ERROR: built image has no immutable image identity." >&2
  exit 1
fi

CONTAINER_POSSIBLE=true
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
  --env RAG_RUNTIME_DIR=/app/.cache/02.rag-rulebook \
  "$IMAGE_ID" >/dev/null

node - "$PORT" "$TOKEN" "$(git rev-parse HEAD)" <<'NODE'
const [port, token, expectedCommit] = process.argv.slice(2);
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

  if (version.commit !== expectedCommit || version.runtime?.ready !== true) {
    throw new Error("packaged service version/runtime does not match the built source revision");
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
  const archiveQuery = await fetch(`${base}/context/query`, {
    method:"POST", headers:{authorization:`Bearer ${token}`,"content-type":"application/json"},
    body:JSON.stringify({requestText:"How do governed script permissions, run-governed-script, and governed scripts rules apply to Codex Claude Mistral?",maxChunks:8,format:"compact"}),
  });
  if(archiveQuery.status!==200)throw new Error(`archive evidence query failed: ${await archiveQuery.text()}`);
  const archivePacket=await archiveQuery.json();
  const unavailable=[".codex/rules/governed-scripts.rules",".claude/settings.json",".vibe/config.toml"];
  const missing=(archivePacket.gaps||[]).filter(gap=>gap.type==="missing-evidence").map(gap=>gap.description).join(" ");
  if(!unavailable.every(path=>missing.includes(path)) || !missing.includes("Unavailable source"))throw new Error("archive query hid unavailable canonical evidence");
  if((archivePacket.selected_chunks||[]).some(chunk=>unavailable.includes(chunk.source_path)))throw new Error("archive query included excluded local tool configuration");
  console.log(JSON.stringify({schema:"rag-rulebook/image-http-checks/v1",source_revision:version.commit,health:"ready",unauthorized_status:unauthorized.status,query_status:query.status,selected_chunk_count:packet.packet_summary.selected_chunk_count,archive_missing_evidence:unavailable}));
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
NODE

"$ENGINE" exec "$CONTAINER_NAME" node -e '
const fs=require("node:fs"),crypto=require("node:crypto"),path=require("node:path");
const hostCaches=[];
function inspectSources(root){
  for(const item of fs.readdirSync(root,{withFileTypes:true})){
    const name=path.join(root,item.name);
    if(item.name==="__pycache__" || /\.py[co]$/.test(item.name))hostCaches.push(name);
    else if(item.isDirectory())inspectSources(name);
  }
}
inspectSources("/app");
if(hostCaches.length)throw new Error("packaged host Python cache is present: "+hostCaches.join(","));
console.log(JSON.stringify({schema:"rag-rulebook/image-source-hygiene/v1",host_cache_sentinels:"excluded",python_cache_paths:hostCaches,verdict:"passed"}));
const bytes=fs.readFileSync("/app/.cache/02.rag-rulebook/manifest.json");
const manifest=JSON.parse(bytes);
if(manifest.git_sha!==process.env.COMMIT_SHA)throw new Error("packaged runtime source revision mismatch");
console.log(JSON.stringify({schema:"rag-rulebook/image-cache-evidence/v1",source_revision:manifest.git_sha,source_layout:manifest.source_layout,manifest_sha256:crypto.createHash("sha256").update(bytes).digest("hex"),fingerprints:manifest.fingerprints,counts:manifest.counts}));
'
cleanup
CONTAINER_POSSIBLE=false
printf '{"schema":"rag-rulebook/image-qualification/v1","image_id":"%s","cleanup":"confirmed-absent","verdict":"passed"}\n' "$IMAGE_ID"
echo "RAG/rulebook service image smoke test passed."
