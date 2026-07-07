#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.query-context
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#     - sre
#   kind: script
#   purpose: Query the RAG/rulebook context provider through the hosted/local provider boundary.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#     - network
#   used_by:
#     - id: rag-rulebook.source-material.hosted-context-provider-contract
#       path: docs/02.rag-rulebook/source-material/hosted-context-provider-contract.md
#     - id: rag-rulebook.rules.concerns.hosted-context-provider-contract
#       path: docs/02.rag-rulebook/rules/concerns/hosted-context-provider-contract.yml
#     - id: rag-rulebook.script.query-context.readme
#       path: scripts/02.rag-rulebook/query-context/README.md
#     - id: rag-rulebook.script.query-context.smoke-test
#       path: scripts/02.rag-rulebook/query-context/smoke-test.sh

if [ -n "${RAG_REPO_ROOT:-}" ]; then
  ROOT="$(cd "$RAG_REPO_ROOT" && pwd)"
else
  ROOT="$(git rev-parse --show-toplevel)"
fi
for marker in package.json .agentic/02.rag-rulebook/service scripts/02.rag-rulebook; do
  if [ ! -e "$ROOT/$marker" ]; then
    echo "ERROR: RAG repo root is missing required marker: $marker" >&2
    exit 2
  fi
done
cd "$ROOT"

CONFIG_PATH="${RAG_RULEBOOK_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/rag-rulebook/rag.env}"
PROVIDER_ARG=""
BASE_URL_ARG=""
RUNTIME_DIR=".cache/02.rag-rulebook"
REQUEST_TEXT=""
SESSION_ID=""
SESSION_BRANCH=""
SESSION_WORKTREE=""
SESSION_LAYER="unknown"
SESSION_MODE="unknown"
SESSION_WORKFLOW="unknown"
PREVIOUS_PACKET_ID=""
PREVIOUS_ROUTING_SUMMARY=""
TRUST_SESSION_ROUTING=false
MAX_CHUNKS=""
PRETTY=false
FORMAT="compact"
NO_FOCUSED_PATHS=false
FOCUSED_PATHS=()

usage() {
  cat <<'EOF'
Usage:
  query-context/script.sh --request-text <text> [options]

Options:
  --provider <hosted|local|auto>
                              Provider mode. Defaults to RAG_RULEBOOK_PROVIDER
                              from config, or local when unset.
  --config <path>             Local RAG provider config. Default:
                              ~/.config/rag-rulebook/rag.env
  --base-url <url>            Hosted RAG service base URL. May also come from
                              RAG_RULEBOOK_BASE_URL.
  --runtime-dir <path>        Local runtime cache for local provider mode.
  --request-text <text>       Prompt text used for context retrieval.
  --session-id <id>           Chat/session ID for provenance.
  --session-branch <branch>   Chat/session branch for provenance.
  --session-worktree <path>   Chat/session worktree for provenance.
  --session-layer <layer>     Legacy session routing hint. Default: unknown.
  --session-mode <mode>       Legacy session routing hint. Default: unknown.
  --session-workflow <path>   Legacy session workflow hint. Default: unknown.
  --previous-packet-id <id>   Previous context packet for continuity.
  --previous-routing-summary <text>
                              Previous packet routing summary.
  --trust-session-routing     Local-provider only. Trust supplied session
                              layer/mode/workflow after governed session proof.
  --focused-path <path>       Focused path signal. Repeatable.
  --no-focused-paths          Use no focused path signals.
  --max-chunks <n>            Maximum selected chunks. Range: 3-12.
  --format <full|compact>     Output format. Default: compact.
  --pretty                    Pretty-print JSON responses.

Hosted mode loads auth from RAG_RULEBOOK_TOKEN or, when available,
RAG_RULEBOOK_TOKEN_SECRET_ARN plus AWS profile/region. Token values and
Authorization headers must not be printed.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --provider)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --provider requires hosted, local, or auto." >&2
        exit 2
      fi
      PROVIDER_ARG="$2"
      shift 2
      ;;
    --config)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --config requires a path." >&2
        exit 2
      fi
      CONFIG_PATH="$2"
      shift 2
      ;;
    --base-url)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --base-url requires a URL." >&2
        exit 2
      fi
      BASE_URL_ARG="$2"
      shift 2
      ;;
    --runtime-dir)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --runtime-dir requires a path." >&2
        exit 2
      fi
      RUNTIME_DIR="$2"
      shift 2
      ;;
    --request-text)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --request-text requires text." >&2
        exit 2
      fi
      REQUEST_TEXT="$2"
      shift 2
      ;;
    --session-id)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-id requires a value." >&2
        exit 2
      fi
      SESSION_ID="$2"
      shift 2
      ;;
    --session-branch)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-branch requires a value." >&2
        exit 2
      fi
      SESSION_BRANCH="$2"
      shift 2
      ;;
    --session-worktree)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-worktree requires a value." >&2
        exit 2
      fi
      SESSION_WORKTREE="$2"
      shift 2
      ;;
    --session-layer)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-layer requires a layer." >&2
        exit 2
      fi
      SESSION_LAYER="$2"
      shift 2
      ;;
    --session-mode)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-mode requires a mode." >&2
        exit 2
      fi
      SESSION_MODE="$2"
      shift 2
      ;;
    --session-workflow)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-workflow requires a path." >&2
        exit 2
      fi
      SESSION_WORKFLOW="$2"
      shift 2
      ;;
    --previous-packet-id)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --previous-packet-id requires a value." >&2
        exit 2
      fi
      PREVIOUS_PACKET_ID="$2"
      shift 2
      ;;
    --previous-routing-summary)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --previous-routing-summary requires text." >&2
        exit 2
      fi
      PREVIOUS_ROUTING_SUMMARY="$2"
      shift 2
      ;;
    --trust-session-routing)
      TRUST_SESSION_ROUTING=true
      shift
      ;;
    --focused-path)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --focused-path requires a path." >&2
        exit 2
      fi
      FOCUSED_PATHS+=("$2")
      shift 2
      ;;
    --no-focused-paths)
      NO_FOCUSED_PATHS=true
      shift
      ;;
    --max-chunks)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --max-chunks requires a number." >&2
        exit 2
      fi
      MAX_CHUNKS="$2"
      shift 2
      ;;
    --format)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --format requires full or compact." >&2
        exit 2
      fi
      FORMAT="$2"
      case "$FORMAT" in
        full|compact)
          ;;
        *)
          echo "ERROR: --format must be full or compact." >&2
          exit 2
          ;;
      esac
      shift 2
      ;;
    --pretty)
      PRETTY=true
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

