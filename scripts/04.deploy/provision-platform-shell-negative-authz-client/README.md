<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.provision-platform-shell-negative-authz-client.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded staging Cognito negative-authorization test-client provisioner.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.provision-platform-shell-negative-authz-client
  path: scripts/04.deploy/provision-platform-shell-negative-authz-client/script.sh
-->
# Provision Platform-Shell Negative Authorization Client

This command creates the one Kanbien staging Cognito machine client used to
prove the difference between a valid identity with insufficient permission
(`403`) and an invalid identity (`401`). It is not a generic Cognito client,
scope, or secret administration tool.

Before its live mode it verifies the selected account and requires that the
exactly named resource server, client, and secret are all absent. It then
creates only:

- `platform-shell-authz-probe`, with one deliberately unmapped `deny` scope;
- `platform-shell-staging-negative-authz-client`, with client-credentials only
  and only that scope; and
- `kanbien/staging/platform-shell/cognito-negative-authz-client`, containing
  the generated secret.

The generated secret stays in process memory until it is written through a
mode-`0600` temporary file to Secrets Manager. It is never printed, written to
source control, placed in ECS, or returned by this command. The safe result
contains only the new client ID and secret ARN. If a later operation fails, the
command rolls back only resources it created during the current invocation.

Validate policy without AWS access:

```bash
npm run platform:shell:negative-authz-client:provision -- --validate
```

Live execution is an AWS mutation and requires current-chat approval:

```bash
npm run platform:shell:negative-authz-client:provision
```

Provisioning alone does not make the client trusted by the service. A reviewed
service deployment must add its exact, non-secret client ID to
`PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS` before the status-only `403`
smoke can run.
