#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-persistence-delivery-proof.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: persistence
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Verify that the staging outbox delivery proof is fixed, bounded, and redacted without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.py").read_text(encoding="utf-8"), "persistence-delivery-proof.py", "exec")'
result="$(bash scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.sh --validate)"
if [[ "$result" != *'"persistence_delivery_proof":"validated"'* ]] || [[ "$result" != *'"maximum_wait_seconds":360'* ]] || [[ "$result" != *'"worker_metric_settlement_wait_seconds":75'* ]]; then
  echo "ERROR: persistence delivery-proof validation must emit only the reviewed aggregate policy." >&2
  exit 1
fi

if bash scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.sh --start-relay >/dev/null 2>&1; then
  echo "ERROR: a mutating persistence delivery-proof stage must require its explicit live-operation guard." >&2
  exit 1
fi

if bash scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.sh --validate --start-relay >/dev/null 2>&1; then
  echo "ERROR: persistence delivery proof must accept exactly one operating mode." >&2
  exit 1
fi

if rg -n 'add_argument\("--target-profile"|add_argument\("--aws-cli"|add_argument\("--aws-credential-source"|add_argument\("--task-definition"|add_argument\("--network-configuration"|send-message|message-body|ecs", "wait"' scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.py >/dev/null; then
  echo "ERROR: persistence delivery proof must not accept caller-selected target, credential, task, network, or direct queue-message inputs." >&2
  exit 1
fi

python3 - <<'PY'
from pathlib import Path

source = Path("scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.py").read_text(encoding="utf-8")
valid_filter = '"ecs", "list-tasks", "--cluster", policy["cluster"], "--started-by", started_by'
stopped_filter = '"ecs", "list-tasks", "--cluster", policy["cluster"], "--family", expected_family, "--desired-status", "STOPPED"'
if valid_filter not in source or stopped_filter not in source or 'task.get("startedBy") == started_by' not in source:
    raise SystemExit("ERROR: labelled ECS task inspection must use valid active and stopped task filters before matching the proof label in memory.")
if 'def recovery_relay_not_started' not in source:
    raise SystemExit("ERROR: persistence delivery proof must prevent a second labelled relay task after a failed first attempt.")
if '"TargetGroupArn"' not in source or 'def public_target_health_is_healthy' not in source or 'outputs["TargetGroupArn"]' not in source:
    raise SystemExit("ERROR: persistence delivery proof must derive and verify target health from the Foundation-exported platform-shell target group.")
PY

echo "Persistence delivery-proof local validation passed."
