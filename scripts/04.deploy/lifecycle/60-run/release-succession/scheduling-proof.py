#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.scheduling-acceptance-proof
#   version: 2
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate explicitly selected scheduling qualification through declared component custody and its trusted evidence owner, preserving HTTP release identity.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.collect-acceptance.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/implementation/acceptance-route.py
#   - id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py
"""Additional component proof, never a replacement primary image or cloud grant."""
from datetime import datetime, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
import yaml

IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[5]
PROFILE = "scheduling-a2-v1"
SCHEMA = "deploy/scheduling-qualification/v1"
RUNTIME_SCHEMA = "deploy/scheduling-runtime-proof/v1"
ROLES = {"dispatch", "worker"}
CASES = {"minute-delivery", "duplicate-delivery", "missed-tick-recovery", "cancellation", "failure-recovery", "scope-isolation", "cost-and-idle"}
LIMIT = 2 * 1024 * 1024
OWNER = "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py"


class ProofFailure(ValueError):
    def __init__(self, code):
        self.code = "scheduling-proof-" + code
        super().__init__(self.code)


def require(value, code):
    if not value: raise ProofFailure(code)


def profile(value=None):
    require(value is None or value == PROFILE, "profile-invalid")
    return value


def database_proof(value=None):
    """One explicit selection shared by task admission and retained readers."""
    selected = profile(value)
    return {"stage": "scheduling-qualification" if selected else "initial-recovery",
            "operation": "observe-scheduling-state" if selected else "observe-migration-state",
            "result_code": "PERSISTENCE_SCHEDULING_STATE_CONFIRMED" if selected else "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED"}


def record_profile(record):
    selected = profile(record.get("qualification_profile"))
    require((selected is not None) == ("scheduling_qualification" in record), "profile-proof-mismatch")
    if selected is not None:
        require(isinstance(record["scheduling_qualification"], dict)
                and record["scheduling_qualification"].get("profile") == selected, "profile-proof-mismatch")
    return selected


def complete_database_state(value, *, manifest_sha256=None):
    """Captured full state, not prefix, privilege or activation authority."""
    owner = module(IMPLEMENTATION_ROOT / "scripts/04.deploy/shared/scheduling-database-state.py", "acceptance_scheduling_database_state")
    try: checked = owner.validate(value)
    except ValueError: raise ProofFailure("database-state-invalid") from None
    require(checked["migration_count"] == 7, "database-state-incomplete")
    if manifest_sha256 is not None:
        require(checked["manifest_sha256"] == manifest_sha256, "database-manifest-mismatch")
    return checked


def selected_route(route, value=None):
    """Require the selected collector profile and database proof, preserving HTTP identity."""
    if profile(value) is None: return route
    selected = route.get("qualification_profiles", {}).get(PROFILE)
    require(isinstance(selected, dict) and selected.get("database_proof") == database_proof(PROFILE), "profile-invalid")
    commands = route.get("commands")
    collector = route.get("collector")
    require(isinstance(commands, dict) and isinstance(collector, str)
            and isinstance(commands.get(collector), dict), "profile-invalid")
    command = commands[collector]
    argv = command.get("argv")
    require(isinstance(argv, list) and len(argv) >= 2 and all(isinstance(item, str) for item in argv)
            and not any(item.split("=", 1)[0] == "--require-qualification-profile" for item in argv), "profile-invalid")
    projected = {**route, "commands": {**commands, collector: {
        **command, "argv": [*argv, "--require-qualification-profile", PROFILE]}}}
    proofs = route.get("proofs", {})
    require(isinstance(proofs, dict), "profile-invalid")
    if "migration-applied-state" not in proofs: return projected
    proof = proofs["migration-applied-state"]
    require(isinstance(proof, dict) and isinstance(proof.get("command"), str)
            and isinstance(commands.get(proof["command"]), dict), "profile-invalid")
    command = commands[proof["command"]]
    argv = command.get("argv")
    require(isinstance(argv, list) and len(argv) >= 2
            and all(isinstance(item, str) and item for item in argv), "profile-invalid")
    argv = list(argv)
    indexes = [index for index, item in enumerate(argv[:-1]) if item == "--operation"]
    require(len(indexes) == 1 and argv[indexes[0] + 1] == database_proof()["operation"], "profile-invalid")
    argv[indexes[0] + 1] = selected["database_proof"]["operation"]
    argv.extend(["--qualified-receipt", "{candidate_receipt}"])
    return {**projected, "proofs": {**route["proofs"], "migration-applied-state": {
                **proof, **{key: selected["database_proof"][key] for key in ("operation", "result_code")}}},
            "commands": {**projected["commands"], proof["command"]: {**command, "argv": argv}}}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "owner-unavailable")
    result = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(result)
    except (OSError, ImportError, SyntaxError): raise ProofFailure("owner-unavailable") from None
    return result


