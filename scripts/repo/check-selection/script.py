#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.compiler.check-selection
#   version: 5
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-26"
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
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts/repo/check-selection'))
from local_cache import LocalCache, runtime_identity, valid_node_package, TOOLS
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


def dormant_roots(root: Path, catalog: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    roots = catalog.get('dormant_impact_roots', [])
    if not isinstance(roots, list) or not all(isinstance(item, str) and item and coverage.safe_path(item) and (root / item).is_dir() for item in roots):
        return [], [{'code': 'dormant-impact-roots-invalid'}]
    if len(set(roots)) != len(roots):
        return [], [{'code': 'dormant-impact-roots-duplicate'}]
    return roots, []


def consumer_graph(root: Path, paths: list[str], dormant: list[str] | tuple[str, ...] = ()) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    headers = {path: metadata(root / path) for path in paths if coverage.within(root, path) is not None and path.endswith(('.md', '.yml', '.yaml', '.py', '.sh', '.ts', '.mjs'))}
    identities = {meta.get('id'): path for path, meta in headers.items() if isinstance(meta.get('id'), str)}
    for path, meta in headers.items():
        for consumer in meta.get('used_by', []) if isinstance(meta.get('used_by'), list) else []:
            if isinstance(consumer, dict):
                target = consumer.get('path') or identities.get(consumer.get('id'))
                if isinstance(target, str) and coverage.safe_path(target) and not any(below(path, root) or below(target, root) for root in dormant): graph.setdefault(path, set()).add(target)
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
    if not isinstance(stage, str) or stage not in STAGES or not isinstance(check.get('evidence_class'), str) or check['evidence_class'] not in CLASSES[stage]: return fail('check-stage-invalid')
    if not isinstance(argv, list) or len(argv) < 2 or argv[0] != 'bash' or not all(isinstance(arg, str) and arg and not any(c in arg for c in '\n\r\0;|&`$') for arg in argv): return fail('check-argv-invalid')
    parameters = check.get('parameters', {})
    if not isinstance(parameters, dict): return fail('check-parameters-invalid')
    for name, parameter in parameters.items():
        if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', name) or not isinstance(parameter, dict) or parameter.get('kind') != 'path' or parameter.get('required') is not True or not isinstance(parameter.get('schema'), str): return fail('check-parameters-invalid')
        if stage == 'local' or '{' + name + '}' not in argv: return fail('check-runtime-parameter-invalid')
    allowed = PLACEHOLDERS | {'{' + name + '}' for name in parameters}
    if any(('{' in arg or '}' in arg) and arg not in allowed for arg in argv): return fail('check-argument-placeholder-invalid')
    if stage == 'local':
        runtime = check.get('runtime')
        if not isinstance(runtime, dict) or not coverage.strings(runtime.get('tools')) or not set(runtime['tools']) <= TOOLS or not coverage.strings(runtime.get('environment'), empty=True) or not coverage.strings(runtime.get('config_inputs', []), empty=True) or any(coverage.within(root, value) is None for value in runtime.get('config_inputs', [])): return fail('check-runtime-contract-invalid')
        node_packages = runtime.get('node_packages', [])
        if not coverage.strings(node_packages, empty=True) or any(not valid_node_package(name) for name in node_packages) or ('node' in runtime['tools'] and 'node_packages' not in runtime) or ('typescript' in runtime['tools'] and 'typescript' not in node_packages): return fail('check-runtime-node-installation-invalid')
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
            try:
                content = item.read_bytes()
                mode = item.stat().st_mode & 0o777
            except OSError:
                content, mode = b'<missing>', None
            digest.update(json.dumps([item.relative_to(root).as_posix(), mode, len(content)]).encode())
            digest.update(content)
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
    dormant, dormant_findings = dormant_roots(root, catalog)
    findings += dormant_findings
    graph = consumer_graph(root, paths, dormant)
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
        refs.add(scope['index'].relative_to(root).as_posix())
        evidence_refs = upstream_closure(refs, graph)
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
            runtime = check.get('runtime')
            configs = runtime.get('config_inputs', []) if isinstance(runtime, dict) else []
            if isinstance(configs, list): check_inputs.update(value for value in configs if isinstance(value, str))
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
            runtime_parameters = {'{' + name + '}' for name in check.get('parameters', {})}
            if any(not arg or (('{' in arg or '}' in arg) and arg not in runtime_parameters) for arg in argv): findings.append({'code': 'check-arguments-unresolved', 'check_id': identity}); continue
            key = identity + ':' + hashlib.sha256(json.dumps(argv).encode()).hexdigest()[:16]
            item = selected.setdefault(argv, {'check_id': identity, 'check_key': key, 'argv': list(argv), 'stage': check['stage'], 'effects': check['effects'], 'evidence_class': check['evidence_class'], 'scopes': [], 'references': set(), 'status': 'pending', 'runtime': check.get('runtime', {}), 'parameters': check.get('parameters', {}), 'applicability': check.get('applicability', {})})
            if any(item[field] != check.get(field, {}) for field in ('stage', 'effects', 'evidence_class', 'runtime', 'parameters')): findings.append({'code': 'duplicate-check-contract-conflict', 'check_id': identity})
            item['scopes'].append(report['scope'])
            item['references'].update(evidence_refs | set(check.get('inputs', [])) | {catalog_path.relative_to(root).as_posix(), str(Path(argv[1]).parent)} | {arg for arg in argv[2:] if coverage.safe_path(arg) and (root / arg).exists()})
    # Authoritative definitions follow the same transitive consumer graph as
    # executable source. Only prose may rely solely on portable process gates.
    repository_rules = catalog.get('repository_inputs', [])
    if not isinstance(repository_rules, list):
        findings.append({'code': 'repository-input-rule-invalid'}); repository_rules = []
    for rule in repository_rules:
        if isinstance(rule, dict) and coverage.strings(rule.get('inputs')) and coverage.strings(rule.get('checks')):
            covered.update(path for path in changed if any(below(consumer, ref) or below(ref, consumer) for consumer in closure([path], graph) for ref in rule['inputs']))
    non_applicable = []
    for path in changed:
        if path in covered: continue
        authoritative = metadata(root / path).get('kind') in {'schema', 'contract', 'deployment-contract', 'configuration', 'script', 'gate'}
        if (not authoritative and path.endswith('.md') and path.startswith(('.agentic/', 'docs/'))) or (path.startswith('commitLogs/') and path.endswith(('.md', '.json', '.yml', '.yaml', '.log', '.txt'))) or path == 'AGENTS.md':
            non_applicable.append({'path': path, 'reason': 'governance-or-session-input-covered-by-mandatory-metadata-and-process-gates'})
        else: findings.append({'code': 'changed-input-uncovered', 'path': path, 'state': 'present' if (root / path).exists() else 'deleted'})
    for rule in repository_rules:
        if not isinstance(rule, dict) or not coverage.strings(rule.get('inputs')) or not coverage.strings(rule.get('checks')):
            findings.append({'code': 'repository-input-rule-invalid'}); continue
        if not (args.all or any(below(path, ref) or below(ref, path) for path in consumers for ref in rule['inputs'])): continue
        for identity in rule['checks']:
            check = checks.get(identity)
            errors = validate_check(root, identity, check)
            findings += errors
            if errors: continue
            argv = tuple(check['argv'])
            if any('{' in arg or '}' in arg for arg in argv): findings.append({'code': 'repository-check-placeholder-invalid', 'check_id': identity}); continue
            key = identity + ':' + hashlib.sha256(json.dumps(argv).encode()).hexdigest()[:16]
            item = selected.setdefault(argv, {'check_id': identity, 'check_key': key, 'argv': list(argv), 'stage': check['stage'], 'effects': check['effects'], 'evidence_class': check['evidence_class'], 'scopes': [], 'references': set(), 'status': 'pending', 'runtime': check.get('runtime', {}), 'parameters': check.get('parameters', {}), 'applicability': check.get('applicability', {})})
            if any(item[field] != check.get(field, {}) for field in ('stage', 'effects', 'evidence_class', 'runtime', 'parameters')): findings.append({'code': 'duplicate-check-contract-conflict', 'check_id': identity})
            item['references'].update(upstream_closure(set(rule['inputs']) | set(check.get('inputs', [])) | {catalog_path.relative_to(root).as_posix(), str(Path(argv[1]).parent)}, graph))
    cache = None
    if args.execute_local or args.record_preparation or args.require_preparation:
        try: cache = LocalCache(root)
        except (ValueError, OSError) as error: findings.append({'code': 'local-cache-unavailable', 'detail': str(error)})
    results = sorted(selected.values(), key=lambda item: (STAGES[item['stage']], item['check_key']))
    runtime_identities: dict[str, dict] = {}
    def identity(item: dict) -> str:
        item['input_digest'] = fingerprint(root, item['references'])
        runtime = item['runtime']
        runtime_key = json.dumps(runtime, sort_keys=True)
        if item['stage'] == 'local':
            if runtime_key not in runtime_identities: runtime_identities[runtime_key] = runtime_identity(root, runtime)
            item['runtime_identity'] = runtime_identities[runtime_key]
        payload = {key: item.get(key) for key in ('input_digest', 'argv', 'effects', 'stage', 'evidence_class', 'runtime_identity', 'parameters', 'applicability')}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    for item in results:
        item['references'] = upstream_closure(item['references'] | set(item['runtime'].get('config_inputs', [])), graph)
        # The executable runner and catalog are part of every proof definition.
        item['references'].update({'scripts/repo/check-selection/script.py', 'scripts/repo/check-selection/local_cache.py'})
        try: item['evidence_key'] = identity(item)
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            item['input_digest'] = ''
            code = 'check-input-symlink-unsupported' if str(error).startswith('input-symlink:') else 'check-runtime-identity-unavailable'
            findings.append({'code': code, 'check_id': item['check_id'], 'detail': str(error)})
    if args.staged:
        # The hook must prove the bytes that would be committed. Unrelated
        # unstaged work remains outside this selected-input boundary.
        unstaged = set(git(root, 'diff', '--name-only', '--no-renames', '-z').split('\0')) - {''}
        untracked = set(git(root, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')) - {''}
        selected_inputs = {reference for item in results for reference in item['references']}
        for path in sorted(unstaged | untracked):
            if any(below(path, ref) or below(ref, path) for ref in selected_inputs):
                findings.append({'code': 'selected-input-not-staged', 'path': path})
    preparation_status = 'not-requested'
    if args.record_preparation:
        preparation_status = 'recorded-pending-validation'
    if args.require_preparation and results:
        preparation = cache.read_preparation() if cache else {}
        if not preparation:
            findings.append({'code': 'verification-preparation-missing'})
            preparation_status = 'missing'
        else:
            prepared = {(item['check_id'], item['evidence_key']) for item in preparation['checks']}
            mismatched = [item['check_id'] for item in results if (item['check_id'], item.get('evidence_key')) not in prepared]
            if mismatched:
                findings.append({'code': 'verification-preparation-inputs-changed', 'check_ids': sorted(mismatched)})
                preparation_status = 'inputs-changed'
            else:
                preparation_status = 'matched'
    execution_preflight_passed = not findings
    for item in results:
        item['source_revision'] = revision
        item['scopes'] = sorted(set(item['scopes']))
        required_now = STAGES[item['stage']] <= STAGES[args.stage]
        if execution_preflight_passed and item['stage'] == 'local':
            runtime_identities.clear()
            try: current_identity = identity(item)
            except (ValueError, OSError, subprocess.SubprocessError): current_identity = None
            if current_identity != item.get('evidence_key'):
                item['status'] = 'uncertain'
                item['references'] = sorted(item['references'])
                findings.append({'code': 'check-input-changed-before-execution', 'check_id': item['check_id']})
                continue
        proof = cache.read(item.get('evidence_key', 'invalid')) if cache and item['stage'] == 'local' and execution_preflight_passed else {}
        if proof:
            item.update(status='passed', exit_code=0, evidence_source='trusted-worktree-cache', executed_revision=proof.get('executed_revision', proof.get('source_revision')))
        elif not required_now: item['status'] = 'deferred'; item['reason'] = 'required-before-' + item['stage']
        elif args.execute_local and item['stage'] == 'local' and execution_preflight_passed:
            if cache:
                item['cache_invalidation_reasons'] = cache.invalidation_reasons(item)
            completed = subprocess.run(item['argv'], cwd=root, capture_output=True, text=True, check=False)
            item.update(status='passed' if completed.returncode == 0 else 'failed', exit_code=completed.returncode, evidence_source='local-runner', executed_revision=revision)
            # A check cannot qualify bytes that changed while it was executing.
            before = item['evidence_key']
            runtime_identities.clear()
            try: after = identity(item)
            except (ValueError, OSError, subprocess.SubprocessError): after = None
            if after != before:
                item['status'] = 'uncertain'
                findings.append({'code': 'check-input-changed-during-execution', 'check_id': item['check_id']})
            elif completed.returncode:
                findings.append({'code': 'required-check-failed', 'check_id': item['check_id']})
            elif cache: cache.save({**item, 'references': sorted(item['references'])})
        elif args.stage != 'local' or args.execute_local:
            findings.append({'code': 'required-proof-missing-or-stale' if item['stage'] == 'local' else 'required-proof-owned-by-stage-controller', 'check_id': item['check_id'], 'stage': item['stage']})
        item['references'] = sorted(item['references'])
    execution_summary = {
        'reused_check_ids': sorted(item['check_id'] for item in results if item.get('evidence_source') == 'trusted-worktree-cache'),
        'executed_check_ids': sorted(item['check_id'] for item in results if item.get('evidence_source') == 'local-runner'),
        'deferred_check_ids': sorted(item['check_id'] for item in results if item.get('status') == 'deferred'),
        'invalidated_checks': [
            {'check_id': item['check_id'], 'reasons': item['cache_invalidation_reasons']}
            for item in results if item.get('cache_invalidation_reasons') and item.get('cache_invalidation_reasons') != ['no-prior-successful-local-evidence']
        ],
    }
    report = {'schema': 'repo/check-selection-report/v1', 'stage': args.stage, 'verdict': 'gap' if findings else ('passed' if args.execute_local or args.stage != 'local' else 'planned'), 'source_revision': revision, 'changed_inputs': [{'path': path, 'state': 'present' if (root / path).exists() else 'deleted'} for path in changed], 'affected_consumers': sorted(consumers - set(changed) | {path for report in impacted for path in report['consumers']}), 'scopes': impacted, 'checks': results, 'execution_summary': execution_summary, 'non_applicable': non_applicable, 'findings': findings, 'limitations': ['Declared inputs, metadata consumers and workspace dependencies define supported impact; unmapped authoritative definitions remain gaps.', 'Local cache trusts same-user private worktree Git metadata and declared runtime/config/environment inputs; it is not portable or live acceptance evidence.', 'Imported reports cannot qualify checks. Only unchanged successful local runner results are reused; all external proof remains with its owning stage controller.']}
    if args.record_preparation and cache and not findings:
        report['preparation_report_path'] = cache.save_preparation({
            'changed_inputs': report['changed_inputs'],
            'checks': [{'check_id': item['check_id'], 'evidence_key': item.get('evidence_key'), 'stage': item['stage']} for item in results],
        })
        preparation_status = 'recorded'
    report['preparation_status'] = preparation_status
    if args.evidence: report['evidence_import_status'] = 'rejected-untrusted-report'
    if cache:
        report['local_report_path'] = str(cache.directory / 'latest-report.json')
        cache.save_report(report)
    return report



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
    parser.add_argument('--record-preparation', action='store_true')
    parser.add_argument('--require-preparation', action='store_true')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.record_preparation and args.require_preparation:
        parser.error('--record-preparation and --require-preparation are mutually exclusive')
    if args.require_preparation and not args.staged:
        parser.error('--require-preparation requires --staged')
    try: report = plan(args)
    except (OSError, ValueError, TypeError, ImportError, subprocess.SubprocessError) as error:
        report = {'schema': 'repo/check-selection-report/v1', 'verdict': 'gap', 'findings': [{'code': 'selection-input-or-runtime-invalid', 'error_type': type(error).__name__}]}
    print(json.dumps(report, sort_keys=True))
    return 1 if report['findings'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
