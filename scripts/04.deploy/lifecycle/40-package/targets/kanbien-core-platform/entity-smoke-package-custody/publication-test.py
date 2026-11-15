#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.immutable-publication
#   version: 2
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove both workload publication bindings, renamed reuse, immutable reservation and safe failures through the shared publisher.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from dataclasses import replace
from contextlib import redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("entity_smoke_publication", Path(__file__).with_name("publication.py"))
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)
from ecr_publication import PublicationFailure, Publisher
FEATURE = CONTROL.PUBLISHER
BASELINE_SPEC = importlib.util.spec_from_file_location("persistence_publication", Path(__file__).parents[1] / "core-server-persistence-package-custody/publication.py")
BASELINE = importlib.util.module_from_spec(BASELINE_SPEC)
BASELINE_SPEC.loader.exec_module(BASELINE)
if not __debug__: raise SystemExit("ENTITY_SMOKE_PUBLICATION_ASSERTIONS_DISABLED")
CANARY = "credential-row-provider-canary"
SOURCE, IMAGE, DIGEST = "a" * 40, "sha256:" + "b" * 64, "sha256:" + "c" * 64


def fails(call, code):
    try: call()
    except PublicationFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected closed publication rejection")


def exercise(CONTROL, lost):
    with tempfile.TemporaryDirectory(prefix="entity-smoke-publication-") as directory:
        root = Path(directory)
        output = root / "github-output"; output.touch()
        env = {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": CONTROL.binding.source_repository, "GITHUB_REF": "refs/heads/main",
               "GITHUB_WORKFLOW_REF": CONTROL.binding.source_repository + "/.github/workflows/" + CONTROL.binding.workflow + "@refs/heads/main",
               "GITHUB_SHA": SOURCE, "GITHUB_RUN_ID": "123456", "RUNNER_TEMP": str(root), "GITHUB_OUTPUT": str(output),
               "ECR_REPOSITORY": CONTROL.binding.repository, "ECR_URI": CONTROL.binding.uri, "AWS_REGION": CONTROL.binding.region}
        tag = CONTROL.binding.tag_prefix + "-" + SOURCE[:12] + "-run123456"
        calls = []; state = {"lost": False, "identity": True, "image": IMAGE, "source": SOURCE, "remote_digest": DIGEST, "scan": True}
        def provider(*parts):
            calls.append(("aws", *parts))
            if parts[:2] == ("sts", "get-caller-identity"):
                return {"Account": CONTROL.binding.account, "Arn": "arn:aws:sts::" + CONTROL.binding.account + ":assumed-role/" + (CONTROL.binding.role if state["identity"] else "wrong-publisher") + "/fixture"}
            if parts[:2] == ("ecr", "describe-repositories"):
                return {"repositories": [{"repositoryName": CONTROL.binding.repository, "repositoryUri": CONTROL.binding.uri, "imageTagMutability": "IMMUTABLE", "imageScanningConfiguration": {"scanOnPush": state["scan"]}}]}
            assert parts[:2] == ("ecr", "describe-images")
            return {"imageDetails": [{"repositoryName": CONTROL.binding.repository, "imageDigest": state["remote_digest"], "imageTags": [tag]}]}
        def command(argv, timeout=30):
            calls.append(tuple(argv))
            if argv[0] == "python3":
                expected = ["python3", "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py", "verify",
                            "--image", argv[4], "--receipt", str(root / "qualified-image.json")]
                for configuration in CONTROL.binding.configuration:
                    expected.extend(["--configuration-input", *configuration])
                assert argv == expected
                assert argv[4] in {CONTROL.binding.local_image, CONTROL.binding.uri + "@" + DIGEST}
                return state["image"]
            assert argv[0] == "docker"
            if argv[1:3] == ["image", "inspect"]: return state["source"]
            if argv[1] == "push":
                assert (root / (CONTROL.binding.artifact_stem + "-publication-reservation.json")).is_file()
                assert (root / (CONTROL.binding.artifact_stem + "-publication-invoked.json")).is_file(), "intent must be durable before the single push"
                assert argv[2] == CONTROL.binding.uri + ":" + tag
                if state["lost"]: raise PublicationFailure("publication-observation-unavailable")
            assert argv[1] in {"tag", "push", "pull"}
            return ""
        CONTROL.aws, CONTROL.run = provider, command
        for key, invalid in [("GITHUB_REF", "refs/heads/chat"), ("GITHUB_SHA", CANARY), ("GITHUB_WORKFLOW_REF", CANARY), ("ECR_URI", CANARY)]:
            fails(lambda key=key, invalid=invalid: CONTROL.publish("reserve", {**env, key: invalid}), "publication-source-route-invalid" if key in {"GITHUB_REF", "GITHUB_WORKFLOW_REF"} else "publication-source-identity-invalid" if key == "GITHUB_SHA" else "publication-destination-invalid")
        assert calls == [], "invalid routing must stop before any provider call"
        fails(lambda: CONTROL.publish("unexpected", env), "publication-operation-invalid")
        assert calls == []
        state["identity"] = False
        fails(lambda: CONTROL.publish("reserve", env), "publication-publisher-identity-invalid")
        assert not list(root.glob("*reservation*"))
        state["identity"] = True; state["scan"] = False
        fails(lambda: CONTROL.publish("reserve", env), "publication-repository-not-confirmed")
        state["scan"] = True
        reserved = CONTROL.publish("reserve", env)
        assert reserved["verdict"] == "reserved" and reserved["publication_performed"] is False
        path = root / (CONTROL.binding.artifact_stem + "-publication-reservation.json")
        original = path.read_bytes()
        assert path.stat().st_mode & 0o777 == 0o600
        fails(lambda: CONTROL.publish("reserve", env), "publication-attempt-already-reserved-reconcile-only")
        assert path.read_bytes() == original
        assert not any(call[:2] == ("docker", "push") for call in calls)
        state["image"] = "sha256:" + "d" * 64
        fails(lambda: CONTROL.publish("publish", env), "publication-qualified-image-mismatch")
        assert not (root / (CONTROL.binding.artifact_stem + "-publication-invoked.json")).exists()
        state["image"] = IMAGE; state["lost"] = lost
        if lost:
            fails(lambda: CONTROL.publish("publish", env), "publication-observation-unavailable")
        else:
            published = CONTROL.publish("publish", env)
            assert published["verdict"] == "passed" and published["qualification_evidence"] is False
        assert CONTROL.publication_effect == "unknown"
        fails(lambda: CONTROL.publish("publish", env), "publication-attempt-already-reserved-reconcile-only")
        assert CONTROL.publication_effect == "unknown", "duplicate rejection cannot erase the earlier uncertain effect"
        assert sum(call[:2] == ("docker", "push") for call in calls) == 1
        start = len(calls)
        observed = CONTROL.publish("reconcile", env)
        assert observed["verdict"] == "passed" and observed["image_digest"] == DIGEST and observed["qualification_evidence"] is False
        assert not any(call[:2] in {("docker", "push"), ("docker", "tag")} for call in calls[start:])
        assert path.read_bytes() == original
        assert output.read_text() == ("digest=" + DIGEST + "\ntag=" + tag + "\n") * (1 if lost else 2)
        before = output.read_text()
        state["image"] = "sha256:" + "d" * 64
        fails(lambda: CONTROL.publish("reconcile", env), "publication-remote-image-mismatch")
        state["image"] = IMAGE; state["source"] = "d" * 40
        fails(lambda: CONTROL.publish("reconcile", env), "publication-remote-source-mismatch")
        state["source"] = SOURCE
        state["remote_digest"] = CANARY
        fails(lambda: CONTROL.publish("reconcile", env), "publication-remote-image-not-confirmed")
        assert output.read_text() == before
        assert sum(call[:2] == ("docker", "push") for call in calls) == 1

