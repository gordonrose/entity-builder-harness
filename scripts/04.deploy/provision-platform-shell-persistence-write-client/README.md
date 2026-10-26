<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.script.provision-platform-shell-persistence-write-client.readme
version: 1
status: active
created_on: "2026-09-24"
updated_on: "2026-10-26"
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded Cognito write-client provisioner for the Kanbien staging persistence smoke proof.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.provision-platform-shell-persistence-write-client
  path: scripts/04.deploy/provision-platform-shell-persistence-write-client/script.sh
-->
# Provision Platform-Shell Persistence Write Client

This command creates one separate confidential Cognito machine client for the
bounded persistence acceptance proof. It is not a general client, scope, or
secret administration tool.

It first requires the exact read-only `platform-shell` resource-server state,
then adds only `smoke.write`, creates only
`platform-shell-staging-persistence-write-client`, and stores its generated
secret only in `kanbien/staging/platform-shell/cognito-persistence-write-client`.
The new client can request only `platform-shell/smoke.write`; the existing
read/synthetic client remains read-only.

The client secret is held only in process memory and a mode-`0600` temporary
file while Secrets Manager receives it. It is never printed or committed. The
safe result includes only the generated client ID and secret ARN.

If provisioning fails, the command removes only resources it created and
restores the resource server to its exact prior read-only scope. It does not
modify the server allowlist; after a successful live provision, that generated
non-secret client ID requires a separately reviewed target-configuration
revision before a write token is trusted by the service.

Validate locally without AWS access:

```bash
npm run platform:shell:persistence-write-client:provision -- --validate
```

Live execution is an AWS mutation and requires current-chat approval:

```bash
npm run platform:shell:persistence-write-client:provision -- --execute
```

`--reconcile --json` is observation-only: it lists the declared resource server,
client and secret metadata without retrieving secret values. It distinguishes
absent, partial, present-but-unqualified and uncertain outcomes. Secret deletion
pending, duplicate identities, denied reads and paginated/incomplete results
cannot become completed cleanup or qualification. Failed compensation preserves
the original safe failure and reports `compensation-unproven-reconcile-required`.
The existing invocation remains blocked until the reviewed partial state is
resolved; reconciliation never repeats provisioning automatically.
