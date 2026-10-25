<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.kanbien-core-platform.core-server-persistence.operation-diagnostics
version: 1
status: draft
created_on: "2026-10-25"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.core-server-persistence
disciplines: [security, sre]
kind: evidence-location
purpose: Retain safe deployment-operation diagnostics before failed provider artifacts are cleaned up.
portability: { class: internal, targets: [] }
used_by:
  - id: deploy.command.kanbien-core-platform.create-core-server-persistence-change-set
    path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py
-->
# Operation Diagnostics

This directory retains `deploy/deployment-operation-diagnostic/v1` reports for
the named `core-server-persistence` CloudFormation operation that produced
them. A report is failure evidence, not a package receipt, successful proof, or
accepted-release record.

Only the governed controller may write a report here. It uses an operation name
as the filename and records an opaque receipt-path reference. Reports hold
allowlisted operation/resource facts only; raw provider response bodies,
property values, account identifiers, endpoints, credentials, and command
output are prohibited. Commit or retain a report through the normal evidence
route before deleting the corresponding failed provider artifact.
