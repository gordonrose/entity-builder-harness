<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.safe-command-diagnostics
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-20"
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

A lifecycle script may keep successful child-command output quiet. It must not
turn a child failure into an unexplained exit code.

On failure, a wrapper emits a stable diagnostic code, lifecycle stage, safe
summary, bounded redacted tail of the child output, and bounded next check.
The complete unredacted output is never printed or committed. It may be held
only as an access-controlled CI artifact when the target policy explicitly
permits that evidence class.

## Rules

- Do not use `>/dev/null` for a consequential build, run, scan, or provider
  command unless its failure path captures and safely reports the output.
- Redact configured secret values and common credential-bearing assignments
  before printing output.
- Limit printed output by line count and byte size.
- Preserve the child exit status; a diagnostic wrapper must not convert failure
  into success.
- Test one controlled child failure for every reusable wrapper.
