#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.qualify-managed-handler-image
#   version: 2
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Qualify one immutable local image through its official Lambda runtime client under isolated Docker controls.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-scheduling
#     path: .github/workflows/publish-kanbien-core-platform-scheduling.yml
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
import uuid
import yaml

ROOT = Path(__file__).resolve().parents[5]
FIXTURE = Path(__file__).with_name("runtime-api-fixture.mjs")
PROGRAM = re.compile(r"kanbien-(?:core-server-persistence|entity-smoke)-scheduling-(?:dispatch|worker)")
DIGEST = re.compile(r"sha256:[a-f0-9]{64}")
CASES = {
    "invalid": ["configuration-rejection"],
    "dispatch": ["initialization-deadline", "warm-deadline", "preflight-malformed-rejected",
                 "preflight-deadline-rejected", "preflight-unavailable-database-rejected"],
    "worker": ["initialization-empty-batch", "malformed-record-retained", "deadline-record-retained", "unavailable-database-retained",
               "oversize-batch-rejected", "malformed-event-rejected", "warm-empty-batch", "preflight-malformed-rejected",
               "preflight-deadline-rejected", "preflight-unavailable-database-rejected"],
}
CONTRACT = ROOT / "infra/04.deploy/03.product/image/scheduling-lambda/image-contract.yml"
class QualificationFailure(Exception):
    def __init__(self, code, context=None): self.code, self.context = code, context; super().__init__(code)

def require(condition, code):
    if not condition: raise QualificationFailure(code)

def command(argv, timeout=30):
    try:
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, UnicodeError, subprocess.SubprocessError):
        raise QualificationFailure("managed-image-command-unavailable") from None
    if result.returncode != 0:
        context = None
        if argv[:3] == ["docker", "start", "--attach"] and len(result.stderr) <= 4096:
            try:
                value = json.loads(result.stderr)
                require(isinstance(value, dict) and set(value) == {"schema", "verdict", "code", "program_id", "mode", "case"}
                        and value["schema"] == "deploy/managed-runtime-invocation/v1" and value["verdict"] == "failed"
                        and value["code"] == "managed-runtime-invocation-failed" and isinstance(value["program_id"], str)
                        and PROGRAM.fullmatch(value["program_id"]) and value["mode"] in ("invalid", "valid"), "managed-image-command-failed")
                expected = CASES["invalid" if value["mode"] == "invalid" else ("dispatch" if value["program_id"].endswith("-dispatch") else "worker")]
                require(value["case"] in ["initialization", "completion", *expected], "managed-image-command-failed")
                context = {key: value[key] for key in ("program_id", "mode", "case")}
            except (ValueError, TypeError, QualificationFailure):
                pass
        raise QualificationFailure("managed-image-command-failed", context)
    return result.stdout

def read_contract(path=CONTRACT):
    try: value = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError): raise QualificationFailure("managed-image-contract-invalid") from None
    require(isinstance(value, dict) and value.get("schema") == "deploy/managed-handler-image-contract/v1", "managed-image-contract-invalid")
    require(value.get("id") == "scheduling-lambda-image-family" and value.get("runnable_program_contract") == "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml", "managed-image-contract-invalid")
    require(value.get("program_selection") == "managed-handler" and value.get("command") == ["handler.handler"], "managed-image-contract-invalid")
    require(value.get("runtime") == {"family": "aws-lambda-nodejs22", "architecture": "x86_64", "user": "10001:10001", "writable_path": "/tmp", "timeout_seconds": 60}, "managed-image-contract-invalid")
    base = value.get("runtime_base", {})
    require(isinstance(base, dict) and re.fullmatch(r"public\.ecr\.aws/lambda/nodejs@sha256:[a-f0-9]{64}", str(base.get("reference", ""))), "managed-image-contract-invalid")
    require(base.get("vulnerability_policy") == {"blocked_severities": ["CRITICAL", "HIGH"], "required_evidence": "published-ecr-scan", "exception": "explicit-approved-package-exception-only"}, "managed-image-contract-invalid")
    require(value.get("qualification") == {"interface": "aws-lambda-runtime-api", "network": "none", "filesystem": "read-only-with-tmpfs", "command": "scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification.py", "required": ["initialization", "configuration-rejection", "warm-invocation", "deadline-preservation", "native-batch-settlement", "safe-errors", "cleanup"]}, "managed-image-contract-invalid")
    return value

