#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.platform-shell-package-custody
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Capture the successful shell publication boundaries as the existing immutable package custody receipt.
#   portability: { class: internal, targets: [kanbien-staging] }
#   effects: [writes-files]
#   used_by:
#   - id: github.workflow.deploy-platform-shell-staging
#     path: .github/workflows/deploy-platform-shell-staging.yml
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    required=['SOURCE_CHECKS_OUTCOME','QUALIFICATION_OUTCOME','CREDENTIALS_OUTCOME','REGISTRY_LOGIN_OUTCOME','PUBLISHED_IMAGE_OUTCOME','SCAN_OUTCOME','SBOM_OUTCOME','PROVENANCE_OUTCOME','SBOM_ATTESTATION_OUTCOME']
    if any(os.environ.get(key)!='success' for key in required):raise ValueError('publication-prerequisite-not-successful')
    source=os.environ.get('GITHUB_SHA','');digest=os.environ.get('PUBLISHED_DIGEST','');run=os.environ.get('GITHUB_RUN_ID','')
    if not re.fullmatch('[a-f0-9]{40,64}',source) or not re.fullmatch('sha256:[a-f0-9]{64}',digest) or not run.isdigit():raise ValueError('publication-identity-invalid')
    sbom=json.loads(Path(os.environ['SBOM_PATH']).read_text())
    if not isinstance(sbom,dict) or not str(sbom.get('spdxVersion','')).startswith('SPDX-'):raise ValueError('publication-sbom-invalid')
    # The published image equality was checked by its preceding CLI boundary;
    # retain that exact source/digest/run and successful evidence outcomes.
    receipt={'schema':'deploy/package-custody-receipt/v1','target':'kanbien-staging','environment_class':'staging','provider_region_alias':'aws-eu-west-1','candidate_id':'platform-shell','package_contract_id':'kanbien-staging-platform-shell','program_id':'platform-shell','source_revision':source,'image_digest':digest,'release_identity':'source-'+source,'checked_at':datetime.now(timezone.utc).isoformat(),'checks':{key:'passed' for key in ['runnable_program_contract','dependency_boundary','delivery_access_static','delivery_access_live','local_image_smoke','ecr_scan','sbom','provenance_attestation']},'verdict':'qualified','receipt_reference':'github-actions-run:'+run}
    with Path(args.output).open('x') as handle:json.dump(receipt,handle,sort_keys=True,indent=2);handle.write('\n')
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,KeyError,ValueError) as error:
        print(json.dumps({'verdict':'failed','code':str(error) if isinstance(error,ValueError) else 'publication-evidence-unavailable'}));raise SystemExit(1)
