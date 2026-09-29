#!/usr/bin/env python3
"""Keep the source validation workflow read-only and wired to the full check."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.release-control-source-validation
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject workflow authority, bypasses and omitted governance metadata in source validation.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import shlex
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ".github/workflows/release-control-source-validation.yml"
GATE = "scripts/04.deploy/operational-realization-gate"
METADATA_CHECK = "scripts/01.harness/artifact-metadata/check-headers/script.sh"
REQUIRED_METADATA = {
    ".agentic/01.harness/standards/autonomous-delivery-envelope.v1.md",
    ".agentic/01.harness/workflows/sustained-implementation.md",
    ".agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md",
    "docs/04.deploy/plans/release-control-source-adoption",
    WORKFLOW,
    GATE,
    "scripts/04.deploy/release-control",
    "infra/04.deploy/contracts/release-control/v1",
}
# Reviewed immutable upstream release commits; updating an action requires review.
ACTIONS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/setup-node": "820762786026740c76f36085b0efc47a31fe5020",
    "actions/setup-python": "5fda3b95a4ea91299a34e894583c3862153e4b97",
}


def check_workflow(document):
    """Assert this bounded workflow's safety contract, not a general YAML policy."""
    assert isinstance(document, dict)
    assert set(document) == {"name", "on", "permissions", "jobs"}
    assert document["permissions"] == {"contents": "read"}
    assert document["on"] == {"pull_request": {}, "push": {}, "workflow_dispatch": {}}
    assert set(document["jobs"]) == {"source-validation"}
    job = document["jobs"]["source-validation"]
    assert set(job) == {"name", "runs-on", "timeout-minutes", "steps"}
    assert job["name"] == "Release control source validation"
    assert job["runs-on"] == "ubuntu-24.04"
    assert type(job["timeout-minutes"]) is int and 1 <= job["timeout-minutes"] <= 30
    steps = job["steps"]
    assert isinstance(steps, list) and len(steps) == 4
    seen = set()
    for step in steps[:-1]:
        assert set(step) == {"name", "uses", "with"}
        match = re.fullmatch(r"(actions/[a-z-]+)@([0-9a-f]{40})", step["uses"])
        assert match is not None
        action, revision = match.groups()
        assert action in ACTIONS and revision == ACTIONS[action]
        assert action not in seen
        seen.add(action)
        settings = step["with"]
        if action == "actions/checkout":
            assert step is steps[0]
            assert set(settings) == {"persist-credentials", "clean"}
            assert settings["persist-credentials"] is False
            assert settings["clean"] is False
        elif action == "actions/setup-node":
            assert set(settings) == {"node-version", "architecture", "package-manager-cache"}
            assert settings["node-version"] == "22.23.3"
            assert settings["architecture"] == "x64"
            assert settings["package-manager-cache"] is False
        else:
            assert set(settings) == {"python-version", "architecture", "freethreaded"}
            assert settings["python-version"] == "3.14.4"
            assert settings["architecture"] == "x64"
            assert settings["freethreaded"] is False
    assert seen == set(ACTIONS)
    check = steps[-1]
    assert set(check) == {"name", "shell", "run"}
    assert check["shell"] == "bash"
    assert shlex.split(check["run"]) == [
        "bash", GATE + "/verify-clean-environment.sh", "--python", "python3",
    ]


def check_package_wiring(package):
    scripts = package["scripts"]
    assert shlex.split(scripts["deployment:realization:clean-check"]) == [
        "bash", GATE + "/verify-clean-environment.sh",
    ]
    command = shlex.split(scripts["deployment:realization:check"])
    assert command[:7] == [
        "npm", "run", "deployment:realization:test", "&&", "bash", METADATA_CHECK, "--paths",
    ]
    paths = command[7:]
    assert paths and len(paths) == len(set(paths))
    assert REQUIRED_METADATA.issubset(paths)
    assert all(re.fullmatch(r"[.a-zA-Z0-9_/-]+", path) for path in paths)
    assert shlex.split(scripts["deployment:realization:test"]) == ["bash", GATE + "/smoke-test.sh"]
    # An npm lifecycle hook would expand the command beyond the reviewed boundary.
    for command_name in ("deployment:realization:clean-check", "deployment:realization:check",
                         "deployment:realization:test"):
        assert "pre" + command_name not in scripts and "post" + command_name not in scripts


class ValidationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.safe_load((ROOT / WORKFLOW).read_text(encoding="utf-8"))
        self.package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    def rejected(self, change):
        candidate = deepcopy(self.workflow)
        change(candidate)
        with self.assertRaises((AssertionError, KeyError, TypeError)):
            check_workflow(candidate)

    def test_repository_workflow_is_validation_only(self):
        check_workflow(self.workflow)

    def test_normal_check_includes_previously_omitted_governance(self):
        check_package_wiring(self.package)
        for relative in REQUIRED_METADATA:
            self.assertTrue((ROOT / relative).exists(), relative)
        for relative in (
            "docs/04.deploy/plans/release-control-source-adoption/README.md",
            "docs/04.deploy/plans/release-control-source-adoption/2026-09-29-triage-and-callers/README.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_missing_normal_metadata_scope_is_rejected(self):
        for relative in REQUIRED_METADATA:
            with self.subTest(path=relative):
                package = deepcopy(self.package)
                package["scripts"]["deployment:realization:check"] = package["scripts"][
                    "deployment:realization:check"].replace(" " + relative, "")
                with self.assertRaises(AssertionError):
                    check_package_wiring(package)

    def test_failure_masking_or_replaced_check_is_rejected(self):
        for command in ("true", "npm run deployment:realization:test || true", "echo skipped"):
            with self.subTest(command=command):
                package = deepcopy(self.package)
                package["scripts"]["deployment:realization:check"] = command
                with self.assertRaises(AssertionError):
                    check_package_wiring(package)
        self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][-1].update(
            run="npm run deployment:realization:clean-check -- --python python3 || true"))

    def test_clean_check_cannot_bypass_canonical_wrapper(self):
        for command in ("npm run deployment:realization:check", "true"):
            package = deepcopy(self.package)
            package["scripts"]["deployment:realization:clean-check"] = command
            with self.assertRaises(AssertionError):
                check_package_wiring(package)

    def test_workflow_enters_wrapper_before_any_npm_configuration(self):
        # An outer npm invocation can honor .npmrc before the wrapper sanitizes it.
        self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][-1].update(
            run="npm run deployment:realization:clean-check -- --python python3"))

    def test_npm_hook_cannot_expand_validation_effects(self):
        for prefix in ("pre", "post"):
            package = deepcopy(self.package)
            package["scripts"][prefix + "deployment:realization:clean-check"] = "external-command"
            with self.assertRaises(AssertionError):
                check_package_wiring(package)

    def test_missing_or_privileged_events_are_rejected(self):
        for event in ("pull_request", "push", "workflow_dispatch"):
            self.rejected(lambda doc: doc["on"].pop(event))
        self.rejected(lambda doc: doc["on"].update(pull_request_target={}))
        self.rejected(lambda doc: doc["on"].update(workflow_run={"workflows": ["trusted"]}))

    def test_event_filters_cannot_skip_the_named_check(self):
        for configuration in ({"paths": ["scripts/**"]}, {"paths-ignore": ["docs/**"]},
                              {"branches": ["main"]}):
            self.rejected(lambda doc: doc["on"].update(pull_request=configuration))

    def test_write_permissions_and_oidc_are_rejected(self):
        for permission in ("contents", "id-token", "packages", "attestations", "pull-requests"):
            self.rejected(lambda doc: doc["permissions"].update({permission: "write"}))
        self.rejected(lambda doc: doc.pop("permissions"))
        self.rejected(lambda doc: doc["jobs"]["source-validation"].update(permissions={"contents": "write"}))

    def test_remote_mutations_or_extra_actions_are_rejected(self):
        for step in ({"name": "Publish", "run": "npm publish"},
                     {"name": "AWS", "uses": "aws-actions/configure-aws-credentials@" + "a" * 40}):
            self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"].append(step))

    def test_missing_runtime_setup_or_untrusted_action_pin_is_rejected(self):
        for index in range(3):
            self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"].pop(index))
        for reference in ("actions/checkout@v7", "actions/checkout@" + "a" * 40,
                          "other/checkout@" + ACTIONS["actions/checkout"]):
            self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][0].update(uses=reference))

    def test_credentials_cache_and_checkout_override_are_rejected(self):
        for settings in ({"persist-credentials": True}, {"token": "${{ secrets.TOKEN }}"},
                         {"ref": "main"}, {"allow-unsafe-pr-checkout": True}):
            self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][0]["with"].update(settings))
        self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][1]["with"].update(
            {"package-manager-cache": True}))

    def test_unpinned_or_incompatible_runtimes_are_rejected(self):
        for version in ("3.14", "3.14.4t", "3.13.0"):
            self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][2]["with"].update(
                {"python-version": version}))
        self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][2]["with"].update(
            {"freethreaded": True}))
        self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][1]["with"].update(
            {"node-version": "22"}))
        self.rejected(lambda doc: doc["jobs"]["source-validation"].update({"runs-on": "self-hosted"}))

    def test_conditions_failure_suppression_and_secret_environment_are_rejected(self):
        for extra in ({"if": "false"}, {"continue-on-error": True}, {"environment": "production"},
                      {"env": {"TOKEN": "${{ secrets.TOKEN }}"}}):
            self.rejected(lambda doc: doc["jobs"]["source-validation"].update(extra))
            self.rejected(lambda doc: doc["jobs"]["source-validation"]["steps"][-1].update(extra))


if __name__ == "__main__":
    unittest.main()
