<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.review.release-control.dependency-effects.2026-09-29
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record exact packaged-command verification against a disposable dependency and its limits.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Independent dependency effects — acceptance record

Status: accepted source delivery unit. Focused tests, fresh public-wrapper
execution and final clean verification passed: 1,455 tests across 38 suites,
plus 51 metadata headers. See [verification summary](verification-summary.json).

This delivery unit extends the existing Operational Realization Gate and image
smoke wrapper. It qualifies the actual packaged bootstrap and migration commands
against a digest-locked disposable PostgreSQL 17.11 engine. Independent database
queries verify effects; workload success output alone cannot satisfy them.

Acceptance requires a freshly built final product image, exact payload/command
bindings, full TLS verification with a separately bound qualification CA, no
published dependency port, bounded execution, independent privilege/schema and
migration-history checks, repeated-operation behavior, negative authentication,
TLS and altered-history cases, and verified owned-resource cleanup. The ordinary
RDS certificate path remains the production default and must retain coverage.

Local observations cannot qualify RDS/ECS/IAM, grant release authority, close the
whole-estate source gate, or satisfy relay/worker/restore obligations. A local
configuration binding must be explicit in the receipt and cannot be relabelled
as the production configuration. The effect receipt lists the remaining
relational commands; the full upstream image receipt also retains all other
task/sidecar obligations. No target profile is promoted by this local result.
Raw generated credentials and dependency logs must not enter retained source
evidence.

The [effect receipt](effect-result.json) retains all nine actual command cases
and ten independent assertions, including four deliberately missing privileges,
runtime password authentication over verified TLS, denied runtime DDL, successful
transactional DML, stable repeated operations and verified owned cleanup. The
[complete build receipt](build-result.json) retains the upstream compiler,
payload, image, server health and task-obligation evidence. All 3,902 packaged
files matched. Four command cases succeeded and five intentionally failed;
expected failures cannot be relabelled successful state changes.

Focused dependency verification passed 125 tests, and five additional production
target boundary cases prove the default pinned RDS certificate path remains
required and local qualification fields are forbidden in staging descriptors.
The public command completed with exit 0 and empty stderr after source freeze.

The initial real execution exposed the official dependency initializer's socket
requirement. The owned temporary socket paths and early startup classification
were repaired before the successful rerun. A subsequent refresh returned a
generic failure; the wrapper now preserves only explicit reviewed upstream error
codes, while unknown, malformed and private exception values remain redacted.
The precise cause of that earlier generic failure was not retained. Heavy final
build and source verification run sequentially without extending their deadlines.

The recorded repository HEAD is the pre-checkpoint label. Actual source bytes
are separately digest-bound and were independently matched after execution. A
published release still needs a fresh build bound to its reviewed clean commit.

This receipt is unsigned local evidence. Docker/host versions are observed;
remote service identity, IAM, injected provider secrets and RDS/ECS behavior are
still unqualified. Next: durable operation records and interruption recovery,
alongside remaining caller/export coverage and authenticated producer integration.

Accepted local effect identity: `sha256:09c3cfea610c2bf600ae3b2d33fbaeca64f54898fabf1bb0c6ecfdf81b3e3cf2`.

Exact tested image identity: `sha256:03432806c5bf2b4e39ea43a52b8722346b1d4e223eb9b9c2fc021c8d785ad512`.