def canonical(value):
    try: return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    except (ValueError, TypeError, RecursionError): raise ProofFailure("document-invalid") from None


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


ARCHIVE_SCHEMA = "deploy/scheduling-proof-archive/v1"
ARCHIVE_REFERENCE = "deploy/scheduling-proof-archive-reference/v1"
ARCHIVE_KINDS = {"native", "preparation", "phase", "cost", "alert"}
ARCHIVE_PART_LIMIT = 2048
# The complete finite case set can use 53 distinct roots when optional
# preflights and runtime windows are not shared. Byte/expansion caps stay fixed.
ARCHIVE_ROOT_LIMIT = 64
ARCHIVE_EXPANSION_LIMIT = 32 * 1024 * 1024


def _archive_copy(value, *, resolve=None, collect=None):
    """Bound expanded JSON, including repeated references, before retaining it."""
    active, nodes, used = set(), 0, 0
    def charge(size):
        nonlocal used
        used += size
        require(used <= LIMIT, "archive-expansion-limit")
    def walk(item, depth):
        nonlocal nodes
        nodes += 1
        require(depth <= 64 and nodes <= 131072, "archive-complexity-limit")
        if isinstance(item, dict) and item.get("schema") == ARCHIVE_REFERENCE:
            require(resolve is not None, "archive-reference-collision")
            require(set(item) == {"schema", "reference"}, "archive-reference-invalid")
            return resolve(item["reference"], depth, walk)
        if isinstance(item, (dict, list)):
            require(id(item) not in active, "archive-cycle")
            active.add(id(item))
            start = used
            charge(2 + max(0, len(item) - 1))
            if isinstance(item, dict):
                require(all(isinstance(key, str) for key in item), "archive-value-invalid")
                copied = {}
                for key, child in item.items():
                    charge(len(canonical(key)))  # encoded key plus colon
                    copied[key] = walk(child, depth + 1)
            else:
                copied = [walk(child, depth + 1) for child in item]
            active.remove(id(item))
            return collect(copied, used - start) if collect is not None and depth > 0 else copied
        require(item is None or type(item) in {str, int, float, bool}, "archive-value-invalid")
        charge(len(canonical(item)) - 1)
        return item
    return walk(value, 0), used


