#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.runnable-program-contract
#   version: 3
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - agentic
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove the runnable-program contract checker accepts safe declarations and rejects the required fail-closed fixtures.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   - writes-files
#   used_by:
#   - id: deploy.command.runnable-program-contract
#     path: scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
SCRIPT="scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh"
FIXTURES="scripts/04.deploy/lifecycle/20-build/runnable-program-contract/fixtures"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

expect_pass() {
  local output
  output="$(bash "$SCRIPT" --contract "$1" --json)"
  [[ "$output" == *'"verdict": "passed"'* ]]
}

expect_failure() {
  local expected_code="$1"
  local contract="$2"
  local output
  if output="$(bash "$SCRIPT" --contract "$contract" --json 2>&1)"; then
    echo "ERROR: expected contract failure: $expected_code" >&2
    exit 1
  fi
  if [[ "$output" != *"\"code\": \"$expected_code\""* ]]; then
    echo "ERROR: expected safe code $expected_code" >&2
    exit 1
  fi
  if [[ "$output" == *"not-approved"* || "$output" == *"unsafe-field"* ]]; then
    echo "ERROR: checker exposed fixture input in its diagnostic" >&2
    exit 1
  fi
}

python3 - <<'PY'
from pathlib import Path
import yaml

for path in (
    ".agentic/04.deploy/20-build/schemas/runnable-program-contract.v1.schema.yml",
    ".agentic/04.deploy/20-build/schemas/runnable-program-contract.v1.template.yml",
    "scripts/04.deploy/lifecycle/20-build/runnable-program-contract/fixtures/valid-contract.yml",
):
    if not isinstance(yaml.safe_load(Path(path).read_text(encoding="utf-8")), dict):
        raise SystemExit(f"ERROR: expected YAML mapping: {path}")
source = Path("scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py").read_text(encoding="utf-8")
compile(source, "runnable-program-contract.py", "exec")
for forbidden in ("socket", "urllib", "requests"):
    if forbidden in source:
        raise SystemExit(f"ERROR: report-only checker must not contain {forbidden}")
PY

node --test scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs-test.mjs
python3 -B scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-validation-test.py

expect_pass "$FIXTURES/valid-contract.yml"

python3 - "$FIXTURES/valid-contract.yml" "$TEMPORARY_DIRECTORY/missing-program.yml" <<'PY'
from pathlib import Path
import sys
import yaml

document = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
document["image_contracts"][0]["program"] = "missing-program"
Path(sys.argv[2]).write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
PY
expect_failure "program-record-missing" "$TEMPORARY_DIRECTORY/missing-program.yml"

python3 - "$FIXTURES/valid-contract.yml" "$TEMPORARY_DIRECTORY/invalid-command.yml" <<'PY'
from pathlib import Path
import sys
import yaml

document = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
document["image_contracts"][0]["command"] = ["node", "artifacts/generic-server.main.js; unexpected"]
Path(sys.argv[2]).write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
PY
expect_failure "image-command-invalid" "$TEMPORARY_DIRECTORY/invalid-command.yml"

python3 - "$FIXTURES/valid-contract.yml" "$TEMPORARY_DIRECTORY/unapproved-dependency.yml" <<'PY'
from pathlib import Path
import sys
import yaml

document = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
document["runnable_programs"][0]["observed_dependencies"].append("not-approved")
Path(sys.argv[2]).write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
PY
expect_failure "dependency-unapproved" "$TEMPORARY_DIRECTORY/unapproved-dependency.yml"

python3 - "$FIXTURES/valid-contract.yml" "$TEMPORARY_DIRECTORY/unsafe-evidence.yml" <<'PY'
from pathlib import Path
import sys
import yaml

document = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
document["candidate_verification"]["required_evidence_fields"].append("unsafe-field")
Path(sys.argv[2]).write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
PY
expect_failure "evidence-field-unsafe" "$TEMPORARY_DIRECTORY/unsafe-evidence.yml"

echo "Runnable-program contract local tests passed."

python3 - "$FIXTURES/valid-contract.yml" "$TEMPORARY_DIRECTORY" <<'PYTHON'
from pathlib import Path
import copy, json, subprocess, sys, yaml
original=yaml.safe_load(Path(sys.argv[1]).read_text())
entry=original['runnable_programs'][0]['entrypoint']
handler=copy.deepcopy(original)
handler['runnable_programs'][0].update(execution_kind='managed-handler', handler_export='handler')
handler['image_contracts'][0].update(command_mode='handler', command=[entry.rsplit('.',1)[0]+'.handler'])
def handler_case(document, expected):
    path=Path(sys.argv[2])/'managed-handler.yml'; path.write_text(yaml.safe_dump(document))
    result=subprocess.run([sys.executable,'-B','scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py','--contract',str(path),'--json'],capture_output=True,text=True)
    report=json.loads(result.stdout)
    assert (result.returncode,report['findings']) == ((0,[]) if expected is None else (1,[{'code':expected}]))
handler_case(handler,None)
for field,value in [('handler_export','a.b'),('entrypoint','artifacts/../private.js'),('runtime_executable','python3')]:
    rejected=copy.deepcopy(handler); rejected['runnable_programs'][0][field]=value
    handler_case(rejected,'program-handler-invalid')
for command in [['node',entry],['unexpected.handler'],[entry.rsplit('.',1)[0]+'.handler','extra']]:
    rejected=copy.deepcopy(handler); rejected['image_contracts'][0]['command']=command
    handler_case(rejected,'image-command-invalid')
rejected=copy.deepcopy(original); rejected['image_contracts'][0]['command_mode']='handler'
handler_case(rejected,'image-command-invalid')
rejected=copy.deepcopy(original); rejected['runnable_programs'][0]['handler_export']='handler'
handler_case(rejected,'program-handler-invalid')
rejected=copy.deepcopy(handler); rejected['runnable_programs'][0]['execution_kind']='shell'
handler_case(rejected,'program-execution-kind-invalid')
for command in [['echo',entry],['sh',entry],['node','--eval','0',entry]]:
    document=copy.deepcopy(original);document['image_contracts'][0]['command']=command
    path=Path(sys.argv[2])/'runtime-mismatch.yml';path.write_text(yaml.safe_dump(document))
    result=subprocess.run(['python3','-B','scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py','--contract',str(path),'--json'],capture_output=True,text=True)
    assert result.returncode==1 and 'image-command-invalid' in result.stdout
for owner,field,code in [('runnable_programs','runtime_executable','program-runtime-unsupported'),('package_candidates','image_contract','image-contract-missing')]:
    for value in [[],{}]:
        document=copy.deepcopy(original); document[owner][0][field]=value
        path=Path(sys.argv[2])/'shape.yml'; path.write_text(yaml.safe_dump(document))
        result=subprocess.run([sys.executable,'-B','scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py','--contract',str(path)],capture_output=True,text=True)
        assert result.returncode==1 and json.loads(result.stdout)['findings']==[{'code':code}]
for value in [[],{}]:
    document=copy.deepcopy(original); document['candidate_verification']['candidate']=value
    path.write_text(yaml.safe_dump(document)); result=subprocess.run([sys.executable,'-B','scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py','--contract',str(path)],capture_output=True,text=True)
    assert result.returncode==1 and json.loads(result.stdout)['findings']==[{'code':'candidate-verification-invalid'}]
path.write_bytes(b'\xff'); result=subprocess.run([sys.executable,'-B','scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py','--contract',str(path)],capture_output=True,text=True)
assert json.loads(result.stdout)['findings']==[{'code':'contract-unreadable'}]
PYTHON
