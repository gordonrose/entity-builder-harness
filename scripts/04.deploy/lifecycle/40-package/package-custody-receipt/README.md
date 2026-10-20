<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.command.package-custody-receipt.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.package-candidates
disciplines: [architecture, security, sre]
kind: script-guide
purpose: Explain validation of safe package-custody receipts after immutable image publication.
portability: { class: internal, targets: [] }
used_by:
  - id: deploy.command.package-custody-receipt-validation
    path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py
-->
# Package Custody Receipt Validation

This package-phase control validates the small, safe receipt retained after an immutable package is published. It neither publishes nor deploys. Callers bind it to their expected target, candidate, image contract, and program so a valid receipt for another target is rejected.