def _archive_materials(materials):
    require(isinstance(materials, dict) and len(materials) <= ARCHIVE_PART_LIMIT, "archive-material-limit")
    require(len(canonical(materials)) <= LIMIT, "archive-material-limit")
    for reference, value in materials.items():
        require(isinstance(reference, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", reference)
            and isinstance(value, dict) and set(value) == {"kind", "packet"}
            and isinstance(value["kind"], str) and digest(value) == reference, "archive-material-mismatch")


def pack_archive(value, materials, *, kind):
    """Share immutable JSON parts inside this bundle, never native proof meaning.

    Existing proof-prerequisite-reference objects remain original JSON. Only
    this codec's distinct reference is expanded, before any real proof reader.
    The caller owns native validation and rejects unused material globally.
    """
    require(isinstance(kind, str) and kind in ARCHIVE_KINDS and isinstance(value, dict), "archive-kind-invalid")
    _archive_materials(materials)
    pending = {}
    def retain(packet, selected):
        entry = {"kind": selected, "packet": packet}
        reference = digest(entry)
        previous = pending.get(reference, materials.get(reference))
        require(previous is None or previous == entry, "archive-material-conflict")
        if previous is None:
            require(len(materials) + len(pending) < ARCHIVE_PART_LIMIT, "archive-material-limit")
            pending[reference] = entry
        return reference
    def collect(item, size):
        if not isinstance(item, dict) or size < 1024: return item
        return {"schema": ARCHIVE_REFERENCE, "reference": retain(item, "archive-part")}
    encoded, _ = _archive_copy(value, collect=collect)
    reference = retain({"schema": ARCHIVE_SCHEMA, "original_sha256": digest(value), "value": encoded}, kind)
    _archive_materials({**materials, **pending})
    materials.update(pending)
    return reference


def unpack_archive(reference, materials, *, kind):
    """Return the exact original plus every consumed reference; no file access."""
    require(isinstance(kind, str) and kind in ARCHIVE_KINDS, "archive-kind-invalid")
    _archive_materials(materials)
    consumed, active = set(), set()
    def entry(selected, expected):
        require(isinstance(selected, str) and selected in materials, "archive-reference-missing")
        value = materials[selected]
        require(value["kind"] == expected, "archive-kind-mismatch")
        consumed.add(selected)
        return value["packet"]
    packet = entry(reference, kind)
    require(isinstance(packet, dict) and set(packet) == {"schema", "original_sha256", "value"}
        and packet["schema"] == ARCHIVE_SCHEMA and isinstance(packet["value"], dict), "archive-envelope-invalid")
    def resolve(selected, depth, walk):
        require(isinstance(selected, str) and selected not in active, "archive-cycle")
        active.add(selected)
        part = entry(selected, "archive-part")
        require(isinstance(part, dict) and part.get("schema") != ARCHIVE_REFERENCE, "archive-part-invalid")
        result = walk(part, depth)
        active.remove(selected)
        return result
    original, _ = _archive_copy(packet["value"], resolve=resolve)
    require(digest(original) == packet["original_sha256"], "archive-original-mismatch")
    return original, consumed


def pack_native_archive(value, materials, *, preparation=False):
    return pack_archive(value, materials, kind="preparation" if preparation else "native")


def unpack_native_archive(reference, materials, *, preparation=False):
    return unpack_archive(reference, materials, kind="preparation" if preparation else "native")


def instant(value):
    require(isinstance(value, str), "timestamp-invalid")
    try: result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: raise ProofFailure("timestamp-invalid") from None
    require(result.tzinfo is not None, "timestamp-invalid")
    return result


def read(path):
    path = Path(path).absolute()
    require(not any(item.is_symlink() for item in (path, *path.parents)), "path-unsafe")
    try:
        with path.open("rb") as stream: raw = stream.read(LIMIT + 1)
        require(len(raw) <= LIMIT, "document-too-large")
        def pairs(items):
            result = {}
            for key, value in items:
                require(key not in result, "document-ambiguous")
                result[key] = value
            return result
        result = json.loads(raw, object_pairs_hook=pairs)
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, ProofFailure): raise
        raise ProofFailure("document-unavailable") from None
    require(isinstance(result, dict), "document-invalid")
    return result


def selection(root, target, scope):
    require(all(isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9-]+", value) for value in (target, scope)), "scope-invalid")
    base = Path(root) / "infra/04.deploy/03.product/targets" / target / "20-scopes" / scope / "00-declaration"
    try:
        contract = yaml.safe_load((base / "declaration-contract.yml").read_text())
        route = yaml.safe_load((base / "acceptance-route-contract.yml").read_text())
        selected = route["qualification_profiles"][PROFILE]
        requirements = {item["id"]: item for item in contract["change_impact"]["requirements"]}
        programs = yaml.safe_load((Path(root) / contract["program"]["contract"]).read_text())
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError): raise ProofFailure("profile-unavailable") from None
    require((contract.get("target"), contract.get("scope"), route.get("target"), route.get("scope")) == (target, scope, target, scope), "scope-mismatch")
    require(set(selected) == {"requirements", "inputs", "database_proof"} and set(selected["requirements"]) == ROLES
            and selected["database_proof"] == database_proof(PROFILE), "profile-invalid")
    result = {}
    for role, identity in selected["requirements"].items():
        try:
            subjects = requirements[identity]["subjects"]
            require(isinstance(subjects, list) and len(subjects) == 1, "subject-invalid")
            subject = subjects[0]
            matches = [item for item in programs["package_candidates"] if item.get("image_contract") == subject["image_id"]]
            require(len(matches) == 1, "candidate-invalid")
            result[role] = {"program_id": subject["program_id"], "package_contract_id": subject["image_id"], "candidate_id": matches[0]["id"]}
        except (KeyError, TypeError): raise ProofFailure("subject-invalid") from None
    require(result["dispatch"]["program_id"] != result["worker"]["program_id"], "subject-invalid")
    return result


