<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.source-material.package-documentation-v1
version: 1
status: active
layer: 03.product
domain: architecture
disciplines:
- architecture
kind: source-material
purpose: Record the package documentation policy for navigable product code boundaries.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.architecture.rules.concerns.package-documentation
  path: docs/03.product/rules/concerns/package-documentation.yml
-->
# Package Documentation Policy v1

## Decision

Every independently consumable, runnable, deployed, or public package in the
product architecture should have a concise root `README.md`. Its README makes
the package's purpose, public boundary, important files, dependencies, and
verification route visible without requiring a reader to infer them from a
large parent catalogue or search the entire repository.

When a named module inside a package has several responsibility files whose
relationship is not obvious from the file names alone, that module should have
its own concise local `README.md`. The local README explains the files in that
module; it does not repeat the package README.

This is a navigation and ownership policy. It does not turn every directory
into a package, require prose beside every small source file, or replace code,
tests, public TypeScript contracts, or generated API documentation.

## Why the Policy Exists

The repository has a growing set of capability boundaries. A reader should be
able to answer, from the nearest README:

- What problem does this package solve?
- What must not live here?
- Which imports or consumers form its public boundary?
- What does each substantive responsibility file own?
- Where are its key tests or package-level checks?

A root catalogue such as `packages/core/README.md` remains useful, but it
should stay an abridged map of capabilities. It cannot be the detailed,
maintained explanation for every current and future module under `packages`,
`platform`, or `apps`.

## Scope

The policy applies to package boundaries under `packages/**`, `platform/**`,
and `apps/**`, and to product composition modules under `products/**` when
they expose a separately consumed or deployed surface.

A package boundary is identified by one or more of these facts:

- it has its own `package.json` or another explicit public entry point;
- other code imports it through an approved package or module path;
- it is started, deployed, or verified as a distinct runtime target; or
- it is an approved public integration boundary, such as an app mount module.

An arbitrary helper directory is not automatically a package boundary.

## Required Root README Content

The root README for an in-scope package should be short, current, and specific.
It should include:

1. **Purpose and non-goals** — the problem the package owns and nearby concerns
   it deliberately does not own.
2. **Public boundary** — supported imports, public entry points, or the package
   role when it is a runtime target rather than a library.
3. **Responsibility map** — a brief table or tree explaining each substantive
   source file or named module.
4. **Dependency boundary** — important allowed dependencies and forbidden
   dependencies, especially layer direction or provider restrictions.
5. **Verification** — the closest package check, test command, or evidence
   path that proves the stated boundary.

The README should distinguish current behaviour from intended future work. It
must not promise a provider integration, security control, runtime target, or
feature that does not exist.

## Local Module README Threshold

A local module README is useful when a module becomes a small subsystem, for
example `packages/core/src/security/` after it contains
`classification.ts`, `secrets.ts`, `hashing.ts`, and `policy.ts`.

The local README should say which concern each file owns, why the files are
separate, what `index.ts` deliberately exports, and which files must not absorb
one another's responsibility. It should link back to the package README rather
than repeating its public boundary and verification instructions.

Do not create a local README merely because a directory contains one obvious
`index.ts`, a generated file, a test fixture, or a private implementation
detail that is already clear from its name and nearby package map.

## Relationship to `index.ts`

An `index.ts` file remains a deliberate public barrel. It states which exports
are supported; it is not expected to explain the role of every internal file.

The README and file layout answer different questions:

| Reader question | Best source of truth |
|---|---|
| Which imports are public? | `index.ts` and package export metadata |
| Which responsibility does this file own? | The nearest README and the file name |
| Does the behaviour work? | Focused tests and package checks |
| Why does this boundary exist? | Package README and governing architecture rule |

## Change Discipline

When a contributor creates, splits, moves, removes, or materially changes a
substantive responsibility file, they must update the nearest relevant README
in the same change. A review should reject a file-map entry that describes a
different path, stale responsibility, or unsupported public import.

New packages and newly split multi-file modules must satisfy this policy when
they are introduced. Existing packages should be documented as they are
materially reorganised or touched for a capability change; the policy does not
justify a broad, unreviewed documentation rewrite.

## Security and Operational Constraints

Documentation is part of the attack surface and operating model. Package and
module READMEs must not contain secrets, credentials, tokens, customer or
tenant data, private endpoints, security bypasses, or copyable production
access instructions.

They should describe security boundaries accurately: for example, a generic
platform package may describe provider-neutral mechanisms, while a provider
adapter README may document the translation boundary without exposing provider
configuration values.

Package READMEs should be compact. They should link to deeper source material,
runbooks, or plans rather than duplicating long procedures that would drift.

## Worked Example: Core Security

`packages/core/README.md` should say that core provides provider-neutral,
stable concepts and link to the `security` capability.

`packages/core/src/security/README.md`, when added, should explain:

| File | Responsibility |
|---|---|
| `classification.ts` | Data sensitivity and sensitive-value kinds. |
| `secrets.ts` | Safe secret-string handling. |
| `hashing.ts` | Hash shapes and the provider-neutral hasher port. |
| `policy.ts` | Policy decisions, violations, and evaluator contracts. |
| `index.ts` | Deliberate public exports for the security module. |

It should not restate every core module, contain a tutorial on cryptography, or
claim that core implements a cloud key-management provider.

## Verification Expectations

The policy is initially enforced through review and rulebook retrieval, not a
blanket repository-wide failure for legacy packages. Later, once package
boundaries and documentation coverage are stable, a deterministic checker may
verify required root README presence and required sections for new packages.

That future checker must not infer package ownership from arbitrary directories
or force boilerplate README files into one-file modules.
