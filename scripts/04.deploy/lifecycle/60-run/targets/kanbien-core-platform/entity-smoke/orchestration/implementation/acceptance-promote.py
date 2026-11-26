#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.promote-acceptance.implementation
#   version: 2
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Guard ordinary local release/scope promotion with fresh exact-candidate proof and original custody reconciliation, never provider mutation.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.promote-acceptance
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/orchestration/commands/promote-acceptance.sh
import argparse
import importlib.util
import json
from pathlib import Path
import re


spec = importlib.util.spec_from_file_location("entity_smoke_acceptance_promote_state", (Path(__file__).resolve().parents[2] / "acceptance-evaluation/implementation/acceptance-state.py"))
STATE = importlib.util.module_from_spec(spec); spec.loader.exec_module(STATE)
K, S = STATE.K, STATE.S


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(K.CollectionFailure("acceptance-promotion-arguments-invalid"))
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--candidate-record", required=True, type=Path)
    parser.add_argument("--scope-contract", required=True, type=Path)
    parser.add_argument("--expected-predecessor", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    K.require(args.write and re.fullmatch(r"none|release-[a-f0-9]{24}", args.expected_predecessor), "acceptance-promotion-arguments-invalid")
    relative = (K.C.CONTRACT.parent / "declaration-contract.yml").relative_to(K.C.ROOT)
    if args.validate_arguments:
        K.require(args.scope_contract.parts[-len(relative.parts):] == relative.parts, "acceptance-promotion-scope-invalid")
    else: K.require(args.scope_contract.absolute() == K.C.ROOT / relative, "acceptance-promotion-scope-invalid")
    return args


def current_runtime(packet, provider):
    """Recheck only the live workload; retained proof is already validated."""
    runtime, binding = packet["runtime"], packet["binding"]
    database = K.C.ALIGN.only(provider("rds", "describe-db-instances",
        DBInstanceIdentifier=K.C.ALIGN.DATABASE), "DBInstances")
    K.require(database.get("DBInstanceStatus") == "available"
              and database.get("DbiResourceId") == runtime["source_resource_id"]
              and database.get("DBName") == runtime["database_name"],
              "acceptance-promotion-database-changed")
    service = K.C.RESOURCE.service(provider, runtime["definition"], 1)
    arns = K.C.RESOURCE.running_service_tasks(provider)
    K.require(len(arns) == 1 and arns[0] == runtime["task"]
              and service.get("runningCount") == 1 and service.get("pendingCount") == 0,
              "acceptance-promotion-candidate-not-current")
    running = K.C.RESOURCE.task(provider, arns[0], runtime["definition"], binding["image_digest"])
    K.require(running.get("lastStatus") == "RUNNING" and running.get("healthStatus") == "HEALTHY",
              "acceptance-promotion-candidate-not-current")


def run(args, provider, progress):
    owner = STATE.State()
    candidate = owner.candidate(args.candidate_record)
    lock = owner.root / ".release-succession.lock"
    K.C.RESOURCE.CONTROL.no_symlinks(lock)
    with lock.open("a+b") as handle:
        S.fcntl.flock(handle.fileno(), S.fcntl.LOCK_EX)
        candidate = owner.candidate(args.candidate_record)
        identifier = S.release_id(candidate["identity"])
        before = S.current(owner.root)
        already_current = before is not None and before["release_id"] == identifier
        history = owner.root / S.HISTORY_DIRECTORY / (identifier + ".yml")
        reconciling = before is None and history.exists()
        if reconciling:
            original = S.history_identity(owner.root, {"path": str(history.relative_to(owner.root)), "sha256": K.C.digest_file(history)})
            K.require(original == (K.TARGET, K.SCOPE, identifier, None) and args.expected_predecessor == "none", "acceptance-promotion-history-conflict")
        if already_current:
            owner.current()
        elif not reconciling:
            selected = K.resolve_inputs(K.parse(["--inputs", str(args.inputs), "--write-candidate"]))
            K.require((getattr(selected, "expected_predecessor", None) or "none") == args.expected_predecessor,
                      "acceptance-promotion-predecessor-mismatch")
            custody = K.C.ALIGN.read_receipt(selected.receipt.absolute())
            K.C.ALIGN.source_preflight(custody, retained_source_evidence=K.retained_source_evidence(selected, custody))
            current_runtime(candidate["packet"], provider)
            rechecked = owner.candidate(args.candidate_record)
            K.require(rechecked["sha256"] == candidate["sha256"], "acceptance-promotion-candidate-changed")
            K.C.retained_controller({"binding": candidate["packet"]["binding"],
                "plan": {"controller_sha256": candidate["packet"]["controller_sha256"]}}, K.C.source_digest())
        progress["effect"] = "release-custody-reconciliation-required"
        release_verdict, release_id = S.promote(owner.root, target=K.TARGET, scope=K.SCOPE, identity=candidate["identity"],
            source_path=candidate["path"], source_digest=candidate["sha256"], expected_predecessor=args.expected_predecessor, legacy=False)
        progress["effect"] = "accepted-reference-current-scope-transition-reconciliation-required"
        scope_owner = K.module("entity_smoke_acceptance_scope_promotion", K.C.ROOT / "scripts/04.deploy/lifecycle/60-run/promote-accepted-scope/script.py")
        try: scope = scope_owner.promote(args.scope_contract, K.C.ROOT, write=True)
        except ValueError as failure:
            code = str(failure)
            raise K.CollectionFailure(code if re.fullmatch(r"scope-promotion-[a-z0-9-]+", code) else "acceptance-scope-promotion-not-confirmed") from None
        owner.current()
        return {"verdict": "accepted" if not (already_current or reconciling) else "retained", "release_id": release_id,
            "release_verdict": release_verdict, "scope_verdict": scope["verdict"], "evidence_class": "live", "current_readiness": False,
            "effect": "local-custody-and-scope-only-no-provider-mutation"}


def main():
    progress = {"effect": "not-started"}
    try:
        args = parse()
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        result = run(args, K.Provider(), progress)
        print(json.dumps({"schema": "deploy/entity-smoke-acceptance-promotion-report/v1", "target": K.TARGET, "scope": K.SCOPE, **result}, sort_keys=True)); return 0
    except Exception as failure:
        print(json.dumps({"schema": "deploy/entity-smoke-acceptance-promotion-report/v1", "target": K.TARGET, "scope": K.SCOPE,
            "verdict": "blocked", **K.failure_details(failure), **progress, "current_readiness": False}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
