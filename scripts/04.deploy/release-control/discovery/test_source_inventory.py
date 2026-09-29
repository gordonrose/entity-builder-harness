#!/usr/bin/env python3
"""Adversarial tests for independent source enumeration and safe observations."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.source-inventory-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify source collector determinism, omitted-surface detection and fail-closed safety boundaries.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from source_inventory import canonical, digest, discover


class SourceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="source-inventory-test-")
        self.root = Path(self.temp.name)
        self.put("package.json", "{}")

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value))
        return target

    def result(self):
        return discover(self.root)

    def codes(self, result=None):
        return {finding["code"] for finding in (result or self.result())["findings"]}

    def kinds(self, result=None):
        return [item["kind"] for item in (result or self.result())["observations"]]

    def resource(self):
        return {"Resources": {"Task": {"Type": "AWS::ECS::TaskDefinition", "Properties": {
            "TaskRoleArn": {"Fn::ImportValue": "owned-elsewhere"},
            "ContainerDefinitions": [{"Name": "loader", "Image": "synthetic",
                "Command": ["loader"],
                "Environment": [{"Name": "MODE", "Value": "safe"}],
                "Secrets": [{"Name": "ACCESS", "ValueFrom": "synthetic-reference"}]}]}}}}

    def test_static_resource_inventory_is_deterministic_and_content_bound(self):
        self.put("infra/04.deploy/static.json", self.resource())
        first, second = self.result(), self.result()
        self.assertEqual(first, second)
        self.assertEqual(first["findings"], [])
        self.assertEqual(first["schema"], "source-inventory/v1")
        self.assertEqual(first["inventory_digest"], digest(canonical({k:v for k,v in first.items() if k != "inventory_digest"})))
        for kind in ("source-file", "resource", "container", "command-binding", "configuration-binding", "secret-binding", "identity-binding", "external-dependency"):
            self.assertIn(kind, self.kinds(first))
        ids = {item["id"] for item in first["observations"]}
        self.assertTrue(all(item["subject_id"] in ids for item in first["observations"]))

    def test_inventory_exposes_no_source_values_or_raw_locators(self):
        resource = self.resource()
        resource["Resources"]["confidential-resource-name"] = resource["Resources"].pop("Task")
        resource["Resources"]["confidential-resource-name"]["Properties"]["ContainerDefinitions"][0]["Secrets"][0]["ValueFrom"] = "secret-value-do-not-print"
        self.put("infra/04.deploy/static.json", resource)
        serialized = json.dumps(self.result())
        for value in ("secret-value-do-not-print", "confidential-resource-name", "owned-elsewhere", "synthetic-reference", "ContainerDefinitions", "TaskRoleArn"):
            self.assertNotIn(value, serialized)

    def test_new_package_command_changes_inventory(self):
        before = self.result()
        self.put("package.json", {"scripts": {"hidden": "node secret-loader.js"}})
        after = self.result()
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])
        self.assertIn("package-command", self.kinds(after))
        self.assertIn("opaque-executable", self.codes(after))
        self.assertNotIn("secret-loader", json.dumps(after))

    def test_new_process_entrypoint_is_found_independently(self):
        before = self.result()
        self.put("apps/new/src/hidden.main.ts", "startHiddenProcess();")
        after = self.result()
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])
        self.assertIn("source-entrypoint", self.kinds(after))
        self.assertIn("opaque-executable", self.codes(after))

    def test_hidden_sidecar_changes_independent_inventory(self):
        value = self.resource()
        self.put("infra/04.deploy/static.json", value)
        before = self.result()
        value["Resources"]["Task"]["Properties"]["ContainerDefinitions"].append({"Name": "hidden-sidecar", "Image": "image"})
        self.put("infra/04.deploy/static.json", value)
        after = self.result()
        self.assertEqual(self.kinds(after).count("container"), 2)
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])

    def test_hidden_secret_changes_independent_inventory(self):
        value = self.resource()
        self.put("infra/04.deploy/static.json", value)
        before = self.result()
        value["Resources"]["Task"]["Properties"]["ContainerDefinitions"][0]["Secrets"].append({"Name": "HIDDEN", "ValueFrom": "new-reference"})
        self.put("infra/04.deploy/static.json", value)
        after = self.result()
        self.assertEqual(self.kinds(after).count("secret-binding"), 2)
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])

    def test_changed_details_preserve_locator_but_change_digest(self):
        value = self.resource()
        self.put("infra/04.deploy/static.json", value)
        before = self.result()
        value["Resources"]["Task"]["Properties"]["ContainerDefinitions"][0]["Command"] = ["different-loader"]
        self.put("infra/04.deploy/static.json", value)
        after = self.result()
        old = next(item for item in before["observations"] if item["kind"] == "command-binding")
        new = next(item for item in after["observations"] if item["kind"] == "command-binding")
        self.assertEqual(old["id"], new["id"])
        self.assertNotEqual(old["detail_digest"], new["detail_digest"])

    def test_duplicate_json_keys_and_yaml_aliases_fail_closed(self):
        cases = [('package.json', '{"scripts":{}, "scripts":{}}', "source-key-invalid"),
                 ('infra/04.deploy/static.yml', 'Resources: &resources {}\nOther: *resources\n', "source-alias-unsupported")]
        for path, text, code in cases:
            with self.subTest(code=code):
                target = self.put(path, text)
                self.assertIn(code, self.codes())
                target.write_text("{}")

    def test_json_is_not_permissively_parsed_as_yaml(self):
        self.put("package.json", "name: invalid-json\n")
        self.assertIn("source-parse-failed", self.codes())

    def test_unknown_yaml_tags_and_duplicate_container_names_fail(self):
        self.put("infra/04.deploy/static.yml", "Resources: !Execute arbitrary\n")
        self.assertIn("source-tag-unsupported", self.codes())
        value = self.resource()
        containers = value["Resources"]["Task"]["Properties"]["ContainerDefinitions"]
        containers.append(deepcopy(containers[0]))
        self.put("infra/04.deploy/static.json", value)
        self.assertIn("container-shape-invalid", self.codes())

    def test_symbolic_import_is_hashed_as_external_dependency(self):
        self.put("infra/04.deploy/static.yml", "Resources:\n  Existing:\n    Type: AWS::ECS::TaskDefinition\n    Properties:\n      TaskRoleArn: !ImportValue private-upstream-name\n      ContainerDefinitions:\n        - Name: consumer\n          Image: synthetic\n          Command: [consume]\n")
        result = self.result()
        self.assertEqual(result["findings"], [])
        self.assertIn("external-dependency", self.kinds(result))
        self.assertNotIn("private-upstream-name", json.dumps(result))

    def test_unknown_resource_executables_are_not_plain_resources(self):
        for resource_type in ("AWS::Lambda::Function", "AWS::StepFunctions::StateMachine", "AWS::CloudFormation::CustomResource", "AWS::CloudFormation::Stack", "Custom::Invoke", "Generic::Task"):
            with self.subTest(resource_type=resource_type):
                value = {"Resources": {"Hidden": {"Type": resource_type, "Properties": {
                    "Runtime": "python3.12", "Handler": "index.main", "Role": "static-role",
                    "Code": {"ZipFile": "print('hidden-execution')"}}}}}
                self.put("infra/04.deploy/static.json", value)
                result = self.result()
                self.assertIn("resource", self.kinds(result))
                self.assertIn("resource-type-unsupported", self.codes(result))
                self.assertNotIn("hidden-execution", json.dumps(result))

    def test_dynamic_and_malformed_container_commands_remain_unresolved(self):
        for command in ({"Fn::If": ["Mode", ["node", "a.js"], ["node", "b.js"]]}, "node loader.js", [], ["node", None]):
            with self.subTest(command=command):
                value = self.resource()
                value["Resources"]["Task"]["Properties"]["ContainerDefinitions"][0]["Command"] = command
                self.put("infra/04.deploy/static.json", value)
                self.assertIn("container-command-unsupported", self.codes())

    def test_symbolic_missing_image_and_inherited_command_are_unresolved(self):
        value = self.resource()
        container = value["Resources"]["Task"]["Properties"]["ContainerDefinitions"][0]
        container["Image"] = {"Ref": "ImageUri"}
        self.put("infra/04.deploy/static.json", value)
        self.assertIn("container-image-unresolved", self.codes())
        del container["Image"]
        del container["Command"]
        self.put("infra/04.deploy/static.json", value)
        codes = self.codes()
        self.assertIn("container-image-missing", codes)
        self.assertIn("container-command-inherited", codes)

    def test_supported_task_requires_at_least_one_container(self):
        self.put("infra/04.deploy/static.json", {"Resources": {"Task": {"Type": "AWS::ECS::TaskDefinition", "Properties": {}}}})
        self.assertIn("container-shape-invalid", self.codes())

    def test_template_transforms_and_macros_are_unresolved(self):
        cases = [
            {"Transform": "AWS::Serverless-2016-10-31", "Resources": {}},
            {"Resources": {"Task": {"Type": "AWS::ECS::TaskDefinition", "Properties": {"Fn::Transform": {"Name": "HiddenMacro"}}}}},
        ]
        for value in cases:
            with self.subTest(value=value):
                self.put("infra/04.deploy/static.json", value)
                self.assertIn("infrastructure-transform-unsupported", self.codes())
        self.put("infra/04.deploy/static.yml", "Resources: {}\nOther: !Transform {Name: HiddenMacro}\n")
        self.assertIn("infrastructure-transform-unsupported", self.codes())

    def test_export_targets_are_content_bound_and_code_stays_unresolved(self):
        self.put("apps/a/package.json", {"exports": "./src/index.ts"})
        target = self.put("apps/a/src/index.ts", "export const value = 1;")
        before = self.result()
        target.write_text("export const value = 2;")
        after = self.result()
        self.assertNotEqual(before["inventory_digest"], after["inventory_digest"])
        self.assertIn("apps/a/src/index.ts", {item["path"] for item in after["sources"]})
        self.assertIn("opaque-export-target", self.codes(after))

    def test_declared_entrypoints_are_opaque_regardless_of_extension(self):
        self.put("apps/a/runtime", "startHiddenProcess();")
        for field in ("main", "module", "browser", "exports", "imports", "bin"):
            with self.subTest(field=field):
                value = {field: "./runtime"}
                if field == "imports":
                    value[field] = {"#internal": "./runtime"}
                self.put("apps/a/package.json", value)
                result = self.result()
                self.assertIn("package-bin" if field == "bin" else "package-export", self.kinds(result))
                self.assertIn("opaque-export-target", self.codes(result))
                self.assertIn("apps/a/runtime", {item["path"] for item in result["sources"]})

    def test_out_of_scope_export_is_never_treated_as_covered(self):
        self.put("runtime.ts", "startHiddenProcess();")
        self.put("package.json", {"exports": "./runtime.ts"})
        self.assertIn("source-reference-outside-scope", self.codes())

    def test_unsafe_source_filename_is_never_echoed(self):
        self.put("infra/04.deploy/private token.json", "{}")
        result = self.result()
        self.assertIn("source-path-unsafe", self.codes(result))
        self.assertNotIn("private token", json.dumps(result))
        self.assertTrue(any(item["path"] == "unavailable" for item in result["sources"]))

    def test_source_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory(prefix="outside-inventory-") as outside:
            sensitive = Path(outside) / "confidential"
            sensitive.write_text("secret-value-do-not-print")
            folder = self.root / "infra/04.deploy"
            folder.mkdir(parents=True)
            (folder / "linked.json").symlink_to(sensitive)
            result = self.result()
            self.assertIn("source-symlink-unsupported", self.codes(result))
            self.assertNotIn("secret-value-do-not-print", json.dumps(result))

    def test_scope_root_symlink_and_excluded_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="outside-inventory-") as outside:
            (self.root / "infra").symlink_to(outside, target_is_directory=True)
            self.assertIn("source-symlink-unsupported", self.codes())
            (self.root / "infra").unlink()
            folder = self.root / "scripts/04.deploy"
            folder.mkdir(parents=True)
            (folder / "fixtures").symlink_to(outside, target_is_directory=True)
            self.assertIn("source-symlink-unsupported", self.codes())

    def test_root_through_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="outside-inventory-") as outside:
            link = Path(outside) / "root-link"
            link.symlink_to(self.root, target_is_directory=True)
            self.assertIn("source-root-invalid", self.codes(discover(link)))

    def test_missing_root_manifest_and_unknown_executable_are_unresolved(self):
        (self.root / "package.json").unlink()
        self.put("scripts/04.deploy/hidden/run.rb", "dangerous()")
        codes = self.codes()
        self.assertIn("package-root-missing", codes)
        self.assertIn("executable-format-unsupported", codes)

    def test_fixed_fixture_exclusions_do_not_classify_scripts_as_test_only(self):
        self.put("scripts/04.deploy/example/fixtures/ignored.sh", "echo fixture")
        self.put("scripts/04.deploy/example/smoke-test.sh", "perform_live_mutation")
        result = self.result()
        self.assertEqual(self.kinds(result).count("script-entrypoint"), 1)
        self.assertIn("opaque-executable", self.codes(result))
        self.assertNotIn("test-only", json.dumps(result))

    def test_package_export_and_bin_targets_are_checked(self):
        self.put("apps/a/package.json", {"exports": {".": "./tests/helper.js"}, "bin": {"a": "./missing.js"}})
        result = self.result()
        self.assertIn("package-export", self.kinds(result))
        self.assertIn("package-bin", self.kinds(result))
        self.assertIn("excluded-source-reference", self.codes(result))
        self.assertIn("source-reference-missing", self.codes(result))
        self.put("apps/a/package.json", {"exports": "./../../outside.js"})
        self.assertIn("source-reference-outside-scope", self.codes())

    def test_out_of_scope_workspace_cannot_hide_package(self):
        self.put("package.json", {"workspaces": ["outside/*"]})
        self.assertIn("workspace-scope-unsupported", self.codes())

    def test_workflow_steps_services_and_secret_references_are_collected(self):
        self.put(".github/workflows/static.yml", "on: push\njobs:\n  check:\n    services:\n      dependency:\n        image: immutable-image\n    steps:\n      - run: echo private-command\n        env:\n          ACCESS: '${{ secrets.ACCESS }}'\n")
        result = self.result()
        for kind in ("workflow-step", "workflow-service", "secret-binding"):
            self.assertIn(kind, self.kinds(result))
        self.assertEqual(self.codes(result), {"opaque-executable"})
        self.assertNotIn("private-command", json.dumps(result))

    def test_final_image_source_commands_are_structural_only(self):
        self.put("infra/04.deploy/image/Dockerfile", 'FROM scratch\nENTRYPOINT ["loader"]\nCMD ["run"]\nENV MODE=safe\n')
        result = self.result()
        self.assertEqual(result["findings"], [])
        self.assertEqual(self.kinds(result).count("image-command"), 2)
        self.put("infra/04.deploy/image/Dockerfile", 'FROM external-base\nCMD ["run"]\n')
        self.assertIn("image-entrypoint-inherited", self.codes())

    def test_unsupported_infrastructure_grammars_are_not_plain_documents(self):
        self.put("infra/04.deploy/compose.yml", "services:\n  hidden:\n    image: arbitrary\n")
        self.put("infra/04.deploy/hidden.tf", 'resource "unknown" "hidden" {}')
        codes = self.codes()
        self.assertIn("infrastructure-format-unsupported", codes)
        self.assertIn("executable-format-unsupported", codes)

    def test_infrastructure_code_is_opaque_without_main_suffix(self):
        self.put("infra/04.deploy/hidden/loader.ts", "startHiddenProcess();")
        self.assertIn("source-entrypoint", self.kinds())
        self.assertIn("opaque-executable", self.codes())

    def test_unsupported_docker_commands_do_not_look_qualified(self):
        self.put("infra/04.deploy/image/Dockerfile", 'FROM external-base\nRUN arbitrary-build\nENTRYPOINT arbitrary-shell\n')
        codes = self.codes()
        self.assertIn("opaque-image-build", codes)
        self.assertIn("image-command-unsupported", codes)


if __name__ == "__main__":
    unittest.main()
