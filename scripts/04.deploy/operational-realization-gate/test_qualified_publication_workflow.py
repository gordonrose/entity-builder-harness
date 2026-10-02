"""The existing publisher must publish one freshly qualified image and retain its gates."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.qualified-image-workflow
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Preserve official main-only image-publication checks while adopting exact qualified images.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.verify-platform-shell-deployment-workflow
#     path: scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh
from pathlib import Path
import hashlib
import io
import json
import os
import tarfile
import subprocess
import sys
import tempfile
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[3]
WORKFLOW='.github/workflows/deploy-platform-shell-staging.yml'
PROFILE='infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml'
VALIDATOR='scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh'


class QualifiedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        for relative in (WORKFLOW,PROFILE,'scripts/04.deploy/build-platform-shell-image/script.sh','infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml'):
            target=self.root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/relative).read_bytes())
        profile=self.root/PROFILE;profile.write_text(profile.read_text().replace('build_image_policy: pin-by-digest-for-official-build','build_image_policy: locked-toolchain-verified-payload'))
        source=(ROOT/VALIDATOR).read_text();self.validator=source.split("python3 - <<'PY'\n",1)[1].rsplit('\nPY',1)[0]
        self.source=(self.root/WORKFLOW).read_text()

    def check(self,source=None):
        if source is not None:(self.root/WORKFLOW).write_text(source)
        return subprocess.run([sys.executable,'-B','-c',self.validator],cwd=self.root,capture_output=True,timeout=20)

    def test_adopted_workflow_passes_all_existing_and_new_static_checks(self):
        result=self.check();self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_legacy_second_build_is_not_a_publication_route(self):
        changed=self.source.replace('--publication-directory "$RUNNER_TEMP/qualified-image/handoff"','--tag "unsafe-tag"')
        self.assertNotEqual(self.check(changed).returncode,0)

    def test_registry_digest_verification_is_required(self):
        changed=self.source.replace('--published-image "$RUNNER_TEMP/qualified-image/published-image.json"','--other-document "$RUNNER_TEMP/qualified-image/published-image.json"')
        self.assertNotEqual(self.check(changed).returncode,0)

    def test_exact_image_push_and_manifest_binding_are_required(self):
        changed=self.source.replace('steps.qualified-image.outputs.image_id','steps.unqualified.outputs.image_id')
        self.assertNotEqual(self.check(changed).returncode,0)

    def test_failed_qualification_emits_only_the_normalized_safe_result(self):
        changed=self.source.replace('cat "$RUNNER_TEMP/qualified-image/result.json" >&2','true')
        self.assertNotEqual(self.check(changed).returncode,0)

    def test_qualification_sandbox_dependency_and_policy_are_required(self):
        for before, after in (
            ('sudo apt-get install --yes --no-install-recommends bubblewrap', 'true'),
            ('test -x /usr/bin/bwrap', 'sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0'),
        ):
            with self.subTest(before=before):
                self.assertNotEqual(self.check(self.source.replace(before, after)).returncode, 0)

    def test_sandbox_profile_cannot_be_broadened_or_replaced(self):
        for before, after in (
            ('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest'),
            ('4e7d728322f899a7a06e71bedd4f4bd1f20c21f0b3361120f34cf5c0feec849e', '0' * 64),
            ('11d39094f044f0cda0febb3ad517b830301da6b2ce929664af09ee9e4dd264f9', '0' * 64),
            ('apparmor_parser --add --skip-cache', 'apparmor_parser --replace --skip-cache'),
            ('dpkg-deb --extract', 'sudo dpkg --install'),
            ('test ! -e "$local_policy"', 'true'),
            ('test ! -L "$local_policy"', 'true'),
        ):
            with self.subTest(before=before):
                self.assertNotEqual(self.check(self.source.replace(before, after)).returncode, 0)

    def test_qualification_requires_same_daemon_manifest_store_and_private_builder(self):
        for before, after in (
            ('test -z "$(docker ps -aq)"', 'true'),
            ('"containerd-snapshotter":true', '"containerd-snapshotter":false'),
            ('os.O_EXCL', 'os.O_CREAT'),
            ('sudo systemctl restart docker', 'true'),
            ('driver: docker', 'driver: docker-container'),
            ('test ! -e "$system_plugin"', 'true'),
            ('DOCKER_CONFIG="$qualifier_config"', 'DOCKER_CONFIG="$HOME/.docker"'),
            ('test "$(/usr/bin/docker --host unix:///var/run/docker.sock version --format', 'test "$(/bin/true --format'),
        ):
            with self.subTest(before=before):
                self.assertNotEqual(self.check(self.source.replace(before, after)).returncode, 0)

    def test_sandbox_dependency_installation_precedes_credentials(self):
        value = yaml.load(self.source, Loader=yaml.BaseLoader)
        steps = value['jobs']['build-image']['steps']
        sandbox = next(row for row in steps if row['name'] == 'Install local qualification sandbox')
        steps.remove(sandbox)
        credentials = next(i for i, row in enumerate(steps) if row['name'] == 'Configure AWS credentials')
        steps.insert(credentials + 1, sandbox)
        self.assertNotEqual(self.check(yaml.safe_dump(value, sort_keys=False)).returncode, 0)

    def test_scan_zero_critical_and_high_remain_mandatory(self):
        for severity in ('critical','high'):
            with self.subTest(severity=severity):
                changed=self.source.replace(f'{severity}" != "0"',f'{severity}" != "9"')
                self.assertNotEqual(self.check(changed).returncode,0)

    def test_exact_digest_sbom_and_attestation_subject_remain_mandatory(self):
        changed=self.source.replace('subject-digest: ${{ steps.image.outputs.digest }}','subject-digest: sha256:untrusted')
        self.assertNotEqual(self.check(changed).returncode,0)

    def test_no_target_mutation_allowed(self):
        self.assertNotEqual(self.check(self.source+'\n# aws ecs update-service\n').returncode,0)

    def test_workflow_preserves_source_identity_environment_and_oidc(self):
        value=yaml.load(self.source,Loader=yaml.BaseLoader)
        self.assertEqual(value['jobs']['build-image']['environment'],'staging')
        self.assertEqual(value['permissions']['id-token'],'write')
        steps=value['jobs']['build-image']['steps']
        main=next(row for row in steps if row['name']=='Enforce remote-main deploy source')
        self.assertIn('"$GITHUB_REF" != "refs/heads/main"',main['run'])
        credential=next(row for row in steps if row['name']=='Configure AWS credentials')
        self.assertEqual(credential['if'],'${{ inputs.publish_image }}')
        self.assertEqual(credential['with']['role-to-assume'],'${{ env.AWS_ROLE_ARN }}')
        self.assertEqual(value['on']['workflow_dispatch']['inputs'].keys(),{'publish_image'})
        self.assertEqual(next(row for row in steps if row['name']=='Set up Node')['with']['node-version'],'22.23.3')
        self.assertEqual(next(row for row in steps if row['name']=='Set up Python')['with']['python-version'],'3.14.4')
        self.assertIn('--require-hashes',next(row for row in steps if row['name']=='Install script dependencies')['run'])



    def test_receipt_upload_paths_are_explicit_and_raw_diagnostics_cannot_be_added(self):
        for path in ("${{ runner.temp }}/qualified-image/**", "${{ runner.temp }}/qualified-image/published-image.json", "${{ runner.temp }}/qualified-image/", "${{ runner.temp }}/qualified-image/credentials.json"):
            with self.subTest(path=path):
                changed=self.source.replace("${{ runner.temp }}/qualified-image/handoff/container-result.json",path)
                self.assertNotEqual(self.check(changed).returncode,0)

    def test_receipt_retention_pin_privacy_and_nonoverwriting_controls_are_required(self):
        for before,after in (("retention-days: 7","retention-days: 0"), ("include-hidden-files: false","include-hidden-files: true"), ("overwrite: false","overwrite: true"), ("if-no-files-found: error","if-no-files-found: warn"), ("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02","actions/upload-artifact@v4")):
            with self.subTest(before=before):
                self.assertNotEqual(self.check(self.source.replace(before,after)).returncode,0)

    def test_failed_producer_cannot_upload_partial_or_raw_runner_output(self):
        for before in ("if: ${{ success() }}", "if: ${{ inputs.publish_image && steps.image.outcome == 'success' }}"):
            with self.subTest(before=before):
                self.assertNotEqual(self.check(self.source.replace(before,"if: ${{ always() }}")).returncode,0)

    def test_receipt_uploads_precede_later_scan_or_attestation_failure(self):
        value=yaml.load(self.source,Loader=yaml.BaseLoader)
        names=[row['name'] for row in value['jobs']['build-image']['steps']]
        self.assertLess(names.index('Build platform shell image'),names.index('Retain normalized qualification receipts'))
        self.assertLess(names.index('Retain normalized qualification receipts'),names.index('Push platform shell image'))
        self.assertLess(names.index('Resolve immutable image digest'),names.index('Retain normalized publication receipt'))
        self.assertLess(names.index('Retain normalized publication receipt'),names.index('Read ECR scan finding counts'))


    def test_each_unpinned_action_is_refused(self):
        value=yaml.load(self.source,Loader=yaml.BaseLoader)
        for row in value['jobs']['build-image']['steps']:
            if 'uses' not in row:continue
            with self.subTest(step=row['name']):
                changed=self.source.replace(row['uses'],row['uses'].split('@')[0]+'@main',1)
                self.assertNotEqual(self.check(changed).returncode,0)

    def test_unreviewed_commit_or_additional_action_is_refused(self):
        value=yaml.load(self.source,Loader=yaml.BaseLoader)
        action=next(row['uses'] for row in value['jobs']['build-image']['steps'] if 'uses' in row)
        self.assertNotEqual(self.check(self.source.replace(action,action.split('@')[0]+'@'+'a'*40,1)).returncode,0)
        changed=self.source+'\n      - name: Unreviewed extra action\n        uses: actions/checkout@'+'a'*40+'\n'
        self.assertNotEqual(self.check(changed).returncode,0)

    def test_mutable_builder_and_sbom_downloads_are_refused(self):
        for before,after in (('version: v0.37.2','version: latest'),('driver: docker','driver: docker-container'),('releases/download/v1.42.3/','releases/download/latest/'),('sha256sum --check --status','true'),('SYFT_IMAGE: ${{ steps.image.outputs.uri }}','SYFT_IMAGE: mutable:latest')):
            with self.subTest(before=before):
                self.assertIn(before,self.source)
                self.assertNotEqual(self.check(self.source.replace(before,after)).returncode,0)

    def sbom_execution(self, *, image=None, corrupt_archive=False, changed_binary=False, version='1.42.3'):
        # Exercise the maintained shell protocol offline with a harmless fixture
        # executable. This does not execute downloaded Syft or contact Docker.
        row=next(row for row in yaml.load(self.source,Loader=yaml.BaseLoader)['jobs']['build-image']['steps'] if row['name']=='Generate image SBOM')
        run=row['run']
        binary=("#!/usr/bin/env python3\nimport json,os,pathlib,sys\n"
                "if sys.argv[1]=='version': print(json.dumps({'version':"+repr(version)+"}))\n"
                "elif sys.argv[1]=='scan':\n"
                " pathlib.Path(os.environ['SBOM_SCAN_MARKER']).write_text(sys.argv[2])\n"
                " pathlib.Path(sys.argv[4].split('=',1)[1]).write_text(json.dumps({'spdxVersion':'SPDX-2.3'}))\n").encode()
        archive=self.root/'fixture.tar.gz'
        with tarfile.open(archive,'w:gz') as stream:
            info=tarfile.TarInfo('syft');info.size=len(binary);info.mode=0o700
            stream.addfile(info,io.BytesIO(binary))
        archive_digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        binary_digest=hashlib.sha256(binary).hexdigest()
        run=run.replace('0d6be741479eddd2c8644a288990c04f3df0d609bbc1599a005532a9dff63509',archive_digest)
        run=run.replace('6c1eb5c6f15c177fa3dd727ee186c61a660a3939a4e1dc1bc4b3e00eafec098e','0'*64 if changed_binary else binary_digest)
        if corrupt_archive:archive.write_bytes(b'corrupt archive')
        commands=self.root/'commands';commands.mkdir()
        curl=commands/'curl'
        curl.write_text("#!/usr/bin/env python3\nimport os,pathlib,shutil,sys\npathlib.Path(os.environ['SBOM_DOWNLOAD_MARKER']).write_text('called')\nshutil.copyfile(os.environ['SBOM_TEST_ARCHIVE'],sys.argv[sys.argv.index('--output')+1])\n")
        curl.chmod(0o700)
        environment=dict(os.environ,PATH=str(commands)+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(self.root),
                         SYFT_IMAGE=image or 'example.invalid/repository@sha256:'+'a'*64,
                         SYFT_CHECK_FOR_APP_UPDATE='false',SBOM_TEST_ARCHIVE=str(archive),
                         SBOM_SCAN_MARKER=str(self.root/'scan-called'),SBOM_DOWNLOAD_MARKER=str(self.root/'download-called'))
        return subprocess.run(['bash','-c',run],env=environment,capture_output=True,timeout=20)

    def test_verified_sbom_protocol_produces_expected_fixture_output(self):
        result=self.sbom_execution();self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.root/'scan-called').read_text(),'docker:example.invalid/repository@sha256:'+'a'*64)
        self.assertEqual(json.loads((self.root/'platform-shell.sbom.spdx.json').read_text())['spdxVersion'],'SPDX-2.3')

    def test_sbom_mutable_image_refused_before_download(self):
        result=self.sbom_execution(image='example.invalid/repository:latest')
        self.assertNotEqual(result.returncode,0);self.assertFalse((self.root/'download-called').exists())
        self.assertFalse((self.root/'scan-called').exists())

    def test_sbom_corrupt_archive_refused_before_extraction_or_scan(self):
        result=self.sbom_execution(corrupt_archive=True)
        self.assertNotEqual(result.returncode,0);self.assertFalse((self.root/'scan-called').exists())
        self.assertFalse(any(self.root.glob('reviewed-syft.*/syft')))

    def test_sbom_changed_binary_refused_before_execution(self):
        result=self.sbom_execution(changed_binary=True)
        self.assertNotEqual(result.returncode,0);self.assertFalse((self.root/'scan-called').exists())

    def test_sbom_wrong_version_refused_before_scan(self):
        result=self.sbom_execution(version='9.9.9')
        self.assertNotEqual(result.returncode,0);self.assertFalse((self.root/'scan-called').exists())


    def clean_source_execution(self, change):
        repository=self.root/'clean-source-fixture';repository.mkdir()
        def git(*args):
            return subprocess.run(['git',*args],cwd=repository,check=True,capture_output=True,text=True)
        git('init','--quiet')
        (repository/'source.txt').write_text('reviewed source\n')
        (repository/'.gitignore').write_text('ignored-cache/\n')
        git('add','source.txt','.gitignore')
        git('-c','user.name=Workflow Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','commit','--quiet','-m','fixture')
        revision=git('rev-parse','HEAD').stdout.strip()
        if change=='unstaged':(repository/'source.txt').write_text('changed\n')
        elif change=='staged':
            (repository/'source.txt').write_text('changed\n');git('add','source.txt')
        elif change=='untracked':(repository/'untracked.txt').write_text('unreviewed\n')
        elif change=='newline-untracked':(repository/'\n').write_text('unreviewed\n')
        elif change=='ignored':
            (repository/'ignored-cache').mkdir();(repository/'ignored-cache'/'cache').write_text('allowed ignored data\n')
        elif change=='wrong-head':revision='0'*40
        value=yaml.load(self.source,Loader=yaml.BaseLoader)
        for name in ('Build platform shell image','Push platform shell image'):
            run=next(row['run'] for row in value['jobs']['build-image']['steps'] if row['name']==name)
            if name=='Build platform shell image':run=run.split('if ! bash scripts/',1)[0]
            else:run=run.split('python3 -I -B scripts/',1)[0]
            result=subprocess.run(['bash','-c',run],cwd=repository,env=dict(os.environ,GITHUB_SHA=revision),capture_output=True,timeout=20)
            with self.subTest(step=name,change=change):
                self.assertEqual(result.returncode==0,change in ('clean','ignored'),result.stderr)

    def test_clean_source_and_ignored_cache_are_accepted(self):
        self.clean_source_execution('clean')

    def test_ignored_cache_remains_accepted(self):
        self.clean_source_execution('ignored')

    def test_staged_source_change_is_refused_at_both_boundaries(self):
        self.clean_source_execution('staged')

    def test_unstaged_source_change_is_refused_at_both_boundaries(self):
        self.clean_source_execution('unstaged')

    def test_untracked_source_is_refused_at_both_boundaries(self):
        self.clean_source_execution('untracked')

    def test_newline_untracked_name_is_still_refused(self):
        self.clean_source_execution('newline-untracked')

    def test_wrong_head_is_refused_at_both_boundaries(self):
        self.clean_source_execution('wrong-head')

    def test_clean_source_checks_cannot_be_removed(self):
        for before in ('git diff --cached --quiet','git ls-files --others --exclude-standard -z','test "$(git rev-parse HEAD)" = "$GITHUB_SHA"'):
            with self.subTest(check=before):
                self.assertNotEqual(self.check(self.source.replace(before,'true')).returncode,0)

if __name__=='__main__':unittest.main()
