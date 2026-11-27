#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.helper.package-custody-github-artifact
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [security, sre]
#   kind: script
#   purpose: Authenticate selected package documents against their successful main workflow and immutable GitHub artifact without extracting files.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, network]
#   used_by:
#   - id: deploy.capability.scheduling-control
#     path: scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py
"""Read-only provenance; callers retain package-specific qualification rules."""
from datetime import datetime
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import zipfile
import zlib

MAX_ARCHIVE = 16 * 1024 * 1024
MAX_DOCUMENT = 2 * 1024 * 1024


class ArtifactFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(value, code):
    if not value:
        raise ArtifactFailure(code)


def api(path):
    """Fixed host and GET: no token, URL, response body or stderr is reported."""
    try:
        result = subprocess.run(["gh", "api", "--hostname", "github.com", "--method", "GET", path],
            capture_output=True, timeout=45, check=False,
            env={**os.environ, "GH_PROMPT_DISABLED": "1", "GH_DEBUG": ""})
    except (OSError, subprocess.SubprocessError):
        raise ArtifactFailure("custody-publication-read-unavailable") from None
    require(result.returncode == 0, "custody-publication-read-unavailable")
    require(len(result.stdout) <= MAX_ARCHIVE, "custody-publication-response-too-large")
    return result.stdout


def document(raw):
    try:
        require(isinstance(raw, bytes) and len(raw) <= MAX_DOCUMENT, "custody-publication-document-invalid")
        value = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise ArtifactFailure("custody-publication-document-invalid") from None
    require(isinstance(value, dict), "custody-publication-document-invalid")
    return value


def timestamp(value):
    try:
        require(isinstance(value, str) and value.endswith("Z"), "custody-publication-time-invalid")
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise ArtifactFailure("custody-publication-time-invalid") from None


def documents(*, repository, workflow, source_revision, run_id, artifact_name, members, get=None):
    get = api if get is None else get
    patterns = ((repository, r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"),
        (workflow, r"[a-z0-9][a-z0-9-]*\.yml"), (source_revision, r"[a-f0-9]{40}"),
        (run_id, r"[1-9][0-9]{0,19}"), (artifact_name, r"[A-Za-z0-9][A-Za-z0-9_.-]{0,199}"))
    require(all(isinstance(value, str) and re.fullmatch(pattern, value) for value, pattern in patterns), "custody-publication-binding-invalid")
    require(isinstance(members, tuple) and bool(members) and len(set(members)) == len(members)
        and all(isinstance(name, str) and re.fullmatch(r"[a-z0-9][a-z0-9.-]*\.json", name) for name in members), "custody-publication-members-invalid")
    prefix = "repos/" + repository + "/actions/"
    run = document(get(prefix + "runs/" + run_id))
    repo, head_repo = run.get("repository"), run.get("head_repository")
    require(isinstance(repo, dict) and isinstance(head_repo, dict) and repo.get("full_name") == repository
        and head_repo.get("full_name") == repository and type(repo.get("id")) is int
        and repo["id"] > 0 and repo["id"] == head_repo.get("id"), "custody-publication-repository-mismatch")
    expected_path = ".github/workflows/" + workflow
    require(type(run.get("id")) is int and run["id"] == int(run_id) and run.get("head_branch") == "main"
        and run.get("head_sha") == source_revision and run.get("path") in {expected_path, expected_path + "@main"}
        and run.get("event") == "workflow_dispatch", "custody-publication-run-mismatch")
    require(run.get("status") == "completed" and run.get("conclusion") == "success", "custody-publication-not-successful")
    # Publishers reserve by run ID, not attempt. Do not combine artifacts from
    # different attempts of that ID or reinterpret a rerun as fresh custody.
    require(type(run.get("run_attempt")) is int and run["run_attempt"] == 1, "custody-publication-attempt-unsupported")
    started, finished = timestamp(run.get("run_started_at")), timestamp(run.get("updated_at"))
    require(started <= finished, "custody-publication-time-invalid")
    listing = document(get(prefix + "runs/" + run_id + "/artifacts?per_page=100"))
    rows = listing.get("artifacts")
    require(isinstance(rows, list) and type(listing.get("total_count")) is int
        and listing["total_count"] == len(rows) <= 100 and all(isinstance(row, dict) for row in rows), "custody-publication-artifact-list-incomplete")
    selected = [row for row in rows if row.get("name") == artifact_name]
    require(len(selected) == 1, "custody-publication-artifact-not-unique")
    artifact = selected[0]
    require(type(artifact.get("id")) is int and artifact["id"] > 0 and artifact.get("expired") is False
        and type(artifact.get("size_in_bytes")) is int and 0 < artifact["size_in_bytes"] <= MAX_ARCHIVE, "custody-publication-artifact-unavailable")
    lineage = artifact.get("workflow_run")
    require(isinstance(lineage, dict) and lineage.get("id") == int(run_id)
        and lineage.get("repository_id") == repo["id"] and lineage.get("head_repository_id") == repo["id"]
        and lineage.get("head_branch") == "main" and lineage.get("head_sha") == source_revision, "custody-publication-artifact-lineage-mismatch")
    require(started <= timestamp(artifact.get("created_at")) <= timestamp(artifact.get("updated_at")) <= finished,
        "custody-publication-artifact-attempt-mismatch")
    digest = artifact.get("digest")
    require(isinstance(digest, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", digest), "custody-publication-artifact-digest-invalid")
    raw = get(prefix + "artifacts/" + str(artifact["id"]) + "/zip")
    require(isinstance(raw, bytes) and len(raw) == artifact["size_in_bytes"] and "sha256:" + hashlib.sha256(raw).hexdigest() == digest,
        "custody-publication-artifact-content-mismatch")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            require(len(names) == len(set(names)) and 0 < len(names) <= 64
                and sum(entry.file_size for entry in entries) <= MAX_ARCHIVE, "custody-publication-archive-invalid")
            for entry in entries:
                require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", entry.filename)
                    and not entry.is_dir() and not entry.flag_bits & 1
                    and not stat.S_ISLNK(entry.external_attr >> 16), "custody-publication-archive-invalid")
            require(set(members).issubset(names), "custody-publication-document-missing")
            require(all(archive.getinfo(name).file_size <= MAX_DOCUMENT for name in members), "custody-publication-document-invalid")
            result = {name: document(archive.read(name)) for name in members}
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, NotImplementedError, zlib.error):
        raise ArtifactFailure("custody-publication-archive-invalid") from None
    return result
