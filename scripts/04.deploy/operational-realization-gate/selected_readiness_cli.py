"""Strict public shim for the fixed passive selected-target inspector."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-readiness-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: script
#   purpose: Expose bounded passive selected-target observations without unsafe arguments or operation authority.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [network]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
CODES={'arguments-invalid','readiness-dependency-unavailable','readiness-source-invalid','readiness-result-invalid',
 'readiness-inspector-source-mismatch','readiness-target-mismatch','readiness-policy-invalid','readiness-source-groups-invalid',
 'readiness-source-changed','readiness-evidence-expired','readiness-inspection-timeout','readiness-inspection-blocked','readiness-inspection-unavailable'}
class CliFailure(Exception):pass
class Parser(argparse.ArgumentParser):
 def error(self,message):raise CliFailure('arguments-invalid')
def arguments(argv):
 flags=[v.split('=',1)[0] for v in argv if v.startswith('--')]
 if len(flags)!=len(set(flags)):raise CliFailure('arguments-invalid')
 parser=Parser(add_help=False,allow_abbrev=False)
 parser.add_argument('--selected-readiness',action='store_true',required=True)
 parser.add_argument('--inspect-target',action='store_true',required=True)
 for name in ('blueprint','source-root','source-revision','image-digest','release-id'):parser.add_argument('--'+name,required=True)
 parser.add_argument('--json',action='store_true')
 return parser.parse_args(argv)
def load_adapter():
 root=Path(__file__).resolve().parents[3];directory=root/'scripts/04.deploy/release-control'
 if str(directory) not in sys.path:sys.path.insert(0,str(directory))
 path=directory/'adapters/aws/selected_readiness.py'
 spec=importlib.util.spec_from_file_location('maintained_selected_readiness',path)
 if spec is None or spec.loader is None:raise CliFailure('readiness-dependency-unavailable')
 adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter);return adapter
def failure(code):
 return {'schema':'selected-readiness-error/v1','scope':'selected-target-passive-readiness','verdict':'blocked',
  'authorized':False,'release_eligibility':'blocked','operation_authorization':'blocked','qualification_verdict':'blocked',
  'findings':[{'code':code if type(code) is str and code in CODES else 'readiness-source-invalid'}]}
def main(argv=None):
 try:
  args=arguments(list(sys.argv[1:] if argv is None else argv))
  try:adapter=load_adapter()
  except Exception:raise CliFailure('readiness-dependency-unavailable') from None
  blueprint=adapter.release.load_document(args.blueprint)
  result=adapter.inspect(args.source_root,blueprint,args.source_revision,args.image_digest,args.release_id)
  try:adapter.validate_current_result(result,args.source_root,blueprint,args.source_revision,args.image_digest,args.release_id)
  except Exception:raise CliFailure('readiness-result-invalid') from None
  print(json.dumps(result,sort_keys=True));return 0 if result['verdict']=='observed' else 1
 except Exception as error:
  code=str(error) if isinstance(error,CliFailure) else getattr(error,'code','readiness-source-invalid')
  print(json.dumps(failure(code),sort_keys=True));return 1
if __name__=='__main__':raise SystemExit(main())
