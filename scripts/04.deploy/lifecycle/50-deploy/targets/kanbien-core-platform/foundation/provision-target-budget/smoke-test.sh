#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.provision-target-budget
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.foundation-cost-control
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the target-budget bootstrap route fails closed before AWS when alert configuration is absent and preserves CloudFormation's typed parameter semantics.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.provision-target-budget
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py
#   effects: [read-only, writes-files]
ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py"

if output="$(env -u KANBIEN_CORE_PLATFORM_COST_ALERT_EMAIL python3 "$SCRIPT" --mode create --json 2>&1)"; then
  echo "ERROR: expected absent cost-alert configuration to block before AWS" >&2
  exit 1
fi
[[ "$output" == *'"code": "cost-alert-email-required"'* ]]

python3 - "$SCRIPT" <<'PY'
import ast
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
ast.parse(source)
assert '"UsePreviousValue": True' in source
assert 'expect_json: bool = True' in source
assert 'not expect_json and not completed.stdout.strip()' in source
PY

echo "Target-budget provisioning smoke test passed."

python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/aws/recovery-test.py" RecoveryCli.test_budget_lost_response_resumes_exact_operation RecoveryCli.test_cli_retry_decoration_preserves_typed_errors_not_retry_authority

python3 -B - "$SCRIPT" <<'PY'
import contextlib, importlib.util, io, json, subprocess, sys
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('budget_boundaries',sys.argv[1]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module._AWS_RESPONSE=SimpleNamespace(inventory_covered=lambda _root:True)
for error,code in [(OSError('private-native-canary'),'aws-command-unavailable'),(UnicodeDecodeError('utf8',b'\xff',0,1,'private-native-canary'),'aws-response-invalid'),(subprocess.TimeoutExpired(['private-native-canary'],1),'aws-command-timeout')]:
    with patch.object(module.subprocess,'run',side_effect=error) as call:
        assert module.aws('cloudformation','execute-change-set')==(False,None,code)
        assert call.call_count==1
with patch.object(module,'aws',return_value=(True,[], 'ok')):
    assert module.describe_change_set('retained-operation')==(None,'foundation-budget-change-set-observation-invalid')
with patch.object(module,'aws',return_value=(True,{'Stacks':[{'StackStatus':[]}]}, 'ok')):
    assert module.stack_parameters('not-retained')==([], 'foundation-stack-observation-invalid')
with patch.object(module,'aws',return_value=(True,{'Stacks':[{'StackStatus':'UPDATE_COMPLETE','Parameters':[{'ParameterKey':[],'ParameterValue':'private-canary'}]}]}, 'ok')):
    assert module.stack_parameters('not-retained')==([], 'foundation-stack-parameters-invalid')
# Nonthrowing historical alternatives remain governed by the original predicate.
with patch.object(module,'aws',return_value=(True,{'Stacks':[]}, 'ok')):
    assert module.stack_parameters('not-retained')==([], 'foundation-stack-not-stable')
result=subprocess.run([sys.executable,'-B',sys.argv[1],'--mode','private-argument-canary\nsecond-line'],capture_output=True,text=True,timeout=10)
assert result.returncode==2 and result.stdout==''
assert result.stderr=='ERROR: foundation-budget-arguments-invalid\n'
for field,value,code in [('Status',[],'foundation-budget-review-status-unobservable'),('ExecutionStatus',{},'foundation-budget-execution-status-unobservable')]:
    out=io.StringIO()
    with patch.object(module,'describe_change_set',return_value=({'ChangeSetName':'retained-operation','Status':'CREATE_COMPLETE','ExecutionStatus':'EXECUTE_COMPLETE',field:value},None)),contextlib.redirect_stdout(out):
        assert module.reconcile('retained-operation')==1
    report=json.loads(out.getvalue());assert report['verdict']=='uncertain' and report['findings']==[{'code':code}],report
class CleanupFailure(io.StringIO):
    name='fixture-only.json'
    def __exit__(self,*args):super().__exit__(*args);raise OSError('private-native-canary')
for cleanup in (False,True):
    out=io.StringIO()
    temporary=patch.object(module.tempfile,'NamedTemporaryFile',return_value=CleanupFailure()) if cleanup else patch.object(module.tempfile,'NamedTemporaryFile',side_effect=OSError('private-native-canary'))
    with temporary,patch.object(module,'cost_alert_email',return_value='not-printed'),patch.object(module,'require_active_tag',return_value=None),patch.object(module,'stack_parameters',return_value=([],None)),patch.object(module,'describe_change_set',return_value=(None,'aws-resource-missing')),patch.object(module,'aws',return_value=(True,{},'ok')) as provider,patch.object(sys,'argv',['fixture','--mode','create']),contextlib.redirect_stdout(out):
        assert module.main()==1
    report=json.loads(out.getvalue());assert report['verdict']==('uncertain' if cleanup else 'blocked'),report
    assert provider.call_count==(1 if cleanup else 0)
    assert report['findings']==[{'code':'foundation-budget-submission-or-parameter-cleanup-unavailable' if cleanup else 'foundation-budget-parameter-file-unavailable'}]
    assert 'private-native-canary' not in out.getvalue()
PY
