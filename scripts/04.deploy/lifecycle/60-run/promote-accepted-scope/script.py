#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.promote-accepted-scope
#   version: 1
#   status: active
#   created_on: '2026-10-25'
#   updated_on: '2026-10-25'
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Validate acceptance before updating reciprocal local scope ownership; never
#     mutate a provider.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   - writes-files
#   argument_validation:
#     flag: --validate-arguments
#     effects:
#     - read-only
#   used_by:
#   - id: deploy.command.promote-accepted-scope
#     path: scripts/04.deploy/lifecycle/60-run/promote-accepted-scope/script.sh
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import yaml
ROOT=Path(__file__).resolve().parents[5]

def route_module():
    path=ROOT/'scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py'
    spec=importlib.util.spec_from_file_location('promotion_route',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def contained(path:Path,root:Path):
    if not path.resolve().is_relative_to(root.resolve()) or any(item.is_symlink() for item in (path,*path.parents) if item!=root.parent):
        raise ValueError('scope-promotion-path-outside-root')


def inventory_module():
    path=ROOT/'scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.py'
    spec=importlib.util.spec_from_file_location('promotion_inventory',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def promote(contract_path:Path,root:Path,write=False,simulation=False):
    root=root.resolve();contract_path=contract_path.absolute();contained(contract_path,root)
    if simulation and not root.is_relative_to(Path(tempfile.gettempdir()).resolve()):raise ValueError('scope-promotion-simulation-root-invalid')
    route_api=route_module();contract=route_api.document(contract_path);route,_=route_api.load_route(contract_path,root)
    if not route or route.get('target')!=contract.get('target') or route.get('scope')!=contract.get('scope'):raise ValueError('scope-promotion-route-invalid')
    record_contract=route.get('accepted_record');commands=route.get('commands')
    if not isinstance(record_contract,dict) or not isinstance(commands,dict):raise ValueError('scope-promotion-route-invalid')
    record_path=route_api.reference(contract_path.parent.parent,record_contract.get('path'))
    index_path=contract_path.parents[2]/'scope-index.yml'
    if record_path is None:raise ValueError('scope-promotion-record-path-invalid')
    contained(record_path,root);contained(index_path,root)
    record=route_api.document(record_path)
    if any(record.get(key)!=value for key,value in [('target',contract.get('target')),('scope',contract.get('scope')),('schema',record_contract.get('schema'))]):raise ValueError('scope-promotion-record-subject-invalid')
    if record.get('evidence_class','live')!=('simulated' if simulation else 'live') or record.get('status')!=('rehearsed' if simulation else 'accepted'):raise ValueError('scope-promotion-evidence-not-accepted')
    validator=record_contract.get('validator');command=commands.get(validator) if isinstance(validator,str) else None
    if not isinstance(command,dict):raise ValueError('scope-promotion-validator-invalid')
    argv=route_api.resolve(command.get('argv'),{'accepted_record':str(record_path),'scope_contract':str(contract_path),'target_root':str(contract_path.parents[2])})
    if argv is None or argv[0]!='bash':raise ValueError('scope-promotion-validator-invalid')
    script=route_api.reference(ROOT,argv[1]);metadata=route_api.command_metadata(script) if script else {}
    if metadata.get('id')!=command.get('owner') or command.get('effects')!=['read-only'] or metadata.get('effects')!=['read-only']:raise ValueError('scope-promotion-validator-owner-or-effects-invalid')
    route_report=route_api.inspect(contract_path,root,ROOT)
    if route_report.get('verdict')!='covered':raise ValueError('scope-promotion-route-invalid')
    argv[1]=str(script);argv+=['--rehearsal-root' if simulation else '--root',str(root)]
    try:
        checked=subprocess.run(argv,capture_output=True,text=True,check=False,timeout=30)
        report=json.loads(checked.stdout)
    except (subprocess.TimeoutExpired,json.JSONDecodeError):raise ValueError('scope-promotion-validation-failed') from None
    if checked.returncode or not isinstance(report,dict) or report.get('verdict')!='validated':raise ValueError('scope-promotion-validation-failed')
    index=route_api.document(index_path);entries=index.get('scopes');scope=contract.get('scope')
    if not isinstance(entries,list):raise ValueError('scope-promotion-inventory-invalid')
    inventory=inventory_module()
    if inventory.inspect(index_path.parent,root if simulation else None,index).get('verdict')!='passed':raise ValueError('scope-promotion-inventory-invalid')
    selected=next((item for item in entries if isinstance(item,dict) and item.get('id')==scope),None)
    if not isinstance(selected,dict):raise ValueError('scope-promotion-scope-missing')
    if selected.get('lifecycle')=='active':return {'verdict':'already-active','evidence_class':'simulated' if simulation else 'live'}
    predecessor=next((item for item in entries if isinstance(item,dict) and item.get('id')==selected.get('predecessor')),None)
    if selected.get('lifecycle')!='candidate' or not isinstance(predecessor,dict) or predecessor.get('lifecycle')!='active':raise ValueError('scope-promotion-transition-invalid')
    selected['lifecycle']='active';predecessor['lifecycle']='accepted-historical';predecessor['successor']=scope
    if inventory.inspect(index_path.parent,root if simulation else None,index).get('verdict')!='passed':raise ValueError('scope-promotion-proposed-inventory-invalid')
    if write:
        text=index_path.read_text();header=''.join(line+'\n' for line in text.splitlines() if line.startswith('#'))
        with tempfile.NamedTemporaryFile(mode='w',dir=index_path.parent,delete=False,prefix='.scope-promotion-',suffix='.tmp') as handle:
            pending=Path(handle.name);handle.write(header+yaml.safe_dump(index,sort_keys=False));handle.flush();os.fsync(handle.fileno())
        os.replace(pending,index_path)
    return {'verdict':'promoted' if write else 'ready','evidence_class':'simulated' if simulation else 'live'}

def main():
    parser=argparse.ArgumentParser(add_help=False,exit_on_error=False);parser.add_argument('--scope-contract',type=Path);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--rehearsal-root',type=Path);parser.add_argument('--write',action='store_true');parser.add_argument('--json',action='store_true');parser.add_argument('--validate-arguments',action='store_true')
    try:
        args,unknown=parser.parse_known_args()
        if unknown or args.scope_contract is None:raise ValueError('scope-promotion-arguments-invalid')
        if args.validate_arguments:
            print(json.dumps({'schema':'deploy/command-arguments-report/v1','verdict':'valid','findings':[]}));return 0
        result=promote(args.scope_contract,args.rehearsal_root or args.root,args.write,bool(args.rehearsal_root));result.update(schema='deploy/scope-promotion-report/v1',findings=[])
    except (ValueError,TypeError,KeyError,AttributeError,OSError,argparse.ArgumentError) as error:result={'schema':'deploy/scope-promotion-report/v1','verdict':'blocked','findings':[{'code':str(error) if isinstance(error,ValueError) else 'scope-promotion-input-invalid'}]}
    print(json.dumps(result,sort_keys=True));return int(result['verdict']=='blocked')
if __name__=='__main__':raise SystemExit(main())