for publisher in (FEATURE, BASELINE.PUBLISHER, Publisher(FEATURE.root, replace(FEATURE.binding,
        source_repository="fixture/project", workflow="publish-renamed.yml", target="fixture-target", scope="renamed-workload",
        account="123456789012", region="us-east-1", repository="fixture/renamed", role="renamed-publisher",
        local_image="fixture-renamed:qualification", tag_prefix="renamed", artifact_stem="renamed", error_prefix="RENAMED"))):
    for lost in (False, True):
        exercise(publisher, lost)

for field, value in [("workflow", "../escape.yml"), ("account", CANARY), ("configuration", []),
                     ("configuration", (("../outside.py", "infra/04.deploy/example.yml", "*"),)), ("role", CANARY + "/bad")]:
    fails(lambda field=field, value=value: Publisher(FEATURE.root, replace(FEATURE.binding, **{field: value})), "publication-binding-invalid")

for binding in (FEATURE.binding, BASELINE.PUBLISHER.binding):
    # Actual command boundary: native errors/output never become diagnostics.
    publisher = Publisher(FEATURE.root, binding)
    result = SimpleNamespace(returncode=0, stdout='{"safe": true}\n', stderr=CANARY)
    with patch("ecr_publication.subprocess.run", return_value=result) as command:
        assert publisher.aws("sts", "get-caller-identity") == {"safe": True}
        argv = command.call_args.args[0]
        options = command.call_args.kwargs
        assert argv == ["aws", "sts", "get-caller-identity", "--region", binding.region, "--output", "json",
                        "--cli-connect-timeout", "5", "--cli-read-timeout", "20"]
        assert options["cwd"] == FEATURE.root and options["timeout"] == 30 and options["check"] is False
        assert options["env"]["AWS_PAGER"] == "" and options["env"]["AWS_MAX_ATTEMPTS"] == "1"
    for native in (OSError(CANARY), UnicodeError(CANARY), subprocess.TimeoutExpired(["fixture"], 30, output=CANARY)):
        with patch("ecr_publication.subprocess.run", side_effect=native) as command:
            fails(lambda: publisher.aws("sts", "get-caller-identity"), "publication-observation-unavailable")
            assert command.call_count == 1
    for code, result in (
        ("publication-command-not-confirmed", SimpleNamespace(returncode=1, stdout=CANARY, stderr=CANARY)),
        ("publication-provider-observation-invalid", SimpleNamespace(returncode=0, stdout=CANARY, stderr=CANARY)),
    ):
        with patch("ecr_publication.subprocess.run", return_value=result):
            fails(lambda: publisher.aws("sts", "get-caller-identity"), code)
    with tempfile.TemporaryDirectory() as directory:
        publisher.report_directory, publisher.report_run_id = Path(directory), "123456"
        publisher.publication_effect = "unknown"
        for collection, response in (("collected", SimpleNamespace(returncode=0)), ("failed", SimpleNamespace(returncode=1))):
            captured = io.StringIO()
            with patch.object(publisher, "main", side_effect=ValueError(CANARY)), patch("ecr_publication.subprocess.run", return_value=response) as command, redirect_stderr(captured):
                assert publisher.execute() == 1
            report = json.loads(captured.getvalue())
            assert CANARY not in captured.getvalue()
            assert report["code"] == binding.error_prefix + "_PUBLICATION_NOT_CONFIRMED"
            assert report["effect"] == "unknown" and report["condition"] == "publication-boundary-failed"
            assert report["diagnostic_collection"] == collection
            argv = command.call_args.args[0]
            assert argv[argv.index("--scope")+1] == binding.scope
            assert argv[argv.index("--outcome")+1] == "unknown"
            assert command.call_count == 1
        captured = io.StringIO()
        with patch.object(publisher, "main", side_effect=PublicationFailure("publication-remote-image-mismatch")), patch("ecr_publication.subprocess.run", side_effect=OSError(CANARY)), redirect_stderr(captured):
            assert publisher.execute() == 1
        assert json.loads(captured.getvalue())["condition"] == "publication-remote-image-mismatch"
        assert json.loads(captured.getvalue())["diagnostic_collection"] == "failed"
        assert CANARY not in captured.getvalue()
        # The real diagnostic reader/writer must accept each workload binding.
        captured = io.StringIO()
        with patch.object(publisher, "main", side_effect=PublicationFailure("publication-remote-image-mismatch")), redirect_stderr(captured):
            assert publisher.execute() == 1
        assert json.loads(captured.getvalue())["diagnostic_collection"] == "collected"
        report_path = Path(directory) / (binding.artifact_stem + "-publication-operation.json")
        report = json.loads(report_path.read_text())
        assert report["target"] == binding.target and report["scope"] == binding.scope
        assert report["original_failure"] == {"code": binding.error_prefix + "_PUBLICATION_NOT_CONFIRMED", "exit_status": 1}
        assert CANARY not in report_path.read_text()

print(json.dumps({"schema": "deploy/entity-smoke-publication-fixture/v1", "verdict": "passed", "provider_observation": False, "workload_bindings": 3,
                  "cases": ["source-and-destination", "wrong-publisher", "scan-enabled-repository", "reserve-before-push", "immutable-reservation", "changed-qualified-image", "lost-push-response", "no-second-push", "read-only-reconciliation", "typed-remote-digest"]}))
