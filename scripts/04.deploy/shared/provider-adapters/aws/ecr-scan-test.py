#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.ecr-scan
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-15"
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
import copy
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

SPEC=importlib.util.spec_from_file_location('shared_ecr_scan',Path(__file__).with_name('ecr-scan.py'))
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
PARENT='sha256:'+'a'*64
CHILD='sha256:'+'b'*64
REPOSITORY='fixture/repository'

def manifest_response(kind='application/vnd.oci.image.index.v1+json'):
 return {'images':[{'imageId':{'imageDigest':PARENT},'imageManifest':json.dumps({'mediaType':kind,'manifests':[{'mediaType':'application/vnd.oci.image.manifest.v1+json','digest':CHILD,'platform':{'architecture':'amd64','os':'linux'}}]})}]}

def scan_response():
 return {'repositoryName':REPOSITORY,'imageId':{'imageDigest':CHILD},'imageScanStatus':{'status':'COMPLETE'},'imageScanFindings':{'findingSeverityCounts':{}}}

class SharedImageChecks(unittest.TestCase):
 def test_single_observation_and_exact_identity(self):
  for kind in sorted(M.IMAGE_TYPES|M.INDEX_TYPES):
   with self.subTest(kind=kind):
    digest=CHILD if kind in M.INDEX_TYPES else PARENT
    report=scan_response();report['imageId']['imageDigest']=digest
    provider=Mock(side_effect=[manifest_response(kind),report])
    with patch.object(M.time,'sleep') as sleep,patch.object(M.Path,'open') as opened:
     self.assertEqual(M.check_image(provider,REPOSITORY,PARENT),digest)
    sleep.assert_not_called();opened.assert_not_called()
    self.assertEqual(provider.call_count,2)
    self.assertEqual(provider.call_args_list[0].args,('ecr','batch-get-image'))
    self.assertEqual(provider.call_args_list[0].kwargs,{'repositoryName':REPOSITORY,'imageIds':[{'imageDigest':PARENT}],'acceptedMediaTypes':sorted(M.IMAGE_TYPES|M.INDEX_TYPES)})
    self.assertEqual(provider.call_args_list[1].kwargs,{'repositoryName':REPOSITORY,'imageId':{'imageDigest':digest},'maxResults':1})

 def test_manifest_rejections_prevent_scan(self):
  cases=[(None,'ecr-manifest-unavailable'),({'images':[]},'ecr-manifest-unavailable')]
  for mutate,code in [
   (lambda d:d.update(failures=[{}]),'ecr-manifest-unavailable'),
   (lambda d:d['images'][0]['imageId'].update(imageDigest=CHILD),'ecr-manifest-identity-mismatch'),
   (lambda d:d['images'][0].update(imageManifest='private-canary'),'ecr-manifest-invalid'),
   (lambda d:d['images'][0].update(imageManifest='[]'),'ecr-manifest-invalid')]:
   value=manifest_response();mutate(value);cases.append((value,code))
  for change,code in [
   ({'mediaType':[]},'ecr-manifest-type-unsupported'),
   ({'mediaType':'unsupported'},'ecr-manifest-type-unsupported'),
   ({'manifests':None},'ecr-manifest-invalid'),
   ({'manifests':[None]},'ecr-manifest-invalid'),
   ({'manifests':[]},'ecr-runnable-manifest-ambiguous')]:
   value=manifest_response();body=json.loads(value['images'][0]['imageManifest']);body.update(change);value['images'][0]['imageManifest']=json.dumps(body);cases.append((value,code))
  for mutation in ('duplicate','wrong-platform','bad-digest','bad-type'):
   value=manifest_response();body=json.loads(value['images'][0]['imageManifest']);entry=body['manifests'][0]
   if mutation=='duplicate':body['manifests'].append(copy.deepcopy(entry))
   elif mutation=='wrong-platform':entry['platform']['architecture']='arm64'
   elif mutation=='bad-digest':entry['digest']='private-canary'
   else:entry['mediaType']=[]
   value['images'][0]['imageManifest']=json.dumps(body);cases.append((value,'ecr-runnable-manifest-ambiguous'))
  for value,code in cases:
   with self.subTest(code=code,value=value):
    provider=Mock(return_value=value)
    with self.assertRaisesRegex(M.ScanFailure,'^'+code+'$'):M.check_image(provider,REPOSITORY,PARENT)
    self.assertEqual(provider.call_count,1)
  provider=Mock()
  with self.assertRaisesRegex(M.ScanFailure,'^ecr-manifest-identity-mismatch$'):M.check_image(provider,REPOSITORY,None)
  provider.assert_not_called()

 def test_scan_rejections_do_not_poll(self):
  cases=[(None,'ecr-scan-not-complete'),([], 'ecr-scan-identity-mismatch')]
  for mutate,code in [
   (lambda d:d.update(repositoryName='private-canary'),'ecr-scan-identity-mismatch'),
   (lambda d:d['imageId'].update(imageDigest=PARENT),'ecr-scan-identity-mismatch'),
   (lambda d:d.update(imageId=None),'ecr-scan-identity-mismatch'),
   (lambda d:d.update(imageScanStatus=None),'ecr-scan-not-complete'),
   (lambda d:d.update(imageScanFindings=None),'ecr-scan-findings-invalid'),
   (lambda d:d['imageScanFindings'].pop('findingSeverityCounts'),'ecr-scan-findings-invalid')]:
   value=scan_response();mutate(value);cases.append((value,code))
  for status in ('PENDING','IN_PROGRESS','FAILED','private-canary',[]):
   value=scan_response();value['imageScanStatus']['status']=status;cases.append((value,'ecr-scan-not-complete'))
  for counts in (None,[],{'HIGH':'0'},{'LOW':-1},{'HIGH':False},{'CRITICAL':1},{'HIGH':1}):
   value=scan_response();value['imageScanFindings']['findingSeverityCounts']=counts
   cases.append((value,'ecr-scan-blocked-severity' if counts in ({'CRITICAL':1},{'HIGH':1}) else 'ecr-scan-findings-invalid'))
  for value,code in cases:
   with self.subTest(code=code,value=value):
    provider=Mock(side_effect=[manifest_response(),value])
    with patch.object(M.time,'sleep') as sleep,self.assertRaisesRegex(M.ScanFailure,'^'+code+'$'):M.check_image(provider,REPOSITORY,PARENT)
    sleep.assert_not_called();self.assertEqual(provider.call_count,2)
  original=M.ScanFailure('aws-access-denied');provider=Mock(side_effect=original)
  with self.assertRaises(M.ScanFailure) as caught:M.check_image(provider,REPOSITORY,PARENT)
  self.assertIs(caught.exception,original);self.assertEqual(provider.call_count,1)

 def test_publication_uses_same_checks_and_owns_waiting(self):
  args=SimpleNamespace(repository=REPOSITORY,image_digest=PARENT,attempts=2,poll_seconds=3)
  with patch.object(M,'runnable_digest',return_value=CHILD) as resolve,patch.object(M,'scan_complete',side_effect=[False,True]) as observed,patch.object(M.time,'sleep') as sleep:
   proof=M.scan(args)
  resolve.assert_called_once_with(M.aws,REPOSITORY,PARENT)
  self.assertEqual(observed.call_count,2);sleep.assert_called_once_with(3)
  self.assertEqual((proof['image_digest'],proof['scan_digest'],proof['verdict']),(PARENT,CHILD,'passed'))

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
    observed=[json.loads(line) for line in calls.read_text().splitlines()]
    self.assertEqual(observed[0][:2],['ecr','batch-get-image'])
    self.assertEqual(json.loads(observed[0][observed[0].index('--cli-input-json')+1])['imageIds'],[{'imageDigest':PARENT}])
    for invocation in observed[1:]:
     self.assertEqual(invocation[:2],['ecr','describe-image-scan-findings'])
     self.assertEqual(json.loads(invocation[invocation.index('--cli-input-json')+1]),{'repositoryName':REPOSITORY,'imageId':{'imageDigest':PARENT if mode=='plain' else CHILD},'maxResults':1})
    self.assertEqual(len(observed),1 if mode=='ambiguous' else 3 if mode in ['pending','pending-then-complete','missing-then-complete'] else 2)
    if valid:
     proof=json.loads(receipt.read_text());self.assertEqual(proof['image_digest'],'sha256:'+'a'*64);self.assertEqual(proof['scan_digest'],'sha256:'+('a' if mode=='plain' else 'b')*64)
     original=receipt.read_bytes();duplicate=subprocess.run(argv,env=environment,capture_output=True,text=True);self.assertEqual(duplicate.returncode,1);self.assertEqual(receipt.read_bytes(),original)
    else:self.assertFalse(receipt.exists());self.assertFalse(output.exists())
    if mode=='high':self.assertEqual(json.loads(result.stdout)['code'],'ecr-scan-blocked-severity')
    if mode=='denied':self.assertEqual(json.loads(result.stdout)['code'],'aws-access-denied')
if __name__=='__main__':unittest.main(verbosity=2)
