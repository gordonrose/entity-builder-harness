"""Public dispatch refusal checks for fixed passive selected-target inspection."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.selected-readiness-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the existing public wrapper routes strict passive inspection and emits safe failures before cloud access.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh
import builtins
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
DIRECTORY=Path(__file__).resolve().parent
sys.path.insert(0,str(DIRECTORY))
import selected_readiness_cli as cli
spec=importlib.util.spec_from_file_location('selected_readiness_public_gate',DIRECTORY/'script.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
SENTINEL='PRIVATE_SENTINEL_MUST_NOT_ESCAPE'

class PublicReadinessTests(unittest.TestCase):
 def args(self):
  return ['--selected-readiness','--inspect-target','--blueprint',SENTINEL,'--source-root',SENTINEL,'--source-revision','a'*40,'--image-digest','sha256:'+'b'*64,'--release-id','readiness-public-test','--json']
 def invoke(self,args):
  stdout,stderr=io.StringIO(),io.StringIO()
  with patch.object(sys,'argv',['script.py',*args]),redirect_stdout(stdout),redirect_stderr(stderr):status=gate.main()
  self.assertEqual(stderr.getvalue(),'');self.assertNotIn(SENTINEL,stdout.getvalue());self.assertNotIn('Traceback',stdout.getvalue())
  return status,json.loads(stdout.getvalue())
 def refusal(self,args):
  with patch.object(cli,'load_adapter') as load:
   status,result=self.invoke(args);self.assertEqual(status,1);load.assert_not_called()
  self.assertEqual(result,cli.failure('arguments-invalid'))
 def test_selected_mode_precedes_blueprint_dispatch(self):
  expected=cli.failure('readiness-inspection-blocked')
  def entry(args):
   self.assertEqual(args,self.args());print(json.dumps(expected));return 1
  with patch.object(cli,'main',side_effect=entry):self.assertEqual(self.invoke(self.args()),(1,expected))
 def test_missing_selected_mode_refuses(self):self.refusal([v for v in self.args() if v!='--selected-readiness'])
 def test_missing_inspection_mode_refuses(self):self.refusal([v for v in self.args() if v!='--inspect-target'])
 def test_duplicate_selector_refuses(self):self.refusal(self.args()+['--selected-readiness'])
 def test_selector_value_refuses(self):self.refusal([v.replace('--selected-readiness','--selected-readiness=yes') for v in self.args()])
 def test_execution_mode_refuses(self):self.refusal(self.args()+['--execute'])
 def test_uploaded_provider_result_refuses(self):self.refusal(self.args()+['--provider-fixture',SENTINEL])
 def test_alternate_executable_refuses(self):self.refusal(self.args()+['--aws-cli',SENTINEL])
 def test_missing_dependency_uses_safe_bootstrap_error(self):
  real=builtins.__import__
  def importing(name,*args,**kwargs):
   if name=='selected_readiness_cli':raise ImportError(SENTINEL)
   return real(name,*args,**kwargs)
  with patch.object(builtins,'__import__',side_effect=importing):status,result=self.invoke(self.args())
  self.assertEqual(status,1);self.assertEqual(result,cli.failure('readiness-dependency-unavailable'))

if __name__=='__main__':unittest.main()
