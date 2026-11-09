#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.validation.entity-smoke.publication-workflow
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Enforce fixed qualification, pre-publication identity retention and complete immutable custody before any feature publication is accepted.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.entity-smoke.package-workflow
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/script.sh
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt"))
from workflow_guard import job_steps, protected_step, protected_script, record_command, custody_tail, scan_step

class WorkflowLoader(yaml.SafeLoader):
    pass

# GitHub treats `on` as a field name, not the YAML-1.1 boolean True.
WorkflowLoader.yaml_implicit_resolvers = {key: [(tag, pattern) for tag, pattern in values if tag != "tag:yaml.org,2002:bool"] for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()}
WorkflowLoader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$", re.I), list("tTfF"))

def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result: raise ValueError("duplicate-workflow-field")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result

WorkflowLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
WORKFLOW = ".github/workflows/publish-kanbien-core-platform-entity-smoke.yml"
BASE = "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody"
BUILD = "scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/script.sh"
SMOKE = "scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/script.sh"
QUALIFICATION = [shlex.split(value) for value in ["bash scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/script.sh --json","bash scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/script.sh --tag kanbien-entity-smoke:qualification","bash scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/script.sh --tag kanbien-entity-smoke:qualification","python3 scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py record --image kanbien-entity-smoke:qualification --receipt \"$RUNNER_TEMP/qualified-image.json\" --input infra/04.deploy/03.product/image/entity-smoke/image-contract.yml --input infra/04.deploy/03.product/image/entity-smoke/Dockerfile --input scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs --input scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-dependencies.mjs --input scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/script.sh --input scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/verify-image.mjs --input scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/capability-negative-test.py --input scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py --configuration-input scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke.yml entity-smoke-server,entity-smoke-migration,entity-smoke-administration,entity-smoke-verifier,entity-smoke-database-proof --configuration-input scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke-isolated-restore.yml entity-smoke-restore-reader"]]
BUILD_BODY = r'''set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/04.deploy/shared/safe-command-diagnostics.sh
entity_smoke_tag="kanbien-entity-smoke:qualification"
if [[ $# == 2 && "$1" == --tag ]]; then entity_smoke_tag="$2"; elif [[ $# != 0 ]]; then
  printf '%s\n' 'ENTITY_SMOKE_IMAGE_ARGUMENTS_INVALID' >&2; exit 2
fi
[[ "$entity_smoke_tag" =~ ^kanbien-entity-smoke:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || {
  printf '%s\n' 'ENTITY_SMOKE_IMAGE_ARGUMENTS_INVALID' >&2; exit 2;
}
if [[ -n "$(git status --porcelain --untracked-files=all -- . ':!commitLogs')" ]]; then
  printf '%s\n' 'ENTITY_SMOKE_IMAGE_COMMITTED_SOURCE_REQUIRED' >&2; exit 1
fi
entity_smoke_source="$(git rev-parse HEAD)"
[[ "$entity_smoke_source" =~ ^[a-f0-9]{40}$ ]] || { printf '%s\n' 'ENTITY_SMOKE_IMAGE_SOURCE_INVALID' >&2; exit 1; }
bash scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh \
  --scope-contract infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml --json
python3 -B scripts/04.deploy/inventory-deploy-control/script.py --delivery --check
bash scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh \
  --target-root infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes --json
safe_command_diagnostic ENTITY_SMOKE_IMAGE_PROGRAM_INVALID package 'The isolated program contract was not confirmed.' 'Inspect the program declaration without changing accepted programs.' -- \
  bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh \
  --contract infra/04.deploy/03.product/entrypoints/runnable-program-index.yml --json
safe_command_diagnostic ENTITY_SMOKE_IMAGE_DIAGNOSTICS_NOT_CONFIRMED package 'The source diagnostic contract check failed.' 'Regenerate code-owned catalog exports or correct their source before packaging.' -- \
  bash scripts/repo/diagnostic-coverage/verify.sh --unit catalog
safe_command_diagnostic ENTITY_SMOKE_IMAGE_FEATURE_NOT_CONFIRMED package 'The feature contract and use-case checks failed.' 'Correct the feature before image qualification.' -- \
  npm --ignore-scripts run app:entity-smoke:check
safe_command_diagnostic ENTITY_SMOKE_IMAGE_COMPOSITION_FAILED package 'The isolated feature composition failed.' 'Correct the local wiring before image qualification.' -- \
  bash scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
if ! command -v docker >/dev/null 2>&1 || ! timeout 30 docker info >/dev/null 2>&1; then
  printf '%s\n' 'ENTITY_SMOKE_IMAGE_LOCAL_ENGINE_UNAVAILABLE' >&2; exit 1
fi
safe_command_diagnostic ENTITY_SMOKE_IMAGE_BUILD_FAILED package 'The isolated image build failed.' 'Inspect this build attempt; publication and deployment were not invoked.' -- \
  docker build --load --platform linux/amd64 --provenance=false --file infra/04.deploy/03.product/image/entity-smoke/Dockerfile \
  --tag "$entity_smoke_tag" --label "org.opencontainers.image.revision=$entity_smoke_source" \
  --label org.opencontainers.image.source=entity-builder-harness \
  --build-arg "SOURCE_COMMIT_SHA=$entity_smoke_source" "$ROOT"
printf '%s\n' 'ENTITY_SMOKE_LOCAL_IMAGE_BUILT_NOT_QUALIFIED'
'''
SMOKE_BODY = r'''set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [[ $# == 2 && "$1" == --cleanup-reservation ]]; then
  exec node scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/verify-image.mjs "$@"
fi
bash scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh \
  --scope-contract infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml --json
python3 -B scripts/04.deploy/inventory-deploy-control/script.py --delivery --check
node scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/verify-image.mjs "$@"
entity_smoke_tag="kanbien-entity-smoke:qualification"
if [[ $# == 2 && "$1" == --tag ]]; then entity_smoke_tag="$2"; fi
python3 -B scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/capability-negative-test.py --image "$entity_smoke_tag"
'''

