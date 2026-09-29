"""Focused artifact-policy and authenticated evidence semantics tests."""
import copy
import json
from unittest import TestCase, main, mock

import artifact_admission as admission
import artifact_verifier as verifier
import release_compiler as release

NOW = 1790726400


IMAGE_CONFIG = b'{"architecture":"amd64","os":"linux"}'


def fixtures():
    manifest = json.dumps({'schemaVersion': 2, 'mediaType': 'application/vnd.oci.image.manifest.v1+json',
                          'config': {'digest': verifier.digest(IMAGE_CONFIG), 'size': len(IMAGE_CONFIG)},
                          'layers': [{'digest': 'sha256:' + '2' * 64, 'size': 20}]}).encode()
    policy = {'schema': 'artifact-admission-policy/v1', 'target_id': 'kanbien-staging',
              'repository': 'gordonrose/entity-builder-harness', 'ref': 'refs/heads/main',
              'workflow': '.github/workflows/deploy-platform-shell-staging.yml',
              'source_commit': 'a' * 40, 'platform': 'linux/amd64',
              'subject': {'name': '337159794548.dkr.ecr.eu-west-1.amazonaws.com/platform-shell',
                          'digest': verifier.digest(manifest), 'kind': 'oci-manifest'},
              'bases': {'build_digest': 'sha256:' + 'b' * 64, 'runtime_digest': 'sha256:' + 'c' * 64},
              'scan': {'scanner_id': 'aws-ecr-basic', 'scanner_version': 'fixture-version-1',
                       'maximum_age_seconds': 3600}, 'trust_root_maximum_age_seconds': 3600}
    provenance = {'predicate': {'buildDefinition': {
        'buildType': 'https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1',
        'externalParameters': {'workflow': {'repository': 'https://github.com/' + policy['repository'],
                                           'ref': policy['ref'], 'path': policy['workflow']}},
        'resolvedDependencies': [{'uri': 'git+https://github.com/' + policy['repository'] + '@' + policy['ref'],
                                  'digest': {'gitCommit': policy['source_commit']}},
                                 {'uri': 'pkg:docker/node', 'digest': {'sha256': 'b' * 64}},
                                 {'uri': 'pkg:docker/distroless', 'digest': {'sha256': 'c' * 64}}]},
        'runDetails': {'builder': {'id': 'https://github.com/actions/runner/github-hosted'}}}}
    sbom = {'predicate': {'spdxVersion': 'SPDX-2.3', 'SPDXID': 'SPDXRef-DOCUMENT', 'dataLicense': 'CC0-1.0',
                         'packages': [{'SPDXID': 'SPDXRef-package1', 'name': 'fixture-package'}]}}
    scan = {'predicate': {'schema': 'artifact-scan-predicate/v1', 'subject_digest': policy['subject']['digest'],
                         'source_commit': policy['source_commit'], 'bases': dict(policy['bases']),
                         'scanner': {'id': 'aws-ecr-basic', 'version': 'fixture-version-1'},
                         'scan_status': 'COMPLETE', 'scanned_at': NOW, 'vulnerability_database_updated_at': NOW,
                         'counts': dict.fromkeys(('critical', 'high', 'medium', 'low', 'informational', 'undefined'), 0)}}
    return policy, manifest, {'provenance': provenance, 'sbom': sbom, 'scan': scan}


