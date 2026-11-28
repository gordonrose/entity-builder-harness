#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.provider.aws.immutable-publication
#   version: 3
#   status: active
#   created_on: "2026-11-15"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.package-qualification
#   disciplines: [security, sre]
#   kind: script
#   purpose: Observe immutable ECR repositories and publish qualified images through checked workload bindings without uncertain push replay.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.core-platform-target-declaration.implementation
#     path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py
#   - id: deploy.library.aws.preparation-inputs
#     path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py
#   - id: deploy.library.package-custody-acquisition
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/acquire.py
#   - id: deploy.command.entity-smoke.immutable-publication
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/publication.py
#   - id: deploy.command.core-server-persistence.immutable-publication
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/publication.py
import argparse
from dataclasses import dataclass
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

FAILURE_CODES = frozenset({
    "publication-binding-invalid", "publication-observation-unavailable", "publication-command-not-confirmed",
    "publication-provider-observation-invalid", "publication-path-invalid",
    "publication-attempt-already-reserved-reconcile-only", "publication-source-route-invalid",
    "publication-source-identity-invalid", "publication-destination-invalid", "publication-publisher-identity-invalid",
    "publication-repository-not-confirmed", "publication-qualified-image-invalid", "publication-qualified-source-mismatch",
    "publication-operation-invalid", "publication-reservation-mismatch", "publication-qualified-image-mismatch",
    "publication-remote-image-not-confirmed", "publication-remote-image-mismatch", "publication-remote-source-mismatch",
    "publication-output-path-invalid", "publication-arguments-invalid",
    "publication-source-policy-invalid", "publication-source-catalogue-unavailable",
    "publication-source-catalogue-invalid", "publication-source-binding-mismatch",
})


class PublicationFailure(Exception):
    def __init__(self, code):
        self.code = code if code in FAILURE_CODES else "publication-boundary-failed"
        super().__init__(self.code)


def require(allowed, code):
    if not allowed:
        raise PublicationFailure(code)


def source_ref(value):
    """Check an exact branch identity, never a pattern or a dispatch selector."""
    require(isinstance(value, str) and len(value) <= 255
            and re.fullmatch(r"refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]*", value) is not None
            and ".." not in value and not value.endswith(("/", "."))
            and all(part and not part.startswith(".") and not part.endswith(".lock")
                    for part in value.split("/")), "publication-source-policy-invalid")
    return value


def source_policy(pipeline):
    """Return the checked default, approved refs and acquisition selection."""
    require(isinstance(pipeline, dict), "publication-source-policy-invalid")
    default = source_ref(pipeline.get("permitted_source_ref"))
    extra = pipeline.get("additional_permitted_source_refs", [])
    require(isinstance(extra, list) and len(extra) <= 16, "publication-source-policy-invalid")
    allowed = (default, *(source_ref(value) for value in extra))
    require(len(set(allowed)) == len(allowed), "publication-source-policy-invalid")
    acquisition = pipeline.get("custody_acquisition", {})
    require(isinstance(acquisition, dict), "publication-source-policy-invalid")
    selected = source_ref(acquisition.get("source_ref", default))
    require(selected in allowed, "publication-source-policy-invalid")
    return {"default": default, "allowed": allowed, "acquisition": selected}


def repository_identity(provider, *, account, region, repository):
    """Observe the existing immutable/scan contract without publisher-role reuse."""
    require(callable(provider) and isinstance(account, str) and re.fullmatch(r"[0-9]{12}", account) is not None
            and isinstance(region, str) and re.fullmatch(r"[a-z]{2}-[a-z]+-[0-9]", region) is not None
            and isinstance(repository, str) and re.fullmatch(r"[a-z0-9][a-z0-9._/-]*", repository) is not None,
            "publication-binding-invalid")
    uri = account + ".dkr.ecr." + region + ".amazonaws.com/" + repository
    response = provider("ecr", "describe-repositories", repositoryNames=[repository])
    rows = response.get("repositories") if isinstance(response, dict) else None
    require(isinstance(rows, list) and len(rows) == 1, "publication-repository-not-confirmed")
    observed = rows[0]
    scan = observed.get("imageScanningConfiguration") if isinstance(observed, dict) else None
    require(isinstance(observed, dict) and observed.get("repositoryName") == repository
            and observed.get("repositoryUri") == uri and observed.get("imageTagMutability") == "IMMUTABLE"
            and isinstance(scan, dict) and scan.get("scanOnPush") is True, "publication-repository-not-confirmed")
    return {"repository": repository, "repository_uri": uri,
            "repository_arn": "arn:aws:ecr:" + region + ":" + account + ":repository/" + repository}


