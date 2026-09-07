#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-deployment-workflow
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Statically enforce that the Kanbien staging workflow scans, creates an SBOM, and attests an immutable image before service deployment.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-deployment-workflow-check
#     path: package.json
#   - id: github.workflow.deploy-platform-shell-staging
#     path: .github/workflows/deploy-platform-shell-staging.yml

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 - <<'PY'
from __future__ import annotations

from pathlib import Path
import sys

try:
    import yaml
except ImportError as error:
    raise SystemExit("ERROR: PyYAML is required. Install PyYAML==6.0.2 before this check.") from error


WORKFLOW_PATH = Path(".github/workflows/deploy-platform-shell-staging.yml")
TARGET_PROFILE_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"ERROR: deployment workflow is missing: {path}")
    # BaseLoader keeps GitHub's unquoted `on` key and values as strings rather
    # than applying YAML 1.1 boolean coercion.
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(data, dict):
        raise SystemExit("ERROR: deployment workflow must be a YAML mapping.")
    return data


def text(value: object) -> str:
    return value if isinstance(value, str) else ""


workflow = load_yaml(WORKFLOW_PATH)
target_profile = load_yaml(TARGET_PROFILE_PATH)
failures: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


permissions = workflow.get("permissions", {})
if not isinstance(permissions, dict):
    failures.append("workflow permissions must be a mapping")
else:
    for permission, expected in {
        "contents": "read",
        "id-token": "write",
        "attestations": "write",
        "artifact-metadata": "write",
    }.items():
        require(
            permissions.get(permission) == expected,
            f"workflow permission {permission} must be {expected}",
        )

workflow_inputs = workflow.get("on", {}).get("workflow_dispatch", {}).get("inputs", {})
if not isinstance(workflow_inputs, dict):
    failures.append("workflow_dispatch inputs must be a mapping")
    workflow_inputs = {}
for input_name, expected_default in {
    "base_image_ref": "node:22-bookworm-slim",
    "runtime_image_ref": "gcr.io/distroless/nodejs22-debian12:nonroot",
}.items():
    config = workflow_inputs.get(input_name, {})
    require(isinstance(config, dict), f"workflow input {input_name} must be a mapping")
    if isinstance(config, dict):
        require(config.get("required") == "true", f"workflow input {input_name} must be required")
        require(config.get("default") == expected_default, f"workflow input {input_name} must default to the reviewed image")

jobs = workflow.get("jobs", {})
job = jobs.get("build-image", {}) if isinstance(jobs, dict) else {}
steps = job.get("steps", []) if isinstance(job, dict) else []
if not isinstance(steps, list):
    failures.append("build-image job must declare an ordered steps list")
    steps = []


def step(name: str) -> tuple[int, dict]:
    matches = [
        (index, item)
        for index, item in enumerate(steps)
        if isinstance(item, dict) and item.get("name") == name
    ]
    if len(matches) != 1:
        failures.append(f"workflow must contain exactly one step named: {name}")
        return (-1, {})
    return matches[0]


ordered_names = [
    "Resolve immutable image digest",
    "Read ECR scan finding counts",
    "Generate image SBOM",
    "Attest image provenance",
    "Attest image SBOM",
    "Verify the manually governed foundation stack",
    "Deploy immutable image digest to the platform-shell service stack",
]
ordered_steps = [step(name) for name in ordered_names]
indices = [index for index, _ in ordered_steps]
require(
    all(index >= 0 for index in indices) and indices == sorted(indices),
    "image scan, SBOM, and attestations must all occur before service deployment",
)

scan_index, scan_step = ordered_steps[1]
scan_run = text(scan_step.get("run"))
for required_text, message in {
    "set -euo pipefail": "scan step must fail closed",
    "ScanNotFoundException": "scan step must distinguish ECR scan-record creation from scan completion",
    "seq 1 30": "scan step must bound the ECR scan-record availability wait",
    "ECR did not create an image scan record within five minutes.": "scan step must fail when ECR does not create a scan record",
    "aws ecr wait image-scan-complete": "scan step must wait for the ECR scan",
    'scan_status" != "COMPLETE"': "scan step must require COMPLETE status",
    'critical" != "0"': "scan step must block CRITICAL findings",
    'high" != "0"': "scan step must block HIGH findings until a governed risk-acceptance path exists",
}.items():
    require(required_text in scan_run, message)

base_image_index, base_image_step = step("Resolve digest-pinned build and runtime images")
base_image_run = text(base_image_step.get("run"))
for required_text, message in {
    "inputs.base_image_ref": "workflow must resolve the selected build image",
    "inputs.runtime_image_ref": "workflow must resolve the selected runtime image",
    "build_digest": "workflow must record the immutable build-image digest",
    "runtime_digest": "workflow must record the immutable runtime-image digest",
}.items():
    require(required_text in base_image_run, message)

