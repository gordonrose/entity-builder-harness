#!/usr/bin/env python3
"""Aggregate existing bounded callers and independently prove literal dispatch."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.estate-caller-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Link whole-estate command observations to bounded caller facts without clearing child semantics.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-estate-caller-coverage
#     path: scripts/04.deploy/operational-realization-gate/estate_caller_coverage.py

from __future__ import annotations

from pathlib import Path
import re

from caller_inventory import CallerCollector, MAX_CALL_DEPTH, safe_path
from source_inventory import SourceFailure, canonical, digest, discover

MAX_ROOTS = 10000
RULES = ('literal-package-command/v1', 'python-dispatch/v1')
CONTEXT = {'cwd': 'repository-root', 'npm_config': 'repository-config-absent-or-blocked', 'runtime_context': 'unqualified',
           'arguments': 'observed-invocations-only', 'execution': 'not-performed'}


def revision():
    directory = Path(__file__).parent
    return digest(canonical([digest((directory / name).read_bytes()) for name in (
        'estate_caller_inventory.py', 'caller_inventory.py', 'source_inventory.py',
        'cloudformation_inventory.py')]))


def python_dispatch(raw):
    """Recognize the existing complete wrapper grammar; never infer from a name."""
    try:
        if any(byte < 32 and byte not in (9, 10) or byte == 127 for byte in raw):
            return None
        lines = [line.strip(' \t') for line in raw.decode('ascii').split('\n')
                 if line.strip(' \t') and not line.lstrip(' \t').startswith('#')]
    except UnicodeError:
        return None
    if len(lines) != 4 or lines[:3] != [
            'set -euo pipefail', 'ROOT="$(git rev-parse --show-toplevel)"', 'cd "$ROOT"']:
        return None
    match = re.fullmatch(r'exec python3(?: -B)? (?:"\$ROOT/([A-Za-z0-9_./-]+)"|([A-Za-z0-9_./-]+)) "\$@"', lines[3])
    target = (match.group(1) or match.group(2)) if match else None
    return target if target and safe_path(target) else None


class EstateCollector(CallerCollector):
    def __init__(self, root):
        super().__init__(root)
        self.dispatches = {}
        self.locators = {}
        self.invocations = {}
        self.package_bodies = set()

    def node(self, source, kind, locator, detail, issues=()):
        node_id = super().node(source, kind, locator, detail, issues)
        self.locators[node_id] = locator
        return node_id

    def block(self, caller, source, locator, value):
        if (not isinstance(value, str) or any(ord(char) > 126
                or ord(char) < 32 and char not in '\t\n' for char in value)):
            self.issue(caller, 'caller-command-encoding-unsupported')
            return
        super().block(caller, source, locator, value)

    def edge(self, caller, callee, kind, call):
        super().edge(caller, callee, kind, call)
        if len(self.edges) > 10000:
            raise SourceFailure('caller-limit-exceeded')

    def package_script(self, name, hooks=True):
        # Body identity remains compatible with source-inventory/v1. Invocation
        # contexts are distinct: npm's automatic hooks do not recursively run
        # their own hooks, whereas an explicit npm run of that name does.
        if self.package_source is None:
            self.package_source, raw, problem = self.read('package.json')
            self.package_problem = problem
            if not problem:
                try:
                    from source_inventory import checked_document
                    self.package = checked_document(raw, json_only=True)
                except SourceFailure:
                    self.package_problem = 'caller-source-parse-failed'
            if not isinstance(self.package, dict) or not isinstance(self.package.get('scripts', {}), dict):
                self.package_problem = self.package_problem or 'caller-package-shape-invalid'
                self.package = {'scripts': {}}
        command = self.package.get('scripts', {}).get(name)
        body = self.node(self.package_source, 'package-command', ['scripts', name], command)
        locator = ['package-invocation', body, hooks]
        context = self.node(self.package_source, 'package-invocation', locator,
                            {'command_node_id': body, 'lifecycle': hooks, 'context': CONTEXT})
        self.invocations[context] = {'node_id': context, 'command_node_id': body, 'lifecycle': hooks}
        self.edge(context, body, 'invokes', ['package-body', body])
        if self.package_problem or not isinstance(command, str):
            code = self.package_problem or 'caller-package-command-missing'
            self.issue(body, code)
            self.issue(context, code)
            return context
        pair = name, hooks
        if pair in self.active:
            self.issue(context, 'caller-cycle')
            return context
        if pair in self.package_done:
            return context
        self.package_done.add(pair)
        if len(self.active) >= MAX_CALL_DEPTH:
            self.issue(context, 'caller-limit-exceeded')
            return context
        config = self.root / '.npmrc'
        if config.exists() or config.is_symlink():
            self.issue(body, 'caller-context-unsupported')
            self.issue(context, 'caller-context-unsupported')
            self.configuration('.npmrc', context)
            return context
        self.active.append(pair)
        try:
            if hooks:
                for prefix, edge_kind in (('pre', 'npm-pre'), ('post', 'npm-post')):
                    if prefix + name in self.package.get('scripts', {}):
                        child = self.package_script(prefix + name, hooks=False)
                        self.edge(context, child, edge_kind, [prefix, name])
            if name not in self.package_bodies:
                self.package_bodies.add(name)
                self.block(body, self.package_source, ['scripts', name], command)
        finally:
            self.active.pop()
        return context

    def script(self, relative, interpreter='bash'):
        node_id = super().script(relative, interpreter)
        if interpreter == 'bash' and relative.endswith('.sh') and relative in self.raw:
            _source, raw, problem = self.raw[relative]
            target = python_dispatch(raw) if not problem else None
            if target:
                self.dispatches[node_id] = target
        return node_id


def discover_estate_callers(root: Path) -> dict:
    """Fresh root/package aggregate, retaining every unknown leaf and context.

    The source inventory is recollected internally. There is no declaration,
    saved graph, allowlist, or accepted proof-file input to this producer.
    """
    root = Path(root).absolute()
    before_revision = revision()
    inventory = discover(root)
    npm_context_before = (root / '.npmrc').exists() or (root / '.npmrc').is_symlink()
    collector = EstateCollector(root)
    roots, diagnostics = [], set()
    sources = {item['id']: item for item in inventory['sources']}
    observations = {item['id']: item for item in inventory['observations']}
    commands = [item for item in inventory['observations']
                if item['kind'] == 'package-command'
                and sources[item['source_id']]['path'] == 'package.json']
    workflows = [item for item in inventory['sources']
                 if item['path'].startswith('.github/workflows/')
                 and item['path'].endswith(('.yml', '.yaml'))]
    try:
        valid_root = root.is_dir() and not root.is_symlink() and root.resolve() == root
    except (OSError, RuntimeError):
        valid_root = False
    if not valid_root:
        diagnostics.add('estate-root-invalid')
    elif len(commands) + len(workflows) > MAX_ROOTS:
        diagnostics.add('estate-caller-limit-exceeded')
    else:
        try:
            # Loading a package root uses the same strict reader and parser as
            # every existing workflow caller; npm configuration is never run.
            if commands:
                source, raw, problem = collector.read('package.json')
                if problem:
                    raise SourceFailure(problem)
                package = collector.parse_document(source, raw, '', json_only=True)
                if not isinstance(package, dict) or not isinstance(package.get('scripts'), dict):
                    raise SourceFailure('caller-package-shape-invalid')
                for name in sorted(package['scripts']):
                    node = collector.package_script(name)
                    observation = digest(canonical([source['id'], 'package-command', ['scripts', name]]))
                    roots.append({'kind': 'package-command', 'node_id': node, 'observation_id': observation})
            for source in sorted(workflows, key=lambda item: item['path']):
                node = collector.workflow(source['path'])
                observation = digest(canonical([source['id'], 'source-file', 'file']))
                roots.append({'kind': 'workflow', 'node_id': node, 'observation_id': observation})
        except (SourceFailure, RecursionError):
            diagnostics.add('estate-caller-collection-incomplete')
    # Any concurrent source change prevents all proposed structural resolutions.
    after = discover(root)
    if after != inventory:
        diagnostics.add('estate-caller-source-changed')
    if npm_context_before != ((root / '.npmrc').exists() or (root / '.npmrc').is_symlink()):
        diagnostics.add('estate-caller-source-changed')
    recheck = CallerCollector(root)
    for sid, source in collector.sources.items():
        fresh_source, _raw, _problem = recheck.read(source['path'])
        if fresh_source != source or sid in sources and source != sources[sid]:
            diagnostics.add('estate-caller-source-changed')
    if revision() != before_revision:
        diagnostics.add('estate-caller-collector-changed')
    # Remove incomplete unattached nodes after a limit failure. The explicit
    # diagnostic remains, and no structural proof survives any diagnostic.
    reached = {row['node_id'] for row in roots}
    while True:
        previous = set(reached)
        reached.update(edge['callee_id'] for edge in collector.edges.values()
                       if edge['caller_id'] in reached)
        if reached == previous:
            break
    nodes = {key: value for key, value in collector.nodes.items() if key in reached}
    edges = {key: value for key, value in collector.edges.items()
             if value['caller_id'] in reached and value['callee_id'] in reached}
    used_sources = {row['source_id'] for row in nodes.values()}
    graph_sources = {key: value for key, value in collector.sources.items() if key in used_sources}
    graph_findings = {(code, node) for code, node in collector.findings if node in reached}
    links, proofs = [], []
    for node_id, node in sorted(nodes.items()):
        matching = observations.get(node_id)
        if (matching is not None and matching['kind'] == node['kind']
                and matching['source_id'] == node['source_id']
                and matching['detail_digest'] == node['detail_digest']
                and matching['locator_digest'] == node['locator_digest']):
            links.append({'node_id': node_id, 'observation_id': matching['id']})
        else:
            matching = None
        if diagnostics or node['issues'] or matching is None:
            continue
        if matching['issues'] != ['opaque-executable']:
            continue
        outgoing = [edge for edge in edges.values() if edge['caller_id'] == node_id]
        rule = None
        if node['kind'] == 'package-command' and sources[node['source_id']]['path'] == 'package.json':
            if outgoing and all(edge['kind'] in {'invokes', 'npm-pre', 'npm-post'} for edge in outgoing):
                rule = RULES[0]
        elif node_id in collector.dispatches:
            target = collector.dispatches[node_id]
            if (len(outgoing) == 1 and outgoing[0]['kind'] == 'invokes'
                    and outgoing[0]['call_digest'] == digest(canonical(['python3', target, 'forward-arguments']))
                    and graph_sources[nodes[outgoing[0]['callee_id']]['source_id']]['path'] == target):
                rule = RULES[1]
        if rule:
            proofs.append({'observation_id': matching['id'], 'node_id': node_id,
                           'source_digest': sources[node['source_id']]['digest'], 'rule': rule,
                           'outgoing_edge_ids': sorted(edge['id'] for edge in outgoing),
                           'incoming_edge_ids': sorted(edge['id'] for edge in edges.values() if edge['callee_id'] == node_id),
                           'context_digest': digest(canonical(CONTEXT))})
    result = {
        'schema': 'estate-caller-inventory/v1', 'scope': 'root-package-and-workflow-callers',
        'source_inventory_digest': inventory['inventory_digest'], 'collector_revision': revision(),
        'root_bindings': sorted(roots, key=lambda item: (item['kind'], item['node_id'])),
        'sources': sorted(graph_sources.values(), key=lambda item: item['id']),
        'nodes': sorted(nodes.values(), key=lambda item: item['id']),
        'edges': sorted(edges.values(), key=lambda item: item['id']),
        'observation_links': sorted(links, key=lambda item: item['node_id']),
        'invocations': [collector.invocations[nid] for nid in sorted(collector.invocations) if nid in nodes],
        'structural_proofs': sorted(proofs, key=lambda item: item['observation_id']),
        'findings': [{'code': code, 'subject_id': node} for code, node in sorted(graph_findings)],
        'diagnostics': [{'code': code} for code in sorted(diagnostics)],
    }
    result['graph_digest'] = digest(canonical(result))
    return result
