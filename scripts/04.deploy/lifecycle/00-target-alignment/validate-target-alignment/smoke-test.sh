#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.target-alignment-validation
#   version: 1
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove target-alignment validation accepts full matching evidence and fails closed for any missing assertion.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.command.target-alignment-validation
#     path: scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.sh
ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.sh"
FIXTURES="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/fixtures"
"$SCRIPT" --contract "$FIXTURES/contract.yml" --evidence "$FIXTURES/aligned.json" --json | grep -q '"verdict": "aligned"'
bad="$(mktemp)"; trap 'rm -f "$bad"' EXIT
python3 - "$FIXTURES/aligned.json" "$bad" <<'PY'
import json, sys
x=json.load(open(sys.argv[1])); x['assertions'][0]['outcome']='missing'; json.dump(x,open(sys.argv[2],'w'))
PY
if "$SCRIPT" --contract "$FIXTURES/contract.yml" --evidence "$bad" --json >/dev/null; then echo 'expected failure' >&2; exit 1; fi
python3 -B - "$ROOT" <<'PY'
import copy, json, subprocess, sys, tempfile, yaml
from pathlib import Path
root=Path(sys.argv[1]); command=root/'scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.py'
fixtures=command.parent/'fixtures'; contract=yaml.safe_load((fixtures/'contract.yml').read_text()); evidence=json.loads((fixtures/'aligned.json').read_text())
canary='https://private.invalid/secret-canary'
with tempfile.TemporaryDirectory() as directory:
    c=Path(directory)/'contract'; e=Path(directory)/'evidence'
    def run(document, facts, extra=()):
        c.write_text(yaml.safe_dump(document)); e.write_text(json.dumps(facts))
        result=subprocess.run([sys.executable,'-B',str(command),'--contract',str(c),'--evidence',str(e),*extra],capture_output=True,text=True)
        assert canary not in result.stdout+result.stderr
        assert 'Traceback' not in result.stdout+result.stderr
        return result, json.loads(result.stdout)
    for facts in [None, [], {'schema':'deploy/target-alignment-evidence/v1','assertions':[{'id':[]}]}]:
        result, report=run(contract,facts); assert result.returncode==1 and report['verdict']=='blocked'
    bad=copy.deepcopy(contract); bad['assertions'][0]['id']={}
    result, report=run(bad,evidence); assert report['findings'][0]['code']=='target-alignment-contract-invalid'
    result, report=run(contract,evidence,['--'+canary]); assert result.returncode==1 and report['findings'][0]['code']=='arguments-invalid'
    bad=copy.deepcopy(evidence); bad['assertions'][0].update(outcome=canary,finding_code={'secret':canary})
    unsafe=copy.deepcopy(contract); unsafe['target']=canary
    result, report=run(unsafe,bad); assert report['target'] is None and report['assertions'][0]['outcome'] is None and report['assertions'][0]['finding_code'] is None
    duplicate=copy.deepcopy(evidence); duplicate['assertions'].insert(0,{**duplicate['assertions'][0],'outcome':'missing'})
    result, report=run(contract,duplicate); assert result.returncode==0  # last value still wins
    e.write_bytes(b'\xff'); result=subprocess.run([sys.executable,'-B',str(command),'--contract',str(c),'--evidence',str(e)],capture_output=True,text=True)
    assert result.returncode==1 and json.loads(result.stdout)['findings'][0]['code']=='target-alignment-evidence-unreadable'
print('Target alignment validation tests passed.')
PY
