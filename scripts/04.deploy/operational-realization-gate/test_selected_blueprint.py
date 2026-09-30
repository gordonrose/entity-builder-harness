#!/usr/bin/env python3
"""Selected target blueprint compilation and source-drift refusal tests."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.selected-release-blueprint
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove selected blueprint source bindings, complete task coverage and authority refusal.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

GATE = Path(__file__).resolve().parent
ROOT = GATE.parents[2]
sys.path.insert(0, str(GATE))
sys.path.insert(0, str(ROOT / "scripts/04.deploy/release-control"))
import selected_blueprint as bp
import release_compiler as release

BLUEPRINT = bp.TARGET + "operational-realization/target-release-blueprint.v1.yml"
REV = "a" * 40
IMAGE = "sha256:" + "b" * 64


class SelectedBlueprintTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.blueprint = release.load_document(ROOT / BLUEPRINT)
        paths = [row["path"] for row in self.blueprint["source_bindings"]]
        paths += [self.blueprint["realization_contract"], self.blueprint["acceptance_policy"], BLUEPRINT]
        for relative in paths:
            dest = self.root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, dest)

    def compile(self):
        return bp.compile_blueprint(self.root, self.blueprint, REV, IMAGE, "selected-staging-review")

    def reject(self, code=None):
        with self.assertRaises(release.ReleaseFailure) as error:
            self.compile()
        if code:
            self.assertEqual(error.exception.code, code)
        self.assertNotIn("SENSITIVE", str(error.exception))

    def repin(self, relative):
        for row in self.blueprint["source_bindings"]:
            if row["path"] == relative:
                row["digest"] = "sha256:" + hashlib.sha256((self.root / relative).read_bytes()).hexdigest()
                return
        self.fail("fixture does not bind changed source")

    def change_template(self, edit):
        path = self.root / bp.profiles.TEMPLATE
        document = bp.source_document(path.read_text(), template=True)
        edit(document["Resources"])
        path.write_text(yaml.safe_dump(document, sort_keys=False))
        self.repin(bp.profiles.TEMPLATE)

    def change_contract(self, edit):
        path = self.root / self.blueprint["realization_contract"]
        document = release.load_document(path)
        edit(document)
        path.write_text(yaml.safe_dump(document, sort_keys=False))

    def test_actual_selected_graph_is_deterministic_and_stays_unqualified(self):
        result = self.compile()
        self.assertEqual(result, self.compile())
        self.assertEqual(len(result["operation_projection"]), 13)
        self.assertEqual(len({row["execution_group_digest"] for row in result["operation_projection"]}), 9)
        self.assertEqual(len(result["compiled_release"]["acceptance_matrix"]), 17)
        self.assertEqual(sum(len(row["operation_bindings"]) for row in result["compiled_release"]["acceptance_matrix"]), 221)
        self.assertFalse(result["authorized"])
        for key in ("operation_authorization", "release_eligibility", "qualification_verdict"):
            self.assertEqual(result[key], "blocked")
        self.assertTrue(all(row["command_qualification"] == "pending" for row in result["operation_projection"]))
        self.assertEqual(result["source_revision_status"], "declared")
        self.assertEqual(result["artifact_identity_status"], "declared")
        for row in result["compiled_release"]["acceptance_matrix"]:
            self.assertEqual(row["verdict"], "not-started")
        text = json.dumps(result)
        for private in ("arn:", "337159794548", "https://", "SecretArn", "password_value"):
            self.assertNotIn(private, text)

    def test_generated_definition_reuses_existing_compiler(self):
        result = self.compile()
        self.assertEqual(result["compiled_release"], release.compile_release(result["definition"], result["realization_contract"]))
        directory = self.root / "public"
        directory.mkdir()
        (directory / "release.json").write_text(json.dumps(result["definition"]))
        (directory / "contract.json").write_text(json.dumps(result["realization_contract"]))
        command = subprocess.run([sys.executable, str(GATE / "script.py"), "--release", str(directory / "release.json"),
                                  "--contract", str(directory / "contract.json")], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(command.returncode, 0, command.stderr)
        self.assertEqual(json.loads(command.stdout), result["compiled_release"])

    def test_app_commands_share_declared_image_without_substituting_sidecars(self):
        result = self.compile()
        artifacts = {row["artifact_id"]: row["digest"] for row in result["definition"]["artifact_digests"]}
        for op in self.blueprint["operations"]:
            self.assertEqual(artifacts[op["artifact_id"]] == IMAGE, "otel-collector" not in op["source_profile"])

    def test_source_change_refuses_stale_blueprint(self):
        path = self.root / bp.PROFILE
        path.write_text(path.read_text() + "\n# changed source\n")
        self.reject("blueprint-source-binding-stale")

    def test_omitted_source_binding_is_not_an_exemption(self):
        self.blueprint["source_bindings"] = [row for row in self.blueprint["source_bindings"] if row["path"] != "package-lock.json"]
        self.reject("blueprint-source-coverage-incomplete")

    def test_removed_command_source_fails(self):
        path = next(row["path"] for row in self.blueprint["source_bindings"] if row["path"].endswith("postgresql-bootstrap.main.ts"))
        (self.root / path).unlink()
        self.reject("container-profile-source-unreadable")

    def test_omitted_operation_fails(self):
        self.blueprint["operations"].pop()
        self.reject("blueprint-operation-coverage-invalid")

    def test_duplicate_operation_fails(self):
        self.blueprint["operations"].append(deepcopy(self.blueprint["operations"][0]))
        self.reject()

    def test_added_task_cannot_escape_selected_inventory(self):
        self.change_template(lambda r: r.update({"AdditionalTaskDefinition": deepcopy(r["RelationalBootstrapTaskDefinition"])}))
        self.reject("blueprint-operation-coverage-invalid")

    def test_changed_task_role_fails_even_with_fresh_source_hash(self):
        self.change_template(lambda r: r["RelationalBootstrapTaskDefinition"]["Properties"].update(TaskRoleArn={"Ref": "OtherRole"}))
        self.reject("blueprint-identity-binding-mismatch")

    def test_known_command_swap_cannot_keep_old_symbolic_entrypoint(self):
        def edit(resources):
            tasks = resources["RelationalBootstrapTaskDefinition"]["Properties"]["ContainerDefinitions"]
            tasks[0]["Command"] = [bp.profiles.PREFIX + "kanbien-platform-postgresql-migration.main.js"]
        self.change_template(edit)
        self.reject("blueprint-command-binding-mismatch")

    def test_changed_external_digest_is_not_qualified_by_old_binding(self):
        def edit(resources):
            for c in resources["TaskDefinition"]["Properties"]["ContainerDefinitions"]:
                if c["Name"] == "otel-collector":
                    c["Image"] = c["Image"].split("@sha256:")[0] + "@sha256:" + "e" * 64
        self.change_template(edit)
        self.reject("artifact-binding-mismatch")

    def test_source_owner_is_not_arbitrary(self):
        self.blueprint["owner"] = "another-owner"
        self.reject("blueprint-owner-mismatch")

    def test_main_only_publication_policy_cannot_disappear(self):
        path = self.root / bp.PROFILE
        path.write_text(path.read_text().replace("deployable_ref: refs/heads/main", "deployable_ref: refs/heads/other"))
        self.repin(bp.PROFILE)
        self.reject("blueprint-target-policy-mismatch")

    def test_dependency_on_later_operation_fails(self):
        self.blueprint["operations"][0]["depends_on"] = [self.blueprint["operations"][-1]["operation_id"]]
        self.reject("operation-dependency-invalid")

    def test_recovery_route_mismatch_fails(self):
        self.change_contract(lambda c: c["recovery_plans"][0].update(cleanup="different-cleanup"))
        self.reject("gate-operation-binding-mismatch")

    def test_uninterpreted_contract_field_never_reaches_public_output(self):
        self.change_contract(lambda c: c.update(unreviewed="SENSITIVE"))
        self.reject("blueprint-contract-fields-invalid")

    def test_all_seventeen_rows_are_required(self):
        path = self.root / self.blueprint["acceptance_policy"]
        policy = release.load_document(path)
        policy["rows"].pop()
        path.write_text(yaml.safe_dump(policy, sort_keys=False))
        self.reject("release-definition-invalid")

    def test_premature_success_and_not_applicable_are_refused(self):
        path = self.root / self.blueprint["acceptance_policy"]
        original = release.load_document(path)
        for verdict in ("passed", "not-applicable"):
            with self.subTest(verdict=verdict):
                policy = deepcopy(original)
                policy["rows"][0]["verdict"] = verdict
                path.write_text(yaml.safe_dump(policy, sort_keys=False))
                self.reject()

    def test_source_symlink_is_not_followed(self):
        path = self.root / "package-lock.json"
        path.unlink()
        path.symlink_to(ROOT / "package-lock.json")
        self.reject("container-profile-source-unreadable")

    def test_traversal_and_duplicate_source_bindings_fail(self):
        for value in ("../package.json", ".aws/credentials", "/tmp/private"):
            with self.subTest(path=value):
                old = self.blueprint["source_bindings"][0]["path"]
                self.blueprint["source_bindings"][0]["path"] = value
                self.reject()
                self.blueprint["source_bindings"][0]["path"] = old
        self.blueprint["source_bindings"].append(deepcopy(self.blueprint["source_bindings"][0]))
        self.reject()

    def test_source_race_is_refused(self):
        original = bp.SourceSnapshot.verify
        def race(snapshot):
            path = self.root / "package-lock.json"
            path.write_text(path.read_text() + "\n")
            original(snapshot)
        with patch.object(bp.SourceSnapshot, "verify", race):
            self.reject("blueprint-source-changed")

    def test_source_and_image_arguments_are_bound_into_identity(self):
        first = self.compile()
        second = bp.compile_blueprint(self.root, self.blueprint, "c" * 40, "sha256:" + "d" * 64, "new-staging-review")
        self.assertNotEqual(first["result_digest"], second["result_digest"])
        self.assertNotEqual(first["compiled_release"]["release_digest"], second["compiled_release"]["release_digest"])

    def test_invalid_identity_arguments_fail(self):
        for rev, image, name in (("main", IMAGE, "selected-staging-review"), (REV, "latest", "selected-staging-review"),
                                 (REV, IMAGE, "bad/name")):
            with self.subTest(rev=rev, image=image, name=name):
                with self.assertRaises(release.ReleaseFailure):
                    bp.compile_blueprint(self.root, self.blueprint, rev, image, name)

    def test_existing_source_consumer_refuses_blueprint_as_authority(self):
        path = self.root / "blueprint-result.json"
        path.write_text(json.dumps(self.compile()))
        for purpose in ("release-eligibility", "operation-authorization"):
            command = subprocess.run([sys.executable, str(GATE / "script.py"), "--consume-result", str(path),
                                      "--purpose", purpose], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(command.returncode, 0)
            self.assertFalse(json.loads(command.stdout)["authorized"])


if __name__ == "__main__":
    unittest.main()
