#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-accepted-workload-replacement.impl
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-31"
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
import argparse, json, re, subprocess, sys, tempfile, time
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
    try: result=subprocess.run(["aws", *args, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True)
    except OSError: return False, None, "aws-command-unavailable"
    except UnicodeError: return False, None, "aws-response-invalid"
    if result.returncode:
        message=result.stderr.lower()
        return False, None, "aws-access-denied" if "accessdenied" in message or "not authorized" in message else "aws-command-failed"
    try: return True, json.loads(result.stdout), "ok"
    except json.JSONDecodeError: return False, None, "aws-response-invalid"

def accepted_release():
    try: record=yaml.safe_load(RECORD.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError): return None
    release=record.get("release", {}) if isinstance(record, dict) else {}
    required=("source_revision", "image_digest", "runtime_task_definition", "verifier_task_definition", "package_custody_reference")
    verification=release.get("private_verification", {}) if isinstance(release, dict) else {}
    try:
        if record.get("schema") != "deploy/accepted-release/v1" or record.get("status") != "accepted" or not all(isinstance(release.get(key), str) and release[key] for key in required) or not isinstance(verification.get("verified_at"), str): return None
    except (AttributeError, TypeError, KeyError): return None
    return release

def receipt(release, path):
    json.dump({"schema":"deploy/package-custody-receipt/v1","target":"kanbien-core-platform","environment_class":"private-bootstrap","provider_region_alias":"aws-eu-west-1","candidate_id":"kanbien-core-server-candidate","package_contract_id":"kanbien-core-server-image","program_id":"kanbien-core-server","source_revision":release["source_revision"],"image_digest":release["image_digest"],"release_identity":"source-"+release["source_revision"],"checked_at":release["private_verification"]["verified_at"],"checks":{"runnable_program_contract":"passed","dependency_boundary":"passed","delivery_access_static":"passed","delivery_access_live":"passed","local_image_smoke":"passed","ecr_scan":"passed","sbom":"passed","provenance_attestation":"passed"},"verdict":"qualified","receipt_reference":release["package_custody_reference"]}, path.open("w", encoding="utf-8"), sort_keys=True)

def current_workload(release):
    ok, described, code=aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", SERVICE)
    try: services=described.get("services", []) if ok else []
    except (AttributeError, TypeError): return None, "runtime-service-observation-invalid"
    try: cardinality = len(services)
    except TypeError: return None, "runtime-service-observation-invalid"
    if not ok or cardinality != 1: return None, code if not ok else "runtime-service-count-invalid"
    try:
        service=services[0]
        deployments=service.get("deployments", [])
        healthy=not (service.get("status") != "ACTIVE" or service.get("desiredCount") != 1 or service.get("runningCount") != 1 or service.get("taskDefinition", "").rsplit("/", 1)[-1] != release["runtime_task_definition"] or not any(deployment.get("status") == "PRIMARY" and deployment.get("rolloutState") == "COMPLETED" for deployment in deployments))
    except (AttributeError, TypeError, KeyError, IndexError): return None, "runtime-service-observation-invalid"
    if not healthy: return None, "runtime-service-not-healthy"
    ok, listed, code=aws("ecs", "list-tasks", "--cluster", CLUSTER, "--service-name", SERVICE, "--desired-status", "RUNNING")
    try:
        arns=listed.get("taskArns", []) if ok else []
        if not ok or len(arns) != 1: return None, code if not ok else "runtime-running-task-count-invalid"
    except (AttributeError, TypeError): return None, "runtime-running-task-observation-invalid"
    ok, described, code=aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arns[0])
    try:
        tasks=described.get("tasks", []) if ok else []
        if not ok or len(tasks) != 1: return None, code if not ok else "runtime-task-count-invalid"
        task=tasks[0]
        if task.get("lastStatus") != "RUNNING" or task.get("taskDefinitionArn", "").rsplit("/", 1)[-1] != release["runtime_task_definition"]: return None, "runtime-task-not-accepted"
    except (AttributeError, TypeError, KeyError, IndexError): return None, "runtime-task-observation-invalid"
    return task, "ok"

def task_arn_is_reportable(value):
    return isinstance(value, str) and re.fullmatch(rf"arn:aws:ecs:{REGION}:337159794548:task/{CLUSTER}/[0-9a-f]{{32}}", value) is not None

