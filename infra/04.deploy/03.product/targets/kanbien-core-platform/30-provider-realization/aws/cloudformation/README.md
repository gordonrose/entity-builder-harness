<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: infra.04-deploy.03-product.targets.kanbien-core-platform.cloudformation.readme
  version: 4
  status: active
  created_on: "2026-10-20"
  updated_on: "2026-11-27"
  layer: 04.deploy
  domain: deployment.bootstrap-runtime
  disciplines:
  - architecture
  - security
  - sre
  kind: infrastructure-guide
  purpose: Explain the core target templates, production-preserving instance names and still-pending temporary-environment execution boundary.
  portability:
    class: internal
    targets: []
  used_by:
  - id: aws.plan.kanbien-core-platform-e1-foundation-change-set
    path: docs/aws/kanbien-core-platform-e1-foundation-change-set.md
-->
# Core Platform CloudFormation

These files declare AWS resources; editing them does not change AWS. Each
deployment still requires its reviewed source, package proof and approved
change set. Image identities remain immutable digests, not tags.

The original bootstrap sequence used `tag-bootstrap.yml` to create an empty
tagged image repository, `foundation.yml` for the private foundation, and
`bootstrap-runtime.yml` for the first server and dormant verifier. Current
persistence and entity functionality is declared separately in
[`core-server-persistence.yml`](core-server-persistence.yml) and
[`entity-smoke.yml`](entity-smoke.yml).

## One set of definitions, separate instance names

[`foundation.yml`](foundation.yml), `core-server-persistence.yml` and
`entity-smoke.yml` share `ResourceNamePrefix`. Its default is
`kanbien-core-platform`; the default resource definitions, protection policies,
health checks and service counts are unchanged. A prefix is 1–21 characters,
starts with a lowercase letter, and contains lowercase letters, digits and
single internal hyphens. The limit keeps the longest existing IAM role name
within its allowed length. The private namespace is `<prefix>.internal`.

Names, ownership tags, private service addresses and monitoring labels derive
from the same prefix. Published images and application database/schema/user
names do not become test-specific. Existing public controllers still require
the default target; the parameter alone does not permit a new deployment or
authorize deletion. Existing entity stack observations missing the newly
required parameter are rejected, not silently treated as migrated.

The existing declaration fixture checks the full default resource/output/
condition definitions against pre-change fingerprints, checks unchanged
parameter defaults, and checks two distinct prefixes. These are local source
checks, not evidence that two environments have been deployed in AWS.

## Temporary environments are not operational yet

Each of the three templates explicitly declares `Metadata.CreationControls`.
The preparation reader checks those bindings against actual parameters,
conditions, resources and outputs; it does not select resources by service name.
Production keeps its current defaults. A new temporary foundation omits its
image-publication role; temporary persistence omits the two unused legacy
password secrets and starts both service counts at zero while the database is
prepared. The administrator secret, RDS deletion protection and snapshot policies
remain. Desired-count rows also declare a positive `active` value from the
parameter's allowed values. The session planner uses it for a separate activation
projection while keeping optional roles and secrets omitted. The entity service
declares active count one without changing its production default of zero.
Activation still requires observed creation/database readiness and a checked
operation; discard has its separate cleanup gate. No live command is connected
by these template fields alone.

Persistence also declares `Metadata.DiscardControls`, naming the database and
the expected original values of four supported settings. The session reader
copies the stopped temporary projection and changes its deletion/replacement
policies to `Delete`, deletion protection to `false`, and automated-backup
deletion to `true`. Production, creation and activation keep their protections;
the seven-day backup retention setting is unchanged. Unlisted retaining
resources, unsupported resource types and mismatched source expectations reject
the discard plan. This only prepares a sealed session for later owned deletion;
manual snapshots and other leftovers still need physical observation.

These source defaults do not migrate an existing deployed template. Fixed UPDATE
routes reject old templates missing the new parameters; their compatibility
allowlists have not been widened. The persistence YAML also remains close to the
existing inline-size limit; adding source must retain that check, not bypass it.

[`private-network.yml`](private-network.yml) is a local draft for a separately
owned VPC, two private subnets and their S3 gateway endpoint. It has no public
gateway or NAT gateway. Its input checks do not yet prove live zone availability
or that chosen subnet ranges fit without overlap; those belong to the future
creation preflight. It is not wired to an approved create/cleanup operation.
The source profile's optional foundation prerequisite now includes it in the
temporary instance plan, before foundation. Its declared outputs supply the
foundation's VPC, CIDR and subnet parameters. The same source-capture/projection
loop reads it; no second renderer or production network replacement is introduced.
Execution still needs concrete reviewed ranges/zones and positive owned-output
observations before the foundation can be created.

Independent expiry, session ownership, full cleanup and live create/remove/
recreate proof remain pending in the
[disposable-environment plan](../../../../../../../../docs/04.deploy/plans/disposable-test-environments.md).
Do not apply these files manually to bypass that work. The current always-on
test resources have not been removed, so this source work has not yet reduced
their running costs.
