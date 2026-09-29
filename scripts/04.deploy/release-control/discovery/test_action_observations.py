#!/usr/bin/env python3
"""Positive and adversarial source tests for action declaration observations."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.action-observations-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify action declaration binding, source freshness and safe unresolved defaults.
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
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from action_observations import observe_actions
from caller_inventory import discover_callers
from source_inventory import SourceFailure, digest


class ActionObservationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="action-observations-test-")
        self.root = Path(self.temp.name)
        self.workflow = ".github/workflows/staging.yml"
        self.document = {
            "on": {"workflow_dispatch": {"inputs": {"publish": {"type": "boolean", "default": True}}}},
            "permissions": {"contents": "read", "id-token": "write"},
            "env": {"REGISTRY": "fixture-registry"},
            "jobs": {"build": {"runs-on": "ubuntu-latest", "environment": "staging", "steps": [{
                "uses": "example/action@v1", "if": "${{ inputs.publish }}",
                "with": {"subject-digest": "${{ steps.image.outputs.digest }}", "upload": False},
            }]}},
        }
        self.put(self.document)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, document):
        path = self.root / self.workflow
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document if isinstance(document, str) else json.dumps(document))

    @property
    def step(self):
        return self.document["jobs"]["build"]["steps"][0]

    def observe(self, graph=None):
        return observe_actions(self.root, self.workflow, graph or discover_callers(self.root, self.workflow))

    def codes(self, result=None):
        return {finding["code"] for finding in (result or self.observe())[1]}

    @staticmethod
    def kinds(result):
        return {row["kind"] for row in result[0]}

    def detail(self, kind, result=None):
        return {row["detail_digest"] for row in (result or self.observe())[0] if row["kind"] == kind}

    def test_literal_and_expression_inputs_are_complete_and_deterministic(self):
        first = self.observe()
        self.assertEqual(first, self.observe())
        self.assertEqual(self.kinds(first), {
            "action-reference", "action-input-set", "action-input-literal", "action-input-expression",
            "action-context", "action-condition", "action-upstream-output",
        })
        self.assertEqual(self.codes(first), {
            "mutable-action-reference", "action-defaults-unresolved", "action-implementation-unresolved",
        })
        self.assertEqual(sum(row["kind"].startswith("action-input-") for row in first[0]), 3)
        graph = discover_callers(self.root, self.workflow)
        ids = {node["id"] for node in graph["nodes"]}
        self.assertTrue(all(row["subject_id"] in ids for row in first[0]))
        for row in first[0]:
            self.assertEqual(set(row), {"id", "subject_id", "source_id", "kind", "locator_digest", "detail_digest"})
            for key, value in row.items():
                if key != "kind":
                    self.assertRegex(value, r"^sha256:[0-9a-f]{64}$")

    def test_immutable_reference_retains_remote_implementation_and_defaults_obligations(self):
        self.step["uses"] = "example/action@" + "a" * 40
        self.put(self.document)
        self.assertEqual(self.codes(), {"action-defaults-unresolved", "action-implementation-unresolved"})

    def test_empty_inputs_are_observed_and_absence_is_distinct(self):
        del self.step["with"]
        self.put(self.document)
        absent = self.observe()
        self.assertIn("action-input-set", self.kinds(absent))
        self.step["with"] = {}
        self.put(self.document)
        self.assertNotEqual(self.detail("action-input-set", absent), self.detail("action-input-set"))

    def test_changing_reference_changes_binding_but_not_subject(self):
        before = self.observe()
        self.step["uses"] = "example/action@v2"
        self.put(self.document)
        after = self.observe()
        self.assertEqual({row["subject_id"] for row in before[0]}, {row["subject_id"] for row in after[0]})
        self.assertNotEqual(self.detail("action-reference", before), self.detail("action-reference", after))

    def test_removed_input_changes_set_and_drops_its_observation(self):
        before = self.observe()
        del self.step["with"]["upload"]
        self.put(self.document)
        after = self.observe()
        self.assertNotEqual(self.detail("action-input-set", before), self.detail("action-input-set", after))
        self.assertNotIn("action-input-literal", self.kinds(after))

    def test_changed_input_literal_has_new_detail(self):
        before = self.observe()
        self.step["with"]["upload"] = True
        self.put(self.document)
        self.assertNotEqual(self.detail("action-input-literal", before), self.detail("action-input-literal"))

    def test_permissions_and_absent_overrides_are_bound(self):
        before = self.observe()
        self.document["jobs"]["build"]["permissions"] = {"contents": "read"}
        self.put(self.document)
        self.assertNotEqual(self.detail("action-context", before), self.detail("action-context"))

    def test_inherited_workflow_permission_change_invalidates_context(self):
        before = self.observe()
        self.document["permissions"]["id-token"] = "none"
        self.put(self.document)
        self.assertNotEqual(self.detail("action-context", before), self.detail("action-context"))

    def test_trigger_runner_environment_and_unknown_context_fields_are_bound(self):
        for scope, key, value in (
            (self.document, "on", {"push": {}}),
            (self.document["jobs"]["build"], "runs-on", "self-hosted"),
            (self.document["jobs"]["build"], "environment", "production"),
            (self.step, "future-context", "different"),
        ):
            with self.subTest(key=key):
                before = self.observe()
                scope[key] = value
                self.put(self.document)
                self.assertNotEqual(self.detail("action-context", before), self.detail("action-context"))

    def test_changed_condition_changes_condition_and_context(self):
        before = self.observe()
        self.step["if"] = "${{ always() }}"
        self.put(self.document)
        self.assertNotEqual(self.detail("action-condition", before), self.detail("action-condition"))
        self.assertNotEqual(self.detail("action-context", before), self.detail("action-context"))

    def test_removed_condition_is_bound_explicitly(self):
        before = self.observe()
        del self.step["if"]
        self.put(self.document)
        self.assertEqual(len(self.detail("action-condition")), 1)
        self.assertNotEqual(self.detail("action-condition", before), self.detail("action-condition"))

    def test_changed_upstream_reference_is_detected(self):
        before = self.observe()
        self.step["with"]["subject-digest"] = "${{ steps.other.outputs.digest }}"
        self.put(self.document)
        self.assertNotEqual(self.detail("action-upstream-output", before), self.detail("action-upstream-output"))

    def test_bracket_and_condition_output_references_are_observed(self):
        self.step["with"]["subject-digest"] = "${{ steps['image'].outputs['digest'] }}"
        self.step["if"] = "${{ steps.check.outputs.ready == 'true' }}"
        self.put(self.document)
        self.assertGreaterEqual(len(self.detail("action-upstream-output")), 2)

    def test_duplicate_action_instances_keep_separate_subjects(self):
        self.document["jobs"]["build"]["steps"].append(deepcopy(self.step))
        self.put(self.document)
        result = self.observe()
        self.assertEqual(len({row["subject_id"] for row in result[0]}), 2)
        self.assertEqual(sum(row["kind"] == "action-reference" for row in result[0]), 2)

    def test_reusable_workflow_uses_its_existing_caller_subject(self):
        self.document["jobs"] = {"reuse": {"uses": "example/project/.github/workflows/build.yml@main", "with": {"upload": False}}}
        self.put(self.document)
        result = self.observe()
        self.assertEqual(sum(row["kind"] == "action-reference" for row in result[0]), 1)
        self.assertIn("action-implementation-unresolved", self.codes(result))

    def test_local_docker_and_expression_refs_stay_unsupported(self):
        for reference in ("./actions/local", "docker://example/image@sha256:" + "a" * 64, "${{ inputs.action }}"):
            with self.subTest(reference=reference):
                self.step["uses"] = reference
                self.put(self.document)
                self.assertIn("action-reference-unsupported", self.codes())
                self.assertIn("action-implementation-unresolved", self.codes())

    def test_malformed_refs_produce_safe_fixed_findings(self):
        for reference in (None, 3, [], "", "../escape", "example/action/../escape@v1", "example/action", "example/action@bad ref"):
            with self.subTest(reference=reference):
                self.step["uses"] = reference
                self.put(self.document)
                self.assertIn("action-reference-invalid", self.codes())

    def test_malformed_input_shapes_stay_explicit(self):
        for inputs in (None, "unsafe-command", ["input"], {"input": None}, {"input": ["nested"]}, {"": False}):
            with self.subTest(inputs=inputs):
                self.step["with"] = inputs
                self.put(self.document)
                self.assertIn("action-input-shape-invalid", self.codes())

    def test_simultaneous_run_and_uses_cannot_claim_valid_shape(self):
        self.step["run"] = "echo invalid"
        self.put(self.document)
        self.assertIn("action-shape-invalid", self.codes())

    def test_sensitive_input_names_values_and_context_are_never_echoed(self):
        marker = "sensitive-user-supplied-marker"
        self.step["with"][marker] = marker + "${{ secrets.DO_NOT_ECHO }}"
        self.document["env"][marker] = marker
        self.put(self.document)
        encoded = json.dumps(self.observe())
        self.assertNotIn(marker, encoded)
        self.assertNotIn("DO_NOT_ECHO", encoded)
        self.assertNotIn("example/action", encoded)
        self.assertNotIn("authorized", encoded)

    def test_stale_graph_rejects_changed_workflow_bytes(self):
        graph = discover_callers(self.root, self.workflow)
        self.step["with"]["upload"] = True
        self.put(self.document)
        with self.assertRaisesRegex(SourceFailure, "^action-source-stale$"):
            self.observe(graph)

    def test_removed_action_subject_is_not_silently_skipped(self):
        graph = discover_callers(self.root, self.workflow)
        graph["nodes"] = [node for node in graph["nodes"] if node["kind"] != "workflow-step"]
        with self.assertRaisesRegex(SourceFailure, "^action-subject-missing$"):
            self.observe(graph)

    def test_tampered_action_detail_digest_is_rejected(self):
        graph = discover_callers(self.root, self.workflow)
        next(node for node in graph["nodes"] if node["kind"] == "workflow-step")["detail_digest"] = digest(b"forged")
        with self.assertRaisesRegex(SourceFailure, "^action-source-stale$"):
            self.observe(graph)

    def test_graph_for_different_workflow_is_rejected(self):
        graph = discover_callers(self.root, self.workflow)
        graph["entrypoint"]["path"] = ".github/workflows/different.yml"
        with self.assertRaisesRegex(SourceFailure, "^action-source-stale$"):
            self.observe(graph)

    def test_root_resolution_errors_produce_only_fixed_diagnostic(self):
        graph = discover_callers(self.root, self.workflow)
        with patch.object(Path, "resolve", side_effect=OSError("PRIVATE_PATH_SENTINEL")):
            with self.assertRaisesRegex(SourceFailure, "^action-source-invalid$"):
                self.observe(graph)

    def test_duplicate_yaml_keys_aliases_and_tags_are_not_accepted(self):
        graph = discover_callers(self.root, self.workflow)
        for raw in ("jobs: {}\njobs: {}\n", "jobs: &shared {}\ncopy: *shared\n", "jobs: !Ref malicious\n"):
            with self.subTest(raw=raw):
                self.put(raw)
                with self.assertRaisesRegex(SourceFailure, "^action-source-invalid$"):
                    self.observe(graph)

    def test_symlink_workflow_and_root_are_rejected(self):
        graph = discover_callers(self.root, self.workflow)
        target = self.root / "actual.yml"
        target.write_text(json.dumps(self.document))
        workflow = self.root / self.workflow
        workflow.unlink()
        workflow.symlink_to(target)
        with self.assertRaisesRegex(SourceFailure, "^action-source-invalid$"):
            self.observe(graph)
        with tempfile.TemporaryDirectory(prefix="action-root-parent-") as tmp:
            alias = Path(tmp) / "alias"
            alias.symlink_to(self.root, target_is_directory=True)
            with self.assertRaisesRegex(SourceFailure, "^action-source-invalid$"):
                observe_actions(alias, self.workflow, graph)

    def test_excess_inputs_and_observation_limit_fail_closed(self):
        with patch("action_observations.MAX_INPUTS", 1):
            self.assertIn("action-limit-exceeded", self.codes())
        with patch("action_observations.MAX_ACTION_OBSERVATIONS", 1):
            with self.assertRaisesRegex(SourceFailure, "^action-limit-exceeded$"):
                self.observe()

    def test_workflow_without_actions_has_empty_action_surface(self):
        self.document["jobs"]["build"]["steps"] = [{"run": "echo fixture"}]
        self.put(self.document)
        self.assertEqual(self.observe(), ([], []))


if __name__ == "__main__":
    unittest.main()
