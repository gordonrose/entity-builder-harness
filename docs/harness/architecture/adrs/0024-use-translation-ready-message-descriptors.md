<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.adr.0024-use-translation-ready-message-descriptors
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  kind: adr
  purpose: Record the decision that core/platform/app contracts pass translation-ready meaning rather than final localized prose.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: harness.architecture.rules.layers.packages-core
    path: docs/harness/architecture/rules/layers/packages-core.yml
  - id: harness.architecture.source-material.packages-core-contract-surface-v1
    path: docs/harness/architecture/source-material/packages-core-contract-surface-v1.md
-->
# ADR 0024: Use Translation-Ready Message Descriptors

## Status

Accepted.

## Context

The first `packages/core` validation helper slice represented validation
failures with a direct `message` string. That was readable, but it made the
validation module look like the owner of final user-facing prose.

Kanbien needs internationalization and localization to be supported across
future core, platform, and app layers. Validation errors, policy denials, core
errors, notifications, reports, and API/display responses may eventually be
shown to people in different languages and regional formats.

If those contracts pass final prose too early, each module can accidentally
hardcode English copy, duplicate translation behavior, or pass already-formatted
dates, numbers, currencies, and regions before the presentation boundary knows
the user's locale.

## Decision

Core, platform, and app-facing contracts should pass stable meaning rather than
final localized prose when the value may be displayed to a person.

The shared core contract for this is `MessageDescriptor`, with:

- stable `code`
- fallback/debug `defaultMessage`
- optional `messageKey`
- optional primitive `params`

Validation issues, core errors, policy violations, and authorization denial
reasons should use this descriptor shape. Future user-facing contracts should
follow the same pattern unless they are explicitly operational-only.

The `i18n` module owns translation keys, message catalog contracts,
translators, fallbacks, and translation params. The `localization` module owns
locale-sensitive formatting for dates, times, numbers, currencies, and regional
display conventions.

Operational logs may keep direct operational messages when they are not
user-facing display contracts.

## Consequences

Validation and other core modules can describe what happened without owning the
final words shown to a user.

Future app and platform layers get a consistent way to pass displayable meaning
through APIs, notifications, reports, and UI boundaries.

The eventual `i18n` and `localization` modules can be added without rewriting
every earlier validation or error contract.

Developers and agents must avoid passing rich objects, dates, money values, or
provider-specific data as translation params. They should pass stable primitive
facts and let the localization boundary format locale-sensitive values.
