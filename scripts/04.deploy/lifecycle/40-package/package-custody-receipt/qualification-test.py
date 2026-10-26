#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.package-qualification-binding
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise publication qualification omission, substitution and immutable artifact binding through real CLIs.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.package-custody-receipt
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/smoke-test.sh
"""Exercise artifact/configuration binding and actual publication guard CLIs."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[5]
HELPER=ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py'

class QualificationTests(unittest.TestCase):
    def test_exact_artifact_config_reuse_and_invalidation_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'docker'
            binary.write_text('#!/bin/sh\nprintf "%s\\n" "$TEST_IMAGE_ID"\n');binary.chmod(0o755)
            config=root/'config.yml';config.write_text('enabled: true\n');receipt=root/'receipt.json'
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'TEST_IMAGE_ID':'sha256:'+'a'*64}
            def run(action,expected=0,**extra):
                result=subprocess.run(['python3','-B',str(HELPER),action,'--image','fixture:tag','--receipt',str(receipt),'--input',str(config)],env={**env,**extra},capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stdout+result.stderr);return result
            run('record');run('verify');historical=receipt.read_bytes()
            run('verify',1,TEST_IMAGE_ID='sha256:'+'b'*64)
            config.write_text('enabled: false\n');run('verify',1)
            config.write_text('enabled: true\n');run('verify')
            run('record',1)
            self.assertEqual(receipt.read_bytes(),historical)

    def test_publication_guards_reject_control_and_identity_substitution(self):
        for kind, filename, job_name, qualify_name in [
            ('core-server','publish-kanbien-core-platform-core-server.yml','publish-core-server','Qualify the declared core-server candidate'),
            ('core-server-persistence','publish-kanbien-core-platform-core-server-persistence.yml','qualify-and-publish','Qualify declarations and actual candidate payload'),
            ('core-server-persistence-observability-collector','publish-kanbien-core-platform-observability-collector.yml','build-and-qualify','Qualify exact collector startup with non-secret configuration'),
        ]:
            with self.subTest(route=kind), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);(root/'.github/workflows').mkdir(parents=True)
                # Validators are the actual CLI; only workflow input is disposable.
                guard=ROOT/'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform'/(kind+'-package-custody')/'verify-workflow.py'
                original=(ROOT/'.github/workflows'/filename).read_text();workflow=yaml.safe_load(original)
                local=root/'.github/workflows'/filename
                shutil.copytree(ROOT/'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image',root/'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image')
                def run(text, expected):
                    local.write_text(text)
                    args=['python3','-B',str(guard),'--json']
                    if kind.endswith('collector'):args+=['--workflow',str(local)]
                    result=subprocess.run(args,cwd=root,capture_output=True,text=True)
                    self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
                    return json.loads(result.stdout)
                if kind.endswith('collector'):
                    relative='scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh'
                    nested=root/relative;nested.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,nested)
                run(original,0)
                if kind.endswith('collector'):
                    nested_original=nested.read_text()
                    proof=next(line for line in nested_original.splitlines() if line.startswith('exec python3'))
                    for mutated in [nested_original.replace(proof,proof+' || true'),nested_original.replace(proof,'if false; then '+proof+'; fi'),nested_original.replace(proof,''),nested_original.replace('trap - EXIT\n\n'+proof,proof+'\ntrap - EXIT'),nested_original.replace('set -euo pipefail','set +e')]:
                        nested.write_text(mutated);run(original,1)
                    nested.write_text(nested_original)

                    for replacement in ['--output observability-collector.trivy.json || true', '--output observability-collector.trivy.json; true', '--output other.json']:
                        report=run(original.replace('--output observability-collector.trivy.json',replacement),1)
                        self.assertIn('collector-qualification-route-invalid',{item['code'] for item in report['findings']})
                    for replacement in ['id: unobserved_scan','id: vulnerability_scan\n        if: false',"id: vulnerability_scan\n        env: {TRIVY_SKIP_FILES: '*'}"]:
                        run(original.replace('id: vulnerability_scan',replacement),1)
                    for stage in ['Verify collector archive provenance','Export exact qualified collector archive','Verify archive is the scanned qualified payload','Install pinned portable scanner','Retrieve exact qualified collector archive','Retain vulnerability scan artifact']:
                        for mutation in ['omitted','conditional','substituted']:
                            broken=copy.deepcopy(workflow)
                            owner=next(job for job in broken['jobs'].values() if any(item.get('name')==stage for item in job.get('steps',[])))
                            item=next(item for item in owner['steps'] if item.get('name')==stage)
                            if mutation=='omitted':owner['steps'].remove(item)
                            elif mutation=='conditional':item['if']='false'
                            elif 'run' in item:item['run']+=' || true'
                            else:item['with']['name']='unrelated-artifact'
                            run(yaml.safe_dump(broken,sort_keys=False),1)
                # Each later proof is an executable prerequisite, not a name
                # whose presence can survive a conditional/suppressed body.
                later_job='complete-custody' if kind.endswith('collector') else job_name
                for stage in ['Generate SBOM','Attest collector provenance' if kind.endswith('collector') else 'Attest image provenance','Attest collector SBOM' if kind.endswith('collector') else 'Attest image SBOM','Write and validate safe collector custody receipt' if kind.endswith('collector') else 'Write and validate safe package-custody receipt','Upload safe collector custody evidence' if kind.endswith('collector') else 'Upload safe package-custody evidence']:
                    for change in ['omitted','conditional','suppressed','substituted','reordered','environment-substituted']:
                        broken=copy.deepcopy(workflow);later=broken['jobs'][later_job]['steps'];item=next(x for x in later if x.get('name')==stage)
                        if change=='omitted':later.remove(item)
                        elif change=='conditional':item['if']='false'
                        elif change=='suppressed':item['continue-on-error']=True
                        elif change=='environment-substituted':item['env']={'BASH_ENV':'injected-shell-environment'}
                        elif change=='substituted':
                            if 'uses' in item:item['uses']='actions/checkout@v4'
                            else:item['run']+='\ntrue'
                        else:later.remove(item);later.insert(0,item)
                        run(yaml.safe_dump(broken,sort_keys=False),1)
                if not kind.endswith('collector'):
                    for change in ['omitted','conditional','suppressed','reordered','shell-suppressed','digest-substitution']:
                        broken=copy.deepcopy(workflow);later=broken['jobs'][job_name]['steps'];item=next(x for x in later if x.get('name')=='Require clean ECR scan')
                        if change=='omitted':later.remove(item)
                        elif change=='conditional':item['if']='false'
                        elif change=='suppressed':item['continue-on-error']=True
                        elif change=='reordered':later.remove(item);later.insert(0,item)
                        elif change=='shell-suppressed':item['run']+=' || true'
                        else:item['run']=item['run'].replace('steps.image.outputs.digest','steps.unrelated.outputs.digest')
                        run(yaml.safe_dump(broken,sort_keys=False),1)
                for mutation in ['omitted','conditional','failure-suppressed','reordered','substituted','publication-tag-substitution','publication-failstop-disabled','publication-identity-suppressed']:
                    broken=copy.deepcopy(workflow);steps=broken['jobs'][job_name]['steps'];qualify=next(x for x in steps if x.get('name')==qualify_name)
                    if mutation=='omitted':steps.remove(qualify)
                    elif mutation=='conditional':qualify['if']='false'
                    elif mutation=='failure-suppressed':qualify['continue-on-error']=True
                    elif mutation=='reordered':steps.remove(qualify);steps.append(qualify)
                    elif mutation=='substituted':qualify['run']=qualify['run'].replace('bash ','echo ',1)
                    else:
                        pubjob=broken['jobs']['complete-custody'] if kind.endswith('collector') else broken['jobs'][job_name]
                        publish=next(x for x in pubjob['steps'] if x.get('name','').startswith(('Publish immutable','Publish exact')))
                        if mutation=='publication-failstop-disabled':publish['run']=publish['run'].replace('docker pull ', 'set +e\ndocker pull ')
                        elif mutation=='publication-identity-suppressed':publish['run']=publish['run'].replace('= "$qualified_image"','= "$qualified_image" || true')
                        else:publish['run']=publish['run'].replace('docker tag "$qualified_image"','docker tag unrelated:tag')
                    report=run(yaml.safe_dump(broken,sort_keys=False),1)
                    self.assertTrue(any('qualification-route-invalid' in x['code'] for x in report['findings']),report)

    def test_shell_workflow_and_durable_custody_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'bin';binary.mkdir()
            git=binary/'git';git.write_text('#!/bin/sh\nprintf "%s\\n" "$FIXTURE_ROOT"\n');git.chmod(0o755)
            paths=['.github/workflows/deploy-platform-shell-staging.yml','infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml','infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml','scripts/04.deploy/build-platform-shell-image/script.sh','scripts/04.deploy/verify-platform-shell-deployment-workflow/qualify-image.sh','scripts/04.deploy/lifecycle/40-package/package-custody-receipt/workflow_guard.py']
            for relative in paths:
                destination=root/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,destination)
            workflow_path=root/paths[0];original=workflow_path.read_text();workflow=yaml.safe_load(original)
            def run(value,expected):
                workflow_path.write_text(value)
                result=subprocess.run(['bash',str(ROOT/'scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh')],cwd=root,env={**os.environ,'PATH':str(binary)+os.pathsep+os.environ['PATH'],'FIXTURE_ROOT':str(root)},capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
            run(original,0)
            qualifier=root/'scripts/04.deploy/verify-platform-shell-deployment-workflow/qualify-image.sh';qualifier_original=qualifier.read_text()
            smoke=next(line for line in qualifier_original.splitlines() if line.startswith('bash scripts/'))
            for mutated in [qualifier_original.replace(smoke,smoke+' || true'),qualifier_original.replace(smoke,'if false; then '+smoke+'; fi'),qualifier_original.replace(smoke,''),qualifier_original.replace(smoke+'\n','')+'\n'+smoke,qualifier_original.replace('set -euo pipefail','set +e')]:
                qualifier.write_text(mutated);run(original,1)
            qualifier.write_text(qualifier_original)
            for mutation in ['omitted','conditional','suppressed','reordered','substituted','custody-omitted','custody-outcome-forged','upload-overwrite','scan-omitted','scan-suppressed','scan-substituted','sbom-conditional','attestation-conditional','published-identity-suppressed']:
                broken=copy.deepcopy(workflow);steps=broken['jobs']['build-image']['steps'];qualify=next(item for item in steps if item.get('name')=='Qualify exact platform shell image')
                if mutation=='omitted':steps.remove(qualify)
                elif mutation=='conditional':qualify['if']='false'
                elif mutation=='suppressed':qualify['continue-on-error']=True
                elif mutation=='reordered':steps.remove(qualify);steps.append(qualify)
                elif mutation=='substituted':qualify['run']='echo bypass'
                elif mutation=='custody-omitted':steps.remove(next(item for item in steps if item.get('name')=='Capture durable package custody receipt'))
                elif mutation=='custody-outcome-forged':next(item for item in steps if item.get('name')=='Capture durable package custody receipt')['env']['QUALIFICATION_OUTCOME']='success'
                elif mutation=='upload-overwrite':next(item for item in steps if item.get('name')=='Retain immutable package custody evidence')['with']['overwrite']=True
                elif mutation=='scan-omitted':steps.remove(next(item for item in steps if item.get('name')=='Read ECR scan finding counts'))
                elif mutation=='scan-suppressed':next(item for item in steps if item.get('name')=='Read ECR scan finding counts')['run']+=' || true'
                elif mutation=='scan-substituted':next(item for item in steps if item.get('name')=='Read ECR scan finding counts')['run']='echo passed'
                elif mutation=='sbom-conditional':next(item for item in steps if item.get('name')=='Generate image SBOM')['if']='false'
                elif mutation=='attestation-conditional':next(item for item in steps if item.get('name')=='Attest image provenance')['if']='false'
                else:next(item for item in steps if item.get('name')=='Verify published target-platform image')['run']+='\nset +e'
                run(yaml.safe_dump(broken,sort_keys=False),1)
            emitter=ROOT/'scripts/04.deploy/verify-platform-shell-deployment-workflow/emit-custody.py'
            sbom=root/'sbom.json';sbom.write_text('{"spdxVersion":"SPDX-2.3"}')
            receipt=root/'custody.json';keys=['SOURCE_CHECKS_OUTCOME','QUALIFICATION_OUTCOME','CREDENTIALS_OUTCOME','REGISTRY_LOGIN_OUTCOME','PUBLISHED_IMAGE_OUTCOME','SCAN_OUTCOME','SBOM_OUTCOME','PROVENANCE_OUTCOME','SBOM_ATTESTATION_OUTCOME']
            environment={**os.environ,**{key:'success' for key in keys},'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'456','PUBLISHED_DIGEST':'sha256:'+'b'*64,'SBOM_PATH':str(sbom)}
            for key in keys:
                failed=subprocess.run(['python3','-B',str(emitter),'--output',str(receipt)],env={**environment,key:'skipped'},capture_output=True,text=True)
                self.assertEqual(failed.returncode,1,failed.stdout+failed.stderr);self.assertFalse(receipt.exists())
            accepted=subprocess.run(['python3','-B',str(emitter),'--output',str(receipt)],env=environment,capture_output=True,text=True);self.assertEqual(accepted.returncode,0,accepted.stdout+accepted.stderr)
            checked=subprocess.run(['python3','-B',str(ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py'),'--receipt',str(receipt),'--expected-target','kanbien-staging','--expected-candidate','platform-shell','--expected-package-contract','kanbien-staging-platform-shell','--expected-program','platform-shell','--json'],capture_output=True,text=True)
            self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr);proof=json.loads(receipt.read_text());self.assertEqual(proof['receipt_reference'],'github-actions-run:456');self.assertEqual(proof['source_revision'],'a'*40)
            original_receipt=receipt.read_bytes();duplicate=subprocess.run(['python3','-B',str(emitter),'--output',str(receipt)],env=environment,capture_output=True,text=True);self.assertEqual(duplicate.returncode,1);self.assertEqual(receipt.read_bytes(),original_receipt)

    def test_common_capture_requires_real_outcomes_and_immutable_valid_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sbom=root/'sbom.json';sbom.write_text('{"spdxVersion":"SPDX-2.3"}');receipt=root/'receipt.json'
            keys=['QUALIFICATION_OUTCOME','ACCESS_OUTCOME','PUBLICATION_OUTCOME','SCAN_OUTCOME','SBOM_OUTCOME','PROVENANCE_OUTCOME','SBOM_ATTESTATION_OUTCOME']
            environment={**os.environ,**{key:'success' for key in keys},'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'123','IMAGE_DIGEST':'sha256:'+'b'*64}
            argv=['python3','-B',str(ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/capture.py'),'--target','catalog-target','--environment-class','private-fixture','--provider-region-alias','provider-local-fixture','--candidate','catalog-candidate','--package-contract','catalog-image','--program','catalog-worker','--scan-check','vulnerability_scan','--sbom',str(sbom),'--output',str(receipt)]
            for key in keys:
                result=subprocess.run(argv,env={**environment,key:'skipped'},capture_output=True,text=True);self.assertEqual(result.returncode,1,result.stdout);self.assertFalse(receipt.exists())
            result=subprocess.run(argv,env=environment,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr);original=receipt.read_bytes()
            duplicate=subprocess.run(argv,env=environment,capture_output=True,text=True);self.assertEqual(duplicate.returncode,1);self.assertEqual(receipt.read_bytes(),original)

    def test_shell_actual_qualification_resume_and_failure_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'bin';binary.mkdir();docker=binary/'docker'
            docker.write_text('#!/bin/sh\nif [ "$1" = image ]; then printf "sha256:'+'a'*64+'\\n"; fi\n');docker.chmod(0o755)
            smoke=root/'scripts/04.deploy/smoke-test-platform-shell-image/script.sh';smoke.parent.mkdir(parents=True);smoke.write_text('#!/bin/sh\ntouch "$SMOKE_MARKER"\nexit "$SMOKE_RESULT"\n')
            capture=root/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py';capture.parent.mkdir(parents=True);shutil.copy2(HELPER,capture)
            for relative in ['infra/04.deploy/03.product/image/Dockerfile','infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml','scripts/04.deploy/smoke-test-platform-shell-image/relational-package-test.py','infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml']:
                destination=root/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text('synthetic input')
            adapter='scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py'
            (root/adapter).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/adapter,root/adapter)
            (root/'infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml').write_text('Resources: {Worker: {Type: "AWS::ECS::TaskDefinition", Properties: {ContainerDefinitions: [{Name: worker, Command: [node, worker.js]}]}}}')
            for existing in ['true','false']:
                for status in [23,0]:
                    output=root/(existing+'-'+str(status));output.mkdir();marker=output/'smoke-called';github=output/'github-output'
                    environment={**os.environ,'PATH':str(binary)+os.pathsep+os.environ['PATH'],'EXISTING_IMAGE':existing,'EXISTING_DIGEST':'sha256:'+'b'*64,'ECR_URI':'fixture.example/repository','CANDIDATE_IMAGE':'fixture:tag','RUNNER_TEMP':str(output),'GITHUB_OUTPUT':str(github),'SMOKE_MARKER':str(marker),'SMOKE_RESULT':str(status)}
                    result=subprocess.run(['/bin/bash',str(ROOT/'scripts/04.deploy/verify-platform-shell-deployment-workflow/qualify-image.sh')],cwd=root,env=environment,capture_output=True,text=True)
                    self.assertEqual(result.returncode,status,result.stdout+result.stderr);self.assertTrue(marker.exists())
                    if status:self.assertFalse((output/'qualified-image.json').exists());self.assertFalse(github.exists())
                    else:self.assertEqual(json.loads((output/'qualified-image.json').read_text())['image_id'],'sha256:'+'a'*64);self.assertIn('image_id=sha256:',github.read_text())

    def test_configuration_projection_reuses_permissions_and_invalidates_runtime_cli(self):
        adapter='scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'docker';binary.write_text('#!/bin/sh\nprintf "sha256:'+'a'*64+'\\n"\n');binary.chmod(0o755)
            ordinary=root/'input';ordinary.write_text('package proof');receipt=root/'receipt.json';config=root/'template.yml'
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH']}
            source=(ROOT/'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml').read_text()
            def run(action,expected=0,selector='core-server-persistence'):
                result=subprocess.run(['python3','-B',str(HELPER),action,'--image','fixture:tag','--receipt',str(receipt),'--input',str(ordinary),'--configuration-input',adapter,str(config),selector],cwd=ROOT,env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
            config.write_text(source);run('record');run('verify');historical=receipt.read_bytes()
            self.assertIn('rds-db:connect',source)
            config.write_text(source.replace('rds-db:connect','rds-db:changed-permission'));run('verify')
            self.assertIn('Value: kanbienpersistence',source)
            config.write_text(source.replace('Value: kanbienpersistence','Value: different-database'));run('verify',1)
            config.write_text(source);run('verify');self.assertEqual(receipt.read_bytes(),historical)
            missing=json.loads(historical);missing.pop('configuration_inputs');receipt.write_text(json.dumps(missing));run('verify',1)
            receipt.unlink()
            fixture={'Mappings':{'Settings':{'Local':{'Endpoint':'http://first.invalid'}},'Unrelated':{'Local':{'Value':'initial'}}},'Resources':{'Worker':{'Type':'AWS::ECS::TaskDefinition','Properties':{'ContainerDefinitions':[{'Name':'worker','Command':['node','catalog.js'],'Environment':[{'Name':'CATALOG_ENDPOINT','Value':{'Fn::FindInMap':['Settings','Local','Endpoint']}}]}]}}}}
            original=copy.deepcopy(fixture)
            config.write_text(yaml.safe_dump(fixture));run('record',selector='worker');run('verify',selector='worker')
            fixture['Mappings']['Unrelated']['Local']['Value']='changed';config.write_text(yaml.safe_dump(fixture));run('verify',selector='worker')
            fixture['Mappings']['Settings']['Local']['Endpoint']='http://changed.invalid';config.write_text(yaml.safe_dump(fixture));run('verify',1,selector='worker')
            fixture=copy.deepcopy(original);fixture['Resources']['Worker']['Properties']['ContainerDefinitions'][0]['Command']=['node','unrelated.js'];config.write_text(yaml.safe_dump(fixture));run('verify',1,selector='worker')
            fixture=copy.deepcopy(original);fixture['Resources']['Worker']['Properties']['ContainerDefinitions'][0]['Environment'][0]['Value']={'Fn::Unsupported':['hidden-input']};config.write_text(yaml.safe_dump(fixture));run('verify',1,selector='worker')
            config.write_text(yaml.safe_dump(original));run('verify',selector='worker')

    def test_missing_engine_is_unavailable_not_passed_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'docker';binary.write_text('#!/bin/sh\nexit 1\n');binary.chmod(0o755)
            for owner in ['lifecycle/40-package/build-core-server-image','lifecycle/40-package/smoke-test-core-server-image','smoke-test-platform-shell-image']:
                result=subprocess.run(['bash',str(ROOT/'scripts/04.deploy'/owner/'script.sh'),'--allow-skip-without-engine'],cwd=ROOT,env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH']},capture_output=True,text=True,timeout=180)
                self.assertEqual(result.returncode,77,result.stdout+result.stderr)
                self.assertIn('SKIP:',result.stdout)
                self.assertNotIn('image smoke test passed',result.stdout.lower())

if __name__=='__main__':unittest.main(verbosity=2)
