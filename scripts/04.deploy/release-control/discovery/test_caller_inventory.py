#!/usr/bin/env python3
"""Positive and adversarial tests for the bounded caller graph collector."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.caller-inventory-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify caller topology, lifecycle edges, binding freshness and conservative source boundaries.
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
from caller_inventory import canonical, commands, digest, discover_callers


class CallerInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="caller-inventory-test-")
        self.root = Path(self.temp.name)
        self.workflow = ".github/workflows/staging.yml"
        self.put("package.json", {"scripts": {"check": "bash scripts/check.sh"}})
        self.put("scripts/check.sh", "#!/usr/bin/env bash\nset -euo pipefail\necho ready\n")
        self.workflow_document = {"name": "safe-fixture", "jobs": {"build": {"runs-on": "ubuntu-latest", "steps": [{"run": "npm run check"}]}}}
        self.put(self.workflow, self.workflow_document)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, relative, value):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value))
        return target

    def graph(self):
        return discover_callers(self.root, self.workflow)

    def codes(self, graph=None):
        return {entry["code"] for entry in (graph or self.graph())["findings"]}

    def workflow_run(self, value):
        self.workflow_document["jobs"]["build"]["steps"] = [{"run": value}]
        self.put(self.workflow, self.workflow_document)

    def assert_integrity(self, graph):
        ids = {node["id"] for node in graph["nodes"]}
        self.assertEqual(len(ids), len(graph["nodes"]))
        source_ids = {source["id"] for source in graph["sources"]}
        self.assertTrue(all(node["source_id"] in source_ids for node in graph["nodes"]))
        self.assertTrue(all(edge["caller_id"] in ids and edge["callee_id"] in ids for edge in graph["edges"]))
        self.assertTrue(all(finding["subject_id"] in ids for finding in graph["findings"]))
        reached = {graph["entrypoint"]["node_id"]}
        previous = set()
        while previous != reached:
            previous = set(reached)
            reached.update(edge["callee_id"] for edge in graph["edges"] if edge["caller_id"] in reached)
        self.assertEqual(ids, reached)
        self.assertEqual(graph["graph_digest"], digest(canonical({k: v for k, v in graph.items() if k != "graph_digest"})))

    def test_literal_fanout_is_deterministic_fresh_and_connected(self):
        first = self.graph()
        self.assertEqual(first, self.graph())
        self.assert_integrity(first)
        self.assertEqual({node["kind"] for node in first["nodes"]}, {"workflow", "workflow-step", "package-command", "script-entrypoint", "tool-command"})
        self.assertEqual(self.codes(first), {"caller-tool-behavior-unresolved"})
        self.assertEqual({source["path"] for source in first["sources"]}, {self.workflow, "package.json", "scripts/check.sh"})

    def test_lifecycle_hooks_are_explicit_pre_and_post_edges(self):
        self.put("package.json", {"scripts": {"precheck": "echo before", "check": "bash scripts/check.sh", "postcheck": "echo after"}})
        graph = self.graph()
        self.assertEqual({edge["kind"] for edge in graph["edges"]}, {"invokes", "npm-pre", "npm-post"})
        self.assertEqual(sum(node["kind"] == "package-command" for node in graph["nodes"]), 3)
        self.assert_integrity(graph)

    def test_automatic_hook_does_not_invent_recursive_preprehook(self):
        self.put("package.json", {"scripts": {"preprecheck": "echo unused", "precheck": "echo before", "check": "echo ready"}})
        graph = self.graph()
        self.assertEqual(sum(node["kind"] == "package-command" for node in graph["nodes"]), 2)

    def test_explicit_hook_invocation_gets_its_own_lifecycle(self):
        self.put("package.json", {"scripts": {"check": "npm run precheck", "precheck": "echo before", "preprecheck": "echo earlier"}})
        graph = self.graph()
        self.assertEqual(sum(node["kind"] == "package-command" for node in graph["nodes"]), 3)
        self.assert_integrity(graph)

    def test_new_lifecycle_hook_changes_graph_without_selected_list(self):
        before = self.graph()
        self.put("package.json", {"scripts": {"check": "bash scripts/check.sh", "postcheck": "node scripts/hidden.mjs"}})
        self.put("scripts/hidden.mjs", "console.log('fixture');")
        after = self.graph()
        self.assertNotEqual(before["graph_digest"], after["graph_digest"])
        self.assertIn("scripts/hidden.mjs", {source["path"] for source in after["sources"]})

    def test_new_workflow_step_is_discovered_independently(self):
        before = self.graph()
        self.workflow_document["jobs"]["build"]["steps"].append({"run": "echo hidden"})
        self.put(self.workflow, self.workflow_document)
        after = self.graph()
        self.assertNotEqual(before["graph_digest"], after["graph_digest"])
        self.assertEqual(sum(node["kind"] == "workflow-step" for node in after["nodes"]), 2)

    def test_forwarded_package_arguments_remain_explicitly_unresolved(self):
        self.workflow_run("npm run check -- --option literal")
        self.assertIn("caller-arguments-unsupported", self.codes())

    def test_package_and_script_cycles_fail_closed(self):
        self.put("package.json", {"scripts": {"check": "npm run other", "other": "npm run check"}})
        self.assertIn("caller-cycle", self.codes())
        self.put("package.json", {"scripts": {"check": "bash scripts/check.sh"}})
        self.put("scripts/check.sh", "bash scripts/check.sh")
        graph = self.graph()
        self.assertIn("caller-cycle", self.codes(graph))
        self.assert_integrity(graph)

    def test_referenced_tests_are_bound_despite_directory_name(self):
        self.put("scripts/check.sh", "bash tests/helper.sh")
        self.put("tests/helper.sh", "echo test-helper")
        graph = self.graph()
        self.assertIn("tests/helper.sh", {source["path"] for source in graph["sources"]})
        self.assert_integrity(graph)

    def test_terminal_target_byte_changes_invalidate_graph(self):
        before = self.graph()
        self.put("scripts/check.sh", "echo changed")
        after = self.graph()
        self.assertNotEqual(before["graph_digest"], after["graph_digest"])
        before_node = next(node for node in before["nodes"] if node["kind"] == "script-entrypoint")
        after_node = next(node for node in after["nodes"] if node["kind"] == "script-entrypoint")
        self.assertEqual(before_node["id"], after_node["id"])
        self.assertNotEqual(before_node["detail_digest"], after_node["detail_digest"])

    def test_conditions_and_inputs_change_bound_step_even_if_calls_same(self):
        before = self.graph()
        self.workflow_document["jobs"]["build"]["steps"][0]["if"] = "always()"
        self.put(self.workflow, self.workflow_document)
        self.assertNotEqual(before["graph_digest"], self.graph()["graph_digest"])

    def test_dynamic_whole_block_does_not_emit_partial_callees(self):
        for tail in ["echo $DYNAMIC", "echo ok | bash", "eval target", "cd scripts", "npm run check --workspace other", "node -e code", "echo *.sh", "echo `whoami`", "bash scripts/check.sh > out"]:
            with self.subTest(tail=tail):
                self.workflow_run("npm run check\n" + tail)
                graph = self.graph()
                self.assertIn("caller-opaque-command", self.codes(graph))
                self.assertEqual({node["kind"] for node in graph["nodes"]}, {"workflow", "workflow-step"})

    def test_strict_grammar_rejects_broken_and_operator_variants(self):
        for value in ["echo x &&", "&& echo x", "echo x && && echo y", "echo x;echo y", "echo x & echo y", "echo 'broken", "A=x echo y", "./scripts/check.sh", "npm --workspace x run check", "bash ../outside.sh"]:
            with self.subTest(value=value):
                self.assertIsNone(commands(value))
        self.assertEqual(len(commands("echo first && echo second\necho third")), 3)

    def test_context_mutating_builtins_cannot_redirect_literal_targets(self):
        self.put("apps/child/scripts/check.sh", "echo alternate-target")
        for prefix in ["pushd apps/child", "popd", "hash -p scripts/hidden bash", "alias bash=hidden", "enable -n echo", "declare PATH=hidden", "trap hidden EXIT", "read COMMAND", "getopts a choice", "shopt -s expand_aliases"]:
            with self.subTest(prefix=prefix):
                self.workflow_run(prefix + " && bash scripts/check.sh")
                graph = self.graph()
                self.assertIn("caller-opaque-command", self.codes(graph))
                self.assertEqual({node["kind"] for node in graph["nodes"]}, {"workflow", "workflow-step"})
                self.assertEqual({source["path"] for source in graph["sources"]}, {self.workflow})

    def test_complex_shell_body_does_not_hide_opaque_behavior(self):
        self.put("scripts/check.sh", "if test -f marker; then bash scripts/hidden.sh; fi")
        self.assertIn("caller-script-body-unresolved", self.codes())

    def test_canonical_python_dispatch_wrapper_binds_target(self):
        self.put("scripts/check.sh", '#!/usr/bin/env bash\nset -euo pipefail\nROOT="$(git rev-parse --show-toplevel)"\ncd "$ROOT"\nexec python3 "$ROOT/scripts/worker.py" "$@"\n')
        self.put("scripts/worker.py", "print('fixture')")
        graph = self.graph()
        self.assertEqual(self.codes(graph), {"caller-script-body-unresolved"})
        self.assertIn("scripts/worker.py", {source["path"] for source in graph["sources"]})
        self.assert_integrity(graph)

    def test_non_shell_interpreter_does_not_parse_shell_suffix(self):
        self.workflow_run("node scripts/check.sh")
        graph = self.graph()
        self.assertIn("caller-script-body-unresolved", self.codes(graph))
        self.assertNotIn("tool-command", {node["kind"] for node in graph["nodes"]})

    def test_unknown_workflow_actions_and_reusable_jobs_remain_unresolved(self):
        self.workflow_document["jobs"]["build"]["steps"].append({"uses": "provider/action@revision", "with": {"token": "never-output-this"}})
        self.workflow_document["jobs"]["reuse"] = {"uses": "provider/workflow@revision"}
        self.put(self.workflow, self.workflow_document)
        graph = self.graph()
        self.assertIn("caller-workflow-action-unresolved", self.codes(graph))
        self.assertEqual(sum(node["kind"] == "workflow-step" for node in graph["nodes"]), 3)
        self.assertNotIn("never-output-this", json.dumps(graph))
        self.assert_integrity(graph)

    def test_custom_shell_cwd_and_invocation_environment_block_resolution(self):
        for field, value in [("shell", "bash"), ("working-directory", "scripts"), ("env", {"PATH": "hidden"}), ("env", {"GIT_WORK_TREE": "elsewhere"}), ("env", {"HOME": "elsewhere"})]:
            with self.subTest(field=field):
                self.workflow_run("npm run check")
                self.workflow_document["jobs"]["build"]["steps"][0][field] = value
                self.put(self.workflow, self.workflow_document)
                graph = self.graph()
                self.assertIn("caller-context-unsupported", self.codes(graph))
                self.assertEqual({node["kind"] for node in graph["nodes"]}, {"workflow", "workflow-step"})

    def test_inherited_workflow_and_job_context_cannot_be_ignored(self):
        for location in ("workflow", "job"):
            with self.subTest(location=location):
                value = deepcopy(self.workflow_document)
                target = value if location == "workflow" else value["jobs"]["build"]
                target["defaults"] = {"run": {"working-directory": "elsewhere"}}
                self.put(self.workflow, value)
                self.assertIn("caller-context-unsupported", self.codes())

    def test_npm_configuration_is_hashed_and_blocks(self):
        self.put(".npmrc", "script-shell=secret-command-never-output\n")
        graph = self.graph()
        self.assertIn("caller-context-unsupported", self.codes(graph))
        self.assertIn(".npmrc", {source["path"] for source in graph["sources"]})
        self.assertNotIn("secret-command-never-output", json.dumps(graph))
        package_node = next(node for node in graph["nodes"] if node["kind"] == "package-command")
        self.assertIn("caller-context-unsupported", package_node["issues"])
        self.assertNotIn("script-entrypoint", {node["kind"] for node in graph["nodes"]})
        self.assert_integrity(graph)

    def test_symlink_target_is_not_followed(self):
        target = self.root / "scripts/check.sh"
        target.unlink()
        target.symlink_to("/etc/passwd")
        graph = self.graph()
        self.assertIn("caller-path-unreadable", self.codes(graph))
        source = next(source for source in graph["sources"] if source["path"] == "scripts/check.sh")
        self.assertEqual(source["digest"], digest(b""))

    def test_missing_target_is_not_empty_success(self):
        (self.root / "scripts/check.sh").unlink()
        self.assertIn("caller-path-missing", self.codes())

    def test_explicit_outside_scope_source_is_hashed_but_analysis_blocks(self):
        self.workflow_run("bash private/credential.sh")
        self.put("private/credential.sh", "echo highly-secret")
        graph = self.graph()
        self.assertIn("caller-path-unsupported", self.codes(graph))
        source = next(source for source in graph["sources"] if source["path"] == "private/credential.sh")
        self.assertEqual(source["digest"], digest(b"echo highly-secret"))
        self.put("private/credential.sh", "echo changed-secret")
        self.assertNotEqual(graph["graph_digest"], self.graph()["graph_digest"])

    def test_duplicate_manifest_keys_and_workflow_aliases_block(self):
        self.put("package.json", '{"scripts":{},"scripts":{}}')
        self.assertIn("caller-source-parse-failed", self.codes())
        self.put(self.workflow, 'jobs: &j {}\nother: *j\n')
        self.assertIn("caller-source-parse-failed", self.codes())

    def test_workflow_yaml_custom_tags_are_rejected(self):
        self.put(self.workflow, 'jobs: {build: {steps: [{run: echo ready}], extra: !Ref invalid}}')
        self.assertIn("caller-source-parse-failed", self.codes())

    def test_unsafe_entrypoint_and_root_are_normalized(self):
        for path in ("../outside.yml", "/tmp/outside.yml", ".github/workflows/../../outside.yml", "not-a-workflow.yml"):
            with self.subTest(path=path):
                graph = discover_callers(self.root, path)
                self.assertEqual(graph["entrypoint"]["path"], "unavailable")
                self.assertIn("caller-entrypoint-invalid", self.codes(graph))
                self.assert_integrity(graph)
        graph = discover_callers(self.root / "missing", self.workflow)
        self.assertIn("caller-root-invalid", self.codes(graph))

    def test_graph_limit_is_safe_connected_failure(self):
        for limit in (2, 3, 4):
            with self.subTest(limit=limit):
                with patch("caller_inventory.MAX_GRAPH_NODES", limit):
                    graph = self.graph()
                self.assertIn("caller-limit-exceeded", self.codes(graph))
                self.assert_integrity(graph)

    def test_oversized_source_is_rejected_before_content_read(self):
        with patch("caller_inventory.MAX_BYTES", 10):
            graph = self.graph()
        self.assertIn("caller-limit-exceeded", self.codes(graph))

    def test_collector_does_not_execute_source(self):
        marker = self.root / "never-created"
        self.put("scripts/check.sh", "touch " + str(marker))
        self.graph()
        self.assertFalse(marker.exists())

    def test_commands_and_values_are_absent_from_safe_graph(self):
        self.workflow_run('echo "value-that-must-never-leak"')
        graph = self.graph()
        serialized = json.dumps(graph)
        self.assertNotIn("value-that-must-never-leak", serialized)
        self.assertNotIn("echo", serialized)
        self.assertNotIn("safe-fixture", serialized)


if __name__ == "__main__":
    unittest.main()
