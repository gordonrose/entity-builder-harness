#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.environment-session-controller.package-workflow
#   version: 1
#   status: draft
#   created_on: "2026-11-28"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove controller publication gates and committed-source build failure propagation without AWS or Docker.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.environment-session-controller.package-wrapper
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/environment-session-controller-package-custody/smoke-test.sh
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("tested_session_package", HERE / "verify-workflow.py")
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (CONTROL.ROOT / CONTROL.WORKFLOW).read_text()
        cls.guard = CONTROL.module("package_test_guard", CONTROL.ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/workflow_guard.py")
        cls.documents = CONTROL.module("package_test_documents", CONTROL.ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")

    def test_real_workflow_and_target_catalogue_are_connected(self):
        self.assertEqual(CONTROL.check(), {"verdict": "passed", "publication_performed": False})
        declaration = CONTROL.module("package_target_catalogue", CONTROL.ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py")
        declaration.check_pipeline(CONTROL.ROOT / CONTROL.TARGET)

    def test_omission_reordering_overrides_and_wrong_destination_reject(self):
        import yaml
        original = self.guard.workflow_document(self.text)
        steps = original["jobs"]["qualify-and-publish"]["steps"]
        names = {row.get("name"): index for index, row in enumerate(steps)}
        cases = []
        for name in ("Qualify declarations and actual candidate payload", "Require clean ECR scan",
                     "Attest image provenance", "Attest image SBOM", "Retain pre-publication identity"):
            changed = deepcopy(original)
            changed["jobs"]["qualify-and-publish"]["steps"].pop(names[name])
            cases.append(changed)
        for field, value in (("if", False), ("continue-on-error", True), ("env", {"PATH": "foreign"})):
            changed = deepcopy(original)
            changed["jobs"]["qualify-and-publish"]["steps"][names["Qualify declarations and actual candidate payload"]][field] = value
            cases.append(changed)
        changed = deepcopy(original)
        changed["env"]["ECR_REPOSITORY"] = "kanbien-core-platform/core-server"
        cases.append(changed)
        changed = deepcopy(original)
        selected = changed["jobs"]["qualify-and-publish"]["steps"]
        selected[4], selected[5] = selected[5], selected[4]
        cases.append(changed)
        changed = deepcopy(original)
        changed["jobs"]["qualify-and-publish"]["steps"].insert(6, {"name": "Deploy", "run": "aws cloudformation deploy"})
        cases.append(changed)
        for index, value in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValueError):
                CONTROL.check(yaml.safe_dump(value, sort_keys=False))

    def test_duplicate_workflow_keys_are_not_last_writer_wins(self):
        with self.assertRaises(ValueError):
            self.guard.workflow_document("on: {}\non: {push: {}}\n")
        self.assertEqual(self.guard.workflow_document("on: {workflow_dispatch: {}}\nenabled: false"),
                         {"on": {"workflow_dispatch": {}}, "enabled": False})

    def test_publisher_cannot_gain_workload_or_foreign_registry_permissions(self):
        source = self.documents.template((CONTROL.ROOT / CONTROL.TARGET / "30-provider-realization/aws/cloudformation/environment-session-controller-publication.yml").read_text())
        statements = source["Resources"]["ControllerPublisherRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
        statements[1]["Action"].sort()
        access = self.documents.template((CONTROL.ROOT / CONTROL.TARGET / "40-package-custody/github-actions/environment-session-controller-package-custody.delivery-access.yml").read_text())
        CONTROL.policy(source, access)
        for field, value in (("Action", ["cloudformation:DeleteStack"]), ("Resource", "*"), ("Effect", "Deny")):
            changed = deepcopy(source)
            changed["Resources"]["ControllerPublisherRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                CONTROL.policy(changed, access)

    def test_cleanup_executes_image_code_not_zip_code_or_python_path(self):
        source = self.documents.template((CONTROL.ROOT / CONTROL.TARGET / "30-provider-realization/aws/cloudformation/environment-sessions.yml").read_text())
        specification = self.guard.workflow_document(source["Resources"]["Cleanup"]["Properties"]["Source"]["BuildSpec"])
        self.assertEqual(specification["phases"]["build"]["commands"], [
            '/usr/local/bin/python3 -I -B /opt/controller/scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/script.py cleanup --input "$CODEBUILD_SRC_DIR/session-input.json" --max-seconds 540'])

    def test_builder_binds_committed_archive_and_stops_before_receipt_on_smoke_failure(self):
        with tempfile.TemporaryDirectory(prefix="controller-build-proof-") as directory:
            directory = Path(directory)
            root, binary = directory / "repo", directory / "bin"
            root.mkdir(); binary.mkdir()
            paths = [CONTROL.BUILDER, "scripts/04.deploy/shared/safe-command-diagnostics.sh",
                "scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh",
                "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py"]
            for name in paths:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(CONTROL.ROOT / name, target)
            contract = root / CONTROL.IMAGE / "image-contract.yml"
            contract.parent.mkdir(parents=True)
            contract.write_text(json.dumps({"schema": "deploy/controller-image-contract/v1",
                "source_paths": ["scripts/04.deploy", "infra/04.deploy"]}))
            (root / ".gitignore").write_text("scripts/04.deploy/ignored-secret.txt\n")
            environment = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
            def git(*arguments):
                subprocess.run(["git", *arguments], cwd=root, env=environment, check=True, capture_output=True, timeout=15)
            git("init", "-q"); git("add", "."); git("commit", "-qm", "fixture")
            (root / "scripts/04.deploy/ignored-secret.txt").write_text("private-package-canary")
            fake = binary / "docker"
            fake.write_text("#!" + sys.executable + "\n" + """import json,os,sys,tarfile
from pathlib import Path
args=sys.argv[1:]
with Path(os.environ['DOCKER_CALLS']).open('a') as out:out.write(json.dumps(args)+'\\n')
if args[0]=='build':
    with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
        assert all('ignored-secret' not in row.name for row in archive)
elif args[:2]==['image','inspect']:print('sha256:'+'a'*64)
elif args[0]=='run' and '/usr/local/bin/aws' in args:print('aws-cli/2.36.50 fixture')
elif args[0]=='run' and os.environ.get('SMOKE_FAIL')=='1':raise SystemExit(9)
""")
            fake.chmod(0o700)
            calls = directory / "calls.jsonl"
            environment.update(PATH=str(binary) + os.pathsep + os.environ["PATH"], DOCKER_CALLS=str(calls))
            def build(receipt, **extra):
                return subprocess.run(["bash", str(root / CONTROL.BUILDER), "--tag", "kanbien-environment-session-controller:qualification",
                    "--receipt", str(receipt)], cwd=root, env={**environment, **extra}, capture_output=True, text=True, timeout=30)
            failed = directory / "failed.json"
            self.assertEqual(build(failed, SMOKE_FAIL="1").returncode, 9)
            self.assertFalse(failed.exists())
            qualified = directory / "qualified.json"
            result = build(qualified)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(qualified.read_text())
            self.assertEqual(receipt["image_id"], "sha256:" + "a" * 64)
            self.assertNotIn("scripts/04.deploy/ignored-secret.txt", receipt["inputs"])
            before = calls.read_bytes()
            (root / "untracked.txt").write_text("uncommitted")
            rejected = build(directory / "not-qualified.json")
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("SESSION_IMAGE_COMMITTED_SOURCE_REQUIRED", rejected.stderr)
            self.assertEqual(calls.read_bytes(), before)
            self.assertTrue(all(row[0] not in {"push", "tag", "login"} for row in map(json.loads, calls.read_text().splitlines())))


if __name__ == "__main__":
    unittest.main()
