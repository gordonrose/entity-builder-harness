#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.acceptance-route
#   version: 2
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate connected acceptance route templates using each command's real offline argument parser before consequential stages.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.acceptance-route
#     path: scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.sh
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[5]
CONTEXT = {'scope_contract', 'accepted_record', 'target_root', 'target_directory', 'evidence_root', 'candidate_record', 'current_release_id'}


def document(path: Path) -> dict:
    try:
        value = yaml.safe_load(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, yaml.YAMLError):
        return {}
    return value if isinstance(value, dict) else {}


def reference(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9._/-]+', value) or value.startswith(('/', '-')) or '..' in Path(value).parts:
        return None
    path = root / value
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        return None
    return path


def load_route(scope_contract: Path, root: Path = ROOT) -> tuple[dict, Path | None]:
    contract = document(scope_contract)
    acceptance = contract.get('acceptance')
    route_path = reference(root, acceptance.get('route')) if isinstance(acceptance, dict) else None
    return (document(route_path), route_path) if route_path is not None else ({}, None)


def command_metadata(path: Path) -> dict:
    try:
        lines = path.read_text().splitlines()
        at = next(index for index, line in enumerate(lines) if line.strip() == '# agentic-artifact:')
        header = []
        for line in lines[at + 1:]:
            if not line.startswith('#'): break
            header.append(line[1:])
        value = yaml.safe_load('\n'.join(header))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, StopIteration, yaml.YAMLError):
        return {}


def resolve(argv: Any, values: dict[str, Any]) -> list[str] | None:
    if not isinstance(argv, list) or len(argv) < 2 or not all(isinstance(item, str) and item for item in argv): return None
    result = []
    for item in argv:
        match = re.fullmatch(r'\{([a-z][a-z0-9_]*)\}', item)
        value = values.get(match[1]) if match else item
        if not isinstance(value, str) or not value or any(char in value for char in '\n\r\0') or (not match and ('{' in item or '}' in item)): return None
        result.append(value)
    return result


def input_values(path: Path, route: dict, *, root: Path = ROOT) -> dict:
    data = document(path)
    values = data.get('values')
    specifications = route.get('inputs')
    if data.get('schema') != 'deploy/acceptance-inputs/v1' or data.get('target') != route.get('target') or data.get('scope') != route.get('scope') or not isinstance(values, dict) or not isinstance(specifications, dict):
        raise ValueError('acceptance-inputs-identity-invalid')
    if set(values) != set(specifications): raise ValueError('acceptance-inputs-set-invalid')
    for key, spec in specifications.items():
        value = values[key]
        if not isinstance(spec, dict): raise ValueError('acceptance-input-contract-invalid')
        kind = spec.get('kind')
        if kind in {'path', 'identifier', 'optional-path'}:
            if kind == 'optional-path' and value is None:
                continue
            if not isinstance(value, str) or not value or any(char in value for char in '\n\r\0'): raise ValueError('acceptance-input-value-invalid')
            if kind in {'path', 'optional-path'}:
                selected = Path(value) if Path(value).is_absolute() else root / value
                if not selected.is_file() or selected.is_symlink(): raise ValueError('acceptance-input-path-missing')
                values[key] = str(selected)
        elif kind in {'proof-map', 'receipt-map'}:
            expected = route.get('proofs', {}) if kind == 'proof-map' else spec.get('receipts')
            if not isinstance(expected, (dict, list)):
                raise ValueError('acceptance-input-receipt-map-invalid')
            expected_names = set(expected)
            if not expected_names or any(not isinstance(name, str) or not name for name in expected_names):
                raise ValueError('acceptance-input-receipt-map-invalid')
            if not isinstance(value, dict) or set(value) != expected_names or not all(isinstance(name, str) and isinstance(item, str) and item for name, item in value.items()): raise ValueError('acceptance-input-proof-map-invalid')
            for name, item in value.items():
                selected = Path(item) if Path(item).is_absolute() else root / item
                if not selected.is_file() or selected.is_symlink(): raise ValueError('acceptance-input-proof-path-missing')
                value[name] = str(selected)
        else: raise ValueError('acceptance-input-kind-unsupported')
    return values


