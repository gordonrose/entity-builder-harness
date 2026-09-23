#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-rate-limit-smoke.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate the bounded staging rate-limit proof source without contacting the public target.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-rate-limit-smoke-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

output="$(npm run platform:shell:rate-limit-smoke -- --validate)"
if [[ "$output" != *'"rate_limit_smoke":"validated"'* ]] || [[ "$output" != *'"max_request_count":121'* ]]; then
  echo "ERROR: rate-limit smoke validation must expose only the bounded validated result." >&2
  exit 1
fi

if npm run platform:shell:rate-limit-smoke -- --validate --execute >/dev/null 2>&1; then
  echo "ERROR: rate-limit smoke must require exactly one execution mode." >&2
  exit 1
fi

echo "Platform-shell rate-limit smoke local validation passed."
