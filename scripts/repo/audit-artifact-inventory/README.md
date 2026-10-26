<!-- agentic-artifact:
schema: agentic-artifact/v3
id: repo.script.audit-artifact-inventory.readme
version: 1
status: active
created_on: "2026-10-26"
updated_on: "2026-10-26"
layer: 06.shared
domain: validation
disciplines:
- agentic
kind: capability-readme
purpose: Explain the explicit complete artifact inventory audit.
portability:
  class: source-only
  targets: []
used_by:
- id: repo.script.audit-artifact-inventory
  path: scripts/repo/audit-artifact-inventory/script.sh
-->
# Audit Artifact Inventory

Run this command when changing artifact metadata policy, preparing a broad
governance change, or auditing repository-wide declaration coverage:

```bash
bash scripts/repo/audit-artifact-inventory/script.sh
```

It performs the complete strict metadata-index and coverage audit. Ordinary task
commits run focused impact checks plus staged metadata validation instead.
