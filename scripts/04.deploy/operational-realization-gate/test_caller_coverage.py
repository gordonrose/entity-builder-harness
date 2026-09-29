#!/usr/bin/env python3
"""Focused caller-accounting mutations; source review never grants qualification."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-caller-coverage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify complete caller accounting and retain every unresolved execution obligation.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
sys.path.insert(0, str(DIRECTORY))
sys.path.insert(0, str(ROOT / "scripts/04.deploy/release-control/discovery"))
import caller_coverage as coverage
import caller_inventory as discovery
import release_compiler as release

WORKFLOW = ".github/workflows/staging.yml"
SENTINEL = "SENTINEL-SENSITIVE-DO-NOT-PRINT"
UNKNOWN = "sha256:" + "a" * 64


class CallerCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="release-caller-coverage-")
        self.addCleanup(self.temporary.cleanup)
        self.source_root = Path(self.temporary.name) / "source"
        self.source_root.mkdir()
        self.write("package.json", json.dumps({
            "name": "caller-fixture", "private": True,
            "scripts": {
                "predeploy:staging": "bash scripts/04.deploy/check.sh",
                "deploy:staging": "bash scripts/04.deploy/deploy.sh",
                "postdeploy:staging": "bash scripts/04.deploy/verify.sh",
            },
        }))
        self.write(WORKFLOW, """name: Staging caller fixture