@dataclass(frozen=True)
class Binding:
    source_repository: str
    workflow: str
    pipeline: str
    target: str
    scope: str
    account: str
    region: str
    repository: str
    role: str
    local_image: str
    tag_prefix: str
    artifact_stem: str
    error_prefix: str
    configuration: tuple

    @property
    def uri(self):
        return self.account + ".dkr.ecr." + self.region + ".amazonaws.com/" + self.repository

    def checked(self):
        # Static composition supplies these fields; environment cannot select
        # a workflow, role, repository, schema or configuration implementation.
        patterns = {
            "source_repository": r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
            "workflow": r"[a-z0-9][a-z0-9-]*\.yml",
            "pipeline": r"[a-z0-9][a-z0-9-]*",
            "target": r"[a-z0-9][a-z0-9-]*", "scope": r"[a-z0-9][a-z0-9-]*",
            "account": r"[0-9]{12}", "region": r"[a-z]{2}-[a-z]+-[0-9]",
            "repository": r"[a-z0-9][a-z0-9._/-]*", "role": r"[A-Za-z0-9+=,.@_-]+",
            "local_image": r"[a-z0-9][a-z0-9._/-]*:[A-Za-z0-9_.-]+",
            "tag_prefix": r"[a-z0-9][a-z0-9-]*", "artifact_stem": r"[a-z0-9][a-z0-9-]*",
            "error_prefix": r"[A-Z][A-Z0-9_]*",
        }
        for name, pattern in patterns.items():
            value = getattr(self, name)
            require(isinstance(value, str) and re.fullmatch(pattern, value) is not None, "publication-binding-invalid")
        # Non-ECS tools bind their full source payload through qualification
        # inputs; workload bindings still supply their explicit projections.
        require(isinstance(self.configuration, tuple), "publication-binding-invalid")
        for item in self.configuration:
            require(isinstance(item, tuple) and len(item) == 3, "publication-binding-invalid")
            adapter, source, selector = item
            for path in (adapter, source):
                require(isinstance(path, str) and re.fullmatch(r"[A-Za-z0-9_./-]+", path) is not None and not path.startswith("/") and ".." not in Path(path).parts, "publication-binding-invalid")
            require(adapter.startswith("scripts/04.deploy/") and source.startswith("infra/04.deploy/") and isinstance(selector, str) and re.fullmatch(r"[A-Za-z0-9_*,.-]+", selector) is not None, "publication-binding-invalid")
        return self


def exclusive(path, value):
    require(not path.is_symlink() and not any(part.is_symlink() for part in path.parents), "publication-path-invalid")
    try:
        with path.open("x", encoding="utf-8") as stream:
            os.chmod(path, 0o600)
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except FileExistsError:
        raise PublicationFailure("publication-attempt-already-reserved-reconcile-only") from None


