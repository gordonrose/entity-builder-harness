#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-core-server-persistence-observability-mvp
#   version: 2
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the observability MVP gate rejects unsafe schedules, unbounded event fields, missing application metrics, and indistinct alarm silence policy.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.validate-core-server-persistence-observability-mvp
#     path: scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/script.sh
#   effects: [read-only, writes-files]
ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/script.sh"
SOURCE="$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

pass() { bash "$SCRIPT" --target-root "$1" --json | grep -q '"verdict": "valid"'; }
fail() { local expected="$1" root="$2"; local output; if output="$(bash "$SCRIPT" --target-root "$root" --json 2>&1)"; then echo "expected failure $expected" >&2; exit 1; fi; [[ "$output" == *"$expected"* ]] || { echo "$output" >&2; exit 1; }; }
fixture() {
  local fixture_root="$TEMPORARY_DIRECTORY/$1"
  local root="$fixture_root/targets/kanbien-core-platform"
  mkdir -p "$(dirname "$root")"
  cp -R "$SOURCE" "$root"
  # The target validator resolves the collector package contract from the
  # provider-realisation parent.  Preserve that relationship in every fixture
  # so a mutation is rejected for its own reason rather than a missing
  # neighbouring contract.
  cp -R "$ROOT/infra/04.deploy/03.product/image" "$fixture_root/image"
  printf '%s' "$root"
}

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

malformed_codes="$(fixture malformed-codes)"
python3 - "$malformed_codes/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys, yaml
p=Path(sys.argv[1]); d=yaml.safe_load(p.read_text()); d['observability_mvp']['readiness_observation']['not_ready_codes']=[{}]; p.write_text(yaml.safe_dump(d,sort_keys=False))
PY
fail observability-readiness-code-policy-invalid "$malformed_codes"
unreadable_template="$(fixture unreadable-template)"
printf '\377' > "$unreadable_template/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
fail observability-provider-realization-unreadable "$unreadable_template"

# Exercise the real validator against altered source without replacing its
# existing raw security checks or introducing a second template interpreter.
python3 - "$ROOT" "$SOURCE" "$TEMPORARY_DIRECTORY" <<'PY'
import contextlib, importlib.machinery, importlib.util, io, json, runpy, shutil, sys
from pathlib import Path
from unittest.mock import patch
root, source, temporary = map(Path, sys.argv[1:])
path = root / 'scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/script.py'
spec = importlib.util.spec_from_file_location('observability_fixture', path)
owner = importlib.util.module_from_spec(spec); spec.loader.exec_module(owner)
destination = temporary / 'identity' / 'targets' / source.name
shutil.copytree(source, destination)
shutil.copytree(root / 'infra/04.deploy/03.product/image', destination.parent.parent / 'image')
template_path = destination / '30-provider-realization/aws/cloudformation/core-server-persistence.yml'
original = template_path.read_text()
changes = [
    ('    Default: kanbien-core-platform', '    Default: different-target'),
    ('    Default: kanbien-core-platform', '    Default: private-canary\n    Default: kanbien-core-platform'),
    ('    MaxLength: 21', '    MaxLength: 1'),
    ('http://observability-collector.${ResourceNamePrefix}.internal:4318/v1/metrics', 'http://private-canary.invalid'),
    ('Name: PLATFORM_OBSERVABILITY_TARGET, Value: !Ref ResourceNamePrefix', 'Name: PLATFORM_OBSERVABILITY_TARGET, Value: private-canary'),
    ('Name: PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT, Value: !Ref ResourceNamePrefix', 'Name: PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT, Value: private-canary'),
    ('Name: target, Value: !Ref ResourceNamePrefix', 'Name: target, Value: private-canary'),
]
for old, new in changes:
    assert old in original, old
    template_path.write_text(original.replace(old, new, 1))
    try:
        owner.check(destination)
    except owner.Failure as error:
        assert error.code == 'observability-provider-realization-invalid', error.code
    else:
        raise AssertionError('unsafe identity accepted')
template_path.write_text(original)
owner.check(destination)
execute = importlib.machinery.SourceFileLoader.exec_module
for kind in (FileNotFoundError, SyntaxError, ImportError, RuntimeError):
    def injected(loader, module):
        if loader.name == 'observability_cloudformation':
            raise kind('private-canary')
        return execute(loader, module)
    output, errors = io.StringIO(), io.StringIO()
    with patch.object(importlib.machinery.SourceFileLoader, 'exec_module', injected), \
            patch.object(sys, 'argv', [str(path), '--target-root', str(destination), '--json']), \
            contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        try:
            runpy.run_path(str(path), run_name='__main__')
        except SystemExit as exit:
            assert exit.code == 1, exit.code
        else:
            raise AssertionError('missing CLI exit')
    report = json.loads(output.getvalue())
    assert report == {'schema': 'deploy/observability-mvp-declaration-report/v1',
                      'target': 'kanbien-core-platform', 'scope': 'core-server-persistence',
                      'verdict': 'invalid', 'findings': [{'code': 'observability-provider-realization-unreadable'}]}
    assert errors.getvalue() == '' and 'private-canary' not in output.getvalue()
print('Identity projection and safe import failures passed.')
PY
echo "Core-server persistence observability MVP declaration tests passed."

