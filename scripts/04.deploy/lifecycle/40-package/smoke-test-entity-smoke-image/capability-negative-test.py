#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.image-negative-capabilities
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject forbidden packaged capabilities, production synthetic authentication and credential delivery to proof-only tasks in the actual image.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network]
#   used_by:
#   - id: deploy.command.smoke-test-entity-smoke-image
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/script.sh
import argparse
import json
import re
import subprocess
import sys

CANARY = "entity-smoke-negative-credential-canary"


def invoke(args, expected=0):
    try:
        result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=30, check=False)
    except (OSError, UnicodeError, subprocess.SubprocessError):
        raise ValueError("image-negative-observation-unavailable") from None
    if result.returncode != expected or CANARY in result.stdout + result.stderr:
        raise ValueError("image-negative-result-not-confirmed")
    return result


def rejected(image, entrypoint, environment, field, reason):
    args = ["run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
    for key, value in environment.items():
        args.extend(["-e", key + "=" + value])
    result = invoke([*args, image, "artifacts/" + entrypoint + ".main.js"], expected=1)
    records = []
    for line in result.stderr.splitlines():
        try: records.append(json.loads(line))
        except (TypeError, json.JSONDecodeError): continue
    diagnostic = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.configuration-invalid", "definitionVersion": 1,
                  "detail": {"field": field, "reason": reason, "effect": "not-started"}}
    if len(records) != 1 or records[0] != {"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": diagnostic}:
        raise ValueError("image-negative-diagnostic-not-confirmed")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: parser.exit(2, "ENTITY_SMOKE_NEGATIVE_ARGUMENTS_INVALID\n")
    parser.add_argument("--image", required=True)
    args, unknown = parser.parse_known_args()
    if unknown or re.fullmatch(r"kanbien-entity-smoke:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", args.image) is None:
        raise ValueError("image-negative-arguments-invalid")
    invoke(["image", "inspect", args.image, "--format", "{{.Id}}"])
    program = r'''
const assert=require('node:assert/strict');
assert.notEqual(process.getuid(),0);
const app=require('/app/artifacts/node_modules/@kanbien/app-entity-smoke');
assert.equal(typeof app.createEntitySmokePersistenceApp,'function');
for(const name of ['@kanbien/platform-workers','@kanbien/product-kanbien-platform','@kanbien/app-platform-smoke','@kanbien/platform-adapter-aws-observability-cloudwatch']){
  assert.throws(()=>require(name),error=>error.code==='MODULE_NOT_FOUND');
}
process.stdout.write('ENTITY_SMOKE_IMAGE_CAPABILITY_BOUNDARY_CONFIRMED\n');
'''
    result = invoke(["run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--entrypoint", "/nodejs/bin/node", args.image, "-e", program])
    if result.stdout.strip() != "ENTITY_SMOKE_IMAGE_CAPABILITY_BOUNDARY_CONFIRMED":
        raise ValueError("image-negative-capability-boundary-not-confirmed")
    rejected(args.image, "kanbien-entity-smoke-migration", {}, "operation", "invalid")
    rejected(args.image, "kanbien-entity-smoke-verifier", {"ENTITY_SMOKE_VERIFICATION_OPERATION": "ready", "PERSISTENCE_ADMINISTRATOR_CREDENTIALS": CANARY}, "identity", "mismatch")
    rejected(args.image, "kanbien-entity-smoke-database-proof", {"ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "permissions", "ENTITY_SMOKE_PROOF_LABEL": "entity-smoke-" + "a" * 24, "PERSISTENCE_ADMINISTRATOR_CREDENTIALS": CANARY}, "identity", "mismatch")
    rejected(args.image, "kanbien-entity-smoke", {
        "NODE_ENV": "production", "PLATFORM_DEPLOYMENT_EXPOSURE": "private",
        "PERSISTENCE_POSTGRES_HOST": "postgres", "PERSISTENCE_POSTGRES_PORT": "5432",
        "PERSISTENCE_POSTGRES_DATABASE": "entitysmoke", "PERSISTENCE_POSTGRES_SCHEMA": "entity_smoke",
        "PERSISTENCE_POSTGRES_CA_PATH": "/app/assets/rds-eu-west-1-bundle.crt", "PERSISTENCE_POSTGRES_IAM_REGION": "eu-west-1",
        "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE": "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-ABCDEFGHIJKLMNOP/entity_smoke_runtime",
        "PERSISTENCE_RUNTIME_DATABASE_USERNAME": "entity_smoke_runtime", "ENTITY_SMOKE_LOCAL_QUALIFICATION_TOKEN": "entity-smoke-disposable-fixture",
    }, "identity", "invalid")
    print(json.dumps({"schema": "deploy/entity-smoke-image-negative-proof/v1", "verdict": "passed", "code": "ENTITY_SMOKE_IMAGE_NEGATIVE_CAPABILITIES_PROVEN",
                      "cases": ["nonroot-and-forbidden-imports", "explicit-migration-only", "http-verifier-no-credentials", "database-proof-no-administrator", "production-no-synthetic-authentication"], "aws_observation": False}))
    return 0


if __name__ == "__main__":
    try: status = main()
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        print(json.dumps({"schema": "deploy/entity-smoke-image-negative-proof/v1", "verdict": "failed", "code": "ENTITY_SMOKE_IMAGE_NEGATIVE_PROOF_NOT_CONFIRMED"}), file=sys.stderr)
        status = 1
    raise SystemExit(status)
