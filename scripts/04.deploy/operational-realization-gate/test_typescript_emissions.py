"""Bind actual compiler origins to fresh source and output bytes without release authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.typescript-emissions
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject missing ambiguous stale and non-executable compiler emission mappings.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import local_build
import local_build_contracts as contracts
import release_compiler as release
from test_local_build import observation as legacy,seal,HASH
from test_local_build_bindings import fixture as build_fixture,reseal


def fixture():
    value=legacy();value['schema']='local-typescript-emission-observation/v1'
    value['inputs'].append({'kind':'repository','path':'src/entry.ts','digest':HASH,'bytes':1})
    value['outputs']=[{'path':'.cache/output/actual-name.js','digest':HASH,'bytes':1}]
    value.update(output_mode='fresh-exclusive',existing_remainder=[],emission_map={
        'schema':'local-typescript-emission-map/v1','module_kind':'commonjs','entries':[
            {'output_path':'.cache/output/actual-name.js','source_paths':['src/entry.ts'],'kind':'javascript'}]})
    return seal(value,'observation_digest')


class TypeScriptEmissionContractTests(unittest.TestCase):
    def reject(self,value):
        seal(value,'observation_digest')
        with self.assertRaises(release.ReleaseFailure):contracts.observation(value)

    def lookup(self,value,**changes):
        arguments={'source_path':'src/entry.ts','output_root':'.cache/output','source_digest':HASH,
                   'configuration':'src/tsconfig.json',**changes}
        return contracts.runtime_emission(value,**arguments)

    def test_actual_output_name_is_returned_without_source_name_substitution(self):
        value=fixture();self.assertEqual(self.lookup(value),value['outputs'][0])

    def test_legacy_receipt_readable_but_not_emission_evidence(self):
        contracts.observation(legacy())
        with self.assertRaisesRegex(release.ReleaseFailure,'local-build-emission-required'):
            contracts.emission_map_binding(legacy())

    def test_new_identity_requires_map_and_mode_and_remainder(self):
        for key in ('emission_map','output_mode','existing_remainder'):
            with self.subTest(key=key):
                value=fixture();value.pop(key);self.reject(value)

    def test_unknown_nested_fields_are_rejected(self):
        for target in ('map','entry','remainder'):
            with self.subTest(target=target):
                value=fixture()
                if target=='map':value['emission_map']['password']='PRIVATE_FIXTURE_CANARY'
                elif target=='entry':value['emission_map']['entries'][0]['raw']='PRIVATE_FIXTURE_CANARY'
                else:value['existing_remainder']=[{'path':'.cache/output/extra.js','digest':HASH,'bytes':1,'raw':'PRIVATE_FIXTURE_CANARY'}]
                self.reject(value)

    def test_missing_duplicate_extra_and_out_of_order_emissions_fail(self):
        for mode in ('missing','duplicate','extra','order'):
            with self.subTest(mode=mode):
                value=fixture();rows=value['emission_map']['entries']
                if mode=='missing':rows.clear()
                elif mode=='duplicate':rows.append(deepcopy(rows[0]))
                elif mode=='extra':rows.append({**rows[0],'output_path':'.cache/output/unknown.js'})
                else:
                    value['outputs'].append({'path':'.cache/output/second.js','digest':HASH,'bytes':1})
                    rows.insert(0,{**rows[0],'output_path':'.cache/output/second.js'})
                self.reject(value)

    def test_missing_duplicate_and_unknown_origins_fail(self):
        for paths in ([],['src/entry.ts','src/entry.ts'],['src/missing.ts'],['../private.ts']):
            with self.subTest(paths=paths):
                value=fixture();value['emission_map']['entries'][0]['source_paths']=paths;self.reject(value)

    def test_declaration_cannot_be_labelled_javascript(self):
        value=fixture();value['outputs'][0]['path']='.cache/output/entry.d.ts'
        value['emission_map']['entries'][0]['output_path']='.cache/output/entry.d.ts';self.reject(value)

    def test_declaration_input_cannot_claim_javascript_origin(self):
        value=fixture();value['inputs'][-1]['path']='src/entry.d.ts'
        value['emission_map']['entries'][0]['source_paths']=['src/entry.d.ts'];self.reject(value)

    def test_nonexecutable_origins_cannot_claim_javascript_after_rehash(self):
        for path in ('src/package.json','src/tsconfig.json','src/notes.txt'):
            with self.subTest(path=path):
                value=fixture();value['inputs'][-1]['path']=path
                value['emission_map']['entries'][0]['source_paths']=[path]
                self.reject(value)

    def test_noncommonjs_failed_noemit_and_skipped_observations_cannot_supply_runtime(self):
        for mode in ('module','failed','noemit','skipped'):
            with self.subTest(mode=mode):
                value=fixture()
                if mode=='module':value['emission_map']['module_kind']='other'
                elif mode=='failed':value.update(verdict='failed',findings=[{'code':'observer-compiler-failed'}])
                elif mode=='noemit':value.update(no_emit=True,outputs=[]);value['emission_map']['entries']=[]
                else:value['emit_skipped']=True
                seal(value,'observation_digest')
                with self.assertRaises(release.ReleaseFailure):self.lookup(value)

    def test_stale_source_wrong_configuration_and_output_root_fail(self):
        for change in ({'source_digest':'sha256:'+'b'*64},{'configuration':'other/tsconfig.json'},
                       {'output_root':'.cache/other'},{'source_path':'node_modules/entry.ts'}):
            with self.subTest(change=change),self.assertRaises(release.ReleaseFailure):self.lookup(fixture(),**change)

    def test_ambiguous_multiple_outputs_and_bundled_origins_fail(self):
        value=fixture();value['outputs'].append({'path':'.cache/output/second.js','digest':HASH,'bytes':1})
        value['emission_map']['entries'].append({'output_path':'.cache/output/second.js','source_paths':['src/entry.ts'],'kind':'javascript'})
        seal(value,'observation_digest')
        with self.assertRaises(release.ReleaseFailure):self.lookup(value)
        value=fixture();value['inputs'].append({'kind':'repository','path':'src/second.ts','digest':HASH,'bytes':1})
        value['emission_map']['entries'][0]['source_paths'].append('src/second.ts');seal(value,'observation_digest')
        with self.assertRaises(release.ReleaseFailure):self.lookup(value)

    def test_declaration_only_output_cannot_replace_runtime(self):
        value=fixture();value['outputs'][0]['path']='.cache/output/actual-name.d.ts'
        value['emission_map']['entries'][0].update(output_path=value['outputs'][0]['path'],kind='declaration')
        seal(value,'observation_digest');contracts.observation(value)
        with self.assertRaises(release.ReleaseFailure):self.lookup(value)

    def test_verify_existing_remainder_is_explicit_and_disjoint(self):
        value=fixture();value.update(output_mode='verify-existing',existing_remainder=[{'path':'.cache/output/node_modules/fixture/index.js','digest':HASH,'bytes':1}])
        seal(value,'observation_digest');contracts.observation(value)
        value['output_mode']='fresh-exclusive';self.reject(value)
        value['output_mode']='verify-existing';value['existing_remainder']=deepcopy(value['outputs']);self.reject(value)

    def test_changed_observation_digest_fails_before_lookup(self):
        value=fixture();value['outputs'][0]['digest']='sha256:'+'b'*64
        with self.assertRaises(release.ReleaseFailure):self.lookup(value)

    def test_actual_output_bytes_and_compiler_input_bytes_are_parent_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);output=root/'.cache/output/actual-name.js';output.parent.mkdir(parents=True)
            output.write_bytes(b'x');value=fixture();value['outputs'][0]['digest']=local_build.digest(b'x');seal(value,'observation_digest')
            local_build.check_observed_files(root,value,value['inputs'])
            output.write_bytes(b'y')
            with self.assertRaisesRegex(local_build.LocalBuildFailure,'local-build-output-changed'):
                local_build.check_observed_files(root,value,value['inputs'])
            output.write_bytes(b'x');fresh=deepcopy(value['inputs'])
            next(row for row in fresh if row['path']=='node_modules/typescript/lib/typescript.js')['digest']='sha256:'+'b'*64
            with self.assertRaisesRegex(local_build.LocalBuildFailure,'local-build-input-binding-invalid'):
                local_build.check_observed_files(root,value,fresh)

    def modern_runtime_pair(self):
        value=build_fixture();build=value['builds'][0];observed=build['observation'];runtime=build['runtime']
        observed['schema']='local-typescript-emission-observation/v1'
        observed.update(output_mode='fresh-exclusive',existing_remainder=[],emission_map={'schema':'local-typescript-emission-map/v1','module_kind':'commonjs','entries':[]})
        for index,row in enumerate(observed['outputs']):
            source='src/origin'+str(index)+'.ts';observed['inputs'].append({'kind':'repository','path':source,'digest':HASH,'bytes':1})
            observed['emission_map']['entries'].append({'output_path':row['path'],'source_paths':[source],'kind':'javascript'})
        seal(observed,'observation_digest');runtime['schema']='local-workspace-runtime-observation/v1'
        runtime['workspace_exports']={'compiler_observation_digest':observed['observation_digest'],
            'generated_files':[deepcopy(row) for row in runtime['artifact_files'] if row['path'].startswith('node_modules/')]}
        return runtime,observed

    def test_modern_runtime_exact_compiler_generated_union_is_accepted(self):
        runtime,observed=self.modern_runtime_pair();contracts.runtime_compiler_binding(runtime,observed)

    def test_modern_runtime_hidden_node_modules_artifact_is_rejected(self):
        runtime,observed=self.modern_runtime_pair()
        runtime['artifact_files'].append({'path':'node_modules/hidden/index.js','digest':HASH,'bytes':1})
        with self.assertRaises(release.ReleaseFailure):contracts.runtime_compiler_binding(runtime,observed)

    def test_modern_runtime_generated_fingerprint_cannot_drift(self):
        for field,value in [('digest','sha256:'+'f'*64),('bytes',2)]:
            with self.subTest(field=field):
                runtime,observed=self.modern_runtime_pair();runtime['workspace_exports']['generated_files'][0][field]=value
                with self.assertRaises(release.ReleaseFailure):contracts.runtime_compiler_binding(runtime,observed)

    def test_modern_runtime_duplicate_or_colliding_generated_paths_are_rejected(self):
        for mode in ('duplicate','collision'):
            with self.subTest(mode=mode):
                runtime,observed=self.modern_runtime_pair();generated=runtime['workspace_exports']['generated_files']
                generated.append(deepcopy(generated[0] if mode=='duplicate' else next(row for row in runtime['artifact_files'] if not row['path'].startswith('node_modules/'))))
                with self.assertRaises(release.ReleaseFailure):contracts.runtime_compiler_binding(runtime,observed)

    def test_modern_runtime_missing_generated_or_duplicate_artifact_is_rejected(self):
        for mode in ('missing','duplicate'):
            with self.subTest(mode=mode):
                runtime,observed=self.modern_runtime_pair()
                if mode=='missing':runtime['artifact_files']=[row for row in runtime['artifact_files'] if row['path']!=runtime['workspace_exports']['generated_files'][0]['path']]
                else:runtime['artifact_files'].append(deepcopy(runtime['artifact_files'][0]))
                with self.assertRaises(release.ReleaseFailure):contracts.runtime_compiler_binding(runtime,observed)

    def test_modern_runtime_cannot_use_another_compiler_observation(self):
        runtime,observed=self.modern_runtime_pair();runtime['workspace_exports']['compiler_observation_digest']='sha256:'+'f'*64
        with self.assertRaises(release.ReleaseFailure):contracts.runtime_compiler_binding(runtime,observed)

    def test_enclosing_build_preserves_new_observation_identity_and_map(self):
        value=build_fixture();observed=value['builds'][0]['observation'];observed['schema']='local-typescript-emission-observation/v1'
        observed.update(output_mode='fresh-exclusive',existing_remainder=[],emission_map={'schema':'local-typescript-emission-map/v1','module_kind':'commonjs','entries':[]})
        for index,row in enumerate(observed['outputs']):
            source='src/origin'+str(index)+'.ts';observed['inputs'].append({'kind':'repository','path':source,'digest':HASH,'bytes':1})
            observed['emission_map']['entries'].append({'output_path':row['path'],'source_paths':[source],'kind':'javascript'})
        with self.assertRaisesRegex(release.ReleaseFailure,'local-build-runtime-export-proof-required'):
            contracts.result(reseal(value))
        value['builds'][0]['runtime']=None;value['verdict']='failed';value['findings']=[{'code':'local-build-runtime-failed'}]
        contracts.result(reseal(value));self.assertIn('emission_map',value['builds'][0]['observation'])
        observed['output_mode']='verify-existing'
        with self.assertRaisesRegex(release.ReleaseFailure,'local-build-fresh-emission-required'):
            contracts.result(reseal(value))

if __name__=='__main__':unittest.main()
