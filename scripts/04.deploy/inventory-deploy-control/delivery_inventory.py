#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.delivery-inventory
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.declaration-coverage
#   disciplines: [architecture, sre]
#   kind: script
#   purpose: Reconcile a physical delivery census with existing declarations and emit source-bound coverage without provider access.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.inventory-deploy-control
#     path: scripts/04.deploy/inventory-deploy-control/script.sh
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path
import yaml

sys.dont_write_bytecode = True
SKIP = {'.git', 'node_modules', '__pycache__', '.cache', 'artifacts', 'dist', 'build', 'commitLogs'}
PATH = re.compile(r'(?<![A-Za-z0-9_.-])(?:\.github|\.agentic|infra|scripts|platform|packages|products|apps)/[A-Za-z0-9_./-]+')

class Loader(getattr(yaml, 'CSafeLoader', yaml.SafeLoader)):
    pass
Loader.add_multi_constructor('!', lambda loader, tag, node: loader.construct_scalar(node) if isinstance(node, yaml.ScalarNode) else loader.construct_sequence(node) if isinstance(node, yaml.SequenceNode) else loader.construct_mapping(node))

def document(body):
    try:
        value = yaml.load(body, Loader=Loader)
        return value if isinstance(value, dict) else {}
    except yaml.YAMLError:
        return {}

