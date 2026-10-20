#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.release-contract
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Check the connected local image, workload, verifier, configuration, private-network, and startup-access contract before a runtime change set is created.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.create-runtime-change-set
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/script.py
#   effects: [read-only]
"""Fail closed when the container and fixed private workload contracts diverge."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[8]


def load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return value if isinstance(value, dict) else None


def check(root: Path) -> list[str]:
    codes: list[str] = []
    image = load_yaml(root / "infra/04.deploy/03.product/image/core-server/image-contract.yml")
    programs = load_yaml(root / "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml")
    network = load_yaml(root / "infra/04.deploy/03.product/targets/kanbien-core-platform/foundation/network.yml")
    access = load_yaml(root / "infra/04.deploy/03.product/targets/kanbien-core-platform/foundation/technical-access.yml")
    try:
        docker = (root / "infra/04.deploy/03.product/image/core-server/Dockerfile").read_text(encoding="utf-8")
        template = (root / "infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/bootstrap-runtime.yml").read_text(encoding="utf-8")
        foundation = (root / "infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/foundation.yml").read_text(encoding="utf-8")
    except OSError:
        return ["release-contract-source-unreadable"]
    if not image or image.get("id") != "kanbien-core-server-image" or image.get("runtime", {}).get("user") != "nonroot":
        codes.append("image-runtime-identity-invalid")
    if "USER nonroot" not in docker or 'CMD ["artifacts/kanbien-core-server.main.js"]' not in docker:
        codes.append("image-command-contract-invalid")
    program = next((item for item in (programs or {}).get("runnable_programs", []) if isinstance(item, dict) and item.get("id") == "kanbien-core-server"), None)
    image_program = next((item for item in (programs or {}).get("image_contracts", []) if isinstance(item, dict) and item.get("id") == "kanbien-core-server-image"), None)
    if not isinstance(program, dict) or not isinstance(image_program, dict) or image_program.get("command") != ["node", "artifacts/kanbien-core-server.main.js"]:
        codes.append("runnable-program-command-invalid")
    if "User:" in template or "TaskRoleArn:" in template:
        codes.append("workload-runtime-identity-invalid")
    if "AssignPublicIp: DISABLED" not in template or "@${ImageDigest}" not in template:
        codes.append("workload-immutable-private-image-invalid")
    if "- CMD\n              - /nodejs/bin/node\n              - -e" not in template or "CMD-SHELL" in template:
        codes.append("workload-health-command-invalid")
    verifier_marker = "Name: private-release-verifier"
    verifier = template[template.find(verifier_marker):] if verifier_marker in template else ""
    if not verifier or "Command:\n            - -e" not in verifier or "\n            - node\n" in verifier:
        codes.append("verifier-entrypoint-contract-invalid")
    required_names = {"NODE_ENV", "HOST", "PORT", "PLATFORM_SOURCE_COMMIT_SHA"}
    present_names = {line.split(":", 1)[1].strip() for line in template.splitlines() if line.strip().startswith("- Name:")}
    if not required_names <= present_names:
        codes.append("workload-configuration-contract-invalid")
    if not network or network.get("public_ingress") != "prohibited" or "image-layer-object-store" not in network.get("private_image_retrieval", {}).get("destinations", []):
        codes.append("private-network-contract-invalid")
    intent_ids = {item.get("id") for item in (access or {}).get("access_intents", []) if isinstance(item, dict)}
    if intent_ids != {"delivery-custody", "workload-startup"}:
        codes.append("startup-access-contract-invalid")
    if "S3ArtifactPrefixListId:" not in foundation or "CidrIp: 0.0.0.0/0" in foundation:
        codes.append("private-image-retrieval-contract-invalid")
    return codes


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    codes = ["release-contract-arguments-invalid"] if unknown else check(args.root)
    print(json.dumps({"schema": "deploy/release-contract-report/v1", "target": "kanbien-core-platform", "scope": "bootstrap-runtime", "verdict": "passed" if not codes else "failed", "findings": [{"code": code} for code in codes]}, sort_keys=True))
    return 0 if not codes else 1


if __name__ == "__main__":
    raise SystemExit(main())
