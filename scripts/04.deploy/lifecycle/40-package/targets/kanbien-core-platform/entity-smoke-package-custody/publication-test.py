#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.immutable-publication
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove exact publication identity, reservation before push and observation-only reconciliation with controlled provider responses.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import importlib.util
import json
from pathlib import Path
import tempfile

SPEC = importlib.util.spec_from_file_location("entity_smoke_publication", Path(__file__).with_name("publication.py"))
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)
if not __debug__: raise SystemExit("ENTITY_SMOKE_PUBLICATION_ASSERTIONS_DISABLED")
CANARY = "credential-row-provider-canary"
SOURCE, IMAGE, DIGEST = "a" * 40, "sha256:" + "b" * 64, "sha256:" + "c" * 64


def fails(call, code):
    try: call()
    except CONTROL.PublicationFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected closed publication rejection")


with tempfile.TemporaryDirectory(prefix="entity-smoke-publication-") as directory:
    root = Path(directory)
    output = root / "github-output"; output.touch()
    env = {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": "gordonrose/entity-builder-harness", "GITHUB_REF": "refs/heads/main",
           "GITHUB_WORKFLOW_REF": "gordonrose/entity-builder-harness/.github/workflows/publish-kanbien-core-platform-entity-smoke.yml@refs/heads/main",
           "GITHUB_SHA": SOURCE, "GITHUB_RUN_ID": "123456", "RUNNER_TEMP": str(root), "GITHUB_OUTPUT": str(output),
           "ECR_REPOSITORY": CONTROL.REPOSITORY, "ECR_URI": CONTROL.URI, "AWS_REGION": "eu-west-1"}
    tag = "entity-smoke-" + SOURCE[:12] + "-run123456"
    calls = []; state = {"lost": False, "identity": True, "image": IMAGE, "source": SOURCE, "remote_digest": DIGEST, "scan": True}
    def provider(*parts):
        calls.append(("aws", *parts))
        if parts[:2] == ("sts", "get-caller-identity"):
            return {"Account": "337159794548", "Arn": "arn:aws:sts::337159794548:assumed-role/" + (CONTROL.ROLE if state["identity"] else "wrong-publisher") + "/fixture"}
        if parts[:2] == ("ecr", "describe-repositories"):
            return {"repositories": [{"repositoryName": CONTROL.REPOSITORY, "repositoryUri": CONTROL.URI, "imageTagMutability": "IMMUTABLE", "imageScanningConfiguration": {"scanOnPush": state["scan"]}}]}
        assert parts[:2] == ("ecr", "describe-images")
        return {"imageDetails": [{"repositoryName": CONTROL.REPOSITORY, "imageDigest": state["remote_digest"], "imageTags": [tag]}]}
    def command(argv, timeout=30):
        calls.append(tuple(argv))
        if argv[0] == "python3":
            assert argv[1].endswith("qualification.py") and argv[2] == "verify"
            assert argv.count("--configuration-input") == 2
            return state["image"]
        assert argv[0] == "docker"
        if argv[1:3] == ["image", "inspect"]: return state["source"]
        if argv[1] == "push":
            assert (root / "entity-smoke-publication-reservation.json").is_file()
            assert (root / "entity-smoke-publication-invoked.json").is_file(), "intent must be durable before the single push"
            assert argv[2] == CONTROL.URI + ":" + tag
            if state["lost"]: raise CONTROL.PublicationFailure("publication-observation-unavailable")
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
    path = root / "entity-smoke-publication-reservation.json"
    original = path.read_bytes()
    assert path.stat().st_mode & 0o777 == 0o600
    fails(lambda: CONTROL.publish("reserve", env), "publication-attempt-already-reserved-reconcile-only")
    assert path.read_bytes() == original
    assert not any(call[:2] == ("docker", "push") for call in calls)
    state["image"] = "sha256:" + "d" * 64
    fails(lambda: CONTROL.publish("publish", env), "publication-qualified-image-mismatch")
    assert not (root / "entity-smoke-publication-invoked.json").exists()
    state["image"] = IMAGE; state["lost"] = True
    fails(lambda: CONTROL.publish("publish", env), "publication-observation-unavailable")
    assert CONTROL.publication_effect == "unknown"
    fails(lambda: CONTROL.publish("publish", env), "publication-attempt-already-reserved-reconcile-only")
    assert sum(call[:2] == ("docker", "push") for call in calls) == 1
    start = len(calls)
    observed = CONTROL.publish("reconcile", env)
    assert observed["verdict"] == "passed" and observed["image_digest"] == DIGEST and observed["qualification_evidence"] is False
    assert not any(call[:2] in {("docker", "push"), ("docker", "tag")} for call in calls[start:])
    assert path.read_bytes() == original
    assert output.read_text() == "digest=" + DIGEST + "\ntag=" + tag + "\n"
    state["remote_digest"] = CANARY
    fails(lambda: CONTROL.publish("reconcile", env), "publication-remote-image-not-confirmed")
    assert sum(call[:2] == ("docker", "push") for call in calls) == 1
print(json.dumps({"schema": "deploy/entity-smoke-publication-fixture/v1", "verdict": "passed", "provider_observation": False,
                  "cases": ["source-and-destination", "wrong-publisher", "scan-enabled-repository", "reserve-before-push", "immutable-reservation", "changed-qualified-image", "lost-push-response", "no-second-push", "read-only-reconciliation", "typed-remote-digest"]}))
