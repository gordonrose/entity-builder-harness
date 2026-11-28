<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.architecture.adr.0044-use-temporary-instances-of-production-deployments
version: 2
status: active
created_on: "2026-11-27"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.environment-lifecycle
disciplines: [architecture, security, sre]
kind: adr
purpose: Preserve production deployments while selecting bounded disposable instances through shared deployment and cleanup owners.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.plan.disposable-test-environments
  path: docs/04.deploy/plans/disposable-test-environments.md
-->
# ADR 0044: Use Temporary Instances of Production Deployments

## Status

Accepted design under the adopted disposable-environment goal. Implementation
and live qualification are incomplete; current evidence and remaining milestones
belong to the [implementation plan](../plans/disposable-test-environments.md).
This decision does not expand that goal's resource or execution authority.

## Context

The current AWS services are used for occasional functionality tests, not a
continuous production workload. Application data need not survive between those
tests. Stopping tasks alone leaves infrastructure charges, while hardcoding
test-only behavior into the product would undermine the software factory's
purpose: building production-capable services.

[ADR 0028](0028-use-client-environment-deployment-target-profiles.md) already
places environment choices in deployment profiles. Extend that boundary instead
of maintaining a second application or deployment engine.

## Decision

Keep persistent environments and their data-protection defaults unchanged.
A temporary session is a separately named instance of the selected service and
its dependencies, using the same source, images and infrastructure definitions.
Explicit lifecycle settings select a bounded lifetime and disposable application
data. Missing settings retain persistent behavior. The
[lifecycle standard](../../../.agentic/04.deploy/00-target-alignment/standards/require-environment-lifecycle-policy.md)
owns these rules; application code does not select them.

Capture the selected declarations once, bind their content identities, and derive
instance names and dependency order from that captured graph. Template-owned
controls describe stopped creation and later activation without altering
production defaults. Instance identity stays separate from source/package
identity. A valid source plan grants neither resource ownership nor permission.

Select declared disposable retention from the first temporary creation and keep
it during activation. This avoids a protected partial database requiring a later
protection-lowering update solely to remove it. Bind explicit preserve-on-failure
execution so partial creation can be reconciled without guessing a provider
default. Ordinary fresh functionality-test databases also select zero automated-
backup retention from creation, while production keeps its backup settings.
Use the same declared retention projection, not a second template. These sessions
do not prove backup recovery or replication functionality. Such tests require a
separately admitted retention-enabled lifecycle and cleanup proof. Original
zero-retention custody, native observations and a protected mutation boundary
must all agree before excluding replication over the session lifetime; a final
setting alone is insufficient. Manual snapshots and other backups still require
observation. Failed operation reconciliation is not successful output or physical
absence. The lifecycle standard owns the exact qualification requirements.

Use the existing reservation, CloudFormation submission, diagnostic and proof
owners. For independent workers, retain session admission and immutable operation
intents together in one conditionally updated, versioned S3 target record.
Protect history and conditional writes before use. Lost or conflicting writes
do not grant fresh submission; uncertain operations remain observation-only.
Completion requires physical absence of owned resources, and a later session
must bind the completed predecessor without erasing its evidence.

Keep the expiry mechanism outside disposable infrastructure. Select a versioned
Standard Step Functions workflow that waits for the absolute expiry and invokes
a fixed CodeBuild cleanup job using the same cleanup implementation as foreground
shutdown. Standard supports the required two-hour wait; Express has a five-minute
maximum. [AWS Wait semantics](https://docs.aws.amazon.com/step-functions/latest/dg/state-wait.html)

Bind qualified controller source and image identities, the exact job and checked
session input before admitting creation. CodeBuild permits per-run source,
buildspec, image and role overrides, so a fixed project name alone does not fix
the executed code. Restrict invocation and artifact access as part of the
control-plane qualification. [AWS StartBuild contract](https://docs.aws.amazon.com/codebuild/latest/APIReference/API_StartBuild.html)

Separate creation authority, its deadline and cleanup authority. Both the
submitting identity and the CloudFormation execution identity need effective
creation limits; cleanup authority must survive expiry. CloudFormation retains
an attached service role for later stack operations, so binding the role in the
approved request is part of the security boundary. Early shutdown also requires
reconciliation of accepted work: expiry or a sealed record cannot prove an
asynchronous operation has finished. [AWS service-role behavior](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)

## Alternatives

Scaling tasks to zero is useful during preparation but is not full cleanup.
Duplicated test templates or application switches would create competing
production behavior. Laptop-only cleanup cannot cover loss of that laptop.
Local reservation files remain appropriate for their current single-runner
consumers, but cannot alone coordinate an independent cloud cleanup worker.

## Consequences

Cold creation takes time and a fresh database needs fixture preparation. Reduced
test arrangements can prove only the capabilities they actually exercise.
Production data recovery and persistent service health remain unchanged.

Retain source, non-sensitive results and recovery evidence outside disposable
application storage. Controller storage and execution have residual costs;
removing resources is not a zero-cost promise or billing confirmation.
Existing always-on resources require their separately inventoried retirement,
after successful rehearsal. A temporary session cannot adopt them for deletion.
