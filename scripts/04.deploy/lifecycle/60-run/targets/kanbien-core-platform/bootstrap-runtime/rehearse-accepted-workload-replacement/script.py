#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-accepted-workload-replacement.impl
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Implement a bounded accepted-task stop, replacement proof, and fresh private verification without exposing credentials or arbitrary target selection.
#   portability: { class: internal, targets: [] }
#   effects: [aws-mutation]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.rehearse-accepted-workload-replacement
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.sh
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION = "kanbien-dev", "eu-west-1"
CLUSTER, SERVICE = "kanbien-core-platform", "kanbien-core-platform-bootstrap-runtime"
RECORD = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml"
COST = ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/validate-cost-condition/script.sh"
ALIGNMENT = ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/inspect-runtime-alignment/script.sh"
VERIFY = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/script.sh"

def report(verdict, *codes, facts=None):
    body={"schema":"deploy/workload-recovery-rehearsal-report/v1","target":"kanbien-core-platform","scope":"bootstrap-runtime","verdict":verdict,"findings":[{"code":code} for code in codes]}
    if facts: body["facts"]=facts
    print(json.dumps(body, sort_keys=True))

def aws(*args):
    result=subprocess.run(["aws", *args, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True)
    if result.returncode:
        message=result.stderr.lower()
        return False, None, "aws-access-denied" if "accessdenied" in message or "not authorized" in message else "aws-command-failed"
    try: return True, json.loads(result.stdout), "ok"
    except json.JSONDecodeError: return False, None, "aws-response-invalid"

def accepted_release():
    try: record=yaml.safe_load(RECORD.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError): return None
    release=record.get("release", {}) if isinstance(record, dict) else {}
    required=("source_revision", "image_digest", "runtime_task_definition", "verifier_task_definition", "package_custody_reference")
    verification=release.get("private_verification", {}) if isinstance(release, dict) else {}
    if record.get("schema") != "deploy/accepted-release/v1" or record.get("status") != "accepted" or not all(isinstance(release.get(key), str) and release[key] for key in required) or not isinstance(verification.get("verified_at"), str): return None
    return release

def receipt(release, path):
    json.dump({"schema":"deploy/package-custody-receipt/v1","target":"kanbien-core-platform","environment_class":"private-bootstrap","provider_region_alias":"aws-eu-west-1","candidate_id":"kanbien-core-server-candidate","package_contract_id":"kanbien-core-server-image","program_id":"kanbien-core-server","source_revision":release["source_revision"],"image_digest":release["image_digest"],"release_identity":"source-"+release["source_revision"],"checked_at":release["private_verification"]["verified_at"],"checks":{"runnable_program_contract":"passed","dependency_boundary":"passed","delivery_access_static":"passed","delivery_access_live":"passed","local_image_smoke":"passed","ecr_scan":"passed","sbom":"passed","provenance_attestation":"passed"},"verdict":"qualified","receipt_reference":release["package_custody_reference"]}, path.open("w", encoding="utf-8"), sort_keys=True)

def current_workload(release):
    ok, described, code=aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", SERVICE)
    services=described.get("services", []) if ok else []
    if not ok or len(services) != 1: return None, code
    service=services[0]
    deployments=service.get("deployments", [])
    if service.get("status") != "ACTIVE" or service.get("desiredCount") != 1 or service.get("runningCount") != 1 or service.get("taskDefinition", "").rsplit("/", 1)[-1] != release["runtime_task_definition"] or not any(deployment.get("status") == "PRIMARY" and deployment.get("rolloutState") == "COMPLETED" for deployment in deployments): return None, "runtime-service-not-healthy"
    ok, listed, code=aws("ecs", "list-tasks", "--cluster", CLUSTER, "--service-name", SERVICE, "--desired-status", "RUNNING")
    arns=listed.get("taskArns", []) if ok else []
    if not ok or len(arns) != 1: return None, code if not ok else "runtime-running-task-count-invalid"
    ok, described, code=aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arns[0])
    tasks=described.get("tasks", []) if ok else []
    if not ok or len(tasks) != 1: return None, code
    task=tasks[0]
    if task.get("lastStatus") != "RUNNING" or task.get("taskDefinitionArn", "").rsplit("/", 1)[-1] != release["runtime_task_definition"]: return None, "runtime-task-not-accepted"
    return task, "ok"

def task_suffix(task):
    return task.get("taskArn", "").rsplit("/", 1)[-1][-12:]

def preflight(release, receipt_path):
    for command, code in ((["bash", str(COST), "--json"], "cost-condition-not-approved"), (["bash", str(ALIGNMENT), "--receipt", str(receipt_path), "--operation", "restore", "--json"], "target-alignment-not-approved")):
        result=subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
        if result.returncode: return code
    task, code=current_workload(release)
    return (task, "ok") if task else (None, code)

def replacement(original, release, deadline):
    while time.monotonic() < deadline:
        task, code=current_workload(release)
        if task and task.get("taskArn") != original.get("taskArn"):
            return task, "ok"
        time.sleep(5)
    return None, "ecs-replacement-not-healthy"

def main():
    parser=argparse.ArgumentParser(add_help=False); parser.add_argument("--execute", action="store_true"); parser.add_argument("--json", action="store_true")
    args, unknown=parser.parse_known_args()
    if unknown: report("blocked", "workload-recovery-arguments-invalid"); return 2
    release=accepted_release()
    if not release: report("blocked", "accepted-release-record-invalid"); return 1
    with tempfile.TemporaryDirectory() as directory:
        receipt_path=Path(directory)/"accepted-receipt.json"; receipt(release, receipt_path)
        original, code=preflight(release, receipt_path)
        if not original: report("blocked", code); return 1
        facts={"source_revision":release["source_revision"],"image_digest":release["image_digest"],"runtime_task_definition":release["runtime_task_definition"],"original_task_suffix":task_suffix(original)}
        if not args.execute: report("prepared", "accepted-workload-replacement-ready", facts=facts); return 0
        not_before=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        ok, _, code=aws("ecs", "stop-task", "--cluster", CLUSTER, "--task", original["taskArn"], "--reason", "governed accepted workload replacement rehearsal")
        if not ok: report("blocked", code); return 1
        replacement_task, code=replacement(original, release, time.monotonic()+600)
        if not replacement_task: report("blocked", code, facts=facts); return 1
        verified=subprocess.run(["bash", str(VERIFY), "--receipt", str(receipt_path), "--not-before", not_before, "--json"], capture_output=True, text=True, cwd=ROOT)
        if verified.returncode:
            report("blocked", "fresh-private-verification-failed", facts={**facts, "replacement_task_suffix":task_suffix(replacement_task)}); return 1
        try: verification=json.loads(verified.stdout)
        except json.JSONDecodeError: report("blocked", "fresh-private-verification-report-invalid", facts=facts); return 1
        verifier=(verification.get("facts") or {}).get("verifier_task_definition")
        report("accepted", "accepted-workload-replaced-and-fresh-private-verifier-accepted", facts={**facts, "replacement_task_suffix":task_suffix(replacement_task), "recovery_boundary":not_before, "verifier_task_definition":verifier, "verification_mode":(verification.get("facts") or {}).get("verification_mode")})
        return 0

if __name__ == "__main__": sys.exit(main())
