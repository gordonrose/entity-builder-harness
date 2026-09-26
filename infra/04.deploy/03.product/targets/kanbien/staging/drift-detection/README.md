<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.kanbien.staging.drift-detection.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the staged CloudFormation drift-detection boundary for Kanbien staging.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-drift-detection-boundary
  path: scripts/04.deploy/verify-platform-shell-drift-detection-boundary/script.py
-->
# Kanbien Staging CloudFormation Drift Detection

This folder is the source-of-truth boundary for CloudFormation drift detection
for the Kanbien staging platform shell.

`resource-read-contract.yml` is deliberately an inventory before it is a
permission policy. CloudFormation drift detection can require provider read
permissions for every resource type in a stack. A GitHub role that merely
looks narrow in IAM simulation is not proof that those dependent reads will
work at runtime. The inventory therefore fails the repository check whenever
the Foundation or artifact stack gains an unclassified resource type.

The GitHub reconciliation role is **not** the detector. It may read the
existing stack summary, but it must never start an active drift scan or gain
the provider permissions needed to do so. A future target-scoped detector will
have its own AWS identity and a reviewed, evidence-backed resource-read
contract. That detector remains unimplemented until the complete permission
mapping and its recurring cost are reviewed.

This separation has two benefits: it keeps CI's GitHub OIDC role genuinely
small, and it makes a missing provider dependency a source-review failure
before it can become a failed production deployment attempt.
