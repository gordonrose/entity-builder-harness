#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.validation.platform-shell-release-evidence.test
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual shell readiness and generic succession CLI boundaries with explicitly simulated immutable release evidence.
#   portability: { class: internal, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.verify-platform-shell-deploy-readiness.smoke-test
#     path: scripts/04.deploy/verify-platform-shell-deploy-readiness/smoke-test.sh
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import yaml

ROOT=Path(__file__).resolve().parents[3]
OWNER=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('shell_evidence_test_subject',OWNER/'release_evidence.py')
evidence=importlib.util.module_from_spec(spec);spec.loader.exec_module(evidence)
SUCCESSION=ROOT/'scripts/04.deploy/lifecycle/60-run/release-succession/script.sh'


def command(argv, expected=0, reason=None):
    result=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==expected,(argv,result.returncode,result.stdout,result.stderr)
    if reason: assert reason in result.stdout,(reason,result.stdout,result.stderr)
    return json.loads(result.stdout) if result.stdout else {}


def observed(manifest,root):
    return {'schema':evidence.OBSERVATION_SCHEMA,'target':evidence.TARGET,'scope':evidence.SCOPE,
      'checked_at':datetime.now(timezone.utc).isoformat(),'source_revision':manifest['source']['commit_sha'],
      'image_digest':manifest['artifacts']['image']['image_digest'],'verdict':'passed','evidence_class':'simulated','permission_state_sha256':'sha256:'+'d'*64,
      **{key:manifest['source'][key] for key in ('repository','workflow_path','workflow_run_id')},
      'checks':{key:'passed' for key in evidence.CHECKS},'input_files':evidence.source_inputs(root)}


def promote(root, candidate, predecessor, expected=0, reason=None):
    return command(['bash',str(SUCCESSION),'--operation','promote','--evidence-root',str(root/'release-evidence'),
      '--candidate-record',str(candidate),'--expected-predecessor',predecessor,'--rehearsal-root',str(root),'--json'],expected,reason)


def package(manifest,root):
    receipt={'schema':'deploy/package-custody-receipt/v1','target':'kanbien-staging','environment_class':'staging',
      'provider_region_alias':'aws-eu-west-1','candidate_id':'platform-shell','package_contract_id':'kanbien-staging-platform-shell',
      'program_id':'platform-shell','source_revision':manifest['source']['commit_sha'],
      'image_digest':manifest['artifacts']['image']['image_digest'],'release_identity':'platform-shell-fixture',
      'checked_at':datetime.now(timezone.utc).isoformat(),'receipt_reference':'github-actions-run:'+str(manifest['source']['workflow_run_id']),
      'checks':{name:'passed' for name in ('runnable_program_contract','dependency_boundary','delivery_access_static','delivery_access_live','local_image_smoke','sbom','provenance_attestation','ecr_scan')},'verdict':'qualified'}
    path=root/'package-custody.json';path.write_text(json.dumps(receipt));return path


def prepare(manifest_path,root):
    root.mkdir(parents=True,exist_ok=True)
    target=root/evidence.TARGET_PATH;target.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/evidence.CONFIGURATION,root/evidence.CONFIGURATION)
    for directory in ('cloudformation','iam'):
        shutil.copytree(ROOT/evidence.TARGET_PATH/directory,target/directory,dirs_exist_ok=True)
    manifest=yaml.safe_load(manifest_path.read_text())
    manifest['acceptance']={'evidence_root':'release-evidence','current_observation':'current-observation.json','package_custody_receipt':'package-custody.json'}
    package(manifest,root)
    observation=root/'current-observation.json';observation.write_text(json.dumps(observed(manifest,root)))
    produced=evidence.write_candidate(manifest,observation,root/'release-evidence',root=root,evidence_class='simulated')
    promote(root,produced['candidate_record'],'none')
    manifest_path.write_text(yaml.safe_dump(manifest,sort_keys=False))
    return manifest,produced


