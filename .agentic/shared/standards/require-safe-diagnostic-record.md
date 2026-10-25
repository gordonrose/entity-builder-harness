<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.standards.safe-diagnostic-record
version: 1
status: active
created_on: "2026-10-23"
updated_on: "2026-10-25"
layer: 06.shared
domain: diagnostics
disciplines: [security, sre, agentic]
kind: standard
purpose: Require safe, bounded, actionable diagnostic records across product and deployment layers.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.standard.persistence-diagnostic-mapping
  path: .agentic/04.deploy/60-run/standards/require-persistence-diagnostic-mapping.md
-->
# Require Safe Diagnostic Records

A diagnostic records an observed failure class and the next governed check. It
does not expose raw implementation detail, infer an unproved cause, or grant
permission for an unsafe repair.

Every diagnostic record has a stable code, logical dependency and scope where
applicable, lifecycle stage, workload identity where applicable, safe summary,
retryability, and bounded next check. Stable codes are controlled vocabulary,
not ad-hoc message text. An unknown observation uses a named unclassified code
with stop-and-escalate behaviour; it never becomes permission to guess, expose
raw output, replay uncertain work, or mutate a target.

A deployment-operation diagnostic additionally records the named operation,
whether its effect is known, unknown, pending, rejected, or failed, and a
reference to retained evidence. It names the next permitted observation or
retry decision. A timeout, interrupted response, or failed diagnosis remains
an *unknown operation outcome* until the governed reconciliation route proves
otherwise; it is never authority to resubmit a mutation.

Repository artifacts, reports, logs, and diagnostics must not contain secret
or credential values, tokens, connection strings, hostnames or internal
addresses, certificate bodies, SQL values, raw provider responses, or personal
data. A provider reference is not a secret value, but it belongs in the
provider binding rather than a portable diagnostic record. Pattern redaction
is a useful boundary check; it is not a general secret or PII detector. Do not
retain or print arbitrary provider response bodies merely because a pattern
redactor removed one apparent credential. Useful provider facts are copied
only into a field explicitly allowed by the owning report schema, such as a
resource logical identifier, resource type, provider status, or safe property
path. If no safe fact is available, report that fact as unavailable rather than
guessing from raw output.

The product/core layer owns bounded provider-neutral diagnostic primitives.
Platform capabilities own provider-neutral meaning and safe workload effects.
Provider adapters translate provider facts privately into those meanings.
Deploy declarations state the lifecycle consequence and proof requirement.
Deployment scripts preserve child exit status and emit only safe bounded
diagnostics. No one layer substitutes for another's provider observation or
live proof.
