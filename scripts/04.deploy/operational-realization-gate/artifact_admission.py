"""Admit authenticated artifact evidence for one gate, never grant operation authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.artifact-admission
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind cryptographically verified provenance, SBOM and scan evidence to exact artifact and source policy.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import json
from pathlib import Path
import re
import time

import build_contracts
import release_compiler as release
import artifact_verifier as verifier

SCHEMAS = ('artifact-admission-policy', 'artifact-admission-result',
           'artifact-verifier-lock', 'artifact-scan-predicate')


def validate(name, document):
    try:
        return build_contracts.validate_schema(name, document)
    except release.ReleaseFailure:
        verifier.fail('policy-invalid' if name == 'artifact-admission-policy' else 'schema-invalid')


def bindings():
    return {
        'runner_digest': release.digest_document({name: verifier.digest(verifier.read_bytes(verifier.ROOT / name))
            for name in ('artifact_verifier.py', 'artifact_admission.py', 'artifact_admission_cli.py',
                         'artifact_verifier_conformance.py', 'build_contracts.py', 'release_compiler.py',
                         'requirements.lock')}),
        'schema_digests': {name: release.digest_document(release.load_document(
            build_contracts.SCHEMA_DIR / (name + '.schema.yml'), 'schema-invalid')) for name in SCHEMAS},
        'lock_digest': verifier.digest(verifier.read_bytes(verifier.ROOT / 'artifact-verifier.lock.json')),
    }


def initial(now):
    result = {'schema': 'artifact-admission-result/v1', 'scope': 'artifact-supply-chain',
              'authorized': False, 'release_eligibility': 'blocked', 'operation_authorization': 'blocked',
              'qualification_verdict': 'blocked', 'verdict': 'blocked', 'policy_digest': None,
              'subject_digest': None, 'verifier_digest': None, 'trusted_root_digest': None,
              'verified_evidence': [], 'evidence_digests': {'provenance': None, 'sbom': None, 'scan': None},
              'observed_at': now, 'findings': [], 'image_config_digest': None,
              **bindings()}
    return result


def finish(result, code=None):
    if code:
        result['findings'] = [{'code': code}]
    result['result_digest'] = release.digest_document({key: value for key, value in result.items()
                                                     if key != 'result_digest'})
    validate('artifact-admission-result', result)
    return result


def validate_policy(policy, now, lock):
    validate('artifact-admission-policy', policy)
    if (policy['scan']['scanner_version'] is None or policy['scan']['maximum_age_seconds'] is None
            or policy['trust_root_maximum_age_seconds'] is None):
        verifier.fail('policy-incomplete')
    age = now - lock['trusted_root_observed_at']
    if age < 0 or age > policy['trust_root_maximum_age_seconds']:
        verifier.fail('trust-root-expired')
    return policy


def manifest(artifact, expected_digest, image_config):
    """An OCI manifest is a different object from Docker's config/image ID."""
    if verifier.digest(artifact) != expected_digest:
        verifier.fail('artifact-digest-mismatch')
    try:
        value = verifier.json_bytes(artifact)
        allowed = {'application/vnd.oci.image.manifest.v1+json',
                   'application/vnd.docker.distribution.manifest.v2+json'}
        if (not isinstance(value, dict) or value.get('schemaVersion') != 2
                or isinstance(value.get('schemaVersion'), bool)
                or value.get('mediaType') not in allowed):
            verifier.fail('artifact-manifest-invalid')
        config, layers = value['config'], value['layers']
        if not isinstance(layers, list) or not layers or len(layers) > 256:
            verifier.fail('artifact-manifest-invalid')
        for row in [config, *layers]:
            if (not isinstance(row, dict) or not isinstance(row.get('digest'), str)
                    or not re.fullmatch(r'sha256:[0-9a-f]{64}', row['digest'])
                    or type(row.get('size')) is not int or row['size'] < 0
                    or row.get('urls') or row.get('data')):
                verifier.fail('artifact-manifest-invalid')
        if (config['digest'] == expected_digest or not isinstance(image_config, bytes)
                or verifier.digest(image_config) != config['digest'] or len(image_config) != config['size']):
            verifier.fail('artifact-manifest-invalid')
        settings = verifier.json_bytes(image_config)
        if (not isinstance(settings, dict) or settings.get('os') != 'linux'
                or settings.get('architecture') != 'amd64' or settings.get('variant')):
            verifier.fail('artifact-manifest-invalid')
    except (KeyError, TypeError):
        verifier.fail('artifact-manifest-invalid')


