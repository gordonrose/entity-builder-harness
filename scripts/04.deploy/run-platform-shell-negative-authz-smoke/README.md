<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.run-platform-shell-negative-authz-smoke.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded staging valid-token authorization-denial smoke command.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-negative-authz-smoke
  path: scripts/04.deploy/run-platform-shell-negative-authz-smoke/script.sh
-->
# Platform Shell Negative Authorization Smoke

This command proves the authorization boundary, rather than the authentication
boundary. It reads only the declared negative-test client secret, requests a
five-minute Cognito client-credentials token with the single intentionally
unmapped scope, and calls only `GET /smoke/negative-authz` on the fixed staging
host.

The command can run only after the target configuration is deployed and the
profile says `deployed-pending-403-proof`. It rejects an unexpected account,
hostname, token URL, client allowlist, secret delivery route, scope, permission
mapping, or lifecycle state. It prints only a result, HTTP status, and rounded
duration; it never prints a secret, token, header, response body, or provider
error.

Run the local policy check with:

```bash
npm run platform:shell:negative-authz-smoke:check
```

The live command requires a separate current-chat approval after post-deploy
inspection:

```bash
npm run platform:shell:negative-authz-smoke -- --execute
```
