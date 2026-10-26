#!/usr/bin/env python3
"""Validate the fixed collector custody route without contacting a registry."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-persistence-observability-collector-package-custody.verify
#   version: 3
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
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
import yaml
import shlex
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "package-custody-receipt"))
from workflow_guard import protected_script, job_steps, protected_step, unconditional_run, custody_tail

ROOT = Path(__file__).resolve().parents[7]
DEFAULT_WORKFLOW = ROOT / ".github/workflows/publish-kanbien-core-platform-observability-collector.yml"
DEFAULT_CONTRACT = ROOT / "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/image-contract.yml"
DEFAULT_CONFIG = ROOT / "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/collector-qualification-config.yml"
DEFAULT_DOCKERFILE = ROOT / "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/Dockerfile"
DEFAULT_COMPONENT_MANIFEST = ROOT / "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/builder-config.yaml"
BUILDER_IMAGE = "docker.io/library/golang@sha256:27f2d3b83cfc5803c8078f8e730af0f7c431bf067afaec8f60a36fb763187cba"
UPSTREAM_MANIFEST_SHA256 = "0bd72a020e0b8414c85df56fd5dcc1ebd05f160a8bbe03f8fb2c53a1248218e8"
REQUIRED = ("workflow_dispatch:", "build-and-qualify:", "scan-qualified-payload:", "needs: build-and-qualify", "needs: [build-and-qualify, scan-qualified-payload]", "retain-safe-failure-diagnostic:", "collector-package-workflow-failed", "deployment-operation-diagnostics.py record", "observability-collector-package-failure-diagnostic.json", "docker build --pull --platform linux/amd64", "docker save kanbien-observability-collector:qualification", "sha256sum", "docker load --input", "docker push", "aquasecurity/setup-trivy@3fb12ec12f41e471780db15c232d5dd185dcb514", "trivy image --input scan-input/observability-collector.scan-input.tar", "id: vulnerability_scan", "continue-on-error: true", "if: always()", "if: steps.vulnerability_scan.outcome != 'success'", "environment: kanbien-core-platform", "id-token: write", "attestations: write", "refs/heads/main", "aws-actions/configure-aws-credentials@v4", "aws-actions/amazon-ecr-login@v2", "actions/attest@v4", "actions/upload-artifact@v4", "aws ecr describe-images", "core-server-persistence-package-custody/validate-delivery-access/script.sh", "package-custody-receipt/script.sh")
FORBIDDEN = ("aws cloudformation", "aws ecs", "aws lambda", "terraform apply", "aws ecr describe-image-scan-findings", "public.ecr.aws/token/", "aquasecurity/trivy-action@", "COLLECTOR_SOURCE_IMAGE")


def qualification_route_valid(text):
    try:
        protected_script(Path('scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh'), 'set -euo pipefail\nROOT="$(git rev-parse --show-toplevel)"\nimage="kanbien-observability-collector:qualification"\nif [[ "$#" -gt 0 ]]; then\n  if [[ "$#" -ne 2 || "$1" != --image || -z "$2" ]]; then echo "Usage: qualify-image.sh [--image <reference>]" >&2; exit 2; fi\n  image="$2"\nfi\nname="kanbien-observability-collector-qualification-${GITHUB_RUN_ID:-$$}"\ncleanup() { python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py" --container "$name"; }\nfinish() {\n  local original=$? cleanup_status=0\n  trap - EXIT\n  cleanup || cleanup_status=$?\n  if [[ "$original" -ne 0 ]]; then exit "$original"; fi\n  exit "$cleanup_status"\n}\ntrap finish EXIT\ndocker run --detach --rm --name "$name" --network none --read-only \\\n  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL \\\n  --security-opt no-new-privileges \\\n  -e AWS_EC2_METADATA_DISABLED=true \\\n  -e "AOT_CONFIG_CONTENT=$(cat infra/04.deploy/03.product/image/core-server-persistence-observability-collector/collector-qualification-config.yml)" \\\n  "$image" >/dev/null\nsleep 5\ntest "$(docker inspect --format \'{{.State.Running}}\' "$name")" = true\nlogs="$(docker logs "$name" 2>&1)"\n! grep -Ei \'error.*(config|awsemf)|failed.*(config|awsemf)\' <<<"$logs"\ncleanup\ntrap - EXIT\n\nexec python3 -B "$ROOT/scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/behavior-test.py" --image "$image"')
        build = job_steps(text, "build-and-qualify")
        scan = job_steps(text, "scan-qualified-payload")
        custody = job_steps(text, "complete-custody")
        workflow = yaml.safe_load(text)
        if workflow["jobs"]["scan-qualified-payload"].get("needs") != "build-and-qualify": return False
        if workflow["jobs"]["complete-custody"].get("needs") != ["build-and-qualify", "scan-qualified-payload"]: return False
        expected = [['bash', 'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh'], shlex.split('python3 scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py record --image kanbien-observability-collector:qualification --receipt "$RUNNER_TEMP/qualified-image.json" --input infra/04.deploy/03.product/image/core-server-persistence-observability-collector/image-contract.yml --input infra/04.deploy/03.product/image/core-server-persistence-observability-collector/collector-qualification-config.yml --configuration-input scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml observability-collector --input scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh --input scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/behavior-test.py')]
        qualify_index, _ = protected_step(build, "Qualify exact collector startup with non-secret configuration", expected)
        build_index, _ = protected_step(build, "Build the declared minimal collector source")
        export_index, export = protected_step(build, "Export exact qualified collector archive")
        if not build_index < qualify_index < export_index: return False
        def exact_run(items,name,source):
            return protected_step(items,name,[shlex.split(line) for line in source.splitlines() if line.strip()])
        exact_run(build,"Build the declared minimal collector source",'set -euo pipefail\ndocker build --pull --platform linux/amd64 --file infra/04.deploy/03.product/image/core-server-persistence-observability-collector/Dockerfile --tag kanbien-observability-collector:qualification .')
        _, archive_step = exact_run(build,"Export exact qualified collector archive",'''set -euo pipefail
image_id="$(python3 scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py verify --image kanbien-observability-collector:qualification --receipt "$RUNNER_TEMP/qualified-image.json" --configuration-input scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml observability-collector)"
echo "image_id=$image_id" >> "$GITHUB_OUTPUT"
docker save kanbien-observability-collector:qualification -o "$RUNNER_TEMP/observability-collector.scan-input.tar"
sha256sum "$RUNNER_TEMP/observability-collector.scan-input.tar" | awk '{print "sha256=" $1}' >> "$GITHUB_OUTPUT"''')
        if archive_step.get("id")!="archive" or workflow["jobs"]["build-and-qualify"].get("outputs")!={"archive_sha256":"${{ steps.archive.outputs.sha256 }}","image_id":"${{ steps.archive.outputs.image_id }}"}:return False
        _,archive_upload=protected_step(build,"Export exact qualified image for unprivileged scan")
        if archive_upload.get("uses")!="actions/upload-artifact@v4" or archive_upload.get("with")!={"name":"kanbien-core-platform-observability-collector-scan-input-${{ github.run_id }}","path":"${{ runner.temp }}/observability-collector.scan-input.tar\n${{ runner.temp }}/qualified-image.json\n","if-no-files-found":"error","overwrite":False,"retention-days":1}:return False
        for items,name in [(scan,"Retrieve exact qualified collector archive"),(custody,"Retrieve scanned collector archive")]:
            _,download=protected_step(items,name)
            if download.get("uses")!="actions/download-artifact@v4" or download.get("with")!={"name":"kanbien-core-platform-observability-collector-scan-input-${{ github.run_id }}","path":"scan-input"}:return False
        archive_verify='''set -euo pipefail
actual="$(sha256sum scan-input/observability-collector.scan-input.tar | awk '{print $1}')"
test "$actual" = "${{ needs.build-and-qualify.outputs.archive_sha256 }}"'''
        provenance_index,_=exact_run(scan,"Verify collector archive provenance",archive_verify)
        exact_run(custody,"Verify archive is the scanned qualified payload",archive_verify+'\ndocker load --input scan-input/observability-collector.scan-input.tar\npython3 scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py verify --image "${{ needs.build-and-qualify.outputs.image_id }}" --receipt scan-input/qualified-image.json --configuration-input scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml observability-collector')
        if 'qualification.py verify --image kanbien-observability-collector:qualification' not in export.get("run", ""): return False
        scans = [(i, item) for i, item in enumerate(scan) if item.get("name") == "Scan exact qualified collector payload"]
        if len(scans) != 1: return False
        scan_index, scanner = scans[0]
        installer_index,installer=protected_step(scan,"Install pinned portable scanner")
        if not provenance_index < installer_index < scan_index or installer.get("uses")!="aquasecurity/setup-trivy@3fb12ec12f41e471780db15c232d5dd185dcb514" or installer.get("with")!={"version":"v0.70.0","cache":True}:return False
        if scanner.get("id") != "vulnerability_scan" or scanner.get("continue-on-error") is not True: return False
        if any(key in scanner for key in ("if", "shell", "working-directory", "env")): return False
        scan_argv = shlex.split(scanner.get("run", "").replace("\\\n", " "))
        if scan_argv != ["trivy", "image", "--input", "scan-input/observability-collector.scan-input.tar", "--severity", "HIGH,CRITICAL", "--ignore-unfixed=false", "--exit-code", "1", "--format", "json", "--output", "observability-collector.trivy.json"]: return False
        gate_index, gate = protected_step(scan, "Require clean portable vulnerability scan of qualified payload", [["exit", "1"]], "steps.vulnerability_scan.outcome != 'success'")
        if not provenance_index < scan_index < gate_index: return False
        artifact_index,scan_upload=protected_step(scan,"Retain vulnerability scan artifact",condition="always()")
        if not scan_index < artifact_index < gate_index or scan_upload.get("uses")!="actions/upload-artifact@v4" or scan_upload.get("with")!={"name":"kanbien-core-platform-observability-collector-vulnerability-scan-${{ github.run_id }}","path":"observability-collector.trivy.json","if-no-files-found":"error","overwrite":False,"retention-days":30}:return False
        load_index, load = protected_step(custody, "Verify archive is the scanned qualified payload")
        publish_index, publish = protected_step(custody, "Publish exact scanned collector to private ECR")
        credentials = [i for i, item in enumerate(custody) if str(item.get("uses", "")).startswith("aws-actions/")]
        if not credentials or not load_index < min(credentials) < publish_index: return False
        for step in (export, load, publish):
            unconditional_run(step)
        for step in (load, publish):
            if 'qualification.py verify --image "${{ needs.build-and-qualify.outputs.image_id }}" --receipt scan-input/qualified-image.json' not in step.get("run", ""): return False
        if 'docker tag "$qualified_image" "$ECR_URI:$CANDIDATE_TAG"' not in publish.get("run", ""): return False
        exact_run(custody,"Publish exact scanned collector to private ECR",'''set -euo pipefail
qualified_image="$(python3 scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py verify --image "${{ needs.build-and-qualify.outputs.image_id }}" --receipt scan-input/qualified-image.json --configuration-input scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml observability-collector)"
docker tag "$qualified_image" "$ECR_URI:$CANDIDATE_TAG"
docker push "$ECR_URI:$CANDIDATE_TAG"
digest="$(aws ecr describe-images --repository-name "$ECR_REPOSITORY" --image-ids imageTag="$CANDIDATE_TAG" --query 'imageDetails[0].imageDigest' --output text)"
[[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]
docker pull "$ECR_URI@$digest" >/dev/null
test "$(docker image inspect "$ECR_URI@$digest" --format '{{.Id}}')" = "$qualified_image"
echo "digest=$digest" >> "$GITHUB_OUTPUT"''')
        access_index,access=protected_step(custody,"Prove fixed delivery read access",[["bash","scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/verify-delivery-role-access/script.sh"]])
        if access.get("id")!="access" or publish.get("id")!="image" or not min(credentials)<access_index<publish_index:return False
        _,scan_artifact=protected_step(custody,"Retrieve clean collector scan evidence")
        if scan_artifact.get("uses")!="actions/download-artifact@v4" or scan_artifact.get("with")!={"name":"kanbien-core-platform-observability-collector-vulnerability-scan-${{ github.run_id }}","path":"scan-proof"}:return False
        return custody_tail(custody,published_index=publish_index,target="kanbien-core-platform",environment="private-persistence-candidate",region="aws-eu-west-1",candidate="observability-collector",contract="core-server-persistence-observability-collector-image",program="kanbien-observability-collector",stem="observability-collector",artifact_name="kanbien-core-platform-observability-collector-package-custody-${{ github.run_id }}",qualification_outcome="${{ needs.build-and-qualify.result }}",scan_outcome="${{ needs.scan-qualified-payload.result }}",scan_check="vulnerability_scan",provenance_name="Attest collector provenance",attestation_name="Attest collector SBOM",capture_name="Write and validate safe collector custody receipt",upload_name="Upload safe collector custody evidence",receipt_filename="observability-collector-package-custody-receipt.json",extra_artifacts=["scan-input/qualified-image.json","scan-proof/observability-collector.trivy.json"],registry_expression="${{ env.ECR_URI }}")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, yaml.YAMLError): return False

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
    if not qualification_route_valid(workflow):
        codes.append("collector-qualification-route-invalid")
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
    try:
        configuration = yaml.safe_load(config)
        metrics = configuration["service"]["pipelines"]["metrics"]
        if not all(name in configuration["receivers"] for name in metrics["receivers"]) or "awsemf" not in metrics["exporters"] or not all(name in configuration["exporters"] for name in metrics["exporters"]):
            codes.append("collector-configuration-pipeline-disconnected")
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError):
        codes.append("collector-configuration-pipeline-disconnected")
    if re.search(r"(?:password|secret|credential|authorization|bearer)\s*:", config, re.I):
        codes.append("collector-custody-configuration-unsafe")
    result = {"schema": "deploy/collector-package-workflow-validation/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": "passed" if not codes else "failed", "findings": [{"code": code} for code in dict.fromkeys(codes)]}
    print(json.dumps(result, sort_keys=True))
    return 0 if not codes else 1

if __name__ == "__main__":
    sys.exit(main())
