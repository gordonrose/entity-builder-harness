#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.package-custody-capture
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Capture the existing package custody schema only from exact successful upstream qualification and provenance outcomes.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-core-server-persistence
#     path: .github/workflows/publish-kanbien-core-platform-core-server-persistence.yml
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
from types import SimpleNamespace
from validate import validate,Failure,BASE_CHECKS

OUTCOMES=['QUALIFICATION_OUTCOME','ACCESS_OUTCOME','PUBLICATION_OUTCOME','SCAN_OUTCOME','SBOM_OUTCOME','PROVENANCE_OUTCOME','SBOM_ATTESTATION_OUTCOME']
def main():
    parser=argparse.ArgumentParser()
    for name in ['target','environment-class','provider-region-alias','candidate','package-contract','program','scan-check','sbom','output']:parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    if any(os.environ.get(key)!='success' for key in OUTCOMES):raise ValueError('custody-prerequisite-not-successful')
    if args.scan_check not in {'ecr_scan','vulnerability_scan'}:raise ValueError('custody-scan-kind-invalid')
    sbom=json.loads(Path(args.sbom).read_text())
    if not isinstance(sbom,dict) or not str(sbom.get('spdxVersion','')).startswith('SPDX-'):raise ValueError('custody-sbom-invalid')
    receipt={'schema':'deploy/package-custody-receipt/v1','target':args.target,'environment_class':args.environment_class,'provider_region_alias':args.provider_region_alias,'candidate_id':args.candidate,'package_contract_id':args.package_contract,'program_id':args.program,'source_revision':os.environ.get('GITHUB_SHA'),'image_digest':os.environ.get('IMAGE_DIGEST'),'release_identity':'source-'+os.environ.get('GITHUB_SHA',''),'checked_at':datetime.now(timezone.utc).isoformat(),'checks':{key:'passed' for key in BASE_CHECKS|{args.scan_check}},'verdict':'qualified','receipt_reference':'github-actions-run:'+os.environ.get('GITHUB_RUN_ID','')}
    validate(receipt,SimpleNamespace(expected_target=args.target,expected_candidate=args.candidate,expected_package_contract=args.package_contract,expected_program=args.program))
    with Path(args.output).open('x') as handle:json.dump(receipt,handle,sort_keys=True);handle.write('\n')
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,TypeError,Failure) as error:
        print(json.dumps({'verdict':'failed','code':str(error) if isinstance(error,ValueError) else 'custody-evidence-invalid'}));raise SystemExit(1)
