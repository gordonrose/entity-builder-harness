#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.build-core-server-image.verify-payload
#   version: 2
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Fail closed when a compiled core-server package payload disagrees with its declared image or dependency boundary.
#   portability:
#     class: internal
#     targets: []
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.build-core-server-image
#     path: scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[5]
IMAGE_CONTRACT = ROOT / "infra/04.deploy/03.product/image/core-server/image-contract.yml"
PROGRAM_CONTRACT = ROOT / "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml"
DOCKERFILE = ROOT / "infra/04.deploy/03.product/image/core-server/Dockerfile"
DOCKERIGNORE = ROOT / "infra/04.deploy/03.product/image/core-server/Dockerfile.dockerignore"
BUILD_SCRIPT = ROOT / "scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh"
COMPILED_ENTRYPOINT = Path("kanbien-core-server.main.js")
EXPECTED_SHIMS = {
    "@kanbien/core", "@kanbien/platform-config", "@kanbien/platform-contracts",
    "@kanbien/platform-health", "@kanbien/platform-observability", "@kanbien/platform-runtime",
    "@kanbien/platform-security", "@kanbien/platform-server",
}
FORBIDDEN_MARKERS = {
    "app-platform-smoke": "@kanbien/app-platform-smoke",
    "platform-adapter-aws": "@kanbien/platform-adapter-aws",
    "platform-persistence": "@kanbien/platform-persistence",
    "platform-workers": "@kanbien/platform-workers",
    "product-kanbien-platform": "@kanbien/product-kanbien-platform",
    "staging-platform-server": "kanbien-platform-server.main",
    "postgresql": "postgresql",
    "relay": "kanbien-platform-relay",
    "worker": "kanbien-platform-worker",
}


class PayloadFailure(Exception):
    def __init__(self, *codes: str):
        self.codes = tuple(sorted(set(codes)))


def load_document(path: Path, missing_code: str, invalid_code: str) -> dict:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError:
        raise PayloadFailure(missing_code) from None
    except yaml.YAMLError:
        raise PayloadFailure(invalid_code) from None
    if not isinstance(document, dict):
        raise PayloadFailure(invalid_code)
    return document


def validate_source_contracts() -> dict:
    image = load_document(IMAGE_CONTRACT, "image-contract-missing", "image-contract-invalid")
    program = load_document(PROGRAM_CONTRACT, "program-contract-missing", "program-contract-invalid")
    if image.get("id") != "kanbien-core-server-image" or image.get("program_id") != "kanbien-core-server":
        raise PayloadFailure("image-contract-program-mismatch")
    command = [f"artifacts/{COMPILED_ENTRYPOINT.as_posix()}"]
    if image.get("compiled_entrypoint") != command[0] or image.get("command") != command:
        raise PayloadFailure("image-contract-command-invalid")
    runtime = image.get("runtime")
    base = image.get("runtime_base")
    health = image.get("health")
    if (
        not isinstance(runtime, dict)
        or runtime.get("user") != "nonroot"
        or not isinstance(base, dict)
        or not isinstance(base.get("reference"), str)
        or "@sha256:" not in base["reference"]
        or not isinstance(base.get("vulnerability_policy"), dict)
        or base["vulnerability_policy"].get("blocked_severities") != ["CRITICAL", "HIGH"]
        or base["vulnerability_policy"].get("required_evidence") != "published-ecr-scan"
        or not isinstance(health, dict)
        or health.get("proof") != "external-container-smoke"
    ):
        raise PayloadFailure("image-contract-runtime-policy-invalid")
    try:
        build_script = BUILD_SCRIPT.read_text(encoding="utf-8")
    except OSError:
        raise PayloadFailure("image-build-script-missing") from None
    if f"RUNTIME_NODE_IMAGE={base['reference']}" not in build_script:
        raise PayloadFailure("image-build-runtime-base-mismatch")
    programs = program.get("runnable_programs")
    if not isinstance(programs, list) or not any(isinstance(item, dict) and item.get("id") == "kanbien-core-server" for item in programs):
        raise PayloadFailure("program-record-missing")
    return image


def validate_docker_boundary(image: dict) -> None:
    try:
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        dockerignore = DOCKERIGNORE.read_text(encoding="utf-8")
    except OSError:
        raise PayloadFailure("image-source-missing") from None
    required = (
        f"ARG RUNTIME_NODE_IMAGE={image['runtime_base']['reference']}",
        "FROM ${RUNTIME_NODE_IMAGE}",
        "USER nonroot",
        f"CMD {json.dumps(image['command'])}",
        "COPY --chown=nonroot:nonroot --from=build /payload/artifacts/ ./artifacts/",
    )
    if dockerfile.count("\nCMD ") != 1 or any(item not in dockerfile for item in required):
        raise PayloadFailure("dockerfile-runtime-boundary-invalid")
    if any(item not in dockerignore for item in ("*", "!platform/server/**", "**/.aws", "**/secrets", "**/node_modules")):
        raise PayloadFailure("dockerignore-boundary-invalid")


def validate_payload(compiled_root: Path, image: dict) -> None:
    if not (compiled_root / COMPILED_ENTRYPOINT).is_file():
        raise PayloadFailure("compiled-entrypoint-missing")
    forbidden = image.get("payload", {}).get("forbidden_dependency_ids")
    if not isinstance(forbidden, list) or not all(isinstance(item, str) for item in forbidden):
        raise PayloadFailure("image-contract-invalid")
    files = tuple(sorted(compiled_root.rglob("*.js")))
    if not files:
        raise PayloadFailure("compiled-payload-missing")
    try:
        content = "\n".join(file.read_text(encoding="utf-8") for file in files)
    except OSError:
        raise PayloadFailure("compiled-payload-unreadable") from None
    if any(FORBIDDEN_MARKERS[item] in content for item in forbidden if item in FORBIDDEN_MARKERS):
        raise PayloadFailure("compiled-payload-forbidden-dependency")
    if any(path.suffix == ".ts" for path in compiled_root.rglob("*")):
        raise PayloadFailure("compiled-payload-contains-typescript")
    package_root = compiled_root / "node_modules" / "@kanbien"
    shims = {f"@kanbien/{path.name}" for path in package_root.iterdir() if path.is_dir()} if package_root.is_dir() else set()
    if shims != EXPECTED_SHIMS:
        raise PayloadFailure("compiled-payload-shims-invalid")
    roots = {path.name for path in compiled_root.iterdir() if path.is_dir()}
    if not roots.issubset({"infra", "node_modules", "packages", "platform"}):
        raise PayloadFailure("compiled-payload-unapproved-root")


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--compiled-root", required=True)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    try:
        if unknown:
            raise PayloadFailure("payload-check-argument-invalid")
        image = validate_source_contracts()
        validate_docker_boundary(image)
        validate_payload(Path(args.compiled_root), image)
        report = {"scope": "core-server-image-payload", "verdict": "passed", "diagnostics": []}
        status = 0
    except PayloadFailure as failure:
        report = {"scope": "core-server-image-payload", "verdict": "failed", "diagnostics": [{"code": code} for code in failure.codes]}
        status = 1
    print(json.dumps(report, sort_keys=True))
    return status


if __name__ == "__main__":
    sys.exit(main())
