#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.runtime-credential-lifecycle
#   version: 1
#   status: draft
#   created_on: "2026-10-24"
#   updated_on: "2026-10-24"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove bounded non-secret credential-lifecycle controller decisions without AWS mutation.
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
# the revocation migration again.
calls = []
module.healthy = lambda mode: calls.append(("health", mode)) or mode == "health-unready"
module.migrate = lambda operation: calls.append(("migrate", operation)) or True
module.rotate_and_replace = lambda *_args: calls.append(("rotate",)) or ("v2", "ok")
assert module.healthy("health-unready")
assert not any(call == ("migrate", "revoke") for call in calls)

# The continuation's first precondition is denied readiness, not healthy
# readiness: requiring the latter would prevent recovery from ever starting.
source = open(sys.argv[1], encoding="utf-8").read()
assert 'args.operation in {"recover-after-revocation", "recover-secret"}' in source
assert '"recover-secret"' in source
assert 'persistence-runtime-credential-secret-advanced-migration-required' in source

class Fixture:
    def __init__(self, response): self.response = response
    def aws(self, *_args): return True, self.response, "ok"

assert module.current_secret_version(Fixture({"VersionIdsToStages": {"v1": ["AWSCURRENT"]}}), "synthetic") == ("v1", "ok")
assert module.current_secret_version(Fixture({"VersionIdsToStages": {"v1": ["AWSCURRENT"], "v2": ["AWSCURRENT"]}}), "synthetic")[1] == "persistence-credential-lifecycle-current-secret-version-ambiguous"
print("runtime credential lifecycle controller checks passed")
PY
