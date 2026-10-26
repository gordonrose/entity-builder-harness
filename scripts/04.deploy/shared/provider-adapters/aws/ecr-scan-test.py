#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.ecr-scan
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.package-qualification
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise exact image scan identity, severity, pending and denied outcomes through the real provider adapter CLI.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.package-custody-receipt
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/smoke-test.sh
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

FAKE='''#!/usr/bin/env python3
import json,os,pathlib,sys
mode=os.environ['MODE'];parent='sha256:'+'a'*64;child='sha256:'+'b'*64;state=pathlib.Path(os.environ['STATE']);op=sys.argv[2]
with pathlib.Path(os.environ['CALLS']).open('a') as log:log.write(json.dumps(sys.argv[1:])+'\\n')
if op=='batch-get-image':
 image={'mediaType':'application/vnd.oci.image.manifest.v1+json','digest':child,'platform':{'architecture':'amd64','os':'linux'}}
 manifest={'mediaType':'application/vnd.oci.image.index.v1+json','manifests':[image]}
 if mode=='plain':manifest={'mediaType':'application/vnd.oci.image.manifest.v1+json'}
 if mode=='ambiguous':manifest['manifests'].append(image)
 print(json.dumps({'images':[{'imageId':{'imageDigest':parent},'imageManifest':json.dumps(manifest)}]}));sys.exit(0)
count=int(state.read_text()) if state.exists() else 0;state.write_text(str(count+1))
if mode=='denied':print('An error occurred (AccessDeniedException) when calling the DescribeImageScanFindings operation: denied',file=sys.stderr);sys.exit(254)
if mode=='unknown':print('unobservable ScanNotFoundException',file=sys.stderr);sys.exit(1)
if mode=='missing-then-complete' and count==0:print('An error occurred (ScanNotFoundException) when calling the DescribeImageScanFindings operation: pending',file=sys.stderr);sys.exit(254)
status='IN_PROGRESS' if mode=='pending' or (mode=='pending-then-complete' and count==0) else 'FAILED' if mode=='failed' else 'COMPLETE'
counts={'HIGH':1} if mode=='high' else {'CRITICAL':1} if mode=='critical' else {'HIGH':'0'} if mode=='malformed' else {}
digest=parent if mode=='plain' else child
if mode=='wrong-identity':digest='sha256:'+'c'*64
print(json.dumps({'repositoryName':'fixture/repository','imageId':{'imageDigest':digest},'imageScanStatus':{'status':status},'imageScanFindings':{'findingSeverityCounts':counts}}))
'''
class EcrScanTests(unittest.TestCase):
 def test_actual_provider_cli(self):
  command=Path(__file__).with_name('ecr-scan.py')
  for mode in ['clean','plain','pending-then-complete','missing-then-complete','denied','unknown','pending','failed','high','critical','malformed','wrong-identity','ambiguous']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
    root=Path(directory);binary=root/'aws';binary.write_text(FAKE);binary.chmod(0o755);receipt=root/'scan.json';output=root/'github-output';calls=root/'calls'
    environment={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'MODE':mode,'STATE':str(root/'state'),'CALLS':str(calls),'GITHUB_OUTPUT':str(output)}
    argv=['python3','-B',str(command),'--repository','fixture/repository','--image-digest','sha256:'+'a'*64,'--report',str(receipt),'--attempts','2','--poll-seconds','0']
    result=subprocess.run(argv,env=environment,capture_output=True,text=True);valid=mode in ['clean','plain','pending-then-complete','missing-then-complete']
    self.assertEqual(result.returncode,0 if valid else 1,result.stdout+result.stderr)
    if valid:
     proof=json.loads(receipt.read_text());self.assertEqual(proof['image_digest'],'sha256:'+'a'*64);self.assertEqual(proof['scan_digest'],'sha256:'+('a' if mode=='plain' else 'b')*64)
     original=receipt.read_bytes();duplicate=subprocess.run(argv,env=environment,capture_output=True,text=True);self.assertEqual(duplicate.returncode,1);self.assertEqual(receipt.read_bytes(),original)
    else:self.assertFalse(receipt.exists());self.assertFalse(output.exists())
    if mode=='high':self.assertEqual(json.loads(result.stdout)['code'],'ecr-scan-blocked-severity')
    if mode=='denied':self.assertEqual(json.loads(result.stdout)['code'],'aws-access-denied')
if __name__=='__main__':unittest.main(verbosity=2)