def module(root, name, path):
    spec = importlib.util.spec_from_file_location(name, root / path)
    if not spec or not spec.loader:
        raise ValueError('inventory-owner-unavailable:' + path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def files(root):
    # Scan physical source locations, including root/new package entrypoints.
    # Build outputs, private configuration and evidence history are not sources.
    result = []
    for directory, names, filenames in os.walk(root, followlinks=False):
        names[:] = [name for name in names if name not in SKIP and (not name.startswith('.') or name in {'.agentic', '.github'})]
        result.extend(Path(directory) / name for name in names if (Path(directory) / name).is_symlink())
        for name in filenames:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            image = name in {'Dockerfile', 'Containerfile'} or name.startswith(('Dockerfile.', 'Containerfile.')) and not name.endswith('dockerignore')
            if path.is_symlink() or image or name == '.dockerignore' or name.endswith('.dockerignore') or path.suffix in {'.py', '.sh', '.mjs', '.cjs', '.js', '.jsx', '.ts', '.tsx', '.json', '.yml', '.yaml'} or path.suffix == '.md' and relative.startswith(('.agentic/', 'scripts/', 'infra/')):
                result.append(path)
    return sorted(result)


def repository_ci_findings(root, documents, catalog):
    path = '.github/workflows/delivery-coverage.yml'
    # Existing catalogue inputs make removal visible; fixtures can carry their
    # own CI contract without implicitly acquiring this repository's workflow.
    required = any(path in item.get('inputs', []) for item in catalog.get('repository_inputs', []) if isinstance(item, dict))
    if not required and path not in documents: return []
    if path not in documents: return [{'code': 'delivery-ci-workflow-missing', 'path': path}]
    guard = module(Path(__file__).resolve().parents[3], 'delivery_workflow_guard', 'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/workflow_guard.py')
    try:
        workflow = documents[path]
        events = workflow.get('on', workflow.get(True, {}))
        if not isinstance(events, dict) or not {'pull_request', 'workflow_dispatch'} <= set(events): raise ValueError('ci-trigger-coverage-missing')
        # No filtered trigger is currently governed. Even a seemingly broad glob
        # can omit future delivery inputs, branches or normal PR activity.
        if events['pull_request'] is not None and events['pull_request'] != {}:
            raise ValueError('ci-pull-request-restrictions-unsupported')
        steps = guard.job_steps((root / path).read_text(), 'source-and-local-proof')
        inventory, _ = guard.protected_step(steps, 'Reconcile independent delivery census', [['python3', 'scripts/04.deploy/inventory-deploy-control/script.py', '--delivery', '--check']])
        regression, _ = guard.protected_step(steps, 'Exercise discovery and command boundaries', [['bash', 'scripts/04.deploy/inventory-deploy-control/smoke-test.sh']])
        selector, selected = guard.protected_step(steps, 'Execute selected local proofs', [['bash', 'scripts/repo/check-selection/script.sh', '--ci', '--execute-local', '--json']], environment={'BASE_SHA': '${{ github.event.pull_request.base.sha }}', 'HEAD_SHA': '${{ github.sha }}'})
        if selected.get('env') != {'BASE_SHA': '${{ github.event.pull_request.base.sha }}', 'HEAD_SHA': '${{ github.sha }}'}: raise ValueError('ci-diff-identity-substituted')
        installs = [i for i, step in enumerate(steps) if 'npm ci' in step.get('run', '')]
        if len(installs) != 1 or not inventory < installs[0] < regression < selector: raise ValueError('ci-stage-order-invalid')
        for index, step in enumerate(steps):
            if index < inventory and re.search(r'(?:npm|docker|aws|podman|kubectl|terraform)\s', step.get('run', '')): raise ValueError('ci-consequence-before-inventory')
    except (KeyError, TypeError, ValueError) as error:
        return [{'code': 'delivery-ci-enforcement-invalid', 'path': path, 'reference': str(error)}]
    return []


def effects(body):
    match = re.search(r'^(?:#|//)[ \t]+effects:[ \t]*(.*)$', body, re.MULTILINE)
    if match is None: return []
    inline = match.group(1).strip()
    if inline.startswith('['):
        try: value = yaml.safe_load(inline)
        except yaml.YAMLError: return []
        return value if isinstance(value, list) else []
    following = body[match.end():].splitlines()
    result = []
    for line in following:
        if not line.strip(): continue
        item = re.fullmatch(r'(?:#|//)\s+-\s+([a-z-]+)\s*', line)
        if not item: break
        result.append(item.group(1))
    return result


def fixture_source(path):
    p = Path(path)
    return bool({'fixtures', 'tests'} & set(p.parts)) or any(word in p.name for word in ('test', 'regression'))


def external_command(body):
    return bool(re.search(r'(?:^|[\s;&|])(?:aws|docker|podman|buildah|kubectl|terraform)(?:\s|$)|\[\s*[\"\']aws[\"\']', body))


def package_execution(root, package_path, command, packages, bodies, seen=()):
    """Trace literal interpreter/governed-wrapper and npm-alias commands only.

    Unknown shell constructs are an explicit coverage gap for delivery commands;
    this is deliberately not a shell evaluator. No discovered command is run.
    """
    refs, unknown = set(), []
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|()<>')
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return refs, ['malformed-command'], False
    parts, part = [], []
    for token in tokens + [';']:
        if token in {';', '&&', '||'}:
            if part: parts.append(part); part = []
        else: part.append(token)
    external = False
    for args in parts:
        while args and (args[0] in {'exec', 'command', 'env'} or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=[^$`]*', args[0])):
            args = args[1:]
        if not args: continue
        if any(re.search(r'[$`]|^[|&()<>]+$', arg) for arg in args):
            unknown.append('dynamic-or-unsupported-shell'); continue
        tool = Path(args[0]).name
        if tool == 'npm' and len(args) >= 3 and args[1] in {'run', 'run-script'}:
            identity = (package_path, args[2])
            target = packages[package_path].get('scripts', {}).get(args[2])
            if identity in seen or not isinstance(target, str):
                unknown.append('unresolved-or-cyclic-npm-alias'); continue
            child_refs, child_unknown, child_external = package_execution(root, package_path, target, packages, bodies, (*seen, identity))
            refs.update(child_refs); unknown.extend(child_unknown); external |= child_external
            continue
        if tool in {'aws', 'docker', 'podman', 'buildah', 'kubectl', 'terraform'}:
            external = True; continue
        if tool in {'bash', 'sh', 'python', 'python3', 'node', 'tsx', 'ts-node'}:
            rest = args[1:]
            if rest and rest[0] in {'-c', '-lc'} and len(rest) == 2:
                child_refs, child_unknown, child_external = package_execution(root, package_path, rest[1], packages, bodies, seen)
                refs.update(child_refs); unknown.extend(child_unknown); external |= child_external
                continue
            while rest and rest[0] in {'--', '-e', '-u', '-eu'}: rest = rest[1:]
            if not rest or rest[0].startswith('-'):
                unknown.append('unsupported-interpreter-form'); continue
            target, rest = rest[0], rest[1:]
        elif tool in {'tsc', 'echo', 'printf', 'true', 'false'}:
            # Known local commands do not imply delivery effects by their names.
            continue
        else:
            target, rest = args[0], args[1:]
        candidate = ((root / package_path).parent / target).resolve()
        if not candidate.is_relative_to(root) or candidate.relative_to(root).as_posix() not in bodies:
            unknown.append('implementation-unresolved'); continue
        ref = candidate.relative_to(root).as_posix(); refs.add(ref)
        if ref == 'scripts/01.harness/run-governed-script.sh':
            if len(rest) >= 2 and rest[0] == '--approved-action':
                action = ((root / package_path).parent / rest[1]).resolve()
                if action.is_relative_to(root) and action.relative_to(root).as_posix() in bodies:
                    refs.add(action.relative_to(root).as_posix())
                else: unknown.append('governed-action-unresolved')
            else: unknown.append('governed-action-unresolved')
    return refs, sorted(set(unknown)), external


def report(root, source_revision=None):
    root = root.resolve()
    paths = files(root)
    bodies, modes, source_errors = {}, {}, []
    for path in paths:
        ref = path.relative_to(root).as_posix()
        if path.is_symlink():
            source_errors.append({'code': 'delivery-source-symlink-unsupported', 'path': ref}); continue
        try:
            bodies[ref] = path.read_bytes().decode('utf-8')
            modes[ref] = path.stat().st_mode & 0o777
        except UnicodeError:
            source_errors.append({'code': 'delivery-source-encoding-invalid', 'path': ref})
    documents = {path: document(body) for path, body in bodies.items() if path.endswith(('.yml', '.yaml')) and (path.startswith(('infra/', '.github/')) or path == 'scripts/repo/check-selection/checks.yml')}
    catalog = documents.get('scripts/repo/check-selection/checks.yml', {})
    checks = catalog.get('checks', {})
    if not isinstance(checks, dict): checks = {}
    requirements = {}
    declared = set()
    references = {}
    for source, body in bodies.items():
        references[source] = {match.rstrip('.') for match in PATH.findall(body)}
        # Provider compositions and wrappers commonly use paths relative to themselves.
        for local in re.findall(r'(?<![A-Za-z0-9_.-])[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.(?:yml|yaml|py|sh|mjs)\b', body):
            candidate = (root / source).parent / local
            if candidate.is_file() and candidate.resolve().is_relative_to(root):
                references[source].add(candidate.resolve().relative_to(root).as_posix())
        # Authoritative references register exact paths, never an entire directory.
        if (source.startswith('infra/') and '/fixtures/' not in source) or (source.startswith('.agentic/') and '/plans/' not in source and '/templates/' not in source) or source in {'package.json', 'scripts/repo/check-selection/checks.yml'}:
            declared.update(ref for ref in references[source] if ref != source)
    while True:
        expanded = declared | {ref for source in declared for ref in references.get(source, set()) if ref != source}
        if expanded == declared: break
        declared = expanded
    findings = source_errors + repository_ci_findings(root, documents, catalog)
    def gap(code, path, **extra):
        item = dict(code=code, path=path, **extra)
        if item not in findings: findings.append(item)
    scope_roots = sorted({p.parent for p in paths if p.name == 'scope-index.yml'} | {p.parents[2] for p in paths if p.name == 'declaration-contract.yml' and p.parent.name == '00-declaration'})
    for scope_root in scope_roots:
        index_path = (scope_root / 'scope-index.yml').relative_to(root).as_posix()
        index = documents.get(index_path)
        if not index:
            gap('scope-inventory-missing', index_path); continue
        entries = index.get('scopes', [])
        indexed = {entry.get('id') for entry in entries if isinstance(entry, dict)}
        found = {p.name for p in scope_root.iterdir() if p.is_dir() and ((p / '00-declaration').exists() or (p / '10-workload-binding').exists())}
        if found != indexed: gap('scope-inventory-incomplete', index_path)
    for path, value in documents.items():
        if Path(path).name in {'declaration-contract.yml', 'target-profile.yml', 'scope-index.yml', 'workload-binding.yml'} and not value:
            gap('delivery-declaration-invalid', path)
        if value.get('schema') == 'deploy/target-profile/v1':
            target_root = (root / path).parent.parent
            if not (target_root / '20-scopes/scope-index.yml').is_file(): gap('target-scope-inventory-missing', path)
    routes = []
    coverage = module(Path(__file__).resolve().parents[3], 'delivery_declaration_coverage', 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py')
    for path, value in documents.items():
        schema = value.get('schema')
        if schema not in {'deploy/target-scope-contract/v1', 'deploy/declaration-contract/v1'}: continue
        if not path.startswith('infra/'): continue
        impact = value.get('change_impact', {})
        reqs = impact.get('requirements', value.get('requirements', []))
        program = value.get('program', {})
        chain = []
        for req in reqs:
            if not isinstance(req, dict): continue
            proofs = {stage: req.get(stage + '_proofs', []) if isinstance(req.get(stage + '_proofs', []), list) else [] for stage in ('local', 'package', 'target', 'run')}
            chain.append({'requirement': req.get('id'), 'implementation': req.get('required_by', []), 'declarations': req.get('declarations', []), 'proofs': proofs, 'commands': {identity: checks[identity]['argv'] for values in proofs.values() for identity in values if isinstance(identity, str) and identity in checks and isinstance(checks[identity], dict) and isinstance(checks[identity].get('argv'), list)}, 'not_applicable': req.get('not_applicable', {})})
        if schema == 'deploy/target-scope-contract/v1':
            result = coverage.inspect(root / path, root, catalog, probe_commands=False)
            for issue in result['findings']: gap(issue['code'], path, reference=issue.get('reference', ''))
            binding = (root / path).parent.parent / '10-workload-binding/workload-binding.yml'
            route_refs = result['references']
        else:
            # Older supported declaration format retains its own readiness and workflow owners.
            result = coverage.inspect(root / path, root, catalog, probe_commands=False)
            for issue in result['findings']: gap(issue['code'], path, reference=issue.get('reference', ''))
            binding = root / value.get('target', {}).get('profile', '')
            route_refs = result['references']
        rid = value.get('id', path)
        route = {'id': rid, 'classification': 'supported', 'declaration': path, 'target': value.get('target'), 'scope': value.get('scope'), 'program': program, 'binding': binding.relative_to(root).as_posix(), 'acceptance': value.get('acceptance', {}), 'recovery': value.get('rollback', {}), 'chain': chain, 'references': route_refs, 'coverage': result['verdict']}
        routes.append(route)
        for ref in route_refs:
            requirements.setdefault(ref, []).append(rid)
            if ref in bodies: declared.add(ref)
    # Trace each owner route through existing references and selected proof commands.
    # Directory input declarations describe affected consumers, not registration.
    packages = {path: json.loads(body) for path, body in bodies.items() if Path(path).name == 'package.json'}
    package_executions = {(path, name): package_execution(root, path, command, packages, bodies, ((path, name),))
                          for path, package in packages.items() for name, command in package.get('scripts', {}).items() if isinstance(command, str)}
    operational = {path for path, body in bodies.items() if 'aws-mutation' in effects(body) or
                   external_command('\n'.join(line for line in body.splitlines() if not line.lstrip().startswith(('#', '//')))) and
                   (not fixture_source(path) or bool({'network', 'aws-mutation'} & set(effects(body))) or path.startswith('scripts/04.deploy/') and not effects(body))}
    module_exports = {}
    for package_path, package in packages.items():
        for export, target in package.get('exports', {}).items() if isinstance(package.get('exports'), dict) else []:
            if not isinstance(target, str) or not isinstance(package.get('name'), str): continue
            candidate = (root / package_path).parent / target
            if candidate.is_file() and candidate.resolve().is_relative_to(root):
                module_exports[package['name'] + (export[1:] if export != '.' else '')] = candidate.resolve().relative_to(root).as_posix()
    trace_references = {}
    for source, body in bodies.items():
        if Path(source).name == 'target-profile.yml': continue
        if source.startswith(('infra/', '.github/workflows/')):
            data = documents.get(source)
            semantic = json.dumps(data, default=str) if data else body
        elif Path(source).suffix in {'.py', '.sh', '.mjs', '.ts'} and (not fixture_source(source) or source in operational):
            semantic = '\n'.join(line for line in body.splitlines() if not line.lstrip().startswith(('#', '//')))
        else:
            continue
        trace_references[source] = {ref.rstrip('.') for ref in PATH.findall(semantic)}
        for local in re.findall(r'(?<![A-Za-z0-9_.-])[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.(?:yml|yaml|py|sh|mjs)\b', semantic):
            candidate = (root / source).parent / local
            if candidate.is_file() and candidate.resolve().is_relative_to(root): trace_references[source].add(candidate.resolve().relative_to(root).as_posix())
        for imported in re.findall(r'''["'](@[^"']+)["']''', semantic):
            if imported in module_exports: trace_references[source].add(module_exports[imported])
        for name in re.findall(r'npm run ([A-Za-z0-9:_-]+)', semantic):
            trace_references[source].update(package_executions.get(('package.json', name), (set(), [], False))[0])
    for route in routes:
        reached = set(route['references']) | {route['declaration'], route['binding']}
        reached.update(arg for requirement in route['chain'] for argv in requirement['commands'].values() for arg in argv if arg in bodies)
        if '/20-scopes/' in route['declaration']:
            target_prefix = route['declaration'].split('/20-scopes/', 1)[0] + '/'
            reached.update(path for path in bodies if path.startswith(target_prefix + '00-target/') or path.startswith(target_prefix + '40-package-custody/') or path == target_prefix + '10-foundation/foundation-index.yml')
        while True:
            added = {ref for source in reached for ref in trace_references.get(source, set()) if ref != 'scripts/repo/check-selection/checks.yml'}
            if added <= reached: break
            reached |= added
        route['trace_inputs'] = sorted(path for path in reached if path in bodies)
        for ref in reached: requirements.setdefault(ref, []).append(route['id'])
    # Image launch instructions independently reveal programs whose filenames
    # are not main.*; an index cannot be the only way to discover them.
    image_commands = {}
    launched_sources = set()
    for path, body in bodies.items():
        name = Path(path).name
        if not (name in {'Dockerfile', 'Containerfile'} or name.startswith(('Dockerfile.', 'Containerfile.')) and not name.endswith('dockerignore')): continue
        commands = []
        for match in re.finditer(r'^(?:CMD|ENTRYPOINT)\s+(.*)$', body, re.MULTILINE):
            raw = match.group(1)
            try: command = json.loads(raw) if raw.startswith('[') else [raw]
            except ValueError: gap('delivery-image-command-invalid', path); continue
            commands.append(command)
            for arg in command:
                if isinstance(arg, str):
                    candidate = arg.removeprefix('/app/').removeprefix('./')
                    if candidate in bodies and Path(candidate).suffix in {'.js', '.mjs', '.cjs', '.py', '.sh'}:
                        launched_sources.add(candidate)
        image_commands[path] = commands
    package_launches = {}
    for package_path, package in packages.items():
        for name, command in package.get('scripts', {}).items():
            if not isinstance(command, str) or not re.search(r'(?:^|:)(?:start|serve|service)(?:$|:)', name): continue
            try: arguments = shlex.split(command)
            except ValueError:
                gap('delivery-package-command-invalid', package_path + '#scripts.' + name); arguments = []
            sources = set()
            for argument in arguments:
                for base in (root / package_path).parent, root:
                    candidate = (base / argument).resolve()
                    if candidate.is_relative_to(root) and candidate.is_file() and candidate.suffix in {'.js', '.mjs', '.cjs', '.ts', '.tsx', '.py', '.sh'}:
                        sources.add(candidate.relative_to(root).as_posix())
            package_launches[(package_path, name)] = sources
            launched_sources.update(sources)
    discovered = []
    for path, body in bodies.items():
        p = Path(path)
        value = documents.get(path, {})
        kind = None
        semantic = '\n'.join(line for line in body.splitlines() if not line.lstrip().startswith(('#', '//')))
        has_external_command = external_command(semantic)
        script_effects = effects(body)
        if path.startswith('.github/workflows/') and p.suffix in {'.yml', '.yaml'}: kind = 'ci-workflow'
        elif p.name in {'Dockerfile', 'Containerfile'} or p.name.startswith(('Dockerfile.', 'Containerfile.')) and not p.name.endswith('dockerignore'): kind = 'image-definition'
        elif path.startswith('scripts/04.deploy/') and p.suffix in {'.sh', '.py', '.mjs'} and (p.suffix == '.sh' or re.search(r"^if __name__\s*==", body, re.MULTILINE) is not None or p.name in {'script.py', 'script.mjs'} or p.suffix == '.mjs' and 'process.argv' in body):
            kind = 'regression-command' if any(word in p.name for word in ('test', 'regression')) or '/fixtures/' in path else 'command'
        elif p.suffix in {'.sh', '.py', '.mjs', '.js', '.cjs'} and path in operational: kind = 'command'
        elif path in launched_sources or p.name.endswith(('.main.ts', '.main.js')) or p.name in {'main.ts', '__main__.py'}: kind = 'runnable-program'
        elif p.name == 'target-profile.yml': kind = 'target'
        elif p.name == 'workload-binding.yml': kind = 'provider-binding'
        elif value.get('schema') in {'deploy/target-scope-contract/v1', 'deploy/declaration-contract/v1'} and path.startswith('infra/'): kind = 'scope'
        elif isinstance(value.get('Resources'), dict) and path.startswith('infra/'): kind = 'provider-template'
        if kind is None: continue
        inbound = sorted(source for source, refs in references.items() if source != path and path in refs)
        # A shell wrapper's adjacent implementation is the same public interface.
        wrapper = p.with_name('script.sh').as_posix()
        if kind == 'command' and p.name in {'script.py', 'script.mjs'} and wrapper in bodies and wrapper in declared:
            inbound.append(wrapper)
            declared.add(path)
        registered = path in declared
        if kind in {'provider-binding', 'scope', 'target'}: registered = registered or path in requirements
        retired = False
        # Retirement comes from authoritative manifests, not path names or an exemption list.
        for manifest_path, manifest in documents.items():
            if (manifest.get('status') == 'retired' or manifest.get('deployment', {}).get('status') == 'retired') and path in references.get(manifest_path, set()): retired = True
        if kind == 'ci-workflow':
            jobs = value.get('jobs', {})
            if jobs and all(str(job.get('if', '')).strip() in {'${{ false }}', 'false', 'False'} for job in jobs.values() if isinstance(job, dict)):
                retired = any((doc.get('status') == 'retired' or doc.get('deployment', {}).get('status') == 'retired') and path in references.get(ref, set()) for ref, doc in documents.items())
        # A retired deployment may retain an artifact also used by a supported
        # local route. Keep that historical reference; direct current declaration
        # ownership decides whether the artifact itself is still supported.
        direct_current_use = any(path in route['references'] for route in routes)
        classification = 'retired' if retired and not direct_current_use else 'supported' if registered else 'unsupported'
        if classification == 'unsupported': gap('delivery-entrypoint-unregistered', path, kind=kind)
        if not script_effects and p.name in {'script.py', 'script.mjs'}:
            script_effects = effects(bodies.get(wrapper, ''))
        needs_route = kind in {'image-definition', 'provider-template', 'runnable-program'} or kind in {'command', 'ci-workflow'} and (has_external_command or bool({'network', 'aws-mutation'} & set(script_effects))) or kind == 'regression-command' and path in operational
        if classification == 'supported' and needs_route and not requirements.get(path):
            gap('delivery-consumer-unbound', path, kind=kind)

        discovered.append({'path': path, 'kind': kind, 'classification': classification, 'registered_by': sorted(set(inbound)), 'routes': sorted(set(requirements.get(path, []))), 'sha256': hashlib.sha256(body.encode()).hexdigest(), 'effects': script_effects, 'requires_delivery_chain': needs_route, **({'image_commands': image_commands[path]} if path in image_commands else {})})
    for package_path, package in packages.items():
        for name, command in package.get('scripts', {}).items():
            if not isinstance(command, str): continue
            refs, unknown, direct_external = package_executions[(package_path, name)]
            consequential = refs & operational
            named = bool(re.search(r'(?:build|publish|deploy|image|release|rollback|cleanup|accept|recovery|(?:^|:)(?:start|serve|service)(?:$|:))', name))
            if not (named or consequential or direct_external or 'scripts/04.deploy/' in command): continue
            linked = sorted({rid for ref in refs for rid in requirements.get(ref, [])})
            requires_chain = direct_external or bool(consequential) or (package_path, name) in package_launches
            missing = sorted(ref for ref in consequential | package_launches.get((package_path, name), set()) if not requirements.get(ref))
            # A separate inline provider command cannot borrow a neighboring
            # script's requirement route. Keep provider effects in their existing
            # declared command owners rather than invent a package mapping registry.
            if direct_external: unknown = [*unknown, 'inline-provider-command-requires-owned-script']
            unsupported = bool(unknown or missing or requires_chain and not linked)
            identity = package_path + '#scripts.' + name
            if unknown: gap('delivery-command-relationship-unsupported', identity, reasons=unknown)
            if missing or requires_chain and not linked: gap('delivery-command-unbound', identity, implementations=missing)
            discovered.append({'path': identity, 'kind': 'package-command', 'classification': 'unsupported' if unsupported else 'supported', 'command': command, 'registered_by': [package_path], 'routes': linked, 'implementation': sorted(refs), 'requires_delivery_chain': requires_chain})
    # Render the chain from declarations, check owners and discovered consumers.
    # These are references into existing authority, not a second route registry.
    for route in routes:
        owned = [item for item in discovered if route['id'] in item['routes']]
        proof_ids = sorted({identity for requirement in route['chain'] for identities in requirement['proofs'].values() for identity in identities if isinstance(identity, str)})
        evidence = {identity: {field: checks[identity].get(field) for field in ('argv', 'stage', 'evidence_class', 'effects', 'inputs')} for identity in proof_ids if identity in checks}
        binding = documents.get(route['binding'], {})
        route['delivery_chain'] = {
            'requirements': [item['requirement'] for item in route['chain']],
            'implementation': sorted({path for item in route['chain'] for path in item['implementation'] if isinstance(path, str)}),
            'packages': [item['path'] for item in owned if item['kind'] == 'image-definition'],
            'programs': [item['path'] for item in owned if item['kind'] == 'runnable-program'],
            'configuration_and_permissions': {'binding': route['binding'], 'runtime_requirements': binding.get('runtime_requirements', []), 'provider_templates': [item['path'] for item in owned if item['kind'] == 'provider-template'], 'identity_sources': [path for path in route['trace_inputs'] if '/iam/' in path]},
            'execution_entrypoints': [item['path'] for item in owned if item['kind'] in {'command', 'ci-workflow', 'package-command'}],
            'evidence': evidence,
            'acceptance_and_recovery': {'acceptance_contract': route['acceptance'], 'rollback_contract': route['recovery'], 'target_recovery': binding.get('operations', {}).get('rollback', {}), 'commands': [item['path'] for item in owned if item['kind'] == 'command' and re.search(r'(?:accept|readiness|release-succession|restore|rollback|reconcil|cleanup|recovery)', item['path'])]},
            'stage_applicability': route['scope'].get('stage_applicability', {}) if isinstance(route['scope'], dict) else {},
        }
    inputs = [{'path': path, 'sha256': hashlib.sha256(body.encode()).hexdigest(), 'mode': modes[path]} for path, body in sorted(bodies.items())]
    revision = source_revision or subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    return {'schema': 'deploy/delivery-coverage-report/v1', 'source_revision': revision, 'source_state': 'working-tree', 'input_digest': hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(), 'inputs': inputs, 'verdict': 'gap' if findings else 'covered', 'summary': {'entrypoints': len(discovered), 'routes': len(routes), 'kinds': dict(Counter(item['kind'] for item in discovered)), 'classifications': dict(Counter(item['classification'] for item in discovered)), 'gaps': len(findings)}, 'entrypoints': discovered, 'routes': routes, 'findings': findings, 'limitations': ['Source coverage is distinct from local, finished-image, CI and live evidence; this command neither executes proof commands nor grants provider authority.', 'Historical accepted artifacts are references only and are never rewritten by this inventory.']}

def markdown(value):
    lines = ['# Delivery coverage inventory', '', f"Revision: `{value['source_revision']}`; input digest: `{value['input_digest']}`.", '', f"{value['summary']['entrypoints']} entrypoints; {value['summary']['routes']} requirement scopes; {value['summary']['gaps']} gaps. Source coverage: **{value['verdict']}**.", '', '| Kind | Count |', '| --- | ---: |']
    lines += [f'| {kind} | {count} |' for kind, count in sorted(value['summary']['kinds'].items())]
    lines += ['', '| Requirement scope | Classification | Declaration coverage |', '| --- | --- | --- |']
    lines += [f"| {route['id']} | {route['classification']} | {route['coverage']} |" for route in value['routes']]
    lines += ['', '## Executable delivery chains', '', '| Scope | Requirement | Package proof | Target proof | Acceptance/run proof |', '| --- | --- | --- | --- | --- |']
    for route in value['routes']:
        for requirement in route['chain']:
            cells = [route['id'], requirement['requirement']]
            for stage in ('package', 'target', 'run'):
                cells.append(', '.join(requirement['proofs'][stage]) or 'N/A: ' + requirement['not_applicable'].get(stage + '_proofs', 'not declared'))
            lines.append('| ' + ' | '.join(str(cell).replace('|', r'\|') for cell in cells) + ' |')
    lines += ['', '## Workflows and images', '', '| Entrypoint | Classification | Requirement scopes |', '| --- | --- | --- |']
    lines += [f"| `{item['path']}` | {item['classification']} | {', '.join(item['routes']) or 'not applicable to declared delivery scopes'} |" for item in value['entrypoints'] if item['kind'] in {'ci-workflow', 'image-definition'}]
    lines += ['', '## Gaps', '']
    lines += [f"- `{item['code']}`: `{item['path']}` {item.get('reference', '')}" for item in value['findings']] or ['None.']
    lines += ['', 'The JSON view contains every discovered command, workflow, program, image, target, binding and template, its registration sources, input hashes and requirement chains. This is source coverage, not live proof.']
    return '\n'.join(lines)
