<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.source-material.packages-core-contract-surface-v1
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  kind: source-material
  purpose: Record the approved initial packages/core contract surface for RAG/rulebook projection.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: harness.architecture.rules.layers.packages-core
    path: docs/harness/architecture/rules/layers/packages-core.yml
-->
# packages/core Contract Surface v1

## Decision

The initial `packages/core` slice may establish the package boundary and a
small set of contract-shaped capability modules before product apps and
platform adapters exist.

This is a bootstrap exception to the normal "extract after observed reuse"
rule. The exception is narrow: the slice may define stable names, types, ports,
and small pure primitives that future apps and platform packages will consume,
but it may not define provider implementations, app workflows, infrastructure,
runtime hosts, or cloud SDK integrations.

## Approved Capability Surface

The initial package surface may include these contract modules:

- `shared`: branded identifiers, result/error shapes, translation-ready message descriptors, request context, clocks.
- `config`: config source and schema contracts.
- `logging`: logger, log record, and redaction contracts.
- `validation`: validation issue and validator contracts.
- `authn`: principal and authenticator contracts.
- `authz`: permission and authorizer contracts.
- `tenancy`: tenant identifiers and tenant-resolution contracts.
- `persistence`: repository, unit-of-work, transaction, and pagination contracts.
- `security`: defensive policy and secret/hash contracts.
- `audit`: audit event and recorder contracts.
- `events`: event envelope and event bus contracts.

## Message, i18n, and Localization Boundary

Core, platform, and app-facing contracts should pass stable meaning rather than
final localized prose. User-facing or consumer-facing explanations should carry
machine-stable codes, optional translation keys, fallback/default messages, and
primitive interpolation params.

Validation issues, core errors, policy denials, notification descriptions,
report labels, and API/display responses should use translation-ready
descriptors when they may be shown to people. The fallback/default message is
for debugging, logs, tests, and untranslated contexts; it is not the canonical
localized copy.

The `i18n` contract layer owns translation keys, message catalogs, translators,
fallback behavior, and translation params. The `localization` contract layer
owns locale-sensitive formatting for dates, times, numbers, currency, and
regional display conventions. Validation and other core capability modules
should emit facts that those layers can translate or format later.

Operational logs may keep direct operational messages when they are not
user-facing display contracts.

## Placement Rules

Core owns the shape of stable cross-cutting contracts. Platform owns concrete
runtime adapters. Apps own product-specific workflows. Infra owns deployment
resources and cloud topology.

Provider adapters for AWS, databases, queues, object storage, observability,
or authentication systems must not live in `packages/core`. They belong under
platform or infra depending on whether they are runtime code or deployment
resources.

## RAG Implication

When agents add or change `packages/core` contracts, the RAG/rulebook layer must
be able to answer how the contracts should be used and where implementation
code belongs. Code changes to `packages/core` therefore require a RAG knowledge
disposition at commit time: covered by source/rules/selector proof, no-impact
with a reason, or deferred with an explicit corpus gap.
