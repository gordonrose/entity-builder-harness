<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.run-platform-shell-controlled-smoke.readme
version: 3
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded, redacted protected-route smoke command for Kanbien staging.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-controlled-smoke
  path: scripts/04.deploy/run-platform-shell-controlled-smoke/script.sh
-->
# Run Platform-Shell Controlled Smoke

This command validates, or performs exactly one, protected staging smoke read.
It is not a general HTTP client, token printer, credential tool, load test, or
identity-administration command.

Local policy validation makes no AWS or network call:

```bash
npm run platform:shell:controlled-smoke -- --validate
```

A live invocation reads the one declared opaque Cognito client secret, confirms
the selected AWS account, exchanges it for an in-memory client-credentials
token, makes `GET /smoke/synthetic-read`, and prints only JSON containing the
result, HTTP status, and elapsed milliseconds:

```bash
npm run platform:shell:controlled-smoke
```

That local form uses the selected target profile's named AWS CLI profile. The
temporary GitHub Actions scheduler uses an explicit, separate OIDC mode:

```bash
npm run platform:shell:controlled-smoke -- --aws-credential-source environment
```

The environment mode does not accept a profile name and clears any inherited
`AWS_PROFILE`; it relies only on the short-lived OIDC credentials configured by
the scheduler workflow. It is not a general credential-selection mechanism.

It never prints or writes the client secret, token, authorization header,
provider response, or application response body. It accepts no arbitrary URL,
route, HTTP method, scope, or expected status. It currently proves the
correctly scoped `200` path only. A real `403` proof needs a separately created
valid machine client without the smoke-read permission; an invalid token would
prove `401`, not authorization.

The live command reads AWS Secrets Manager and sends one public request, but
does not mutate AWS. Run it only with explicit current-chat approval for the
staging target; it is intentionally excluded from ordinary CI and test suites.
The distinct, source-prepared synthetic scheduler is the only planned automated
caller, once its separate IAM role and workflow have been reviewed and enabled.
It invokes this unchanged fixed command twice, 75 seconds apart. The first
request establishes an exported cumulative-counter baseline after a fresh task
start; the second advances that counter so the separate PromQL `increase()`
coverage verifier can prove freshness. This does not add a route, method,
scope, secret, free-form input, or provider permission.
