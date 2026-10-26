#!/usr/bin/env python3
"""Collect one persistence acceptance record from independently observed AWS facts."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#   version: 3
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Record persistence-scope acceptance only after AWS independently confirms every required rehearsal task, final workload, recovery-point cleanup, budget, and qualified immutable package identity.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.workflow.govern-scope-lifecycle
#     path: .agentic/04.deploy/60-run/workflows/govern-scope-lifecycle.md
#   effects: [network, writes-files]
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
from functools import lru_cache

import yaml


ROOT = Path(__file__).resolve().parents[8]
IMPLEMENTATION_ROOT = ROOT
EVIDENCE_CLASS = "live"
PROFILE, REGION, ACCOUNT = "kanbien-dev", "eu-west-1", "337159794548"
TARGET, SCOPE, CLUSTER = "kanbien-core-platform", "core-server-persistence", "kanbien-core-platform"
STACK = "kanbien-core-platform-core-server-persistence"
SERVICE = "kanbien-core-platform-core-server-persistence"
DATABASE = "kanbien-core-platform-persistence"
LOG_GROUP = "/aws/ecs/kanbien-core-platform"
RECORD = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/accepted-release.yml"
# The collector and retained-receipt validator use one target-owned durable
# evidence root.  Tests and controllers must not infer a second location.
EVIDENCE_ROOT = RECORD.parent
TASK_ARN = re.compile(rf"^arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/[0-9a-f]{{32}}$")
SNAPSHOT = re.compile(r"^kanbien-core-platform-persistence-recovery-[0-9]{8}(?:-[a-z0-9]{1,8})?$")
TASKS: dict[str, dict[str, Any]] = {}


class EvidenceFailure(Exception):
    pass


def succession_module():
    """Load the one generic release-succession authority; do not fork it."""
    path = IMPLEMENTATION_ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py"
    spec = importlib.util.spec_from_file_location("release_succession", path)
    value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(value)
    value.REPOSITORY_ROOT = ROOT
    value.EVIDENCE_CLASS = EVIDENCE_CLASS
    return value


def candidate_record(package: dict[str, str], proofs: dict[str, dict[str, str]], accepted_at: str, retained: dict[str, Path] | None = None) -> tuple[Path, dict[str, Any]]:
    """Build, but do not publish, a succession-compatible candidate record.

    Publishing remains the generic succession controller's responsibility.  A
    candidate is bound to the two target-owned contracts and hashes of the
    already validated retained receipts, so a later acceptance cannot silently
    substitute proof files or contract revisions.
    """
    succession = succession_module()
    source_revision = package.get("source_revision")
    image_digest = package.get("image_digest")
    if not isinstance(source_revision, str) or not re.fullmatch(r"[a-f0-9]{40}", source_revision) or not isinstance(image_digest, str) or re.fullmatch(r"sha256:[a-f0-9]{64}", image_digest) is None:
        raise EvidenceFailure("acceptance-evidence-package-receipt-invalid")
    receipt_set: dict[str, dict[str, str]] = {}
    for name, binding in proofs.items():
        relative = binding.get("receipt") if isinstance(binding, dict) else None
        if not isinstance(name, str) or not name or not isinstance(relative, str):
            raise EvidenceFailure("acceptance-evidence-proof-reference-invalid")
        path = (ROOT / relative).resolve()
        try:
            evidence_relative = path.relative_to(EVIDENCE_ROOT.resolve())
            path.relative_to(EVIDENCE_ROOT.resolve() / "proof-receipts")
            raw = path.read_bytes()
        except (OSError, ValueError):
            raise EvidenceFailure("acceptance-evidence-proof-reference-invalid") from None
        # Generic release succession owns an evidence-root-relative proof set;
        # the target collector's observed record may use repository-relative
        # paths, but those are not meaningful to the generic controller.
        receipt_set[name] = {"path": evidence_relative.as_posix(), "sha256": succession.sha256_bytes(raw)}
    for name, source in (retained or {}).items():
        if not isinstance(name, str) or not name or not isinstance(source, Path):
            raise EvidenceFailure("acceptance-evidence-retained-reference-invalid")
        try:
            path = source.resolve()
            relative = path.relative_to(EVIDENCE_ROOT.resolve())
            succession.retained_evidence_file(EVIDENCE_ROOT, path)
            raw = path.read_bytes()
        except (OSError, ValueError, succession.SuccessionFailure):
            raise EvidenceFailure("acceptance-evidence-retained-reference-invalid") from None
        if name in receipt_set:
            raise EvidenceFailure("acceptance-evidence-retained-reference-invalid")
        receipt_set[name] = {"path": relative.as_posix(), "sha256": succession.sha256_bytes(raw)}
    if not receipt_set:
        raise EvidenceFailure("acceptance-evidence-proof-reference-invalid")
    contract_paths = {
        "configuration_contract": "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml",
        "permission_contract": "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml",
    }
    contracts: dict[str, dict[str, str]] = {}
    for key, relative in contract_paths.items():
        try:
            contracts[key] = {"path": relative, "sha256": succession.sha256_bytes((ROOT / relative).read_bytes())}
        except OSError as error:
            raise EvidenceFailure("acceptance-evidence-contract-unreadable") from error
    identity = {
        "target": TARGET,
        "scope": SCOPE,
        "source_revision": source_revision,
        "image_digest": image_digest,
        **contracts,
        "proof_set_sha256": succession.sha256_bytes(succession.canonical(receipt_set)),
    }
    value: dict[str, Any] = {
        "schema": succession.CANDIDATE_SCHEMA,
        "evidence_class": EVIDENCE_CLASS,
        "target": TARGET,
        "scope": SCOPE,
        "status": "verified",
        "release": {
            "id": succession.release_id(identity),
            "source_revision": source_revision,
            "image_digest": image_digest,
            **contracts,
            "proof_set_sha256": identity["proof_set_sha256"],
        },
        "proof": {"accepted_at": accepted_at, "receipt_count": len(receipt_set)},
        "proof_set": receipt_set,
    }
    try:
        succession.candidate_identity(value, EVIDENCE_ROOT)
    except succession.SuccessionFailure as error:
        raise EvidenceFailure("acceptance-evidence-candidate-record-invalid") from error
    return EVIDENCE_ROOT / succession.CANDIDATE_DIRECTORY / f"{value['release']['id']}.yml", value


def qualified_rollback_compatibility(rollback: dict[str, str]) -> dict[str, str]:
    """Require the separately archived proof for a qualified rollback image.

    A package receipt alone says the image was qualified.  It cannot establish
    that the image works against the corrected permission/configuration
    boundary.  The generic succession controller owns the immutable archive;
    this target collector only selects the one record whose exact immutable
    identity is the supplied rollback receipt.
    """
    succession = succession_module()
    directory = EVIDENCE_ROOT / succession.COMPATIBILITY_DIRECTORY
    matches: list[tuple[Path, dict[str, Any]]] = []
    try:
        candidates = sorted(directory.glob("rollback-compatibility-*.yml"))
    except OSError as error:
        raise EvidenceFailure("acceptance-evidence-rollback-compatibility-unavailable") from error
    for path in candidates:
        try:
            _, observed = succession.compatibility_record(EVIDENCE_ROOT, path.stem)
        except succession.SuccessionFailure as error:
            raise EvidenceFailure("acceptance-evidence-rollback-compatibility-invalid") from error
        identity = observed["identity"]
        predecessor = identity.get("qualified_predecessor") if isinstance(identity, dict) else None
        if not isinstance(predecessor, dict):
            continue
        if predecessor.get("source_revision") == rollback["source_revision"] and predecessor.get("image_digest") == rollback["image_digest"] and predecessor.get("package_custody_reference") == rollback["receipt_reference"]:
            matches.append((path, observed))
    if len(matches) != 1:
        raise EvidenceFailure("acceptance-evidence-rollback-compatibility-missing-or-ambiguous")
    path, observed = matches[0]
    try:
        relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as error:
        raise EvidenceFailure("acceptance-evidence-rollback-compatibility-invalid") from error
    return {"id": path.stem, "path": relative, "sha256": observed["sha256"]}


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value: dict[str, Any] = {"schema": "deploy/persistence-acceptance-collection-report/v1", "target": TARGET, "scope": SCOPE, "verdict": verdict, "findings": [{"code": code} for code in dict.fromkeys(codes)]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict in {"ready", "recorded"} else 1


def aws(*parts: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True, timeout=30, env={**os.environ, "AWS_PAGER": ""}, check=False)
    except subprocess.TimeoutExpired as error:
        raise EvidenceFailure("acceptance-evidence-aws-observation-timeout") from error
    if completed.returncode:
        detail = completed.stderr.lower()
        code = "acceptance-evidence-aws-access-denied" if "accessdenied" in detail or "not authorized" in detail else "acceptance-evidence-aws-observation-failed"
        raise EvidenceFailure(code)
    try:
        parsed = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as error:
        raise EvidenceFailure("acceptance-evidence-aws-response-invalid") from error
    if not isinstance(parsed, dict):
        raise EvidenceFailure("acceptance-evidence-aws-response-invalid")
    return parsed


def receipt(path: Path) -> dict[str, str]:
    command = IMPLEMENTATION_ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceFailure("acceptance-evidence-package-receipt-unreadable") from error
    if not isinstance(candidate, dict):
        raise EvidenceFailure("acceptance-evidence-package-receipt-invalid")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json") as snapshot:
        json.dump(candidate, snapshot)
        snapshot.flush()
        completed = subprocess.run(["bash", str(command), "--receipt", snapshot.name, "--expected-target", TARGET, "--expected-candidate", "kanbien-core-server-persistence-candidate", "--expected-package-contract", "kanbien-core-server-persistence-image", "--expected-program", "kanbien-core-server-persistence", "--json"], capture_output=True, text=True, check=False)
    required = ("source_revision", "image_digest", "receipt_reference")
    if completed.returncode or not all(isinstance(candidate.get(key), str) and candidate[key] for key in required):
        raise EvidenceFailure("acceptance-evidence-package-receipt-invalid")
    digest = candidate["image_digest"]
    if re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is None:
        raise EvidenceFailure("acceptance-evidence-package-receipt-invalid")
    return {key: candidate[key] for key in required}


def parsed_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise EvidenceFailure("acceptance-evidence-task-timestamp-invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise EvidenceFailure("acceptance-evidence-task-timestamp-invalid") from error
    if parsed.tzinfo is None:
        raise EvidenceFailure("acceptance-evidence-task-timestamp-invalid")
    return parsed.astimezone(timezone.utc)


def contract_deadlines() -> dict[str, int]:
    path = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise EvidenceFailure("acceptance-evidence-scope-contract-unreadable") from error
    workloads = document.get("health_recovery", {}).get("workloads") if isinstance(document, dict) else None
    if not isinstance(workloads, list):
        raise EvidenceFailure("acceptance-evidence-scope-contract-invalid")
    deadlines: dict[str, int] = {}
    for workload in workloads:
        if not isinstance(workload, dict) or not isinstance(workload.get("id"), str):
            continue
        completion = workload.get("completion")
        value = completion.get("deadline_seconds") if isinstance(completion, dict) else None
        if workload["id"] in {"private-release-verifier", "persistence-migration", "persistence-administration", "persistence-restoration-verifier"} and type(value) is int and value > 0:
            deadlines[workload["id"]] = value
    if set(deadlines) != {"private-release-verifier", "persistence-migration", "persistence-administration", "persistence-restoration-verifier"}:
        raise EvidenceFailure("acceptance-evidence-scope-contract-invalid")
    return deadlines


@lru_cache(maxsize=8)
def task_definition(arn: str) -> dict[str, Any]:
    response = aws("ecs", "describe-task-definition", "--task-definition", arn)
    definition = response.get("taskDefinition")
    if not isinstance(definition, dict):
        raise EvidenceFailure("acceptance-evidence-task-definition-unavailable")
    return definition


def preload_tasks(arns: list[str]) -> None:
    """Observe the immutable proof set together, not through serial task reads."""
    unique = list(dict.fromkeys(arns))
    if not unique or any(TASK_ARN.fullmatch(arn) is None for arn in unique):
        raise EvidenceFailure("acceptance-evidence-task-identity-invalid")
    response = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", *unique)
    tasks = response.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != len(unique):
        raise EvidenceFailure("acceptance-evidence-task-not-terminal")
    observed = {item.get("taskArn"): item for item in tasks if isinstance(item, dict) and isinstance(item.get("taskArn"), str)}
    if set(observed) != set(unique):
        raise EvidenceFailure("acceptance-evidence-task-not-terminal")
    TASKS.update(observed)


def observed_task(arn: str) -> dict[str, Any]:
    task = TASKS.get(arn)
    if task is None:
        response = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arn)
        tasks = response.get("tasks")
        task = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 and isinstance(tasks[0], dict) else None
        if isinstance(task, dict):
            TASKS[arn] = task
    if not isinstance(task, dict):
        raise EvidenceFailure("acceptance-evidence-task-not-terminal")
    return task


def definition_identity(arn: object, expected_family: str, expected_digest: str) -> None:
    if not isinstance(arn, str):
        raise EvidenceFailure("acceptance-evidence-task-definition-unavailable")
    definition = task_definition(arn)
    containers = definition.get("containerDefinitions")
    if definition.get("taskDefinitionArn") != arn or definition.get("family") != expected_family or not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        raise EvidenceFailure("acceptance-evidence-task-definition-mismatch")
    image = containers[0].get("image")
    if image != f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/kanbien-core-platform/core-server@{expected_digest}":
        raise EvidenceFailure("acceptance-evidence-task-image-mismatch")


def expected_stream(kind: str, task_id: str) -> str:
    prefixes = {"verifier": "persistence-verifier/private-persistence-verifier", "migration": "persistence-migration/persistence-migration", "restore": "persistence-restoration-verifier/persistence-restoration-verifier"}
    return f"{prefixes[kind]}/{task_id}"


def log_has_code(kind: str, arn: str, code: str) -> None:
    task_id = arn.rsplit("/", 1)[-1]
    response = aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", expected_stream(kind, task_id), "--start-from-head")
    events = response.get("events")
    if not isinstance(events, list) or not any(safe_result(event, code) for event in events):
        raise EvidenceFailure("acceptance-evidence-safe-result-code-missing")


def safe_result(event: object, code: str) -> bool:
    if not isinstance(event, dict) or not isinstance(event.get("message"), str): return False
    try:
        value = controller("scripts/04.deploy/shared/deployment-operation-diagnostics.py").validate_verifier_result(json.loads(event["message"]))
    except Exception: return False
    return value["verdict"] == "accepted" and value["code"] == code


def task_fact(name: str, arn: str, kind: str, family: str, digest: str, code: str, deadline: int) -> dict[str, Any]:
    if TASK_ARN.fullmatch(arn) is None:
        raise EvidenceFailure("acceptance-evidence-task-identity-invalid")
    task = observed_task(arn)
    if task is None or task.get("taskArn") != arn or task.get("lastStatus") != "STOPPED":
        raise EvidenceFailure("acceptance-evidence-task-not-terminal")
    containers = task.get("containers")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or type(containers[0].get("exitCode")) is not int or containers[0]["exitCode"] != 0:
        raise EvidenceFailure("acceptance-evidence-task-unsuccessful")
    started, stopped = parsed_time(task.get("startedAt")), parsed_time(task.get("stoppedAt"))
    duration = int((stopped - started).total_seconds())
    if duration < 0 or duration > deadline:
        raise EvidenceFailure("acceptance-evidence-task-deadline-exceeded")
    definition_identity(task.get("taskDefinitionArn"), family, digest)
    log_has_code(kind, arn, code)
    return {"name": name, "task_arn": arn, "task_definition": task["taskDefinitionArn"], "image_digest": digest, "started_at": started.isoformat().replace("+00:00", "Z"), "stopped_at": stopped.isoformat().replace("+00:00", "Z"), "duration_seconds": duration, "result_code": code}


def server_task(arn: str, digest: str) -> dict[str, Any]:
    if TASK_ARN.fullmatch(arn) is None:
        raise EvidenceFailure("acceptance-evidence-server-task-identity-invalid")
    task = observed_task(arn)
    if task is None or task.get("taskArn") != arn or task.get("group") != f"service:{SERVICE}":
        raise EvidenceFailure("acceptance-evidence-server-task-invalid")
    definition_identity(task.get("taskDefinitionArn"), "kanbien-core-platform-core-server-persistence", digest)
    started = parsed_time(task.get("startedAt"))
    stopped = parsed_time(task.get("stoppedAt")) if task.get("lastStatus") == "STOPPED" else None
    return {"task_arn": arn, "task_definition": task["taskDefinitionArn"], "started_at": started, "stopped_at": stopped, "stopped_reason": task.get("stoppedReason")}


def parse_proofs(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if value.count("=") != 1:
            raise EvidenceFailure("acceptance-evidence-proof-argument-invalid")
        name, arn = value.split("=", 1)
        if not name or not arn or name in result:
            raise EvidenceFailure("acceptance-evidence-proof-argument-invalid")
        result[name] = arn
    return result


def receipt_module():
    path = IMPLEMENTATION_ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py"
    specification = importlib.util.spec_from_file_location("persistence_proof_receipts", path)
    module = importlib.util.module_from_spec(specification)
    assert specification and specification.loader
    specification.loader.exec_module(module)
    return module


def observability_receipt_module():
    path = IMPLEMENTATION_ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts.py"
    specification = importlib.util.spec_from_file_location("persistence_observability_receipts", path)
    module = importlib.util.module_from_spec(specification)
    assert specification and specification.loader
    specification.loader.exec_module(module)
    return module


def proof_applicability_module():
    path = IMPLEMENTATION_ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/qualify-proof-applicability/script.py"
    specification = importlib.util.spec_from_file_location("persistence_proof_applicability", path)
    module = importlib.util.module_from_spec(specification)
    assert specification and specification.loader
    specification.loader.exec_module(module)
    return module


def proof_applicability(path: Path | None, candidate: dict[str, str]) -> dict[str, Any] | None:
    """Load a narrowly scoped predecessor-proof reuse decision, if supplied."""
    if path is None:
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceFailure("acceptance-evidence-proof-applicability-unreadable") from error
    try:
        return proof_applicability_module().validate(raw, candidate)
    except (ValueError, OSError) as error:
        raise EvidenceFailure("acceptance-evidence-proof-applicability-invalid") from error


def parse_proof_receipts(values: list[str], required: dict[str, tuple[str, str, str, str, str]], deadlines: dict[str, int], receipt_root: Path | None = None, applicability: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Validate retained controller receipts without re-querying aged ECS tasks."""
    result: dict[str, dict[str, Any]] = {}
    receipt_paths: dict[str, Path] = {}
    root = receipt_root.resolve() if receipt_root is not None else ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts"
    module = receipt_module()
    for value in values:
        if value.count("=") != 1:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-argument-invalid")
        name, raw_path = value.split("=", 1)
        path = Path(raw_path).resolve()
        if not name or name in result or root not in path.parents:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-argument-invalid")
        try:
            item = module.validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-invalid") from error
        if item["provenance"].get("evidence_class", "live") != EVIDENCE_CLASS:
            raise EvidenceFailure("acceptance-evidence-simulation-not-live")
        result[name] = item
        receipt_paths[name] = path
    if set(result) != set(required):
        raise EvidenceFailure("acceptance-evidence-proof-receipt-set-invalid")
    observed: dict[str, dict[str, Any]] = {}
    controllers = {
        "administration": "run-administration",
        "migration": "run-migration",
        "verifier": "verify-candidate",
        "restore": "rehearse-isolated-database-restore",
        "server-replacement": "rehearse-server-replacement",
    }
    operations = {name: proof["operation"] for name, proof in route_contract()["proofs"].items()}
    for name, (kind, family, expected_digest, code, workload) in required.items():
        item = result[name]
        task = item["task"]
        if kind not in controllers or name not in operations:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-mapping-invalid")
        if item["proof_type"] != kind or item["operation"] != operations[name] or task["result_code"] != code or item["provenance"]["controller"] != controllers[kind] or item["provenance"]["collection_method"] != "ecs-terminal-task+task-definition+safe-log":
            raise EvidenceFailure("acceptance-evidence-proof-receipt-mismatch")
        if task["image_digest"] != expected_digest:
            predecessor = applicability.get("predecessor") if isinstance(applicability, dict) else None
            reusable = applicability.get("reused_proofs") if isinstance(applicability, dict) else None
            if not isinstance(predecessor, dict) or not isinstance(reusable, list) or name not in reusable or task["image_digest"] != predecessor.get("image_digest"):
                raise EvidenceFailure("acceptance-evidence-proof-receipt-mismatch")
        replacement = kind == "server-replacement"
        if TASK_ARN.fullmatch(task["arn"]) is None or not isinstance(task["definition"], str) or f":task-definition/{family}:" not in task["definition"] or task["terminal_status"] != "STOPPED" or (not replacement and task["exit_code"] != 0) or (replacement and task.get("stopped_reason") != "governed core-server-persistence replacement rehearsal"):
            raise EvidenceFailure("acceptance-evidence-proof-receipt-terminal-invalid")
        started, stopped = parsed_time(task["started_at"]), parsed_time(task["stopped_at"])
        if parsed_time(item["provenance"]["collected_at"]) < stopped:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-provenance-invalid")
        duration = int((stopped - started).total_seconds())
        if duration < 0 or (workload is not None and duration > deadlines[workload]):
            raise EvidenceFailure("acceptance-evidence-proof-receipt-deadline-exceeded")
        context = item["context"]
        if "completion_duration_seconds" in context and context["completion_duration_seconds"] != duration:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-duration-mismatch")
        if workload is not None and context.get("completion_deadline_seconds") != deadlines[workload]:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-deadline-mismatch")
        if replacement:
            try:
                successor_started = parsed_time(context["successor_started_at"])
                boundary = parsed_time(context["recovery_boundary"])
            except (KeyError, EvidenceFailure) as error:
                raise EvidenceFailure("acceptance-evidence-server-replacement-receipt-invalid") from error
            if context.get("original_stopped_reason") != "governed core-server-persistence replacement rehearsal" or context.get("runtime_task_definition") != task["definition"] or context.get("successor_task_arn") == task["arn"] or successor_started <= started or boundary < started or boundary > stopped:
                raise EvidenceFailure("acceptance-evidence-server-replacement-receipt-invalid")
        try:
            receipt_path = str(receipt_paths[name].relative_to(ROOT))
        except ValueError:  # test-only injected root; production receipts are repo-relative.
            receipt_path = str(receipt_paths[name])
        observed[name] = {"name": name, "task_arn": task["arn"], "task_definition": task["definition"], "image_digest": task["image_digest"], "started_at": task["started_at"], "stopped_at": task["stopped_at"], "duration_seconds": duration, "result_code": task["result_code"], "receipt": receipt_path}
    return observed


