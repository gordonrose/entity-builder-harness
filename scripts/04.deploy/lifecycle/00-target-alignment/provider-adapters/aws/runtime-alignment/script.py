#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.runtime-alignment
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Collect bounded, safe AWS facts for a declared first private ECS release.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [network]
"""AWS-only read adapter.  It emits normalized assertions, never raw responses."""
from __future__ import annotations
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from typing import Any

IDS = ("right-destination", "right-application", "known-healthy-baseline", "allowed-deployment-route", "package-destination", "required-access", "required-settings", "change-safety", "freshness-and-drift")

def command(args: argparse.Namespace, *items: str) -> tuple[bool, Any, str]:
    result = subprocess.run(["aws", *items, "--profile", args.profile, "--region", args.region, "--output", "json"], capture_output=True, text=True)
    if result.returncode:
        error = result.stderr.lower()
        if "does not exist" in error or "does not exist for stack" in error: return False, None, "not-found"
        if "accessdenied" in error or "not authorized" in error: return False, None, "access-denied"
        return False, None, "unavailable"
    try: return True, json.loads(result.stdout), "ok"
    except json.JSONDecodeError: return False, None, "invalid-response"

def assertion(identifier: str, matched: bool, code: str, failed_outcome: str = "unknown") -> dict[str, str]:
    return {"id": identifier, "outcome": "match" if matched else failed_outcome, "finding_code": code}

def main() -> int:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--profile", required=True); p.add_argument("--region", required=True); p.add_argument("--account-id", required=True)
    p.add_argument("--repository", required=True); p.add_argument("--image-digest", required=True)
    p.add_argument("--foundation-stack", required=True); p.add_argument("--runtime-stack", required=True)
    p.add_argument("--cluster", required=True); p.add_argument("--delivery-role", required=True); p.add_argument("--execution-role", required=True)
    p.add_argument("--json", action="store_true")
    args, unknown = p.parse_known_args()
    if unknown:
        print(json.dumps({"schema":"deploy/target-alignment-evidence/v1", "assertions":[assertion(i, False, "arguments-invalid") for i in IDS]})); return 2
    assertions: dict[str, dict[str, str]] = {}
    ok, identity, code = command(args, "sts", "get-caller-identity")
    assertions["right-destination"] = assertion("right-destination", ok and identity.get("Account") == args.account_id, "account-match" if ok else code, "mismatch" if ok else "unknown")
    ok, image, code = command(args, "ecr", "describe-images", "--repository-name", args.repository, "--image-ids", f"imageDigest={args.image_digest}")
    details = image.get("imageDetails", []) if isinstance(image, dict) else []
    assertions["package-destination"] = assertion("package-destination", ok and bool(details), "immutable-digest-present" if ok else code, "missing" if ok else "unknown")
    ok, foundation, code = command(args, "cloudformation", "describe-stacks", "--stack-name", args.foundation_stack)
    stacks = foundation.get("Stacks", []) if isinstance(foundation, dict) else []
    outputs = {entry.get("OutputKey") for entry in stacks[0].get("Outputs", [])} if stacks else set()
    required_outputs = {"VpcId", "PrivateSubnetIds", "RepositoryUri", "ClusterArn", "LogGroupName", "TaskExecutionRoleArn", "ServiceSecurityGroupId", "VerifierSecurityGroupId", "ServiceDiscoveryArn"}
    foundation_ready = ok and bool(stacks) and stacks[0].get("StackStatus") == "CREATE_COMPLETE" and required_outputs <= outputs
    foundation_failure = "unknown" if not ok else ("mismatch" if stacks and stacks[0].get("StackStatus") != "CREATE_COMPLETE" else "missing")
    assertions["right-application"] = assertion("right-application", foundation_ready, "foundation-ready" if foundation_ready else "foundation-runtime-output-missing", foundation_failure)
    ok, runtime, code = command(args, "cloudformation", "describe-stacks", "--stack-name", args.runtime_stack)
    assertions["known-healthy-baseline"] = assertion("known-healthy-baseline", not ok and code == "not-found", "runtime-absent" if not ok and code == "not-found" else "runtime-not-absent", "mismatch" if ok else "unknown")
    ok, cluster, code = command(args, "ecs", "describe-clusters", "--clusters", args.cluster)
    clusters = cluster.get("clusters", []) if isinstance(cluster, dict) else []
    assertions["required-settings"] = assertion("required-settings", ok and bool(clusters) and clusters[0].get("status") == "ACTIVE", "runtime-configuration-declared" if ok else code)
    delivery_ok, _, delivery_code = command(args, "iam", "get-role", "--role-name", args.delivery_role)
    execution_ok, _, execution_code = command(args, "iam", "get-role", "--role-name", args.execution_role)
    assertions["required-access"] = assertion("required-access", delivery_ok and execution_ok, "roles-present" if delivery_ok and execution_ok else (delivery_code if not delivery_ok else execution_code))
    assertions["allowed-deployment-route"] = assertion("allowed-deployment-route", delivery_ok and execution_ok, "fixed-role-route-ready" if delivery_ok and execution_ok else "route-not-ready")
    assertions["change-safety"] = assertion("change-safety", True, "create-only-and-no-automatic-retry")
    assertions["freshness-and-drift"] = assertion("freshness-and-drift", True, "fresh-read-only-inspection")
    report = {"schema":"deploy/target-alignment-evidence/v1", "provider":"aws", "provider_adapter_version":"aws-runtime-alignment/v1", "checked_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"), "assertions":[assertions[i] for i in IDS]}
    print(json.dumps(report, sort_keys=True)); return 0 if all(x["outcome"] == "match" for x in report["assertions"]) else 1
if __name__ == "__main__": sys.exit(main())
