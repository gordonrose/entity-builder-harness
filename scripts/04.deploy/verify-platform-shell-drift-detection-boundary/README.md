<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-drift-detection-boundary.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the fast static guard that prevents hidden CloudFormation drift-detection dependencies.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: package.script.platform-shell-drift-detection-boundary-check
  path: package.json
-->
# Verify Platform-Shell Drift-Detection Boundary

This fast, source-only check makes two rules executable:

1. The GitHub reconciliation identity remains a passive verifier. It cannot
   start CloudFormation drift detection or acquire the provider-dependent
   permissions required to do so.
2. Every resource type in the target's CloudFormation sources appears in the
   detector's resource-read contract. A new resource cannot silently create a
   future IAM dependency.

It deliberately does not guess provider permissions. A detector policy cannot
be written until each inventory entry has a reviewed, authoritative action and
scope analysis. Run this while changing target infrastructure, before the
slower full repository validation:

```bash
npm run platform:shell:drift-detection-boundary:check
```

The check does not call AWS, change a role, or claim that a detector is live.
