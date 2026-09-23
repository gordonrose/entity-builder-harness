<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.run-platform-shell-ingress-smoke.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded staging ingress, WAF, routing, and liveness proof.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-ingress-smoke
  path: scripts/04.deploy/run-platform-shell-ingress-smoke/script.sh
-->
# Platform-shell ingress smoke

This command proves four public-boundary facts together, without retaining raw
AWS responses or HTTP bodies:

1. the named WAF is associated with the staging ALB;
2. listener priority `20` forwards only `staging.platform.kanbien.com`;
3. the server task security group permits only TCP `3000` from the declared
   ALB security group; and
4. `GET /livez` on the public host returns `200`.

`--validate` is offline. `--execute` is a bounded read-only AWS inspection
plus one public request, so it remains subject to the current AWS-operation
approval even though it does not mutate cloud resources.
