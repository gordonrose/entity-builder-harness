"""Exercise maintained signature verification on a public, genuinely signed fixture."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.artifact-verifier-conformance
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove offline cryptographic verification and refusal paths without claiming production artifact qualification.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.artifact-admission-cli
#     path: scripts/04.deploy/operational-realization-gate/artifact_admission_cli.py

import base64
from copy import deepcopy
import json
import time

import build_contracts
import release_compiler as release
import artifact_verifier as verifier
import artifact_admission as admission


def fixture_expected():
    return verifier.expected_identity(
        'actions/attest-demo', 'refs/heads/main', '.github/workflows/build-python.yml',
        'a6c23b9806c593664f68637c8f9d45dfcf98b2db', 'github_provenance_demo-0.0.12-py3-none-any.whl',
        'sha256:ae57936def59bc4c75edd3a837d89bcefc6d3a5e31d55a6fa7a71624f92c3c3b', verifier.PROVENANCE)


def conformance(cache):
    bindings = admission.bindings()
    schema_path = build_contracts.SCHEMA_DIR / 'artifact-verifier-conformance.schema.yml'
    conformance_schema_digest = verifier.digest(verifier.read_bytes(schema_path))
    artifact = verifier.read_bytes(verifier.FIXTURES / 'upstream-artifact.whl')
    bundle = verifier.read_bytes(verifier.FIXTURES / 'upstream-provenance.bundle.jsonl')
    expected = fixture_expected()
    cases = []
    statement = verifier.verify_bundle(cache, artifact, bundle, expected)
    cases.append({'id': 'authentic-offline-signature', 'outcome': 'verified'})
    negatives = []
    for field, value in [('repository', 'other/repository'), ('ref', 'refs/heads/other'),
                         ('workflow', '.github/workflows/other.yml'), ('commit', '0' * 40),
                         ('subject_name', 'different-artifact'), ('predicate', verifier.SBOM)]:
        changed = dict(expected, **{field: value})
        negatives.append(('wrong-' + field.replace('_', '-'), artifact, bundle, changed))
    negatives.append(('modified-artifact', artifact + b'x', bundle, expected))
    original = verifier.json_bytes(bundle)
    for field in ('signature', 'payload', 'certificate', 'timestamp'):
        changed = deepcopy(original)
        if field == 'signature':
            changed['dsseEnvelope']['signatures'][0]['sig'] = base64.b64encode(b'invalid-signature').decode()
        elif field == 'payload':
            changed['dsseEnvelope']['payload'] = base64.b64encode(b'{}').decode()
        elif field == 'certificate':
            changed['verificationMaterial']['certificate']['rawBytes'] = base64.b64encode(b'invalid-certificate').decode()
        else:
            changed['verificationMaterial'].pop('timestampVerificationData')
        negatives.append(('modified-' + field, artifact, json.dumps(changed).encode(), expected))
    for name, subject, raw, policy in negatives:
        try:
            verifier.verify_bundle(cache, subject, raw, policy)
        except verifier.AdmissionFailure:
            cases.append({'id': name, 'outcome': 'rejected'})
        else:
            verifier.fail('verifier-output-invalid')
    lock, _ = verifier.load_lock()
    if (admission.bindings() != bindings
            or verifier.digest(verifier.read_bytes(schema_path)) != conformance_schema_digest):
        verifier.fail('input-changed')
    result = {**bindings, 'conformance_schema_digest': conformance_schema_digest, 'schema': 'artifact-verifier-conformance/v1', 'scope': 'public-upstream-signature-fixture',
              'authorized': False, 'release_eligibility': 'blocked', 'operation_authorization': 'blocked',
              'qualification_verdict': 'blocked', 'production_admission': 'unproven', 'verdict': 'passed',
              'artifact_digest': verifier.digest(artifact), 'bundle_digest': verifier.digest(bundle),
              'verified_statement_digest': release.digest_document(statement),
              'verifier_digest': lock['binary_digest'], 'trusted_root_digest': lock['trusted_root_digest'],
              'observed_at': int(time.time()), 'cases': cases}
    result['result_digest'] = release.digest_document(result)
    build_contracts.validate_schema('artifact-verifier-conformance', result)
    return result