def _inspect(scope_contract: Path, root: Path = ROOT, command_root: Path | None = None) -> dict:
    command_root = command_root or root
    findings, references = [], set()
    def gap(code, value=None):
        finding = {'code': code}
        if value is not None: finding['reference'] = str(value)
        if finding not in findings: findings.append(finding)
    def required_path(value, code):
        path = reference(root, value)
        if path is None or not path.is_file(): gap(code, value); return None
        references.add(str(value)); return path
    contract = document(scope_contract)
    route, route_path = load_route(scope_contract, root)
    if route_path is None or not route:
        gap('acceptance-route-missing')
        return {'schema': 'deploy/acceptance-route-report/v1', 'verdict': 'gap', 'findings': findings, 'references': []}
    references.add(route_path.relative_to(root).as_posix())
    program = contract.get('program') if isinstance(contract.get('program'), dict) else {}
    image_path = reference(root, program.get('image_contract'))
    image = document(image_path) if image_path else {}
    if route.get('schema') != 'deploy/acceptance-route/v1': gap('acceptance-route-schema-invalid')
    for field, expected in [('target', contract.get('target')), ('scope', contract.get('scope')), ('program_id', program.get('id')), ('image_id', image.get('id'))]:
        if not isinstance(expected, str) or route.get(field) != expected: gap('acceptance-route-subject-mismatch', field)
    inputs = route.get('inputs')
    if not isinstance(inputs, dict): gap('acceptance-route-inputs-invalid'); inputs = {}
    values = {}
    for key, spec in inputs.items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', key) or not isinstance(spec, dict) or spec.get('kind') not in {'path', 'identifier', 'optional-path', 'proof-map', 'receipt-map'} or not isinstance(spec.get('owner'), str) or not spec['owner']:
            gap('acceptance-route-input-contract-invalid', key); continue
        if spec['kind'] == 'receipt-map':
            receipt_names = spec.get('receipts')
            if not isinstance(receipt_names, list) or not receipt_names or any(not isinstance(name, str) or not name for name in receipt_names) or len(set(receipt_names)) != len(receipt_names):
                gap('acceptance-route-input-contract-invalid', key)
        elif spec['kind'] != 'proof-map':
            if not isinstance(spec.get('example'), str) or not spec['example']: gap('acceptance-route-input-example-missing', key)
            else: values[key] = spec['example']
    inputs_schema = required_path(route.get('inputs_schema'), 'acceptance-route-input-schema-missing')
    if inputs_schema and document(inputs_schema).get('record_schema') != 'deploy/acceptance-inputs/v1': gap('acceptance-route-input-schema-invalid')
    record = route.get('accepted_record')
    if not isinstance(record, dict): gap('acceptance-route-record-contract-invalid'); record = {}
    record_schema = required_path(record.get('schema_path'), 'acceptance-route-record-schema-missing')
    if record_schema and document(record_schema).get('record_schema') != record.get('schema'): gap('acceptance-route-record-schema-invalid')
    record_path = reference(scope_contract.parent.parent, record.get('path'))
    if record_path is None: gap('acceptance-route-record-path-invalid')
    outputs = route.get('outputs')
    if not isinstance(outputs, dict) or set(outputs) != {'candidate_record', 'current_release_id'}:
        gap('acceptance-route-outputs-invalid')
        outputs = {}
    expected_outputs = {
        'candidate_record': {'command': 'collect', 'fact': 'candidate_record', 'kind': 'target-evidence-path'},
        'current_release_id': {'command': 'current-release', 'fact': 'release_id', 'kind': 'release-id'},
    }
    if outputs != expected_outputs:
        gap('acceptance-route-outputs-invalid')
    evidence_root = scope_contract.parent.parent / '30-release-evidence'
    values.update(
        scope_contract=str(scope_contract), accepted_record=str(record_path or ''),
        target_root=str(scope_contract.parents[2]), target_directory=str(scope_contract.parents[3]),
        evidence_root=str(evidence_root),
        candidate_record=str(evidence_root / 'release-candidates/release-aaaaaaaaaaaaaaaaaaaaaaaa.yml'),
        current_release_id='release-aaaaaaaaaaaaaaaaaaaaaaaa',
    )
    # The collector takes one bounded manifest; the contents are checked only at
    # the acceptance stage. A package build must not require future live proof.
    values['acceptance_inputs'] = '/tmp/acceptance-route-inputs.json'
    commands = route.get('commands')
    if not isinstance(commands, dict) or not commands: gap('acceptance-route-commands-invalid'); commands = {}
    probes = []
    for name, command in commands.items():
        if not isinstance(command, dict): gap('acceptance-route-command-invalid', name); continue
        argv = resolve(command.get('argv'), values)
        if argv is None or argv[0] != 'bash': gap('acceptance-route-command-unresolved', name); continue
        script = reference(command_root, argv[1])
        if script is None or not script.is_file(): gap('acceptance-route-command-missing', argv[1]); continue
        references.add(argv[1])
        metadata = command_metadata(script)
        declared_effects, actual_effects = command.get('effects'), metadata.get('effects')
        valid_effects = all(isinstance(value, list) and value and all(isinstance(effect, str) for effect in value) for value in (declared_effects, actual_effects))
        if not valid_effects or metadata.get('id') != command.get('owner') or set(actual_effects) != set(declared_effects):
            gap('acceptance-route-command-owner-or-effects-mismatch', name); continue
        if metadata.get('argument_validation') != {'flag': '--validate-arguments', 'effects': ['read-only']}:
            gap('acceptance-route-command-offline-parser-undeclared', name); continue
        probes.append((name, script, argv))
    proofs = route.get('proofs')
    if not isinstance(proofs, dict) or not proofs: gap('acceptance-route-proofs-missing'); proofs = {}
    obligations = document(record_schema).get('required_proofs') if record_schema else None
    if not isinstance(obligations, list) or not obligations or any(not isinstance(item, str) for item in obligations) or len(set(obligations)) != len(obligations) or set(obligations) != set(proofs):
        gap('acceptance-route-required-proofs-mismatch')
    for name, proof in proofs.items():
        if not isinstance(proof, dict) or not isinstance(proof.get('command'), str) or proof.get('command') not in commands or not all(isinstance(proof.get(field), str) and proof[field] for field in ('proof_type', 'operation', 'result_code', 'image_role')): gap('acceptance-route-proof-binding-invalid', name)
    sequence = route.get('sequence')
    if not isinstance(sequence, list) or any(not isinstance(pair, list) or len(pair) != 2 or any(not isinstance(name, str) or name not in proofs for name in pair) for pair in sequence): gap('acceptance-route-sequence-invalid')
    for field, value in [('collector', route.get('collector')), ('record-validator', record.get('validator')), ('candidate-validator', route.get('candidate_validator')), ('promotion', route.get('promotion'))]:
        if not isinstance(value, str) or value not in commands: gap('acceptance-route-stage-missing', field)
    downstream = route.get('downstream')
    if not isinstance(downstream, list) or not downstream or any(not isinstance(item, str) or item not in commands for item in downstream): gap('acceptance-route-downstream-gates-missing')
    if not findings:
        reports = {}
        for name, script, argv in probes:
            key = tuple(argv)
            try:
                if key in reports: continue
                result = subprocess.run([argv[0], str(script), *argv[2:], '--validate-arguments'], cwd=command_root, capture_output=True, text=True, timeout=15, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'AWS_EC2_METADATA_DISABLED': 'true'})
                parsed = json.loads(result.stdout)
                reports[key] = parsed
                if result.returncode or not isinstance(parsed, dict) or parsed.get('schema') != 'deploy/command-arguments-report/v1' or parsed.get('verdict') != 'valid': gap('acceptance-route-command-arguments-invalid', name)
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError): gap('acceptance-route-command-arguments-invalid', name)
        for name, proof in proofs.items():
            command = commands[proof['command']]
            parsed = reports.get(tuple(resolve(command['argv'], values)), {})
            expected = {key: value for key, value in proof.items() if key not in {'command', 'image_role'}}
            if not isinstance(parsed, dict) or parsed.get('proof_contract') != expected:
                gap('acceptance-route-proof-command-contract-mismatch', name)
    return {'schema': 'deploy/acceptance-route-report/v1', 'target': contract.get('target'), 'scope': contract.get('scope'), 'verdict': 'gap' if findings else 'covered', 'validation': 'route-template-actual-command-parsers', 'findings': findings, 'references': sorted(references)}