class Publisher:
    def __init__(self, root, binding):
        require(isinstance(binding, Binding), "publication-binding-invalid")
        self.binding = binding.checked()
        self.root = Path(root)
        require(self.root.is_absolute() and self.root.is_dir(), "publication-binding-invalid")
        self.publication_effect = "not-started"
        self.report_directory = None
        self.report_run_id = None
        self.source_gate = False

    def run(self, argv, timeout=30):
        try:
            result = subprocess.run(argv, cwd=self.root, capture_output=True, text=True, timeout=timeout, check=False,
                                    env={**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1"})
        except (OSError, UnicodeError, subprocess.SubprocessError):
            raise PublicationFailure("publication-observation-unavailable") from None
        require(result.returncode == 0, "publication-command-not-confirmed")
        return result.stdout.strip()

    def aws(self, *parts):
        output = self.run(["aws", *parts, "--region", self.binding.region, "--output", "json", "--cli-connect-timeout", "5", "--cli-read-timeout", "20"])
        try:
            return json.loads(output)
        except (TypeError, json.JSONDecodeError):
            raise PublicationFailure("publication-provider-observation-invalid") from None

    def source_selection(self):
        binding = self.binding
        path = self.root / "infra/04.deploy/03.product/targets" / binding.target / "40-package-custody/github-actions/pipeline-index.yml"
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise PublicationFailure("publication-source-catalogue-unavailable") from None
        try:
            spec = importlib.util.spec_from_file_location("publication_source_document", Path(__file__).with_name("cloudformation-template.py"))
            document = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(document)
            catalogue = document.template(raw)
        except (ImportError, OSError, ValueError, TypeError, AttributeError):
            raise PublicationFailure("publication-source-catalogue-invalid") from None
        rows = catalogue.get("pipelines")
        require(catalogue.get("schema") == "deploy/pipeline-index/v1" and catalogue.get("target") == binding.target
                and isinstance(rows, list) and all(isinstance(row, dict) for row in rows), "publication-source-catalogue-invalid")
        selected = [row for row in rows if row.get("id") == binding.pipeline]
        require(len(selected) == 1, "publication-source-binding-mismatch")
        pipeline = selected[0]
        acquisition = pipeline.get("custody_acquisition")
        require(pipeline.get("type") == "package-publication" and pipeline.get("trigger") == "workflow_dispatch"
                and pipeline.get("executable_workflow") == ".github/workflows/" + binding.workflow
                and pipeline.get("provider_identity") == binding.role and pipeline.get("package_destination") == binding.repository
                and pipeline.get("provider_region_alias") == "aws-" + binding.region
                and pipeline.get("approval") == "github-environment:" + binding.target
                and isinstance(acquisition, dict) and acquisition.get("source_repository") == binding.source_repository,
                "publication-source-binding-mismatch")
        return source_policy(pipeline)

    def source_context(self, env):
        binding = self.binding
        approved = self.source_selection()
        actual = env.get("GITHUB_REF")
        workflow = binding.source_repository + "/.github/workflows/" + binding.workflow + "@" + (actual if isinstance(actual, str) else "")
        require(env.get("GITHUB_ACTIONS") == "true" and env.get("GITHUB_REPOSITORY") == binding.source_repository
                and actual in approved["allowed"] and env.get("GITHUB_WORKFLOW_REF") == workflow, "publication-source-route-invalid")
        source, run_id = env.get("GITHUB_SHA", ""), env.get("GITHUB_RUN_ID", "")
        require(re.fullmatch(r"[a-f0-9]{40}", source) is not None and re.fullmatch(r"[1-9][0-9]{0,19}", run_id) is not None, "publication-source-identity-invalid")
        return source, run_id

    def context(self, env):
        source, run_id = self.source_context(env)
        binding = self.binding
        require(env.get("ECR_REPOSITORY") == binding.repository and env.get("ECR_URI") == binding.uri and env.get("AWS_REGION") == binding.region, "publication-destination-invalid")
        directory = Path(env.get("RUNNER_TEMP", ""))
        require(directory.is_absolute() and directory.is_dir() and not directory.is_symlink() and not any(part.is_symlink() for part in directory.parents), "publication-path-invalid")
        return source, run_id, directory

    def identity(self):
        binding = self.binding
        caller = self.aws("sts", "get-caller-identity")
        role = r"arn:aws:sts::" + binding.account + r":assumed-role/" + re.escape(binding.role) + r"/[A-Za-z0-9+=,.@_-]+"
        require(isinstance(caller, dict) and caller.get("Account") == binding.account and isinstance(caller.get("Arn"), str) and re.fullmatch(role, caller["Arn"]) is not None, "publication-publisher-identity-invalid")
        repository_identity(lambda service, operation, **arguments: self.aws(service, operation, "--repository-names", *arguments["repositoryNames"]),
                            account=binding.account, region=binding.region, repository=binding.repository)

    def qualified(self, directory, image):
        command = ["python3", "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py", "verify", "--image", image, "--receipt", str(directory / "qualified-image.json")]
        for binding in self.binding.configuration:
            command.extend(["--configuration-input", *binding])
        value = self.run(command)
        require(re.fullmatch(r"sha256:[a-f0-9]{64}", value) is not None, "publication-qualified-image-invalid")
        return value

    def publish(self, operation, env):
        require(operation in {"reserve", "publish", "reconcile"}, "publication-operation-invalid")
        source, run_id, directory = self.context(env)
        self.report_directory, self.report_run_id = directory, run_id
        invoked_path = directory / (self.binding.artifact_stem + "-publication-invoked.json")
        # A rejected duplicate must not relabel the earlier push as unstarted.
        self.publication_effect = "unknown" if operation == "reconcile" or invoked_path.exists() or invoked_path.is_symlink() else "not-started"
        self.identity()
        binding = self.binding
        reservation_path = directory / (binding.artifact_stem + "-publication-reservation.json")
        schema = "deploy/" + binding.artifact_stem + "-publication-reservation/v1"
        tag = binding.tag_prefix + "-" + source[:12] + "-run" + run_id
        if operation == "reserve":
            image_id = self.qualified(directory, binding.local_image)
            revision = self.run(["docker", "image", "inspect", image_id, "--format", '{{ index .Config.Labels "org.opencontainers.image.revision" }}'])
            require(revision == source, "publication-qualified-source-mismatch")
            exclusive(reservation_path, {"schema": schema, "source_revision": source, "run_id": run_id, "image_id": image_id, "repository": binding.repository, "tag": tag})
            return {"verdict": "reserved", "source_revision": source, "publication_performed": False}
        require(not reservation_path.is_symlink(), "publication-path-invalid")
        reservation = json.loads(reservation_path.read_text())
        require(isinstance(reservation, dict) and set(reservation) == {"schema", "source_revision", "run_id", "image_id", "repository", "tag"} and reservation.get("schema") == schema and reservation.get("source_revision") == source and reservation.get("run_id") == run_id and reservation.get("repository") == binding.repository and reservation.get("tag") == tag and isinstance(reservation.get("image_id"), str) and re.fullmatch(r"sha256:[a-f0-9]{64}", reservation["image_id"]) is not None, "publication-reservation-mismatch")
        if operation == "publish":
            require(self.qualified(directory, binding.local_image) == reservation["image_id"], "publication-qualified-image-mismatch")
            # Durable intent prevents a second push, including after a lost response.
            exclusive(invoked_path, reservation)
            self.run(["docker", "tag", reservation["image_id"], binding.uri + ":" + tag])
            self.publication_effect = "unknown"
            self.run(["docker", "push", binding.uri + ":" + tag], timeout=600)
        response = self.aws("ecr", "describe-images", "--repository-name", binding.repository, "--image-ids", "imageTag=" + tag)
        images = response.get("imageDetails") if isinstance(response, dict) else None
        require(isinstance(images, list) and len(images) == 1, "publication-remote-image-not-confirmed")
        image = images[0]
        digest = image.get("imageDigest") if isinstance(image, dict) else None
        tags = image.get("imageTags") if isinstance(image, dict) else None
        require(isinstance(digest, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is not None and isinstance(tags, list) and all(isinstance(item, str) for item in tags) and tag in tags and image.get("repositoryName") == binding.repository, "publication-remote-image-not-confirmed")
        reference = binding.uri + "@" + digest
        self.run(["docker", "pull", reference], timeout=180)
        require(self.qualified(directory, reference) == reservation["image_id"], "publication-remote-image-mismatch")
        revision = self.run(["docker", "image", "inspect", reference, "--format", '{{ index .Config.Labels "org.opencontainers.image.revision" }}'])
        require(revision == source, "publication-remote-source-mismatch")
        output = Path(env.get("GITHUB_OUTPUT", ""))
        require(output.is_absolute() and output.is_file() and not output.is_symlink() and not any(part.is_symlink() for part in output.parents), "publication-output-path-invalid")
        with output.open("a") as stream:
            stream.write("digest=" + digest + "\ntag=" + tag + "\n")
        return {"verdict": "passed", "source_revision": source, "image_digest": digest, "tag": tag, "qualification_evidence": False}

    def main(self):
        parser = argparse.ArgumentParser(add_help=False)
        parser.error = lambda _message: parser.exit(2, self.binding.error_prefix + "_PUBLICATION_ARGUMENTS_INVALID\n")
        parser.add_argument("--operation", choices=["validate-source", "reserve", "publish", "reconcile"], required=True)
        args, unknown = parser.parse_known_args()
        require(not unknown, "publication-arguments-invalid")
        self.source_gate = args.operation == "validate-source"
        if self.source_gate:
            self.source_context(os.environ)
            result = {"verdict": "passed", "publication_performed": False, "qualification_evidence": False}
        else:
            result = self.publish(args.operation, os.environ)
        print(json.dumps({"schema": "deploy/" + self.binding.artifact_stem + "-publication-result/v1", **result}, sort_keys=True))
        return 0

    def execute(self):
        try:
            return self.main()
        except (PublicationFailure, OSError, ValueError, TypeError, KeyError, AttributeError) as failure:
            collection = "not-started"
            binding = self.binding
            if self.report_directory is not None and not self.source_gate:
                try:
                    captured = subprocess.run(["python3", "scripts/04.deploy/shared/deployment-operation-diagnostics.py", "record",
                        "--target", binding.target, "--scope", binding.scope, "--operation-id", binding.artifact_stem + "-publication-" + self.report_run_id,
                        "--stage", "package", "--original-code", binding.error_prefix + "_PUBLICATION_NOT_CONFIRMED", "--exit-status", "1",
                        "--outcome", "unknown" if self.publication_effect == "unknown" else "rejected", "--classification", "child-command-failed",
                        "--evidence-reference", "github-actions-run:" + self.report_run_id, "--next-decision", "inspect-retained-evidence",
                        "--report", str(self.report_directory / (binding.artifact_stem + "-publication-operation.json"))], cwd=self.root, capture_output=True, timeout=30, check=False)
                    collection = "collected" if captured.returncode == 0 else "failed"
                except (OSError, subprocess.SubprocessError):
                    collection = "failed"
            print(json.dumps({"schema": "deploy/" + binding.artifact_stem + "-publication-result/v1", "verdict": "failed",
                              "code": binding.error_prefix + "_PUBLICATION_NOT_CONFIRMED",
                              "condition": failure.code if isinstance(failure, PublicationFailure) else "publication-boundary-failed",
                              "effect": "not-started" if self.source_gate else self.publication_effect, "diagnostic_collection": collection,
                              "next_action": "inspect-approved-publication-source" if self.source_gate else "reconcile-reserved-publication-no-push-replay"}), file=sys.stderr)
            return 1
