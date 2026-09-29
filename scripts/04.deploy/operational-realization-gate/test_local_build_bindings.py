#!/usr/bin/env python3
"""Reject runtime evidence detached from its compiler, source or selected tests."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.local-build-bindings
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Check runtime receipt identity, exact selected tests and compiler and generator bindings.
#   portability: {class: internal, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import copy
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_build_contracts as contracts
import release_compiler as release

HASH = "sha256:" + "a" * 64
OTHER = "sha256:" + "b" * 64
SERVER = "platform/server/tsconfig.runtime-test.json"
PRODUCT = "products/kanbien-platform/tsconfig.runtime-test.json"
IMAGE = "platform/server/tsconfig.image.json"


def fingerprint(path, digest=HASH, size=1):
    return {"path": path, "digest": digest, "bytes": size}


def seal(value, field):
    value[field] = release.digest_document({key: item for key, item in value.items() if key != field})
    return value


def reseal(value):
    for build in value["builds"]:
        seal(build["observation"], "observation_digest")
        if build["runtime"] is not None:
            seal(build["runtime"], "receipt_digest")
    return seal(value, "result_digest")


def fixture(configuration=SERVER):
    output, kind, generator, test_dir = contracts.RUNTIME_LAYOUTS[configuration]
    compiled = [fingerprint("src/index.js")]
    selected = []
    if test_dir:
        selected = [test_dir + "/a-runtime.test.js", test_dir + "/b-runtime.test.js"]
        compiled.extend(fingerprint(path) for path in selected)
        compiled.append(fingerprint(test_dir + "/nested/c-runtime.test.js"))
    compiled.sort(key=lambda row: row["path"])
    artifacts = sorted(compiled + [fingerprint("node_modules/@fixture/core/index.js"),
                                  fingerprint("node_modules/@fixture/core/package.json")],
                       key=lambda row: row["path"])
    observed = {"schema": "local-typescript-observation/v1", "configuration": configuration,
                "node_version": "22.23.3", "typescript_version": "5.9.3", "verdict": "passed",
                "no_emit": False, "emit_skipped": False,
                "inputs": [{"kind": "repository", **fingerprint(configuration)},
                           {"kind": "dependency", **fingerprint("node_modules/typescript/lib/typescript.js")}],
                "resolutions": [], "outputs": [{**row, "path": output + "/" + row["path"]} for row in compiled],
                "diagnostics": [], "findings": []}
    runtime = {"schema": "local-runtime-observation/v1", "scope": "isolated-local-runtime",
               "configuration": configuration, "kind": kind, "authorized": False,
               "qualification_verdict": "blocked", "source_inventory_digest": HASH,
               "generator": {"path": generator, "digest": HASH},
               "compiler_artifact_digest": release.digest_document(compiled),
               "dependency_tree_digest": HASH, "copied_dependency_digest": HASH,
               "artifact_files": artifacts, "selected_runtime_tests": selected,
               "executed_runner_count": int(bool(test_dir)), "returncode": 0,
               "stdout_digest": HASH, "stderr_digest": HASH}
    return reseal({"schema": "local-build-result/v1", "scope": "locked-local-build", "authorized": False,
                   "release_eligibility": "blocked", "operation_authorization": "blocked",
                   "qualification_verdict": "blocked", "source_closure": "blocked", "verdict": "passed",
                   "source_digest": HASH, "build_inventory_digest": HASH, "graph_digest": HASH,
                   "runner_digest": HASH,
                   "toolchain": {"contract_digest": HASH, "node_version": "22.23.3", "npm_version": "10.9.9",
                                 "typescript_version": "5.9.3", "lock_digest": HASH, "dependency_digest": HASH},
                   "sandbox": {"filesystem": "disposable-selected-sources", "network": "private-loopback-only",
                               "environment": "explicit-allowlist", "timeout_seconds": 180,
                               "source_checkout": "not-mounted", "authority": "none"},
                   "builds": [{"build_id": HASH, "configuration": configuration, "observation": observed,
                               "runtime": runtime, "prediction_status": "bounded",
                               "unpredicted_outputs": [], "unemitted_predictions": []}], "findings": []})


class RuntimeBindingTests(unittest.TestCase):
    def setUp(self):
        self.value = fixture()
        self.build = self.value["builds"][0]
        self.runtime = self.build["runtime"]
        self.observed = self.build["observation"]

    def reject(self, code=None, reseal_digest=True):
        if reseal_digest:
            reseal(self.value)
        if code:
            with self.assertRaisesRegex(release.ReleaseFailure, "^" + code + "$"):
                contracts.result(self.value)
        else:
            with self.assertRaises(release.ReleaseFailure):
                contracts.result(self.value)

    def test_server_compiler_and_runtime_are_bound(self):
        self.assertFalse(contracts.result(self.value)["authorized"])

    def test_product_membership_is_bound(self):
        value = contracts.result(fixture(PRODUCT))
        self.assertEqual(2, len(value["builds"][0]["runtime"]["selected_runtime_tests"]))

    def test_image_generator_does_not_claim_runtime_tests(self):
        value = contracts.result(fixture(IMAGE))
        self.assertEqual(0, value["builds"][0]["runtime"]["executed_runner_count"])

    def test_external_buildinfo_is_not_part_of_runtime_payload(self):
        self.observed["outputs"].append(fingerprint(".cache/tsconfig.tsbuildinfo"))
        contracts.result(reseal(self.value))

    def test_failed_runtime_has_explicit_failed_result(self):
        self.build["runtime"] = None
        self.value["verdict"] = "failed"
        self.value["findings"] = [{"code": "local-build-runtime-failed"}]
        contracts.result(reseal(self.value))

    def test_failed_compiler_does_not_require_runtime(self):
        self.build["runtime"] = None
        self.observed.update(verdict="failed", outputs=[], emit_skipped=True,
                             findings=[{"code": "observer-compiler-failed"}])
        self.value.update(verdict="failed", findings=[{"code": "local-build-compiler-failed"}])
        contracts.result(reseal(self.value))

    def test_missing_runtime_cannot_pass(self):
        self.build["runtime"] = None
        self.reject("local-build-runtime-missing")

    def test_missing_runtime_requires_specific_failure(self):
        self.build["runtime"] = None
        self.value.update(verdict="failed", findings=[{"code": "local-build-other-failed"}])
        self.reject("local-build-runtime-missing")

    def test_runtime_failure_finding_cannot_pass(self):
        self.value["findings"] = [{"code": "local-build-runtime-failed"}]
        self.reject("local-build-result-inconsistent")

    def test_failed_result_without_reason_rejects(self):
        self.value["verdict"] = "failed"
        self.reject("local-build-result-inconsistent")

    def test_runtime_with_failed_compiler_rejects(self):
        self.observed.update(verdict="failed", findings=[{"code": "observer-compiler-failed"}])
        self.value.update(verdict="failed", findings=[{"code": "local-build-compiler-failed"}])
        self.reject("local-build-runtime-binding-invalid")

    def test_compiler_artifact_digest_mismatch_rejects(self):
        self.runtime["compiler_artifact_digest"] = OTHER
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_changed_compiler_output_rejects(self):
        self.observed["outputs"][0]["digest"] = OTHER
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_changed_runtime_regular_bytes_rejects(self):
        next(row for row in self.runtime["artifact_files"] if row["path"] == "src/index.js")["digest"] = OTHER
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_changed_runtime_regular_size_rejects(self):
        next(row for row in self.runtime["artifact_files"] if row["path"] == "src/index.js")["bytes"] = 2
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_missing_runtime_regular_file_rejects(self):
        self.runtime["artifact_files"] = [row for row in self.runtime["artifact_files"] if row["path"] != "src/index.js"]
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_fake_runtime_regular_file_rejects(self):
        self.runtime["artifact_files"].append(fingerprint("src/fake.js"))
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_fake_runtime_test_cannot_be_added_with_matching_selection(self):
        path = "platform/server/tests/c-runtime.test.js"
        self.runtime["artifact_files"].append(fingerprint(path))
        self.runtime["selected_runtime_tests"].append(path)
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_compiler_output_outside_runtime_root_cannot_replace_payload(self):
        for row in self.observed["outputs"]:
            row["path"] = row["path"].replace(".cache/platform-server-runtime/", ".cache/other/")
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_compiler_cannot_emit_generated_dependency(self):
        path = "node_modules/@fixture/core/index.js"
        compiled = [{**row, "path": row["path"].removeprefix(".cache/platform-server-runtime/")} for row in self.observed["outputs"]]
        compiled.append(fingerprint(path))
        self.observed["outputs"].append(fingerprint(".cache/platform-server-runtime/" + path))
        self.runtime["compiler_artifact_digest"] = release.digest_document(sorted(compiled, key=lambda row: row["path"]))
        self.reject("local-build-runtime-compiler-binding-invalid")

    def test_missing_selected_test_rejects(self):
        self.runtime["selected_runtime_tests"].pop()
        self.reject("local-build-runtime-membership-invalid")

    def test_duplicate_selected_test_rejects(self):
        self.runtime["selected_runtime_tests"].append(self.runtime["selected_runtime_tests"][0])
        self.reject("local-build-runtime-membership-invalid")

    def test_nested_test_cannot_be_claimed_selected(self):
        self.runtime["selected_runtime_tests"].append("platform/server/tests/nested/c-runtime.test.js")
        self.reject("local-build-runtime-membership-invalid")

    def test_arbitrary_javascript_cannot_be_claimed_test(self):
        self.runtime["selected_runtime_tests"] = ["src/index.js"]
        self.reject("local-build-runtime-membership-invalid")

    def test_test_order_is_canonical(self):
        self.runtime["selected_runtime_tests"].reverse()
        self.reject("local-build-runtime-membership-invalid")

    def test_runner_cannot_be_labelled_image_preparation(self):
        self.runtime.update(kind="image-shim-generator", selected_runtime_tests=[], executed_runner_count=0)
        self.reject("local-build-runtime-identity-invalid")

    def test_wrong_generator_path_rejects(self):
        self.runtime["generator"]["path"] = "../../generator.mjs"
        self.reject("local-build-runtime-identity-invalid")

    def test_wrong_runtime_configuration_rejects(self):
        self.runtime["configuration"] = "untrusted/../tsconfig.json"
        self.reject("local-build-runtime-identity-invalid")

    def test_unknown_result_configuration_rejects(self):
        self.build["configuration"] = "untrusted/tsconfig.json"
        self.reject("local-build-identity-invalid")

    def test_runtime_source_inventory_mismatch_rejects(self):
        self.runtime["source_inventory_digest"] = OTHER
        self.reject("local-build-runtime-binding-invalid")

    def test_runtime_dependency_tree_mismatch_rejects(self):
        self.runtime["dependency_tree_digest"] = OTHER
        self.reject("local-build-runtime-binding-invalid")

    def test_source_typescript_fallback_rejects(self):
        self.runtime["artifact_files"].append(fingerprint("node_modules/pkg/source.ts"))
        self.reject("local-build-runtime-artifact-invalid")

    def test_duplicate_runtime_artifact_rejects(self):
        self.runtime["artifact_files"].append(copy.deepcopy(self.runtime["artifact_files"][0]))
        self.reject("local-build-path-invalid")

    def test_runtime_artifact_traversal_rejects(self):
        self.runtime["artifact_files"].append(fingerprint("node_modules/../../secret"))
        self.reject("local-build-path-invalid")

    def test_receipt_hash_tamper_rejects(self):
        self.runtime["compiler_artifact_digest"] = OTHER
        seal(self.value, "result_digest")
        self.reject("local-build-digest-invalid", reseal_digest=False)

    def test_unknown_runtime_fields_reject(self):
        self.runtime["raw_output"] = "SENSITIVE-LOCAL-SENTINEL"
        self.reject()

    def test_no_runtime_authority_can_be_granted(self):
        self.runtime["authorized"] = True
        self.reject()

    def test_no_result_authority_can_be_granted(self):
        self.value["operation_authorization"] = "allowed"
        self.reject()

    def test_generator_matches_fresh_source_manifest(self):
        manifest = [fingerprint(self.runtime["generator"]["path"])]
        contracts.runtime_source_binding(self.runtime, manifest)

    def test_changed_source_generator_rejects(self):
        manifest = [fingerprint(self.runtime["generator"]["path"], OTHER)]
        with self.assertRaisesRegex(release.ReleaseFailure, "^local-build-runtime-generator-binding-invalid$"):
            contracts.runtime_source_binding(self.runtime, manifest)

    def test_missing_source_generator_rejects(self):
        with self.assertRaisesRegex(release.ReleaseFailure, "^local-build-runtime-generator-binding-invalid$"):
            contracts.runtime_source_binding(self.runtime, [])

    def test_duplicate_source_generator_rejects(self):
        row = fingerprint(self.runtime["generator"]["path"])
        with self.assertRaisesRegex(release.ReleaseFailure, "^local-build-runtime-generator-binding-invalid$"):
            contracts.runtime_source_binding(self.runtime, [row, copy.deepcopy(row)])


if __name__ == "__main__":
    unittest.main()
