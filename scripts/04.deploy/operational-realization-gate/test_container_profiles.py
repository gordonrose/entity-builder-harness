"""Check complete command accounting and reject unsafe or ambiguous descriptors."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.container-profiles
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify source-bound container obligations, fail-closed command discovery and exact payload coverage.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import container_profiles as profiles
import release_compiler as release

REPOSITORY = DIRECTORY.parents[2]
DOCKERFILE = 'FROM runtime\nWORKDIR /app\nCMD ["' + profiles.SERVER + '"]\n'
TEMPLATE = '''Resources:
  Server:
    Type: AWS::ECS::TaskDefinition
    Properties:
      ContainerDefinitions:
        - Name: server
          Image: !Ref ImageUri
  Bootstrap:
    Type: AWS::ECS::TaskDefinition
    Properties:
      ContainerDefinitions:
        - Name: bootstrap
          Image: !Ref ImageUri
          Command: [.cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.js]
'''


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="container-profiles-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.docker = self.root / profiles.DOCKERFILE
        self.template = self.root / profiles.TEMPLATE
        self.docker.parent.mkdir(parents=True)
        self.template.parent.mkdir(parents=True)
        self.docker.write_text(DOCKERFILE)
        self.template.write_text(TEMPLATE)

    def discover(self):
        return profiles.discover(self.root)

    def reject(self, template=None, docker=None):
        if template is not None:
            self.template.write_text(template)
        if docker is not None:
            self.docker.write_text(docker)
        with self.assertRaises(release.ReleaseFailure) as failure:
            self.discover()
        self.assertNotIn("SENSITIVE_SENTINEL", str(failure.exception))

    def test_literal_and_inherited_commands_are_separate_pending_profiles(self):
        rows = self.discover()
        self.assertEqual(len(rows), 3)
        self.assertEqual([row["id"] for row in rows], sorted(row["id"] for row in rows))
        self.assertEqual({row["status"] for row in rows}, {"pending"})
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id["image-default"]["command"], by_id["task-Server-server"]["command"])
        self.assertEqual(by_id["task-Bootstrap-bootstrap"]["kind"], "finite-task")
        self.assertEqual(by_id["image-default"]["reason"], "local-runtime-unverified")
        self.assertEqual(by_id["task-Server-server"]["reason"], "target-runtime-unqualified")

    def test_actual_repository_accounts_for_all_fourteen_profiles(self):
        rows = profiles.discover(REPOSITORY)
        self.assertEqual(len(rows), 14)
        self.assertEqual(sum(row["image_scope"] == "external" for row in rows), 4)
        self.assertEqual(sum(row["kind"] == "finite-task" for row in rows), 5)
        self.assertEqual({row["command"][0] for row in rows if row["command"]}, set(profiles.COMMAND_KINDS))
        self.assertTrue(all(row["status"] == "pending" for row in rows))

    def test_discovery_is_deterministic(self):
        self.assertEqual(self.discover(), self.discover())

    def test_source_digests_are_exact_descriptor_bytes(self):
        for row in self.discover():
            expected = "sha256:" + hashlib.sha256((self.root / row["source_path"]).read_bytes()).hexdigest()
            self.assertEqual(row["source_digest"], expected)

    def test_target_configuration_change_invalidates_target_binding(self):
        before = self.discover()
        self.template.write_text(TEMPLATE.replace("Image: !Ref ImageUri", "Image: !Ref ImageUri\n          Environment: [{Name: SECRET_VALUE, Value: SENSITIVE_SENTINEL}]"))
        after = self.discover()
        self.assertNotEqual(before[1]["source_digest"], after[1]["source_digest"])
        self.assertEqual(before[0], after[0])
        self.assertNotIn("SENSITIVE_SENTINEL", json.dumps(after))
        self.assertNotIn("SECRET_VALUE", json.dumps(after))

    def test_new_task_is_included_without_changing_collector(self):
        extra = TEMPLATE.split("  Bootstrap:")[1]
        self.template.write_text(TEMPLATE + "  SecondBootstrap:" + extra)
        rows = self.discover()
        self.assertEqual(len(rows), 4)
        self.assertIn("task-SecondBootstrap-bootstrap", [row["id"] for row in rows])

    def test_new_task_unsupported_command_cannot_silently_disappear(self):
        self.reject(TEMPLATE + '''  Unknown:
    Type: AWS::ECS::TaskDefinition
    Properties:
      ContainerDefinitions:
        - Name: unknown
          Image: !Ref ImageUri
          Command: [.cache/unknown.js]
''')

    def test_candidate_image_reference_is_product(self):
        self.template.write_text(TEMPLATE.replace("!Ref ImageUri", "{Ref: CandidateImageUri}"))
        self.assertEqual({row["image_scope"] for row in self.discover()}, {"product"})

    def test_fixed_external_image_stays_pending_and_digest_bound(self):
        digest = "a" * 64
        self.template.write_text(TEMPLATE.replace("Image: !Ref ImageUri", "Image: registry.example/sidecar@sha256:" + digest))
        rows = self.discover()
        for row in rows[1:]:
            self.assertEqual(row["image_scope"], "external")
            self.assertEqual(row["image_digest"], "sha256:" + digest)
            self.assertEqual(row["reason"], "external-image-unqualified")
            self.assertEqual(row["command"], [])

    def test_dynamic_external_image_is_explicitly_unresolved(self):
        self.template.write_text(TEMPLATE.replace("!Ref ImageUri", "!Sub '${SENSITIVE_SENTINEL}/image'"))
        rows = self.discover()
        self.assertTrue(all(row["reason"] == "unresolved-image" for row in rows[1:]))
        self.assertNotIn("SENSITIVE_SENTINEL", json.dumps(rows))

    def test_shell_docker_command_rejected(self):
        self.reject(docker="FROM runtime\nCMD node SENSITIVE_SENTINEL\n")

    def test_changed_default_command_rejected(self):
        self.reject(docker=DOCKERFILE.replace("server.main", "worker.main"))

    def test_healthcheck_command_is_not_default_command(self):
        self.docker.write_text(DOCKERFILE + 'HEALTHCHECK --interval=5s CMD ["node", "-e", "0"]\n')
        self.assertEqual(self.discover()[0]["command"], [profiles.SERVER])

    def test_multistage_default_reads_only_final_stage(self):
        self.docker.write_text('FROM builder\nCMD ["ignored"]\n' + DOCKERFILE)
        self.assertEqual(self.discover()[0]["command"], [profiles.SERVER])

    def test_continued_cmd_supported(self):
        self.docker.write_text(DOCKERFILE.replace("CMD [", "CMD \\\n ["))
        self.assertEqual(self.discover()[0]["command"], [profiles.SERVER])

    def test_duplicate_default_commands_rejected(self):
        self.reject(docker=DOCKERFILE + 'CMD ["' + profiles.SERVER + '"]\n')

    def test_changed_image_entrypoint_rejected(self):
        self.reject(docker=DOCKERFILE + 'ENTRYPOINT ["/bin/sh"]\n')

    def test_explicit_reviewed_node_entrypoint_supported(self):
        self.docker.write_text(DOCKERFILE + 'ENTRYPOINT ["/nodejs/bin/node"]\n')
        self.assertEqual(len(self.discover()), 3)

    def test_nonliteral_task_command_rejected(self):
        self.reject(TEMPLATE.replace("Command: [", "Command: !If ["))

    def test_nonliteral_command_element_rejected(self):
        self.reject(TEMPLATE.replace("Command: [", "Command: [!Sub "))

    def test_unknown_literal_command_rejected(self):
        self.reject(TEMPLATE.replace("postgresql-bootstrap.main.js", "new-operation.main.js"))

    def test_absolute_command_path_rejected(self):
        self.reject(TEMPLATE.replace("Command: [", "Command: [/"))

    def test_parent_escape_command_path_rejected(self):
        self.reject(TEMPLATE.replace("Command: [", "Command: [../"))

    def test_extra_command_argument_rejected(self):
        self.reject(TEMPLATE.replace("bootstrap.main.js]", "bootstrap.main.js, SENSITIVE_SENTINEL]"))

    def test_entrypoint_override_rejected(self):
        self.reject(TEMPLATE.replace("Image: !Ref ImageUri", 'Image: !Ref ImageUri\n          EntryPoint: ["/bin/sh"]'))

    def test_changed_working_directory_rejected(self):
        self.reject(TEMPLATE.replace("Image: !Ref ImageUri", 'Image: !Ref ImageUri\n          WorkingDirectory: /other'))

    def test_duplicate_keys_rejected(self):
        self.reject(TEMPLATE.replace("Name: server", "Name: server\n          Name: duplicate"))

    def test_duplicate_resource_rejected(self):
        self.reject(TEMPLATE + TEMPLATE[len("Resources:\n"):])

    def test_duplicate_container_ids_rejected(self):
        self.reject(TEMPLATE.replace("  Bootstrap:", "        - Name: server\n          Image: !Ref ImageUri\n  Bootstrap:"))

    def test_alias_rejected_before_expansion(self):
        self.reject(TEMPLATE.replace("Name: server", "Name: &alias server") + "Alias: *alias\n")

    def test_unknown_tag_rejected(self):
        self.reject(TEMPLATE.replace("!Ref ImageUri", "!Secret SENSITIVE_SENTINEL"))

    def test_python_object_yaml_tag_rejected(self):
        self.reject(TEMPLATE.replace("!Ref ImageUri", "!!python/object/new:tuple [SENSITIVE_SENTINEL]"))

    def test_parent_directory_symlink_rejected(self):
        original = self.template.parent
        displaced = original.with_name("moved")
        original.rename(displaced)
        original.symlink_to(displaced.name, target_is_directory=True)
        self.reject()

    def test_fifo_descriptor_rejected_without_blocking(self):
        self.template.rename(self.template.with_suffix(".original"))
        os.mkfifo(self.template)
        self.reject()

    def test_missing_image_build_stage_rejected(self):
        self.reject(docker=DOCKERFILE.replace("FROM runtime\n", ""))

    def test_dynamic_resource_type_rejected(self):
        self.reject(TEMPLATE.replace("Type: AWS::ECS::TaskDefinition", "Type: !Ref ResourceType"))

    def test_dynamic_containers_rejected(self):
        self.reject("Resources: {Task: {Type: 'AWS::ECS::TaskDefinition', Properties: {ContainerDefinitions: !Ref Containers}}}")

    def test_empty_task_inventory_rejected(self):
        self.reject("Resources: {}")

    def test_no_container_image_rejected(self):
        self.reject(TEMPLATE.replace("          Image: !Ref ImageUri\n", ""))

    def test_unsafe_container_name_rejected(self):
        self.reject(TEMPLATE.replace("Name: server", "Name: '../SENSITIVE_SENTINEL'"))

    def test_combined_identifier_cannot_exceed_result_contract(self):
        self.reject(TEMPLATE.replace("  Server:", "  " + "S" * 100 + ":")
                    .replace("Name: server", "Name: " + "s" * 100))

    def test_deep_document_rejected(self):
        self.reject(TEMPLATE + "Deep: " + "[" * 40 + "0" + "]" * 40)

    def test_document_size_bounded(self):
        self.reject(TEMPLATE + "#" + "x" * profiles.MAX_BYTES)

    def test_document_node_count_bounded(self):
        with patch.object(profiles, "MAX_NODES", 10):
            self.reject(TEMPLATE)

    def test_task_count_bounded(self):
        with patch.object(profiles, "MAX_CONTAINERS", 1):
            self.reject(TEMPLATE)

    def test_descriptor_symlink_rejected(self):
        displaced = self.template.with_suffix(".original")
        self.template.rename(displaced)
        self.template.symlink_to(displaced.name)
        self.reject()

    def test_missing_descriptor_rejected(self):
        self.template.rename(self.template.with_suffix(".absent"))
        self.reject()

    def test_invalid_utf8_is_fixed_failure(self):
        self.template.write_bytes(b"\xffSENSITIVE_SENTINEL")
        self.reject()


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.rows = profiles.discover(REPOSITORY)
        self.files = [{"path": path, "digest": "sha256:" + "a" * 64, "bytes": 1}
                      for path in sorted(profiles.COMMAND_KINDS)]

    def test_all_product_commands_present(self):
        self.assertEqual(profiles.require_payload(self.rows, self.files), self.rows)

    def test_missing_bootstrap_cannot_inherit_server_coverage(self):
        files = [row for row in self.files if "bootstrap" not in row["path"]]
        with self.assertRaisesRegex(release.ReleaseFailure, "container-profile-command-missing"):
            profiles.require_payload(self.rows, files)

    def test_missing_relay_cannot_inherit_other_command_coverage(self):
        files = [row for row in self.files if "postgresql-relay" not in row["path"]]
        with self.assertRaises(release.ReleaseFailure):
            profiles.require_payload(self.rows, files)

    def test_duplicate_manifest_path_rejected(self):
        with self.assertRaises(release.ReleaseFailure):
            profiles.require_payload(self.rows, self.files + [self.files[0]])

    def test_unsafe_manifest_path_rejected(self):
        with self.assertRaises(release.ReleaseFailure):
            profiles.require_payload(self.rows, self.files + [{"path": "../secret"}])

    def test_duplicate_profile_id_rejected(self):
        with self.assertRaises(release.ReleaseFailure):
            profiles.require_payload(self.rows + [self.rows[0]], self.files)

    def test_external_profile_cannot_be_qualified(self):
        rows = copy.deepcopy(self.rows)
        next(row for row in rows if row["image_scope"] == "external")["status"] = "passed"
        with self.assertRaises(release.ReleaseFailure):
            profiles.require_payload(rows, self.files)

    def test_external_profile_does_not_require_foreign_image_files(self):
        self.assertTrue(any(row["image_scope"] == "external" for row in self.rows))
        profiles.require_payload(self.rows, self.files)


if __name__ == "__main__":
    unittest.main()
