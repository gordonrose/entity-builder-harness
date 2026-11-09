#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.compiler.check-selection
#   version: 8
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-11-09"
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
import math
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts/repo/check-selection'))
import execution_policy
from local_cache import (LocalCache, LocalCheckError, RuntimeIdentityWindow, runtime_identity,
                         valid_node_package, local_check_diagnostic, CACHE_INVALIDATION_REASONS, NO_PRIOR_EVIDENCE, TOOLS)
sys.path.insert(0, str(ROOT / 'scripts/01.harness/artifact-metadata'))
from header_discovery import HeaderError, parse_header_text, repository_paths
spec = importlib.util.spec_from_file_location('declaration_coverage', ROOT / 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py')
assert spec and spec.loader
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)
BOUNDARIES = {'commit': 0, 'integration': 1}
STAGES = {'local': 0, 'package': 1, 'deploy': 2, 'acceptance': 3}
CLASSES = {'local': {'static', 'local-runtime'}, 'package': {'container-qualification', 'ci'}, 'deploy': {'live'}, 'acceptance': {'live'}}
LOCAL_EFFECTS = {'read-only', 'writes-files'}
PLACEHOLDERS = {'{scope_contract}', '{workload_binding}', '{target_root}', '{program_contract}'}


def safe_nested_execution_summary(value: object, allowed_ids: set[str]) -> dict:
    """Project the existing summary as bounded observation, never proof."""
    lists = {'selected_check_ids', 'reused_check_ids', 'executed_check_ids', 'deferred_check_ids'}
    timings = {'planning_seconds', 'fingerprinting_seconds', 'runtime_identity_seconds',
               'receipt_validation_seconds', 'command_execution_seconds', 'other_seconds'}
    reasons = CACHE_INVALIDATION_REASONS
    fields = lists | {'elapsed_seconds', 'execution_seconds', 'timings', 'invalidated_checks'}
    unavailable = {'unavailable': True}
    if type(value) is not dict or set(value) != fields:
        return unavailable
    copied = {}
    for field in lists:
        items = value[field]
        if type(items) is not list or len(items) > len(allowed_ids) or any(type(item) is not str or item not in allowed_ids for item in items) or len(set(items)) != len(items):
            return unavailable
        copied[field] = list(items)
    selected = set(copied['selected_check_ids'])
    observed = [set(copied[field]) for field in ('reused_check_ids', 'executed_check_ids', 'deferred_check_ids')]
    if any(not items <= selected for items in observed) or any(observed[left] & observed[right] for left, right in ((0, 1), (0, 2), (1, 2))):
        return unavailable
    def seconds(item):
        return type(item) in {int, float} and 0 <= item <= 9007199254740991 and math.isfinite(item)
    for field in ('elapsed_seconds', 'execution_seconds'):
        if not seconds(value[field]):
            return unavailable
        copied[field] = value[field]
    measured = value['timings']
    if type(measured) is not dict or set(measured) != timings or not all(seconds(item) for item in measured.values()):
        return unavailable
    copied['timings'] = dict(measured)
    invalidated = value['invalidated_checks']
    if type(invalidated) is not list or len(invalidated) > len(selected):
        return unavailable
    copied['invalidated_checks'] = []
    seen = set()
    for entry in invalidated:
        if type(entry) is not dict or set(entry) != {'check_id', 'reasons'} or type(entry['check_id']) is not str or entry['check_id'] not in selected or entry['check_id'] in seen:
            return unavailable
        causes = entry['reasons']
        if type(causes) is not list or not causes or len(causes) > len(reasons) or any(type(cause) is not str or cause not in reasons for cause in causes) or len(set(causes)) != len(causes):
            return unavailable
        seen.add(entry['check_id'])
        copied['invalidated_checks'].append({'check_id': entry['check_id'], 'reasons': list(causes)})
    return copied


