<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.command.runnable-program-contract.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
- agentic
- architecture
- security
- sre
kind: capability-readme
purpose: Describe the report-only checker for runnable-program and package-candidate contracts.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.workflow.runnable-program-candidates
  path: .agentic/04.deploy/workflows/runnable-program-candidates.md
-->
# Runnable Program Contract Checker

This is an offline, provider-neutral declaration checker. It reads a contract
and emits only a safe JSON report. It does not inspect source imports yet,
build an image, access a network, publish a package, read a target, or mutate
anything.

```bash
bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh \
  --contract path/to/runnable-program-contract.yml --json

bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/smoke-test.sh
```

The caller supplies the observed dependency list. A later deterministic source
dependency reporter will generate that list from a selected program root.

The checker fails closed with stable codes for missing program records, invalid
image commands, unapproved dependencies, and unsafe evidence field names.