def parse_observability_receipts(values: list[str], expected_digest: str, receipt_root: Path | None = None) -> dict[str, dict[str, Any]]:
    """Bind the alert-path receipts to genuine retained verifier proof.

    Historical task lookup is intentionally unnecessary here: the referenced
    verifier receipt captured task identity, immutable image and terminal
    result when it completed.  Current service/database observations remain a
    separate acceptance requirement below.
    """
    module = observability_receipt_module()
    evidence_root = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
    root = receipt_root.resolve() if receipt_root is not None else evidence_root / "observability-receipts"
    proof_root = evidence_root / "proof-receipts"
    required = {"readiness-failure-observed", "readiness-alarm-notified", "readiness-recovery-observed"}
    entries: dict[str, dict[str, Any]] = {}
    locations: dict[str, Path] = {}
    for value in values:
        if value.count("=") != 1:
            raise EvidenceFailure("acceptance-evidence-observability-receipt-argument-invalid")
        name, raw_path = value.split("=", 1)
        path = Path(raw_path).resolve()
        if not name or name in entries or root not in path.parents:
            raise EvidenceFailure("acceptance-evidence-observability-receipt-argument-invalid")
        try:
            item = module.validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise EvidenceFailure("acceptance-evidence-observability-receipt-invalid") from error
        if item["receipt_type"] != name or item["provenance"]["evidence_class"] != EVIDENCE_CLASS:
            raise EvidenceFailure("acceptance-evidence-observability-receipt-mismatch")
        entries[name], locations[name] = item, path
    if set(entries) != required:
        raise EvidenceFailure("acceptance-evidence-observability-receipt-set-invalid")

    source_receipts: dict[str, dict[str, Any]] = {}
    for name, item in entries.items():
        source = item["source_proof"]
        source_path = (ROOT / source["path"]).resolve()
        if proof_root.resolve() not in source_path.parents:
            raise EvidenceFailure("acceptance-evidence-observability-source-invalid")
        try:
            raw = source_path.read_bytes()
            proof = receipt_module().validate(json.loads(raw.decode("utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise EvidenceFailure("acceptance-evidence-observability-source-invalid") from error
        if succession_module().sha256_bytes(raw) != source["sha256"] or proof["provenance"].get("evidence_class", "live") != EVIDENCE_CLASS or proof["proof_type"] != "verifier" or proof["task"]["arn"] != source["task_arn"] or proof["task"]["definition"] != source["task_definition"] or proof["task"]["image_digest"] != source["image_digest"] or proof["task"]["result_code"] != source["result_code"] or source["image_digest"] != expected_digest:
            raise EvidenceFailure("acceptance-evidence-observability-source-invalid")
        source_receipts[name] = proof

    failure, notification, recovery = entries["readiness-failure-observed"], entries["readiness-alarm-notified"], entries["readiness-recovery-observed"]
    if failure["source_proof"]["result_code"] != "KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY" or notification["source_proof"] != failure["source_proof"] or recovery["source_proof"]["result_code"] != "KANBIEN_CORE_PERSISTENCE_HEALTHY":
        raise EvidenceFailure("acceptance-evidence-observability-sequence-invalid")
    if parsed_time(failure["observation"]["metric_observed_at"]) > parsed_time(failure["observation"]["alarm_state_updated_at"]) or parsed_time(notification["observation"]["operator_delivery_confirmed_at"]) < parsed_time(notification["observation"]["alarm_state_updated_at"]) or parsed_time(recovery["observation"]["metric_observed_at"]) < parsed_time(notification["observation"]["operator_delivery_confirmed_at"]) or parsed_time(recovery["observation"]["metric_observed_at"]) > parsed_time(recovery["observation"]["alarm_state_updated_at"]):
        raise EvidenceFailure("acceptance-evidence-observability-sequence-invalid")
    result: dict[str, dict[str, Any]] = {}
    for name, item in entries.items():
        try:
            relative = str(locations[name].relative_to(ROOT))
        except ValueError:
            relative = str(locations[name])
        result[name] = {
            "receipt": relative,
            "sha256": item["integrity"]["payload_sha256"],
            "source_task": item["source_proof"]["task_arn"],
            "source_image_digest": item["source_proof"]["image_digest"],
            "alarm_state": item["observation"]["alarm_state"],
        }
    return result


def stack_outputs() -> dict[str, str]:
    response = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = response.get("Stacks")
    stack = stacks[0] if isinstance(stacks, list) and len(stacks) == 1 and isinstance(stacks[0], dict) else None
    if stack is None or stack.get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        raise EvidenceFailure("acceptance-evidence-runtime-stack-not-stable")
    outputs = stack.get("Outputs")
    result = {item.get("OutputKey"): item.get("OutputValue") for item in outputs if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)} if isinstance(outputs, list) else {}
    required = {"CoreServerPersistenceTaskDefinitionArn", "CoreServerPersistenceVerifierTaskDefinitionArn", "CoreServerPersistenceMigrationTaskDefinitionArn", "CoreServerPersistenceRestorationVerifierTaskDefinitionArn"}
    if not required <= set(result):
        raise EvidenceFailure("acceptance-evidence-runtime-stack-outputs-invalid")
    return result


def controller(relative: str):
    source = IMPLEMENTATION_ROOT / relative
    spec = importlib.util.spec_from_file_location("acceptance_controller", source)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def recovery_controller():
    module = controller("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py")
    module.EVIDENCE_CLASS = EVIDENCE_CLASS
    return module


def qualified_runnable_digest(candidate: dict) -> str:
    prepare = controller("scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py")
    prepare.aws = lambda *parts: (True, aws(*parts), "ok")
    digest, code = prepare.candidate_runnable_manifest(candidate)
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is None: raise EvidenceFailure(code)
    return digest


def inert_server_overrides(task: dict) -> bool:
    value = task.get("overrides", {})
    if not isinstance(value, dict) or set(value) - {"containerOverrides", "inferenceAcceleratorOverrides"}: return False
    if "inferenceAcceleratorOverrides" in value and value["inferenceAcceleratorOverrides"] != []: return False
    containers = value.get("containerOverrides", [])
    return containers == [] or containers == [{"name": "core-server-persistence"}]


def current_service(expected_server_definition: str, candidate: dict, runnable_digest: str) -> dict[str, str]:
    digest = candidate["image_digest"]
    response = aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", SERVICE)
    services = response.get("services")
    service = services[0] if isinstance(services, list) and len(services) == 1 and isinstance(services[0], dict) else None
    deployments = service.get("deployments") if isinstance(service, dict) else None
    if not isinstance(service, dict) or service.get("serviceName") != SERVICE or service.get("status") != "ACTIVE" or type(service.get("desiredCount")) is not int or service.get("desiredCount") != 1 or type(service.get("runningCount")) is not int or service.get("runningCount") != 1 or type(service.get("pendingCount")) is not int or service.get("pendingCount") != 0 or service.get("taskDefinition") != expected_server_definition or not isinstance(deployments, list) or not any(isinstance(item, dict) and item.get("status") == "PRIMARY" and item.get("rolloutState") == "COMPLETED" for item in deployments):
        raise EvidenceFailure("acceptance-evidence-current-service-unhealthy")
    definition_identity(expected_server_definition, "kanbien-core-platform-core-server-persistence", digest)
    definition = task_definition(expected_server_definition)
    container = definition["containerDefinitions"][0]
    environment = container.get("environment")
    sources = [item.get("value") for item in environment if isinstance(item, dict) and item.get("name") == "PLATFORM_SOURCE_COMMIT_SHA"] if isinstance(environment, list) else []
    if container.get("name") != "core-server-persistence" or sources != [candidate["source_revision"]]:
        raise EvidenceFailure("acceptance-evidence-current-source-revision-mismatch")
    response = aws("ecs", "list-tasks", "--cluster", CLUSTER, "--service-name", SERVICE, "--desired-status", "RUNNING")
    arns = response.get("taskArns")
    if not isinstance(arns, list) or len(arns) != 1 or not isinstance(arns[0], str):
        raise EvidenceFailure("acceptance-evidence-current-service-task-invalid")
    task_response = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arns[0])
    tasks = task_response.get("tasks")
    task = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 and isinstance(tasks[0], dict) else None
    if task is None or task.get("lastStatus") != "RUNNING" or task.get("taskDefinitionArn") != expected_server_definition or task.get("taskArn") != arns[0] or task.get("healthStatus") != "HEALTHY":
        raise EvidenceFailure("acceptance-evidence-current-service-task-invalid")
    containers = task.get("containers")
    image = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/kanbien-core-platform/core-server@{digest}"
    if TASK_ARN.fullmatch(arns[0]) is None or task.get("group") != f"service:{SERVICE}" or not inert_server_overrides(task) or not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or containers[0].get("name") != "core-server-persistence" or containers[0].get("image") != image or containers[0].get("imageDigest") not in {digest, runnable_digest}:
        raise EvidenceFailure("acceptance-evidence-current-runtime-identity-mismatch")
    return {"service": SERVICE, "task_definition": expected_server_definition, "running_task": arns[0]}


def current_health(arn: str, definition: str, candidate: dict, runnable_digest: str) -> dict:
    health = task_fact("current-health", arn, "verifier", "kanbien-core-platform-persistence-verifier", candidate["image_digest"], "KANBIEN_CORE_PERSISTENCE_HEALTHY", contract_deadlines()["private-release-verifier"])
    observed = observed_task(arn)
    verifier = controller("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py")
    containers = observed["containers"]
    expected_image = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/kanbien-core-platform/core-server@{candidate['image_digest']}"
    if health["task_definition"] != definition or not verifier.task_operation_bound(observed, "health-ready") or containers[0].get("name") != "private-persistence-verifier" or containers[0].get("image") != expected_image or containers[0].get("imageDigest") not in {candidate["image_digest"], runnable_digest}:
        raise EvidenceFailure("acceptance-evidence-current-health-binding-invalid")
    now = datetime.now(timezone.utc)
    if not now - timedelta(minutes=10) <= parsed_time(health["started_at"]) <= parsed_time(health["stopped_at"]) <= now:
        raise EvidenceFailure("acceptance-evidence-current-health-stale-or-mismatched")
    return health


def database_posture(snapshot_id: str, record_proof: dict) -> dict[str, str]:
    database = aws("rds", "describe-db-instances", "--db-instance-identifier", DATABASE).get("DBInstances")
    instance = database[0] if isinstance(database, list) and len(database) == 1 and isinstance(database[0], dict) else None
    if not isinstance(instance, dict) or instance.get("DBInstanceStatus") != "available" or instance.get("Engine") != "postgres" or instance.get("PubliclyAccessible") is not False or instance.get("StorageEncrypted") is not True or instance.get("DeletionProtection") is not True:
        raise EvidenceFailure("acceptance-evidence-source-database-posture-invalid")
    snapshots = aws("rds", "describe-db-snapshots", "--db-snapshot-identifier", snapshot_id).get("DBSnapshots")
    snapshot = snapshots[0] if isinstance(snapshots, list) and len(snapshots) == 1 and isinstance(snapshots[0], dict) else None
    if not isinstance(snapshot, dict) or snapshot.get("Status") != "available" or snapshot.get("Encrypted") is not True or snapshot.get("DBInstanceIdentifier") != DATABASE:
        raise EvidenceFailure("acceptance-evidence-recovery-point-invalid")
    restored_identifier = snapshot_id.replace("-recovery-", "-restore-", 1)
    binding, code = recovery_controller().recovery_point_binding(instance, snapshot, snapshot_id, restored_identifier, record_proof)
    if binding is None: raise EvidenceFailure(code)
    _, recovery_facts = binding
    check = subprocess.run(["aws", "rds", "describe-db-instances", "--db-instance-identifier", restored_identifier, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True, timeout=30, env={**os.environ, "AWS_PAGER": ""}, check=False)
    if check.returncode == 0:
        raise EvidenceFailure("acceptance-evidence-restored-database-not-cleaned-up")
    if "DBInstanceNotFound" not in check.stderr:
        raise EvidenceFailure("acceptance-evidence-restored-database-observation-failed")
    return {"database": DATABASE, "snapshot": snapshot_id, "restored_database": restored_identifier, "restore_cleanup": "confirmed-absent", **recovery_facts, "source_created_at": instance["InstanceCreateTime"]}


def live_budget() -> None:
    path = ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"
    try:
        specification = importlib.util.spec_from_file_location("persistence_acceptance_prepare", path)
        if specification is None or specification.loader is None:
            raise OSError("provider preparation module unavailable")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        result = module.live_budget()
    except (OSError, AttributeError, TypeError, ValueError) as error:
        raise EvidenceFailure("acceptance-evidence-budget-observation-failed") from error
    if not isinstance(result, tuple) or not result or result[0] is not True:
        raise EvidenceFailure("acceptance-evidence-target-budget-invalid")


def write_record(record: dict[str, Any]) -> None:
    if record.get("evidence_class", "live") == "simulated" and (record.get("status") != "rehearsed" or RECORD.resolve().is_relative_to(IMPLEMENTATION_ROOT.resolve())):
        raise EvidenceFailure("acceptance-evidence-simulation-production-write-forbidden")
    record_date = parsed_time(record["acceptance"]["accepted_at"]).date().isoformat()
    metadata = {"schema": "agentic-artifact/v3", "id": "infra.04-deploy.03-product.targets.kanbien-core-platform.scope.core-server-persistence.accepted-release", "version": 1, "status": "active", "created_on": record_date, "updated_on": record_date, "layer": "04.deploy", "domain": "deployment.core-server-persistence", "disciplines": ["security", "sre"], "kind": "accepted-release-record", "purpose": "Record the qualified persistence release and AWS-observed proof set accepted for core-server-persistence.", "portability": {"class": "internal", "targets": []}, "used_by": [{"id": "deploy.command.core-platform-target-declaration", "path": "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh"}]}
    rendered = "# agentic-artifact:\n" + "".join("#   " + line + "\n" for line in yaml.safe_dump(metadata, sort_keys=False).splitlines()) + yaml.safe_dump(record, sort_keys=False)
    try:
        succession_module().immutable_write(RECORD, rendered.encode())
    except Exception as error:
        raise EvidenceFailure("acceptance-evidence-record-conflict") from error


def write_successor(record: dict[str, Any]) -> dict[str, str]:
    """Capture fresh observations durably before emitting the generic candidate.

    The original accepted record is immutable.  Candidate promotion is a
    separate compare-and-swap command and must name the expected predecessor.
    """
    succession = succession_module()
    if EVIDENCE_CLASS == "simulated" and (not EVIDENCE_ROOT.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()) or EVIDENCE_ROOT.resolve().is_relative_to(IMPLEMENTATION_ROOT.resolve())):
        raise EvidenceFailure("acceptance-evidence-simulation-production-write-forbidden")
    raw = yaml.safe_dump(record, sort_keys=True).encode()
    observation = EVIDENCE_ROOT / "proof-receipts" / ("acceptance-observation-" + succession.sha256_bytes(raw)[7:] + ".yml")
    succession.immutable_write(observation, raw)
    proofs = dict(record["provider_observation"]["proofs"])
    proofs["current-acceptance-observation"] = {"receipt": observation.relative_to(ROOT).as_posix()}
    path, value = candidate_record(record["release"], proofs, record["acceptance"]["accepted_at"])
    succession.immutable_write(path, succession.rendered(value))
    return {"candidate_record": str(path), "release_id": value["release"]["id"]}


def publish_candidate_record(package: dict[str, str], proofs: dict[str, dict[str, str]], accepted_at: str, retained: dict[str, Path]) -> tuple[Path, dict[str, Any]]:
    """Publish one immutable successor candidate without changing legacy history.

    The historical ``accepted-release.yml`` remains the accepted observation it
    was when first recorded.  A later release is represented by the generic
    succession candidate and can therefore be resumed after an interrupted
    controller without rewriting either history or proof timestamps.
    """
    if EVIDENCE_CLASS == "simulated" and (not EVIDENCE_ROOT.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()) or EVIDENCE_ROOT.resolve().is_relative_to(IMPLEMENTATION_ROOT.resolve()) or IMPLEMENTATION_ROOT.resolve().is_relative_to(EVIDENCE_ROOT.resolve())):
        raise EvidenceFailure("acceptance-evidence-simulation-production-write-forbidden")
    succession = succession_module()
    path, candidate = candidate_record(package, proofs, accepted_at, retained)
    try:
        relative = path.resolve().relative_to(EVIDENCE_ROOT.resolve())
    except ValueError as error:
        raise EvidenceFailure("acceptance-evidence-candidate-path-invalid") from error
    if path.exists():
        try:
            existing, _ = succession.document(path)
            existing_target, existing_scope, _, existing_identity = succession.candidate_identity(existing, EVIDENCE_ROOT)
            _, _, _, proposed_identity = succession.candidate_identity(candidate, EVIDENCE_ROOT)
        except (OSError, succession.SuccessionFailure) as error:
            raise EvidenceFailure("acceptance-evidence-candidate-record-invalid") from error
        if (existing_target, existing_scope, existing_identity) != (TARGET, SCOPE, proposed_identity):
            raise EvidenceFailure("acceptance-evidence-candidate-record-conflict")
        return path, existing
    try:
        succession.immutable_write(path, succession.rendered(candidate))
    except (OSError, succession.SuccessionFailure) as error:
        raise EvidenceFailure("acceptance-evidence-candidate-record-unwritable") from error
    return path, candidate