def check_provenance(statement, policy):
    try:
        predicate = statement['predicate']
        definition = predicate['buildDefinition']
        expected = {'repository': 'https://github.com/' + policy['repository'],
                    'ref': policy['ref'], 'path': policy['workflow']}
        if (definition['externalParameters']['workflow'] != expected
                or definition['buildType'] != 'https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1'
                or predicate['runDetails']['builder']['id'] != 'https://github.com/actions/runner/github-hosted'):
            verifier.fail('provenance-mismatch')
        materials = definition['resolvedDependencies']
        source = {'uri': 'git+https://github.com/' + policy['repository'] + '@' + policy['ref'],
                  'digest': {'gitCommit': policy['source_commit']}}
        if not isinstance(materials, list) or sum(row == source for row in materials) != 1:
            verifier.fail('provenance-mismatch')
        observed = set()
        for row in materials:
            if not isinstance(row, dict) or not isinstance(row.get('uri'), str):
                verifier.fail('provenance-mismatch')
            if row['uri'].startswith(('pkg:docker/', 'docker://')):
                material = row.get('digest')
                if (not isinstance(material, dict) or set(material) != {'sha256'}
                        or not isinstance(material['sha256'], str)
                        or not re.fullmatch(r'[0-9a-f]{64}', material['sha256'])):
                    verifier.fail('provenance-mismatch')
                bound = 'sha256:' + material['sha256']
                if bound in observed:
                    verifier.fail('provenance-mismatch')
                observed.add(bound)
            elif row != source:
                verifier.fail('provenance-mismatch')
        if set(policy['bases'].values()) != observed:
            verifier.fail('provenance-mismatch')
    except (KeyError, TypeError):
        verifier.fail('provenance-mismatch')


def check_sbom(statement):
    try:
        document = statement['predicate']
        if (document.get('spdxVersion') != 'SPDX-2.3' or document.get('SPDXID') != 'SPDXRef-DOCUMENT'
                or document.get('dataLicense') != 'CC0-1.0' or document.get('externalDocumentRefs')
                or not isinstance(document.get('packages'), list) or not document['packages']):
            verifier.fail('sbom-invalid')
        identifiers = set()
        for package in document['packages']:
            identifier = package.get('SPDXID')
            if (not isinstance(identifier, str) or not re.fullmatch(r'SPDXRef-[A-Za-z0-9.-]+', identifier)
                    or identifier in identifiers or not isinstance(package.get('name'), str)
                    or not package['name']):
                verifier.fail('sbom-invalid')
            identifiers.add(identifier)
        # This verifies signed SBOM shape and binding, not independent component completeness.
    except (KeyError, TypeError, AttributeError):
        verifier.fail('sbom-invalid')


def check_scan(statement, policy, now):
    scan = statement['predicate']
    try:
        build_contracts.validate_schema('artifact-scan-predicate', scan)
    except release.ReleaseFailure:
        verifier.fail('scan-invalid')
    if (scan['subject_digest'] != policy['subject']['digest'] or scan['source_commit'] != policy['source_commit']
            or scan['bases'] != policy['bases']):
        verifier.fail('scan-binding-mismatch')
    if scan['scanner'] != {'id': policy['scan']['scanner_id'], 'version': policy['scan']['scanner_version']}:
        verifier.fail('scan-version-mismatch')
    if max(scan['scanned_at'], scan['vulnerability_database_updated_at']) > now:
        verifier.fail('scan-future')
    if min(scan['scanned_at'], scan['vulnerability_database_updated_at']) < now - policy['scan']['maximum_age_seconds']:
        verifier.fail('scan-stale')
    if scan['vulnerability_database_updated_at'] > scan['scanned_at']:
        verifier.fail('scan-invalid')
    if scan['counts']['critical'] or scan['counts']['high'] or scan['counts']['undefined']:
        verifier.fail('scan-vulnerable')


def admit(policy, artifact, bundles, cache, image_config):
    """Re-verify raw signed inputs each invocation; no saved-result admission path."""
    now = int(time.time())
    result = initial(now)
    try:
        lock, _ = verifier.load_lock()
        result.update(verifier_digest=lock['binary_digest'], trusted_root_digest=lock['trusted_root_digest'])
        validate_policy(policy, now, lock)
        result.update(policy_digest=release.digest_document(policy), subject_digest=policy['subject']['digest'])
        manifest(artifact, policy['subject']['digest'], image_config)
        result['image_config_digest'] = verifier.digest(image_config)
        if not isinstance(bundles, dict) or set(bundles) != {'provenance', 'sbom', 'scan'}:
            verifier.fail('input-invalid')
        for name, predicate in [('provenance', verifier.PROVENANCE), ('sbom', verifier.SBOM), ('scan', verifier.SCAN)]:
            expected = verifier.expected_identity(policy['repository'], policy['ref'], policy['workflow'],
                                                  policy['source_commit'], policy['subject']['name'],
                                                  policy['subject']['digest'], predicate)
            statement = verifier.verify_bundle(cache, artifact, bundles[name], expected)
            if name == 'provenance':
                check_provenance(statement, policy)
            elif name == 'sbom':
                check_sbom(statement)
            else:
                check_scan(statement, policy, now)
            result['verified_evidence'].append(name)
            result['evidence_digests'][name] = verifier.digest(bundles[name])
        if bindings() != {key: result[key] for key in ('runner_digest', 'schema_digests', 'lock_digest')}:
            verifier.fail('input-changed')
        result['verdict'] = 'verified'
        return finish(result)
    except verifier.AdmissionFailure as error:
        return finish(result, error.code)
    except Exception:
        return finish(result, 'input-invalid')
