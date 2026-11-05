#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.verify-platform-shell-infrastructure
#   version: 44
#   status: active
#   created_on: "2026-09-06"
#   updated_on: "2026-10-28"
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Statically enforce the Kanbien staging platform-shell infrastructure and selected capability-observability policy invariants.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   - writes-files
#   used_by:
#   - id: package.script.platform-shell-infrastructure-check
#     path: package.json
#   - id: github.workflow.deploy-platform-shell-staging
#     path: .github/workflows/deploy-platform-shell-staging.yml
#   - id: deploy.rules.03-product.platform-target-alerting-policy
#     path: docs/04.deploy/rules/03.product/platform-target-alerting-policy.yml

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

exec bash scripts/repo/check-selection/script.sh --aggregate-members shell-infrastructure --execute-local --json
