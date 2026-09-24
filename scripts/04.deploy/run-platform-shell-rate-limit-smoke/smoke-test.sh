#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-rate-limit-smoke.smoke-test
#   version: 2
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate the bounded staging rate-limit proof source without contacting the public target.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-rate-limit-smoke-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

output="$(npm run platform:shell:rate-limit-smoke -- --validate)"
if [[ "$output" != *'"rate_limit_smoke":"validated"'* ]] || [[ "$output" != *'"max_request_count":121'* ]]; then
  echo "ERROR: rate-limit smoke validation must expose only the bounded validated result." >&2
  exit 1
fi

if npm run platform:shell:rate-limit-smoke -- --validate --execute >/dev/null 2>&1; then
  echo "ERROR: rate-limit smoke must require exactly one execution mode." >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 python3 - "$ROOT/scripts/04.deploy/run-platform-shell-rate-limit-smoke/script.py" <<'PY'
import contextlib
import importlib.util
import io
import json
import sys

spec = importlib.util.spec_from_file_location("rate_limit_smoke", sys.argv[1])
if spec is None or spec.loader is None:
    raise SystemExit("ERROR: cannot load rate-limit smoke module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Clock:
    def __init__(self) -> None:
        self.now_seconds = 60.750
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now_seconds

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now_seconds += seconds


clock = Clock()
module.time.time = clock.time
module.time.sleep = clock.sleep
if module.wait_for_next_fixed_window(60_000) != 120_000 or clock.sleeps != [59.25]:
    raise SystemExit("ERROR: rate-limit smoke must wait for a fresh fixed window")

clock = Clock()
module.time.time = clock.time
module.time.sleep = clock.sleep
request_count = 0


def request_then_cross_window(hostname: str, timeout_seconds: int) -> tuple[int, int]:
    del hostname, timeout_seconds
    global request_count
    request_count += 1
    clock.now_seconds = 180.001
    return 200, 1


module.request_liveness = request_then_cross_window
output = io.StringIO()
with contextlib.redirect_stdout(output):
    outcome = module.execute({"window_ms": 60_000, "max_requests": 3, "hostname": "staging.platform.kanbien.com"}, 1)
result = json.loads(output.getvalue())
if outcome != 1 or request_count != 1 or result.get("rate_limit_smoke") != "inconclusive-window-rolled-over":
    raise SystemExit("ERROR: rate-limit smoke must fail inconclusively when its fixed window rolls over")
PY

echo "Platform-shell rate-limit smoke local validation passed."
