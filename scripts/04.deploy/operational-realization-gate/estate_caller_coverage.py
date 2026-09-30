#!/usr/bin/env python3
"""Reconcile freshly parsed caller facts; source review cannot waive unknown code."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-estate-caller-coverage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Resolve bounded dispatch structure while preserving raw findings, child semantics and pending adoption.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-source-coverage
#     path: scripts/04.deploy/operational-realization-gate/source_coverage.py

from __future__ import annotations

from pathlib import Path
import source_coverage as coverage
import release_compiler as release
from estate_caller_inventory import CONTEXT, RULES, discover_estate_callers, revision
from source_inventory import canonical, digest, discover


def _checked_graph(inventory, graph):
    """Validate internal freshly collected data, never admit an uploaded graph."""
    coverage.validate_schema('source-inventory', inventory)
    coverage.validate_schema('estate-caller-inventory', graph)
    if digest(canonical({k: v for k, v in inventory.items() if k != 'inventory_digest'})) != inventory['inventory_digest']:
        raise coverage.CoverageFailure('inventory-digest-invalid')
    if digest(canonical({k: v for k, v in graph.items() if k != 'graph_digest'})) != graph['graph_digest']:
        raise coverage.CoverageFailure('estate-caller-graph-digest-invalid')
    if graph['source_inventory_digest'] != inventory['inventory_digest']:
        raise coverage.CoverageFailure('estate-caller-inventory-stale')
    if graph['collector_revision'] != revision():
        raise coverage.CoverageFailure('estate-caller-collector-stale')
    sources = coverage.unique(inventory['sources'], 'id')
    observations = coverage.unique(inventory['observations'], 'id')
    graph_sources = coverage.unique(graph['sources'], 'id')
    nodes = coverage.unique(graph['nodes'], 'id')
    edges = coverage.unique(graph['edges'], 'id')
    for sid, source in graph_sources.items():
        if source['id'] != digest(source['path'].encode()):
            raise coverage.CoverageFailure('estate-caller-source-identity-invalid')
        if sid in sources and source != sources[sid]:
            raise coverage.CoverageFailure('estate-caller-source-stale')
    if any(node['source_id'] not in graph_sources for node in nodes.values()):
        raise coverage.CoverageFailure('estate-caller-source-unknown')
    if any(edge['caller_id'] not in nodes or edge['callee_id'] not in nodes for edge in edges.values()):
        raise coverage.CoverageFailure('estate-caller-edge-invalid')
    if any(row['subject_id'] not in nodes for row in graph['findings']):
        raise coverage.CoverageFailure('estate-caller-finding-invalid')
    for edge in edges.values():
        if edge['id'] != digest(canonical([edge['caller_id'], edge['callee_id'], edge['kind'], edge['call_digest']])):
            raise coverage.CoverageFailure('estate-caller-edge-identity-invalid')
    roots = coverage.unique(graph['root_bindings'], 'node_id')
    expected = {item['id'] for item in observations.values()
                if item['kind'] == 'package-command' and sources[item['source_id']]['path'] == 'package.json'}
    expected.update(item['id'] for item in observations.values()
                    if item['kind'] == 'source-file'
                    and sources[item['source_id']]['path'].startswith('.github/workflows/')
                    and sources[item['source_id']]['path'].endswith(('.yaml', '.yml')))
    if not graph['diagnostics'] and {row['observation_id'] for row in roots.values()} != expected:
        raise coverage.CoverageFailure('estate-caller-root-coverage-incomplete')
    for node_id, row in roots.items():
        observed = observations.get(row['observation_id'])
        node = nodes.get(node_id)
        expected_kind = 'package-invocation' if row['kind'] == 'package-command' else 'workflow'
        if (observed is None or node is None or node['kind'] != expected_kind
                or node['source_id'] != observed['source_id']
                or observed['kind'] != ('source-file' if row['kind'] == 'workflow' else 'package-command')):
            raise coverage.CoverageFailure('estate-caller-root-invalid')
    reached = set(roots)
    while True:
        previous = set(reached)
        reached.update(edge['callee_id'] for edge in edges.values() if edge['caller_id'] in reached)
        if reached == previous:
            break
    if reached != set(nodes):
        raise coverage.CoverageFailure('estate-caller-unreachable-subject')
    links = coverage.unique(graph['observation_links'], 'node_id')
    coverage.unique(graph['observation_links'], 'observation_id')
    for nid, row in links.items():
        node, observed = nodes.get(nid), observations.get(row['observation_id'])
        if (node is None or observed is None or node['source_id'] != observed['source_id']
                or node['kind'] != observed['kind'] or node['detail_digest'] != observed['detail_digest']
                or node['locator_digest'] != observed['locator_digest']):
            raise coverage.CoverageFailure('estate-caller-observation-link-invalid')
    invocations = coverage.unique(graph['invocations'], 'node_id')
    if set(invocations) != {node['id'] for node in nodes.values() if node['kind'] == 'package-invocation'}:
        raise coverage.CoverageFailure('estate-caller-context-coverage-incomplete')
    for nid, invocation in invocations.items():
        node, body = nodes[nid], nodes.get(invocation['command_node_id'])
        if (body is None or body['kind'] != 'package-command' or body['source_id'] != node['source_id']
                or node['detail_digest'] != digest(canonical({
                    'command_node_id': body['id'], 'lifecycle': invocation['lifecycle'], 'context': CONTEXT}))
                or node['locator_digest'] != digest(canonical(['package-invocation', body['id'], invocation['lifecycle']]))
                or node['id'] != digest(canonical([node['source_id'], 'package-invocation',
                                                  ['package-invocation', body['id'], invocation['lifecycle']]]))):
            raise coverage.CoverageFailure('estate-caller-context-invalid')
        outgoing = [edge for edge in edges.values() if edge['caller_id'] == nid]
        body_edges = [edge for edge in outgoing if edge['kind'] == 'invokes']
        if (len(body_edges) != 1 or body_edges[0]['callee_id'] != body['id']
                or body_edges[0]['call_digest'] != digest(canonical(['package-body', body['id']]))
                or not invocation['lifecycle'] and any(edge['kind'] != 'invokes' for edge in outgoing)):
            raise coverage.CoverageFailure('estate-caller-context-edges-invalid')
        if nid in roots and (not invocation['lifecycle'] or roots[nid]['observation_id'] != body['id']):
            raise coverage.CoverageFailure('estate-caller-root-context-invalid')
    for edge in edges.values():
        if edge['kind'] in {'npm-pre', 'npm-post'}:
            parent, child = invocations.get(edge['caller_id']), invocations.get(edge['callee_id'])
            if parent is None or child is None or not parent['lifecycle'] or child['lifecycle']:
                raise coverage.CoverageFailure('estate-caller-hook-context-invalid')
    proofs = coverage.unique(graph['structural_proofs'], 'observation_id')
    coverage.unique(graph['structural_proofs'], 'node_id')
    for oid, proof in proofs.items():
        observed, node = observations.get(oid), nodes.get(proof['node_id'])
        if (graph['diagnostics'] or observed is None or node is None
                or node['issues'] or observed['issues'] != ['opaque-executable']
                or links.get(node['id'], {}).get('observation_id') != oid
                or any(f['subject_id'] == node['id'] for f in graph['findings'])
                or proof['source_digest'] != sources[observed['source_id']]['digest']
                or proof['context_digest'] != digest(canonical(CONTEXT))):
            raise coverage.CoverageFailure('estate-caller-proof-invalid')
        outgoing = {eid for eid, edge in edges.items() if edge['caller_id'] == node['id']}
        incoming = {eid for eid, edge in edges.items() if edge['callee_id'] == node['id']}
        if (set(proof['outgoing_edge_ids']) != outgoing or set(proof['incoming_edge_ids']) != incoming
                or not outgoing):
            raise coverage.CoverageFailure('estate-caller-proof-edge-incomplete')
        if proof['rule'] == RULES[0]:
            if node['kind'] != 'package-command' or sources[node['source_id']]['path'] != 'package.json':
                raise coverage.CoverageFailure('estate-caller-proof-rule-mismatch')
        elif proof['rule'] == RULES[1]:
            if node['kind'] != 'script-entrypoint' or len(outgoing) != 1 or edges[next(iter(outgoing))]['kind'] != 'invokes':
                raise coverage.CoverageFailure('estate-caller-proof-rule-mismatch')
        else:
            raise coverage.CoverageFailure('estate-caller-proof-rule-mismatch')
    return observations, nodes, links, proofs


def policy_revision():
    try:
        return digest(canonical([revision(), *[digest(Path(path).read_bytes()) for path in (
            __file__, coverage.__file__, release.__file__,
            coverage.SCHEMA_DIR / 'source-inventory.schema.yml',
            coverage.SCHEMA_DIR / 'estate-caller-inventory.schema.yml',
            coverage.SCHEMA_DIR / 'estate-caller-reconciliation.schema.yml')]]))
    except OSError:
        raise coverage.CoverageFailure('estate-caller-policy-unreadable') from None


def reconcile_estate(root: Path, inventory=None):
    """Public Python seam recollects the graph; it accepts no saved proof input.

    An optional inventory is the caller's independently collected source snapshot.
    It must match a new collection. Declarations and review statuses never enter
    structural resolution. Arbitrary code and runtime behavior stay unqualified.
    """
    before_policy = policy_revision()
    inventory = discover(root) if inventory is None else inventory
    graph = discover_estate_callers(root)
    observations, nodes, links, proofs = _checked_graph(inventory, graph)
    resolved = set(proofs)
    raw = {(row['code'], row['source_id']) for row in inventory['findings']}
    raw.update((code, row['source_id']) for row in observations.values() for code in row['issues'])
    cleared = set()
    for code, sid in raw:
        affected = {row['id'] for row in observations.values()
                    if row['source_id'] == sid and code in row['issues']}
        if code == 'opaque-executable' and affected and affected <= resolved:
            cleared.add((code, sid))
    boundaries = {(row['code'], row['subject_id']) for row in graph['findings']}
    boundaries.update((code, node['id']) for node in nodes.values() for code in node['issues'])
    boundaries.update((row['code'], 'estate-callers') for row in graph['diagnostics'])
    # A reachable implementation outside the broad estate scan cannot disappear
    # simply because its wrapper parsed. Future import/operation units must bind it.
    boundaries.update(('estate-caller-subject-unrepresented', node['id']) for node in nodes.values()
                      if node['kind'] not in {'workflow', 'configuration', 'package-invocation'} and node['id'] not in links)
    result = {
        'schema': 'estate-caller-reconciliation/v1', 'scope': 'structural-caller-reconciliation',
        'authorized': False, 'release_eligibility': 'blocked', 'operation_authorization': 'blocked',
        'qualification_verdict': 'blocked', 'review_verdict': 'not-evaluated',
        'inventory_digest': inventory['inventory_digest'], 'graph_digest': graph['graph_digest'],
        'collector_revision': graph['collector_revision'],
        'policy_revision': before_policy,
        'roots': len(graph['root_bindings']), 'nodes': len(nodes), 'edges': len(graph['edges']),
        'resolved_observations': [{'observation_id': oid, 'node_id': proofs[oid]['node_id'],
                                  'rule': proofs[oid]['rule'], 'proof_digest': digest(canonical(proofs[oid]))}
                                 for oid in sorted(proofs)],
        'raw_source_findings': [{'code': code, 'source_id': sid} for code, sid in sorted(raw)],
        'resolved_source_findings': [{'code': code, 'source_id': sid} for code, sid in sorted(cleared)],
        'remaining_source_findings': [{'code': code, 'source_id': sid} for code, sid in sorted(raw - cleared)],
        'boundary_findings': [{'code': code, 'subject_id': sid} for code, sid in sorted(boundaries)],
        'structural_verdict': 'blocked' if raw - cleared or boundaries else 'accounted',
    }
    result['result_digest'] = digest(canonical(result))
    coverage.validate_schema('estate-caller-reconciliation', result)
    if policy_revision() != before_policy:
        raise coverage.CoverageFailure('estate-caller-policy-changed')
    return result
