"""Adversarial local image proof accounting tests; no daemon or network calls."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.local-container-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Reject stale, forged, skipped and cross-command local container evidence.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate.smoke-test
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_container_contracts as contracts
import release_compiler as release

FIXTURES = Path(__file__).resolve().parent / 'fixtures/local-containers'
OTHER = 'sha256:' + 'd' * 64


def fixture():
    return json.loads((FIXTURES / 'valid-result.json').read_text()), json.loads((FIXTURES / 'pending-profiles.json').read_text())


def seal(value):
    value['result_digest'] = contracts.digest({k: v for k, v in value.items() if k != 'result_digest'})
    return value


class ContainerContractTests(unittest.TestCase):
    def setUp(self):
        self.value, self.profiles = fixture()
        self.production = deepcopy(self.value["payload"]["production_dependencies"])

    def reject(self, change, reseal=True):
        change(self.value)
        if reseal:
            seal(self.value)
        with self.assertRaises(release.ReleaseFailure):
            contracts.validate_result(self.value, self.profiles, self.production)

    def test_complete_fixture_validates_without_authority(self):
        actual = contracts.validate_result(self.value, self.profiles, self.production)
        self.assertFalse(actual['authorized'])
        self.assertEqual([r['status'] for r in actual['profiles']], ['local-health-passed', 'pending', 'pending'])

    def test_docker_configuration_identity_is_also_supported(self):
        self.value['base']['image_id'] = self.value['lock']['runtime_config_digest']
        contracts.validate_result(seal(self.value), self.profiles, self.production)

    def test_unknown_envelope_field_rejects(self): self.reject(lambda v: v.update(secret='redacted-fixture'))
    def test_unknown_nested_field_rejects(self): self.reject(lambda v: v['runtime'].update(raw_output='fixture'))
    def test_authorization_rejects(self): self.reject(lambda v: v.update(authorized=True))
    def test_release_eligibility_rejects(self): self.reject(lambda v: v.update(release_eligibility='eligible'))
    def test_operation_authority_rejects(self): self.reject(lambda v: v.update(operation_authorization='authorized'))
    def test_source_closure_rejects(self): self.reject(lambda v: v.update(source_closure='complete'))
    def test_release_qualification_rejects(self): self.reject(lambda v: v.update(qualification_verdict='qualified'))
    def test_skipped_execution_rejects(self): self.reject(lambda v: v['runtime'].update(verdict='skipped'))
    def test_wrong_image_rejects(self): self.reject(lambda v: v['runtime'].update(image_id=OTHER))
    def test_changed_command_rejects(self): self.reject(lambda v: v['runtime'].update(command=['other.js']))
    def test_changed_entrypoint_rejects(self): self.reject(lambda v: v['runtime'].update(entrypoint=['/bin/sh']))
    def test_network_enabled_rejects(self): self.reject(lambda v: v['runtime']['settings'].update(network='bridge'))
    def test_host_mount_rejects(self): self.reject(lambda v: v['runtime']['settings'].update(host_mounts=['/host']))
    def test_root_execution_rejects(self): self.reject(lambda v: v['runtime']['settings'].update(user='root'))
    def test_missing_health_check_rejects(self): self.reject(lambda v: v['runtime']['checks'].pop())
    def test_failed_health_rejects(self): self.reject(lambda v: v['runtime']['checks'][0].update(status=503))
    def test_timeout_shutdown_rejects(self): self.reject(lambda v: v['runtime']['shutdown'].update(exit_code=137))
    def test_missing_cleanup_rejects(self): self.reject(lambda v: v['runtime'].update(cleanup_verified=False))
    def test_wrong_runtime_major_rejects(self): self.reject(lambda v: v['runtime'].update(node_version='v24.1.0'))
    def test_mutable_runtime_tag_rejects(self): self.reject(lambda v: v['lock'].update(runtime_image='gcr.io/distroless/nodejs22-debian12:nonroot'))
    def test_wrong_base_identity_rejects(self): self.reject(lambda v: v['base'].update(image_id=OTHER))
    def test_base_reference_mismatch_rejects(self): self.reject(lambda v: v['base'].update(repo_digests=['gcr.io/distroless/nodejs22-debian12@'+OTHER]))
    def test_lock_digest_mismatch_rejects(self): self.reject(lambda v: v.update(lock_digest=OTHER))
    def test_wrong_image_payload_digest_rejects(self): self.reject(lambda v: v.update(image_payload_digest=OTHER))
    def test_stale_payload_digest_rejects(self): self.reject(lambda v: v['payload']['files'][0].update(bytes=2))
    def test_outer_digest_tamper_rejects(self): self.reject(lambda v: v.update(repository_head='2'*40), False)
    def test_nested_compiler_digest_tamper_rejects(self): self.reject(lambda v: v['build']['builds'][0]['observation']['outputs'][0].update(bytes=2))
    def test_wrong_environment_commit_rejects(self): self.reject(lambda v: v.update(repository_head='2'*40))
    def test_unknown_environment_rejects(self): self.reject(lambda v: v['image']['environment'].append({'name':'AWS_SECRET_ACCESS_KEY','value':'fixture'}))
    def test_duplicate_environment_rejects(self): self.reject(lambda v: v['image']['environment'].append(v['image']['environment'][0]))
    def test_missing_environment_rejects(self): self.reject(lambda v: v['image']['environment'].pop())
    def test_invalid_timestamp_rejects(self): self.reject(lambda v: v.update(started_at='2026-02-31T00:00:00Z'))
    def test_reversed_time_rejects(self): self.reject(lambda v: v.update(completed_at='2025-01-01T00:00:00Z'))
    def test_missing_profile_rejects(self): self.reject(lambda v: v['profiles'].pop())
    def test_duplicate_profile_rejects(self): self.reject(lambda v: v['profiles'].append(v['profiles'][0]))
    def test_stale_profile_inventory_rejects(self): self.reject(lambda v: v.update(profile_inventory_digest=OTHER))
    def test_bootstrap_cannot_inherit_server_success(self): self.reject(lambda v: v['profiles'][1].update(status='local-health-passed', reason='local-health-verified'))
    def test_external_image_cannot_inherit_server_success(self): self.reject(lambda v: v['profiles'][2].update(status='local-health-passed', reason='local-health-verified'))
    def test_changed_target_source_rejects(self): self.reject(lambda v: v['profiles'][1].update(source_digest=OTHER))
    def test_missing_new_obligation_rejects(self):
        self.profiles.append({**self.profiles[-1], 'id':'new-task'})
        with self.assertRaises(release.ReleaseFailure):contracts.validate_result(self.value,self.profiles,self.production)

    def mutate_payload(self, change):
        def update(value):
            change(value['payload'])
            value['payload']['files'].sort(key=lambda row:row['path'])
            value['payload']['payload_digest']=contracts.digest(value['payload']['files'])
            value['image_payload_digest']=value['payload']['payload_digest']
        self.reject(update)

    def test_missing_compiled_file_rejects_after_resealing(self):self.mutate_payload(lambda p:p['files'].pop(0))
    def test_modified_compiled_byte_rejects_after_resealing(self):self.mutate_payload(lambda p:p['files'][0].update(digest=OTHER))
    def test_path_escape_rejects_after_resealing(self):self.mutate_payload(lambda p:p['files'].append({'path':'../escape','digest':OTHER,'bytes':1}))
    def test_duplicate_payload_rejects_after_resealing(self):self.mutate_payload(lambda p:p['files'].append(p['files'][0]))
    def test_source_fallback_rejects_after_resealing(self):self.mutate_payload(lambda p:p['files'].append({'path':'node_modules/pg/index.ts','digest':OTHER,'bytes':1}))
    def test_extra_payload_file_rejects_after_resealing(self):self.mutate_payload(lambda p:p['files'].append({'path':'arbitrary.txt','digest':OTHER,'bytes':1}))
    def test_certificate_changed_rejects_after_resealing(self):self.mutate_payload(lambda p:next(r for r in p['files'] if r['path']==contracts.CERTIFICATE).update(digest=OTHER))
    def test_production_package_omission_rejects(self):self.reject(lambda v:v['payload']['production_dependencies'].clear())
    def test_extra_undeclared_dependency_rejects(self):self.mutate_payload(lambda p:p['files'].append({'path':'node_modules/other/package.json','digest':OTHER,'bytes':1}))
    def test_dependency_manifest_tamper_rejects(self):self.reject(lambda v:v['payload'].update(production_dependency_digest=OTHER))


    def test_production_version_change_rejects(self):
        self.reject(lambda v:v['payload']['production_dependencies'][0].update(version='99.0.0'))

    def test_dependency_byte_change_cannot_reseal_itself(self):
        def change(v):
            row=next(r for r in v['payload']['files'] if r['path'].startswith('node_modules/'))
            row['digest']=OTHER
            v['payload']['production_dependency_digest']=contracts.digest([r for r in v['payload']['files'] if r['path'].startswith('node_modules/')])
            v['payload']['payload_digest']=contracts.digest(v['payload']['files'])
            v['image_payload_digest']=v['payload']['payload_digest']
        self.reject(change)

    def test_extra_excluded_dependency_rejects(self):
        self.reject(lambda v:v['payload']['excluded_dependency_files'].append({'path':'node_modules/dev/package.json','digest':OTHER,'bytes':1}))

    def test_duplicate_excluded_dependency_rejects(self):
        self.reject(lambda v:v['payload']['excluded_dependency_files'].extend([{'path':'node_modules/dev/package.json','digest':OTHER,'bytes':1}]*2))


if __name__ == '__main__':unittest.main()
