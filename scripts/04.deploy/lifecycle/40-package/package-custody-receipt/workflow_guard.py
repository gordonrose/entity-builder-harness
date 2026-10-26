#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.validation.package-qualification-workflow
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
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


def custody_tail(steps, *, published_index, target, environment, region, candidate, contract, program, stem, artifact_name, qualification_outcome, scan_outcome, scan_check, provenance_name, attestation_name, capture_name, upload_name, receipt_filename, extra_artifacts, registry_expression):
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
