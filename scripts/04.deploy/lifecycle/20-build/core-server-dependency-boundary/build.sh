#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.core-server-program-build
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Compile only the declared Kanbien core server program to caller-owned temporary output for local boundary inspection.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - writes-files
#   used_by:
#   - id: deploy.command.core-server-dependency-boundary
#     path: scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [[ $# -ne 2 || "$1" != "--out-dir" || -z "$2" ]]; then
  printf '%s\n' 'Usage: build.sh --out-dir <temporary-directory>' >&2
  exit 2
fi

if [[ ! -x node_modules/.bin/tsc ]]; then
  printf '%s\n' 'The local TypeScript compiler is unavailable. Run npm ci before this local build check.' >&2
  exit 3
fi

node_modules/.bin/tsc \
  --project infra/04.deploy/03.product/entrypoints/kanbien-core-server.tsconfig.json \
  --outDir "$2" \
  --incremental false