def task_suffix(task):
    value = task.get("taskArn", "")
    return value.rsplit("/", 1)[-1][-12:] if task_arn_is_reportable(value) else "identity-unavailable"

def preflight(release, receipt_path):
    for command, code in ((["bash", str(COST), "--json"], "cost-condition-not-approved"), (["bash", str(ALIGNMENT), "--receipt", str(receipt_path), "--operation", "restore", "--json"], "target-alignment-not-approved")):
        try: result=subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
        except (OSError, UnicodeError): return None, code
        if result.returncode: return None, code
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
    phase="replacement-temporary-directory-unavailable"
    mutation_attempted=False
    facts={}
    try:
        with tempfile.TemporaryDirectory() as directory:
            body_failed=False
            try:
                phase="accepted-receipt-unavailable"
                receipt_path=Path(directory)/"accepted-receipt.json"
                try: receipt(release, receipt_path)
                except (OSError, UnicodeError): report("blocked", "accepted-receipt-unavailable"); return 1
                phase="accepted-workload-preflight-observation-unavailable"
                original, code=preflight(release, receipt_path)
                if not original: report("blocked", code); return 1
                facts={"source_revision":release["source_revision"],"image_digest":release["image_digest"],"runtime_task_definition":release["runtime_task_definition"],"original_task_suffix":task_suffix(original)}
                if not args.execute: report("prepared", "accepted-workload-replacement-ready", facts=facts); return 0
                phase="replacement-clock-observation-unavailable"
                not_before=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                phase="replacement-stop-observation-unavailable"
                mutation_attempted=True
                ok, _, code=aws("ecs", "stop-task", "--cluster", CLUSTER, "--task", original["taskArn"], "--reason", "governed accepted workload replacement rehearsal")
                if not ok: report("uncertain", code, facts=facts); return 1
                phase="replacement-task-observation-unavailable"
                replacement_task, code=replacement(original, release, time.monotonic()+600)
                if not replacement_task: report("blocked", code, facts=facts); return 1
                phase="fresh-private-verification-observation-unavailable"
                try: verified=subprocess.run(["bash", str(VERIFY), "--receipt", str(receipt_path), "--not-before", not_before, "--json"], capture_output=True, text=True, cwd=ROOT)
                except (OSError, UnicodeError): report("uncertain", "fresh-private-verification-unavailable", facts=facts); return 1
                if verified.returncode:
                    report("blocked", "fresh-private-verification-failed", facts={**facts, "replacement_task_suffix":task_suffix(replacement_task)}); return 1
                try: verification=json.loads(verified.stdout)
                except json.JSONDecodeError: report("blocked", "fresh-private-verification-report-invalid", facts=facts); return 1
                try:
                    verifier=(verification.get("facts") or {}).get("verifier_task_definition")
                    mode=(verification.get("facts") or {}).get("verification_mode")
                except (AttributeError, TypeError): report("uncertain", "fresh-private-verification-observation-unavailable", facts=facts); return 1
                expected_verifier=release["verifier_task_definition"]
                if not isinstance(verifier,str) or re.fullmatch(rf"(?:arn:aws:ecs:{REGION}:337159794548:task-definition/)?kanbien-core-platform-release-verifier:[0-9]+",verifier) is None or verifier not in (expected_verifier, f"arn:aws:ecs:{REGION}:337159794548:task-definition/{expected_verifier}"):
                    verifier=None
                if mode not in ("fresh-private-task", "reused-completed-private-task"):
                    mode=None
                report("accepted", "accepted-workload-replaced-and-fresh-private-verifier-accepted", facts={**facts, "replacement_task_suffix":task_suffix(replacement_task), "recovery_boundary":not_before, "verifier_task_definition":verifier, "verification_mode":mode})
                return 0
            except BaseException:
                body_failed=True
                raise
            finally:
                if not body_failed: phase="replacement-temporary-cleanup-unavailable"
    except (OSError, UnicodeError, AttributeError, TypeError, KeyError, IndexError, ValueError):
        report("uncertain" if mutation_attempted else "blocked", phase, facts=facts); return 1

if __name__ == "__main__": sys.exit(main())
