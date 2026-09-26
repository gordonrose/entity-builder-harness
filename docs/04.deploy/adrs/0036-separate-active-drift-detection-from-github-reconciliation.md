<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.architecture.adr.0036-separate-active-drift-detection-from-github-reconciliation
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- architecture
- security
- sre
kind: adr
purpose: Separate provider-dependent active CloudFormation drift detection from narrow GitHub deployment reconciliation.
portability:
  class: source-only
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-drift-detection-boundary
  path: scripts/04.deploy/verify-platform-shell-drift-detection-boundary/script.py
-->
# ADR 0036: Separate Active Drift Detection from GitHub Reconciliation

## Status

Accepted. The detector deployment remains deliberately pending a reviewed
provider-read contract and cost check.

## Context

CloudFormation drift detection is not authorised solely by
`cloudformation:DetectStackDrift`. For every supported resource in the stack,
AWS can also require provider-specific read permissions. IAM simulation of the
top-level action therefore did not prove that the GitHub OIDC role could start
a scan. The live role failed safely, but only after a GitHub workflow had run.

Giving GitHub all dependent provider reads would join repository CI to a broad,
hard-to-audit AWS permission boundary. It would also make each new resource
type a hidden reason for a later deployment failure.

## Decision

GitHub reconciliation remains a narrow, passive verifier. It may validate its
own identity, exact stack summaries, the private artifact store, and the
declared budget. It must not start a drift scan or hold the provider reads
needed for one.

Active drift detection will be a separate target-scoped AWS workload and
identity. Before that identity or workload can be created, every resource type
in the two stacks must have an evidence-backed provider-read contract: required
actions, possible resource scoping, authoritative documentation, and a safe
live probe. The source inventory is a mandatory static gate; adding an
unclassified resource type fails validation.

Until the detector exists, an `IN_SYNC` stack summary that is no older than the
declared evidence window is an interim fail-closed guard only. It is not a
claim of continuous drift-detection coverage.

## Consequences

The next Foundation change remains blocked if fresh drift evidence is missing.
The GitHub role stays small and its workflow proves the operations it actually
performs. A later detector requires a reviewed AWS change plan, a cost estimate,
an exact separate role, a disposable failure rehearsal, and explicit approval
before AWS resources are created.
