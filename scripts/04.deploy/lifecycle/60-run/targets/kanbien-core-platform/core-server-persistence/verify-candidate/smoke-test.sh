#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.private-persistence-verifier-isolation
#   version: 1
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-24"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove private persistence verifier isolation uses the real lower-case ECS response fields.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.verify-core-server-persistence-candidate
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh
#   effects: [read-only]

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py"

python3 -B - "$SCRIPT" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("verify_candidate", sys.argv[1])
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

class Fixture:
    def __init__(self, container): self.container = container
    def aws(self, *_args): return True, {"taskDefinition": {"containerDefinitions": [self.container]}}, "ok"

safe = {"environment": [{"name": "PERSISTENCE_VERIFIER_MODE", "value": "create"}], "secrets": []}
unsafe_host = {"environment": [{"name": "PERSISTENCE_POSTGRES_HOST", "value": "db.example.invalid"}], "secrets": []}
unsafe_secret = {"environment": [], "secrets": [{"name": "PERSISTENCE_RUNTIME_CREDENTIALS", "valueFrom": "synthetic"}]}
# Exercise the provider-response predicate by temporarily supplying the fixture.
original = module.aws
try:
    module.aws = Fixture(safe).aws
    assert module.no_direct_database_credential("synthetic")
    module.aws = Fixture(unsafe_host).aws
    assert not module.no_direct_database_credential("synthetic")
    module.aws = Fixture(unsafe_secret).aws
    assert not module.no_direct_database_credential("synthetic")
finally:
    module.aws = original
print("private persistence verifier isolation checks passed")
PY