def owner_validate(root, evidence, expected, *, historical):
    """Only the fixed owning controller may validate provider/task provenance.

    Its self-consistency observation is deliberately NOT an acceptance reader.
    Until that producer/reader exists, live qualification remains blocked.
    """
    owner = module(IMPLEMENTATION_ROOT / OWNER, "scheduling_acceptance_evidence_owner")
    reader = getattr(owner, "validate_acceptance_evidence", None)
    require(callable(reader), "owner-unavailable")
    try: result = reader(evidence, expected=expected, historical=historical)
    except Exception as error:
        if isinstance(error, ProofFailure): raise
        raise ProofFailure("provenance-not-confirmed") from None
    require(result == evidence, "provenance-not-confirmed")


def validate(bundle, *, root, target, scope, source, primary_image, observed_at=None, historical=False, evidence_class="live"):
    require(isinstance(bundle, dict) and set(bundle) == {"schema", "profile", "target", "scope", "source_revision", "primary_image_digest", "recorded_at", "components", "evidence"}, "envelope-invalid")
    require(bundle["schema"] == SCHEMA and bundle["profile"] == PROFILE, "profile-invalid")
    require(len(canonical(bundle)) <= LIMIT, "document-too-large")
    require((bundle["target"], bundle["scope"], bundle["source_revision"], bundle["primary_image_digest"]) == (target, scope, source, primary_image), "identity-mismatch")
    subjects = selection(root, target, scope)
    require(isinstance(bundle["components"], dict) and set(bundle["components"]) == ROLES, "components-incomplete")
    custody = module(IMPLEMENTATION_ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py", "scheduling_component_custody")
    for role, selected in subjects.items():
        receipt = bundle["components"][role]
        try:
            custody.validate(receipt, SimpleNamespace(expected_target=target, expected_candidate=selected["candidate_id"], expected_package_contract=selected["package_contract_id"], expected_program=selected["program_id"]))
        except custody.Failure: raise ProofFailure("component-custody-invalid") from None
        require(receipt["source_revision"] == source, "component-source-mismatch")
    evidence = bundle["evidence"]
    require(isinstance(evidence, dict) and set(evidence) == {"schema", "evidence_class", "target", "scope", "source_revision", "primary_image_digest", "observed_at", "components", "observations"}, "runtime-envelope-invalid")
    require(evidence["schema"] == RUNTIME_SCHEMA and evidence["evidence_class"] == evidence_class, "evidence-class-mismatch")
    require(all(evidence[key] == bundle[key] for key in ("target", "scope", "source_revision", "primary_image_digest")), "runtime-identity-mismatch")
    require(isinstance(evidence["components"], dict) and set(evidence["components"]) == ROLES, "runtime-components-incomplete")
    for role, value in evidence["components"].items():
        require(isinstance(value, dict) and set(value) == {"program_id", "image_digest", "version_arn"}, "runtime-component-invalid")
        require(all(value[key] == bundle["components"][role][key] for key in ("program_id", "image_digest")), "runtime-component-mismatch")
        require(isinstance(value["version_arn"], str) and re.fullmatch(r"arn:aws:lambda:[a-z0-9-]+:[0-9]{12}:function:[a-zA-Z0-9-_]+:[1-9][0-9]*", value["version_arn"]), "runtime-version-invalid")
    observations = evidence["observations"]
    require(isinstance(observations, dict) and set(observations) == CASES and all(isinstance(value, dict) and value for value in observations.values()), "cases-incomplete")
    observed, recorded = instant(evidence["observed_at"]), instant(bundle["recorded_at"])
    require(observed <= recorded <= observed + timedelta(minutes=15), "observation-stale")
    if not historical:
        require(observed_at is not None and recorded <= instant(observed_at) <= observed + timedelta(minutes=15), "observation-stale")
    expected = {"target": target, "scope": scope, "source_revision": source, "primary_image_digest": primary_image, "components": bundle["components"], "subjects": subjects, "evidence_class": evidence_class}
    owner_validate(root, evidence, expected, historical=historical)
    return bundle


def collect(*, root, target, scope, source, primary_image, proof, packages, observed_at, evidence_class="live"):
    require(isinstance(packages, dict) and set(packages) == ROLES, "components-incomplete")
    evidence = read(proof)
    bundle = {"schema": SCHEMA, "profile": PROFILE, "target": target, "scope": scope, "source_revision": source, "primary_image_digest": primary_image,
              "recorded_at": evidence.get("observed_at"), "components": {role: read(path) for role, path in packages.items()}, "evidence": evidence}
    return validate(bundle, root=root, target=target, scope=scope, source=source, primary_image=primary_image, observed_at=observed_at, evidence_class=evidence_class)


def material(bundle):
    values = {"scheduling-qualification": ("proof-receipts", bundle), **{"scheduling-" + role + "-package": ("package-receipts", value) for role, value in bundle["components"].items()}}
    return {name: (directory + "/" + name + "-" + digest(value)[7:] + ".json", canonical(value)) for name, (directory, value) in values.items()}


def retain(bundle, evidence_root, succession):
    result = {}
    for name, (relative, payload) in material(bundle).items():
        path = succession.retained_evidence_file(evidence_root, evidence_root / relative)
        require(not any(item.is_symlink() for item in (path, *path.parents)), "path-unsafe")
        succession.immutable_write(path, payload)
        result[name] = path
    return result


# These are the fixed public job contracts selected by the two target mounts,
# not caller-supplied SQL, application code or arbitrary scheduler payloads.
PROOF_JOBS = {"core-server-persistence": "kanbien-core-server.persistence.scheduling.verify",
              "entity-smoke": "entity-smoke.test-entity.purge-expired"}
PROOF_OPERATIONS = {"seed-scheduling-proof": "PERSISTENCE_SCHEDULING_PROOF_SEEDED",
                    "observe-scheduling-proof": "PERSISTENCE_SCHEDULING_PROOF_OBSERVED"}
SNAPSHOTS = ("before", "after", "recovered", "duplicate", "restored", "not-yet-due")


def proof_identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", value, re.I), "identifier-invalid")
    return value


def proof_time(value):
    # Native Core ISODateTime values are normalized before crossing this seam.
    require(isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z", value), "timestamp-invalid")
    instant(value)
    return value


def proof_selection(value, *, scope):
    require(scope in PROOF_JOBS and isinstance(value, dict), "selection-invalid")
    fields = {"kind", "id"} | ({"due_at"} if scope == "entity-smoke" and "due_at" in value else set())
    require(set(value) == fields and value["kind"] == ("subject" if scope == "entity-smoke" else "schedule"), "selection-invalid")
    proof_identifier(value["id"])
    if "due_at" in value: proof_time(value["due_at"])
    return value


def proof_seed(value):
    require(isinstance(value, dict) and set(value) == {"schema", "schedule_id", "job_name", "due_at", "disposition"}
            and value["schema"] == "kanbien/scheduling-proof-seed/v1" and value["job_name"] == PROOF_JOBS["core-server-persistence"]
            and value["disposition"] in {"created", "already-exists"}, "seed-invalid")
    proof_identifier(value["schedule_id"]); proof_time(value["due_at"])
    return value


def proof_snapshot(value, *, scope, selection=None, start=None, stop=None):
    """Validate exact-ID facts only; absence is not a successful-job verdict."""
    require(isinstance(value, dict) and set(value) == {"schema", "selection", "observed_at", "schedule", "outbox", "processing", "application", "delivery_message"}
            and value["schema"] == "kanbien/scheduling-proof-observation/v1", "snapshot-invalid")
    selected = proof_selection(value["selection"], scope=scope)
    if selection is not None: require(selected == proof_selection(selection, scope=scope), "selection-mismatch")
    observed = instant(proof_time(value["observed_at"]))
    if start is not None and stop is not None:
        require(instant(start) - timedelta(seconds=60) <= observed <= instant(stop) + timedelta(seconds=60), "snapshot-time-mismatch")
    schedule, outbox, processing, application = (value[key] for key in ("schedule", "outbox", "processing", "application"))
    if scope == "entity-smoke" and "due_at" not in selected: require(schedule is None, "untouched-reminder-unexpected")
    if schedule is None:
        require(outbox is None and processing is None, "snapshot-link-invalid")
    else:
        fields = {"id", "job_name", "due_at", "state"} | ({"subject"} if scope == "entity-smoke" else set())
        require(isinstance(schedule, dict) and schedule.get("state") in {"waiting", "delivery-created", "blocked-job-unavailable", "blocked-invalid-row"}, "schedule-invalid")
        if schedule["state"] == "delivery-created": fields.add("outbox_entry_id")
        require(set(schedule) == fields and schedule["job_name"] == PROOF_JOBS[scope], "schedule-invalid")
        proof_identifier(schedule["id"]); proof_time(schedule["due_at"])
        if scope == "entity-smoke":
            require(schedule["subject"] == {"kind": "entity-smoke.test-entity", "id": selected["id"]}
                    and schedule["due_at"] == selected["due_at"], "selection-mismatch")
        else: require(schedule["id"] == selected["id"], "selection-mismatch")
        if "outbox_entry_id" in schedule:
            proof_identifier(schedule["outbox_entry_id"])
        else: require(outbox is None and processing is None, "snapshot-link-invalid")
    if outbox is not None:
        require(isinstance(outbox, dict) and outbox.get("state") in {"pending", "leased", "published"}, "outbox-invalid")
        fields = {"id", "state", "attempt", "created_at"} | ({"published_at"} if outbox["state"] == "published" else set())
        require(set(outbox) == fields and type(outbox["attempt"]) is int and outbox["attempt"] >= 0
                and schedule is not None and outbox["id"] == schedule.get("outbox_entry_id"), "outbox-invalid")
        proof_identifier(outbox["id"]); created = instant(proof_time(outbox["created_at"]))
        if "published_at" in outbox: require(created <= instant(proof_time(outbox["published_at"])), "outbox-time-invalid")
    message = value["delivery_message"]
    if outbox is None: require(message is None, "delivery-message-invalid")
    else:
        fields = {"id", "type", "version", "enqueuedAt", "idempotencyKey", "payload"}
        require(isinstance(message, dict), "delivery-message-invalid")
        for optional in ("correlationId", "causationId"):
            if optional in message:
                require(isinstance(message[optional], str) and 0 < len(message[optional]) <= 256, "delivery-message-invalid")
                fields.add(optional)
        require(set(message) == fields and message["id"] == message["idempotencyKey"] == outbox["id"]
                and message["type"] == PROOF_JOBS[scope] and type(message["version"]) is int and message["version"] == 1
                and message["enqueuedAt"] == value["observed_at"] and message["payload"] == {"outboxEntryId": outbox["id"]}, "delivery-message-invalid")
    if processing is not None:
        require(isinstance(processing, dict) and processing.get("state") in {"claimed", "retry-eligible", "completed"}, "processing-invalid")
        fields = {"outbox_entry_id", "state", "attempt"}
        if processing["state"] == "retry-eligible": fields.add("released_at")
        if processing["state"] == "completed": fields.add("completion")
        if "retry_at" in processing:
            require(processing["state"] == "retry-eligible", "processing-invalid"); fields.add("retry_at")
        require(set(processing) == fields and type(processing["attempt"]) is int and processing["attempt"] > 0
                and schedule is not None and processing["outbox_entry_id"] == schedule.get("outbox_entry_id"), "processing-invalid")
        proof_identifier(processing["outbox_entry_id"])
        if "released_at" in processing: proof_time(processing["released_at"])
        if "retry_at" in processing: require(instant(proof_time(processing["retry_at"])) >= instant(processing["released_at"]), "processing-time-invalid")
        if "completion" in processing:
            completion = processing["completion"]
            require(isinstance(completion, dict) and set(completion) == {"outcome", "completed_at"}
                    and completion["outcome"] in {"succeeded", "terminal-failure"}, "processing-invalid")
            proof_time(completion["completed_at"])
    require(isinstance(application, dict) and type(application.get("present")) is bool
            and application.get("kind") == ("entity" if scope == "entity-smoke" else "acceptance"), "application-invalid")
    fields = {"kind", "present"}
    if application["present"]:
        if scope == "core-server-persistence":
            fields.add("fact_digest")
            require(isinstance(application.get("fact_digest"), str) and re.fullmatch(r"[a-f0-9]{64}", application["fact_digest"]), "application-invalid")
        else:
            fields.update({"visibility", "lifecycle_state"})
            require(application.get("visibility") in {"active", "archived"} and application.get("lifecycle_state") in {"active", "deleted"}, "application-invalid")
            if application["lifecycle_state"] == "deleted":
                fields.update({"deleted_at", "restore_eligible_until"})
                require(instant(proof_time(application.get("deleted_at"))) <= instant(proof_time(application.get("restore_eligible_until"))), "application-invalid")
    require(set(application) == fields, "application-invalid")
    return value
