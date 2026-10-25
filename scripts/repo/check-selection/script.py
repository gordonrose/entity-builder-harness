#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.compiler.check-selection
#   version: 1
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Connect changed inputs and declared consumers to existing checks without crossing execution or evidence stages.
#   portability: { class: source-only, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.command.check-selection
#     path: scripts/repo/check-selection/script.sh
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts/01.harness/artifact-metadata'))
from header_discovery import HeaderError, parse_header_text, repository_paths
spec = importlib.util.spec_from_file_location('declaration_coverage', ROOT / 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py')
assert spec and spec.loader
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)
STAGES = {'local': 0, 'package': 1, 'deploy': 2, 'acceptance': 3}
CLASSES = {'local': {'static', 'local-runtime'}, 'package': {'container-qualification', 'ci'}, 'deploy': {'live'}, 'acceptance': {'live'}}
LOCAL_EFFECTS = {'read-only', 'writes-files'}
PLACEHOLDERS = {'{scope_contract}', '{workload_binding}', '{target_root}', '{program_contract}'}


def below(path: str, prefix: str) -> bool:
    prefix = prefix.rstrip('/')
    return path == prefix or path.startswith(prefix + '/')


def git(root: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout


def metadata(path: Path) -> dict[str, Any]:
    try:
        value = parse_header_text(path.read_text(encoding='utf-8'))
        result = value.get('agentic-artifact', value.get('agentic-script', {}))
        return result if isinstance(result, dict) else {}
    except (OSError, UnicodeError, HeaderError):
        return {}


def consumer_graph(root: Path, paths: list[str]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    headers = {path: metadata(root / path) for path in paths if coverage.within(root, path) is not None and path.endswith(('.md', '.yml', '.yaml', '.py', '.sh', '.ts', '.mjs'))}
    identities = {meta.get('id'): path for path, meta in headers.items() if isinstance(meta.get('id'), str)}
    for path, meta in headers.items():
        for consumer in meta.get('used_by', []) if isinstance(meta.get('used_by'), list) else []:
            if isinstance(consumer, dict):
                target = consumer.get('path') or identities.get(consumer.get('id'))
                if isinstance(target, str) and coverage.safe_path(target): graph.setdefault(path, set()).add(target)
    # Workspace packages expose real dependency edges even when ordinary source
    # files have no artifact header. Explicit scope inputs cover entrypoints and
    # tsconfig path aliases; unmatched imports remain reported impact gaps.
    packages: dict[str, tuple[str, dict[str, Any]]] = {}
    for path in paths:
        if path.endswith('/package.json'):
            try: data = json.loads((root / path).read_text())
            except (OSError, ValueError): continue
            if isinstance(data, dict) and isinstance(data.get('name'), str): packages[data['name']] = (str(Path(path).parent), data)
    for consumer, data in packages.values():
        for field in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'):
            for dependency in data.get(field, {}) if isinstance(data.get(field), dict) else {}:
                if dependency in packages: graph.setdefault(packages[dependency][0], set()).add(consumer)
    return graph


def closure(changed: list[str], graph: dict[str, set[str]]) -> set[str]:
    reached = set(changed)
    while True:
        added = {target for source, targets in graph.items() if any(below(path, source) for path in reached) for target in targets}
        if added <= reached: return reached
        reached |= added


def upstream_closure(references: set[str], graph: dict[str, set[str]]) -> set[str]:
    """Fingerprint the source inputs that feed selected consumers, not just the consumers."""
    reached = set(references)
    while True:
        sources = {source for source, targets in graph.items() if any(below(target, ref) or below(ref, target) for target in targets for ref in reached)}
        if sources <= reached: return reached
        reached |= sources


def discover(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    scopes: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    base = root / 'infra/04.deploy'
    for index_path in sorted(base.glob('*/targets/*/20-scopes/scope-index.yml')):
        index = coverage.document(index_path)
        entries = index.get('scopes')
        if not isinstance(entries, list): findings.append({'code': 'scope-inventory-invalid', 'path': index_path.relative_to(root).as_posix()}); continue
        indexed: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get('id'), str): findings.append({'code': 'scope-inventory-entry-invalid'}); continue
            scope_id = entry['id']
            if scope_id in indexed or '/' in scope_id or scope_id in {'.', '..'}: findings.append({'code': 'scope-inventory-entry-invalid'}); continue
            indexed.add(scope_id)
            expected = scope_id + '/00-declaration/declaration-contract.yml'
            if entry.get('declaration') != expected or entry.get('workload_binding') != scope_id + '/10-workload-binding/workload-binding.yml': findings.append({'code': 'scope-inventory-path-invalid'}); continue
            scopes.append({'contract': index_path.parent / expected, 'index': index_path, 'id': scope_id})
        found = {path.name for path in index_path.parent.iterdir() if path.is_dir() and ((path / '00-declaration').exists() or (path / '10-workload-binding').exists())}
        if found != indexed: findings.append({'code': 'scope-inventory-incomplete', 'path': index_path.relative_to(root).as_posix()})
    return scopes, findings


def validate_check(root: Path, check_id: str, check: Any) -> list[dict[str, str]]:
    def fail(code: str) -> list[dict[str, str]]: return [{'code': code, 'check_id': check_id}]
    if not isinstance(check, dict): return fail('required-check-missing')
    stage, argv, effects = check.get('stage'), check.get('argv'), check.get('effects')
    if not isinstance(stage, str) or stage not in STAGES or check.get('evidence_class') not in CLASSES[stage]: return fail('check-stage-invalid')
    if not isinstance(argv, list) or len(argv) < 2 or argv[0] != 'bash' or not all(isinstance(arg, str) and arg and not any(c in arg for c in '\n\r\0;|&`$') for arg in argv): return fail('check-argv-invalid')
    if any(('{' in arg or '}' in arg) and arg not in PLACEHOLDERS for arg in argv): return fail('check-argument-placeholder-invalid')
    command = coverage.within(root, argv[1])
    if command is None or not command.is_file(): return fail('required-check-command-missing')
    command_metadata = metadata(command)
    if 'owner' in check and check['owner'] != command_metadata.get('id'): return fail('check-owner-mismatch')
    declared = command_metadata.get('effects')
    if not coverage.strings(effects) or not coverage.strings(declared) or set(effects) != set(declared): return fail('check-effects-mismatch')
    if stage == 'local' and not set(effects) <= LOCAL_EFFECTS: return fail('local-check-effects-forbidden')
    inputs = check.get('inputs', [])
    if not coverage.strings(inputs, empty=True) or any(coverage.within(root, value) is None or not (root / value).exists() for value in inputs): return fail('check-input-missing')
    return []


def fingerprint(root: Path, refs: set[str]) -> str:
    digest = hashlib.sha256()
    for ref in sorted(refs):
        path = coverage.within(root, ref)
        if path is None: digest.update(('invalid:' + ref).encode()); continue
        entries = sorted(item for item in path.rglob('*') if not any(part in {'node_modules', '__pycache__', '.git', '.cache'} for part in item.relative_to(path).parts)) if path.is_dir() else [path]
        for item in entries:
            if item.is_symlink(): raise ValueError('input-symlink:' + item.relative_to(root).as_posix())
        files = [item for item in entries if item.is_file()] if path.is_dir() else entries
        for item in files:
            digest.update(item.relative_to(root).as_posix().encode())
            try: digest.update(item.read_bytes())
            except OSError: digest.update(b'<missing>')
    return digest.hexdigest()


def plan(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    catalog_path = args.catalog or root / 'scripts/repo/check-selection/checks.yml'
    catalog = coverage.document(catalog_path)
    checks = catalog.get('checks', {})
    findings: list[dict[str, str]] = []
    if catalog.get('schema') != 'repo/check-catalog/v1' or not isinstance(checks, dict): checks = {}; findings.append({'code': 'check-catalog-invalid'})
    changed = sorted(set(args.paths or []))
    if args.staged: changed = sorted(set(git(root, 'diff', '--cached', '--name-only', '--no-renames', '-z').split('\0')) - {''})
    if any(not coverage.safe_path(path) for path in changed): findings.append({'code': 'changed-path-invalid'})
    paths = repository_paths(root)
    graph = consumer_graph(root, paths)
    consumers = closure(changed, graph)
    scopes, discovery_gaps = discover(root)
    findings += discovery_gaps
    selected: dict[tuple[str, ...], dict[str, Any]] = {}
    impacted: list[dict[str, Any]] = []
    covered: set[str] = set()
    catalog_changed = any(below(path, 'scripts/repo/check-selection') for path in changed)
    revision = git(root, 'rev-parse', 'HEAD').strip()
    for scope in scopes:
        contract = scope['contract']
        report = coverage.inspect(contract, root, catalog)
        refs = set(report['references']) | set(report['inputs'])
        evidence_refs = upstream_closure(refs, graph)
        refs.add(scope['index'].relative_to(root).as_posix())
        # A checker implementation change impacts every scope that requires it.
        proof_dirs: set[str] = set()
        check_inputs: set[str] = set()
        for identity in report['required_checks']:
            check = checks.get(identity)
            if not isinstance(check, dict): continue
            argv = check.get('argv')
            if isinstance(argv, list) and len(argv) > 1 and isinstance(argv[1], str) and coverage.safe_path(argv[1]): proof_dirs.add(str(Path(argv[1]).parent))
            values = check.get('inputs', [])
            if isinstance(values, list): check_inputs.update(value for value in values if isinstance(value, str))
        triggers = refs | proof_dirs | check_inputs
        if not (args.all or catalog_changed or any(below(path, ref) or below(ref, path) for path in consumers for ref in triggers)): continue
        for path in changed:
            if any(below(path, ref) or below(ref, path) for ref in triggers) or closure([path], graph) & consumers & refs: covered.add(path)
        impacted.append(report)
        findings += report['findings']
        data = coverage.document(contract)
        program = data.get('program')
        program = program if isinstance(program, dict) else {}
        program_contract = program.get('contract')
        program_contract = program_contract if isinstance(program_contract, str) else ''
        substitutions = {'{scope_contract}': contract.relative_to(root).as_posix(), '{workload_binding}': (contract.parent.parent / '10-workload-binding/workload-binding.yml').relative_to(root).as_posix(), '{target_root}': scope['index'].parent.relative_to(root).as_posix(), '{program_contract}': program_contract}
        for identity in report['required_checks']:
            check = checks.get(identity)
            errors = validate_check(root, identity, check)
            findings += errors
            if errors: continue
            argv = tuple(substitutions.get(arg, arg) for arg in check['argv'])
            if any(not arg or ('{' in arg or '}' in arg) for arg in argv): findings.append({'code': 'check-arguments-unresolved', 'check_id': identity}); continue
            key = identity + ':' + hashlib.sha256(json.dumps(argv).encode()).hexdigest()[:16]
            item = selected.setdefault(argv, {'check_id': identity, 'check_key': key, 'argv': list(argv), 'stage': check['stage'], 'effects': check['effects'], 'evidence_class': check['evidence_class'], 'scopes': [], 'references': set(), 'status': 'pending'})
            if item['stage'] != check['stage'] or item['effects'] != check['effects'] or item['evidence_class'] != check['evidence_class']: findings.append({'code': 'duplicate-check-contract-conflict', 'check_id': identity})
            item['scopes'].append(report['scope'])
            item['references'].update(evidence_refs | set(check.get('inputs', [])) | {catalog_path.relative_to(root).as_posix(), str(Path(argv[1]).parent)} | {arg for arg in argv[2:] if coverage.safe_path(arg) and (root / arg).exists()})
    # Governance/docs/session changes are covered by mandatory portable metadata
    # and process gates, not by an invented deployment test. All other unmapped
    # inputs are explicit gaps, including deleted or renamed old paths.
    repository_rules = catalog.get('repository_inputs', [])
    if not isinstance(repository_rules, list):
        findings.append({'code': 'repository-input-rule-invalid'}); repository_rules = []
    for rule in repository_rules:
        if isinstance(rule, dict) and coverage.strings(rule.get('inputs')) and coverage.strings(rule.get('checks')):
            covered.update(path for path in changed if any(below(path, ref) for ref in rule['inputs']))
    non_applicable = []
    for path in changed:
        if path in covered: continue
        if path.startswith(('.agentic/', 'docs/', 'commitLogs/')) or path in {'AGENTS.md'}:
            non_applicable.append({'path': path, 'reason': 'governance-or-session-input-covered-by-mandatory-metadata-and-process-gates'})
        elif below(path, 'scripts/repo/check-selection') or below(path, 'scripts/repo/commit-gates') or below(path, 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage'):
            non_applicable.append({'path': path, 'reason': 'selector-implementation-requires-selector-regression-suite'})
        else: findings.append({'code': 'changed-input-uncovered', 'path': path, 'state': 'present' if (root / path).exists() else 'deleted'})
    for rule in repository_rules:
        if not isinstance(rule, dict) or not coverage.strings(rule.get('inputs')) or not coverage.strings(rule.get('checks')):
            findings.append({'code': 'repository-input-rule-invalid'}); continue
        if not (args.all or any(below(path, ref) for path in changed for ref in rule['inputs'])): continue
        for identity in rule['checks']:
            check = checks.get(identity)
            errors = validate_check(root, identity, check)
            findings += errors
            if errors: continue
            argv = tuple(check['argv'])
            if any('{' in arg or '}' in arg for arg in argv): findings.append({'code': 'repository-check-placeholder-invalid', 'check_id': identity}); continue
            key = identity + ':' + hashlib.sha256(json.dumps(argv).encode()).hexdigest()[:16]
            item = selected.setdefault(argv, {'check_id': identity, 'check_key': key, 'argv': list(argv), 'stage': check['stage'], 'effects': check['effects'], 'evidence_class': check['evidence_class'], 'scopes': [], 'references': set(), 'status': 'pending'})
            item['references'].update(set(rule['inputs']) | set(check.get('inputs', [])) | {catalog_path.relative_to(root).as_posix(), str(Path(argv[1]).parent)})
    evidence_doc = coverage.document(args.evidence) if args.evidence else {}
    supplied = evidence_doc.get('checks', [])
    evidence = {item.get('check_key'): item for item in supplied if isinstance(item, dict)} if isinstance(supplied, list) else {}
    results = sorted(selected.values(), key=lambda item: (STAGES[item['stage']], item['check_key']))
    for item in results:
        try: item['input_digest'] = fingerprint(root, item.pop('references'))
        except ValueError as error:
            item['input_digest'] = ''
            findings.append({'code': 'check-input-symlink-unsupported', 'path': str(error).removeprefix('input-symlink:')})
    execution_preflight_passed = not findings
    for item in results:
        item['source_revision'] = revision
        item['scopes'] = sorted(set(item['scopes']))
        required_now = STAGES[item['stage']] <= STAGES[args.stage]
        proof = evidence.get(item['check_key'], {})
        matches = item['stage'] == 'local' and evidence_doc.get('schema') == 'repo/check-selection-report/v1' and all(proof.get(key) == item[key] for key in ('input_digest', 'source_revision', 'evidence_class', 'stage', 'argv')) and proof.get('status') == 'passed'
        if matches: item['status'] = 'passed'; item['evidence_source'] = 'supplied-report'
        elif not required_now: item['status'] = 'deferred'; item['reason'] = 'required-before-' + item['stage']
        elif args.execute_local and item['stage'] == 'local' and execution_preflight_passed:
            # argv arrays only. Metadata and the catalog must agree on effects;
            # neither later-stage selectors nor evidence can authorize execution.
            completed = subprocess.run(item['argv'], cwd=root, capture_output=True, text=True, check=False)
            item['status'] = 'passed' if completed.returncode == 0 else 'failed'
            item['exit_code'] = completed.returncode
            if completed.returncode: findings.append({'code': 'required-check-failed', 'check_id': item['check_id']})
        elif args.stage != 'local' or args.execute_local:
            findings.append({'code': 'required-proof-missing-or-stale' if item['stage'] == 'local' else 'required-proof-owned-by-stage-controller', 'check_id': item['check_id'], 'stage': item['stage']})
    return {'schema': 'repo/check-selection-report/v1', 'stage': args.stage, 'verdict': 'gap' if findings else ('passed' if args.execute_local or args.stage != 'local' else 'planned'), 'source_revision': revision, 'changed_inputs': [{'path': path, 'state': 'present' if (root / path).exists() else 'deleted'} for path in changed], 'affected_consumers': sorted(consumers - set(changed) | {path for report in impacted for path in report['consumers']}), 'scopes': impacted, 'checks': results, 'non_applicable': non_applicable, 'findings': findings, 'limitations': ['Explicit scope inputs and workspace dependencies cover supported source consumers; unclassified changed inputs remain gaps.', 'Selection and local proof never authorize package publication, provider access, secrets or acceptance.', 'Aggregate reports can reuse only local evidence; later-stage receipts must pass their owning controller and cannot be waived here.']}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--paths', nargs='+')
    mode.add_argument('--staged', action='store_true')
    mode.add_argument('--all', action='store_true')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--stage', choices=STAGES, default='local')
    parser.add_argument('--execute-local', action='store_true')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = plan(args)
    print(json.dumps(report, sort_keys=True))
    return 1 if report['findings'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
