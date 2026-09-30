#!/usr/bin/env python3
"""Join literal package exports to genuine compiler output and runtime projection."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-package-exports
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Derive source-bound runtime exports from actual compiler emission while retaining runtime and owner obligations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-local-runtime
#     path: scripts/04.deploy/operational-realization-gate/local_runtime.py

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import posixpath

from jsonschema import Draft202012Validator

import release_compiler as release
import source_coverage
import local_build_contracts as contracts
import build_artifacts as artifacts
from package_export_inventory import collect, NAME, SUBPATH, revision
from source_inventory import SourceFailure, canonical, checked_document, digest

SCHEMA_DIR = release.SCHEMA_DIR
SHARED_HELPER = 'scripts/04.deploy/build-platform-shell-image/workspace-runtime.mjs'
PROJECTION_INPUT = '.release-control-workspace-projection.json'
RUNTIME_DRIVER = '.release-control-workspace-driver.mjs'
SCHEMAS = ('source-package-export-inventory', 'local-workspace-export-projection', 'local-package-export-reconciliation')
# Existing source-only executable alias: not a manifest export, owner approval,
# or an extensible caller-provided exception list. All four sources are checked.
SERVER_ALIAS = {
    'configuration': 'platform/server/tsconfig.image.json',
    'specifier': '@kanbien/platform-server/main', 'package': '@kanbien/platform-server', 'subpath': './main',
    'manifest': 'platform/server/package.json', 'target': 'platform/server/src/main.ts',
    'consumer': 'infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts',
}


def validate(name, value):
    if name not in SCHEMAS and name != 'local-workspace-runtime-observation':
        raise SourceFailure('package-export-schema-unsupported')
    schema = release.load_document(SCHEMA_DIR / (name + '.schema.yml'), 'package-export-schema-unavailable')
    if (schema.get('$schema') != 'https://json-schema.org/draft/2020-12/schema'
            or schema.get('$id') != 'urn:release-control:' + name + ':v1'
            or schema.get('properties', {}).get('schema') != {'const': name + '/v1'}):
        raise SourceFailure('package-export-schema-invalid')
    stack = [schema]
    while stack:
        part = stack.pop()
        if isinstance(part, dict):
            if (any(key in part for key in ('$ref', '$dynamicRef', '$recursiveRef'))
                    or ('properties' in part or part.get('type') == 'object')
                    and (part.get('type') != 'object' or part.get('additionalProperties') is not False
                         or set(part.get('required', [])) != set(part.get('properties', {})))):
                raise SourceFailure('package-export-schema-invalid')
            stack.extend(part.values())
        elif isinstance(part, list):
            stack.extend(part)
    release.bounded_json(value, max_nodes=500000)
    Draft202012Validator.check_schema(schema)
    if next(Draft202012Validator(schema).iter_errors(value), None):
        raise SourceFailure('package-export-document-invalid')
    return digest(canonical(schema))


def policy_revision():
    directory = Path(__file__).parent
    schema_names = SCHEMAS + ('local-workspace-runtime-observation', 'package-export-error',
                             'local-typescript-emission-observation', 'local-typescript-observation')
    return digest(canonical([revision(), digest((directory.parents[2] / SHARED_HELPER).read_bytes()),
        *[digest((directory / name).read_bytes()) for name in (
            'package_exports.py', 'package_exports_cli.py', 'local_build_contracts.py',
            'build_contracts.py', 'source_coverage.py', 'release_compiler.py', 'typescript_observer.mjs')],
        *[digest((SCHEMA_DIR / (name + '.schema.yml')).read_bytes()) for name in schema_names]]))


def seal(value, field):
    value[field] = digest(canonical({key: item for key, item in value.items() if key != field}))
    return value


def fingerprint(files):
    return [{'path': path, 'digest': digest(raw), 'bytes': len(raw)} for path, raw in sorted(files.items())]


def check_digest(document, field):
    if document.get(field) != digest(canonical({key: value for key, value in document.items() if key != field})):
        raise SourceFailure('package-export-digest-invalid')


def read(root, relative):
    descriptor = artifacts.open_root(root)
    try:
        return artifacts.read_relative(descriptor, relative)
    finally:
        os.close(descriptor)


def generated_files(projection):
    """Compute all expected bytes; no arbitrary source command is interpreted."""
    validate('local-workspace-export-projection', projection)
    check_digest(projection, 'projection_digest')
    packages, files = {}, {}
    seen = set()
    for row in projection['entries']:
        name, subpath, target = row['package_name'], row['subpath'], row['output_path']
        if (not NAME.fullmatch(name) or not SUBPATH.fullmatch(subpath)
                or not artifacts.safe_path(target) or artifacts.private_path(target)
                or target.startswith('node_modules/') or not target.endswith(('.js', '.cjs'))
                or (name, subpath) in seen):
            raise SourceFailure('package-export-projection-unsafe')
        seen.add((name, subpath))
        package_root = 'node_modules/' + name
        shim = package_root + ('/index.js' if subpath == '.' else '/' + subpath[2:] + '/index.js')
        relative = posixpath.relpath(target, posixpath.dirname(shim))
        if not relative.startswith('.'):
            relative = './' + relative
        files[shim] = ('module.exports = require(' + json.dumps(relative) + ');\n').encode()
        exports = packages.setdefault(name, {})
        exports[subpath] = './index.js' if subpath == '.' else './' + subpath[2:] + '/index.js'
    for name, exports in sorted(packages.items()):
        files['node_modules/' + name + '/package.json'] = (
            json.dumps({'name': name, 'type': 'commonjs', 'exports': dict(sorted(exports.items()))}, indent=2) + '\n').encode()
    paths = set(files)
    if any('/'.join(path.split('/')[:count]) in paths for path in paths for count in range(1, len(path.split('/')))):
        raise SourceFailure('package-export-projection-collision')
    if len(files) > artifacts.MAX_FILES:
        raise SourceFailure('package-export-limit-exceeded')
    return files


def alias_binding(root, observation, inventory, bindings, output_root):
    """Keep the existing executable alias distinct from literal package exports."""
    if observation['configuration'] != SERVER_ALIAS['configuration']:
        return None
    alias = SERVER_ALIAS
    manifests = [row for row in bindings if row['manifest_path'] == alias['manifest']]
    if not manifests or any(row['package_name'] != alias['package'] for row in manifests):
        raise SourceFailure('package-export-alias-manifest-invalid')
    # A future manifest declaration must take the declaration route, never two
    # competing mappings for the same specifier.
    if any(row['subpath'] == alias['subpath'] for row in manifests):
        return None
    configuration = checked_document(read(root, alias['configuration']), json_only=True)
    options = configuration.get('compilerOptions', {}) if isinstance(configuration, dict) else {}
    if (options.get('baseUrl') != '../..'
            or options.get('paths', {}).get(alias['specifier']) != [alias['target']]):
        raise SourceFailure('package-export-alias-config-invalid')
    inputs = {row['path']: row for row in observation['inputs']}
    evidence = []
    for path in (alias['configuration'], alias['consumer'], alias['target']):
        raw = read(root, path)
        actual = inputs.get(path)
        if (actual is None or actual['kind'] != 'repository' or actual['digest'] != digest(raw)
                or actual['bytes'] != len(raw)):
            raise SourceFailure('package-export-alias-source-invalid')
        evidence.append({'path_digest': digest(path.encode()), 'source_digest': digest(raw)})
    resolutions = [row for row in observation['resolutions']
                   if row['from'] == alias['consumer'] and row['specifier_digest'] == digest(alias['specifier'].encode())]
    if (len(resolutions) != 1 or resolutions[0]['resolved_path'] != alias['target']
            or resolutions[0]['is_external']):
        raise SourceFailure('package-export-alias-resolution-invalid')
    source_digest = inputs[alias['target']]['digest']
    emitted = contracts.runtime_emission(observation, alias['target'], output_root,
                                        source_digest=source_digest, configuration=alias['configuration'])
    identity = digest(canonical(['executable-alias/v1', alias, evidence, resolutions[0]]))
    return ({'kind': 'executable-alias', 'declaration_id': identity, 'package_name': alias['package'],
             'subpath': alias['subpath'], 'source_path': alias['target'], 'source_digest': source_digest,
             'output_path': emitted['path'][len(output_root) + 1:], 'output_digest': emitted['digest'],
             'output_bytes': emitted['bytes']},
            {'id': identity, 'route': 'source-bound-executable-alias', 'source_bindings': evidence,
             'resolution_digest': digest(canonical(resolutions[0])), 'qualification': 'unqualified'})


def prepare_projection(root, observation, compiled_root):
    """Fresh internal seam. Caller owns compiler/dependency acquisition trust.

    This API does not accept a saved export map, waiver or owner declaration.
    Direct callers obtain an observation by actual verify-existing emit; the
    locked parent supplies its just-completed isolated compiler observation.
    """
    revision_before = policy_revision()
    contracts.observation(observation)
    contracts.emission_map_binding(observation, require_commonjs=True)
    if (observation['schema'] != 'local-typescript-emission-observation/v1'
            or observation['verdict'] != 'passed' or observation['no_emit'] or observation['emit_skipped']):
        raise SourceFailure('package-export-emission-required')
    configuration = observation['configuration']
    if configuration not in contracts.RUNTIME_LAYOUTS:
        raise SourceFailure('package-export-configuration-unsupported')
    output_root = contracts.RUNTIME_LAYOUTS[configuration][0]
    inventory, bindings = collect(root)
    validate('source-package-export-inventory', inventory)
    check_digest(inventory, 'inventory_digest')
    if inventory['findings']:
        raise SourceFailure('package-export-source-unresolved')
    sources = {row['id']: row for row in inventory['sources']}
    exports = {row['id']: row for row in inventory['exports']}
    inputs = {row['path']: row for row in observation['inputs']}
    outputs = {row['path']: row for row in observation['outputs']}
    if (len(inputs) != len(observation['inputs']) or len(outputs) != len(observation['outputs'])
            or any(not path.startswith(output_root + '/') for path in outputs)):
        raise SourceFailure('package-export-compiler-membership-invalid')
    actual = artifacts.artifact_files(Path(compiled_root) / output_root)
    compiler_files = {}
    for path, output in outputs.items():
        relative = path[len(output_root) + 1:]
        raw = actual.get(relative)
        if raw is None or output['digest'] != digest(raw) or output['bytes'] != len(raw):
            raise SourceFailure('package-export-compiler-bytes-invalid')
        compiler_files[relative] = raw
    entries, rows = [], []
    for binding in bindings:
        export = exports[binding['id']]
        source = sources[export['target_source_id']]
        specifier = binding['package_name'] + ('' if binding['subpath'] == '.' else binding['subpath'][1:])
        required_resolutions = [row for row in observation['resolutions']
                                if row['specifier_digest'] == digest(specifier.encode())]
        # TypeScript's external-library flag also marks npm workspace links.
        # Trust the exact canonical declared target only; the repository input
        # kind, current source digest and unique actual emission are required
        # below regardless of that classification. node_modules origins cannot
        # satisfy those joins.
        if any(row['resolved_path'] != binding['target_path'] for row in required_resolutions):
            raise SourceFailure('package-export-required-resolution-invalid')
        if binding['target_path'] not in inputs and not required_resolutions:
            rows.append({'export_id': export['id'], 'selection': 'outside-selected-compilation',
                         'output_digest': None, 'output_path_digest': None, 'qualification': 'unqualified'})
            continue
        if digest(read(root, binding['target_path'])) != source['digest']:
            raise SourceFailure('package-export-source-changed')
        emitted = contracts.runtime_emission(observation, binding['target_path'], output_root,
                                            source_digest=source['digest'], configuration=configuration)
        entries.append({'kind': 'package-export', 'declaration_id': export['id'],
                        'package_name': binding['package_name'], 'subpath': binding['subpath'],
                        'source_path': binding['target_path'], 'source_digest': source['digest'],
                        'output_path': emitted['path'][len(output_root) + 1:],
                        'output_digest': emitted['digest'], 'output_bytes': emitted['bytes']})
        rows.append({'export_id': export['id'], 'selection': 'emitted', 'output_digest': emitted['digest'],
                     'output_path_digest': digest(emitted['path'].encode()), 'qualification': 'unqualified'})
    if not entries:
        raise SourceFailure('package-export-empty-selection')
    aliases = []
    alias = alias_binding(root, observation, inventory, bindings, output_root)
    if alias is not None:
        entries.append(alias[0])
        aliases.append(alias[1])
    projection = seal({'schema': 'local-workspace-export-projection/v1', 'scope': 'compiler-bound-runtime-exports',
                       'authorized': False, 'configuration': configuration, 'output_root': output_root,
                       'source_inventory_digest': inventory['source_inventory_digest'],
                       'export_inventory_digest': inventory['inventory_digest'],
                       'compiler_observation_digest': observation['observation_digest'],
                       'policy_revision': revision_before, 'compiler_files': fingerprint(compiler_files),
                       'entries': sorted(entries, key=lambda row: (row['package_name'], row['subpath']))}, 'projection_digest')
    generated = generated_files(projection)
    remainder = {path: raw for path, raw in actual.items() if path not in compiler_files}
    reported = observation['existing_remainder']
    normalized = [{'path': output_root + '/' + row['path'], 'digest': row['digest'], 'bytes': row['bytes']}
                  for row in fingerprint(remainder)]
    if normalized != reported or (observation['output_mode'] == 'fresh-exclusive' and remainder):
        raise SourceFailure('package-export-remainder-mismatch')
    # Empty is the first preparation. Complete exact generated bytes is a repeat.
    # Partial remnants or arbitrary extra files never acquire compiler authority.
    if remainder and remainder != generated:
        raise SourceFailure('package-export-unexpected-output')
    if set(compiler_files) & set(generated):
        raise SourceFailure('package-export-output-collision')
    receipt = seal({'schema': 'local-package-export-reconciliation/v1', 'scope': 'compiler-export-reconciliation',
                    'authorized': False, 'release_eligibility': 'blocked', 'operation_authorization': 'blocked',
                    'qualification_verdict': 'blocked', 'source_closure': 'blocked', 'review_verdict': 'not-evaluated',
                    'configuration': configuration, 'source_inventory_digest': inventory['source_inventory_digest'],
                    'export_inventory_digest': inventory['inventory_digest'],
                    'compiler_observation_digest': observation['observation_digest'],
                    'projection_digest': projection['projection_digest'], 'policy_revision': revision_before,
                    'declared_exports': len(rows), 'selected_exports': sum(row['selection'] == 'emitted' for row in rows),
                    'outside_selected_exports': sum(row['selection'] == 'outside-selected-compilation' for row in rows),
                    'exports': sorted(rows, key=lambda row: row['export_id']), 'aliases': aliases,
                    'generated_files': fingerprint(generated), 'source_findings': inventory['source_findings'],
                    'structural_verdict': 'accounted', 'findings': []}, 'receipt_digest')
    validate('local-package-export-reconciliation', receipt)
    if collect(root)[0]['inventory_digest'] != inventory['inventory_digest'] or policy_revision() != revision_before:
        raise SourceFailure('package-export-source-changed')
    if artifacts.artifact_files(Path(compiled_root) / output_root) != actual:
        raise SourceFailure('package-export-artifact-changed')
    return projection, receipt


def check_reconciliation(document):
    validate('local-package-export-reconciliation', document)
    check_digest(document, 'receipt_digest')
    rows = document['exports']
    if (len({row['export_id'] for row in rows}) != len(rows)
            or document['declared_exports'] != len(rows)
            or document['selected_exports'] != sum(row['selection'] == 'emitted' for row in rows)
            or document['outside_selected_exports'] != sum(row['selection'] == 'outside-selected-compilation' for row in rows)
            or not document['selected_exports']
            or any((row['output_digest'] is not None or row['output_path_digest'] is not None)
                   if row['selection'] == 'outside-selected-compilation' else
                   (row['output_digest'] is None or row['output_path_digest'] is None) for row in rows)
            or len({row['path'] for row in document['generated_files']}) != len(document['generated_files'])
            or len({row['id'] for row in document['aliases']}) != len(document['aliases'])
            or any(len(row['source_bindings']) != 3 for row in document['aliases'])):
        raise SourceFailure('package-export-reconciliation-invalid')
    return document


def check_runtime(document):
    validate('local-workspace-runtime-observation', document)
    check_digest(document, 'receipt_digest')
    exports = check_reconciliation(document['workspace_exports'])
    actual = {row['path']: row for row in document['artifact_files']}
    if (len(actual) != len(document['artifact_files'])
            or exports['configuration'] != document['configuration']
            or len(document['generator_helpers']) != 1
            or document['generator_helpers'][0]['path'] != SHARED_HELPER
            or document['execution_driver_digest'] != digest(driver_bytes(document['configuration']))
            or any(actual.get(row['path']) != row for row in exports['generated_files'])):
        raise SourceFailure('package-export-runtime-binding-invalid')
    return document


def validate_current_projection(projection, root, observation):
    """Final direct-command boundary; a self-hash is never a fresh source join."""
    generated = generated_files(projection)
    if not isinstance(observation, dict) or observation.get('output_mode') != 'verify-existing':
        raise SourceFailure('package-export-current-observation-required')
    expected, _receipt = prepare_projection(root, observation, root)
    if projection != expected:
        raise SourceFailure('package-export-current-projection-mismatch')
    if projection['policy_revision'] != policy_revision():
        raise SourceFailure('package-export-policy-stale')
    inventory, _bindings = collect(root)
    if (projection['source_inventory_digest'] != inventory['source_inventory_digest']
            or projection['export_inventory_digest'] != inventory['inventory_digest']
            or inventory['findings']):
        raise SourceFailure('package-export-source-stale')
    actual = artifacts.artifact_files(Path(root) / projection['output_root'])
    compiler = {row['path']: row for row in projection['compiler_files']}
    if len(compiler) != len(projection['compiler_files']):
        raise SourceFailure('package-export-compiler-membership-invalid')
    for path, row in compiler.items():
        raw = actual.get(path)
        if raw is None or digest(raw) != row['digest'] or len(raw) != row['bytes']:
            raise SourceFailure('package-export-compiler-bytes-invalid')
    remainder = {path: raw for path, raw in actual.items() if path not in compiler}
    if remainder and remainder != generated:
        raise SourceFailure('package-export-unexpected-output')
    for entry in projection['entries']:
        raw = read(root, entry['source_path'])
        output = compiler.get(entry['output_path'])
        if (digest(raw) != entry['source_digest'] or output is None
                or output['digest'] != entry['output_digest'] or output['bytes'] != entry['output_bytes']):
            raise SourceFailure('package-export-projection-binding-invalid')
    return projection


def driver_bytes(configuration):
    if configuration not in contracts.RUNTIME_LAYOUTS:
        raise SourceFailure('package-export-configuration-unsupported')
    generator = contracts.RUNTIME_LAYOUTS[configuration][2]
    return ("import {readFileSync} from 'node:fs';\n"
            "import {runPreparedGenerator} from './" + SHARED_HELPER + "';\n"
            "await runPreparedGenerator(" + json.dumps(configuration) + ", " + json.dumps(generator)
            + ", readFileSync(" + json.dumps(PROJECTION_INPUT) + "));\n").encode()
