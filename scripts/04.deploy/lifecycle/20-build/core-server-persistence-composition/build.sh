#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.core-server-persistence-composition-build
#   version: 1
#   status: draft
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Compile the provider-neutral persistence-capable core-server composition to caller-owned temporary output.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - writes-files
#   used_by:
#   - id: deploy.test.core-server-persistence-composition
#     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh

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
  --project infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.tsconfig.json \
  --outDir "$2" \
  --incremental false
