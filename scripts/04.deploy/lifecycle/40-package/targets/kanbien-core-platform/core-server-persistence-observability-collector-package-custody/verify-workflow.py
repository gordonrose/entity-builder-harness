#!/usr/bin/env python3
"""Validate the fixed collector custody route without contacting a registry."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-persistence-observability-collector-package-custody.verify
#   version: 3
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
DEFAULT_DOCKERFILE = ROOT / "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/Dockerfile"
DEFAULT_COMPONENT_MANIFEST = ROOT / "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/builder-config.yaml"
BUILDER_IMAGE = "docker.io/library/golang@sha256:27f2d3b83cfc5803c8078f8e730af0f7c431bf067afaec8f60a36fb763187cba"
UPSTREAM_MANIFEST_SHA256 = "0bd72a020e0b8414c85df56fd5dcc1ebd05f160a8bbe03f8fb2c53a1248218e8"
REQUIRED = ("workflow_dispatch:", "build-and-qualify:", "scan-qualified-payload:", "needs: build-and-qualify", "needs: [build-and-qualify, scan-qualified-payload]", "retain-safe-failure-diagnostic:", "collector-package-workflow-failed", "deployment-operation-diagnostics.py record", "observability-collector-package-failure-diagnostic.json", "docker build --pull --platform linux/amd64", "docker save kanbien-observability-collector:qualification", "sha256sum", "docker load --input", "docker push", "aquasecurity/setup-trivy@3fb12ec12f41e471780db15c232d5dd185dcb514", "trivy image --input scan-input/observability-collector.scan-input.tar", "id: vulnerability_scan", "continue-on-error: true", "if: always()", "if: steps.vulnerability_scan.outcome != 'success'", "environment: kanbien-core-platform", "id-token: write", "attestations: write", "refs/heads/main", "aws-actions/configure-aws-credentials@v4", "aws-actions/amazon-ecr-login@v2", "actions/attest@v4", "actions/upload-artifact@v4", "AOT_CONFIG_CONTENT", "aws ecr describe-images", "core-server-persistence-package-custody/validate-delivery-access/script.sh", "package-custody-receipt/script.sh")
FORBIDDEN = ("aws cloudformation", "aws ecs", "aws lambda", "terraform apply", "aws ecr describe-image-scan-findings", "public.ecr.aws/token/", "aquasecurity/trivy-action@", "COLLECTOR_SOURCE_IMAGE")

def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dockerfile", type=Path, default=DEFAULT_DOCKERFILE)
    parser.add_argument("--component-manifest", type=Path, default=DEFAULT_COMPONENT_MANIFEST)
    args, unknown = parser.parse_known_args()
    codes: list[str] = []
    if unknown:
        codes.append("arguments-invalid")
    try:
        workflow, contract, config, dockerfile, components = (args.workflow.read_text(encoding="utf-8"), args.contract.read_text(encoding="utf-8"), args.config.read_text(encoding="utf-8"), args.dockerfile.read_text(encoding="utf-8"), args.component_manifest.read_text(encoding="utf-8"))
    except OSError:
        codes.append("collector-custody-artifact-unreadable")
        workflow = contract = config = dockerfile = components = ""
    if not all(item in workflow for item in REQUIRED):
        codes.append("collector-custody-workflow-incomplete")
    if any(item in workflow.lower() for item in FORBIDDEN):
        codes.append("collector-custody-workflow-target-mutation-present")
    scan_job = workflow.split("  scan-qualified-payload:", 1)[1].split("  complete-custody:", 1)[0] if "  scan-qualified-payload:" in workflow and "  complete-custody:" in workflow else ""
    if any(item in scan_job for item in ("id-token:", "AWS_ROLE_ARN", "environment: kanbien-core-platform", "ECR_URI:")):
        codes.append("collector-custody-unprivileged-scan-boundary-invalid")
    if not all(item in contract for item in ("kind: minimal-custom-collector-build", "repository: open-telemetry/opentelemetry-collector-releases", "version: v0.163.0", f"contrib_manifest_sha256: {UPSTREAM_MANIFEST_SHA256}", f"reference: {BUILDER_IMAGE}", "go_version: 1.26.10", "identity_proof: reviewed-upstream-release-manifest-and-pinned-builder-image", "precondition: exact-qualified-archive-must-pass-unprivileged-scan-before-private-publication", "aws-emf-cloudwatch-logs")):
        codes.append("collector-custody-contract-invalid")
    if not all(item in dockerfile for item in (BUILDER_IMAGE, "go install go.opentelemetry.io/collector/cmd/builder@v${OTELCOL_VERSION}", "FROM scratch", "--config=env:AOT_CONFIG_CONTENT")):
        codes.append("collector-custody-dockerfile-invalid")
    if not all(item in components for item in ("name: kanbien-observability-collector", "otelcol_version: 0.163.0", "otlpreceiver v0.163.0", "batchprocessor v0.163.0", "memorylimiterprocessor v0.163.0", "awsemfexporter v0.163.0", "healthcheckextension v0.163.0")):
        codes.append("collector-custody-component-manifest-invalid")
    if not all(item in config for item in ("awsemf:", "dimension_rollup_option: NoDimensionRollup", "log_group_name: /aws/ecs/kanbien-core-platform", "metric_name_selectors:")):
        codes.append("collector-custody-configuration-invalid")
    if re.search(r"(?:password|secret|credential|authorization|bearer)\s*:", config, re.I):
        codes.append("collector-custody-configuration-unsafe")
    result = {"schema": "deploy/collector-package-workflow-validation/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": "passed" if not codes else "failed", "findings": [{"code": code} for code in dict.fromkeys(codes)]}
    print(json.dumps(result, sort_keys=True))
    return 0 if not codes else 1

if __name__ == "__main__":
    sys.exit(main())
