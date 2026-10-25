#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.persistence-accepted-release.validate.impl
#   version: 1
#   status: active
#   created_on: '2026-10-25'
#   updated_on: '2026-10-25'
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Validate the exact accepted record and retained proof bindings offline.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   argument_validation:
#     flag: --validate-arguments
#     effects:
#     - read-only
#   used_by:
#   - id: deploy.command.persistence-accepted-release.validate
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/validate-accepted-release/script.sh
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import yaml
ROOT = Path(__file__).resolve().parents[8]
IMPLEMENTATION_ROOT = ROOT


def validate_historical_legacy_record(path: Path, record: dict, root: Path) -> list[str]:
    """Validate immutable predecessor custody without calling it current-policy compliant.

    A release accepted before the IAM permission contract cannot prove facts
    that did not exist then.  Its historic evidence remains usable only when
    the generic succession reference preserves the exact record hash and
    identity.  A new candidate is still subject to the current collector.
    """
    try:
        source = IMPLEMENTATION_ROOT / 'scripts/04.deploy/lifecycle/60-run/release-succession/script.py'
        spec = importlib.util.spec_from_file_location('release_succession_validation', source)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        evidence_root = path.parent
        current = module.current(evidence_root)
        if not isinstance(current, dict):
            return ['accepted-release-historical-succession-missing']
        history_path = evidence_root / current['record']['path']
        history, _ = module.document(history_path)
        evidence = history.get('evidence') if isinstance(history, dict) else None
        if not isinstance(evidence, dict) or evidence.get('kind') != 'legacy-accepted-record' or evidence.get('path') != path.name:
            return ['accepted-release-historical-succession-mismatch']
        raw = path.read_bytes()
        if module.sha256_bytes(raw) != evidence.get('sha256'):
            return ['accepted-release-historical-record-mutated']
        target, scope, _, _ = module.legacy_identity(record, raw)
        if target != current.get('target') or scope != current.get('scope'):
            return ['accepted-release-historical-identity-mismatch']
        return []
    except Exception:
        return ['accepted-release-historical-succession-invalid']

def validate(path: Path, root: Path = ROOT, evidence_class: str = 'live') -> list[str]:
    try:
        record = yaml.safe_load(path.read_text())
        if evidence_class == 'simulated' and not root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()): return ['accepted-release-simulation-root-invalid']
        if evidence_class == 'live' and isinstance(record, dict) and record.get('schema') == 'deploy/persistence-accepted-release/v1' and record.get('status') == 'accepted':
            return validate_historical_legacy_record(path, record, root)
        if not isinstance(record, dict) or record.get('evidence_class', 'live') != evidence_class or record.get('status') != ('accepted' if evidence_class == 'live' else 'rehearsed'): return ['accepted-release-evidence-class-invalid']
        source = IMPLEMENTATION_ROOT / 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py'
        spec=importlib.util.spec_from_file_location('retained_acceptance_collector',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.ROOT=root;module.EVIDENCE_CLASS=evidence_class
        module.validate_record(record,evidence_class=evidence_class)
        return []
    except Exception as error:
        codes=getattr(error,'codes',None)
        return list(codes) if isinstance(codes,tuple) else [str(error) if error.__class__.__name__ == 'EvidenceFailure' else 'accepted-release-record-invalid']

def main():
    parser=argparse.ArgumentParser(add_help=False,exit_on_error=False)
    parser.add_argument('--record',type=Path);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--rehearsal-root',type=Path);parser.add_argument('--json',action='store_true');parser.add_argument('--validate-arguments',action='store_true')
    try:
        args,unknown=parser.parse_known_args()
        if unknown or args.record is None: raise ValueError()
        if args.validate_arguments:
            print(json.dumps({'schema':'deploy/command-arguments-report/v1','verdict':'valid','findings':[]}));return 0
        codes=validate(args.record,args.rehearsal_root or args.root,'simulated' if args.rehearsal_root else 'live')
    except (ValueError,argparse.ArgumentError): codes=['accepted-release-arguments-invalid']
    print(json.dumps({'schema':'deploy/accepted-release-validation-report/v1','verdict':'failed' if codes else 'validated','findings':[{'code':code} for code in codes]}));return int(bool(codes))
if __name__=='__main__':raise SystemExit(main())
