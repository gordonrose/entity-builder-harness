<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.provider-async-conditions
version: 2
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.target-alignment
disciplines:
- agentic
- security
- sre
kind: standard
purpose: Model provider-controlled propagation and asynchronous conditions without treating a request as proof of readiness.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: infra.04-deploy.03-product.targets.kanbien-core-platform.foundation.cost-control
  path: infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/cost-control.yml
-->
# Provider Asynchronous Conditions

Provider-controlled states such as tag discovery, cost-allocation activation,
image scanning, DNS propagation, and stack completion are not complete when a
request has been accepted. They require separately fresh evidence.

Each condition must declare its owner, required evidence, status, next safe
recheck, expiry, and whether an explicitly approved temporary waiver exists.
Allowed statuses are `not-requested`, `requested`, `waiting-on-provider`,
`verified`, `expired`, and `waived-by-approved-exception`.

Condition evidence is validated by the provider-neutral
`validate-provider-condition-evidence` command before any workflow treats a
condition as verified or waived. A provider adapter may collect the fact, but
the validator receives only the safe evidence record.

A waiver is narrow: it names the waived condition, authority, reason, expiry,
compensating controls, and required follow-up. It does not waive unrelated
security, access, cost, or target-alignment conditions.

## Controller Outcomes and Continuation

The condition statuses above describe provider readiness evidence. A command's
observation outcome is separate: `pending` means a known operation or its proof
is still progressing; `failed` means a terminal failure was positively observed;
`uncertain` means the operation's identity, state, or result cannot be proved.
`blocked` means a precondition or permitted boundary rejects the action. None
of these outcomes grants permission to repeat a mutation or counts as success.

Before submitting an asynchronous operation, retain a safe operation identity.
Where the provider supports request idempotency, bind it to that same identity.
An interrupted observer must offer an observation-only continuation using the
existing operation; it must not submit replacement work when observation finds
nothing. Provider idempotency and discovery windows are bounded, so their expiry
never permits replay. Keep completed-task evidence and request new authority for
any fresh operation after an unresolved outcome. Report pending proof separately
from failed work, including when successful work's logs have not arrived yet.

The provider workflow owns concrete identifiers, reconciliation commands and
provider-specific state mappings. A wrapper must preserve the safe child
operation receipt and outcome so nested execution does not lose continuation.
