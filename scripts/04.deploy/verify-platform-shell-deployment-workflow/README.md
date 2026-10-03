<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-deployment-workflow.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the static supply-chain gate for the Kanbien staging platform-shell deployment workflow.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-deployment-workflow
  path: scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh
-->
# Verify Platform-Shell Deployment Workflow

`script.sh` is a read-only check of the GitHub Actions workflow that deploys
the Kanbien staging platform shell. It makes the intended supply-chain order
machine-checkable:

```text
publish immutable image
        ↓
wait for ECR to create the asynchronous scan record, then complete scan with zero critical and high findings
        ↓
generate SPDX SBOM
        ↓
attest provenance and the SBOM for that exact digest
        ↓
deploy the CloudFormation service stack by digest
```

The check also requires the narrowly scoped GitHub permissions used by the
attestation action. The real workflow publishes the signed provenance and SBOM
attestations beside the immutable ECR image and records their GitHub URLs in
the run summary. It does not upload a separate SBOM artifact or request broad
repository-write permission; the attested SBOM is the durable evidence.

This command does not call GitHub or AWS, build an image, or alter repository
files.

Run it with:

```bash
npm run platform:shell:deployment-workflow:check
```

This check guards the workflow shape. The workflow itself remains responsible
for evaluating the actual scan result, generating the SBOM, and creating the
signed attestations during a real deployment.

The workflow resolves and pins both image boundaries: a build-stage Node image
and the minimal non-root image which becomes the final deployable artifact.
The scan gate evaluates the latter. A scan record can appear a few seconds
after an ECR push, so the workflow has a bounded five-minute wait for record
creation before using the AWS completion waiter. That is intentionally not a
retry of a failed scan: a completed scan with any critical or high finding still
blocks the deployment.