def inspect(text, builder=None, smoke=None):
    try:
        workflow = yaml.load(text, Loader=WorkflowLoader)
        if not isinstance(workflow, dict) or workflow.get("on") != {"workflow_dispatch": {}}:
            raise ValueError("trigger")
        if set(workflow) - {"name", "on", "permissions", "concurrency", "env", "jobs"}:
            raise ValueError("workflow-fields")
        if workflow.get("permissions") != {"contents": "read", "id-token": "write", "attestations": "write", "artifact-metadata": "write"}:
            raise ValueError("permissions")
        if workflow.get("env") != {"AWS_REGION": "eu-west-1", "AWS_ROLE_ARN": "arn:aws:iam::337159794548:role/github-kanbien-core-platform-entity-smoke-publisher", "ECR_REPOSITORY": "kanbien-core-platform/entity-smoke", "ECR_URI": "337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/entity-smoke"}:
            raise ValueError("destination")
        if workflow.get("concurrency") != {"group": "kanbien-core-platform-entity-smoke-publication", "cancel-in-progress": False}:
            raise ValueError("concurrency")
        if set(workflow["jobs"]) != {"qualify-and-publish"}:
            raise ValueError("jobs")
        job = workflow["jobs"]["qualify-and-publish"]
        if set(job) != {"runs-on", "timeout-minutes", "environment", "steps"} or job["runs-on"] != "ubuntu-latest" or job["timeout-minutes"] != 35 or job["environment"] != "kanbien-core-platform":
            raise ValueError("job")
        steps = job_steps(text, "qualify-and-publish")
        order = [
            "@actions/checkout@v4", "Enforce protected main source", "@actions/setup-node@v4", "Install dependencies", "Install script dependencies",
            "Enforce delivery-chain registration and contracts", "Qualify declarations and actual candidate payload",
            "@aws-actions/configure-aws-credentials@v4", "Prove fixed delivery read access", "Retain pre-publication identity",
            "Log in to Amazon ECR", "Publish immutable image", "Require clean ECR scan", "Generate SBOM", "Attest image provenance", "Attest image SBOM",
            "Write and validate safe package-custody receipt", "Upload safe package-custody evidence", "Record package-custody summary", "Retain safe failed-operation evidence",
        ]
        if [step.get("name", "@"+str(step.get("uses"))) for step in steps] != order:
            raise ValueError("steps")
        if steps[0] != {"uses": "actions/checkout@v4", "with": {"persist-credentials": False}} or steps[2] != {"uses": "actions/setup-node@v4", "with": {"node-version": "22"}}:
            raise ValueError("source")
        protected_step(steps, "Enforce protected main source", [["test", "$GITHUB_REF", "=", "refs/heads/main"]])
        protected_step(steps, "Install dependencies", [["npm", "ci", "--ignore-scripts"]])
        protected_step(steps, "Install script dependencies", [["python3", "-m", "pip", "install", "PyYAML==6.0.2"]])
        protected_step(steps, "Enforce delivery-chain registration and contracts", [["python3", "scripts/04.deploy/inventory-deploy-control/script.py", "--delivery", "--check"]])
        qualification_index, qualification = protected_step(steps, "Qualify declarations and actual candidate payload", QUALIFICATION)
        if qualification.get("id") != "qualification":
            raise ValueError("qualification-outcome")
        if steps[7] != {"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "${{ env.AWS_ROLE_ARN }}", "aws-region": "${{ env.AWS_REGION }}"}}:
            raise ValueError("credentials")
        access_index, access = protected_step(steps, "Prove fixed delivery read access", [["python3", BASE+"/publication.py", "--operation", "reserve"]])
        retained_index, retained = protected_step(steps, "Retain pre-publication identity")
        if retained != {"name": "Retain pre-publication identity", "uses": "actions/upload-artifact@v4", "with": {
            "name": "kanbien-core-platform-entity-smoke-reservation-${{ github.run_id }}",
            "path": "${{ runner.temp }}/entity-smoke-publication-reservation.json\n${{ runner.temp }}/qualified-image.json\n",
            "if-no-files-found": "error", "overwrite": False, "retention-days": 30}}:
            raise ValueError("reservation-retention")
        login_index, login = protected_step(steps, "Log in to Amazon ECR")
        if login != {"name": "Log in to Amazon ECR", "uses": "aws-actions/amazon-ecr-login@v2"}:
            raise ValueError("registry-login")
        publication_index, publication = protected_step(steps, "Publish immutable image", [["python3", BASE+"/publication.py", "--operation", "publish"]])
        if access.get("id") != "access" or publication.get("id") != "image" or not qualification_index < access_index < retained_index < login_index < publication_index:
            raise ValueError("publication-order")
        scanned = scan_step(steps, ["python3", "scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py", "--repository", "$ECR_REPOSITORY", "--image-digest", "${{ steps.image.outputs.digest }}", "--report", "$RUNNER_TEMP/ecr-scan.json"], "Require clean ECR scan")
        if scanned <= publication_index:
            raise ValueError("scan-order")
        custody_tail(steps, published_index=scanned, target="kanbien-core-platform", environment="private-feature-candidate", region="aws-eu-west-1",
                     candidate="kanbien-entity-smoke-candidate", contract="kanbien-entity-smoke-image", program="kanbien-entity-smoke", stem="entity-smoke",
                     artifact_name="kanbien-core-platform-entity-smoke-package-custody-${{ github.run_id }}",
                     qualification_outcome="${{ steps.qualification.outcome }}", scan_outcome="${{ steps.scan.outcome }}", scan_check="ecr_scan",
                     provenance_name="Attest image provenance", attestation_name="Attest image SBOM", capture_name="Write and validate safe package-custody receipt",
                     upload_name="Upload safe package-custody evidence", receipt_filename="package-custody-receipt.json",
                     extra_artifacts=["${{ runner.temp }}/qualified-image.json", "${{ runner.temp }}/ecr-scan.json"], registry_expression="${{ env.ECR_URI }}")
        failure_index, failure = protected_step(steps, "Retain safe failed-operation evidence", condition="${{ failure() }}")
        if failure != {"name": "Retain safe failed-operation evidence", "if": "${{ failure() }}", "uses": "actions/upload-artifact@v4", "with": {
            "name": "kanbien-core-platform-entity-smoke-failed-operation-${{ github.run_id }}-${{ github.run_attempt }}",
            "path": "${{ runner.temp }}/entity-smoke-publication-reservation.json\n${{ runner.temp }}/entity-smoke-publication-invoked.json\n${{ runner.temp }}/entity-smoke-publication-operation.json\n",
            "if-no-files-found": "ignore", "overwrite": False, "retention-days": 30}}:
            raise ValueError("failure-retention")
        # Summary is information-only, but cannot run an unreviewed provider command.
        summary_index, summary = protected_step(steps, "Record package-custody summary")
        expected_summary = '''{
echo '## Kanbien core platform entity-smoke package custody'
echo "- Source revision: $GITHUB_SHA"
echo "- Immutable image digest: ${{ steps.image.outputs.digest }}"
echo "- Scanned AMD64 manifest: ${{ steps.scan.outputs.scan_digest }}"
echo "- ECR scan: ${{ steps.scan.outputs.verdict }}"
echo "- Receipt: github-actions-run:$GITHUB_RUN_ID"
echo '- Deployment: not performed by this workflow.'
} >> "$GITHUB_STEP_SUMMARY"'''
        summary_lines = [line.strip() for line in summary["run"].splitlines() if line.strip()]
        if summary_lines != expected_summary.splitlines():
            raise ValueError("summary-command")
        protected_script(builder or ROOT/BUILD, BUILD_BODY)
        protected_script(smoke or ROOT/SMOKE, SMOKE_BODY)
    except (OSError, UnicodeError, yaml.YAMLError, ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError):
        return ["entity-smoke-publication-contract-invalid"]
    return []


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: parser.exit(2, "ENTITY_SMOKE_WORKFLOW_ARGUMENTS_INVALID\n")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    findings = ["entity-smoke-publication-arguments-invalid"] if unknown else inspect((ROOT/WORKFLOW).read_text())
    print(json.dumps({"schema": "deploy/package-workflow-validation/v1", "target": "kanbien-core-platform", "scope": "entity-smoke",
                      "verdict": "failed" if findings else "passed", "findings": [{"code": item} for item in findings]}, sort_keys=True))
    return int(bool(findings))


if __name__ == "__main__":
    try: status = main()
    except (OSError, ValueError, TypeError):
        print(json.dumps({"schema": "deploy/package-workflow-validation/v1", "verdict": "failed", "findings": [{"code": "entity-smoke-publication-observation-unavailable"}]}))
        status = 1
    raise SystemExit(status)
