<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.run-platform-shell-persistence-smoke.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded one-request persistence acceptance smoke for Kanbien staging.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-persistence-smoke
  path: scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh
-->
# Run Platform-Shell Persistence Smoke

This is not a general API client. It has one job: after a reviewed persistence
deployment, request a short-lived Cognito access token from the separately
owned write-only machine client, then make exactly one no-body request:

```text
POST https://staging.platform.kanbien.com/smoke/work-items
```

The fixed `X-Request-Id` makes the work item deterministic. The command is
therefore deliberately one-shot: it runs only while the target profile is in
`deployed-pending-write-proof`. After a successful result, the retained proof
record changes state and a second invocation is rejected rather than relying
on a duplicate response as evidence.

It accepts no caller-supplied client ID, secret, scope, route, body, or request
ID. It requests only `platform-shell/smoke.write`, reads only the separately
declared secret, and emits only a verdict, HTTP status, and rounded duration.
It never prints a token, secret, request/response body, generated work-item
identifier, or provider response.

Before live execution, source policy may be checked without contacting AWS:

```bash
npm run platform:shell:persistence-smoke -- --validate
```

Live execution is an AWS secret read and one production-like staging write. It
requires the governed AWS workflow and explicit current-chat approval:

```bash
npm run platform:shell:persistence-smoke -- --execute
```

The command does not start the relay or worker. Those remain separately
bounded proof stages in the persistence deployment plan.
