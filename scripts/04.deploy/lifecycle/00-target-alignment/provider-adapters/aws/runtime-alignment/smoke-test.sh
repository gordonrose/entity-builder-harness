#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.runtime-alignment
#   version: 1
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the AWS runtime alignment adapter recognises only stable successful CloudFormation states.
#   portability: { class: reusable, targets: [entity-builder] }
#   used_by:
#   - id: deploy.adapter.aws.runtime-alignment
#     path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py
#   effects: [read-only]

ROOT="$(git rev-parse --show-toplevel)"
python3 - "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("runtime_alignment", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.STABLE_SUCCESSFUL_STACK_STATUSES == {"CREATE_COMPLETE", "UPDATE_COMPLETE"}
assert "UPDATE_IN_PROGRESS" not in module.STABLE_SUCCESSFUL_STACK_STATUSES
assert "UPDATE_ROLLBACK_COMPLETE" not in module.STABLE_SUCCESSFUL_STACK_STATUSES
PY

echo "AWS runtime-alignment state tests passed."
