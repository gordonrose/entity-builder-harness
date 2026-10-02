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
#   purpose: Statically enforce that the Kanbien staging workflow scans, creates an SBOM, attests, and publishes an immutable image without deploying it.
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
BUILD_SCRIPT_PATH = Path("scripts/04.deploy/build-platform-shell-image/script.sh")
SERVICE_TEMPLATE_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml")


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
require(set(workflow_inputs) == {"publish_image"}, "qualified publication accepts only its existing publish toggle; build inputs come from source locks")
publish = workflow_inputs.get("publish_image", {})
require(isinstance(publish, dict) and publish.get("required") == "true" and publish.get("type") == "boolean"
        and publish.get("default") == "true", "existing explicit publication toggle must be preserved")

jobs = workflow.get("jobs", {})
job = jobs.get("build-image", {}) if isinstance(jobs, dict) else {}
require(job.get("runs-on") == "ubuntu-24.04", "qualification must use the reviewed Ubuntu 24.04 host")
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


# Selected action implementations are a reviewed closed set. A different SHA
# requires source review; a tag or additional action cannot bypass this guard.
REVIEWED_ACTIONS = {'Check out repository': 'actions/checkout@11d5960a326750d5838078e36cf38b85af677262',
 'Set up Node': 'actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020',
 'Set up Python': 'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065',
 'Set up Docker Buildx': 'docker/setup-buildx-action@8d2750c68a42422c14e847fe6c8ac0403b4cbd6f',
 'Configure AWS credentials': 'aws-actions/configure-aws-credentials@7474bc4690e29a8392af63c5b98e7449536d5c3a',
 'Log in to Amazon ECR': 'aws-actions/amazon-ecr-login@03f1aad4c6c7ffd436567f42f9384779290529bd',
 'Attest image provenance': 'actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6',
 'Attest image SBOM': 'actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6',
 'Retain normalized qualification receipts': 'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02',
 'Retain normalized publication receipt': 'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02'}
for name, expected in REVIEWED_ACTIONS.items():
    _, selected_action = step(name)
    require(selected_action.get("uses") == expected, f"{name} must use its reviewed immutable action commit")
for selected_action in steps:
    if isinstance(selected_action, dict) and "uses" in selected_action:
        require(selected_action.get("name") in REVIEWED_ACTIONS
                and selected_action.get("uses") == REVIEWED_ACTIONS.get(selected_action.get("name")),
                "every action must belong to the reviewed immutable selected set")
_, buildx_step = step("Set up Docker Buildx")
require(buildx_step.get("with") == {
    "version": "v0.37.2",
    "driver": "docker-container",
    "driver-opts": "image=moby/buildkit@sha256:cec9f139f45e93c5c69c60f8b07cfad9f43f4ef6b6a6cd917527fea5ff2e3dea",
}, "Buildx and its BuildKit image must use the reviewed fixed version and immutable digest")

main_index, main_step = step("Enforce remote-main deploy source")
require('"$GITHUB_REF" != "refs/heads/main"' in text(main_step.get("run")), "publication source must remain main-only")
require(job.get("environment") == "staging", "publication must retain the staging environment")
_, credentials_step = step("Configure AWS credentials")
require(credentials_step.get("if") == "${{ inputs.publish_image }}"
        and credentials_step.get("with", {}).get("role-to-assume") == "${{ env.AWS_ROLE_ARN }}", "publication must retain the existing conditional OIDC role")
for name, version in (("Set up Node", "22.23.3"), ("Set up Python", "3.14.4")):
    _, setup = step(name)
    key = "node-version" if name == "Set up Node" else "python-version"
    require(setup.get("with", {}).get(key) == version, "qualification host tool version must match source support")
_, dependencies_step = step("Install script dependencies")
require("--require-hashes -r scripts/04.deploy/operational-realization-gate/requirements.lock" in text(dependencies_step.get("run")),
        "qualification must install the complete hash-locked Python schema dependency closure")

