<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.script.inventory-deploy-control.readme
version: 1
status: active
created_on: "2026-10-06"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.governance
disciplines:
- architecture
- sre
kind: capability-readme
purpose: Explain the read-only deploy-control inventory and its limits.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.script.inventory-deploy-control
  path: scripts/04.deploy/inventory-deploy-control/script.sh
-->
# Deploy Control Inventory

This command creates a current, read-only census of `scripts/04.deploy/` and
`infra/04.deploy/`. It is the starting point for restoring human control of
the deploy surface; it does not reorganise, approve, execute, or inspect a
cloud target.

It reports, for each deploy-script capability:

- its entrypoint files and package commands;
- whether the root script index and capability README describe it;
- its declared source effects;
- whether its source needs human mutation review; and
- tracked repository files that call it.

It reports, for each infrastructure file:

- a transparent path-based current-role classification;
- line count; and
- tracked repository files that refer to it.

`review-required` is conservative. It indicates that the source contains a
possible execution marker such as `--execute`; it does not claim that the
command will mutate AWS.

## Usage

Human-readable report:

```bash
npm run deploy:control:inventory
```

Machine-readable report:

```bash
bash scripts/04.deploy/inventory-deploy-control/script.sh --json
```

Validate that the census can be generated:

```bash
bash scripts/04.deploy/inventory-deploy-control/script.sh --check
```

## Effects

Read-only. The command reads tracked repository files only. It does not call
AWS, read secrets, build images, open a network connection, or write a report
to disk.
