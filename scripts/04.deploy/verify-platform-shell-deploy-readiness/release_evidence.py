#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.validation.platform-shell-release-evidence
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind shell readiness to producer-observed current state and immutable generic release succession without overwriting historical evidence.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.script.verify-platform-shell-deploy-readiness
#     path: scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[3]
TARGET = 'kanbien-staging'
SCOPE = 'platform-shell'
TARGET_PATH = Path('infra/04.deploy/03.product/targets/kanbien/staging')
CONFIGURATION = TARGET_PATH / 'target-profile.yml'
PERMISSIONS = TARGET_PATH / 'cloudformation/foundation.yml'
OBSERVATION_SCHEMA = 'deploy/platform-shell-runtime-observation/v1'
CHECKS = {'runtime-healthy', 'image-identity', 'configuration', 'permissions'}


def digest(raw): return 'sha256:' + hashlib.sha256(raw).hexdigest()


def source_inputs(root=ROOT):
    paths = [root / CONFIGURATION]
    for directory in ('cloudformation', 'iam'):
        paths.extend(path for path in (root / TARGET_PATH / directory).rglob('*') if path.is_file() and path.suffix in {'.yml', '.yaml', '.json'})
    if root / PERMISSIONS not in paths: raise ValueError('shell-release-permission-source-missing')
    if any(path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) for path in paths): raise ValueError('shell-release-source-symlink')
    return {path.relative_to(root).as_posix(): digest(path.read_bytes()) for path in sorted(set(paths))}


