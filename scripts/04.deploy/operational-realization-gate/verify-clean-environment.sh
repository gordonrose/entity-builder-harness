#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.operational-realization-clean-environment
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Run canonical source validation using a fresh hash-locked CPython environment.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files, network]
#   used_by:
#   - id: package.script.deployment-realization-check-clean
#     path: package.json

SCRIPT_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VALIDATION_PYTHON=python3
VALIDATION_WHEELHOUSE=()
SEEN_PYTHON=false
SEEN_WHEELHOUSE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      [[ $# -ge 2 && "$SEEN_PYTHON" == false && -n "$2" && "$2" != -* ]] || { echo 'clean-environment-arguments-invalid' >&2; exit 2; }
      VALIDATION_PYTHON="$2"
      SEEN_PYTHON=true
      shift 2
      ;;
    --wheelhouse)
      [[ $# -ge 2 && "$SEEN_WHEELHOUSE" == false && -n "$2" && "$2" != -* ]] || { echo 'clean-environment-arguments-invalid' >&2; exit 2; }
      VALIDATION_WHEELHOUSE=(--wheelhouse "$2")
      SEEN_WHEELHOUSE=true
      shift 2
      ;;
    --help)
      echo 'Usage: verify-clean-environment.sh [--python PATH] [--wheelhouse DIRECTORY]'
      echo 'Requires CPython 3.14.4, Linux x86_64, glibc >=2.17; runs npm run deployment:realization:check.'
      exit 0
      ;;
    *) echo 'clean-environment-arguments-invalid' >&2; exit 2 ;;
  esac
done
exec "$VALIDATION_PYTHON" -I -B "$SCRIPT_DIRECTORY/clean_environment.py" "${VALIDATION_WHEELHOUSE[@]}"
