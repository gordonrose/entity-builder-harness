#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-core-server-persistence-observability-mvp
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the observability MVP gate rejects unsafe schedules, unbounded event fields, missing application metrics, and indistinct alarm silence policy.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/script.sh"
SOURCE="$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

pass() { bash "$SCRIPT" --target-root "$1" --json | grep -q '"verdict": "valid"'; }
fail() { local expected="$1" root="$2"; local output; if output="$(bash "$SCRIPT" --target-root "$root" --json 2>&1)"; then echo "expected failure $expected" >&2; exit 1; fi; [[ "$output" == *"$expected"* ]] || { echo "$output" >&2; exit 1; }; }
fixture() { local root="$TEMPORARY_DIRECTORY/$1"; cp -R "$SOURCE" "$root"; printf '%s' "$root"; }

pass "$SOURCE"

bad_schedule="$(fixture bad-schedule)"
python3 - "$bad_schedule/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys, yaml
p=Path(sys.argv[1]); d=yaml.safe_load(p.read_text()); d["observability_mvp"]["readiness_observation"]["timeout_seconds"]=30; p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
fail observability-readiness-observation-invalid "$bad_schedule"

open_envelope="$(fixture open-envelope)"
python3 - "$open_envelope/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys, yaml
p=Path(sys.argv[1]); d=yaml.safe_load(p.read_text()); d["observability_mvp"]["event_envelope"]["closed_fields"].append("provider_message"); p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
fail observability-event-envelope-invalid "$open_envelope"

wrong_metric="$(fixture wrong-metric)"
python3 - "$wrong_metric/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys, yaml
p=Path(sys.argv[1]); d=yaml.safe_load(p.read_text()); d["observability_mvp"]["metric_catalogue"]["application"][0]["source"]="ecs-running-task-count"; p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
fail observability-application-metric-invalid "$wrong_metric"

missing_data="$(fixture missing-data)"
python3 - "$missing_data/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys, yaml
p=Path(sys.argv[1]); d=yaml.safe_load(p.read_text()); d["observability_mvp"]["alarms"]["definitions"][0]["treat_missing_data"]="not-breaching"; p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
fail observability-alarm-policy-invalid "$missing_data"

unsafe_notification="$(fixture unsafe-notification)"
python3 - "$unsafe_notification/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys, yaml
p=Path(sys.argv[1]); d=yaml.safe_load(p.read_text()); d["observability_mvp"]["alarms"]["email"]="not-allowed@example.invalid"; p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
fail observability-notification-recipient-prohibited "$unsafe_notification"

bad_provider="$(fixture bad-provider)"
python3 - "$bad_provider/30-provider-realization/aws/cloudformation/core-server-persistence.yml" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); text=p.read_text(); p.write_text(text.replace("TreatMissingData: breaching", "TreatMissingData: notBreaching", 1))
PY
fail observability-provider-realization-invalid "$bad_provider"

echo "Core-server persistence observability MVP declaration tests passed."