def tests():
    with tempfile.TemporaryDirectory(prefix='shell-release-evidence-') as directory:
        root=Path(directory);manifest_path=root/'readiness.yml'
        fixture=(OWNER/'smoke-test.sh').read_text().split('cat > "$VALID" <<\'YAML\'\n',1)[1].split('\nYAML\n',1)[0]
        manifest_path.write_text(fixture)
        manifest,first=prepare(manifest_path,root)
        readiness=['bash',str(OWNER/'script.sh'),'--manifest',str(manifest_path),'--rehearsal-root',str(root),'--json']
        checks=0
        def ready(value,expected=0,reason=None):
            nonlocal checks
            manifest_path.write_text(yaml.safe_dump(value,sort_keys=False));report=command(readiness,expected,reason)
            assert report['evidence_class']=='simulated';checks+=1
        ready(manifest)
        command(['bash',str(OWNER/'script.sh'),'--manifest',str(manifest_path),'--json'],1);checks+=1
        no_acceptance=copy.deepcopy(manifest);del no_acceptance['acceptance'];ready(no_acceptance,1,'shell-release-acceptance-record-required')
        mismatch=copy.deepcopy(manifest);mismatch['artifacts']['source_commit_sha']='f'*40;ready(mismatch,1,'shell-release-source-identity-mismatch')
        mismatched_run=copy.deepcopy(manifest);mismatched_run['github']['workflow_run_id']='different';ready(mismatched_run,1,'shell-release-source-identity-mismatch')
        missing=copy.deepcopy(manifest);missing['acceptance']['evidence_root']='empty';ready(missing,1,'shell-release-current-reference-required')
        escaped=copy.deepcopy(manifest);escaped['acceptance']['current_observation']='../current-observation.json';ready(escaped,1,'shell-release-path-invalid')
        observation=root/'current-observation.json';original=observation.read_bytes()
        for mutation,reason in [
          (lambda value:value.update(checked_at=(datetime.now(timezone.utc)-timedelta(minutes=16)).isoformat()),'shell-release-current-observation-stale'),
          (lambda value:value['checks'].pop('permissions'),'shell-release-observation-incomplete'),
          (lambda value:value.update(workflow_run_id='unrelated'),'shell-release-observation-publication-mismatch'),
          (lambda value:value.update(raw_provider_output='unsafe-extra'),'shell-release-observation-fields-invalid')]:
            changed=json.loads(original);mutation(changed);observation.write_text(json.dumps(changed));ready(manifest,1,reason)
        observation.write_bytes(original)
        # History stays byte-identical and valid when current source/security changes;
        # current readiness must fail, even for an IAM input outside the two generic anchors.
        policy=next((root/evidence.TARGET_PATH/'iam').rglob('*.yml'),None)
        if policy is None: policy=next((root/evidence.TARGET_PATH/'iam').rglob('*.json'))
        previous=policy.read_bytes();policy.write_bytes(previous+b'\n')
        command(['bash',str(SUCCESSION),'--operation','validate-current','--evidence-root',str(root/'release-evidence'),'--rehearsal-root',str(root),'--json']);checks+=1
        ready(manifest,1,'shell-release-current-inputs-mismatch');policy.write_bytes(previous)
        changed=observed(manifest,root);changed['permission_state_sha256']='sha256:'+'e'*64
        observation.write_text(json.dumps(changed));ready(manifest,1,'shell-release-current-permission-identity-changed')
        observation.write_text(json.dumps(observed(manifest,root)))
        # Durable capture survives disappearance of the original producer report;
        # acceptance uses a separate fresh report and retained historical proof.
        observation.unlink();observation.write_text(json.dumps(observed(manifest,root)))
        (root/'package-custody.json').unlink();ready(manifest)
        reused=evidence.write_candidate(manifest,observation,root/'release-evidence',root=root,evidence_class='simulated')
        assert Path(reused['candidate_record']).is_file()
        package(manifest,root)
        receipt=Path(first['observation_receipt']);retained=receipt.read_bytes();receipt.write_bytes(retained+b' ')
        ready(manifest,1,'release-succession-proof-receipt-mismatch');receipt.write_bytes(retained)
        old_current=(root/'release-evidence/current-accepted-release.yml').read_bytes()
        old_files={path:path.read_bytes() for path in (root/'release-evidence').rglob('*') if path.is_file() and path.name!='.release-succession.lock'}
        successor=copy.deepcopy(manifest)
        for item,key in [('source','commit_sha'),('github','commit_sha'),('artifacts','source_commit_sha')]: successor[item][key]='b'*40
        successor['source']['workflow_run_id']=successor['github']['workflow_run_id']='1234567891'
        successor['artifacts']['image']['image_digest']='sha256:'+'c'*64
        observation.write_text(json.dumps(observed(successor,root)))
        package(successor,root)
        second=evidence.write_candidate(successor,observation,root/'release-evidence',root=root,evidence_class='simulated')
        promote(root,second['candidate_record'],'none',1,'release-succession-predecessor-mismatch');checks+=1
        ready(successor,1,'shell-release-current-identity-mismatch')
        promote(root,second['candidate_record'],first['release_id']);checks+=1
        # Simulate interruption after immutable history publication and before ref replacement.
        (root/'release-evidence/current-accepted-release.yml').write_bytes(old_current)
        promote(root,second['candidate_record'],first['release_id']);checks+=1
        promote(root,second['candidate_record'],first['release_id']);checks+=1
        ready(successor)
        # The retained release can reuse unchanged historical behavior; the
        # additive decision never rewrites its acceptance or advances current.
        manifest_path.write_text(yaml.safe_dump(manifest,sort_keys=False))
        compatibility=readiness+['--record-rollback-compatibility',first['release_id']]
        result=command(compatibility);checks+=1
        compatibility_path=Path(result['facts']['compatibility_record']);compatibility_raw=compatibility_path.read_bytes()
        command(compatibility);checks+=1
        assert compatibility_path.read_bytes()==compatibility_raw
        policy.write_bytes(previous+b'\n')
        command(compatibility,1,'shell-release-rollback-inputs-changed');checks+=1
        policy.write_bytes(previous)
        command(compatibility+['--allow-blocked','--caller-intent','planning'],2);checks+=1
        for path,raw in old_files.items():
            if path.name!='current-accepted-release.yml': assert path.read_bytes()==raw,path
        print(json.dumps({'schema':'deploy/platform-shell-release-evidence-test/v1','verdict':'passed','evidence_class':'simulated','cli_checks':checks}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',type=Path);parser.add_argument('--root',type=Path);args=parser.parse_args()
    if args.prepare:
        if args.root is None: parser.error('--prepare requires --root')
        prepare(args.prepare,args.root)
    else: tests()