class AdmissionTests(TestCase):
    def setUp(self):
        self.policy, self.artifact, self.statements = fixtures()
        self.config = IMAGE_CONFIG
        self.bundles = {key: key.encode() for key in self.statements}
        self.lock, root = verifier.load_lock()
        self.lock = dict(self.lock, trusted_root_observed_at=NOW)
        self.lock_patch = mock.patch.object(verifier, 'load_lock', return_value=(self.lock, root))
        self.lock_patch.start(); self.addCleanup(self.lock_patch.stop)
        self.clock = mock.patch.object(admission.time, 'time', return_value=NOW)
        self.clock.start(); self.addCleanup(self.clock.stop)
        self.crypto = mock.patch.object(verifier, 'verify_bundle', side_effect=lambda cache, artifact, bundle, expected:
                                       self.statements[bundle.decode()])
        self.crypto_mock = self.crypto.start(); self.addCleanup(self.crypto.stop)

    def result(self):
        return admission.admit(self.policy, self.artifact, self.bundles, '/unused-in-policy-tests', self.config)

    def assertBlocked(self, code):
        result = self.result()
        self.assertEqual('blocked', result['verdict'])
        self.assertEqual([{'code': code}], result['findings'])
        self.assertFalse(result['authorized'])
        return result

    def test_authenticated_three_family_semantics_preserve_authority_boundary(self):
        result = self.result()
        self.assertEqual('verified', result['verdict'])
        self.assertEqual(['provenance', 'sbom', 'scan'], result['verified_evidence'])
        self.assertEqual('blocked', result['release_eligibility'])
        self.assertEqual('blocked', result['operation_authorization'])
        self.assertEqual('blocked', result['qualification_verdict'])
        self.assertEqual(release.digest_document({k: v for k, v in result.items() if k != 'result_digest'}), result['result_digest'])

    def test_missing_scanner_version_blocks_before_crypto(self):
        self.policy['scan']['scanner_version'] = None
        self.assertBlocked('policy-incomplete'); self.crypto_mock.assert_not_called()

    def test_missing_scan_age_blocks(self):
        self.policy['scan']['maximum_age_seconds'] = None
        self.assertBlocked('policy-incomplete')

    def test_missing_root_freshness_blocks(self):
        self.policy['trust_root_maximum_age_seconds'] = None
        self.assertBlocked('policy-incomplete')

    def test_expired_trust_root(self):
        self.lock['trusted_root_observed_at'] = NOW - 3601
        self.assertBlocked('trust-root-expired')

    def test_future_trust_root(self):
        self.lock['trusted_root_observed_at'] = NOW + 1
        self.assertBlocked('trust-root-expired')

    def test_wrong_production_repository(self):
        self.policy['repository'] = 'actions/attest-demo'
        self.assertBlocked('policy-invalid')

    def test_other_branch_is_not_authorized_policy(self):
        self.policy['ref'] = 'refs/heads/unreviewed'
        self.assertBlocked('policy-invalid')

    def test_extra_unsafe_field(self):
        self.policy['secret'] = 'SECRET-DO-NOT-ECHO'
        result = self.assertBlocked('policy-invalid')
        self.assertNotIn('SECRET-DO-NOT-ECHO', json.dumps(result))

    def test_boolean_scan_age(self):
        self.policy['scan']['maximum_age_seconds'] = True
        self.assertBlocked('policy-invalid')

    def test_altered_manifest(self):
        self.artifact += b' '
        self.assertBlocked('artifact-digest-mismatch')

    def test_config_object_is_not_manifest(self):
        self.artifact = b'{"architecture":"amd64","os":"linux"}'
        self.policy['subject']['digest'] = verifier.digest(self.artifact)
        self.assertBlocked('artifact-manifest-invalid')

    def test_image_index_not_supported_as_single_platform_manifest(self):
        value = json.loads(self.artifact); value['mediaType'] = 'application/vnd.oci.image.index.v1+json'
        self.artifact = json.dumps(value).encode(); self.policy['subject']['digest'] = verifier.digest(self.artifact)
        self.assertBlocked('artifact-manifest-invalid')

    def test_foreign_layer_url_rejected(self):
        value = json.loads(self.artifact); value['layers'][0]['urls'] = ['https://attacker.invalid/image']
        self.artifact = json.dumps(value).encode(); self.policy['subject']['digest'] = verifier.digest(self.artifact)
        self.assertBlocked('artifact-manifest-invalid')

    def test_missing_bundle_family(self):
        del self.bundles['scan']
        self.assertBlocked('input-invalid')

    def test_signature_verification_failure(self):
        self.crypto_mock.side_effect = verifier.AdmissionFailure('verifier-failed')
        self.assertBlocked('verifier-failed')

    def test_missing_actual_base_materials(self):
        self.statements['provenance']['predicate']['buildDefinition']['resolvedDependencies'] = self.statements['provenance']['predicate']['buildDefinition']['resolvedDependencies'][:1]
        self.assertBlocked('provenance-mismatch')

    def test_wrong_source_material(self):
        self.statements['provenance']['predicate']['buildDefinition']['resolvedDependencies'][0]['digest']['gitCommit'] = 'e' * 40
        self.assertBlocked('provenance-mismatch')

    def test_duplicate_source_material(self):
        rows = self.statements['provenance']['predicate']['buildDefinition']['resolvedDependencies']; rows.append(copy.deepcopy(rows[0]))
        self.assertBlocked('provenance-mismatch')

    def test_wrong_workflow(self):
        self.statements['provenance']['predicate']['buildDefinition']['externalParameters']['workflow']['path'] = '.github/workflows/other.yml'
        self.assertBlocked('provenance-mismatch')

    def test_untrusted_builder(self):
        self.statements['provenance']['predicate']['runDetails']['builder']['id'] = 'https://untrusted.invalid/builder'
        self.assertBlocked('provenance-mismatch')

    def test_empty_sbom(self):
        self.statements['sbom']['predicate']['packages'] = []
        self.assertBlocked('sbom-invalid')

    def test_duplicate_sbom_packages(self):
        rows = self.statements['sbom']['predicate']['packages']; rows.append(dict(rows[0]))
        self.assertBlocked('sbom-invalid')

    def test_unresolved_external_sbom(self):
        self.statements['sbom']['predicate']['externalDocumentRefs'] = [{'externalDocumentId': 'other'}]
        self.assertBlocked('sbom-invalid')

    def test_invalid_spdx_version(self):
        self.statements['sbom']['predicate']['spdxVersion'] = 'future'
        self.assertBlocked('sbom-invalid')

    def test_unsigned_scan_flag_does_not_replace_schema(self):
        self.statements['scan']['predicate'] = {'verified': True, 'critical': 0}
        self.assertBlocked('scan-invalid')

    def test_scan_wrong_source(self):
        self.statements['scan']['predicate']['source_commit'] = 'd' * 40
        self.assertBlocked('scan-binding-mismatch')

    def test_scan_wrong_base(self):
        self.statements['scan']['predicate']['bases']['build_digest'] = 'sha256:' + 'd' * 64
        self.assertBlocked('scan-binding-mismatch')

    def test_unknown_scanner_version(self):
        self.statements['scan']['predicate']['scanner']['version'] = None
        self.assertBlocked('scan-version-mismatch')

    def test_stale_scan(self):
        self.statements['scan']['predicate']['scanned_at'] = NOW - 3601
        self.assertBlocked('scan-stale')

    def test_stale_vulnerability_database(self):
        self.statements['scan']['predicate']['vulnerability_database_updated_at'] = NOW - 3601
        self.assertBlocked('scan-stale')

    def test_future_scan(self):
        self.statements['scan']['predicate']['scanned_at'] = NOW + 1
        self.assertBlocked('scan-future')

    def test_critical_vulnerability(self):
        self.statements['scan']['predicate']['counts']['critical'] = 1
        self.assertBlocked('scan-vulnerable')

    def test_high_vulnerability_without_exception(self):
        self.statements['scan']['predicate']['counts']['high'] = 1
        self.assertBlocked('scan-vulnerable')

    def test_unknown_severity_blocks(self):
        self.statements['scan']['predicate']['counts']['undefined'] = 1
        self.assertBlocked('scan-vulnerable')

    def test_negative_vulnerability_count(self):
        self.statements['scan']['predicate']['counts']['critical'] = -1
        self.assertBlocked('scan-invalid')

    def test_low_findings_permitted_by_current_policy(self):
        self.statements['scan']['predicate']['counts']['low'] = 5
        self.assertEqual('verified', self.result()['verdict'])

    def test_every_invocation_reverifies_all_evidence(self):
        self.result(); self.result()
        self.assertEqual(6, self.crypto_mock.call_count)

    def test_wrong_image_configuration_bytes(self):
        self.config += b' '
        self.assertBlocked('artifact-manifest-invalid')

    def test_other_architecture_even_when_digest_matches(self):
        self.config = b'{"architecture":"arm64","os":"linux"}'
        manifest = json.loads(self.artifact)
        manifest['config'] = {'digest': verifier.digest(self.config), 'size': len(self.config)}
        self.artifact = json.dumps(manifest).encode()
        self.policy['subject']['digest'] = verifier.digest(self.artifact)
        self.assertBlocked('artifact-manifest-invalid')

    def test_other_operating_system_even_when_digest_matches(self):
        self.config = b'{"architecture":"amd64","os":"windows"}'
        manifest = json.loads(self.artifact)
        manifest['config'] = {'digest': verifier.digest(self.config), 'size': len(self.config)}
        self.artifact = json.dumps(manifest).encode()
        self.policy['subject']['digest'] = verifier.digest(self.artifact)
        self.assertBlocked('artifact-manifest-invalid')

    def test_manifest_config_size_is_verified(self):
        manifest = json.loads(self.artifact); manifest['config']['size'] += 1
        self.artifact = json.dumps(manifest).encode(); self.policy['subject']['digest'] = verifier.digest(self.artifact)
        self.assertBlocked('artifact-manifest-invalid')

    def test_undeclared_base_material(self):
        self.statements['provenance']['predicate']['buildDefinition']['resolvedDependencies'].append(
            {'uri': 'pkg:docker/unreviewed', 'digest': {'sha256': 'f' * 64}})
        self.assertBlocked('provenance-mismatch')

    def test_duplicate_base_material(self):
        rows = self.statements['provenance']['predicate']['buildDefinition']['resolvedDependencies']
        rows.append(copy.deepcopy(rows[-1]))
        self.assertBlocked('provenance-mismatch')

    def test_policy_cannot_select_other_platform(self):
        self.policy['platform'] = 'linux/arm64'
        self.assertBlocked('policy-invalid')

    def test_source_change_during_verification_blocks(self):
        before = admission.bindings(); after = copy.deepcopy(before); after['runner_digest'] = 'sha256:' + '0' * 64
        with mock.patch.object(admission, 'bindings', side_effect=[before, after]):
            self.assertBlocked('input-changed')

    def test_schema_change_during_verification_blocks(self):
        before = admission.bindings(); after = copy.deepcopy(before)
        after['schema_digests']['artifact-admission-policy'] = 'sha256:' + '0' * 64
        with mock.patch.object(admission, 'bindings', side_effect=[before, after]):
            self.assertBlocked('input-changed')

    def test_tool_lock_change_during_verification_blocks(self):
        before = admission.bindings(); after = copy.deepcopy(before); after['lock_digest'] = 'sha256:' + '0' * 64
        with mock.patch.object(admission, 'bindings', side_effect=[before, after]):
            self.assertBlocked('input-changed')

    def test_competing_commit_for_selected_source_uri(self):
        rows = self.statements['provenance']['predicate']['buildDefinition']['resolvedDependencies']
        row = copy.deepcopy(rows[0]); row['digest']['gitCommit'] = 'f' * 40; rows.append(row)
        self.assertBlocked('provenance-mismatch')

    def test_unreviewed_material_kind(self):
        self.statements['provenance']['predicate']['buildDefinition']['resolvedDependencies'].append(
            {'uri': 'https://unknown.invalid/code', 'digest': {'sha256': 'f' * 64}})
        self.assertBlocked('provenance-mismatch')

    def test_database_snapshot_must_exist_when_scan_completes(self):
        self.statements['scan']['predicate']['scanned_at'] = NOW - 1800
        self.assertBlocked('scan-invalid')

    def test_source_result_consumer_cannot_grant_authority(self):
        import result_consumption
        for purpose in ('source-analysis', 'release-eligibility', 'operation-authorization'):
            self.assertEqual('rejected', result_consumption.consume_result(self.result(), purpose)['verdict'])


if __name__ == '__main__':
    main()
