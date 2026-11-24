#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.validation.package-qualification-workflow
#   version: 3
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-22"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject qualification omission, substitution, reordered boundaries and mutable publication identity.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.core-server-package-custody.validation
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/verify-workflow.py
"""Fail-closed primitives for the existing publication workflow owners."""
import shlex
import yaml

QUALIFICATION = "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py"

def job_steps(text, job_name):
    workflow = yaml.safe_load(text)
    job = workflow["jobs"][job_name]
    for owner in (workflow, job):
        if owner.get("defaults", {}) != {} or "continue-on-error" in owner: raise ValueError("execution-defaults-overridden")
    if "if" in job: raise ValueError("qualification-job-conditional")
    steps = job["steps"]
    if not isinstance(steps, list) or not all(isinstance(item, dict) for item in steps): raise ValueError("steps-invalid")
    return steps

def protected_step(steps, name, commands=None, condition=None, environment=None):
    found = [(i, step) for i, step in enumerate(steps) if step.get("name") == name]
    if len(found) != 1: raise ValueError("qualification-step-missing-or-duplicate")
    index, step = found[0]
    if any(key in step for key in ("continue-on-error", "shell", "working-directory")): raise ValueError("qualification-step-overridden")
    if step.get("if") != condition: raise ValueError("qualification-step-conditional")
    if step.get("env", {}) != (environment or {}): raise ValueError("qualification-step-environment-substituted")
    if commands is not None:
        lines = [shlex.split(line) for line in step.get("run", "").replace("\\\n", " ").splitlines() if line.strip() and not line.lstrip().startswith("#")]
        if lines != commands: raise ValueError("qualification-command-substituted")
    return index, step

def record_command(tag, inputs, configuration_inputs=()):
    command = ["python3", QUALIFICATION, "record", "--image", tag, "--receipt", "$RUNNER_TEMP/qualified-image.json"]
    for path in inputs: command.extend(["--input", path])
    for adapter,source,selector in configuration_inputs: command.extend(["--configuration-input",adapter,source,selector])
    return command


def publication_binding(steps, qualification_index, tag, credential_prefixes, destination, expected_commands):
    index, step = protected_step(steps, "Publish immutable image")
    if index <= qualification_index: raise ValueError("publication-precedes-qualification")
    credentials = [i for i, item in enumerate(steps) if str(item.get("uses", "")).startswith(credential_prefixes)]
    if not credentials or min(credentials) <= qualification_index: raise ValueError("credentials-precede-qualification")
    lines = [line.strip() for line in step.get("run", "").splitlines() if line.strip()]
    if [shlex.split(line) for line in lines] != expected_commands: raise ValueError("publication-command-substituted")
    tagging = 'docker tag "$qualified_image" "' + destination + '"'
    if len(lines) < 5 or lines[0] != "set -euo pipefail" or lines[3:5] != [tagging, 'docker push "' + destination + '"']:
        raise ValueError("publication-qualified-identity-substituted")
    if 'test "$(docker image inspect "$image" --format \'{{.Id}}\')" = "$qualified_image"' not in lines:
        raise ValueError("publication-remote-identity-unverified")
    for between in steps[qualification_index+1:index]:
        if any(word in between.get("run", "") for word in ("docker build", "docker tag", "docker load", "qualified-image.json")):
            raise ValueError("qualification-replaced-before-publication")
    return True

