<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.render-platform-shell-foundation-template.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: capability-readme
purpose: Explain deterministic rendering of the Kanbien platform-shell foundation source units.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.render-platform-shell-foundation-template
  path: scripts/04.deploy/render-platform-shell-foundation-template/script.sh
-->
# Render Platform-Shell Foundation Template

The Kanbien staging platform-shell foundation is intentionally authored as
focused source units: ingress, edge protection, workload IAM, rate limiting,
logging, alerting, and exported values. AWS CloudFormation accepts one template
body for this foundation stack and cannot include repository-local YAML files
by itself.

`script.sh` deterministically combines those source units into one transient
CloudFormation template. It does not call AWS. The rendered output is used for
local static checks, AWS template validation, a reviewed change set, and the
manually governed first foundation deployment.

Run it with:

```bash
bash scripts/04.deploy/render-platform-shell-foundation-template/script.sh --output /tmp/platform-shell-foundation.yml
```

Do not edit the rendered output or commit it as a second source of truth.
Edit the files named by
`infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation.yml`
instead.
