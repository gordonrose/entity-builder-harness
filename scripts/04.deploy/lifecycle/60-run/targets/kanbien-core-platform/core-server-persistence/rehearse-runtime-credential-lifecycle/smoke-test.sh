#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.runtime-credential-lifecycle
#   version: 1
#   status: draft
#   created_on: "2026-10-24"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove bounded runtime IAM-identity recovery controller decisions without AWS mutation.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.rehearse-runtime-credential-lifecycle
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh
#   effects: [read-only]

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.py"

python3 -B - "$SCRIPT" <<'PY'
import importlib.util
import subprocess
import sys

spec = importlib.util.spec_from_file_location("credential_lifecycle", sys.argv[1])
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

assert module.last_report('{"verdict":"accepted"}\n') == {"verdict": "accepted"}
assert module.last_report("not-json") is None

original = module.subprocess.run
try:
    module.subprocess.run = lambda *_args, **_kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired(["bash"], 180))
    assert module.child("synthetic") is None
finally:
    module.subprocess.run = original

# A recovery continuation must prove the denied state first and must not call
# the revocation administration operation again.
calls = []
module.healthy = lambda mode: calls.append(("health", mode)) or mode == "health-unready"
module.administer = lambda operation: calls.append(("administer", operation)) or True
module.replace = lambda *_args: calls.append(("replace",)) or True
assert module.healthy("health-unready")
assert not any(call == ("administer", "revoke-runtime") for call in calls)

# The continuation's first precondition is denied readiness, not healthy
# readiness: requiring the latter would prevent recovery from ever starting.
source = open(sys.argv[1], encoding="utf-8").read()
assert 'args.operation == "recover-after-revocation"' in source
assert 'revoke-await-observability' in source
assert 'unready_verifier_receipt' in source
assert 'put-secret-value' not in source
assert 'get-random-password' not in source
assert 'rotate-runtime' not in source
assert 'password' not in source.lower()
print("runtime IAM identity lifecycle controller checks passed")
PY
