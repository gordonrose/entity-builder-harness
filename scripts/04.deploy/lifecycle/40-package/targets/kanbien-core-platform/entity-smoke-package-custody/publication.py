#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.immutable-publication
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reserve one qualified feature image publication and reconcile an immutable tag without replaying a push.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

REPOSITORY = "kanbien-core-platform/entity-smoke"
URI = "337159794548.dkr.ecr.eu-west-1.amazonaws.com/" + REPOSITORY
ROLE = "github-kanbien-core-platform-entity-smoke-publisher"
LOCAL = "kanbien-entity-smoke:qualification"
ROOT = Path(__file__).resolve().parents[7]
FAILURE_CODES = frozenset({
    "publication-observation-unavailable", "publication-command-not-confirmed", "publication-provider-observation-invalid",
    "publication-path-invalid", "publication-attempt-already-reserved-reconcile-only", "publication-source-route-invalid",
    "publication-source-identity-invalid", "publication-destination-invalid", "publication-publisher-identity-invalid",
    "publication-repository-not-confirmed", "publication-qualified-image-invalid", "publication-qualified-source-mismatch",
    "publication-operation-invalid", "publication-reservation-mismatch", "publication-qualified-image-mismatch",
    "publication-remote-image-not-confirmed", "publication-remote-image-mismatch", "publication-remote-source-mismatch",
    "publication-output-path-invalid", "publication-arguments-invalid",
})
publication_effect = "not-started"
report_directory = None
report_run_id = None
CONFIGURATION = [
    ("scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py", "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke.yml", "entity-smoke-server,entity-smoke-migration,entity-smoke-administration,entity-smoke-verifier,entity-smoke-database-proof"),
    ("scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py", "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke-isolated-restore.yml", "entity-smoke-restore-reader"),
]


class PublicationFailure(Exception):
    def __init__(self, code):
        self.code = code if code in FAILURE_CODES else "publication-boundary-failed"
        super().__init__(self.code)


def require(allowed, code):
    if not allowed: raise PublicationFailure(code)


