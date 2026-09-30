<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.iaas-release-control-mvp-control-policy-proposal
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record approved operating-policy inputs for selected shared-control source implementation while retaining separate external execution approval.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-release-control-mvp
  path: docs/04.deploy/plans/iaas-release-control-mvp.md
-->

# M4 operating policy — approved for source implementation

The missing capability is a shared, durable record of who may run an operation,
what was attempted, and what must be recovered after an interruption. Extend the
existing realization gate and deployment scripts with one protected GitHub
executor and a small AWS store. No permanent controller service is proposed.

Existing policy already supplies the target/account/region, Gordon Rose as owner,
official-main images, protected staging approval, the USD 25 monthly service
budget and the existing task timeouts. Those decisions remain unchanged.

The user accepted these operating choices for source implementation on
2026-09-30. Resource creation, hosted activation and per-operation execution
remain separately unapproved. The historical proposal filename is retained
so the review and approval link stays valid.

## Accepted operating choices

| Choice | Accepted source policy |
| --- | --- |
| Normal executor | One GitHub path on protected main with staging approval. WSL compiles, plans and inspects. Existing mutation wrappers join the same boundary. Emergency administrator intervention freezes ordinary releases until reconciled. |
| Records and protection | One dedicated DynamoDB table plus one private versioned S3 bucket in eu-west-1. Safe operational metadata only; no secrets, raw logs/provider bodies, database or queue contents. Service-managed encryption and TLS. |
| Retention | Keep closed records at least 90 days; retain unresolved operations until resolved and then at least 90 days. No automatic deletion or TTL in the MVP. Actual retention can exceed 90 days; review storage growth monthly. |
| Recovery | Table recovery history of 35 days. Target safe recovery within four hours and a catastrophic recovery point within five minutes. A controller crash must lose no acknowledged intent. These are acceptance objectives requiring a rehearsal, not guarantees. Restoring a store does not authorize replay. |
| Operation authority | Approval binds one exact source/image/target/operation and expires after two hours. At most 90 minutes execution plus 30 minutes recovery within that absolute deadline. Existing shorter task timeouts remain. Unknown outcomes consume the single allowed effect attempt. |
| Shared lease | 60-second lease, renew every 20 seconds; no new effect call with less than 35 seconds remaining. Verify at most five seconds clock uncertainty. An expired lease permits reconciliation only while earlier credentials or effects remain unresolved. |
| Spending limits | Up to USD 5/month for these controls within the existing USD 25 total; up to USD 2 for initial isolated qualification. These are approved ceilings, not cost estimates. Regional prices and current budget headroom must be checked before creation. |

The proposed first AWS change adds exactly four resources in a dedicated stack:
a DynamoDB table, evidence bucket, bucket policy and separate controller IAM role.
Both stores retain data on stack deletion/replacement. The initial role permits
isolated store conformance and passive inspection only; it has no deployment,
secret-read or database-mutation permission. Existing publisher and reconciler
roles are not expanded.

## Separate approval boundaries

Accepting these operating choices permits source implementation against their
policy digest. It does not authorize creating resources, changing IAM, publishing
code, running a hosted workflow or executing PostgreSQL Stage 6.

Before requesting AWS execution, finish the versioned contracts/backend/controller
fixtures, exact CloudFormation template and IAM trust/access review, current
cost/headroom assessment and expected four-Add change-set scope. The one-time
bootstrap proposal expires after 30 minutes or consumption. Later task/effect
permissions require their own exact scope and approval. A successful table
creation alone does not complete M4.

The table fences journal writes; it cannot cancel an AWS request or a paused
controller with valid credentials. Every effect must have a durable reservation
before dispatch. A successor cannot begin conflicting work until the old
credential lifetime and in-flight effects have been excluded or reconciled.
No automatic token refresh extends the approved operation lifetime.

## Next source delivery and acceptance

Retain the existing local v1 records and tests. Add separately versioned selected
operation, journal, evidence and authority records and an AWS backend under
`scripts/04.deploy/release-control/adapters/aws/`. Reuse shared transition and
action-reservation rules; connect the existing candidate/relational wrappers and
one thin hosted caller to the same gate. No direct execution fallback is allowed
when the shared control boundary is unavailable.

The next complete source unit must demonstrate one writer across competing clients,
stale owner/fence rejection, intent before effects, lost-response quarantine,
source/image/authority expiry rejection, immutable evidence readback, owned
interruption cleanup, restored-store generation invalidation and legacy caller
refusal. Local conformance cannot establish live AWS durability or authority.
All 17 gates remain; scoped staging rehearsal is distinct from complete programme
qualification.

Official semantics reviewed for the proposal: [DynamoDB transactions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html),
[transaction IAM actions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis-iam.html),
[S3 conditional-write enforcement](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes-enforce.html),
[DynamoDB recovery](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html)
and [OIDC condition keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html).
Exact trust claims, immutable repository identifiers, current competing callers,
regional costs and the eventual template remain review obligations.