on: workflow_dispatch
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: npm run deploy:staging
""")
        self.write("scripts/04.deploy/check.sh", "#!/usr/bin/env bash\necho check\n")
        self.write("scripts/04.deploy/deploy.sh", "#!/usr/bin/env bash\nbash tests/helper.sh\n")
        self.write("scripts/04.deploy/verify.sh", "#!/usr/bin/env bash\necho verify\n")
        # A production caller into tests remains in the caller graph.
        self.write("tests/helper.sh", "#!/usr/bin/env bash\necho fixture\n")
        self.graph = self.discover()
        self.review = coverage.make_review(self.graph, target_id="sandbox/delivery")
        self.review_all(self.review)

    def write(self, relative, value):
        path = self.source_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def discover(self):
        return discovery.discover_callers(self.source_root, WORKFLOW)

    @staticmethod
    def review_all(review):
        for index, binding in enumerate(review["bindings"]):
            binding["owner"] = "deployment-team"
            binding["operation_id"] = f"caller-operation-{index}"
            binding["operation_profile"] = "finite-job"
            binding["review_status"] = "reviewed"

    def compile(self, graph=None, review=None):
        return coverage.compile_callers(
            self.graph if graph is None else graph,
            self.review if review is None else review,
        )

    def assert_incomplete(self, graph=None, review=None):
        try:
            result = self.compile(graph, review)
        except release.ReleaseFailure as error:
            self.assertTrue(error.code)
            self.assertNotIn(SENTINEL, str(error))
            return None
        self.assertEqual(result["accounting_verdict"], "incomplete")
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertIs(result["authorized"], False)
        self.assertTrue(result["findings"])
        self.assertNotIn(SENTINEL, json.dumps(result))
        return result

    def command(self, *arguments):
        return subprocess.run(
            ["bash", str(DIRECTORY / "script.sh"), "--callers", "--source-root",
             str(self.source_root), "--workflow", WORKFLOW, *map(str, arguments)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )

    def review_file(self, document=None):
        path = Path(self.temporary.name) / "caller-review.json"
        path.write_text(json.dumps(self.review if document is None else document))
        return path

    def test_generated_review_is_pending_and_covers_all_nodes_and_edges(self):
        review = coverage.make_review(self.graph, target_id="sandbox/delivery")
        self.assertEqual(review["schema"], "source-caller-review/v1")
        self.assertEqual(review["target_id"], "sandbox/delivery")
        self.assertEqual(review["graph_digest"], self.graph["graph_digest"])
        self.assertEqual({item["node_id"] for item in review["bindings"]},
                         {item["id"] for item in self.graph["nodes"]})
        self.assertEqual(set(review["edge_ids"]), {item["id"] for item in self.graph["edges"]})
        self.assertTrue(review["bindings"])
        self.assertTrue(all(item["review_status"] == "pending" for item in review["bindings"]))
        self.assertTrue(all(item["operation_profile"] == "unclassified" for item in review["bindings"]))
        self.assert_incomplete(review=review)

    def test_complete_source_accounting_remains_unqualified_and_unauthorized(self):
        result = self.compile()
        self.assertEqual(result["schema"], "source-caller-result/v1")
        self.assertEqual(result["accounting_verdict"], "accounted")
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertIs(result["authorized"], False)
        self.assertTrue(result["obligations"])
        self.assertEqual(result, self.compile())

    def test_compiler_does_not_mutate_graph_or_review(self):
        before = copy.deepcopy((self.graph, self.review))
        self.compile()
        self.assertEqual(before, (self.graph, self.review))

    def test_opaque_source_findings_are_retained_as_obligations(self):
        codes = {item["code"] for item in self.graph["findings"]}
        codes.update(code for item in self.graph["nodes"] for code in item["issues"])
        self.assertTrue(codes)
        result = self.compile()
        encoded = json.dumps(result["source_findings"])
        for code in codes:
            with self.subTest(code=code):
                self.assertIn(code, encoded)
        unresolved_subjects = {item["subject_id"] for item in result["source_findings"]}
        for obligation in result["obligations"]:
            if obligation["subject_id"] in unresolved_subjects:
                self.assertEqual(obligation["source_closure"], "unresolved")
            self.assertEqual(obligation["qualification"], "pending")
        self.assertEqual(result["qualification_verdict"], "blocked")

    def test_stale_review_and_tampered_graph_digest_are_rejected(self):
        stale = copy.deepcopy(self.review)
        stale["graph_digest"] = UNKNOWN
        self.assert_incomplete(review=stale)
        tampered = copy.deepcopy(self.graph)
        tampered["graph_digest"] = UNKNOWN
        self.assert_incomplete(graph=tampered)

    def test_missing_binding_is_not_hidden_by_complete_edge_list(self):
        self.review["bindings"].pop()
        self.assert_incomplete()

    def test_duplicate_binding_is_rejected(self):
        self.review["bindings"].append(copy.deepcopy(self.review["bindings"][0]))
        self.assert_incomplete()

    def test_distinct_callers_cannot_collapse_into_one_operation(self):
        self.assertGreater(len(self.review["bindings"]), 1)
        self.review["bindings"][1]["operation_id"] = self.review["bindings"][0]["operation_id"]
        self.assert_incomplete()

    def test_unknown_node_binding_is_rejected(self):
        self.review["bindings"][0]["node_id"] = UNKNOWN
        self.assert_incomplete()

    def test_missing_duplicate_and_unknown_edges_are_rejected(self):
        self.assertTrue(self.review["edge_ids"])
        for mutation in ("missing", "duplicate", "unknown"):
            with self.subTest(mutation=mutation):
                review = copy.deepcopy(self.review)
                if mutation == "missing":
                    review["edge_ids"].pop()
                elif mutation == "duplicate":
                    review["edge_ids"].append(review["edge_ids"][0])
                else:
                    review["edge_ids"].append(UNKNOWN)
                self.assert_incomplete(review=review)

    def test_one_pending_or_unclassified_node_prevents_accounting(self):
        for field, value in (("review_status", "pending"), ("operation_profile", "unclassified")):
            with self.subTest(field=field):
                review = copy.deepcopy(self.review)
                review["bindings"][0][field] = value
                self.assert_incomplete(review=review)

    def test_unknown_document_versions_are_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph["schema"] = "caller-inventory/v99"
        self.assert_incomplete(graph=graph)
        review = copy.deepcopy(self.review)
        review["schema"] = "source-caller-review/v99"
        self.assert_incomplete(review=review)

    def test_graph_rejects_unknown_sources_edges_findings_and_detached_nodes(self):
        for mutation in ("source", "edge", "finding", "detached-node"):
            with self.subTest(mutation=mutation):
                graph = copy.deepcopy(self.graph)
                if mutation == "source":
                    graph["nodes"][0]["source_id"] = UNKNOWN
                elif mutation == "edge":
                    graph["edges"][0]["callee_id"] = UNKNOWN
                elif mutation == "finding":
                    graph["findings"].append({"code": "caller-source-unresolved", "subject_id": UNKNOWN})
                else:
                    node = copy.deepcopy(graph["nodes"][0])
                    node["id"] = UNKNOWN
                    graph["nodes"].append(node)
                graph["graph_digest"] = release.digest_document(
                    {key: value for key, value in graph.items() if key != "graph_digest"})
                self.assert_incomplete(graph=graph)

    def test_graph_rejects_unsafe_source_paths_without_echoing_them(self):
        for path in ("/tmp/" + SENTINEL, "../" + SENTINEL, "safe/../../" + SENTINEL):
            with self.subTest(path=path):
                graph = copy.deepcopy(self.graph)
                graph["sources"][0]["path"] = path
                graph["graph_digest"] = release.digest_document(
                    {key: value for key, value in graph.items() if key != "graph_digest"})
                self.assert_incomplete(graph=graph)

    def test_owner_profile_and_target_changes_invalidate_accounting_identity(self):
        original = self.compile()["accounting_digest"]
        for field, value in (("owner", "other-team"), ("operation_profile", "service-rollout"),
                             ("target_id", "sandbox/other")):
            with self.subTest(field=field):
                review = copy.deepcopy(self.review)
                if field == "target_id":
                    review[field] = value
                else:
                    review["bindings"][0][field] = value
                result = self.compile(review=review)
                self.assertEqual(result["accounting_verdict"], "accounted")
                self.assertEqual(result["qualification_verdict"], "blocked")
                self.assertNotEqual(result["accounting_digest"], original)

    def test_unsafe_fields_and_runtime_claims_are_rejected(self):
        for key, value in (("command", SENTINEL), ("authorized", True),
                           ("qualification_verdict", "passed")):
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                review[key] = value
                self.assert_incomplete(review=review)
        review = copy.deepcopy(self.review)
        review["bindings"][0]["owner"] = "https://example.invalid/" + SENTINEL
        self.assert_incomplete(review=review)

    def test_invalid_operation_profile_cannot_claim_runtime_authority(self):
        self.review["bindings"][0]["operation_profile"] = "qualified-production-release"
        self.assert_incomplete()

    def test_production_call_into_test_directory_is_still_bound(self):
        source = next(item for item in self.graph["sources"] if item["path"] == "tests/helper.sh")
        nodes = [item for item in self.graph["nodes"] if item["source_id"] == source["id"]]
        self.assertTrue(nodes)
        node_ids = {item["id"] for item in nodes}
        self.assertTrue(node_ids <= {item["node_id"] for item in self.review["bindings"]})
        self.review["bindings"] = [item for item in self.review["bindings"] if item["node_id"] not in node_ids]
        self.assert_incomplete()

    def test_source_content_change_invalidates_prior_review(self):
        self.write("tests/helper.sh", "#!/usr/bin/env bash\necho changed\n")
        changed = self.discover()
        self.assertNotEqual(changed["graph_digest"], self.graph["graph_digest"])
        self.assert_incomplete(graph=changed)

    def test_new_reachable_caller_cannot_be_hidden_by_rebinding_digest(self):
        self.write("scripts/04.deploy/deploy.sh", "#!/usr/bin/env bash\nbash tests/helper.sh\nbash scripts/04.deploy/new-job.sh\n")
        self.write("scripts/04.deploy/new-job.sh", "#!/usr/bin/env bash\necho new-job\n")
        changed = self.discover()
        self.assertGreater(len(changed["nodes"]), len(self.graph["nodes"]))
        review = copy.deepcopy(self.review)
        review["graph_digest"] = changed["graph_digest"]
        self.assert_incomplete(graph=changed, review=review)

    def test_omitted_npm_pre_and_post_hooks_prevent_accounting(self):
        for path in ("scripts/04.deploy/check.sh", "scripts/04.deploy/verify.sh"):
            with self.subTest(path=path):
                source = next(item for item in self.graph["sources"] if item["path"] == path)
                node_ids = {item["id"] for item in self.graph["nodes"] if item["source_id"] == source["id"]}
                self.assertTrue(node_ids)
                review = copy.deepcopy(self.review)
                review["bindings"] = [item for item in review["bindings"] if item["node_id"] not in node_ids]
                self.assert_incomplete(review=review)

    def test_nonliteral_shell_behavior_cannot_become_qualified(self):
        self.write("scripts/04.deploy/deploy.sh", '#!/usr/bin/env bash\n"${COMMAND}"\n')
        graph = self.discover()
        review = coverage.make_review(graph, target_id="sandbox/delivery")
        self.review_all(review)
        result = self.compile(graph, review)
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertIs(result["authorized"], False)
        self.assertTrue(result["obligations"])

    def test_cli_template_requires_review_and_contains_no_source_literals(self):
        completed = self.command("--review-template", "--json")
        self.assertIn(completed.returncode, (0, 1), completed.stderr)
        review = json.loads(completed.stdout)
        self.assertEqual(review["schema"], "source-caller-review/v1")
        self.assertTrue(all(item["review_status"] == "pending" for item in review["bindings"]))
        self.assertNotIn("npm run", completed.stdout)
        self.assertNotIn("echo fixture", completed.stdout)

    def test_cli_accounting_recollects_and_stale_review_fails(self):
        review_file = self.review_file()
        completed = self.command("--caller-review", review_file, "--json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["accounting_verdict"], "accounted")
        self.assertEqual(result["qualification_verdict"], "blocked")
        self.assertIs(result["authorized"], False)
        self.write("tests/helper.sh", "#!/usr/bin/env bash\necho changed-again\n")
        changed = self.command("--caller-review", review_file, "--json")
        self.assertEqual(changed.returncode, 1, changed.stdout + changed.stderr)
        self.assertEqual(json.loads(changed.stdout)["accounting_verdict"], "incomplete")

    def test_cli_duplicate_flags_and_malformed_inputs_return_safe_diagnostics(self):
        duplicate = self.command("--caller-review", self.review_file(), "--workflow", WORKFLOW, "--json")
        self.assertNotEqual(duplicate.returncode, 0)
        path = self.review_file()
        path.write_text('{"schema":"source-caller-review/v1","schema":"' + SENTINEL + '"}')
        malformed = self.command("--caller-review", path, "--json")
        self.assertNotEqual(malformed.returncode, 0)
        self.assertNotIn(SENTINEL, malformed.stdout + malformed.stderr)
        self.assertNotIn("Traceback", malformed.stdout + malformed.stderr)


if __name__ == "__main__":
    unittest.main()