def succession(root=ROOT, evidence_class='live'):
    spec=importlib.util.spec_from_file_location('shell_release_succession',ROOT/'scripts/04.deploy/lifecycle/60-run/release-succession/script.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.REPOSITORY_ROOT=root;module.EVIDENCE_CLASS=evidence_class
    return module


def within(root, name):
    if not isinstance(name, str) or not name: raise ValueError('shell-release-path-invalid')
    selected=Path(name)
    if selected.is_absolute() or '..' in selected.parts: raise ValueError('shell-release-path-invalid')
    result=root/selected
    if not result.resolve().is_relative_to(root.resolve()) or result.is_symlink(): raise ValueError('shell-release-path-invalid')
    return result


def identity(manifest):
    try:
        sources={manifest['source']['commit_sha'],manifest['github']['commit_sha'],manifest['artifacts']['source_commit_sha']}
        runs={manifest['source']['workflow_run_id'],manifest['github']['workflow_run_id']}
        repositories={manifest['source']['repository'],manifest['github']['repository']}
        workflows={manifest['source']['workflow_path'],manifest['github']['workflow_path']}
        image=manifest['artifacts']['image']['image_digest']
    except (KeyError,TypeError): raise ValueError('shell-release-source-identity-missing') from None
    if len(sources)!=1 or len(runs)!=1 or len(workflows)!=1 or len(repositories)!=1: raise ValueError('shell-release-source-identity-mismatch')
    source=next(iter(sources))
    if not isinstance(source,str) or not re.fullmatch('[a-f0-9]{40}',source) or not isinstance(image,str) or not re.fullmatch('sha256:[a-f0-9]{64}',image): raise ValueError('shell-release-artifact-identity-invalid')
    if manifest.get('client',{}).get('id')!='kanbien' or manifest.get('environment',{}).get('id')!='staging' or manifest.get('deployment',{}).get('service_id')!=SCOPE: raise ValueError('shell-release-target-identity-mismatch')
    return source,image


def observation(path, *, source, image, publication, root=ROOT, evidence_class='live', fresh=True):
    value=json.loads(path.read_text())
    if not isinstance(value,dict) or value.get('schema')!=OBSERVATION_SCHEMA or value.get('target')!=TARGET or value.get('scope')!=SCOPE or value.get('evidence_class','live')!=evidence_class or value.get('verdict')!='passed': raise ValueError('shell-release-observation-invalid')
    if value.get('source_revision')!=source or value.get('image_digest')!=image: raise ValueError('shell-release-observation-identity-mismatch')
    allowed={'schema','target','scope','checked_at','source_revision','image_digest','workflow_run_id','workflow_path','repository','verdict','evidence_class','checks','input_files','permission_state_sha256'}
    if set(value)!=allowed: raise ValueError('shell-release-observation-fields-invalid')
    if any(value.get(key)!=publication.get(key) for key in ('workflow_run_id','workflow_path','repository')): raise ValueError('shell-release-observation-publication-mismatch')
    if not isinstance(value.get('permission_state_sha256'),str) or not re.fullmatch('sha256:[a-f0-9]{64}',value['permission_state_sha256']): raise ValueError('shell-release-permission-identity-invalid')
    checks=value.get('checks')
    if not isinstance(checks,dict) or set(checks)!=CHECKS or any(result!='passed' for result in checks.values()): raise ValueError('shell-release-observation-incomplete')
    recorded=value.get('input_files')
    if not isinstance(recorded,dict) or not recorded or any(not isinstance(key,str) or not isinstance(item,str) or not re.fullmatch('sha256:[a-f0-9]{64}',item) for key,item in recorded.items()): raise ValueError('shell-release-observation-inputs-invalid')
    timestamp=datetime.fromisoformat(value['checked_at'].replace('Z','+00:00'))
    if timestamp.tzinfo is None: raise ValueError('shell-release-observation-time-invalid')
    if fresh:
        age=(datetime.now(timezone.utc)-timestamp).total_seconds()
        if age < -60 or age > 900: raise ValueError('shell-release-current-observation-stale')
        if recorded!=source_inputs(root): raise ValueError('shell-release-current-inputs-mismatch')
    return value


def package_receipt(path, manifest):
    source,image=identity(manifest)
    result=subprocess.run([sys.executable,str(ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py'),
      '--receipt',str(path),'--expected-target',TARGET,'--expected-candidate',SCOPE,
      '--expected-package-contract','kanbien-staging-platform-shell','--expected-program',SCOPE,'--json'],
      cwd=ROOT,text=True,capture_output=True,timeout=30)
    if result.returncode: raise ValueError('shell-release-package-custody-invalid')
    receipt=json.loads(path.read_text())
    if receipt['source_revision']!=source or receipt['image_digest']!=image or receipt['receipt_reference']!='github-actions-run:'+str(manifest['source']['workflow_run_id']): raise ValueError('shell-release-package-identity-mismatch')
    return receipt


def validate_candidate(manifest, *, root=ROOT, evidence_class='live'):
    """Offline publication prerequisite; retain custody after CI downloads expire."""
    acceptance=manifest.get('acceptance')
    if not isinstance(acceptance,dict): raise ValueError('shell-release-acceptance-record-required')
    path=within(root,acceptance.get('package_custody_receipt'))
    if path.exists(): return package_receipt(path,manifest)
    # A missing download may reuse exact immutable proof in accepted lineage.
    # An existing but invalid download never falls back to different evidence.
    source,image=identity(manifest)
    evidence=within(root,acceptance.get('evidence_root'));module=succession(root,evidence_class)
    state=module.current(evidence);cursor=state['release_id'] if state else None
    while cursor is not None:
        history,_=module.history_record_for_id(evidence,cursor)
        if history['release']['source_revision']==source and history['release']['image_digest']==image and history['evidence']['kind']=='verified-release-candidate':
            candidate,_=module.document(evidence/history['evidence']['path'])
            receipt=candidate.get('proof_set',{}).get('package-custody')
            if isinstance(receipt,dict):
                try: return package_receipt(evidence/receipt['path'],manifest)
                except ValueError: pass
        cursor=history['predecessor']
    raise ValueError('shell-release-package-custody-unavailable')


def write_candidate(manifest, observation_path, evidence_root, *, root=ROOT, evidence_class='live'):
    """The provider observer calls this only after its actual checks complete."""
    source,image=identity(manifest)
    custody=validate_candidate(manifest,root=root,evidence_class=evidence_class)
    observed=observation(observation_path,source=source,image=image,publication=manifest['source'],root=root,evidence_class=evidence_class)
    if not evidence_root.resolve().is_relative_to(root.resolve()): raise ValueError('shell-release-path-invalid')
    if evidence_class=='simulated' and (not root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()) or root.resolve().is_relative_to(ROOT.resolve())): raise ValueError('shell-release-rehearsal-root-invalid')
    module=succession(root,evidence_class)
    raw=json.dumps(observed,sort_keys=True,separators=(',',':')).encode()
    receipt=evidence_root/'proof-receipts'/('runtime-alignment-'+digest(raw)[7:]+'.json')
    module.immutable_write(receipt,raw)
    proofs={'runtime-alignment':{'path':receipt.relative_to(evidence_root).as_posix(),'sha256':digest(raw)}}
    package_raw=json.dumps(custody,sort_keys=True,separators=(',',':')).encode()
    package_path=evidence_root/'proof-receipts'/('package-custody-'+digest(package_raw)[7:]+'.json')
    module.immutable_write(package_path,package_raw)
    proofs['package-custody']={'path':package_path.relative_to(evidence_root).as_posix(),'sha256':digest(package_raw)}
    release_identity={'target':TARGET,'scope':SCOPE,'source_revision':source,'image_digest':image,'configuration_contract':{'path':CONFIGURATION.as_posix(),'sha256':digest((root/CONFIGURATION).read_bytes())},'permission_contract':{'path':PERMISSIONS.as_posix(),'sha256':digest((root/PERMISSIONS).read_bytes())},'proof_set_sha256':module.sha256_bytes(module.canonical(proofs))}
    identifier=module.release_id(release_identity)
    record={'schema':module.CANDIDATE_SCHEMA,'evidence_class':evidence_class,'target':TARGET,'scope':SCOPE,'status':'verified','release':{'id':identifier,**{key:value for key,value in release_identity.items() if key not in {'target','scope'}}},'proof':{'accepted_at':observed['checked_at'],'receipt_count':len(proofs)},'proof_set':proofs}
    module.candidate_identity(record,evidence_root)
    path=evidence_root/module.CANDIDATE_DIRECTORY/(identifier+'.yml')
    module.immutable_write(path,module.rendered(record))
    return {'candidate_record':str(path),'release_id':identifier,'observation_receipt':str(receipt)}


def validate_ready(manifest, *, root=ROOT, evidence_class='live'):
    source,image=identity(manifest)
    acceptance=manifest.get('acceptance')
    if not isinstance(acceptance,dict): raise ValueError('shell-release-acceptance-record-required')
    evidence=within(root,acceptance.get('evidence_root'))
    current_observation=within(root,acceptance.get('current_observation'))
    module=succession(root,evidence_class)
    state=module.current(evidence)
    if state is None or state['target']!=TARGET or state['scope']!=SCOPE: raise ValueError('shell-release-current-reference-required')
    history,_=module.history_record_for_id(evidence,state['release_id'])
    if history['evidence']['kind']!='verified-release-candidate': raise ValueError('shell-release-qualified-candidate-required')
    candidate,_=module.document(evidence/history['evidence']['path'])
    _,_,_,release=module.candidate_identity(candidate,evidence)
    if release['source_revision']!=source or release['image_digest']!=image or release['configuration_contract']['path']!=CONFIGURATION.as_posix() or release['permission_contract']['path']!=PERMISSIONS.as_posix(): raise ValueError('shell-release-current-identity-mismatch')
    receipt=candidate.get('proof_set',{}).get('runtime-alignment')
    if not isinstance(receipt,dict): raise ValueError('shell-release-runtime-receipt-required')
    retained=observation(evidence/receipt['path'],source=source,image=image,publication=manifest['source'],root=root,evidence_class=evidence_class,fresh=False)
    custody=candidate.get('proof_set',{}).get('package-custody')
    if not isinstance(custody,dict): raise ValueError('shell-release-package-receipt-required')
    package_receipt(evidence/custody['path'],manifest)
    fresh=observation(current_observation,source=source,image=image,publication=manifest['source'],root=root,evidence_class=evidence_class)
    if retained['permission_state_sha256']!=fresh['permission_state_sha256']: raise ValueError('shell-release-current-permission-identity-changed')
    return state['release_id']


def write_compatibility_from_history(manifest, historical_release_id, *, root=ROOT, evidence_class='live'):
    """Reuse immutable historical behavior only under byte-identical current inputs."""
    source,image=identity(manifest)
    acceptance=manifest.get('acceptance')
    if not isinstance(acceptance,dict): raise ValueError('shell-release-acceptance-record-required')
    evidence=within(root,acceptance.get('evidence_root'))
    module=succession(root,evidence_class)
    state=module.current(evidence)
    cursor=state['release_id'] if state else None
    while cursor is not None and cursor!=historical_release_id:
        ancestor,_=module.history_record_for_id(evidence,cursor);cursor=ancestor['predecessor']
    if cursor is None: raise ValueError('shell-release-retained-history-required')
    history,_=module.history_record_for_id(evidence,historical_release_id)
    if history['target']!=TARGET or history['scope']!=SCOPE or history['evidence']['kind']!='verified-release-candidate': raise ValueError('shell-release-qualified-candidate-required')
    candidate,_=module.document(evidence/history['evidence']['path'])
    _,_,_,release=module.candidate_identity(candidate,evidence,current_contracts=False)
    if release['source_revision']!=source or release['image_digest']!=image: raise ValueError('shell-release-current-identity-mismatch')
    proofs=candidate.get('proof_set',{})
    if set(proofs)!={'runtime-alignment','package-custody'}: raise ValueError('shell-release-runtime-receipt-required')
    previous=observation(evidence/proofs['runtime-alignment']['path'],source=source,image=image,publication=manifest['source'],root=root,evidence_class=evidence_class,fresh=False)
    if previous['input_files']!=source_inputs(root): raise ValueError('shell-release-rollback-inputs-changed')
    current_history,_=module.history_record_for_id(evidence,state['release_id'])
    if current_history['evidence']['kind']!='verified-release-candidate': raise ValueError('shell-release-qualified-candidate-required')
    current_candidate,_=module.document(evidence/current_history['evidence']['path'])
    module.candidate_identity(current_candidate,evidence,current_contracts=False)
    current_runtime=current_candidate.get('proof_set',{}).get('runtime-alignment')
    if not isinstance(current_runtime,dict): raise ValueError('shell-release-runtime-receipt-required')
    current_receipt=json.loads((evidence/current_runtime['path']).read_text())
    if previous['permission_state_sha256']!=current_receipt.get('permission_state_sha256'): raise ValueError('shell-release-rollback-permission-identity-changed')
    package_receipt(evidence/proofs['package-custody']['path'],manifest)
    contracts={'configuration_contract':{'path':CONFIGURATION.as_posix(),'sha256':digest((root/CONFIGURATION).read_bytes())},'permission_contract':{'path':PERMISSIONS.as_posix(),'sha256':digest((root/PERMISSIONS).read_bytes())}}
    proof_hash=module.sha256_bytes(module.canonical(proofs))
    compatibility={'target':TARGET,'scope':SCOPE,'historical_release_id':historical_release_id,'source_revision':source,'image_digest':image,**contracts,'workloads':[SCOPE],'proof_set_sha256':proof_hash}
    identifier='rollback-compatibility-'+hashlib.sha256(module.canonical(compatibility)).hexdigest()[:24]
    record={'schema':module.COMPATIBILITY_SCHEMA,'evidence_class':evidence_class,'target':TARGET,'scope':SCOPE,'status':'verified',
      'historical_release':{'release_id':historical_release_id,'source_revision':source,'image_digest':image},
      'rollback':{'id':identifier,**contracts,'workloads':[SCOPE],'proof_set_sha256':proof_hash},
      'proof':{'qualified_at':datetime.now(timezone.utc).isoformat(),'receipt_count':len(proofs)},'proof_set':proofs}
    path=evidence/module.CANDIDATE_DIRECTORY/(identifier+'.yml')
    if path.exists():
        existing,_=module.document(path);module.compatibility_identity(existing,evidence)
    else: module.immutable_write(path,module.rendered(record))
    module.record_compatibility(evidence,path)
    return {'rollback_compatibility_id':identifier,'candidate_record':str(path),'compatibility_record':str(evidence/module.COMPATIBILITY_DIRECTORY/(identifier+'.yml'))}