def safe_runtime_error_type(error: BaseException) -> str:
    """Class names from arbitrary subclasses are not diagnostic vocabulary."""
    for known in (LocalCheckError, InputSymlinkError, OSError, FileNotFoundError, PermissionError, IsADirectoryError, NotADirectoryError,
                  ValueError, TypeError, ImportError, ModuleNotFoundError, UnicodeError,
                  UnicodeDecodeError, UnicodeEncodeError, UnicodeTranslateError, json.JSONDecodeError,
                  subprocess.SubprocessError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        if type(error) is known:
            return known.__name__
    return 'unknown-runtime-error'


class InputSymlinkError(ValueError):
    pass


def verification_dependencies(checks: dict, seeds: list[str], context: list[str] | None) -> tuple[dict[str, set[str]], list[dict]]:
    """Catalog is the only aggregate/prerequisite membership authority."""
    dependencies: dict[str, set[str]] = {}
    findings = []
    visiting = set()
    def visit(identity, inherited=()):
        check = checks.get(identity)
        if not isinstance(check, dict):
            findings.append({'code': 'verification-dependency-unknown', 'check_id': identity}); return
        if identity in visiting:
            findings.append({'code': 'verification-dependency-cycle', 'check_id': identity}); return
        members = check.get('members', [])
        rules = check.get('focused_prerequisites', [])
        if not isinstance(members, list) or not all(isinstance(member, str) for member in members) or len(set(members)) != len(members) or not isinstance(rules, list):
            findings.append({'code': 'verification-dependency-contract-invalid', 'check_id': identity}); return
        focused = set(inherited)
        if (rules or members) and context is None:
            findings.append({'code': 'verification-task-context-required', 'check_id': identity})
        for rule in rules:
            if not isinstance(rule, dict) or not coverage.strings(rule.get('inputs')) or not coverage.strings(rule.get('checks')):
                findings.append({'code': 'verification-prerequisite-contract-invalid', 'check_id': identity}); continue
            if context is not None and any(below(path, ref) or below(ref, path) for path in context for ref in rule['inputs']):
                focused.update(rule['checks'])
        required = set(members) | focused
        prior = dependencies.get(identity, set())
        if identity in dependencies and required <= prior: return
        dependencies[identity] = prior | required
        visiting.add(identity)
        for child in sorted(required):
            other = checks.get(child)
            if isinstance(other, dict) and (STAGES.get(other.get('stage'), 999) > STAGES.get(check.get('stage'), -1) or BOUNDARIES.get(other.get('boundary', 'commit'), 999) > BOUNDARIES.get(check.get('boundary', 'commit'), -1) or not (set(other.get('effects', [])) - {'read-only'}) <= set(check.get('effects', []))):
                findings.append({'code': 'verification-dependency-boundary-invalid', 'check_id': identity, 'dependency': child}); continue
            visit(child, focused if child in members and child not in focused else ())
        visiting.remove(identity)
    for identity in seeds: visit(identity)
    return dependencies, findings


def dependency_order(items: list[dict], dependencies: dict[str, set[str]]) -> list[dict]:
    by_id = {identity: item for item in items for identity in item['catalog_entries']}
    ordered, visiting, finished = [], set(), set()
    def visit(item):
        key = item['check_key']
        if key in finished or key in visiting: return
        visiting.add(key)
        for identity in sorted({child for alias in item['catalog_entries'] for child in dependencies.get(alias, set())}):
            if identity in by_id: visit(by_id[identity])
        visiting.remove(key); finished.add(key); ordered.append(item)
    for item in sorted(items, key=lambda value: (STAGES[value['stage']], value['check_key'])): visit(item)
    return ordered


def below(path: str, prefix: str) -> bool:
    prefix = prefix.rstrip('/')
    return path == prefix or path.startswith(prefix + '/')


def git(root: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout


def metadata(path: Path) -> dict[str, Any]:
    # Artifact headers are required to be leading and deliberately small.
    # Selection needs their dependency declarations, not multi-megabyte
    # historical bodies.  Keep the read bounded so retained evidence and long
    # teaching material cannot turn a changed-file plan into an I/O sweep.
    try:
        with path.open(encoding='utf-8') as source:
            value = parse_header_text(source.read(64 * 1024))
        result = value.get('agentic-artifact', value.get('agentic-script', {}))
        return result if isinstance(result, dict) else {}
    except (OSError, UnicodeError, HeaderError):
        return {}


def governance_prose(root: Path, path: str) -> bool:
    authoritative = metadata(root / path).get('kind') in {'schema', 'contract', 'deployment-contract', 'configuration', 'script', 'gate'}
    parts = path.split('/')
    skill_instruction = len(parts) == 4 and parts[:2] == ['.agents', 'skills'] and bool(parts[2]) and parts[3] == 'SKILL.md'
    return not authoritative and ((path.endswith('.md') and path.startswith(('.agentic/', 'docs/'))) or skill_instruction)


def dormant_roots(root: Path, catalog: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    roots = catalog.get('dormant_impact_roots', [])
    if not isinstance(roots, list) or not all(isinstance(item, str) and item and coverage.safe_path(item) and (root / item).is_dir() for item in roots):
        return [], [{'code': 'dormant-impact-roots-invalid'}]
    if len(set(roots)) != len(roots):
        return [], [{'code': 'dormant-impact-roots-duplicate'}]
    return roots, []


def consumer_graph(root: Path, paths: list[str], dormant: list[str] | tuple[str, ...] = (), *, include_metadata: bool = True) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    headers = {
        path: metadata(root / path)
        for path in paths
        if coverage.within(root, path) is not None
        and not below(path, 'commitLogs')
        and path.endswith(('.md', '.yml', '.yaml', '.py', '.sh', '.ts', '.mjs'))
    } if include_metadata else {}
    identities = {meta.get('id'): path for path, meta in headers.items() if isinstance(meta.get('id'), str)}
    for path, meta in headers.items():
        for consumer in meta.get('used_by', []) if isinstance(meta.get('used_by'), list) else []:
            if isinstance(consumer, dict):
                target = consumer.get('path') or identities.get(consumer.get('id'))
                if isinstance(target, str) and coverage.safe_path(target) and not any(below(path, dormant_root) or below(target, dormant_root) for dormant_root in dormant): graph.setdefault(path, set()).add(target)
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
    # Discover physical scope roots first. An index cannot prove its own completeness.
    roots = set(base.glob('*/targets/*/20-scopes'))
    roots.update(path.parent.parent for path in base.glob('*/targets/*/20-scopes/*/00-declaration'))
    for scope_root in sorted(roots):
        index_path = scope_root / 'scope-index.yml'
        if not index_path.is_file():
            findings.append({'code': 'scope-inventory-missing', 'path': index_path.relative_to(root).as_posix()})
            continue
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
    if check.get('boundary', 'commit') not in BOUNDARIES: return fail('check-boundary-invalid')
    if not isinstance(check.get('scope_inputs', True), bool): return fail('check-input-contract-invalid')
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
    if check.get('scope_inputs') is False and not coverage.strings(inputs): return fail('check-input-contract-missing')
    if not coverage.strings(inputs, empty=True) or any(coverage.within(root, value) is None or not (root / value).exists() for value in inputs): return fail('check-input-missing')
    if check.get('members'):
        branch = check.get('aggregate_branch')
        text = command.read_text()
        expected = 'exec bash scripts/repo/check-selection/script.sh --aggregate-members ' + check_id + ' --execute-local --json'
        if branch == 'default':
            match = re.search(r'if \[ "\$#" -eq 0 \]; then\n(.*?)\nfi', text, re.S)
            valid = match is not None and match.group(1).strip() == expected
        elif branch == 'unit-base':
            valid = ('  base) ' + expected + ' ;;') in text.splitlines()
        elif branch == 'whole':
            body = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
            valid = body == ['set -euo pipefail', 'ROOT="$(git rev-parse --show-toplevel)"', 'cd "$ROOT"', expected]
        else: valid = False
        if not valid: return fail('verification-aggregate-wrapper-invalid')
    return []


def fingerprint(root: Path, refs: set[str], *, exclude: set[str] | frozenset[str] = frozenset()) -> str:
    digest = hashlib.sha256()
    for ref in sorted(refs):
        if ref in exclude: continue
        path = coverage.within(root, ref)
        if path is None: digest.update(('invalid:' + ref).encode()); continue
        entries = sorted(item for item in path.rglob('*') if not any(part in {'node_modules', '__pycache__', '.git', '.cache'} for part in item.relative_to(path).parts)) if path.is_dir() else [path]
        for item in entries:
            if item.is_symlink(): raise InputSymlinkError('input-symlink:' + item.relative_to(root).as_posix())
        files = [item for item in entries if item.is_file()] if path.is_dir() else entries
        for item in files:
            if item.relative_to(root).as_posix() in exclude: continue
            try:
                content = item.read_bytes()
                mode = item.stat().st_mode & 0o777
            except OSError:
                content, mode = b'<missing>', None
            digest.update(json.dumps([item.relative_to(root).as_posix(), mode, len(content)]).encode())
            digest.update(content)
    return digest.hexdigest()


def changed_catalog_checks(root: Path, catalog_ref: str, current: dict[str, Any], baseline: str = 'HEAD') -> set[str]:
    """Return only check identities whose executable contract changed.

    A catalog is shared selection authority.  A change to one bound check must
    reselect its consumers, but it must not turn every unrelated legacy
    declaration into a prerequisite for a focused change.
    """
    try:
        prior = yaml.safe_load(git(root, 'show', baseline + ':' + catalog_ref))
    except (subprocess.SubprocessError, yaml.YAMLError):
        return set()
    before = prior.get('checks', {}) if isinstance(prior, dict) else {}
    after = current.get('checks', {}) if isinstance(current, dict) else {}
    if not isinstance(before, dict) or not isinstance(after, dict):
        return set()
    return {
        identity for identity in set(before) | set(after)
        if json.dumps(before.get(identity), sort_keys=True) != json.dumps(after.get(identity), sort_keys=True)
    }


def plan(args: argparse.Namespace) -> dict[str, Any]:
    started = time.monotonic()
    timings = {'planning_seconds': 0.0, 'fingerprinting_seconds': 0.0, 'runtime_identity_seconds': 0.0, 'receipt_validation_seconds': 0.0, 'command_execution_seconds': 0.0}
    root = args.root.resolve()
    boundary = getattr(args, 'boundary', 'integration')
    development = getattr(args, 'development', False)
    record_preparation = getattr(args, 'record_preparation', False)
    require_preparation = getattr(args, 'require_preparation', False)
    catalog_path = args.catalog or root / 'scripts/repo/check-selection/checks.yml'
    catalog_ref = catalog_path.relative_to(root).as_posix()
    def source_fingerprint(references):
        phase_started = time.monotonic()
        try: return fingerprint(root, references)
        finally: timings['fingerprinting_seconds'] += time.monotonic() - phase_started
    # Catalog authority is checked fresh for each invocation. Its raw bytes
    # guard planning/execution races, independently of reusable proof identity.
    catalog_snapshot = source_fingerprint({catalog_ref})
    catalog_stable = True
    def catalog_unchanged() -> bool:
        nonlocal catalog_stable
        try: catalog_stable = catalog_stable and source_fingerprint({catalog_ref}) == catalog_snapshot
        except (ValueError, OSError): catalog_stable = False
        return catalog_stable
    catalog = coverage.document(catalog_path)
    checks = catalog.get('checks', {})
    findings: list[dict[str, str]] = []
    if catalog.get('schema') != 'repo/check-catalog/v1' or not isinstance(checks, dict): checks = {}; findings.append({'code': 'check-catalog-invalid'})
    for check_id, check in checks.items():
        if isinstance(check, dict): findings += execution_policy.validate_feedback(check_id, check)
    if development and (not args.paths or args.staged or args.all or getattr(args, 'ci', False)
                        or getattr(args, 'checks', None) is not None or getattr(args, 'aggregate_members', None)
                        or args.stage != 'local' or boundary != 'integration' or record_preparation or require_preparation):
        findings.append({'code': 'development-selection-context-invalid'})
    all_rule_inputs = [ref for check in checks.values() if isinstance(check, dict) for rule in check.get('focused_prerequisites', []) if isinstance(rule, dict) for ref in rule.get('inputs', []) if isinstance(ref, str)]
    _, graph_findings = verification_dependencies(checks, sorted(checks), all_rule_inputs)
    findings += graph_findings
    for identity, check in checks.items():
        if isinstance(check, dict) and check.get('members'): findings += validate_check(root, identity, check)
    explicit_checks = getattr(args, 'checks', None)
    if explicit_checks is not None and not coverage.strings(explicit_checks):
        findings.append({'code': 'explicit-check-selection-invalid'})
        explicit_checks = []
    changed = sorted(set(args.paths or []))
    if args.staged: changed = sorted(set(git(root, 'diff', '--cached', '--name-only', '--no-renames', '-z').split('\0')) - {''})
    if any(not coverage.safe_path(path) for path in changed): findings.append({'code': 'changed-path-invalid'})
    catalog_check_changes = changed_catalog_checks(root, catalog_ref, catalog, getattr(args, 'comparison_base', 'HEAD')) if catalog_ref in changed else set()
    paths = repository_paths(root)
    dormant, dormant_findings = dormant_roots(root, catalog)
    findings += dormant_findings
    # Incidental maintenance prose does not reactivate a dormant subsystem.
    # Authoritative definitions, executable inputs and explicit checks still do.
    # Missing files cannot be classified from a header and remain conservative.
    dormant_changed = any(
        any(below(path, owner) for owner in dormant)
        and (not (root / path).is_file() or not governance_prose(root, path))
        for path in changed
    )
    graph = consumer_graph(root, paths, dormant)
    proof_graph = consumer_graph(root, paths, dormant, include_metadata=False)
    # This graph is immutable for one plan. Cache traversals only within that
    # invocation; later plans must observe new metadata and dependency edges.
    downstream_cache: dict[frozenset[str], frozenset[str]] = {}
    upstream_cache: dict[tuple[frozenset[str], bool], frozenset[str]] = {}
    def downstream(inputs) -> set[str]:
        key = frozenset(inputs)
        if key not in downstream_cache:
            downstream_cache[key] = frozenset(closure(list(key), graph))
        return set(downstream_cache[key])
    def upstream(inputs, *, explicit: bool = False) -> set[str]:
        key = (frozenset(inputs), explicit)
        if key not in upstream_cache:
            upstream_cache[key] = frozenset(upstream_closure(set(inputs), proof_graph if explicit else graph))
        # Callers extend references. Never expose the cached set for mutation.
        return set(upstream_cache[key])
    consumers = downstream(changed)
    scopes, discovery_gaps = discover(root)
    findings += discovery_gaps
    inventory_spec = importlib.util.spec_from_file_location('delivery_inventory', ROOT / 'scripts/04.deploy/inventory-deploy-control/delivery_inventory.py')
    assert inventory_spec and inventory_spec.loader
    inventory = importlib.util.module_from_spec(inventory_spec)
    inventory_spec.loader.exec_module(inventory)
    delivery = inventory.report(root, source_revision=git(root, 'rev-parse', 'HEAD').strip(), routes_only=True)
    # Delivery inventory is repository-wide source coverage.  Its independent
    # CI route owns unrelated legacy gaps; a focused change plan must not
    # report another target's pre-existing gap as though the selected change
    # caused it.  Attach only findings whose declared subject overlaps the
    # requested input.  `--all` deliberately retains the full census verdict.
    def delivery_finding_is_relevant(item: dict[str, Any]) -> bool:
        subject = item.get('path')
        if not isinstance(subject, str) or not coverage.safe_path(subject):
            return args.all
        return args.all or any(below(path, subject) or below(subject, path) for path in changed)
    findings.extend(item for item in delivery['findings'] if delivery_finding_is_relevant(item) and item not in findings)
    # The earlier target-profile declarations remain supported. Discover them
    # from the physical census and select their catalogued proofs through the
    # same runner/cache; they do not require a second registry or special CI.
    known = {item['contract'].resolve() for item in scopes}
    for route in delivery['routes']:
        contract_path = root / route['declaration']
        if contract_path.resolve() in known: continue
        data = coverage.document(contract_path)
        if data.get('schema') == 'deploy/declaration-contract/v1':
            scopes.append({'contract': contract_path, 'index': root / route['binding'], 'id': route['id']})
    selected: dict[tuple[str, ...], dict[str, Any]] = {}
    def bind_catalog_entry(item: dict[str, Any], identity: str, check: dict[str, Any], argv: tuple[str, ...]) -> None:
        # Every selected alias owns a complete proof definition, including
        # description and future fields. Deduplication must not discard one.
        item.setdefault('catalog_entries', {})[identity] = check
        explicit = set(check.get('inputs', [])) | set(check.get('runtime', {}).get('config_inputs', []))
        explicit.update(arg for arg in argv[2:] if coverage.safe_path(arg) and (root / arg).exists())
        # A consumed path can also use --option=value, ./relative, or an
        # absolute spelling. Recognize only this known catalog (or its input
        # directory), without inferring arbitrary command option semantics.
        catalog_argument = False
        for arg in argv[2:]:
            value = arg.partition('=')[2] if arg.startswith('-') and '=' in arg else arg
            if not value: continue
            try: candidate = (root / value).resolve()
            except (OSError, RuntimeError): continue
            if candidate == catalog_path.resolve() or catalog_path.resolve().is_relative_to(candidate):
                catalog_argument = True
        item['catalog_input'] = item.get('catalog_input', False) or catalog_argument or any(below(catalog_ref, ref) for ref in explicit)
    impacted: list[dict[str, Any]] = []
    covered: set[str] = set()
    revision = git(root, 'rev-parse', 'HEAD').strip()
    for scope in scopes:
        # Explicit unit verification is not impact discovery. Never infer a
        # scope binding for a requested command with unresolved placeholders.
        if explicit_checks is not None: continue
        contract = scope['contract']
        contract_ref = contract.relative_to(root).as_posix()
        dormant_owner = next((owner for owner in dormant if below(contract_ref, owner)), None)
        if dormant_owner and not args.all and not dormant_changed:
            continue
        # Route parsers are qualified by selected target/declaration gates.
        report = coverage.inspect(contract, root, catalog, probe_commands=False)
        refs = set(report['references']) | set(report['inputs'])
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
            runtime = check.get('runtime')
            configs = runtime.get('config_inputs', []) if isinstance(runtime, dict) else []
            if isinstance(configs, list): check_inputs.update(value for value in configs if isinstance(value, str))
        triggers = refs | proof_dirs | check_inputs
        check_contract_changed = bool(set(report['required_checks']) & catalog_check_changes)
        if not (args.all or check_contract_changed or any(below(path, ref) or below(ref, path) for path in consumers for ref in triggers)): continue
        for path in changed:
            if any(below(path, ref) or below(ref, path) for ref in triggers) or downstream([path]) & consumers & refs: covered.add(path)
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
            bind_catalog_entry(item, identity, check, argv)
            if item.get('boundary', check.get('boundary', 'commit')) != check.get('boundary', 'commit'): findings.append({'code': 'duplicate-check-contract-conflict', 'check_id': identity})
            item['scopes'].append(report['scope'])
            # Scope impact selects obligations. Only checks declaring that they
            # consume the scope inherit its references in their proof identity.
            scope_refs = refs if check.get('scope_inputs', True) else set()
            implementation = argv[1] if check.get('scope_inputs') is False else str(Path(argv[1]).parent)
            item['references'].update(scope_refs | set(check.get('inputs', [])) | {implementation} | ({check['capability']} if 'capability' in check else set()) | {arg for arg in argv[2:] if coverage.safe_path(arg) and (root / arg).exists()})
            item['boundary'] = check.get('boundary', 'commit')
            item['scope_inputs'] = item.get('scope_inputs', False) or check.get('scope_inputs', True)
    # Authoritative definitions follow the same transitive consumer graph as
    # executable source. Only prose may rely solely on portable process gates.
    repository_rules = catalog.get('repository_inputs', [])
    diagnostic_inputs = []
    diagnostic_bindings = {}
    diagnostic_owner = None
    reviews_ref = 'scripts/repo/diagnostic-coverage/reviews.v1.json'
    if not isinstance(repository_rules, list):
        findings.append({'code': 'repository-input-rule-invalid'}); repository_rules = []
    # Ordinary code has diagnostic obligations even without a deployment scope.
    # Reviews name registered local checks; they never introduce executable argv.
    if 'diagnostic-adoption' in checks:
        try:
            diagnostic_spec = importlib.util.spec_from_file_location('diagnostic_adoption', root / 'scripts/repo/diagnostic-coverage/script.py')
            assert diagnostic_spec and diagnostic_spec.loader
            diagnostic_adoption = importlib.util.module_from_spec(diagnostic_spec)
            diagnostic_spec.loader.exec_module(diagnostic_adoption)
            diagnostic_owner = diagnostic_adoption
            diagnostic_bindings = diagnostic_adoption.review_bindings(root)
            if any(identity not in checks or checks[identity].get('stage') != 'local' for identity in diagnostic_bindings):
                findings.append({'code': 'diagnostic-review-check-unregistered'})
            if explicit_checks is None:
                repository_rules = repository_rules + diagnostic_adoption.review_rules(root, comparison_base=getattr(args, 'comparison_base', 'HEAD'), ledger_changed=reviews_ref in changed)
            if explicit_checks is None or 'diagnostic-adoption' in explicit_checks: diagnostic_inputs = diagnostic_adoption.proof_inputs(root)
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            findings.append({'code': 'diagnostic-adoption-selection-invalid'})
    if explicit_checks is not None:
        repository_rules = [{'inputs': [catalog_ref], 'checks': explicit_checks}] if explicit_checks else []
    def rule_triggered(rule):
        exclusions = rule.get('exclude_inputs', [])
        if not coverage.strings(exclusions, empty=True) or any(not coverage.safe_path(path) for path in exclusions):
            findings.append({'code': 'repository-input-exclusion-invalid'}); return False
        relevant = {path for path in consumers if not any(below(path, excluded) for excluded in exclusions)}
        return explicit_checks is not None or args.all or any(below(path, ref) or below(ref, path) for path in relevant for ref in rule['inputs'])
    task_context = (paths if args.all else changed) if explicit_checks is None else getattr(args, 'task_paths', None)
    preparation_context = None
    parent_binding = None
    if explicit_checks is not None:
        try: preparation_context = LocalCache(root, create=False).read_preparation()
        except (ValueError, OSError): preparation_context = {}
        inputs = preparation_context.get('changed_inputs', [])
        parent_token = os.environ.get('REPO_CHECK_PARENT_BINDING')
        if parent_token and getattr(args, 'aggregate_members', None):
            candidate = preparation_context.get('active_execution', {})
            if candidate.get('token') != parent_token or candidate.get('aggregate_owner') != args.aggregate_members or candidate.get('catalog_digest') != catalog_snapshot or not LocalCache.execution_live(candidate):
                findings.append({'code': 'verification-parent-context-invalid'})
            else:
                parent_binding = candidate
                task_context = candidate.get('task_paths')
        if task_context is None and inputs and all(isinstance(entry, dict) and coverage.safe_path(entry.get('path', '')) for entry in inputs):
            task_context = [entry['path'] for entry in inputs]
    if task_context is not None and (not isinstance(task_context, list) or not task_context or any(not isinstance(path, str) or not coverage.safe_path(path) for path in task_context)):
        findings.append({'code': 'verification-task-context-invalid'})
        task_context = None
    seeds = {identity for item in selected.values() for identity in item['catalog_entries']}
    aggregate_owner = getattr(args, 'aggregate_members', None)
    if aggregate_owner: seeds.add(aggregate_owner)
    for rule in repository_rules:
        if isinstance(rule, dict) and coverage.strings(rule.get('inputs')) and coverage.strings(rule.get('checks')):
            if rule_triggered(rule): seeds.update(rule['checks'])
            seeds.update(set(rule['checks']) & catalog_check_changes)
    dependency_context = sorted(downstream(task_context)) if task_context is not None else None
    dependencies, dependency_findings = verification_dependencies(checks, sorted(seeds), dependency_context)
    findings += dependency_findings
    already_bound = {identity for item in selected.values() for identity in item['catalog_entries']}
    dependency_ids = sorted(set(dependencies) - already_bound - ({aggregate_owner} if aggregate_owner else set()))
    if dependency_ids: repository_rules = repository_rules + [{'inputs': [catalog_ref], 'checks': dependency_ids, 'dependency_selection': True}]
    for rule in repository_rules:
        if isinstance(rule, dict) and coverage.strings(rule.get('inputs')) and coverage.strings(rule.get('checks')):
            covered.update(path for path in changed if any(below(consumer, ref) or below(ref, consumer) for consumer in downstream([path]) for ref in rule['inputs']))
    non_applicable = []
    for path in changed:
        if path in covered: continue
        if governance_prose(root, path) or (path.startswith('commitLogs/') and path.endswith(('.md', '.json', '.yml', '.yaml', '.log', '.txt', '.stderr', '.stdout'))) or path == 'AGENTS.md':
            non_applicable.append({'path': path, 'reason': 'governance-or-session-input-covered-by-mandatory-metadata-and-process-gates'})
        else: findings.append({'code': 'changed-input-uncovered', 'path': path, 'state': 'present' if (root / path).exists() else 'deleted'})
    for rule in repository_rules:
        if not isinstance(rule, dict) or not coverage.strings(rule.get('inputs')) or not coverage.strings(rule.get('checks')):
            findings.append({'code': 'repository-input-rule-invalid'}); continue
        triggered = rule.get('dependency_selection', False) or rule_triggered(rule)
        for identity in rule['checks']:
            if not triggered and identity not in catalog_check_changes: continue
            check = checks.get(identity)
            command = check.get('argv', [None, None])[1] if isinstance(check, dict) and isinstance(check.get('argv'), list) and len(check['argv']) > 1 else None
            if explicit_checks is None and isinstance(command, str) and any(below(command, owner) for owner in dormant) and not args.all and not dormant_changed:
                continue
            errors = validate_check(root, identity, check)
            findings += errors
            if errors: continue
            argv = tuple(check['argv'])
            if any('{' in arg or '}' in arg for arg in argv): findings.append({'code': 'repository-check-placeholder-invalid', 'check_id': identity}); continue
            key = identity + ':' + hashlib.sha256(json.dumps(argv).encode()).hexdigest()[:16]
            item = selected.setdefault(argv, {'check_id': identity, 'check_key': key, 'argv': list(argv), 'stage': check['stage'], 'effects': check['effects'], 'evidence_class': check['evidence_class'], 'scopes': [], 'references': set(), 'status': 'pending', 'runtime': check.get('runtime', {}), 'parameters': check.get('parameters', {}), 'applicability': check.get('applicability', {})})
            if any(item[field] != check.get(field, {}) for field in ('stage', 'effects', 'evidence_class', 'runtime', 'parameters')): findings.append({'code': 'duplicate-check-contract-conflict', 'check_id': identity})
            bind_catalog_entry(item, identity, check, argv)
            if item.get('boundary', check.get('boundary', 'commit')) != check.get('boundary', 'commit'): findings.append({'code': 'duplicate-check-contract-conflict', 'check_id': identity})
            # Mapping triggers are selection authority, not consumed inputs.
            implementation = argv[1] if check.get('scope_inputs') is False else str(Path(argv[1]).parent)
            item['references'].update(set(check.get('inputs', [])) | {implementation} | ({check['capability']} if 'capability' in check else set()) | {arg for arg in argv[2:] if coverage.safe_path(arg) and (root / arg).exists()})
            if identity == 'diagnostic-adoption': item['references'].update(diagnostic_inputs)
            item['boundary'] = check.get('boundary', 'commit')
            item['scope_inputs'] = item.get('scope_inputs', False) or check.get('scope_inputs', True)
    cache = None
    reuse_cache = None
    if args.execute_local or record_preparation or require_preparation:
        try: cache = LocalCache(root)
        except (ValueError, OSError) as error: findings.append({'code': 'local-cache-unavailable', **local_check_diagnostic(error)})
    reuse_source = getattr(args, 'reuse_from_worktree', None)
    if reuse_source is not None:
        try: reuse_cache = LocalCache.registered_source(root, Path(reuse_source))
        except (ValueError, OSError, subprocess.SubprocessError) as error: findings.append({'code': 'reuse-worktree-unavailable', **local_check_diagnostic(error)})
    results = dependency_order(list(selected.values()), dependencies)
    dependency_references = {child for values in dependencies.values() for child in values}
    for identity in dependency_references:
        instances = [item for item in results if identity in item['catalog_entries']]
        if len(instances) > 1: findings.append({'code': 'verification-dependency-instance-ambiguous', 'check_id': identity})
    by_identity = {identity: item for item in results for identity in item['catalog_entries']}
    # A caller's prerequisites order a member but do not change that member's
    # command proof. Otherwise a standalone focused receipt cannot be reused
    # when the same unit appears inside a conditional broad aggregate.
    proof_dependencies = {
        identity: verification_dependencies(checks, [identity], dependency_context)[0].get(identity, set())
        for identity in dependencies
    }
    for item in results:
        item['review_bindings'] = {alias: diagnostic_bindings.get(alias, []) for alias in item['catalog_entries'] if alias in diagnostic_bindings}
        item['dependency_ids'] = sorted({child for alias in item['catalog_entries'] for child in dependencies.get(alias, set())})
        item['proof_dependency_ids'] = sorted({child for alias in item['catalog_entries'] for child in proof_dependencies.get(alias, set())})
        def descendant_contracts(identity, seen, graph):
            for child in graph.get(identity, set()):
                if child not in seen and child in checks:
                    seen[child] = checks[child]
                    descendant_contracts(child, seen, graph)
            return seen
        item['dependency_contracts'] = {}
        item['scheduling_contracts'] = {}
        for alias in item['catalog_entries']:
            descendant_contracts(alias, item['dependency_contracts'], proof_dependencies)
            descendant_contracts(alias, item['scheduling_contracts'], dependencies)
        if len(item['catalog_entries']) > 1 and any(entry.get('members') for entry in item['catalog_entries'].values()):
            findings.append({'code': 'verification-aggregate-alias-ambiguous', 'check_id': item['check_id']})
    def required(item: dict) -> bool:
        return (STAGES[item['stage']] <= STAGES[args.stage] and BOUNDARIES[item['boundary']] <= BOUNDARIES[boundary]
                and (not development or execution_policy.development_check(item)))
    runtime_identities: dict[str, dict] = {}
    runtime_window = RuntimeIdentityWindow(root)
    def reset_runtime_identities() -> None:
        runtime_identities.clear()
        runtime_window.clear()
    def identity(item: dict) -> str:
        phase_started = time.monotonic()
        if diagnostic_owner:
            current_reviews = diagnostic_owner.review_bindings(root)
            item['review_bindings'] = {alias: current_reviews[alias] for alias in item['catalog_entries'] if alias in current_reviews}
        excluded = set() if item['catalog_input'] else {catalog_ref}
        if item['review_bindings'] and 'diagnostic-adoption' not in item['catalog_entries']: excluded.add(reviews_ref)
        item['input_digest'] = fingerprint(root, item['references'], exclude=excluded)
        item['dependency_preparation_keys'] = {child: by_identity[child].get('preparation_key') for child in item['proof_dependency_ids'] if child in by_identity}
        item['dependency_evidence_keys'] = {child: by_identity[child].get('evidence_key') for child in item['proof_dependency_ids'] if child in by_identity}
        timings['fingerprinting_seconds'] += time.monotonic() - phase_started
        runtime = item['runtime']
        runtime_key = json.dumps(runtime, sort_keys=True)
        if item['stage'] == 'local' and required(item):
            if runtime_key not in runtime_identities:
                phase_started = time.monotonic()
                runtime_identities[runtime_key] = runtime_identity(root, runtime, window=runtime_window)
                timings['runtime_identity_seconds'] += time.monotonic() - phase_started
            item['runtime_identity'] = runtime_identities[runtime_key]
        preparation = {key: item.get(key) for key in ('input_digest', 'argv', 'effects', 'stage', 'boundary', 'evidence_class', 'runtime', 'parameters', 'applicability', 'catalog_entries', 'dependency_contracts', 'dependency_preparation_keys', 'review_bindings')}
        item['preparation_key'] = hashlib.sha256(json.dumps(preparation, sort_keys=True).encode()).hexdigest()
        payload = {key: item.get(key) for key in ('input_digest', 'argv', 'effects', 'stage', 'boundary', 'evidence_class', 'runtime_identity', 'parameters', 'applicability', 'catalog_entries', 'dependency_contracts', 'dependency_evidence_keys', 'review_bindings')}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    for item in results:
        if item['catalog_input']: item['references'].add(catalog_ref)
        item['references'] = upstream(item['references'] | set(item['runtime'].get('config_inputs', [])), explicit=not item['scope_inputs'])
        # Metadata traversal may reintroduce the catalog, and a command parent
        # may contain it. Exclude that incidental file at both boundaries;
        # declared consumers still fingerprint the whole catalog normally.
        if not item['catalog_input']: item['references'].discard(catalog_ref)
        item['references'].update({'scripts/repo/check-selection/script.py', 'scripts/repo/check-selection/local_cache.py', 'scripts/repo/check-selection/execution_policy.py'})
        for review in item['review_bindings'].values():
            for entry in review: item['references'].update([source['path'] for source in entry['sources']] + entry['tests'] + entry.get('definitions', []))
        if parent_binding:
            source = parent_binding.get('selected_inputs', {}).get(item['check_id'])
            if not isinstance(source, dict) or not coverage.strings(source.get('references')):
                findings.append({'code': 'verification-parent-member-invalid', 'check_id': item['check_id']})
            else:
                item['references'] = set(source['references'])
        try: item['evidence_key'] = identity(item)
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            item['input_digest'] = ''
            code = 'check-input-symlink-unsupported' if type(error) is InputSymlinkError else 'check-runtime-identity-unavailable'
            detail = {'detail': 'input-symlink-unsupported'} if type(error) is InputSymlinkError else local_check_diagnostic(error)
            findings.append({'code': code, 'check_id': item['check_id'], **detail})
        if parent_binding and item.get('preparation_key') != parent_binding.get('selected_inputs', {}).get(item['check_id'], {}).get('preparation_key'):
            findings.append({'code': 'verification-parent-inputs-changed', 'check_id': item['check_id']})
    if args.staged:
        # The hook must prove the bytes that would be committed. Unrelated
        # unstaged work remains outside this selected-input boundary.
        unstaged = set(git(root, 'diff', '--name-only', '--no-renames', '-z').split('\0')) - {''}
        untracked = set(git(root, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')) - {''}
        selected_inputs = {catalog_ref} | {reference for item in results for reference in item['references']}
        for path in sorted(unstaged | untracked):
            if any(below(path, ref) or below(ref, path) for ref in selected_inputs):
                findings.append({'code': 'selected-input-not-staged', 'path': path})
    explicit_broad = explicit_checks is not None and any(checks.get(identity, {}).get('focused_prerequisites') or checks.get(identity, {}).get('members') for identity in seeds)
    if explicit_broad and not record_preparation and not parent_binding:
        prepared_context = [entry['path'] for entry in (preparation_context or {}).get('changed_inputs', [])]
        if not prepared_context:
            findings.append({'code': 'verification-task-context-required'})
        elif set(task_context or []) != set(prepared_context):
            findings.append({'code': 'verification-task-context-mismatch'})
        prepared = {(entry['check_id'], entry.get('preparation_key')) for entry in preparation_context.get('checks', [])}
        mismatched = [item['check_id'] for item in results if (item['check_id'], item.get('preparation_key')) not in prepared]
        if mismatched: findings.append({'code': 'verification-task-context-stale', 'check_ids': sorted(mismatched)})
    if not catalog_unchanged(): findings.append({'code': 'check-catalog-changed-during-planning'})
    preparation_status = 'not-requested'
    if record_preparation:
        preparation_status = 'recorded-pending-validation'
    if require_preparation and results:
        preparation = cache.read_preparation() if cache else {}
        if not preparation:
            findings.append({'code': 'verification-preparation-missing'})
            preparation_status = 'missing'
        else:
            prepared = {(item['check_id'], item.get('preparation_key')) for item in preparation['checks']}
            mismatched = [item['check_id'] for item in results if (item['check_id'], item.get('preparation_key')) not in prepared]
            if mismatched:
                findings.append({'code': 'verification-preparation-inputs-changed', 'check_ids': sorted(mismatched)})
                preparation_status = 'inputs-changed'
            else:
                preparation_status = 'matched'
    execution_preflight_passed = not findings
    def revalidate_item(item: dict) -> bool:
        blocked = []
        for child in item['dependency_ids']:
            prerequisite = by_identity.get(child)
            try: fresh = prerequisite is not None and prerequisite.get('status') == 'passed' and identity(prerequisite) == prerequisite.get('evidence_key')
            except (ValueError, OSError, subprocess.SubprocessError): fresh = False
            if not fresh: blocked.append(child)
        if blocked:
            item.update(status='blocked', reason='focused-or-member-proof-missing-or-stale')
            findings.append({'code': 'verification-prerequisite-not-passed', 'check_id': item['check_id'], 'check_ids': blocked})
            return False
        if not catalog_unchanged():
            item['status'] = 'uncertain'
            findings.append({'code': 'check-catalog-changed-before-execution', 'check_id': item['check_id']})
            return False
        try: current_identity = identity(item)
        except (ValueError, OSError, subprocess.SubprocessError): current_identity = None
        if current_identity != item.get('evidence_key'):
            item['status'] = 'uncertain'
            findings.append({'code': 'check-input-changed-before-execution', 'check_id': item['check_id']})
            return False
        return True

    # Reprobe each distinct runtime before execution, after each actual command,
    # and at completion. Reusing a receipt cannot itself mutate that runtime.
    reset_runtime_identities()
    timings['planning_seconds'] = max(0.0, time.monotonic() - started - sum(timings.values()))
    for position, item in enumerate(results):
        item['source_revision'] = revision
        item['scopes'] = sorted(set(item['scopes']))
        required_now = required(item)
        if args.execute_local and required_now and item['stage'] == 'local' and not execution_preflight_passed:
            item.update(status='blocked', reason='selection-preflight-failed')
            item['references'] = sorted(item['references'])
            print(json.dumps({'event': 'check-complete', 'check_id': item['check_id'], 'status': 'blocked', 'completed': position + 1, 'total': len(results)}), file=sys.stderr, flush=True)
            continue
        if args.execute_local and execution_preflight_passed and required_now and item['stage'] == 'local':
            if not revalidate_item(item):
                item['references'] = sorted(item['references'])
                print(json.dumps({'event': 'check-complete', 'check_id': item['check_id'], 'status': item['status'], 'completed': position + 1, 'total': len(results)}), file=sys.stderr, flush=True)
                continue
        if args.execute_local and required_now and execution_preflight_passed and item['stage'] == 'local':
            print(json.dumps({'event': 'check-start', 'check_id': item['check_id'], 'completed': position, 'total': len(results)}), file=sys.stderr, flush=True)
        phase_started = time.monotonic()
        proof = cache.read(item.get('evidence_key', 'invalid')) if cache and required_now and item['stage'] == 'local' and execution_preflight_passed else {}
        if not proof and reuse_cache and required_now and item['stage'] == 'local' and execution_preflight_passed:
            proof = reuse_cache.read(item.get('evidence_key', 'invalid'))
            if proof:
                item['reused_from_worktree'] = reuse_cache.worktree
        timings['receipt_validation_seconds'] += time.monotonic() - phase_started
        if proof:
            item.update(status='passed', exit_code=0, evidence_source='trusted-worktree-cache', executed_revision=proof.get('executed_revision', proof.get('source_revision')))
            if item.get('reused_from_worktree') and cache:
                cache.save({**item, 'references': sorted(item['references'])})
        elif not required_now:
            item['status'] = 'deferred'
            item['reason'] = 'integration-pending' if development else 'required-before-' + (item['boundary'] if BOUNDARIES[item['boundary']] > BOUNDARIES[boundary] else item['stage'])
        elif args.execute_local and item['stage'] == 'local' and execution_preflight_passed:
            # Receipt-only checks share one window, but cannot authorize a new
            # command from that snapshot. Remeasure its prerequisites and own
            # inputs immediately before execution, including after cache reads.
            reset_runtime_identities()
            if not revalidate_item(item):
                item['references'] = sorted(item['references'])
                print(json.dumps({'event': 'check-complete', 'check_id': item['check_id'], 'status': item['status'], 'completed': position + 1, 'total': len(results)}), file=sys.stderr, flush=True)
                continue
            if cache:
                phase_started = time.monotonic()
                item['cache_invalidation_reasons'] = cache.invalidation_reasons(item)
                timings['receipt_validation_seconds'] += time.monotonic() - phase_started
            execution_started = time.monotonic()
            # Runner-owned context must not contaminate an unrelated leaf
            # command (including verification fixtures with their own task).
            # Aggregate children receive only a reference to the authoritative
            # private binding below, which already contains their task paths.
            environment = dict(os.environ)
            environment.pop('REPO_CHECK_TASK_PATHS', None)
            environment.pop('REPO_CHECK_PARENT_BINDING', None)
            binding, previous_binding = None, None
            if any(entry.get('members') for entry in item['catalog_entries'].values()) and cache:
                binding = {'token': uuid.uuid4().hex, 'aggregate_owner': item['check_id'], 'catalog_digest': catalog_snapshot, 'task_paths': task_context,
                    'selected_inputs': {child: {'preparation_key': by_identity[child]['preparation_key'], 'references': sorted(by_identity[child]['references'])} for child in item['scheduling_contracts'] if child in by_identity}}
                previous_binding = cache.begin_execution(binding, os.environ.get('REPO_CHECK_PARENT_BINDING'))
                environment['REPO_CHECK_PARENT_BINDING'] = binding['token']
            try:
                completed = subprocess.run(item['argv'], cwd=root, env=environment, capture_output=True, text=True, check=False)
            finally:
                if binding: cache.end_execution(binding['token'], previous_binding)
            item['elapsed_seconds'] = round(time.monotonic() - execution_started, 6)
            timings['command_execution_seconds'] += item['elapsed_seconds']
            item['stdout_tail'] = 'not-retained' if completed.stdout else ''
            item['stderr_tail'] = 'not-retained' if completed.stderr else ''
            if any(entry.get('members') for entry in item['catalog_entries'].values()):
                try:
                    nested = json.loads(completed.stdout)
                    item['nested_execution_summary'] = safe_nested_execution_summary(nested['execution_summary'], set(item['scheduling_contracts']))
                except (ValueError, KeyError, TypeError, RecursionError):
                    item['nested_execution_summary'] = {'unavailable': True}
            item.update(status='passed' if completed.returncode == 0 else 'failed', exit_code=completed.returncode, evidence_source='local-runner', executed_revision=revision)
            # A check cannot qualify bytes that changed while it was executing.
            before = item['evidence_key']
            reset_runtime_identities()
            try: after = identity(item)
            except (ValueError, OSError, subprocess.SubprocessError): after = None
            if not catalog_unchanged():
                item['status'] = 'uncertain'
                findings.append({'code': 'check-catalog-changed-during-execution', 'check_id': item['check_id']})
            elif after != before:
                item['status'] = 'uncertain'
                findings.append({'code': 'check-input-changed-during-execution', 'check_id': item['check_id']})
            elif completed.returncode:
                findings.append({'code': 'required-check-failed', 'check_id': item['check_id']})
            elif cache: cache.save({**item, 'references': sorted(item['references'])})
        elif args.stage != 'local' or args.execute_local:
            findings.append({'code': 'required-proof-missing-or-stale' if item['stage'] == 'local' else 'required-proof-owned-by-stage-controller', 'check_id': item['check_id'], 'stage': item['stage']})
        item['references'] = sorted(item['references'])
        if args.execute_local:
            result = 'reused' if item.get('evidence_source') == 'trusted-worktree-cache' else 'executed' if item.get('evidence_source') == 'local-runner' else item['status']
            print(json.dumps({'event': 'check-complete', 'check_id': item['check_id'], 'status': item['status'], 'result': result, 'completed': position + 1, 'total': len(results)}), file=sys.stderr, flush=True)
    # A later command must not revoke an earlier pass unnoticed. The combined
    # result is qualified only after every required proof still matches.
    reset_runtime_identities()
    for item in results:
        if item['stage'] != 'local' or item['status'] != 'passed': continue
        try: final_identity = identity(item)
        except (ValueError, OSError, subprocess.SubprocessError): final_identity = None
        if final_identity != item.get('evidence_key') or any(by_identity[child]['status'] != 'passed' for child in item['dependency_ids'] if child in by_identity):
            item['status'] = 'uncertain'
            findings.append({'code': 'check-input-changed-before-completion', 'check_id': item['check_id']})
    if not catalog_unchanged() and not any(item['code'].startswith('check-catalog-changed-') for item in findings):
        findings.append({'code': 'check-catalog-changed-during-invocation'})
    execution_summary = {
        'selected_check_ids': sorted(item['check_id'] for item in results),
        'elapsed_seconds': round(time.monotonic() - started, 6),
        'execution_seconds': round(sum(item.get('elapsed_seconds', 0) for item in results if item.get('evidence_source') == 'local-runner'), 6),
        'reused_check_ids': sorted(item['check_id'] for item in results if item.get('evidence_source') == 'trusted-worktree-cache'),
        'executed_check_ids': sorted(item['check_id'] for item in results if item.get('evidence_source') == 'local-runner'),
        'deferred_check_ids': sorted(item['check_id'] for item in results if item.get('status') == 'deferred'),
        'timings': {**{key: round(value, 6) for key, value in timings.items()}, 'other_seconds': round(max(0, time.monotonic() - started - sum(timings.values())), 6)},
        'invalidated_checks': [
            {'check_id': item['check_id'], 'reasons': item['cache_invalidation_reasons']}
            for item in results if item.get('cache_invalidation_reasons') and item.get('cache_invalidation_reasons') != [NO_PRIOR_EVIDENCE]
        ],
    }
    report = {'schema': 'repo/check-selection-report/v1', 'stage': args.stage, 'verdict': 'gap' if findings else ('passed' if args.execute_local or args.stage != 'local' else 'planned'), 'source_revision': revision, 'changed_inputs': [{'path': path, 'state': 'present' if (root / path).exists() else 'deleted'} for path in changed], 'affected_consumers': sorted(consumers - set(changed) | {path for report in impacted for path in report['consumers']}), 'delivery_inventory': {'source_revision': delivery['source_revision'], 'input_digest': delivery['input_digest'], 'summary': delivery['summary']}, 'scopes': impacted, 'checks': results, 'execution_summary': execution_summary, 'non_applicable': non_applicable, 'findings': findings, 'limitations': ['Declared inputs, metadata consumers and workspace dependencies define supported impact; unmapped authoritative definitions remain gaps.', 'Local cache trusts same-user private worktree Git metadata and declared runtime/config/environment inputs; it is not portable or live acceptance evidence.', 'Imported reports cannot qualify checks. Only unchanged successful local runner results are reused; all external proof remains with its owning stage controller.']}
    if record_preparation and cache and not findings:
        report['preparation_report_path'] = cache.save_preparation({
            **cache.read_preparation(),
            'changed_inputs': [{'path': path, 'state': 'present' if (root / path).exists() else 'deleted'} for path in task_context or []],
            'checks': [{'check_id': item['check_id'], 'evidence_key': item.get('evidence_key'), 'preparation_key': item.get('preparation_key'), 'stage': item['stage']} for item in results],
        })
        preparation_status = 'recorded'
    report['preparation_status'] = preparation_status
    report['boundary'] = boundary
    if development and not findings and args.execute_local:
        report['verdict'] = 'partial'
    report['execution_policy'] = execution_policy.execution_view(results, checks, development=development, explicit=explicit_checks is not None)
    if explicit_checks is not None:
        report['selection_mode'] = 'explicit-checks'
        report['requested_check_ids'] = explicit_checks
    if args.evidence: report['evidence_import_status'] = 'rejected-untrusted-report'
    if cache:
        if args.execute_local:
            try: report['run_report_path'] = execution_policy.retain_run(root, report)
            except (OSError, ValueError):
                report['findings'].append({'code': 'test-run-retention-unavailable'})
                report['verdict'] = 'gap'
        report['local_report_path'] = str(cache.directory / 'latest-report.json')
        cache.save_report(report)
    return report



def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--paths', nargs='+')
    mode.add_argument('--checks', nargs='+', help='Verify exact registered checks; not a replacement for impact, staged or CI selection.')
    mode.add_argument('--aggregate-members', help='Execute only the catalog-owned members of an aggregate wrapper.')
    mode.add_argument('--staged', action='store_true')
    mode.add_argument('--all', action='store_true')
    mode.add_argument('--ci', action='store_true', help='Select the PR diff from BASE_SHA/HEAD_SHA, or all inputs for manual CI.')
    mode.add_argument('--inventory', action='store_true', help='Read-only feedback declaration inventory; no proof or execution.')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--stage', choices=STAGES, default='local')
    parser.add_argument('--boundary', choices=BOUNDARIES, default='integration', help='Scheduling boundary only; never grants execution permissions.')
    parser.add_argument('--execute-local', action='store_true')
    parser.add_argument('--task-paths', nargs='+', help='Exact current task context for explicit broad verification; otherwise matching prepared context is required.')
    parser.add_argument('--record-preparation', action='store_true')
    parser.add_argument('--require-preparation', action='store_true')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--reuse-from-worktree', type=Path, help='Revalidate receipts from a registered worktree of this repository; reports are never accepted.')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--development', action='store_true', help='Path-scoped local feedback only; full integration obligations remain pending.')
    parser.add_argument('--explain', action='store_true', help='Render a readable selection summary instead of JSON.')
    args = parser.parse_args()
    if args.development and (not args.paths or args.stage != 'local' or args.boundary != 'integration' or args.record_preparation or args.require_preparation):
        parser.error('--development requires --paths at the local integration boundary, without preparation')
    if args.inventory and (args.execute_local or args.development or args.record_preparation or args.require_preparation):
        parser.error('--inventory is read-only')
    if args.record_preparation and args.require_preparation:
        parser.error('--record-preparation and --require-preparation are mutually exclusive')
    if args.require_preparation and not args.staged:
        parser.error('--require-preparation requires --staged')
    try:
        if args.task_paths is None and 'REPO_CHECK_TASK_PATHS' in os.environ:
            args.task_paths = json.loads(os.environ['REPO_CHECK_TASK_PATHS'])
        if args.aggregate_members:
            catalog = coverage.document(args.catalog or args.root / 'scripts/repo/check-selection/checks.yml')
            aggregate = catalog.get('checks', {}).get(args.aggregate_members, {})
            members = aggregate.get('members')
            if not coverage.strings(members): raise ValueError('verification-aggregate-members-invalid')
            args.checks = members
        if args.ci:
            base, head = os.environ.get('BASE_SHA', ''), os.environ.get('HEAD_SHA', '')
            if base:
                if not re.fullmatch(r'[0-9a-f]{40}', base) or not re.fullmatch(r'[0-9a-f]{40}', head):
                    raise ValueError('ci-source-revision-invalid')
                args.comparison_base = base
                args.paths = [path for path in git(args.root.resolve(), 'diff', '--name-only', '--no-renames', '-z', base, head).split('\0') if path]
            else:
                args.all = True
        if args.inventory:
            catalog = coverage.document(args.catalog or args.root / 'scripts/repo/check-selection/checks.yml')
            if catalog.get('schema') != 'repo/check-catalog/v1' or not isinstance(catalog.get('checks'), dict):
                raise ValueError('check-catalog-invalid')
            report = execution_policy.inventory(catalog['checks'])
        else:
            report = plan(args)
    except (OSError, ValueError, TypeError, ImportError, subprocess.SubprocessError) as error:
        report = {'schema': 'repo/check-selection-report/v1', 'verdict': 'gap', 'findings': [{'code': 'selection-input-or-runtime-invalid', 'error_type': safe_runtime_error_type(error)}]}
    print(execution_policy.render(report) if args.explain else json.dumps(report, sort_keys=True))
    return 1 if report['findings'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