def route_module():
    path = IMPLEMENTATION_ROOT / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py"
    spec = importlib.util.spec_from_file_location("acceptance_route", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def scope_contract() -> Path:
    return ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"


def route_contract() -> dict:
    route, _ = route_module().load_route(scope_contract(), ROOT)
    if route.get("schema") != "deploy/acceptance-route/v1" or not isinstance(route.get("proofs"), dict):
        raise EvidenceFailure("acceptance-evidence-route-invalid")
    return route


def required_proofs(candidate: dict, rollback: dict) -> dict:
    result = {}
    route = route_contract()
    obligations = route_module().document(ROOT / route["accepted_record"]["schema_path"]).get("required_proofs")
    if not isinstance(obligations, list) or any(not isinstance(name, str) for name in obligations) or set(obligations) != set(route["proofs"]):
        raise EvidenceFailure("acceptance-evidence-required-proofs-mismatch")
    for name, proof in route["proofs"].items():
        if not isinstance(proof, dict) or proof.get("image_role") not in {"candidate", "rollback"}:
            raise EvidenceFailure("acceptance-evidence-proof-route-invalid")
        image = candidate if proof["image_role"] == "candidate" else rollback
        result[name] = (proof["proof_type"], proof["family"], image["image_digest"], proof["result_code"], proof["deadline_workload"])
    return result


def retained_context(arguments: list[str], snapshot: str, original: str, successor: str) -> dict:
    values = {}
    for value in arguments:
        name, path = value.split("=", 1)
        try: values[name] = receipt_module().validate(json.loads(Path(path).read_text()))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-invalid") from error
    for item in values.values():
        if item["proof_type"] == "verifier" and item["context"]["record_id"] != "core-persistence-acceptance-v1":
            raise EvidenceFailure("acceptance-evidence-retained-record-mismatch")
    restoration = values["isolated-restore"]["context"]
    if restoration["snapshot"] != snapshot or restoration["restored_database"] != snapshot.replace("-recovery-", "-restore-", 1):
        raise EvidenceFailure("acceptance-evidence-retained-snapshot-mismatch")
    replacement = values["server-replacement"]
    if replacement["task"]["arn"] != original or replacement["context"]["successor_task_arn"] != successor:
        raise EvidenceFailure("acceptance-evidence-replacement-input-mismatch")
    return values


def sequence_valid(observed: dict, values: dict) -> None:
    replacement = values["server-replacement"]
    context, task = replacement["context"], replacement["task"]
    if parsed_time(context["successor_started_at"]) <= parsed_time(task["started_at"]) or parsed_time(observed["server-replacement-read"]["started_at"]) < parsed_time(context["successor_started_at"]):
        raise EvidenceFailure("acceptance-evidence-server-replacement-sequence-invalid")
    for prior, later in route_contract()["sequence"]:
        if parsed_time(observed[later]["started_at"]) < parsed_time(observed[prior]["stopped_at"]):
            raise EvidenceFailure("acceptance-evidence-rehearsal-sequence-invalid")


def validate_record(record: object, *, evidence_class: str = "live") -> None:
    """Validate historical custody and proof without provider queries."""
    if not isinstance(record, dict): raise EvidenceFailure("accepted-release-record-invalid")
    route = route_contract()
    schema = route_module().document(ROOT / route["accepted_record"]["schema_path"])
    fields = schema.get("required_fields")
    if schema.get("record_schema") != record.get("schema") or not isinstance(fields, list) or not all(field in record for field in fields): raise EvidenceFailure("accepted-release-schema-invalid")
    if record.get("target") != TARGET or record.get("scope") != SCOPE or record.get("evidence_class", "live") != evidence_class or record.get("status") != ("accepted" if evidence_class == "live" else "rehearsed"):
        raise EvidenceFailure("accepted-release-evidence-class-or-identity-invalid")
    release, acceptance, provider = record.get("release"), record.get("acceptance"), record.get("provider_observation")
    if not all(isinstance(value, dict) for value in (release, acceptance, provider)): raise EvidenceFailure("accepted-release-record-invalid")
    if re.fullmatch(r"[a-f0-9]{40}", str(release.get("source_revision"))) is None or re.fullmatch(r"sha256:[a-f0-9]{64}", str(release.get("image_digest"))) is None: raise EvidenceFailure("accepted-release-package-identity-invalid")
    if acceptance.get("retained_for_restoration") is not True or acceptance.get("collector") != "collect-acceptance-evidence": raise EvidenceFailure("accepted-release-retention-invalid")
    applicability_reference = acceptance.get("proof_applicability")
    if applicability_reference is not None:
        path = route_module().reference(ROOT, applicability_reference.get("path")) if isinstance(applicability_reference, dict) else None
        if path is None or not path.is_file() or not isinstance(applicability_reference.get("sha256"), str): raise EvidenceFailure("accepted-release-proof-applicability-invalid")
        try: raw = json.loads(path.read_text(encoding="utf-8")); applicability = proof_applicability_module().validate(raw, {"source_revision": release["source_revision"], "image_digest": release["image_digest"], "receipt_reference": release["package_custody_reference"]})
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error: raise EvidenceFailure("accepted-release-proof-applicability-invalid") from error
        if succession_module().sha256_bytes(path.read_bytes()) != applicability_reference["sha256"]: raise EvidenceFailure("accepted-release-proof-applicability-invalid")
    else:
        applicability = None
    accepted_at = parsed_time(acceptance.get("accepted_at"))
    rollback = acceptance.get("rollback_release")
    if not isinstance(rollback, dict) or rollback.get("image_digest") == release.get("image_digest") or re.fullmatch(r"sha256:[a-f0-9]{64}", str(rollback.get("image_digest"))) is None: raise EvidenceFailure("accepted-release-rollback-identity-invalid")
    if evidence_class == "live":
        compatibility = acceptance.get("rollback_compatibility")
        if not isinstance(compatibility, dict) or set(compatibility) != {"id", "path", "sha256"}:
            raise EvidenceFailure("accepted-release-rollback-compatibility-missing")
        expected = qualified_rollback_compatibility(rollback)
        if compatibility != expected:
            raise EvidenceFailure("accepted-release-rollback-compatibility-mismatch")
    proofs, database, replacement = provider.get("proofs"), provider.get("database"), provider.get("server_replacement")
    current = provider.get("current_service")
    observability = provider.get("observability")
    if not all(isinstance(value, dict) for value in (proofs, database, replacement, current, observability)): raise EvidenceFailure("accepted-release-observation-invalid")
    if database.get("database") != DATABASE or database.get("restore_cleanup") != "confirmed-absent" or SNAPSHOT.fullmatch(str(database.get("snapshot"))) is None: raise EvidenceFailure("accepted-release-recovery-observation-invalid")
    if current.get("service") != SERVICE or current.get("task_definition") != release.get("runtime_task_definition") or TASK_ARN.fullmatch(str(current.get("running_task"))) is None: raise EvidenceFailure("accepted-release-runtime-identity-invalid")
    arguments = []
    for name, item in proofs.items():
        if not isinstance(item, dict) or not isinstance(item.get("receipt"), str): raise EvidenceFailure("accepted-release-proof-reference-invalid")
        path = ROOT / item["receipt"]
        arguments.append(name + "=" + str(path))
    observed = parse_proof_receipts(arguments, required_proofs(release, rollback), contract_deadlines(), applicability=applicability)
    try:
        observability_arguments = [name + "=" + str(ROOT / item["receipt"]) for name, item in observability.items()]
    except (TypeError, KeyError):
        raise EvidenceFailure("accepted-release-observability-receipts-invalid") from None
    if parse_observability_receipts(observability_arguments, release["image_digest"]) != observability:
        raise EvidenceFailure("accepted-release-observability-receipts-invalid")
    original, successor = replacement.get("original_task"), replacement.get("replacement_task")
    if not isinstance(original, dict) or not isinstance(successor, dict): raise EvidenceFailure("accepted-release-replacement-invalid")
    values = retained_context(arguments, database["snapshot"], original.get("task_arn"), successor.get("task_arn"))
    sequence_valid(observed, values)
    for name, item in observed.items():
        if proofs.get(name) != item or parsed_time(item["stopped_at"]) > accepted_at: raise EvidenceFailure("accepted-release-proof-binding-invalid")
    # Legacy accepted records keep their original observation vocabulary. New
    # records additionally retain the fresh readiness proof, never a cache hit.
    health = provider.get("current_health")
    if "evidence_class" in record:
        if not isinstance(health, dict): raise EvidenceFailure("accepted-release-current-health-missing")
        reference = route_module().reference(ROOT, database.get("record_proof_receipt"))
        if reference is None: raise EvidenceFailure("accepted-release-record-proof-missing")
        retained, code = recovery_controller().read_record_proof(reference)
        if retained is None: raise EvidenceFailure(code)
        if retained["integrity"]["payload_sha256"] != database.get("record_proof_digest") or database.get("record_id") != "core-persistence-acceptance-v1" or parsed_time(retained["task"]["stopped_at"]) != parsed_time(database.get("record_proven_at")) or not parsed_time(database.get("source_created_at")) <= parsed_time(retained["task"]["started_at"]) <= parsed_time(database.get("record_proven_at")) <= parsed_time(database.get("snapshot_recovery_time")) <= accepted_at:
            raise EvidenceFailure("accepted-release-record-recovery-binding-invalid")
    if health is not None and (not isinstance(health, dict) or health.get("image_digest") != release["image_digest"] or health.get("task_definition") != release.get("verifier_task_definition") or health.get("result_code") != "KANBIEN_CORE_PERSISTENCE_HEALTHY" or parsed_time(health.get("stopped_at")) > accepted_at):
        raise EvidenceFailure("accepted-release-current-health-invalid")


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--receipt", type=Path); parser.add_argument("--rollback-receipt", type=Path)
    parser.add_argument("--proof", action="append", default=[]); parser.add_argument("--proof-receipt", action="append", default=[])
    parser.add_argument("--server-replacement-original"); parser.add_argument("--server-replacement-successor"); parser.add_argument("--recovery-snapshot")
    parser.add_argument("--record-proof-receipt", type=Path); parser.add_argument("--current-health-task"); parser.add_argument("--proof-applicability", type=Path); parser.add_argument("--observability-receipt", action="append", default=[])
    parser.add_argument("--write", action="store_true"); parser.add_argument("--write-candidate", action="store_true"); parser.add_argument("--json", action="store_true"); parser.add_argument("--validate-arguments", action="store_true")
    try: args, unknown = parser.parse_known_args(argv)
    except argparse.ArgumentError as error: raise EvidenceFailure("acceptance-evidence-arguments-invalid") from error
    if unknown or (args.write and args.write_candidate): raise EvidenceFailure("acceptance-evidence-arguments-invalid")
    if args.inputs is not None:
        if args.receipt or args.rollback_receipt or args.proof or args.proof_receipt or args.server_replacement_original or args.server_replacement_successor or args.recovery_snapshot or args.record_proof_receipt or args.current_health_task or args.proof_applicability or args.observability_receipt: raise EvidenceFailure("acceptance-evidence-input-source-ambiguous")
        if args.validate_arguments: return args
        try: values = route_module().input_values(args.inputs, route_contract(), root=ROOT)
        except ValueError as error: raise EvidenceFailure(str(error)) from error
        args.receipt, args.rollback_receipt = Path(values["candidate_receipt"]), Path(values["rollback_receipt"])
        args.proof_receipt = [name + "=" + path for name, path in values["proof_receipts"].items()]
        for name in ("server_replacement_original", "server_replacement_successor", "recovery_snapshot", "current_health_task"): setattr(args, name, values[name])
        args.record_proof_receipt = Path(values["record_proof_receipt"])
        if values.get("proof_applicability") is not None: args.proof_applicability = Path(values["proof_applicability"])
        args.observability_receipt = [name + "=" + path for name, path in values["observability_receipts"].items()]
    if args.receipt is None or args.rollback_receipt is None or not all(isinstance(value, str) for value in (args.server_replacement_original, args.server_replacement_successor, args.recovery_snapshot, args.current_health_task)) or SNAPSHOT.fullmatch(args.recovery_snapshot) is None or args.record_proof_receipt is None:
        raise EvidenceFailure("acceptance-evidence-arguments-invalid")
    if args.proof: raise EvidenceFailure("acceptance-evidence-retained-proof-receipts-required")
    if not args.proof_receipt: raise EvidenceFailure("acceptance-evidence-proof-receipt-set-invalid")
    if not args.observability_receipt: raise EvidenceFailure("acceptance-evidence-observability-receipt-set-invalid")
    return args


def main() -> int:
    global TASKS
    TASKS = {}; task_definition.cache_clear()
    try:
        args = parse_arguments()
        if args.validate_arguments:
            print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[]})); return 0
        candidate, rollback = receipt(args.receipt), receipt(args.rollback_receipt)
        if candidate["image_digest"] == rollback["image_digest"]: raise EvidenceFailure("acceptance-evidence-rollback-identity-invalid")
        compatibility = qualified_rollback_compatibility(rollback) if EVIDENCE_CLASS == "live" else None
        required = required_proofs(candidate, rollback)
        applicability = proof_applicability(args.proof_applicability, candidate)
        observed = parse_proof_receipts(args.proof_receipt, required, contract_deadlines(), applicability=applicability)
        observability = parse_observability_receipts(args.observability_receipt, candidate["image_digest"])
        values = retained_context(args.proof_receipt, args.recovery_snapshot, args.server_replacement_original, args.server_replacement_successor)
        sequence_valid(observed, values)
        # The retained source-record proof is checked before any current provider observation.
        record_proof, code = recovery_controller().read_record_proof(args.record_proof_receipt)
        if record_proof is None: raise EvidenceFailure(code)
        outputs = stack_outputs()
        runnable_digest = qualified_runnable_digest(candidate)
        current = current_service(outputs["CoreServerPersistenceTaskDefinitionArn"], candidate, runnable_digest)
        health = current_health(args.current_health_task, outputs["CoreServerPersistenceVerifierTaskDefinitionArn"], candidate, runnable_digest)
        database = database_posture(args.recovery_snapshot, record_proof)
        try: database["record_proof_receipt"] = args.record_proof_receipt.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError: raise EvidenceFailure("acceptance-evidence-record-proof-path-invalid") from None
        live_budget()
        original_receipt = values["server-replacement"]
        task, context = original_receipt["task"], original_receipt["context"]
        original = {"task_arn":task["arn"],"task_definition":task["definition"],"started_at":task["started_at"],"stopped_at":task["stopped_at"],"stopped_reason":task["stopped_reason"]}
        successor = {"task_arn":context["successor_task_arn"],"task_definition":context["runtime_task_definition"],"started_at":context["successor_started_at"],"stopped_at":None,"stopped_reason":None}
        stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        acceptance = {"accepted_at":stamp,"collector":"collect-acceptance-evidence","retained_for_restoration":True,"rollback_release":rollback}
        if compatibility is not None: acceptance["rollback_compatibility"] = compatibility
        if applicability is not None:
            try: relative = args.proof_applicability.resolve().relative_to(ROOT.resolve()).as_posix()
            except ValueError: raise EvidenceFailure("acceptance-evidence-proof-applicability-path-invalid") from None
            acceptance["proof_applicability"] = {"path": relative, "sha256": succession_module().sha256_bytes(args.proof_applicability.read_bytes())}
        record = {"schema":"deploy/persistence-accepted-release/v1","target":TARGET,"scope":SCOPE,"status":"accepted" if EVIDENCE_CLASS == "live" else "rehearsed","evidence_class":EVIDENCE_CLASS,"release":{"source_revision":candidate["source_revision"],"image_digest":candidate["image_digest"],"image_repository":f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/kanbien-core-platform/core-server","package_custody_reference":candidate["receipt_reference"],"runtime_stack":STACK,"service":SERVICE,"runtime_task_definition":outputs["CoreServerPersistenceTaskDefinitionArn"],"verifier_task_definition":outputs["CoreServerPersistenceVerifierTaskDefinitionArn"],"migration_task_definition":outputs["CoreServerPersistenceMigrationTaskDefinitionArn"],"restoration_verifier_task_definition":outputs["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"]},"acceptance":acceptance,"provider_observation":{"current_service":current,"current_health":health,"database":database,"proofs":observed,"observability":observability,"server_replacement":{"original_task":original,"replacement_task":successor}}}
        validate_record(record, evidence_class=EVIDENCE_CLASS)
        facts = None
        if args.write:
            if RECORD.exists(): raise EvidenceFailure("acceptance-evidence-record-already-exists")
            write_record(record)
        if args.write_candidate:
            retained = {
                "candidate-package": args.receipt,
                "rollback-package": args.rollback_receipt,
                "record-source": args.record_proof_receipt,
                **{f"observability-{name}": ROOT / value["receipt"] for name, value in observability.items()},
            }
            if compatibility is not None:
                retained["rollback-compatibility"] = ROOT / compatibility["path"]
            if args.proof_applicability is not None:
                retained["proof-applicability"] = args.proof_applicability
            candidate_path, candidate = publish_candidate_record(candidate, observed, stamp, retained)
            try:
                relative = candidate_path.resolve().relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                raise EvidenceFailure("acceptance-evidence-candidate-path-invalid") from None
            return report("recorded", facts={"candidate_record": relative, "release_id": candidate["release"]["id"]})
        return report("recorded" if args.write else "ready")
    except (EvidenceFailure, KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError) as error:
        return report("blocked", str(error) if isinstance(error, EvidenceFailure) else "acceptance-evidence-malformed-input")


if __name__ == "__main__": raise SystemExit(main())
