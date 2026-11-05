#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-delivery-access-contract
#   version: 3
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.delivery-access
#   disciplines:
#   - security
#   kind: script
#   purpose: Prove generic delivery access validation rejects missing provider access and undeclared workflow steps without selecting a target or provider.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   - writes-files
#   used_by:
#   - id: deploy.command.validate-delivery-access-contract.wrapper
#     path: scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.sh

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.sh"
CONTRACT="$ROOT/scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/fixtures/valid-contract.yml"
WORKFLOW="$ROOT/scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/fixtures/sample-workflow.yml"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

coverage="$TEMPORARY_DIRECTORY/coverage.json"
python3 - "$CONTRACT" "$coverage" <<'PY'
from pathlib import Path
import json, sys, yaml

root = Path.cwd()
contract_path = Path(sys.argv[1])
contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
Path(sys.argv[2]).write_text(json.dumps({
    "schema": "deploy/provider-policy-coverage/v1",
    "contract": str(contract_path.relative_to(root)),
    "provider_policy_source": contract["provider_policy_source"],
    "granted_actions": [operation["provider_action"] for operation in contract["operations"]],
    "verdict": "covered",
}), encoding="utf-8")
PY
bash "$SCRIPT" --contract "$CONTRACT" --workflow "$WORKFLOW" --provider-policy-coverage "$coverage" --json >/dev/null

python3 - "$coverage" "$TEMPORARY_DIRECTORY/missing-action-coverage.json" <<'PY'
from pathlib import Path
import json, sys
document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
document["granted_actions"].pop()
Path(sys.argv[2]).write_text(json.dumps(document), encoding="utf-8")
PY
if output="$(bash "$SCRIPT" --contract "$CONTRACT" --workflow "$WORKFLOW" --provider-policy-coverage "$TEMPORARY_DIRECTORY/missing-action-coverage.json" --json 2>&1)"; then
  echo 'ERROR: validator accepted a missing provider action.' >&2
  exit 1
fi
[[ "$output" == *'delivery-action-provider-policy-missing'* ]]

python3 - "$CONTRACT" "$coverage" "$TEMPORARY_DIRECTORY/missing-step.yml" "$TEMPORARY_DIRECTORY/missing-step-coverage.json" <<'PY'
from pathlib import Path
import json, sys, yaml
document = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
document["operations"][0]["workflow_step"] = "Undeclared step"
Path(sys.argv[3]).write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
coverage = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
coverage["contract"] = None
Path(sys.argv[4]).write_text(json.dumps(coverage), encoding="utf-8")
PY
if output="$(bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/missing-step.yml" --workflow "$WORKFLOW" --provider-policy-coverage "$TEMPORARY_DIRECTORY/missing-step-coverage.json" --json 2>&1)"; then
  echo 'ERROR: validator accepted an undeclared workflow step.' >&2
  exit 1
fi
[[ "$output" == *'delivery-access-workflow-step-missing'* ]]
python3 - "$ROOT" "$TEMPORARY_DIRECTORY" "$CONTRACT" "$WORKFLOW" "$coverage" <<'PY'
import json,os,subprocess,sys
from pathlib import Path
repo,temp,contract,workflow,coverage=map(Path,sys.argv[1:])
command=repo/'scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.py'
bad=temp/'credential-canary-value';bad.write_bytes(b'\xffcredential-canary-value')
args=['python3','-B',str(command),'--contract',str(contract),'--workflow',str(bad),'--provider-policy-coverage',str(coverage),'--json']
result=subprocess.run(args,capture_output=True,text=True)
assert result.returncode==1 and 'delivery-workflow-unreadable' in result.stdout,(result.stdout,result.stderr)
assert 'credential-canary-value' not in result.stdout+result.stderr and 'Traceback' not in result.stderr
result=subprocess.run(['python3','-B',str(command),'--contract'],capture_output=True,text=True)
assert result.returncode==2 and json.loads(result.stderr)['findings']==[{'code':'delivery-access-arguments-invalid'}]
adapter=repo/'scripts/04.deploy/lifecycle/40-package/provider-adapters/aws/iam-policy-coverage/script.py'
result=subprocess.run(['python3','-B',str(adapter),'--contract',str(contract),'--template',str(bad),'--role-logical-id','DeliveryRole','--provider-policy-source','fixture-policy','--output',str(temp)],capture_output=True,text=True)
assert result.returncode==1 and result.stderr=='DIAGNOSTIC_CODE=DELIVERY_POLICY_COVERAGE_OUTPUT_UNAVAILABLE\n',(result.stdout,result.stderr)
assert 'credential-canary-value' not in result.stdout+result.stderr
binary=temp/'bin';binary.mkdir()
(binary/'git').write_text('#!/bin/sh\nprintf "%s\\n" "$FIXTURE_ROOT"\n')
(binary/'python3').write_text('#!/bin/sh\nprintf "credential-canary-value\\n" >&2\nexit 23\n')
for child in binary.iterdir():child.chmod(0o755)
for owner in ('core-server','core-server-persistence'):
 wrapper=repo/'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform'/(owner+'-package-custody')/'validate-delivery-access/script.sh'
 result=subprocess.run(['/bin/bash',str(wrapper),'--json'],env={**os.environ,'PATH':str(binary)+os.pathsep+os.environ['PATH'],'FIXTURE_ROOT':str(repo)},capture_output=True,text=True)
 assert result.returncode==23 and 'DIAGNOSTIC_CODE=DELIVERY_POLICY_COVERAGE_FAILED' in result.stderr,(result.stdout,result.stderr)
 assert 'credential-canary-value' not in result.stdout+result.stderr and 'LIFECYCLE_STAGE=package' in result.stderr
PY
echo 'Delivery access contract smoke test passed.'
