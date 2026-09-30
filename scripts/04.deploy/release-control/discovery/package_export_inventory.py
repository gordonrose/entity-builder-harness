#!/usr/bin/env python3
"""Collect literal workspace exports independently, retaining executable opacity."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control-package-export-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind independently discovered literal export declarations to source bytes without approving implementation behavior.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-package-exports
#     path: scripts/04.deploy/operational-realization-gate/package_exports.py

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re

import build_artifacts as artifacts
from source_inventory import SourceFailure, EXCLUDED, canonical, checked_document, digest, discover

MAX_EXPORTS = 10000
NAME = re.compile(r"(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*\Z")
SUBPATH = re.compile(r"(?!.*(?:^|/)node_modules(?:/|$))\.(?:/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*)?\Z", re.IGNORECASE)
TARGET = re.compile(r"\./[A-Za-z0-9_./-]+\Z")
EXTENSIONS = {'.ts', '.tsx', '.mts', '.cts', '.js', '.mjs', '.cjs'}


def revision():
    directory = Path(__file__).parent
    return digest(canonical([digest((directory / name).read_bytes()) for name in (
        'package_export_inventory.py', 'source_inventory.py', 'cloudformation_inventory.py', 'build_artifacts.py')]))


def read_source(root_fd, row):
    raw = artifacts.read_relative(root_fd, row['path'])
    if digest(raw) != row['digest']:
        raise SourceFailure('package-export-source-changed')
    return raw


def collect(root):
    """Return safe inventory plus private validated projection inputs.

    The private bindings contain literal package names/subpaths for generating
    runtime files. Public inventory contains only their digests. No declaration
    is executed, no source finding is waived, and no owner is inferred.
    """
    root = Path(root).absolute()
    before_revision = revision()
    before = discover(root)
    sources = {row['id']: row for row in before['sources']}
    by_path = {row['path']: row for row in before['sources']}
    observations = {row['id']: row for row in before['observations']}
    exports, bindings, manifests, used, findings, names = [], [], [], set(), set(), {}
    root_fd = artifacts.open_root(root)
    try:
        for source in sorted(sources.values(), key=lambda row: row['path']):
            if PurePosixPath(source['path']).name != 'package.json':
                continue
            sid = source['id']
            used.add(sid)
            try:
                document = checked_document(read_source(root_fd, source), json_only=True)
                if not isinstance(document, dict):
                    raise SourceFailure('package-export-manifest-invalid')
            except (SourceFailure, OSError):
                findings.add(('package-export-manifest-unreadable', sid))
                continue
            unsupported = any(key in document for key in ('main', 'module', 'browser', 'imports', 'bin'))
            if unsupported:
                findings.add(('package-export-field-unsupported', sid))
            if 'exports' not in document:
                continue
            name, declared = document.get('name'), document['exports']
            if not isinstance(name, str) or not NAME.fullmatch(name):
                findings.add(('package-export-name-invalid', sid))
                continue
            names.setdefault(name, []).append(sid)
            manifests.append({'source_id': sid, 'name_digest': digest(canonical(name))})
            if isinstance(declared, str):
                candidates = [('.', declared, ['exports'])]
            elif isinstance(declared, dict) and declared:
                candidates = [(key, value, ['exports', key]) for key, value in declared.items()]
            else:
                findings.add(('package-export-shape-unsupported', sid))
                continue
            for subpath, target, locator in candidates:
                if len(exports) >= MAX_EXPORTS:
                    raise SourceFailure('package-export-limit-exceeded')
                if (not isinstance(subpath, str) or not SUBPATH.fullmatch(subpath)
                        or not isinstance(target, str) or not TARGET.fullmatch(target)
                        or any(part in {'', '.', '..'} | EXCLUDED for part in target[2:].split('/'))
                        or PurePosixPath(target).suffix not in EXTENSIONS):
                    findings.add(('package-export-shape-unsupported', sid))
                    continue
                relative = str(PurePosixPath(source['path']).parent / target[2:])
                target_source = by_path.get(relative)
                if target_source is None:
                    findings.add(('package-export-target-unavailable', sid))
                    continue
                try:
                    read_source(root_fd, target_source)
                except (SourceFailure, OSError):
                    findings.add(('package-export-target-unavailable', sid))
                    continue
                oid = digest(canonical([sid, 'package-export', locator]))
                observed = observations.get(oid)
                if (observed is None or observed['detail_digest'] != digest(canonical(target))
                        or observed['locator_digest'] != digest(canonical(locator))):
                    findings.add(('package-export-observation-mismatch', sid))
                    continue
                used.add(target_source['id'])
                row = {'id': oid, 'manifest_source_id': sid, 'target_source_id': target_source['id'],
                       'package_name_digest': digest(canonical(name)), 'subpath_digest': digest(canonical(subpath)),
                       'declaration_digest': observed['detail_digest'], 'qualification': 'unqualified'}
                exports.append(row)
                bindings.append({'id': oid, 'package_name': name, 'subpath': subpath,
                                 'manifest_path': source['path'], 'target_path': relative})
        for ids in names.values():
            if len(ids) > 1:
                findings.update(('package-export-name-ambiguous', sid) for sid in ids)
    finally:
        import os
        os.close(root_fd)
    if before['inventory_digest'] != discover(root)['inventory_digest'] or before_revision != revision():
        raise SourceFailure('package-export-source-changed')
    result = {'schema': 'source-package-export-inventory/v1', 'scope': 'literal-package-exports',
              'authorized': False, 'qualification_verdict': 'blocked', 'source_closure': 'blocked',
              'source_inventory_digest': before['inventory_digest'], 'collector_revision': before_revision,
              'sources': sorted((sources[sid] for sid in used), key=lambda row: row['id']),
              'manifests': sorted(manifests, key=lambda row: row['source_id']),
              'exports': sorted(exports, key=lambda row: row['id']),
              'findings': [{'code': code, 'source_id': sid} for code, sid in sorted(findings)],
              'source_findings': before['findings'],
              'structural_verdict': 'blocked' if findings else 'collected'}
    result['inventory_digest'] = digest(canonical(result))
    return result, sorted(bindings, key=lambda row: row['id'])


def discover_exports(root):
    return collect(root)[0]
