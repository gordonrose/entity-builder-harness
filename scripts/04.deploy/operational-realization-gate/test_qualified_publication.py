"""Focused synthetic same-host publication boundary checks; never call Docker."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.qualified-image-publication
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject stale or substituted image handoffs and unsafe publication evidence.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.qualified-image-publication
#     path: scripts/04.deploy/operational-realization-gate/qualified_publication.py
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import qualified_publication as q
from test_local_container_contracts import fixture
from source_inventory import canonical,digest
import result_consumption


class QualifiedPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.scratch=Path(self.temporary.name);self.root=self.scratch/'source';self.root.mkdir()
        self.output=self.scratch/'handoff'
        self.result,self.profiles=fixture()
        self.configuration='sha256:'+'9'*64
        self.manifest=canonical({'schemaVersion':2,'mediaType':'application/vnd.oci.image.manifest.v1+json',
            'config':{'digest':self.configuration,'size':42},'layers':[{'digest':'sha256:'+'d'*64,'size':43}]})
        self.identity={'daemon_image_id':self.result['image']['image_id'],
            'manifest_digest':self.result['image']['image_id'],'configuration_digest':self.configuration}
        self.engine=Mock()
        image=deepcopy(self.result['image']);image['environment']={row['name']:row['value'] for row in image['environment']}
        self.engine.inspect_image.return_value=image
        self.engine.inventory.return_value=deepcopy(self.result['payload']['files'])
        self.engine.build_identity.return_value=self.identity
        self.current=patch.object(q,'current_result',side_effect=lambda root,value:value).start();self.addCleanup(patch.stopall)
        patch.object(q.container,'checked_scratch',side_effect=lambda root,scratch:Path(scratch)).start()
        patch.object(q.container.container_engine,'Engine',return_value=self.engine).start()

    def create(self): return q.create(self.root,self.scratch,self.output,self.result,self.engine)
    def verify(self): return q.verify(self.root,self.scratch,self.output)
    def rewrite(self,value): (self.output/'handoff.json').write_bytes(canonical(q.seal(value))+b'\n')

    def test_same_host_handoff_round_trip_preserves_full_result_and_authority(self):
        value=self.create();self.assertEqual(self.verify(),value)
        self.assertEqual(json.loads((self.output/'container-result.json').read_bytes()),self.result)
        self.assertFalse(value['authorized']);self.assertTrue(value['same_host_only'])
        self.assertEqual(self.output.stat().st_mode&0o777,0o700)
        for file in self.output.iterdir():self.assertEqual(file.stat().st_mode&0o777,0o600)

    def test_existing_destination_never_overwritten(self):
        self.create();before=(self.output/'handoff.json').read_bytes()
        with self.assertRaises(q.release.ReleaseFailure):self.create()
        self.assertEqual((self.output/'handoff.json').read_bytes(),before)

    def test_linked_directory_and_linked_receipt_refused(self):
        link=self.scratch/'link';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(q.release.ReleaseFailure):q.destination(self.root,self.scratch,link,existing=True)
        self.create();(self.output/'handoff.json').rename(self.output/'retained.json')
        (self.output/'handoff.json').symlink_to(self.output/'retained.json')
        with self.assertRaises(q.release.ReleaseFailure):self.verify()

    def test_rehashed_authority_unknown_fields_and_impossible_identity_refused(self):
        value=self.create()
        for mutation in ({'authorized':True},{'extra':'PRIVATE'}, {'artifact':{**value['artifact'],'daemon_image_id':'sha256:'+'f'*64}}):
            with self.subTest(mutation=mutation),self.assertRaises(q.release.ReleaseFailure):q.validate(q.seal({**value,**mutation}))

    def test_changed_handoff_source_and_result_bindings_refused(self):
        original=self.create()
        for name in ('container_result_digest','source_digest','container_runner_digest','recipe_digest','lock_digest','handoff_runner_digest','schema_digest'):
            with self.subTest(name=name):
                value=deepcopy(original);value[name]='sha256:'+'f'*64;self.rewrite(value)
                with self.assertRaises(q.release.ReleaseFailure):self.verify()

    def test_alternate_image_is_not_accepted(self):
        value=self.create();value['artifact']['daemon_image_id']=value['artifact']['configuration_digest'];self.rewrite(value)
        with self.assertRaises(q.release.ReleaseFailure):self.verify()

    def test_current_image_configuration_or_payload_drift_refused(self):
        self.create()
        for method,change in [('inspect_image',{'unexpected':'PRIVATE'}),('inventory',[])]:
            with self.subTest(method=method):
                mock=getattr(self.engine,method);original=mock.return_value;mock.return_value=change
                with self.assertRaises((q.release.ReleaseFailure,KeyError)):self.verify()
                mock.return_value=original

    def test_stale_current_source_cannot_reuse_local_pass(self):
        self.create();self.current.side_effect=q.release.ReleaseFailure('qualified-publication-source-changed')
        with self.assertRaises(q.release.ReleaseFailure):self.verify()

    def test_full_container_contract_remains_required(self):
        q.contracts.validate_result(self.result,self.profiles,self.result['payload']['production_dependencies'])
        self.result['runtime']['cleanup_verified']=False
        self.result['result_digest']=q.contracts.digest({k:v for k,v in self.result.items() if k!='result_digest'})
        with self.assertRaises(q.release.ReleaseFailure):q.contracts.validate_result(self.result,self.profiles,self.result['payload']['production_dependencies'])

    def published_fixture(self):
        value=self.create();manifest_digest=digest(self.manifest)
        value['artifact'].update(daemon_image_id=manifest_digest,manifest_digest=manifest_digest)
        value=q.seal(value)
        response={'images':[{'registryId':'337159794548','repositoryName':'platform-shell',
            'imageId':{'imageDigest':manifest_digest},'imageManifest':self.manifest.decode()}],'failures':[]}
        return value,response

    def test_exact_registry_manifest_and_config_are_matched_without_reserialization(self):
        value,response=self.published_fixture();verified=q.verify_published(value,canonical(response))
        self.assertEqual(verified['phase'],'registry-matched');self.assertEqual(verified['published_digest'],digest(self.manifest))
        self.assertFalse(verified['authorized'])

    def test_remote_wrong_registry_repository_digest_or_manifest_refused(self):
        value,response=self.published_fixture()
        for key,part in [('registryId','999999999999'),('repositoryName','other'),('imageManifest',self.manifest.decode()+'\n'),('imageId',{'imageDigest':'sha256:'+'f'*64})]:
            with self.subTest(key=key):
                changed=deepcopy(response);changed['images'][0][key]=part
                with self.assertRaises(q.release.ReleaseFailure):q.verify_published(value,canonical(changed))

    def test_registry_response_missing_ambiguous_or_failed_refused(self):
        value,response=self.published_fixture()
        for changed in ({'images':[]},{'images':response['images']*2},{**response,'failures':[{'failureCode':'ImageNotFound'}]}):
            with self.assertRaises(q.release.ReleaseFailure):q.verify_published(value,canonical(changed))

    def test_registry_config_or_index_substitution_refused(self):
        value,response=self.published_fixture()
        value['artifact']['configuration_digest']='sha256:'+'e'*64;value=q.seal(value)
        with self.assertRaises(q.release.ReleaseFailure):q.verify_published(value,canonical(response))

    def test_all_authority_and_source_consumption_refused(self):
        value=self.create()
        for purpose in ('source-analysis','release-eligibility','operation-authorization'):
            self.assertEqual(result_consumption.consume_result(value,purpose,value)['verdict'],'rejected')

    def test_public_duplicate_unsafe_arguments_fail_safely(self):
        for args in (['--image','PRIVATE'],['--source-root','PRIVATE','--source-root','PRIVATE']):
            out=io.StringIO();err=io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):status=q.main(args)
            self.assertEqual(status,1);self.assertNotIn('PRIVATE',out.getvalue()+err.getvalue())
            self.assertFalse(json.loads(out.getvalue())['authorized'])

    def test_public_final_output_rejects_unknown_fields_and_authority(self):
        value=self.create()
        args=['--source-root',str(self.root),'--scratch-root',str(self.scratch),'--publication-directory',str(self.output)]
        for mutation in ({'extra':'PRIVATE'},{'authorized':True},{'handoff_digest':'sha256:'+'0'*64}):
            out=io.StringIO()
            with patch.object(q,'verify',return_value={**value,**mutation}),contextlib.redirect_stdout(out):status=q.main(args)
            self.assertEqual(status,1);self.assertNotIn('PRIVATE',out.getvalue())



class QualifiedEngineIdentityTests(unittest.TestCase):
    def setUp(self):
        import test_container_engine as fixtures
        self.fixture=fixtures
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.fake=fixtures.FakeDocker()
        self.engine=q.container.container_engine.Engine(self.root,runner=self.fake)
        self.context=self.root/'context';self.context.mkdir();self.recipe=self.context/'Dockerfile';self.recipe.write_text('fixture')

    def build(self):return self.engine.build(self.context,self.recipe,self.fixture.BASE,self.fixture.COMMIT)

    def test_actual_build_metadata_survives_and_cannot_be_mutated_by_caller(self):
        image=self.build();value=self.engine.build_identity(image)
        self.assertEqual(value,{'daemon_image_id':image,'manifest_digest':self.fixture.IMAGE,'configuration_digest':self.fixture.BASE_ID})
        value['configuration_digest']='changed'
        self.assertEqual(self.engine.build_identity(image)['configuration_digest'],self.fixture.BASE_ID)
        command=next(row for row in self.fake.calls if row[3]=='build')
        self.assertIn('org.opencontainers.image.revision='+self.fixture.COMMIT,command)
        self.assertNotIn('--tag',command)

    def test_classic_config_identity_preserves_distinct_manifest(self):
        self.fake.image['Id']=self.fixture.BASE_ID
        image=self.build();self.assertEqual(image,self.fixture.BASE_ID)
        self.assertEqual(self.engine.build_identity(image)['manifest_digest'],self.fixture.IMAGE)

    def test_unrelated_image_identity_cannot_supply_handoff(self):
        self.build()
        with self.assertRaises(q.container.container_engine.EngineFailure):self.engine.build_identity('sha256:'+'8'*64)

    def test_bad_platform_does_not_trigger_config_identity_fallback(self):
        self.fake.image['Os']='other'
        with self.assertRaises(q.container.container_engine.EngineFailure):self.build()
        self.assertFalse(any(row[3:]==['image','inspect',self.fixture.BASE_ID] for row in self.fake.calls))


class PublicationOptionTests(unittest.TestCase):
    def test_optional_handoff_directory_reaches_only_fresh_qualification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);output=root/'handoff';stream=io.StringIO()
            with patch.object(q.container,'checked_scratch',return_value=root),patch.object(q.container,'run',return_value={}) as run,contextlib.redirect_stdout(stream):
                status=q.container.main(['--source-root',str(root),'--scratch-root',str(root),'--package-cache',str(root/'cache'),'--publication-directory',str(output)])
            self.assertEqual(status,0);run.assert_called_once_with(root,str(root/'cache'),root,str(output))

    def test_acquisition_cannot_masquerade_as_qualified_handoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            stream=io.StringIO()
            with patch.object(q.container,'run') as run,contextlib.redirect_stdout(stream):
                status=q.container.main(['--source-root',temporary,'--scratch-root',temporary,'--acquire-base','--publication-directory',temporary+'/handoff'])
            self.assertEqual(status,1);run.assert_not_called()

class CurrentPublicationSourceTests(unittest.TestCase):
    def setUp(self):
        self.result,self.profiles=fixture();self.root=Path('/synthetic-review-source')
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.patch=lambda obj,key,**kwargs:self.stack.enter_context(patch.object(obj,key,**kwargs))
        self.patch(q.container.container_profiles,'discover',return_value=self.profiles)
        self.patch(q.container.container_payload,'production_packages',return_value=self.result['payload']['production_dependencies'])
        self.patch(q.container.locked_toolchain,'inspect_project',return_value={})
        self.patch(q.container,'read',return_value=b'{}')
        self.head=self.patch(q.container,'repository_head',return_value=self.result['repository_head'])
        self.lock=self.patch(q.container,'load_lock',return_value=self.result['lock'])
        self.runner=self.patch(q.container,'implementation_digest',return_value=self.result['runner_digest'])
        self.patch(q.container,'source_manifest',return_value=[])
        self.source=self.patch(q,'digest',return_value=self.result['build']['source_digest'])
        self.builder=self.patch(q.container.local_build,'implementation_digest',return_value=self.result['build']['runner_digest'])

    def test_complete_contract_and_current_identity_agree(self):
        self.assertEqual(q.current_result(self.root,self.result),self.result)

    def test_changed_current_commit_source_runner_or_builder_refuse(self):
        for mock in (self.head,self.runner,self.source,self.builder):
            with self.subTest(mock=mock):
                prior=mock.return_value;mock.return_value='sha256:'+'f'*64
                with self.assertRaises(q.release.ReleaseFailure):q.current_result(self.root,self.result)
                mock.return_value=prior

    def test_changed_recipe_or_runtime_lock_refuse(self):
        self.lock.return_value={**self.result['lock'],'runtime_config_digest':'sha256:'+'f'*64}
        with self.assertRaises(q.release.ReleaseFailure):q.current_result(self.root,self.result)

    def test_skipped_cleanup_cannot_be_rehashed_into_a_handoff(self):
        self.result['runtime']['cleanup_verified']=False
        self.result['result_digest']=q.contracts.digest({key:value for key,value in self.result.items() if key!='result_digest'})
        with self.assertRaises(q.release.ReleaseFailure):q.current_result(self.root,self.result)


if __name__=='__main__':unittest.main()