if [ -z "$REQUEST_TEXT" ]; then
  echo "ERROR: --request-text is required." >&2
  usage >&2
  exit 2
fi

load_config() {
  if [ ! -f "$CONFIG_PATH" ]; then
    return
  fi
  local mode mode_num
  mode="$(stat -c "%a" "$CONFIG_PATH")"
  mode_num=$((8#$mode))
  if (( (mode_num & 077) != 0 )); then
    echo "ERROR: RAG provider config is group/other-readable: $CONFIG_PATH" >&2
    echo "Expected permissions like 600 or 400." >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  . "$CONFIG_PATH"
  set +a
}

call_local_provider() {
  local command=(
    bash
    scripts/02.rag-rulebook/query-local-context/script.sh
    --runtime-dir "$RUNTIME_DIR"
    --request-text "$REQUEST_TEXT"
    --session-id "$SESSION_ID"
    --session-branch "$SESSION_BRANCH"
    --session-worktree "$SESSION_WORKTREE"
    --session-layer "$SESSION_LAYER"
    --session-mode "$SESSION_MODE"
    --session-workflow "$SESSION_WORKFLOW"
    --previous-packet-id "$PREVIOUS_PACKET_ID"
    --previous-routing-summary "$PREVIOUS_ROUTING_SUMMARY"
    --format "$FORMAT"
  )
  if [ "$TRUST_SESSION_ROUTING" = true ]; then
    command+=(--trust-session-routing)
  fi
  if [ "$NO_FOCUSED_PATHS" = true ]; then
    command+=(--no-focused-paths)
  else
    local focused_path
    for focused_path in "${FOCUSED_PATHS[@]}"; do
      command+=(--focused-path "$focused_path")
    done
  fi
  if [ -n "$MAX_CHUNKS" ]; then
    command+=(--max-chunks "$MAX_CHUNKS")
  fi
  if [ "$PRETTY" = true ]; then
    command+=(--pretty)
  fi
  "${command[@]}"
}

provider_gap() {
  local gap_id="$1"
  local message="$2"
  echo "ERROR: $gap_id: $message" >&2
}

resolve_hosted_token() {
  if [ -n "${RAG_RULEBOOK_TOKEN:-}" ]; then
    printf "%s" "$RAG_RULEBOOK_TOKEN"
    return
  fi
  if [ -z "${RAG_RULEBOOK_TOKEN_SECRET_ARN:-}" ]; then
    return 1
  fi
  local aws_args=(secretsmanager get-secret-value --secret-id "$RAG_RULEBOOK_TOKEN_SECRET_ARN" --query SecretString --output text)
  if [ -n "${RAG_RULEBOOK_AWS_PROFILE:-}" ]; then
    aws_args+=(--profile "$RAG_RULEBOOK_AWS_PROFILE")
  fi
  if [ -n "${RAG_RULEBOOK_AWS_REGION:-}" ]; then
    aws_args+=(--region "$RAG_RULEBOOK_AWS_REGION")
  fi
  aws "${aws_args[@]}"
}

pretty_or_raw_response() {
  local response_file="$1"
  if [ "$PRETTY" = true ]; then
    node - "$response_file" <<'NODE'
const fs = require("fs");
const path = process.argv[2];
const data = JSON.parse(fs.readFileSync(path, "utf8"));
process.stdout.write(JSON.stringify(data, null, 2) + "\n");
NODE
  else
    cat "$response_file"
  fi
}

call_hosted_provider() {
  if [ "$TRUST_SESSION_ROUTING" = true ]; then
    provider_gap \
      "gap.rag-rulebook.hosted-context-provider-local-trust-rejected" \
      "hosted provider mode does not accept --trust-session-routing; pass session fields as provenance only."
    exit 1
  fi
  local base_url token request_json focused_paths_file curl_config response_file http_code
  base_url="${BASE_URL_ARG:-${RAG_RULEBOOK_BASE_URL:-}}"
  if [ -z "$base_url" ]; then
    provider_gap \
      "gap.rag-rulebook.hosted-context-provider-auth-missing" \
      "hosted provider mode requires RAG_RULEBOOK_BASE_URL or --base-url."
    exit 1
  fi
  if [ "${RAG_RULEBOOK_AUTH_MODE:-bearer}" != "bearer" ]; then
    provider_gap \
      "gap.rag-rulebook.hosted-context-provider-auth-missing" \
      "only bearer auth is currently governed for hosted provider mode."
    exit 1
  fi
  if ! token="$(resolve_hosted_token)"; then
    provider_gap \
      "gap.rag-rulebook.hosted-context-provider-auth-missing" \
      "hosted provider mode requires RAG_RULEBOOK_TOKEN or RAG_RULEBOOK_TOKEN_SECRET_ARN."
    exit 1
  fi
  if [ -z "$token" ] || [ "$token" = "None" ]; then
    provider_gap \
      "gap.rag-rulebook.hosted-context-provider-auth-missing" \
      "hosted provider auth resolved to an empty token."
    exit 1
  fi

  request_json="$(mktemp)"
  focused_paths_file="$(mktemp)"
  curl_config="$(mktemp)"
  response_file="$(mktemp)"
  HOSTED_REQUEST_JSON="$request_json"
  HOSTED_FOCUSED_PATHS_FILE="$focused_paths_file"
  HOSTED_CURL_CONFIG="$curl_config"
  HOSTED_RESPONSE_FILE="$response_file"
  cleanup_hosted() {
    rm -f \
      "${HOSTED_REQUEST_JSON:-}" \
      "${HOSTED_FOCUSED_PATHS_FILE:-}" \
      "${HOSTED_CURL_CONFIG:-}" \
      "${HOSTED_RESPONSE_FILE:-}"
  }
  trap cleanup_hosted EXIT
  chmod 600 "$curl_config"
  local focused_path
  for focused_path in "${FOCUSED_PATHS[@]}"; do
    printf "%s\n" "$focused_path" >> "$focused_paths_file"
  done

  REQUEST_TEXT="$REQUEST_TEXT" \
  SESSION_ID="$SESSION_ID" \
  SESSION_BRANCH="$SESSION_BRANCH" \
  SESSION_WORKTREE="$SESSION_WORKTREE" \
  SESSION_LAYER="$SESSION_LAYER" \
  SESSION_MODE="$SESSION_MODE" \
  SESSION_WORKFLOW="$SESSION_WORKFLOW" \
  PREVIOUS_PACKET_ID="$PREVIOUS_PACKET_ID" \
  PREVIOUS_ROUTING_SUMMARY="$PREVIOUS_ROUTING_SUMMARY" \
  NO_FOCUSED_PATHS="$NO_FOCUSED_PATHS" \
  MAX_CHUNKS="$MAX_CHUNKS" \
  FORMAT="$FORMAT" \
  node - "$request_json" "$focused_paths_file" <<'NODE'
const fs = require("fs");
const [requestPath, focusedPathFile] = process.argv.slice(2);
const env = process.env;
const focusedPaths = fs.readFileSync(focusedPathFile, "utf8")
  .split("\n")
  .filter(Boolean);
const body = {
  requestText: env.REQUEST_TEXT,
  focusedPaths,
  noFocusedPaths: env.NO_FOCUSED_PATHS === "true",
  format: env.FORMAT || "compact",
};
const optional = {
  sessionId: env.SESSION_ID,
  sessionBranch: env.SESSION_BRANCH,
  sessionWorktree: env.SESSION_WORKTREE,
  sessionLayer: env.SESSION_LAYER,
  sessionMode: env.SESSION_MODE,
  sessionWorkflow: env.SESSION_WORKFLOW,
  previousPacketId: env.PREVIOUS_PACKET_ID,
  previousRoutingSummary: env.PREVIOUS_ROUTING_SUMMARY,
};
for (const [key, value] of Object.entries(optional)) {
  if (value && value !== "unknown") {
    body[key] = value;
  }
}
if (env.MAX_CHUNKS) {
  body.maxChunks = Number(env.MAX_CHUNKS);
}
fs.writeFileSync(requestPath, JSON.stringify(body));
NODE

  {
    printf "%s\n" "silent"
    printf "%s\n" "show-error"
    printf "%s\n" "request = \"POST\""
    printf "url = \"%s/context/query\"\n" "${base_url%/}"
    printf "%s\n" "header = \"Content-Type: application/json\""
    printf "header = \"Authorization: Bearer %s\"\n" "$token"
    printf "data-binary = \"@%s\"\n" "$request_json"
    printf "output = \"%s\"\n" "$response_file"
    printf "%s\n" "write-out = \"%{http_code}\""
  } > "$curl_config"

  if ! http_code="$(curl --config "$curl_config")"; then
    provider_gap \
      "gap.rag-rulebook.hosted-context-provider-runtime-error" \
      "hosted provider request failed before a usable HTTP response was returned."
    exit 1
  fi
  case "$http_code" in
    200)
      pretty_or_raw_response "$response_file"
      ;;
    401)
      provider_gap \
        "gap.rag-rulebook.hosted-context-provider-auth-rejected" \
        "hosted provider rejected the configured bearer token."
      exit 1
      ;;
    *)
      provider_gap \
        "gap.rag-rulebook.hosted-context-provider-runtime-error" \
        "hosted provider returned HTTP $http_code."
      exit 1
      ;;
  esac
}

