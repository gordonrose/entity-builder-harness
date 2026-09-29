#!/usr/bin/env python3
"""Observe external action declarations without loading or executing actions."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.action-observations
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind action inputs and inherited workflow context without claiming remote implementation proof.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.release-control.operation-inventory
#     path: scripts/04.deploy/release-control/discovery/operation_inventory.py

from pathlib import Path
import re

from caller_inventory import CallerCollector, WORKFLOW_PATH, safe_path
from source_inventory import SourceFailure, canonical, digest

MAX_ACTION_OBSERVATIONS = 10000
MAX_INPUTS = 1024
REMOTE_ACTION = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*"
    r"(?:/[A-Za-z0-9_.-]+)*@([A-Za-z0-9_.\-/]+)\Z"
)
COMMIT = re.compile(r"[0-9a-fA-F]{40}\Z")
EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)
STEP_OUTPUT = re.compile(r"\bsteps(?:\s*\.|\s*\[)")


def action_observations(graph, workflow_source, document):
    """Observe a safely parsed workflow against its independently collected graph.

    Inputs are trusted collector structures, not evidence admission. Source-wide
    inconsistencies raise only fixed diagnostics for the enclosing collector.
    Values and input names never leave this function; observations contain hashes.
    """
    source_id = workflow_source["id"]
    if (workflow_source not in graph["sources"]
            or workflow_source["path"] != graph["entrypoint"]["path"]):
        raise SourceFailure("action-source-stale")
    if (not isinstance(document, dict) or not isinstance(document.get("jobs"), dict)
            or not document["jobs"]):
        raise SourceFailure("action-source-invalid")
    nodes = {node["id"]: node for node in graph["nodes"]}
    observations, findings = {}, set()

    def issue(subject_id, code):
        findings.add((subject_id, code))

    def observe(subject_id, kind, locator, detail):
        identity = digest(canonical([subject_id, source_id, kind, locator]))
        if identity not in observations and len(observations) >= MAX_ACTION_OBSERVATIONS:
            raise SourceFailure("action-limit-exceeded")
        observations[identity] = {
            "id": identity, "subject_id": subject_id, "source_id": source_id,
            "kind": kind, "locator_digest": digest(canonical(locator)),
            "detail_digest": digest(canonical(detail)),
        }

    def upstream(subject_id, value):
        pending = [([], value)]
        while pending:
            locator, item = pending.pop()
            if isinstance(item, dict):
                pending.extend((locator + [key], child) for key, child in item.items())
            elif isinstance(item, list):
                pending.extend((locator + [index], child) for index, child in enumerate(item))
            elif isinstance(item, str):
                for index, expression in enumerate(EXPRESSION.finditer(item)):
                    if STEP_OUTPUT.search(expression.group(1)):
                        observe(subject_id, "action-upstream-output", locator + [index], expression.group(0))

    def action(job, step, locator, reusable=False):
        subject_id = digest(canonical([source_id, "workflow-step", locator]))
        node = nodes.get(subject_id)
        if node is None or node["source_id"] != source_id or node["kind"] != "workflow-step":
            raise SourceFailure("action-subject-missing")
        if (node["locator_digest"] != digest(canonical(locator))
                or node["detail_digest"] != digest(canonical(step))):
            raise SourceFailure("action-source-stale")
        issue(subject_id, "action-defaults-unresolved")
        issue(subject_id, "action-implementation-unresolved")
        reference = step["uses"]
        observe(subject_id, "action-reference", ["uses"], reference)
        if "run" in step or reusable and "steps" in step:
            issue(subject_id, "action-shape-invalid")
        if not isinstance(reference, str) or not reference:
            issue(subject_id, "action-reference-invalid")
        elif reference.startswith(("./", "docker://")) or "${{" in reference:
            issue(subject_id, "action-reference-unsupported")
        else:
            remote = REMOTE_ACTION.fullmatch(reference)
            if remote is None or any(part in (".", "..") for part in reference.split("@")[0].split("/")):
                issue(subject_id, "action-reference-invalid")
            elif not COMMIT.fullmatch(remote.group(1)):
                issue(subject_id, "mutable-action-reference")

        inputs = step.get("with", {})
        observe(subject_id, "action-input-set", ["with"], {
            "present": "with" in step, "keys": sorted(inputs) if isinstance(inputs, dict) else None,
            "invalid_digest": digest(canonical(inputs)) if not isinstance(inputs, dict) else None,
        })
        if not isinstance(inputs, dict):
            issue(subject_id, "action-input-shape-invalid")
        elif len(inputs) > MAX_INPUTS:
            issue(subject_id, "action-limit-exceeded")
        else:
            for key, value in sorted(inputs.items()):
                if not isinstance(key, str) or not key or type(value) not in (str, int, bool):
                    issue(subject_id, "action-input-shape-invalid")
                kind = "action-input-expression" if isinstance(value, str) and "${{" in value else "action-input-literal"
                observe(subject_id, kind, ["with", key], value)

        context = {
            "workflow": {key: value for key, value in document.items() if key != "jobs"},
            "job": {key: value for key, value in job.items() if key != "steps"},
            "step": {key: value for key, value in step.items() if key not in ("uses", "with")},
            "declared_overrides": {
                scope: {key: {"present": key in value, "value": value.get(key)}
                        for key in ("permissions", "env", "if", "defaults", "environment")}
                for scope, value in (("workflow", document), ("job", job), ("step", step))
            },
        }
        observe(subject_id, "action-context", ["context"], context)
        observe(subject_id, "action-condition", ["if"], {"present": "if" in step, "value": step.get("if")})
        upstream(subject_id, {"context": context, "with": inputs})

    for job_name, job in document["jobs"].items():
        if not isinstance(job, dict):
            raise SourceFailure("action-source-invalid")
        if "uses" in job:
            action(job, job, ["jobs", job_name], reusable=True)
        steps = job.get("steps", [])
        if not isinstance(steps, list):
            raise SourceFailure("action-source-invalid")
        for index, step in enumerate(steps):
            if isinstance(step, dict) and "uses" in step:
                action(job, step, ["jobs", job_name, "steps", index])
    return (sorted(observations.values(), key=lambda row: row["id"]),
            [{"subject_id": subject_id, "code": code} for subject_id, code in sorted(findings)])


def observe_actions(root: Path, workflow_path: str, graph: dict):
    """Read no-follow repository bytes; reject a graph from different source bytes."""
    root = Path(root).absolute()
    try:
        valid_root = not root.is_symlink() and root.resolve() == root and root.is_dir()
    except (OSError, RuntimeError):
        valid_root = False
    if (not isinstance(workflow_path, str) or not WORKFLOW_PATH.fullmatch(workflow_path)
            or not safe_path(workflow_path) or not valid_root):
        raise SourceFailure("action-source-invalid")
    reader = CallerCollector(root)
    source, raw, code = reader.read(workflow_path)
    if code:
        raise SourceFailure("action-source-invalid")
    root_id = graph["entrypoint"]["node_id"]
    document = reader.parse_document(source, raw, root_id)
    if document is None:
        raise SourceFailure("action-source-invalid")
    return action_observations(graph, source, document)