ordered_names = [
    "Resolve immutable image digest",
    "Read ECR scan finding counts",
    "Generate image SBOM",
    "Attest image provenance",
    "Attest image SBOM",
    "Record image-publication summary",
]
ordered_steps = [step(name) for name in ordered_names]
indices = [index for index, _ in ordered_steps]
require(
    all(index >= 0 for index in indices) and indices == sorted(indices),
    "image scan, SBOM, and attestations must all occur before image-publication summary",
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

sandbox_index, sandbox_step = step("Install local qualification sandbox")
sandbox_run = text(sandbox_step.get("run"))
require(sandbox_run == 'set -euo pipefail\nsudo apt-get update\nsudo apt-get install --yes --no-install-recommends bubblewrap\ntest -x /usr/bin/bwrap\nsandbox_policy="$(mktemp -d "$RUNNER_TEMP/qualification-policy.XXXXXX")"\n(\n  cd "$sandbox_policy"\n  apt-get download apparmor-profiles=4.0.1really4.0.1-0ubuntu0.24.04.9\n  printf \'%s  %s\\n\' \'90b02aa006eea7702cd4e851343e469e41365dda42145a3cb035de1d6c773b8c\' \'apparmor-profiles_4.0.1really4.0.1-0ubuntu0.24.04.9_all.deb\' | sha256sum --check --strict --status\n  dpkg-deb --extract apparmor-profiles_4.0.1really4.0.1-0ubuntu0.24.04.9_all.deb package\n  printf \'%s  %s\\n\' \'11d39094f044f0cda0febb3ad517b830301da6b2ce929664af09ee9e4dd264f9\' \'package/usr/share/apparmor/extra-profiles/bwrap-userns-restrict\' | sha256sum --check --strict --status\n)\nfor local_policy in /etc/apparmor.d/local/bwrap-userns-restrict /etc/apparmor.d/local/unpriv_bwrap; do\n  test ! -e "$local_policy"\n  test ! -L "$local_policy"\ndone\nsudo /usr/sbin/apparmor_parser --add --skip-cache --base /etc/apparmor.d "$sandbox_policy/package/usr/share/apparmor/extra-profiles/bwrap-userns-restrict"\n',
        "qualification must install bubblewrap and add only its exact reviewed namespace profile")
credentials_index, _ = step("Configure AWS credentials")
require(0 <= sandbox_index < credentials_index,
        "sandbox dependency installation must precede AWS credentials")

base_image_index, base_image_step = step("Acquire reviewed qualification inputs")
base_image_run = text(base_image_step.get("run"))
for required_text, message in {
    "verify-local-build.sh": "workflow must acquire the hash-locked compiler closure",
    "--acquire-cache": "workflow must acquire reviewed package bytes",
    "--qualify-local": "runtime base acquisition must use the existing qualified path",
    "--acquire-base": "workflow must explicitly acquire the locked runtime base",
}.items():
    require(required_text in base_image_run, message)

build_index, build_step = step("Build platform shell image")
build_run = text(build_step.get("run"))
REVIEWED_CLEAN_SOURCE = 'git diff --quiet\ngit diff --cached --quiet\ngit ls-files --others --exclude-standard -z | python3 -c \'import sys; raise SystemExit(bool(sys.stdin.buffer.read(1)))\'\ntest "$(git rev-parse HEAD)" = "$GITHUB_SHA"\n'
require(build_run.startswith("set -euo pipefail\n" + REVIEWED_CLEAN_SOURCE) and build_run.endswith(REVIEWED_CLEAN_SOURCE),
        "qualification must bind HEAD and reject unstaged, staged and untracked source changes before and after the build")
for required_text, message in {
    "--qualify-local": "build must freshly qualify the exact final image",
    "--publication-directory": "build must retain the exact qualified image handoff",
    "qualified_publication.py": "build must verify source and image handoff before publication",
    "--package-cache": "build must consume verified package cache",
    "GITHUB_SHA": "handoff must bind the current workflow commit",
    'cat "$RUNNER_TEMP/qualified-image/result.json" >&2': "a failed local qualification must emit only its normalized safe result",
}.items():
    require(required_text in build_run, message)
require("--base-image" not in build_run and "--tag" not in build_run,
        "qualified build must not fall back to the legacy source Docker build")
push_index, push_step = step("Push platform shell image")
push_run = text(push_step.get("run"))
require(push_run.startswith("set -euo pipefail\n" + REVIEWED_CLEAN_SOURCE),
        "publication must recheck HEAD and reject unstaged, staged and untracked source changes before handoff or push")
for required_text in ("qualified_publication.py", "steps.qualified-image.outputs.image_id", "steps.qualified-image.outputs.manifest_digest", "docker tag", "docker push"):
    require(required_text in push_run, "publication must preserve the verified qualified image identity")
require(push_step.get("if") == "${{ inputs.publish_image }}", "push must retain the explicit publication toggle")
resolve_index, resolve_step = step("Resolve immutable image digest")
resolve_run = text(resolve_step.get("run"))
for required_text in ("steps.qualified-image.outputs.manifest_digest", "batch-get-image", "--published-image", "qualified_publication.py"):
    require(required_text in resolve_run, "registry resolution must verify exact qualified manifest/configuration binding")
require(base_image_index >= 0 and base_image_index < build_index < push_index < resolve_index,
        "qualified acquisition/build/publish/registry verification must be ordered")

platform_index, platform_step = step("Verify published target-platform image")
platform_run = text(platform_step.get("run"))
for required_text, message in {
    'expected_platform="linux/amd64"': "published image verification must bind the reviewed runtime platform",
    'docker pull --platform "$expected_platform"': "published image verification must pull the immutable digest for the reviewed platform",
    'docker image inspect "${{ steps.image.outputs.uri }}"': "published image verification must inspect the immutable digest rather than a mutable tag",
    'if [ "$source_revision" != "$GITHUB_SHA" ]; then': "published image verification must bind the image revision to the checked-out commit",
}.items():
    require(required_text in platform_run, message)
require(
    build_index >= 0 and platform_index > build_index and platform_index < scan_index,
    "published image platform verification must occur after build/push and before scan evidence",
)

# Only the explicitly named normalized receipts may leave the hosted runner.
for name, identity, condition, artifact_name, paths, lower, upper in (
    ("Retain normalized qualification receipts", "qualification-receipts", "${{ success() }}",
     "qualified-image-${{ github.run_id }}-${{ github.run_attempt }}",
     ["${{ runner.temp }}/qualified-image/handoff/container-result.json", "${{ runner.temp }}/qualified-image/handoff/handoff.json"], build_index, push_index),
    ("Retain normalized publication receipt", "publication-receipt", "${{ inputs.publish_image && steps.image.outcome == 'success' }}",
     "published-image-${{ github.run_id }}-${{ github.run_attempt }}",
     ["${{ runner.temp }}/qualified-image/publication-check.json"], resolve_index, platform_index),
):
    index, upload = step(name)
    require(lower < index < upper, "receipt retention must follow its successful producer and precede later failure-prone steps")
    require(upload.get("id") == identity and upload.get("if") == condition,
            "receipt upload may run only after its normalized producer succeeds")
    require(upload.get("uses") == "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
            "receipt uploader must use the reviewed immutable official action")
    inputs = upload.get("with", {})
    require(isinstance(inputs, dict) and set(inputs) == {"name", "path", "retention-days", "include-hidden-files", "overwrite", "if-no-files-found"},
            "receipt upload inputs must remain the bounded reviewed set")
    if not isinstance(inputs, dict): inputs = {}
    require(text(inputs.get("path")).splitlines() == paths,
            "receipt upload must name only the explicit normalized files without directories or globs")
    for key, expected in {"name": artifact_name, "retention-days": "7", "include-hidden-files": "false", "overwrite": "false", "if-no-files-found": "error"}.items():
        require(inputs.get(key) == expected, "receipt upload must retain bounded nonoverwriting seven-day storage and fail on missing files")

image_profile = target_profile.get("artifacts", {}).get("image", {})
if not isinstance(image_profile, dict):
    failures.append("target profile image configuration must be a mapping")
    image_profile = {}
for key, expected in {
    "build_image_policy": "locked-toolchain-verified-payload",
    "runtime_image_policy": "pin-by-digest-for-official-build",
    "runtime_image_class": "minimal-nonroot-distroless-nodejs22-debian12",
    "runtime_platform": "linux/amd64",
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
require(sbom_step.get("if") == "${{ inputs.publish_image }}", "SBOM generation must retain the publication condition")
require(set(sbom_step) == {"name", "if", "id", "env", "run"}, "SBOM generation must use the reviewed direct verified tool path")
require(sbom_step.get("env") == {"SYFT_IMAGE": "${{ steps.image.outputs.uri }}", "SYFT_CHECK_FOR_APP_UPDATE": "false"},
        "SBOM must bind the immutable image and disable update lookup")
REVIEWED_SBOM_RUN = r"""set -euo pipefail
[[ "$SYFT_IMAGE" =~ ^[a-z0-9][a-z0-9./:-]*@sha256:[a-f0-9]{64}$ ]]
umask 077
tool_dir="$(mktemp -d "$RUNNER_TEMP/reviewed-syft.XXXXXX")"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
  https://github.com/anchore/syft/releases/download/v1.42.3/syft_1.42.3_linux_amd64.tar.gz \
  --output "$tool_dir/archive.tar.gz"
printf '%s  %s\n' 0d6be741479eddd2c8644a288990c04f3df0d609bbc1599a005532a9dff63509 "$tool_dir/archive.tar.gz" | sha256sum --check --status
tar --extract --gzip --file "$tool_dir/archive.tar.gz" --directory "$tool_dir" --no-same-owner --no-same-permissions syft
test -f "$tool_dir/syft" && test ! -L "$tool_dir/syft"
printf '%s  %s\n' 6c1eb5c6f15c177fa3dd727ee186c61a660a3939a4e1dc1bc4b3e00eafec098e "$tool_dir/syft" | sha256sum --check --status
chmod 700 "$tool_dir/syft"
test "$("$tool_dir/syft" version --output json | python3 -c 'import json,sys; print(json.load(sys.stdin)["version"])')" = "1.42.3"
"$tool_dir/syft" scan "docker:$SYFT_IMAGE" --output "spdx-json=$RUNNER_TEMP/platform-shell.sbom.spdx.json"
"""
require(text(sbom_step.get("run")) == REVIEWED_SBOM_RUN,
        "SBOM command must verify the fixed archive, binary, version and digest input before exact-image SPDX generation")

for name, expected_id, requires_sbom in [
    ("Attest image provenance", "provenance-attestation", False),
    ("Attest image SBOM", "sbom-attestation", True),
]:
    _, attestation_step = step(name)
    require(attestation_step.get("id") == expected_id, f"{name} must have id {expected_id}")
    require(attestation_step.get("uses") == REVIEWED_ACTIONS[name], f"{name} must use the reviewed immutable attestation action")
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

summary_index, summary_step = step("Record image-publication summary")
summary_run = text(summary_step.get("run"))
for required_text, message in {
    "steps.scan.outputs.status": "deployment summary must record scan status",
    "steps.provenance-attestation.outputs.attestation-url": "deployment summary must record provenance attestation evidence",
    "steps.sbom-attestation.outputs.attestation-url": "deployment summary must record SBOM attestation evidence",
}.items():
    require(required_text in summary_run, message)

workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
build_script_text = BUILD_SCRIPT_PATH.read_text(encoding="utf-8") if BUILD_SCRIPT_PATH.is_file() else ""
service_template_text = SERVICE_TEMPLATE_PATH.read_text(encoding="utf-8") if SERVICE_TEMPLATE_PATH.is_file() else ""
require("TARGET_PLATFORM=\"linux/amd64\"" in build_script_text, "image build wrapper must declare the reviewed linux/amd64 target platform")
require("--platform \"$TARGET_PLATFORM\"" in build_script_text, "image build wrapper must force the reviewed target platform")
require("CpuArchitecture: X86_64" in service_template_text and "OperatingSystemFamily: LINUX" in service_template_text, "service template runtime platform must match the reviewed linux/amd64 target")
for forbidden_text in (
    "aws cloudformation deploy",
    "aws cloudformation create-change-set",
    "aws cloudformation execute-change-set",
    "aws ecs update-service",
    "aws ecs register-task-definition",
):
    require(
        forbidden_text not in workflow_text,
        f"image-publication workflow must not contain target mutation command: {forbidden_text}",
    )
require(
    "Next action: create and review target CloudFormation change sets" in summary_run,
    "image-publication summary must direct service deployment to a separately reviewed change-set workflow",
)

for required_text, message in {
    "steps.base-image.outputs.toolchain_digest": "deployment summary must record the locked compiler contract",
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
