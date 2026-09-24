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

The initial fixed `X-Request-Id` makes the work item deterministic. The command
is therefore deliberately one-shot: it runs only while the target profile is
in `deployed-pending-write-proof`. After a successful result, the retained
proof record changes state and a second invocation is rejected rather than
relying on a duplicate response as evidence.

If the one permitted request fails, the profile first moves to
`write-proof-failed-non-committing-remediation-pending`. Validation still
works in that state, but execution is refused. After the remediation is
deployed and its server health is verified, the profile moves to
`write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending`.
Execution remains refused unless a later user authorises exactly one
replacement and the operator supplies the explicit replacement guard. That
replacement uses a different fixed opaque request identity, so its result is
unambiguous even though the original attempt was proved non-committing. Relay
and worker actions remain prohibited until the replacement has succeeded and
its safe evidence is recorded.

If that replacement also fails, the profile moves to
`write-proof-failed-non-committing-replacement-pre-server-diagnosis-pending`.
Both execution forms are then refused. This is intentional: the command has
no “try again” mode. A reviewer must first diagnose the possible pre-server or
ingress path, record the result, and grant new bounded authority before any
future write, relay, or worker action can occur.

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

After a documented non-committing failure, deployed remediation, and fresh
current-chat approval, the only permitted replacement form is:

```bash
npm run platform:shell:persistence-smoke -- --execute --approve-replacement-after-remediation
```

The guard is not a general retry switch. It is accepted only for the one
recorded lifecycle state and it never accepts a caller-supplied request ID.

The command does not start the relay or worker. Those remain separately
bounded proof stages in the persistence deployment plan.
