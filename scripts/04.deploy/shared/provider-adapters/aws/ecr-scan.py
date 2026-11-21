#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.provider.aws.ecr-scan
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.package-qualification
#   disciplines: [security, sre]
#   kind: script
#   purpose: Require complete clean ECR scan findings for the exact runnable image manifest and retain safe immutable evidence.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [network, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-core-server-persistence
#     path: .github/workflows/publish-kanbien-core-platform-core-server-persistence.yml
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import time

DIGEST=re.compile(r'sha256:[a-f0-9]{64}')
IMAGE_TYPES={'application/vnd.oci.image.manifest.v1+json','application/vnd.docker.distribution.manifest.v2+json'}
INDEX_TYPES={'application/vnd.oci.image.index.v1+json','application/vnd.docker.distribution.manifest.list.v2+json'}
class ScanFailure(Exception):pass

def aws(service, operation, **parameters):
    from response import classify_error
    try:result=subprocess.run(['aws',service,operation,'--cli-input-json',json.dumps(parameters),'--output','json'],capture_output=True,text=True,timeout=45)
    except (OSError,subprocess.SubprocessError):raise ScanFailure('ecr-observation-unavailable') from None
    if result.returncode:
        if operation=='describe-image-scan-findings' and re.search(r'An error occurred \(ScanNotFoundException\) when calling the DescribeImageScanFindings operation:',result.stderr):return None
        raise ScanFailure(classify_error('ecr',operation,result.stderr))
    try:return json.loads(result.stdout)
    except (ValueError,TypeError):raise ScanFailure('ecr-response-invalid') from None

def runnable_digest(provider, repository, image_digest):
    """Resolve one exact linux/amd64 image; the caller owns provider access."""
    if not isinstance(image_digest,str) or not DIGEST.fullmatch(image_digest):raise ScanFailure('ecr-manifest-identity-mismatch')
    document=provider('ecr','batch-get-image',repositoryName=repository,imageIds=[{'imageDigest':image_digest}],acceptedMediaTypes=sorted(IMAGE_TYPES|INDEX_TYPES))
    images=document.get('images') if isinstance(document,dict) else None
    if not isinstance(images,list) or len(images)!=1 or document.get('failures'):raise ScanFailure('ecr-manifest-unavailable')
    image=images[0]
    if not isinstance(image,dict) or not isinstance(image.get('imageId'),dict) or image['imageId'].get('imageDigest')!=image_digest:raise ScanFailure('ecr-manifest-identity-mismatch')
    try:manifest=json.loads(image['imageManifest'])
    except (ValueError,KeyError,TypeError):raise ScanFailure('ecr-manifest-invalid') from None
    if not isinstance(manifest,dict):raise ScanFailure('ecr-manifest-invalid')
    kind=manifest.get('mediaType',image.get('imageManifestMediaType'));digest=image_digest
    if not isinstance(kind,str):raise ScanFailure('ecr-manifest-type-unsupported')
    if kind in INDEX_TYPES:
        entries=manifest.get('manifests')
        if not isinstance(entries,list) or not all(isinstance(entry,dict) for entry in entries):raise ScanFailure('ecr-manifest-invalid')
        candidates=[entry.get('digest') for entry in entries if isinstance(entry.get('mediaType'),str) and entry['mediaType'] in IMAGE_TYPES and entry.get('platform')=={'architecture':'amd64','os':'linux'}]
        if len(candidates)!=1 or not isinstance(candidates[0],str) or not DIGEST.fullmatch(candidates[0]):raise ScanFailure('ecr-runnable-manifest-ambiguous')
        digest=candidates[0]
    elif kind not in IMAGE_TYPES:raise ScanFailure('ecr-manifest-type-unsupported')
    return digest

def scan_complete(provider, repository, digest):
    """Observe once: False is pending/absent, invalid or rejected evidence throws."""
    report=provider('ecr','describe-image-scan-findings',repositoryName=repository,imageId={'imageDigest':digest},maxResults=1)
    if report is None:return False
    if not isinstance(report,dict) or report.get('repositoryName')!=repository or not isinstance(report.get('imageId'),dict) or report['imageId'].get('imageDigest')!=digest:raise ScanFailure('ecr-scan-identity-mismatch')
    status=report['imageScanStatus'].get('status') if isinstance(report.get('imageScanStatus'),dict) else None
    if status in ('IN_PROGRESS','PENDING'):return False
    if status!='COMPLETE':raise ScanFailure('ecr-scan-not-complete')
    findings=report.get('imageScanFindings');counts=findings.get('findingSeverityCounts') if isinstance(findings,dict) else None
    if not isinstance(counts,dict) or any(type(value) is not int or value<0 for value in counts.values()):raise ScanFailure('ecr-scan-findings-invalid')
    if counts.get('CRITICAL',0) or counts.get('HIGH',0):raise ScanFailure('ecr-scan-blocked-severity')
    return True

def check_image(provider, repository, image_digest):
    """Preparation only: no polling, sleeping or evidence-file writes."""
    digest=runnable_digest(provider,repository,image_digest)
    if not scan_complete(provider,repository,digest):raise ScanFailure('ecr-scan-not-complete')
    return digest

def scan(args):
    """Publication owns bounded polling and the existing proof representation."""
    digest=runnable_digest(aws,args.repository,args.image_digest)
    for attempt in range(args.attempts):
        if scan_complete(aws,args.repository,digest):
            return {'schema':'deploy/package-scan-proof/v1','provider':'aws-ecr','repository':args.repository,'image_digest':args.image_digest,'scan_digest':digest,'status':'COMPLETE','critical':0,'high':0,'verdict':'passed','checked_at':datetime.now(timezone.utc).isoformat()}
        if attempt+1<args.attempts:time.sleep(args.poll_seconds)
    raise ScanFailure('ecr-scan-pending-timeout')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repository',required=True);parser.add_argument('--image-digest',required=True);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--attempts',type=int,default=30);parser.add_argument('--poll-seconds',type=float,default=10);args=parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._/-]{1,255}',args.repository) or not DIGEST.fullmatch(args.image_digest) or not 1<=args.attempts<=30 or not 0<=args.poll_seconds<=10:raise ScanFailure('ecr-scan-arguments-invalid')
    proof=scan(args)
    with args.report.open('x') as handle:json.dump(proof,handle,sort_keys=True);handle.write('\n')
    if os.environ.get('GITHUB_OUTPUT'):
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as handle:
            for key in ['scan_digest','status','critical','high','verdict']:handle.write(f'{key}={proof[key]}\n')
    print(json.dumps(proof,sort_keys=True));return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ScanFailure,OSError,ValueError,TypeError) as error:
        print(json.dumps({'verdict':'failed','code':str(error) if isinstance(error,ScanFailure) else 'ecr-scan-evidence-unavailable'}));raise SystemExit(1)
