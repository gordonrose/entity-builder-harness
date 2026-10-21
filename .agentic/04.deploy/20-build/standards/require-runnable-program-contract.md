<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.runnable-program-candidates
version: 1
status: draft
created_on: "2026-10-19"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
- agentic
- architecture
- security
- sre
kind: standard
purpose: Define the provider-neutral declaration and evidence boundary for runnable programs and their package candidates.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.workflow.runnable-program-candidates
  path: .agentic/04.deploy/20-build/workflows/prove-runnable-program-builds.md
- id: deploy.schema.runnable-program-contract.v1
  path: .agentic/04.deploy/20-build/schemas/runnable-program-contract.v1.schema.yml
-->
# Require a Runnable Program Contract

## Purpose

A runnable-program contract is the provider-neutral source declaration for a
program that may be assembled into a package candidate. It records the program
root, its approved dependency boundary, the image command that starts it, and
the minimum safe evidence required to qualify a candidate.

It is not a target definition, an image build recipe, a provider adapter, or
permission to publish or deploy a package.

## Required declaration

Every candidate contract declares:

1. one or more runnable-program records, each with a stable ID, entrypoint,
   approved dependencies, and observed dependencies;
2. one or more image contracts that bind exactly one declared program to an
   exec-form command containing that program's entrypoint;
3. one or more package candidates that select one declared image contract and
   require an immutable identity after publication; and
4. candidate-verification evidence field names drawn only from the safe
   allowlist in the schema.

Observed dependencies are report input, not approval. A dependency may appear
in an image only when the selected program declares it as approved. An
unapproved dependency is a fail-closed boundary violation.

## Safe evidence boundary

Candidate evidence may identify the source revision, immutable package digest,
program, candidate, check verdicts, check time, and receipt reference. It must
not contain secret values, credentials, tokens, headers, request bodies,
personal data, connection data, full locations, or raw provider responses.

The contract records field names, never the evidence values. Provider- or
target-specific collection happens outside this generic checker and supplies
only an approved safe receipt later in the delivery lifecycle.

## Failure rule

The report-only checker must fail closed for a missing program record, an
invalid image command, an observed dependency outside the approved boundary,
or an unsafe evidence field. Its machine-readable output may contain only the
stable contract ID when valid, validation scope, verdict, and stable diagnostic
codes. It must not echo unsafe input values.

## Change rule

Update the contract before a change adds, removes, or redirects a program
entrypoint, package dependency, image command, candidate identity rule, or
verification evidence field. Run the contract checker and the program's
dependency report before considering a package candidate qualified.
