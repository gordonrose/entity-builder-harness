#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.persistence-acceptance-updates
#   version: 2
#   status: active
#   created_on: "2026-11-19"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind persistence's fresh workload observations to shared recovery-input policy and exact accepted predecessor custody.
#   portability: {class: internal, targets: []}
#   effects: [read-only, network]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py
import re

SCHEMA = "deploy/persistence-collected-acceptance/v2"
OBSERVATION = "current-acceptance-observation"


def require(C, condition, code):
    if not condition:
        raise C.EvidenceFailure(code)


def policy(C):
    route = C.route_contract()
    return C.route_module().proof_policy().policy(C.route_module().document(C.ROOT / route["accepted_record"]["schema_path"]))


def qualification(C, package, database):
    S, P = C.succession_module(), C.route_module().proof_policy()
    C.parsed_time(database.get("source_created_at"))
    require(C, database.get("database") == C.DATABASE and isinstance(database.get("source_resource_id"), str)
            and re.fullmatch(r"db-[A-Za-z0-9-]+", database["source_resource_id"]), "acceptance-recovery-binding-changed")
    binding = {"source_revision": package["source_revision"],
        "configuration_contract_sha256": S.sha256_bytes(C.scope_contract().read_bytes()),
        "permission_contract_sha256": S.sha256_bytes((C.ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml").read_bytes()),
        "dependency_incarnation_sha256": S.sha256_bytes(S.canonical({key: database[key] for key in ("database", "source_created_at", "source_resource_id")}))}
    paths = P.recovery_input_paths(policy(C)["recovery_input_paths"])
    return {"binding": binding, "input_paths": paths,
            "inputs_sha256": P.recovery_input_tree(package["source_revision"], paths, root=C.ROOT)}


def accepted(C, identifier, *, seen=None):
    """Only accepted, hash-validated candidates can supply recovery evidence."""
    S = C.succession_module()
    seen = set() if seen is None else seen
    require(C, isinstance(identifier, str) and re.fullmatch(r"release-[a-f0-9]{24}", identifier)
            and identifier not in seen, "acceptance-evidence-predecessor-invalid")
    seen.add(identifier)
    history, _ = S.history_record_for_id(C.EVIDENCE_ROOT, identifier)
    evidence = history["evidence"]
    require(C, history.get("target") == C.TARGET and history.get("scope") == C.SCOPE
            and evidence["kind"] == "verified-release-candidate", "acceptance-recovery-requalification-required")
    path = S.under(C.EVIDENCE_ROOT, C.EVIDENCE_ROOT / evidence["path"], S.CANDIDATE_DIRECTORY)
    candidate, raw = S.document(path)
    target, scope, _, identity = S.candidate_identity(candidate, C.EVIDENCE_ROOT, current_contracts=False)
    require(C, (target, scope) == (C.TARGET, C.SCOPE) and S.release_id(identity) == identifier
            and S.sha256_bytes(raw) == evidence["sha256"], "acceptance-evidence-predecessor-invalid")
    selected = candidate["proof_set"].get(OBSERVATION)
    require(C, isinstance(selected, dict), "acceptance-recovery-requalification-required")
    record, _ = S.document(S.retained_evidence_file(C.EVIDENCE_ROOT, C.EVIDENCE_ROOT / selected["path"]))
    require(C, isinstance(record.get("qualification"), dict), "acceptance-recovery-requalification-required")
    if record.get("schema") == SCHEMA:
        require(C, identity.get("expected_predecessor") == record.get("predecessor", {}).get("release_id"),
                "acceptance-evidence-predecessor-binding-invalid")
        validate(C, record, seen=seen)
    else:
        C.validate_record(record, evidence_class=C.EVIDENCE_CLASS, historical=True)
    q = record["qualification"]
    require(C, q.get("binding", {}).get("source_revision") == identity["source_revision"]
            and record["release"]["image_digest"] == identity["image_digest"]
            and all(q["binding"].get(key + "_sha256") == identity[key]["sha256"]
                    for key in ("configuration_contract", "permission_contract")),
            "acceptance-evidence-predecessor-binding-invalid")
    return record, {"release_id": identifier, "candidate_record": evidence["path"], "candidate_sha256": evidence["sha256"]}


def fresh_proofs(C, record, previous):
    proofs = record["provider_observation"]["proofs"]
    names = record["fresh_tasks"]
    require(C, isinstance(names, list) and names == list(dict.fromkeys(names)) and len(names) == 4
            and set(names) == {"migration-applied-state", "effective-privilege", "runtime-identity-initial-access", "rollback-final-read"},
            "acceptance-evidence-fresh-proof-set-invalid")
    profile = record.get("qualification_profile")
    required = C.required_proofs(record["release"], None, None, selected=names, qualification_profile=profile)
    arguments = [name + "=" + str(C.ROOT / item["receipt"]) for name, item in proofs.items()]
    observed = C.parse_proof_receipts(arguments, required, C.contract_deadlines(), qualification_profile=profile)
    require(C, observed == proofs, "acceptance-evidence-fresh-proof-mismatch")
    runtime = record["provider_observation"]["current_service"]
    after = max(C.parsed_time(runtime["started_at"]), C.parsed_time(previous["acceptance"]["accepted_at"]))
    end = C.parsed_time(record["acceptance"]["accepted_at"])
    tasks = set()
    for name, item in observed.items():
        require(C, after <= C.parsed_time(item["started_at"]) <= C.parsed_time(item["stopped_at"]) <= end
                and item["task_arn"] not in tasks, "acceptance-evidence-fresh-proof-stale-or-mismatched")
        tasks.add(item["task_arn"])
        definition = record["definitions"]["verifier" if required[name][0] == "verifier" else "administration"]
        require(C, item["task_definition"] == definition, "acceptance-evidence-fresh-proof-definition-mismatch")
        if required[name][0] == "verifier":
            proof = C.json.loads((C.ROOT / item["receipt"]).read_text())
            require(C, proof["context"]["record_id"] == "core-persistence-acceptance-v1",
                    "acceptance-evidence-retained-record-mismatch")
    health = record["provider_observation"]["current_health"]
    require(C, health["image_digest"] == record["release"]["image_digest"]
            and health["task_definition"] == record["definitions"]["verifier"]
            and health["result_code"] == "KANBIEN_CORE_PERSISTENCE_HEALTHY"
            and max(C.parsed_time(item["stopped_at"]) for item in observed.values()) <= C.parsed_time(health["started_at"])
            <= C.parsed_time(health["stopped_at"]) <= end,
            "acceptance-evidence-current-health-stale-or-mismatched")


def validate(C, record, *, seen=None):
    C.validate_scheduling(record)
    C.validate_scheduling_migrations(record)
    require(C, set(record) - {"scheduling_qualification", "qualification_profile", "scheduling_migrations"} == {"schema", "target", "scope", "status", "evidence_class", "release", "acceptance",
            "qualification", "predecessor", "applicability", "fresh_tasks", "definitions", "provider_observation"}
            and record["schema"] == SCHEMA and record["target"] == C.TARGET and record["scope"] == C.SCOPE
            and record["evidence_class"] == C.EVIDENCE_CLASS
            and record["status"] == ("accepted" if C.EVIDENCE_CLASS == "live" else "rehearsed"),
            "acceptance-evidence-successor-invalid")
    predecessor = record["predecessor"]
    previous, expected = accepted(C, predecessor["release_id"], seen=seen)
    require(C, predecessor == expected, "acceptance-evidence-predecessor-invalid")
    q, old = record["qualification"], previous["qualification"]
    P = C.route_module().proof_policy()
    require(C, set(q) == {"binding", "input_paths", "inputs_sha256"}
            and P.recovery_input_paths(q["input_paths"]) == q["input_paths"]
            and q["input_paths"] == old["input_paths"] and q["inputs_sha256"] == old["inputs_sha256"]
            and re.fullmatch(r"sha256:[a-f0-9]{64}", q["inputs_sha256"])
            and all(q["binding"].get(key) == old["binding"].get(key) for key in P.BINDINGS)
            and q["binding"].get("source_revision") == record["release"]["source_revision"],
            "acceptance-recovery-binding-changed")
    expected_applicability = {"schema": "deploy/recovery-applicability/v1", "predecessor_source": old["binding"]["source_revision"],
        "candidate_source": q["binding"]["source_revision"], "input_paths": q["input_paths"], "inputs_sha256": q["inputs_sha256"]}
    require(C, record["applicability"] == expected_applicability, "acceptance-recovery-binding-changed")
    fresh_proofs(C, record, previous)


def collect(C, args):
    """Observe only; existing task controllers still own all fresh submissions."""
    S, P = C.succession_module(), C.route_module().proof_policy()
    current = S.current(C.EVIDENCE_ROOT)
    require(C, current is not None and current["release_id"] == args.expected_predecessor,
            "acceptance-evidence-predecessor-mismatch")
    previous, predecessor = accepted(C, args.expected_predecessor)
    package = C.receipt(args.receipt)
    policy_value = policy(C)
    names = policy_value["fresh_tasks"]
    profile = getattr(args, "qualification_profile", None)
    required = C.required_proofs(package, None, None, selected=names, qualification_profile=profile)
    observed = C.parse_proof_receipts(args.proof_receipt, required, C.contract_deadlines(), qualification_profile=profile)
    database = C.source_database_posture()
    q = qualification(C, package, database)
    old = previous["qualification"]
    require(C, q["input_paths"] == old.get("input_paths")
            and old.get("inputs_sha256") == P.recovery_input_tree(old["binding"]["source_revision"], q["input_paths"], root=C.ROOT),
            "acceptance-recovery-requalification-required")
    applicability = P.recovery_applicability(old["binding"], q["binding"], q["input_paths"], root=C.ROOT)
    outputs = C.stack_outputs()
    digest = C.qualified_runnable_digest(package)
    runtime = C.current_service(outputs["CoreServerPersistenceTaskDefinitionArn"], package, digest)
    task = C.observed_task(runtime["running_task"])
    runtime = {**runtime, "started_at": task.get("startedAt")}
    health = C.current_health(args.current_health_task, outputs["CoreServerPersistenceVerifierTaskDefinitionArn"], package, digest)
    record = {"schema": SCHEMA, "target": C.TARGET, "scope": C.SCOPE, "evidence_class": C.EVIDENCE_CLASS,
        "status": "accepted" if C.EVIDENCE_CLASS == "live" else "rehearsed", "release": package,
        "acceptance": {"accepted_at": C.datetime.now(C.timezone.utc).isoformat().replace("+00:00", "Z")},
        "qualification": q, "predecessor": predecessor, "applicability": applicability, "fresh_tasks": names,
        "definitions": {"administration": outputs["CoreServerPersistenceAdministrationTaskDefinitionArn"],
                        "verifier": outputs["CoreServerPersistenceVerifierTaskDefinitionArn"]},
        "provider_observation": {"current_service": runtime, "current_health": health, "proofs": observed}}
    C.attach_scheduling(record, args, database)
    validate(C, record)
    require(C, S.current(C.EVIDENCE_ROOT) == current, "acceptance-evidence-predecessor-mismatch")
    return record