def unconditional_run(step):
    lines = [line.strip() for line in step.get("run", "").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines or lines[0] != "set -euo pipefail": raise ValueError("step-not-fail-closed")
    for line in lines[1:]:
        if line.startswith(("if ", "then", "else", "fi", "for ", "while ", "until ", "case ", "function ", "return", "exit", "set ")) or " || " in line or " && " in line:
            raise ValueError("step-control-flow-overridden")
    return lines


def reserved_publication_binding(steps, qualification_index, *, command, stem, target, access_commands=(), prepublication_artifacts=()):
    """Require the shared publisher's durable reservation and no-replay route."""
    credentials = [(i, step) for i, step in enumerate(steps) if str(step.get("uses", "")).startswith("aws-actions/configure-aws-credentials@")]
    if len(credentials) != 1:
        raise ValueError("publication-credentials-invalid")
    credential_index, credential = credentials[0]
    if credential != {"uses": "aws-actions/configure-aws-credentials@v4", "with": {
        "role-to-assume": "${{ env.AWS_ROLE_ARN }}", "aws-region": "${{ env.AWS_REGION }}"}}:
        raise ValueError("publication-credentials-substituted")
    access_index, access = protected_step(steps, "Prove fixed delivery read access",
        [*access_commands, ["python3", command, "--operation", "reserve"]])
    retained_index, retained = protected_step(steps, "Retain pre-publication identity")
    retained_paths = "${{ runner.temp }}/" + stem + "-publication-reservation.json\n${{ runner.temp }}/qualified-image.json\n" + "".join(path + "\n" for path in prepublication_artifacts)
    if retained != {"name": "Retain pre-publication identity", "uses": "actions/upload-artifact@v4", "with": {
        "name": target + "-" + stem + "-reservation-${{ github.run_id }}",
        "path": retained_paths,
        "if-no-files-found": "error", "overwrite": False, "retention-days": 30}}:
        raise ValueError("publication-reservation-retention-invalid")
    login_index, login = protected_step(steps, "Log in to Amazon ECR")
    if login != {"name": "Log in to Amazon ECR", "uses": "aws-actions/amazon-ecr-login@v2"}:
        raise ValueError("publication-login-substituted")
    index, publication = protected_step(steps, "Publish immutable image", [["python3", command, "--operation", "publish"]])
    if access.get("id") != "access" or publication.get("id") != "image" or not qualification_index < credential_index < access_index < retained_index < login_index < index:
        raise ValueError("publication-order-invalid")
    failure_index, failure = protected_step(steps, "Retain safe failed-operation evidence", condition="${{ failure() }}")
    paths = "".join("${{ runner.temp }}/" + stem + "-publication-" + suffix + ".json\n" for suffix in ("reservation", "invoked", "operation"))
    if failure != {"name": "Retain safe failed-operation evidence", "if": "${{ failure() }}", "uses": "actions/upload-artifact@v4", "with": {
        "name": target + "-" + stem + "-failed-operation-${{ github.run_id }}-${{ github.run_attempt }}",
        "path": paths, "if-no-files-found": "ignore", "overwrite": False, "retention-days": 30}} or failure_index <= index:
        raise ValueError("publication-failure-retention-invalid")
    for between in steps[qualification_index+1:index]:
        if any(word in between.get("run", "") for word in ("docker build", "docker tag", "docker load", "qualified-image.json")):
            raise ValueError("qualification-replaced-before-publication")
    return index


def custody_tail(steps, *, published_index, target, environment, region, candidate, contract, program, stem, artifact_name, qualification_outcome, scan_outcome, scan_check, provenance_name, attestation_name, capture_name, upload_name, receipt_filename, extra_artifacts, registry_expression, local_qualification_filename=None):
    """Protect the producer/consumer proof boundaries; route identities stay with callers."""
    sbom_index, sbom = protected_step(steps, "Generate SBOM")
    provenance_index, provenance = protected_step(steps, provenance_name)
    attestation_index, attestation = protected_step(steps, attestation_name)
    file = stem + ".sbom.spdx.json"
    if sbom.get("id") != "sbom" or sbom.get("uses") != "anchore/sbom-action@v0" or sbom.get("with") != {"image":registry_expression+"@${{ steps.image.outputs.digest }}","format":"spdx-json","output-file":"${{ runner.temp }}/"+file,"upload-artifact":False,"upload-release-assets":False}: raise ValueError("custody-sbom-substituted")
    common={"subject-name":registry_expression,"subject-digest":"${{ steps.image.outputs.digest }}","push-to-registry":True,"create-storage-record":False}
    if provenance.get("id") != "provenance" or provenance.get("uses") != "actions/attest@v4" or provenance.get("with") != common: raise ValueError("custody-provenance-substituted")
    if attestation.get("id") != "sbom-attestation" or attestation.get("uses") != "actions/attest@v4" or attestation.get("with") != {**common,"sbom-path":"${{ runner.temp }}/"+file}: raise ValueError("custody-sbom-attestation-substituted")
    receipt = receipt_filename
    capture_command=["python3","scripts/04.deploy/lifecycle/40-package/package-custody-receipt/capture.py","--target",target,"--environment-class",environment,"--provider-region-alias",region,"--candidate",candidate,"--package-contract",contract,"--program",program,"--scan-check",scan_check,"--sbom","$RUNNER_TEMP/"+file,"--output","$RUNNER_TEMP/"+receipt]
    if local_qualification_filename is not None:
        capture_command[-2:-2] = ["--local-qualification", "$RUNNER_TEMP/" + local_qualification_filename]
    validate_command=["bash","scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh","--receipt","$RUNNER_TEMP/"+receipt,"--expected-target",target,"--expected-candidate",candidate,"--expected-package-contract",contract,"--expected-program",program,"--json"]
    outcomes={"IMAGE_DIGEST":"${{ steps.image.outputs.digest }}","QUALIFICATION_OUTCOME":qualification_outcome,"ACCESS_OUTCOME":"${{ steps.access.outcome }}","PUBLICATION_OUTCOME":"${{ steps.image.outcome }}","SCAN_OUTCOME":scan_outcome,"SBOM_OUTCOME":"${{ steps.sbom.outcome }}","PROVENANCE_OUTCOME":"${{ steps.provenance.outcome }}","SBOM_ATTESTATION_OUTCOME":"${{ steps.sbom-attestation.outcome }}"}
    capture_index,capture=protected_step(steps,capture_name,[capture_command,validate_command],environment=outcomes)
    if capture.get("env")!=outcomes:raise ValueError("custody-outcome-substituted")
    upload_index,upload=protected_step(steps,upload_name)
    paths=["${{ runner.temp }}/"+receipt,"${{ runner.temp }}/"+file]
    paths+=extra_artifacts
    if upload.get("uses")!="actions/upload-artifact@v4" or upload.get("with")!={"name":artifact_name,"path":"\n".join(paths)+"\n","if-no-files-found":"error","retention-days":30,"overwrite":False}:raise ValueError("custody-upload-substituted")
    if not published_index < sbom_index < provenance_index < attestation_index < capture_index < upload_index:raise ValueError("custody-proof-order-invalid")
    return True


def scan_step(steps, command, name, condition=None):
    index,step=protected_step(steps,name,[command],condition)
    if step.get("id")!="scan":raise ValueError("scan-outcome-id-substituted")
    return index


def protected_script(path, expected):
    """Guard a short nested qualification wrapper, including its control flow.

    Workflow owners supply the reviewed executable body; comments and indentation
    are immaterial, but arguments, order, conditions and status handling are exact.
    """
    def executable(source):
        return [line.strip() for line in source.replace("\\\n", " ").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if executable(path.read_text()) != executable(expected):
        raise ValueError("nested-qualification-command-substituted")


CANDIDATE_BUILD_OPERATIONS = "scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh"


def protected_candidate_build(path):
    """Both workflow owners bind the same reviewed private build operations."""
    protected_script(path, r'''candidate_image_prechecks() {
  local scope="$1" target="$2" code="$3" summary="$4" next_check="$5"
  shift 5
  bash scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh --scope-contract "$scope" --json
  "$@" scripts/04.deploy/inventory-deploy-control/script.py --delivery --check
  bash scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh --target-root "$target" --json
  safe_command_diagnostic "$code" package "$summary" "$next_check" -- bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh --contract infra/04.deploy/03.product/entrypoints/runnable-program-index.yml --json
}

candidate_image_build() {
  local code="$1" summary="$2" next_check="$3" dockerfile="$4" tag="$5" revision="$6" source_commit="$7" root="$8"
  shift 8
  safe_command_diagnostic "$code" package "$summary" "$next_check" -- docker build "$@" --file "$dockerfile" --tag "$tag" --label "org.opencontainers.image.revision=$revision" --label org.opencontainers.image.source=entity-builder-harness --build-arg "SOURCE_COMMIT_SHA=$source_commit" "$root"
}
''')