def inspect(scope_contract: Path, root: Path = ROOT, command_root: Path | None = None) -> dict:
    try:
        return _inspect(scope_contract, root, command_root)
    except (KeyError, TypeError, ValueError, OSError):
        return {'schema': 'deploy/acceptance-route-report/v1', 'verdict': 'gap', 'findings': [{'code': 'acceptance-route-contract-malformed'}], 'references': []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope-contract', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--validate-arguments', action='store_true')
    try:
        args, unknown = parser.parse_known_args()
        if unknown or args.scope_contract is None: raise ValueError('acceptance-route-arguments-invalid')
        if args.validate_arguments:
            print(json.dumps({'schema': 'deploy/command-arguments-report/v1', 'verdict': 'valid', 'findings': []})); return 0
        report = inspect(args.scope_contract, args.root)
        if args.inputs is not None and not report['findings']:
            input_values(args.inputs, load_route(args.scope_contract, args.root)[0], root=args.root)
            report['validation'] = 'resolved-run-inputs'
    except (ValueError, TypeError, OSError) as error:
        report = {'schema': 'deploy/acceptance-route-report/v1', 'verdict': 'gap', 'findings': [{'code': str(error) if isinstance(error, ValueError) else 'acceptance-route-input-invalid'}]}
    print(json.dumps(report, sort_keys=True)); return 1 if report['findings'] else 0

if __name__ == '__main__': raise SystemExit(main())