build_index, build_step = step("Build platform shell image")
build_run = text(build_step.get("run"))
for required_text, message in {
    '--base-image "${{ steps.base-image.outputs.build_image }}"': "build step must use the resolved immutable build image",
    '--runtime-image "${{ steps.base-image.outputs.runtime_image }}"': "build step must use the resolved immutable runtime image",
    "--require-digest-base": "build step must require both image references to be digest pinned",
}.items():
    require(required_text in build_run, message)

image_profile = target_profile.get("artifacts", {}).get("image", {})
if not isinstance(image_profile, dict):
    failures.append("target profile image configuration must be a mapping")
    image_profile = {}
for key, expected in {
    "build_image_policy": "pin-by-digest-for-official-build",
    "runtime_image_policy": "pin-by-digest-for-official-build",
    "runtime_image_class": "minimal-nonroot-distroless-nodejs22-debian12",
}.items():
    require(image_profile.get(key) == expected, f"target profile image {key} must be {expected}")
registry_scanning = image_profile.get("registry_scanning", {})
if not isinstance(registry_scanning, dict):
    failures.append("target profile registry scanning must be a mapping")
    registry_scanning = {}
for key, expected in {
    "scope": "account-registry",
    "scan_type": "BASIC",
    "scan_frequency": "SCAN_ON_PUSH",
    "verification_command": "aws ecr get-registry-scanning-configuration",
}.items():
    require(registry_scanning.get(key) == expected, f"target profile registry scanning {key} must be {expected}")
repository_filter = registry_scanning.get("repository_filter", {})
if not isinstance(repository_filter, dict):
    failures.append("target profile registry scan repository filter must be a mapping")
    repository_filter = {}
require(repository_filter.get("value") == "*", "target profile registry scan repository filter must cover all repositories")
require(repository_filter.get("type") == "WILDCARD", "target profile registry scan repository filter must use WILDCARD")

sbom_index, sbom_step = ordered_steps[2]
require(sbom_step.get("id") == "sbom", "SBOM step must have the stable sbom id")
require(sbom_step.get("uses") == "anchore/sbom-action@v0", "SBOM step must use anchore/sbom-action@v0")
sbom_with = sbom_step.get("with", {})
if not isinstance(sbom_with, dict):
    failures.append("SBOM step must provide action inputs")
    sbom_with = {}
for key, expected in {
    "image": "${{ steps.image.outputs.uri }}",
    "format": "spdx-json",
    "output-file": "${{ runner.temp }}/platform-shell.sbom.spdx.json",
    "upload-artifact": "false",
    "upload-release-assets": "false",
}.items():
    require(sbom_with.get(key) == expected, f"SBOM input {key} must be {expected}")

for name, expected_id, requires_sbom in [
    ("Attest image provenance", "provenance-attestation", False),
    ("Attest image SBOM", "sbom-attestation", True),
]:
    _, attestation_step = step(name)
    require(attestation_step.get("id") == expected_id, f"{name} must have id {expected_id}")
    require(attestation_step.get("uses") == "actions/attest@v4", f"{name} must use actions/attest@v4")
    inputs = attestation_step.get("with", {})
    if not isinstance(inputs, dict):
        failures.append(f"{name} must provide action inputs")
        inputs = {}
    require(inputs.get("subject-name") == "${{ env.ECR_URI }}", f"{name} must attest the ECR repository")
    require(inputs.get("subject-digest") == "${{ steps.image.outputs.digest }}", f"{name} must attest the immutable image digest")
    require(inputs.get("push-to-registry") == "true", f"{name} must publish the attestation beside the image")
    require(
        inputs.get("create-storage-record") == "false",
        f"{name} must avoid organization-only artifact storage records for this user-owned repository",
    )
    if requires_sbom:
        require(
            inputs.get("sbom-path") == "${{ runner.temp }}/platform-shell.sbom.spdx.json",
            "SBOM attestation must use the generated SPDX file",
        )
    else:
        require("sbom-path" not in inputs, "provenance attestation must use the action's provenance mode")

summary_index, summary_step = step("Record deployment summary")
summary_run = text(summary_step.get("run"))
for required_text, message in {
    "steps.scan.outputs.status": "deployment summary must record scan status",
    "steps.provenance-attestation.outputs.attestation-url": "deployment summary must record provenance attestation evidence",
    "steps.sbom-attestation.outputs.attestation-url": "deployment summary must record SBOM attestation evidence",
}.items():
    require(required_text in summary_run, message)

for required_text, message in {
    "steps.base-image.outputs.build_digest": "deployment summary must record the build-image digest",
    "steps.base-image.outputs.runtime_digest": "deployment summary must record the runtime-image digest",
}.items():
    require(required_text in summary_run, message)

if failures:
    print("Platform-shell deployment workflow check failed:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    raise SystemExit(1)

print("Platform-shell deployment workflow check passed.")
PY
