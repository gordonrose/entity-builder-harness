#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.infrastructure-plan
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Inspect qualified infrastructure inputs and produce a concrete safe plan without admitting an AWS write.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   argument_validation: {flag: --validate-arguments, effects: [read-only]}
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
for argument in "$@"; do
  case "$argument" in
    --mode|--mode=*) printf '%s\n' '{"schema":"deploy/entity-smoke-infrastructure-report/v1","verdict":"blocked","condition":"infrastructure-arguments-invalid","effect":"not-started"}'; exit 2 ;;
  esac
done
ROOT="$(git rev-parse --show-toplevel)"
exec python3 -B "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/script.py" --mode plan "$@"
