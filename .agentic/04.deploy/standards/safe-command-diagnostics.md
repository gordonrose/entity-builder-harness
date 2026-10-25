<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.safe-command-diagnostics
version: 2
status: active
created_on: "2026-10-20"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.diagnostics
disciplines:
- agentic
- security
- sre
kind: standard
purpose: Preserve bounded, safe diagnostic evidence when deployment scripts invoke child commands.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.shared.safe-command-diagnostics
  path: scripts/04.deploy/shared/safe-command-diagnostics.sh
-->
# Safe Command Diagnostics

This is the deployment-script application of the shared
`require-safe-diagnostic-record.md` standard. It governs child-command output;
it does not replace the scope-level persistence diagnostic mapping or runtime
adapter mapping required for a dependency-bearing workload.

A lifecycle script may keep successful child-command output quiet. It must not
turn a child failure into an unexplained exit code.

On failure, a wrapper emits a stable diagnostic code, lifecycle stage, safe
summary, and bounded next check. A consequential deployment operation also
emits a `deploy/deployment-operation-diagnostic/v1` report with its operation
identity, known/unknown outcome, retained-evidence reference, and next
permitted decision.

The wrapper must not print or commit an arbitrary child-output tail. A redactor
cannot establish that a provider response is safe. It may preserve only facts
in the report schema's explicit allowlist. Complete unredacted output may be
held only as an access-controlled CI artifact when the target policy explicitly
permits that evidence class; the safe report records the opaque artifact
reference, never its contents.

## Rules

- Do not use `>/dev/null` for a consequential build, run, scan, or provider
  command unless its failure path captures and safely reports the output.
- Treat child and provider output as unsafe by default. Classify it into a
  stable code and preserve only explicitly allowed facts.
- Keep any permitted restricted artifact outside repository evidence and bind
  it to the operation with an opaque evidence reference.
- Preserve the child exit status; a diagnostic wrapper must not convert failure
  into success.
- If report collection fails, emit a distinct safe collection-failure finding
  while preserving the original child status and original failure code.
- Test one controlled child failure for every reusable wrapper.
- When a child command can create, alter, rotate, or revoke credentials, apply
  the shared downstream-log rule: review and test the database/provider/task
  error surfaces as well as this wrapper's own output. Passwords, SCRAM
  verifiers, IAM authentication tokens, and connection strings are all
  sensitive and must not be retained in the command text, safe report, or
  ordinary diagnostic output.
