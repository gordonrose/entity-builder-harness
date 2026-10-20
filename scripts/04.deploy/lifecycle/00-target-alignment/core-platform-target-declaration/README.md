<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.command.core-platform-target-declaration.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.target-alignment
disciplines:
- architecture
- security
- sre
kind: capability-readme
purpose: Explain the report-only static declaration check for the planned Kanbien core-platform target.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.core-platform-target-declaration
  path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh
-->
# Core Platform Target Declaration

This report-only checker confirms that the planned target has a complete
repository declaration while it remains deliberately unselected in AWS. It
does not read provider state, GitHub state, credentials, Docker state, or
secrets, and it cannot make a target ready.

Run:

```bash
bash scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh --json
bash scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/smoke-test.sh
```

`repository-declaration-complete` means every required E0 fact is explicitly
unresolved, owned, and evidenced for later inspection. It does **not** mean
`live-target-aligned`. The checker fails closed if a fact is missing or
unowned, a create-only target is replaced, or the declaration claims live
alignment before E0 provider evidence exists.
