#!/usr/bin/env python3
"""Rebase proposed adoption work onto current observations without approving it."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-adoption-migration
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Preserve historical adoption proposals while generating an explicit all-pending current candidate and source delta.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from copy import deepcopy
from pathlib import Path
import source_coverage as coverage
import release_compiler as release


def policy_revision():
    try:
        return release.digest_document([release.digest_document(Path(path).read_text()) for path in (
            __file__, coverage.__file__, release.__file__,
            coverage.SCHEMA_DIR / 'source-inventory.schema.yml',
            coverage.SCHEMA_DIR / 'source-adoption-ledger.schema.yml',
            coverage.SCHEMA_DIR / 'source-adoption-migration.schema.yml')])
    except (OSError, UnicodeError):
        raise coverage.CoverageFailure('adoption-policy-unreadable') from None


def migrate_adoption(inventory, previous):
    """Produce review work only; never write, retire, approve, or delete a source.

    The previous ledger is a proposal input, not authenticated owner authority.
    All current rows remain pending, even if an older row claimed review. Unchanged
    owner/disposition text is retained for human comparison without granting it.
    Removed paths remain visible in the delta and historical ledger.
    """
    before_policy = policy_revision()
    schemas = {name: coverage.validate_schema(name, value) for name, value in (
        ('source-inventory', inventory), ('source-adoption-ledger', previous))}
    release.bounded_json(previous)
    if release.digest_document({key: value for key, value in inventory.items() if key != 'inventory_digest'}) != inventory['inventory_digest']:
        raise coverage.CoverageFailure('inventory-digest-invalid')
    current = coverage.unique(inventory['sources'], 'id')
    old = coverage.unique(previous['entries'], 'source_id')
    entries, changes = [], []
    counts = {'added': 0, 'changed': 0, 'unchanged': 0, 'removed': 0}
    for sid in sorted(set(current) | set(old)):
        prior, source = old.get(sid), current.get(sid)
        status = ('removed' if source is None else 'added' if prior is None else
                  'unchanged' if source['digest'] == prior['source_digest'] else 'changed')
        counts[status] += 1
        changes.append({'source_id': sid, 'change': status,
                        'previous_digest': prior['source_digest'] if prior else None,
                        'current_digest': source['digest'] if source else None})
        if source is None:
            continue
        entry = deepcopy(prior) if prior else {
            'source_id': sid, 'owner': 'release-control-programme', 'disposition': 'migrate'}
        entry.update(source_digest=source['digest'], review_status='pending')
        entries.append(entry)
    candidate = {'schema': 'source-adoption-ledger/v1', 'inventory_digest': inventory['inventory_digest'],
                 'entries': entries}
    coverage.validate_schema('source-adoption-ledger', candidate)
    result = {'schema': 'source-adoption-migration/v1', 'scope': 'pending-adoption-migration',
              'authorized': False, 'release_eligibility': 'blocked', 'operation_authorization': 'blocked',
              'review_verdict': 'pending', 'retirement_authorized': False, 'deletion_authorized': False,
              'prior_ledger_digest': release.digest_document(previous),
              'prior_inventory_digest': previous['inventory_digest'],
              'inventory_digest': inventory['inventory_digest'], 'collector_revision': inventory['collector_revision'],
              'candidate_digest': release.digest_document(candidate), 'candidate': candidate,
              'counts': counts, 'changes': changes,
              'policy_revision': before_policy}
    result['result_digest'] = release.digest_document(result)
    coverage.validate_schema('source-adoption-migration', result)
    if policy_revision() != before_policy:
        raise coverage.CoverageFailure('adoption-policy-changed')
    return result