def inspect_image(image, program, run=command):
    require(isinstance(program, str) and PROGRAM.fullmatch(program), "managed-image-program-invalid")
    require(isinstance(image, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@:-]{1,240}", image), "managed-image-reference-invalid")
    try: rows = json.loads(run(["docker", "image", "inspect", image]))
    except (ValueError, TypeError): raise QualificationFailure("managed-image-inspection-invalid") from None
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict), "managed-image-inspection-invalid")
    value = rows[0]; configuration = value.get("Config", {})
    require(isinstance(configuration, dict), "managed-image-inspection-invalid")
    labels = configuration.get("Labels", {})
    require(isinstance(labels, dict), "managed-image-inspection-invalid")
    require(DIGEST.fullmatch(str(value.get("Id", ""))), "managed-image-identity-invalid")
    require(value.get("Architecture") == "amd64" and value.get("Os") == "linux", "managed-image-platform-invalid")
    require(configuration.get("Entrypoint") == ["/lambda-entrypoint.sh"] and configuration.get("Cmd") == ["handler.handler"], "managed-image-runtime-invalid")
    require(configuration.get("User") == "10001:10001" and configuration.get("WorkingDir") == "/var/task", "managed-image-isolation-invalid")
    require(labels.get("org.kanbien.program") == program, "managed-image-program-mismatch")
    require(re.fullmatch(r"[a-f0-9]{40}", str(labels.get("org.opencontainers.image.revision", ""))), "managed-image-source-invalid")
    environment = configuration.get("Env", [])
    require(isinstance(environment, list) and all(isinstance(item, str) for item in environment) and "NODE_ENV=production" in environment, "managed-image-environment-invalid")
    require(not any(item.startswith(("PERSISTENCE_LOCAL_QUALIFICATION_", "AWS_ACCESS_KEY_ID=", "AWS_SECRET_ACCESS_KEY=", "AWS_SESSION_TOKEN=", "NODE_OPTIONS=")) for item in environment), "managed-image-environment-invalid")
    require(type(value.get("Size")) is int and value["Size"] > 0, "managed-image-size-invalid")
    return value

def validate_result(value, program, mode):
    expected = CASES["invalid" if mode == "invalid" else ("dispatch" if program.endswith("-dispatch") else "worker")]
    require(isinstance(value, dict) and value == {
        "schema": "deploy/managed-runtime-invocation/v1", "verdict": "passed", "program_id": program,
        "mode": mode, "cases": expected, "responses": len(expected), "runtime_interface": "official-aws-lambda-client",
    }, "managed-image-invocation-proof-invalid")
    return expected

def qualify(image, program, run=command):
    start = time.monotonic()
    read_contract()
    inspected = inspect_image(image, program, run)
    results = {}
    for mode in ("invalid", "valid"):
        identity = "managed-proof-" + uuid.uuid4().hex
        container = None
        try:
            created = run(["docker", "create", "--name", identity, "--label", "kanbien.managed-proof=" + identity,
                "--network", "none", "--read-only", "--user", "10001:10001",
                "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m,mode=1777",
                "--mount", "type=bind,src=" + str(FIXTURE) + ",dst=/qualification/runtime-api-fixture.mjs,readonly",
                "--entrypoint", "/var/lang/bin/node", inspected["Id"],
                "/qualification/runtime-api-fixture.mjs", program, mode]).strip()
            require(re.fullmatch(r"[a-f0-9]{64}", created), "managed-image-container-identity-invalid")
            container = created
            output = run(["docker", "start", "--attach", container], timeout=60)
            require(len(output) <= 65536, "managed-image-invocation-proof-invalid")
            try: result = json.loads(output)
            except (TypeError, ValueError): raise QualificationFailure("managed-image-invocation-proof-invalid") from None
            results[mode] = validate_result(result, program, mode)
        except QualificationFailure as error:
            require(error.context is None or error.context["program_id"] == program and error.context["mode"] == mode,
                    "managed-image-invocation-proof-invalid")
            raise
        finally:
            if container is None:
                # A lost create response is reconciled only by this unique owned label.
                found = run(["docker", "ps", "--all", "--quiet", "--no-trunc", "--filter", "label=kanbien.managed-proof=" + identity]).split()
                require(len(found) <= 1 and all(re.fullmatch(r"[a-f0-9]{64}", item) for item in found), "managed-image-cleanup-unconfirmed")
                container = found[0] if found else None
            if container is not None:
                run(["docker", "rm", "--force", container])
    return {"schema": "deploy/managed-runtime-qualification/v1", "verdict": "passed",
        "program_id": program, "image_id": inspected["Id"],
        "source_revision": inspected["Config"]["Labels"]["org.opencontainers.image.revision"],
        "cases": results, "runtime_interface": "official-aws-lambda-client", "network": "none",
        "filesystem": "read-only-with-tmpfs", "user": "10001:10001",
        "image_bytes": inspected["Size"], "duration_seconds": round(time.monotonic() - start, 3)}

def main():
    parser = argparse.ArgumentParser()
    parser.error = lambda message: parser.exit(2, '{"verdict":"failed","code":"managed-image-arguments-invalid"}\n')
    parser.add_argument("--image", required=True); parser.add_argument("--program", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        require(not args.report.exists() and not args.report.is_symlink(), "managed-image-report-exists")
        result = qualify(args.image, args.program)
        with args.report.open("x", encoding="utf-8") as handle: json.dump(result, handle, sort_keys=True); handle.write("\n")
        print(json.dumps(result, sort_keys=True))
        return 0
    except QualificationFailure as error:
        print(json.dumps({"schema": "deploy/managed-runtime-qualification/v1", "verdict": "failed", "code": error.code,
                          **({"runtime_case": error.context["case"], "runtime_mode": error.context["mode"]} if error.context else {})}))
        return 1
    except (OSError, ValueError, TypeError, KeyError):
        print('{"verdict":"failed","code":"managed-image-qualification-unavailable"}')
        return 1
if __name__ == "__main__": raise SystemExit(main())
