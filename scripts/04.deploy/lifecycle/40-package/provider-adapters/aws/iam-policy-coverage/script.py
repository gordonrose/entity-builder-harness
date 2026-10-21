#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.iam-policy-coverage
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.delivery-access
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Normalize the actions granted to one declared CloudFormation IAM role without exposing provider policy contents.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.command.kanbien-core-platform.core-server-package-custody.validate-delivery-access
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access/script.sh

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[7]
ACTION_PATTERN = re.compile(r"\b[a-z0-9-]+:[A-Za-z0-9*]+\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce safe AWS IAM policy coverage for a declared role.")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--role-logical-id", required=True)
    parser.add_argument("--provider-policy-source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def repository_path(path: Path) -> str | None:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return None


def role_actions(template: str, role_logical_id: str) -> set[str]:
    match = re.search(
        rf"^  {re.escape(role_logical_id)}:\n(?P<body>.*?)(?=^  [A-Za-z][A-Za-z0-9]+:|\Z)",
        template,
        re.M | re.S,
    )
    if not match:
        return set()
    policy_body = match.group("body").split("      Policies:", 1)
    if len(policy_body) != 2:
        return set()
    action_lines = "\n".join(line for line in policy_body[1].splitlines() if "Action:" in line)
    return set(ACTION_PATTERN.findall(action_lines))


def main() -> int:
    args = parse_args()
    try:
        template = args.template.read_text(encoding="utf-8")
        contract = repository_path(args.contract)
        if contract is None or not args.provider_policy_source.strip():
            raise ValueError("unsafe input")
        actions = sorted(role_actions(template, args.role_logical_id))
        verdict = "covered" if actions else "unreadable"
        report = {
            "schema": "deploy/provider-policy-coverage/v1",
            "provider": "aws",
            "contract": contract,
            "provider_policy_source": args.provider_policy_source,
            "granted_actions": actions,
            "verdict": verdict,
        }
        args.output.write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
        return 0 if verdict == "covered" else 1
    except (OSError, ValueError):
        report = {
            "schema": "deploy/provider-policy-coverage/v1",
            "provider": "aws",
            "contract": repository_path(args.contract),
            "provider_policy_source": args.provider_policy_source,
            "granted_actions": [],
            "verdict": "unreadable",
        }
        args.output.write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
        return 1


if __name__ == "__main__":
    sys.exit(main())
