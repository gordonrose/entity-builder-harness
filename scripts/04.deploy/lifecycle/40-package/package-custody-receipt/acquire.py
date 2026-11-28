#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.package-custody-acquisition
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.package-qualification
#   disciplines: [security, sre]
#   kind: script
#   purpose: Acquire exact hosted custody through authenticated run, artifact, signature and immutable image observations without publishing or admitting execution.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network]
#   used_by:
#   - id: deploy.library.aws.environment-sessions
#     path: scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py
#   - id: deploy.test.package-qualification-binding
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification-test.py
"""Read-only custody acquisition; receipt syntax alone never authenticates origin."""
import base64
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import time
from types import SimpleNamespace
import zipfile
import zlib


ROOT = Path(__file__).resolve().parents[5]


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


VALIDATOR = _module("acquisition_receipt", Path(__file__).with_name("validate.py"))
PUBLICATION = _module("acquisition_publication", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/ecr_publication.py")
SCAN = _module("acquisition_scan", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py")
SLSA = "https://slsa.dev/provenance/v1"
JSON_LIMIT, ZIP_LIMIT, RECEIPT_LIMIT = 2 * 1024 * 1024, 32 * 1024 * 1024, 65536
SCAN_CODES = frozenset({"ecr-manifest-identity-mismatch", "ecr-manifest-unavailable", "ecr-manifest-invalid",
    "ecr-manifest-type-unsupported", "ecr-runnable-manifest-ambiguous", "ecr-scan-identity-mismatch",
    "ecr-scan-not-complete", "ecr-scan-findings-invalid", "ecr-scan-blocked-severity"})
PROVIDER_CODES = frozenset({"aws-access-denied", "aws-credentials-expired", "aws-command-timeout",
    "aws-command-unavailable", "aws-response-invalid", "aws-parameter-invalid", "aws-command-failed"})
FAILURE_CODES = frozenset("custody-acquisition-" + reason for reason in {
    "selection-invalid", "json-invalid", "github-unavailable", "response-too-large", "verifier-unavailable",
    "repository-unconfirmed", "run-unconfirmed", "workflow-unconfirmed", "workflow-source-mismatch",
    "artifacts-incomplete", "artifact-unconfirmed", "archive-digest-mismatch", "archive-invalid",
    "receipt-missing", "receipt-invalid", "receipt-region-mismatch", "receipt-origin-mismatch",
    "provenance-unconfirmed", "provenance-origin-mismatch", "provenance-subject-mismatch",
    "provider-unavailable", "publication-binding-invalid", "publication-repository-not-confirmed",
    "image-repository-mismatch", "image-unconfirmed", "origin-changed", "observation-invalid",
    *SCAN_CODES, *PROVIDER_CODES})


class AcquisitionFailure(Exception):
    """Finite acquisition cause, never command output, credentials or locations."""
    def __init__(self, reason):
        code = "custody-acquisition-" + reason if isinstance(reason, str) else ""
        self.code = code if code in FAILURE_CODES else "custody-acquisition-observation-invalid"
        super().__init__(self.code)


def _require(valid, reason):
    if not valid: raise AcquisitionFailure(reason)


def _matches(value, pattern):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _positive(value):
    return type(value) is int and 0 < value < 10 ** 20


def _json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            _require(key not in result, "json-invalid")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(AcquisitionFailure("json-invalid")))
    except (ValueError, UnicodeError, RecursionError):
        raise AcquisitionFailure("json-invalid") from None


def _command(arguments, *, limit=JSON_LIMIT, timeout=45, reason="github-unavailable"):
    """Bound actual child output while reading; do not retain stderr or retry."""
    environment = {**os.environ, "GH_HOST": "github.com", "GH_PROMPT_DISABLED": "1", "GH_PAGER": "cat", "GH_DEBUG": ""}
    try:
        with subprocess.Popen(["gh", *arguments], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, env=environment) as child:
            try:
                chunks, size, deadline = [], 0, time.monotonic() + timeout
                with selectors.DefaultSelector() as selected:
                    selected.register(child.stdout, selectors.EVENT_READ)
                    while True:
                        remaining = deadline - time.monotonic()
                        _require(remaining > 0, reason)
                        _require(bool(selected.select(remaining)), reason)
                        chunk = os.read(child.stdout.fileno(), min(65536, limit + 1 - size))
                        if not chunk: break
                        size += len(chunk)
                        _require(size <= limit, "response-too-large")
                        chunks.append(chunk)
                _require(child.wait(timeout=max(0.01, deadline - time.monotonic())) == 0, reason)
                return b"".join(chunks)
            except BaseException:
                child.kill()
                child.wait()
                raise
    except AcquisitionFailure: raise
    except (OSError, ValueError, subprocess.SubprocessError):
        raise AcquisitionFailure(reason) from None


def _api(path, *, binary=False, limit=JSON_LIMIT):
    raw = _command(["api", "--hostname", "github.com", "--method", "GET", "-H", "Accept: application/vnd.github+json",
                    "-H", "X-GitHub-Api-Version: 2022-11-28", path], limit=limit)
    return raw if binary else _json(raw)


def _selection(publication, run_id, source):
    patterns = {key: r"[a-z][a-z0-9-]{1,95}" for key in ("target", "candidate", "package", "program", "pipeline")}
    patterns.update(account=r"[0-9]{12}", region=r"[a-z]{2}(?:-[a-z]+)+-[0-9]+",
        repository=r"[a-z0-9]+(?:[._/-][a-z0-9]+)*", repository_uri=r"[A-Za-z0-9./_-]{1,512}",
        repository_arn=r"[A-Za-z0-9:/_-]{1,512}", source_repository=r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9_-][A-Za-z0-9_.-]{0,99}",
        workflow=r"\.github/workflows/[A-Za-z0-9_-][A-Za-z0-9_.-]{0,120}\.ya?ml",
        source_ref=r".+", artifact_prefix=r"[A-Za-z0-9][A-Za-z0-9_.-]{0,199}-",
        receipt_member=r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.json", workflow_sha256=r"[a-f0-9]{64}")
    _require(isinstance(publication, dict) and set(publication) == set(patterns)
             and all(_matches(publication[key], pattern) for key, pattern in patterns.items()), "selection-invalid")
    _require(_positive(run_id) and _matches(source, r"[a-f0-9]{40}"), "selection-invalid")
    try:
        PUBLICATION.source_ref(publication["source_ref"])
    except PUBLICATION.PublicationFailure:
        raise AcquisitionFailure("selection-invalid") from None
    p = copy.deepcopy(publication)
    uri = p["account"] + ".dkr.ecr." + p["region"] + ".amazonaws.com/" + p["repository"]
    arn = "arn:aws:ecr:" + p["region"] + ":" + p["account"] + ":repository/" + p["repository"]
    _require(p["repository_uri"] == uri and p["repository_arn"] == arn, "selection-invalid")
    return p


def _run(p, run_id, source, repository_id):
    run = _api("repos/" + p["source_repository"] + "/actions/runs/" + str(run_id))
    _require(isinstance(run, dict) and run.get("id") == run_id and _positive(run.get("id"))
             and _positive(run.get("run_attempt")) and _positive(run.get("workflow_id"))
             and run.get("path") == p["workflow"] and run.get("head_sha") == source
             and run.get("head_branch") == p["source_ref"].removeprefix("refs/heads/") and run.get("event") == "workflow_dispatch"
             and run.get("status") == "completed" and run.get("conclusion") == "success", "run-unconfirmed")
    for key in ("repository", "head_repository"):
        row = run.get(key)
        _require(isinstance(row, dict) and type(row.get("id")) is int and row["id"] == repository_id
                 and row.get("full_name") == p["source_repository"], "run-unconfirmed")
    return {key: run[key] for key in ("id", "run_attempt", "workflow_id", "path", "head_sha", "head_branch", "event", "status", "conclusion")}


def _artifact(p, run_id, source, repository_id):
    rows, seen, total = [], set(), None
    for page in range(1, 11):
        result = _api("repos/" + p["source_repository"] + "/actions/runs/" + str(run_id) + "/artifacts?per_page=100&page=" + str(page))
        _require(isinstance(result, dict) and type(result.get("total_count")) is int and 0 <= result["total_count"] <= 1000
                 and isinstance(result.get("artifacts"), list) and len(result["artifacts"]) <= 100, "artifacts-incomplete")
        total = result["total_count"] if total is None else total
        _require(result["total_count"] == total, "artifacts-incomplete")
        for row in result["artifacts"]:
            _require(isinstance(row, dict) and _positive(row.get("id")) and row["id"] not in seen
                     and isinstance(row.get("name"), str), "artifacts-incomplete")
            seen.add(row["id"]); rows.append(row)
        _require(len(rows) <= total and (result["artifacts"] or len(rows) == total), "artifacts-incomplete")
        if len(rows) == total: break
    _require(len(rows) == total, "artifacts-incomplete")
    selected = [row for row in rows if row["name"] == p["artifact_prefix"] + str(run_id)]
    _require(len(selected) == 1, "artifact-unconfirmed")
    artifact = selected[0]
    _require(artifact.get("expired") is False and type(artifact.get("size_in_bytes")) is int
             and 0 < artifact["size_in_bytes"] <= ZIP_LIMIT and _matches(artifact.get("digest"), r"sha256:[a-f0-9]{64}"), "artifact-unconfirmed")
    binding = artifact.get("workflow_run")
    _require(isinstance(binding, dict) and all(type(binding.get(key)) is int and binding[key] == value
             for key, value in (("id", run_id), ("repository_id", repository_id), ("head_repository_id", repository_id)))
             and binding.get("head_sha") == source and binding.get("head_branch") == p["source_ref"].removeprefix("refs/heads/"), "artifact-unconfirmed")
    return {key: artifact[key] for key in ("id", "name", "size_in_bytes", "digest", "expired", "workflow_run")}


def _receipt(raw, member):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries, names, total = archive.infolist(), set(), 0
            _require(0 < len(entries) <= 1024, "archive-invalid")
            for entry in entries:
                name = entry.filename
                _require(name == entry.orig_filename and name not in names and _matches(name, r"[A-Za-z0-9_./-]{1,512}")
                         and not name.startswith("/") and all(part not in {"", ".", ".."} for part in name.rstrip("/").split("/"))
                         and not entry.flag_bits & 1 and entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                         and stat.S_IFMT(entry.external_attr >> 16) in (0, stat.S_IFREG, stat.S_IFDIR), "archive-invalid")
                names.add(name); total += entry.file_size
                _require(total <= 64 * 1024 * 1024, "archive-invalid")
            _require(member in names, "receipt-missing")
            selected = archive.getinfo(member)
            _require(not selected.is_dir() and 0 < selected.file_size <= RECEIPT_LIMIT, "receipt-invalid")
            with archive.open(selected) as stream: receipt = stream.read(RECEIPT_LIMIT + 1)
            _require(len(receipt) == selected.file_size, "receipt-invalid")
            return _json(receipt), hashlib.sha256(receipt).hexdigest()
    except AcquisitionFailure: raise
    except (OSError, ValueError, RuntimeError, NotImplementedError, zipfile.BadZipFile, zlib.error):
        raise AcquisitionFailure("archive-invalid") from None


def _provenance(p, receipt, run, repository_id):
    source, digest = receipt["source_revision"], receipt["image_digest"]
    raw = _command(["attestation", "verify", "oci://" + p["repository_uri"] + "@" + digest,
                    "--hostname", "github.com", "--repo", p["source_repository"], "--bundle-from-oci",
                    "--signer-workflow", p["source_repository"] + "/" + p["workflow"],
                    "--source-ref", p["source_ref"], "--source-digest", source, "--signer-digest", source,
                    "--predicate-type", SLSA, "--deny-self-hosted-runners", "--format", "json"],
                   limit=4 * 1024 * 1024, timeout=120, reason="provenance-unconfirmed")
    rows = _json(raw)
    _require(isinstance(rows, list) and 0 < len(rows) <= 30, "provenance-unconfirmed")
    repository = "https://github.com/" + p["source_repository"]
    workflow = repository + "/" + p["workflow"] + "@" + p["source_ref"]
    expected = {"issuer": "https://token.actions.githubusercontent.com", "sourceRepositoryURI": repository,
                "sourceRepositoryIdentifier": str(repository_id), "sourceRepositoryDigest": source,
                "sourceRepositoryRef": p["source_ref"], "buildSignerURI": workflow, "buildSignerDigest": source,
                "buildConfigURI": workflow, "buildConfigDigest": source, "buildTrigger": "workflow_dispatch",
                "runnerEnvironment": "github-hosted",
                "runInvocationURI": repository + "/actions/runs/" + str(run["id"]) + "/attempts/" + str(run["run_attempt"])}
    for row in rows:
        result = row.get("verificationResult") if isinstance(row, dict) else None
        _require(isinstance(result, dict), "provenance-unconfirmed")
        certificate = result.get("signature", {}).get("certificate")
        _require(isinstance(certificate, dict) and all(certificate.get(key) == value for key, value in expected.items())
                 and isinstance(result.get("verifiedTimestamps"), list) and bool(result["verifiedTimestamps"]), "provenance-origin-mismatch")
        statement = result.get("statement")
        _require(isinstance(statement, dict) and statement.get("predicateType") == SLSA
                 and statement.get("subject") == [{"name": p["repository_uri"], "digest": {"sha256": digest.removeprefix("sha256:")}}], "provenance-subject-mismatch")
    return hashlib.sha256(raw).hexdigest()


def acquire_custody(*, publication, run_id, expected_source_revision, aws_provider):
    """Return unchanged checked receipt and immutable facts, never an admission."""
    try:
        p = _selection(publication, run_id, expected_source_revision)
        _require(callable(aws_provider), "selection-invalid")
        help_text = _command(["attestation", "verify", "--help"], reason="verifier-unavailable")
        _require(all(flag in help_text for flag in (b"--bundle-from-oci", b"--source-ref", b"--source-digest",
                 b"--signer-workflow", b"--signer-digest", b"--format", b"--deny-self-hosted-runners")), "verifier-unavailable")
        repository = _api("repos/" + p["source_repository"])
        _require(isinstance(repository, dict) and _positive(repository.get("id"))
                 and repository.get("full_name") == p["source_repository"], "repository-unconfirmed")
        repository_id = repository["id"]
        run = _run(p, run_id, expected_source_revision, repository_id)
        workflow = _api("repos/" + p["source_repository"] + "/actions/workflows/" + str(run["workflow_id"]))
        _require(isinstance(workflow, dict) and type(workflow.get("id")) is int and workflow["id"] == run["workflow_id"]
                 and workflow.get("path") == p["workflow"], "workflow-unconfirmed")
        source = _api("repos/" + p["source_repository"] + "/contents/" + p["workflow"] + "?ref=" + expected_source_revision)
        _require(isinstance(source, dict) and source.get("type") == "file" and source.get("path") == p["workflow"]
                 and source.get("encoding") == "base64" and type(source.get("size")) is int and 0 < source["size"] <= 1024 * 1024
                 and isinstance(source.get("content"), str), "workflow-unconfirmed")
        raw = base64.b64decode(source["content"].replace("\n", ""), validate=True)
        _require(len(raw) == source["size"] and hashlib.sha256(raw).hexdigest() == p["workflow_sha256"], "workflow-source-mismatch")
        artifact = _artifact(p, run_id, expected_source_revision, repository_id)
        raw = _api("repos/" + p["source_repository"] + "/actions/artifacts/" + str(artifact["id"]) + "/zip", binary=True, limit=ZIP_LIMIT)
        _require(len(raw) == artifact["size_in_bytes"] and "sha256:" + hashlib.sha256(raw).hexdigest() == artifact["digest"], "archive-digest-mismatch")
        receipt, receipt_digest = _receipt(raw, p["receipt_member"])
        try:
            VALIDATOR.validate(receipt, SimpleNamespace(expected_target=p["target"], expected_candidate=p["candidate"],
                               expected_package_contract=p["package"], expected_program=p["program"]))
        except VALIDATOR.Failure:
            raise AcquisitionFailure("receipt-invalid") from None
        _require(receipt["provider_region_alias"] == "aws-" + p["region"], "receipt-region-mismatch")
        _require(receipt["source_revision"] == expected_source_revision and receipt["receipt_reference"] == "github-actions-run:" + str(run_id), "receipt-origin-mismatch")
        provenance_digest = _provenance(p, receipt, run, repository_id)

        def observed(service, operation, **arguments):
            try: return aws_provider(service, operation, **arguments)
            except Exception as failure:
                code = getattr(failure, "code", None)
                raise AcquisitionFailure(code if code in PROVIDER_CODES else "provider-unavailable") from None

        try:
            identity = PUBLICATION.repository_identity(observed, account=p["account"], region=p["region"], repository=p["repository"])
        except PUBLICATION.PublicationFailure as failure:
            raise AcquisitionFailure(failure.code) from None
        _require(identity == {key: p[key] for key in ("repository", "repository_uri", "repository_arn")}, "image-repository-mismatch")
        try: runnable = SCAN.check_image(observed, p["repository"], receipt["image_digest"])
        except SCAN.ScanFailure as failure:
            code = str(failure)
            raise AcquisitionFailure(code if code in SCAN_CODES else "image-unconfirmed") from None
        _require(_run(p, run_id, expected_source_revision, repository_id) == run
                 and _artifact(p, run_id, expected_source_revision, repository_id) == artifact, "origin-changed")
        evidence = {"source_repository": p["source_repository"], "repository_id": repository_id, "workflow": p["workflow"],
                    "workflow_id": run["workflow_id"], "source_ref": p["source_ref"], "source_revision": expected_source_revision,
                    "run_id": run_id, "run_attempt": run["run_attempt"], "artifact_id": artifact["id"],
                    "artifact_sha256": artifact["digest"], "receipt_sha256": receipt_digest, "workflow_sha256": p["workflow_sha256"],
                    "provenance_sha256": provenance_digest, "image_digest": receipt["image_digest"], "runnable_digest": runnable}
        return {"receipt": receipt, "evidence": tuple(sorted(evidence.items()))}
    except AcquisitionFailure: raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        raise AcquisitionFailure("observation-invalid") from None
