#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.docker.disposable-cleanup
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.package-qualification
#   disciplines: [security, sre]
#   kind: script
#   purpose: Test disposable cleanup partial failure, existing absence and unobservable engine through the actual CLI.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.package-custody-receipt
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/smoke-test.sh
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

COMMAND=Path(__file__).with_name('disposable-cleanup.py')
FAKE='''#!/usr/bin/env python3
import os,sys,pathlib
kind,operation,name=sys.argv[1],sys.argv[2],sys.argv[-1];state=pathlib.Path(os.environ['STATE'])
if operation=='inspect':
 if os.environ['MODE']=='invalid-text':sys.stdout.buffer.write(b'\\xff');sys.exit(1)
 if os.environ['MODE']=='unknown':print('Cannot connect to Docker daemon',file=sys.stderr);sys.exit(1)
 if state.exists():print('[{}]');sys.exit(0)
 messages={'container':'No such container: '+name,'network':'network '+name+' not found','volume':'get '+name+': no such volume'}
 print('Error response from daemon: '+messages[kind],file=sys.stderr);sys.exit(1)
if os.environ['MODE']=='partial':sys.exit(1)
state.unlink(missing_ok=True)
'''
class CleanupTests(unittest.TestCase):
 def test_actual_cleanup_cli(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);binary=root/'docker';binary.write_text(FAKE);binary.chmod(0o755);state=root/'present'
   for kind in ['container','network','volume']:
    for mode,present,expected in [('valid',True,0),('valid',False,0),('partial',True,1),('unknown',False,1),('invalid-text',False,1)]:
     state.write_text('present') if present else state.unlink(missing_ok=True)
     result=subprocess.run(['python3','-B',str(COMMAND),'--'+kind,'disposable-fixture'],env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'STATE':str(state),'MODE':mode},capture_output=True,text=True)
     self.assertEqual(result.returncode,expected,(kind,mode,result.stdout,result.stderr));report=json.loads(result.stdout)
     if expected:self.assertNotEqual(report['verdict'],'passed')
     else:self.assertFalse(state.exists())
     if mode=='invalid-text':self.assertEqual(report['findings'],[{'kind':kind,'outcome':'unobservable'}]);self.assertNotIn('Traceback',result.stderr)
 def test_rejected_arguments_are_not_echoed(self):
  result=subprocess.run(['python3','-B',str(COMMAND),'--credential-canary-value'],capture_output=True,text=True)
  self.assertEqual(result.returncode,2);self.assertEqual(result.stderr,'DIAGNOSTIC_CODE=DISPOSABLE_CLEANUP_ARGUMENTS_INVALID\n');self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
 def test_qualifier_cleanup_preserves_original_failure(self):
  repo=COMMAND.resolve().parents[5]
  qualifier=repo/'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh'
  fake_docker='''#!/usr/bin/env python3
import os,sys
args=sys.argv[1:]
if args[0]=='run':sys.exit(int(os.environ['PRIMARY_EXIT']))
if args[0]=='inspect':print(os.environ.get('RUNNING','true'));sys.exit(0)
if args[0]=='logs':print(os.environ.get('LOG_TEXT','diagnostic-unavailable'),file=sys.stderr);sys.exit(int(os.environ['LOG_EXIT']))
if args[:2]==['container','inspect']:print('[{}]');sys.exit(0)
if args[:2]==['container','rm']:sys.exit(1)
sys.exit(90)
'''
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for name,source in [('docker',fake_docker),('sleep','#!/bin/sh\nexit 0\n')]:
    binary=root/name;binary.write_text(source);binary.chmod(0o755)
   for primary,diagnostic,running,log_text,expected,code in [(37,0,'true','diagnostic-unavailable',37,'COLLECTOR_CONTAINER_START_FAILED'),(0,29,'true','diagnostic-unavailable',29,'COLLECTOR_LOG_OBSERVATION_FAILED'),(0,0,'false','diagnostic-unavailable',1,'COLLECTOR_RUNNING_OBSERVATION_FAILED'),(0,0,'true','error config credential-canary-value',1,'COLLECTOR_LOG_QUALIFICATION_FAILED'),(0,0,'true','diagnostic-unavailable',1,None)]:
    result=subprocess.run(['bash',str(qualifier)],cwd=repo,env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'PRIMARY_EXIT':str(primary),'LOG_EXIT':str(diagnostic),'RUNNING':running,'LOG_TEXT':log_text},capture_output=True,text=True)
    self.assertEqual(result.returncode,expected,(result.stdout,result.stderr))
    report=json.loads(result.stdout.splitlines()[-1]);self.assertEqual(report['verdict'],'failed');self.assertEqual(report['findings'][0]['outcome'],'still-present')
    self.assertNotIn('diagnostic-unavailable',result.stdout+result.stderr)
    self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
    if code:self.assertIn('DIAGNOSTIC_CODE='+code,result.stderr);self.assertIn('LIFECYCLE_STAGE=package',result.stderr);self.assertIn('CHILD_OUTPUT=not-retained-unstructured-output',result.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