def run(argv, timeout=30):
    try:
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False,
                                env={**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1"})
    except (OSError, UnicodeError, subprocess.SubprocessError):
        raise PublicationFailure("publication-observation-unavailable") from None
    require(result.returncode == 0, "publication-command-not-confirmed")
    return result.stdout.strip()


def aws(*parts):
    output = run(["aws", *parts, "--region", "eu-west-1", "--output", "json", "--cli-connect-timeout", "5", "--cli-read-timeout", "20"])
    try: return json.loads(output)
    except (TypeError, json.JSONDecodeError): raise PublicationFailure("publication-provider-observation-invalid") from None


def exclusive(path, value):
    require(not path.is_symlink() and not any(part.is_symlink() for part in path.parents), "publication-path-invalid")
    try:
        with path.open("x", encoding="utf-8") as stream:
            os.chmod(path, 0o600)
            json.dump(value, stream, sort_keys=True)
            stream.flush(); os.fsync(stream.fileno())
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    except FileExistsError: raise PublicationFailure("publication-attempt-already-reserved-reconcile-only") from None


def context(env):
    require(env.get("GITHUB_ACTIONS") == "true" and env.get("GITHUB_REPOSITORY") == "gordonrose/entity-builder-harness" and env.get("GITHUB_REF") == "refs/heads/main" and env.get("GITHUB_WORKFLOW_REF") == "gordonrose/entity-builder-harness/.github/workflows/publish-kanbien-core-platform-entity-smoke.yml@refs/heads/main", "publication-source-route-invalid")
    source, run_id = env.get("GITHUB_SHA", ""), env.get("GITHUB_RUN_ID", "")
    require(re.fullmatch(r"[a-f0-9]{40}", source) is not None and re.fullmatch(r"[1-9][0-9]{0,19}", run_id) is not None, "publication-source-identity-invalid")
    require(env.get("ECR_REPOSITORY") == REPOSITORY and env.get("ECR_URI") == URI and env.get("AWS_REGION") == "eu-west-1", "publication-destination-invalid")
    directory = Path(env.get("RUNNER_TEMP", ""))
    require(directory.is_absolute() and directory.is_dir() and not directory.is_symlink() and not any(part.is_symlink() for part in directory.parents), "publication-path-invalid")
    return source, run_id, directory


def identity():
    caller = aws("sts", "get-caller-identity")
    require(isinstance(caller, dict) and caller.get("Account") == "337159794548" and isinstance(caller.get("Arn"), str) and re.fullmatch(r"arn:aws:sts::337159794548:assumed-role/" + ROLE + r"/[A-Za-z0-9+=,.@_-]+", caller["Arn"]) is not None, "publication-publisher-identity-invalid")
    response = aws("ecr", "describe-repositories", "--repository-names", REPOSITORY)
    repositories = response.get("repositories") if isinstance(response, dict) else None
    require(isinstance(repositories, list) and len(repositories) == 1, "publication-repository-not-confirmed")
    repository = repositories[0]
    require(isinstance(repository, dict) and repository.get("repositoryName") == REPOSITORY and repository.get("repositoryUri") == URI and repository.get("imageTagMutability") == "IMMUTABLE" and repository.get("imageScanningConfiguration", {}).get("scanOnPush") is True, "publication-repository-not-confirmed")


def qualified(directory, image):
    command = ["python3", "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py", "verify", "--image", image, "--receipt", str(directory / "qualified-image.json")]
    for binding in CONFIGURATION: command.extend(["--configuration-input", *binding])
    value = run(command)
    require(re.fullmatch(r"sha256:[a-f0-9]{64}", value) is not None, "publication-qualified-image-invalid")
    return value


def publish(operation, env):
    global publication_effect, report_directory, report_run_id
    require(operation in {"reserve", "publish", "reconcile"}, "publication-operation-invalid")
    source, run_id, directory = context(env)
    report_directory, report_run_id = directory, run_id
    publication_effect = "unknown" if operation == "reconcile" else "not-started"
    identity()
    reservation_path = directory / "entity-smoke-publication-reservation.json"
    tag = "entity-smoke-" + source[:12] + "-run" + run_id
    if operation == "reserve":
        image_id = qualified(directory, LOCAL)
        revision = run(["docker", "image", "inspect", image_id, "--format", '{{ index .Config.Labels "org.opencontainers.image.revision" }}'])
        require(revision == source, "publication-qualified-source-mismatch")
        exclusive(reservation_path, {"schema": "deploy/entity-smoke-publication-reservation/v1", "source_revision": source, "run_id": run_id, "image_id": image_id, "repository": REPOSITORY, "tag": tag})
        return {"verdict": "reserved", "source_revision": source, "publication_performed": False}
    require(operation in {"publish", "reconcile"}, "publication-operation-invalid")
    require(not reservation_path.is_symlink(), "publication-path-invalid")
    reservation = json.loads(reservation_path.read_text())
    require(isinstance(reservation, dict) and set(reservation) == {"schema", "source_revision", "run_id", "image_id", "repository", "tag"} and reservation.get("schema") == "deploy/entity-smoke-publication-reservation/v1" and reservation.get("source_revision") == source and reservation.get("run_id") == run_id and reservation.get("repository") == REPOSITORY and reservation.get("tag") == tag and isinstance(reservation.get("image_id"), str) and re.fullmatch(r"sha256:[a-f0-9]{64}", reservation["image_id"]) is not None, "publication-reservation-mismatch")
    if operation == "publish":
        require(qualified(directory, LOCAL) == reservation["image_id"], "publication-qualified-image-mismatch")
        # A duplicate invocation cannot push, including after a lost response.
        exclusive(directory / "entity-smoke-publication-invoked.json", reservation)
        run(["docker", "tag", reservation["image_id"], URI + ":" + tag])
        publication_effect = "unknown"
        run(["docker", "push", URI + ":" + tag], timeout=600)
    response = aws("ecr", "describe-images", "--repository-name", REPOSITORY, "--image-ids", "imageTag=" + tag)
    images = response.get("imageDetails") if isinstance(response, dict) else None
    require(isinstance(images, list) and len(images) == 1, "publication-remote-image-not-confirmed")
    image = images[0]
    digest = image.get("imageDigest") if isinstance(image, dict) else None
    tags = image.get("imageTags") if isinstance(image, dict) else None
    require(isinstance(digest, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is not None and isinstance(tags, list) and all(isinstance(item, str) for item in tags) and tag in tags and image.get("repositoryName") == REPOSITORY, "publication-remote-image-not-confirmed")
    reference = URI + "@" + digest
    run(["docker", "pull", reference], timeout=180)
    require(qualified(directory, reference) == reservation["image_id"], "publication-remote-image-mismatch")
    revision = run(["docker", "image", "inspect", reference, "--format", '{{ index .Config.Labels "org.opencontainers.image.revision" }}'])
    require(revision == source, "publication-remote-source-mismatch")
    output = Path(env.get("GITHUB_OUTPUT", ""))
    require(output.is_absolute() and output.is_file() and not output.is_symlink() and not any(part.is_symlink() for part in output.parents), "publication-output-path-invalid")
    with output.open("a") as stream: stream.write("digest=" + digest + "\ntag=" + tag + "\n")
    return {"verdict": "passed", "source_revision": source, "image_digest": digest, "tag": tag, "qualification_evidence": False}


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: parser.exit(2, "ENTITY_SMOKE_PUBLICATION_ARGUMENTS_INVALID\n")
    parser.add_argument("--operation", choices=["reserve", "publish", "reconcile"], required=True)
    args, unknown = parser.parse_known_args()
    require(not unknown, "publication-arguments-invalid")
    result = publish(args.operation, os.environ)
    print(json.dumps({"schema": "deploy/entity-smoke-publication-result/v1", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try: status = main()
    except (PublicationFailure, OSError, ValueError, TypeError, KeyError, AttributeError) as failure:
        collection = "not-started"
        if report_directory is not None:
            try:
                captured = subprocess.run(["python3", "scripts/04.deploy/shared/deployment-operation-diagnostics.py", "record",
                    "--target", "kanbien-core-platform", "--scope", "entity-smoke", "--operation-id", "entity-smoke-publication-" + report_run_id,
                    "--stage", "package", "--original-code", "ENTITY_SMOKE_PUBLICATION_NOT_CONFIRMED", "--exit-status", "1",
                    "--outcome", "unknown" if publication_effect == "unknown" else "rejected", "--classification", "child-command-failed",
                    "--evidence-reference", "github-actions-run:" + report_run_id, "--next-decision", "inspect-retained-evidence",
                    "--report", str(report_directory / "entity-smoke-publication-operation.json")], cwd=ROOT, capture_output=True, timeout=30, check=False)
                collection = "collected" if captured.returncode == 0 else "failed"
            except (OSError, subprocess.SubprocessError): collection = "failed"
        print(json.dumps({"schema": "deploy/entity-smoke-publication-result/v1", "verdict": "failed", "code": "ENTITY_SMOKE_PUBLICATION_NOT_CONFIRMED",
                          "condition": failure.code if isinstance(failure, PublicationFailure) else "publication-boundary-failed",
                          "effect": publication_effect, "diagnostic_collection": collection,
                          "next_action": "reconcile-reserved-publication-no-push-replay"}), file=sys.stderr)
        status = 1
    raise SystemExit(status)