load_config

PROVIDER="${PROVIDER_ARG:-${RAG_RULEBOOK_PROVIDER:-local}}"
case "$PROVIDER" in
  hosted|local|auto)
    ;;
  *)
    echo "ERROR: provider must be hosted, local, or auto." >&2
    exit 2
    ;;
esac

if [ "$PROVIDER" = "auto" ]; then
  if [ -n "${RAG_RULEBOOK_BASE_URL:-}" ] || [ -n "$BASE_URL_ARG" ] || [ -n "${RAG_RULEBOOK_TOKEN:-}" ] || [ -n "${RAG_RULEBOOK_TOKEN_SECRET_ARN:-}" ]; then
    if [ -n "${RAG_RULEBOOK_TOKEN:-}" ] || [ -n "${RAG_RULEBOOK_TOKEN_SECRET_ARN:-}" ]; then
      PROVIDER="hosted"
    elif [ "${RAG_RULEBOOK_LOCAL_FALLBACK:-}" = "dev-only" ]; then
      PROVIDER="local"
    else
      provider_gap \
        "gap.rag-rulebook.hosted-context-provider-local-fallback-blocked" \
        "auto mode found hosted config without auth, and local fallback is not governed."
      exit 1
    fi
  else
    PROVIDER="local"
  fi
fi

case "$PROVIDER" in
  hosted)
    call_hosted_provider
    ;;
  local)
    call_local_provider
    ;;
esac
