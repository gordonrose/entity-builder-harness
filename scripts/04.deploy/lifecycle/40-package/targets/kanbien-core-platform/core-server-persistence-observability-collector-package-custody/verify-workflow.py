#!/usr/bin/env python3
"""Validate the fixed collector custody route without contacting a registry."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-persistence-observability-collector-package-custody.verify
#   version: 2
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Statically validate the fixed collector package-custody workflow, contract, and non-secret qualification configuration.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.core-server-persistence-observability-collector-package-custody
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/script.sh
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
DEFAULT_WORKFLOW = ROOT / ".github/workflows/publish-kanbien-core-platform-observability-collector.yml"
DEFAULT_CONTRACT = ROOT / "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/image-contract.yml"
DEFAULT_CONFIG = ROOT / "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/collector-qualification-config.yml"
SOURCE = "public.ecr.aws/aws-observability/aws-otel-collector@sha256:7968fb60db6a2390a47ba6a2df029745638486e285c9b2487da1b722d0855a3e"
PLATFORM_MANIFEST = "sha256:d0a012252142c0999982fc34cddc88e2f9ce8c6b2bdf2c53e8e489a49dfbac31"
REQUIRED = ("workflow_dispatch:", "scan-mirrored-payload:", "needs: qualify-and-publish", "needs: [qualify-and-publish, scan-mirrored-payload]", "aquasecurity/setup-trivy@3fb12ec12f41e471780db15c232d5dd185dcb514", "trivy image --input scan-input/observability-collector.scan-input.tar", "environment: kanbien-core-platform", "id-token: write", "attestations: write", "refs/heads/main", "aws-actions/configure-aws-credentials@v4", "aws-actions/amazon-ecr-login@v2", "actions/attest@v4", "actions/upload-artifact@v4", SOURCE, f"COLLECTOR_SOURCE_PLATFORM_MANIFEST_DIGEST: {PLATFORM_MANIFEST}", "Require declared private collector manifest", "AOT_CONFIG_CONTENT", "aws ecr describe-images", "core-server-persistence-package-custody/validate-delivery-access/script.sh", "package-custody-receipt/script.sh")
FORBIDDEN = ("aws cloudformation", "aws ecs", "aws lambda", "terraform apply", "aws ecr describe-image-scan-findings", 'docker pull "$COLLECTOR_SOURCE_IMAGE"', "public.ecr.aws/token/", "aquasecurity/trivy-action@")

def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args, unknown = parser.parse_known_args()
    codes: list[str] = []
    if unknown:
        codes.append("arguments-invalid")
    try:
        workflow, contract, config = (args.workflow.read_text(encoding="utf-8"), args.contract.read_text(encoding="utf-8"), args.config.read_text(encoding="utf-8"))
    except OSError:
        codes.append("collector-custody-artifact-unreadable")
        workflow = contract = config = ""
    if not all(item in workflow for item in REQUIRED):
        codes.append("collector-custody-workflow-incomplete")
    if any(item in workflow.lower() for item in FORBIDDEN):
        codes.append("collector-custody-workflow-target-mutation-present")
    scan_job = workflow.split("  scan-mirrored-payload:", 1)[1].split("  complete-custody:", 1)[0] if "  scan-mirrored-payload:" in workflow and "  complete-custody:" in workflow else ""
    if any(item in scan_job for item in ("id-token:", "AWS_ROLE_ARN", "environment: kanbien-core-platform", "ECR_URI:")):
        codes.append("collector-custody-unprivileged-scan-boundary-invalid")
    if not all(item in contract for item in ("registry: public.ecr.aws", "repository: aws-observability/aws-otel-collector", "immutable_digest: sha256:7968fb60db6a2390a47ba6a2df029745638486e285c9b2487da1b722d0855a3e", "os: linux", "architecture: amd64", f"immutable_manifest_digest: {PLATFORM_MANIFEST}", "identity_proof: reviewed-pinned-source-index-resolution-and-private-manifest-digest-match", "precondition: exact-selected-platform-manifest-already-private", "aws-emf-cloudwatch-logs")):
        codes.append("collector-custody-contract-invalid")
    if not all(item in config for item in ("awsemf:", "dimension_rollup_option: NoDimensionRollup", "log_group_name: /aws/ecs/kanbien-core-platform", "metric_name_selectors:")):
        codes.append("collector-custody-configuration-invalid")
    if re.search(r"(?:password|secret|credential|authorization|bearer)\s*:", config, re.I):
        codes.append("collector-custody-configuration-unsafe")
    result = {"schema": "deploy/collector-package-workflow-validation/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": "passed" if not codes else "failed", "findings": [{"code": code} for code in dict.fromkeys(codes)]}
    print(json.dumps(result, sort_keys=True))
    return 0 if not codes else 1

if __name__ == "__main__":
    sys.exit(main())
