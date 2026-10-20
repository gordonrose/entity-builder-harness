<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.runnable-program-candidates
version: 1
status: draft
created_on: "2026-10-19"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
- agentic
- architecture
- security
- sre
kind: workflow
purpose: Govern a report-only review of runnable-program and package-candidate declarations before package construction.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.standards.runnable-program-candidates
  path: .agentic/04.deploy/standards/runnable-program-candidates.md
- id: deploy.command.runnable-program-contract
  path: scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh
-->
# Runnable Program and Package Candidates

## Use when

Use this workflow when work adds or changes a runnable program, its dependency
boundary, its package start command, or the safe evidence required to qualify
the resulting package candidate.

## Procedure

1. Select the smallest runnable program affected by the change.
2. Create or update its runnable-program contract from the provider-neutral
   template.
3. Produce an observed dependency report from the program root. Do not turn an
   observed dependency into an approved dependency without an explicit review.
4. Bind the program to an exec-form image command. The command must name the
   declared entrypoint and must not invoke a shell or interpolate input.
5. Declare the candidate's immutable identity rule and only the safe evidence
   field names needed for qualification.
6. Run the report-only contract checker. A failed diagnostic blocks package
   construction until the declaration or selected boundary is corrected.
7. Pass the valid contract and observed dependency report to the package-phase
   image build and payload checks.

## Stop conditions

Stop before packaging when a program record is absent, a command is not an
exec-form command for the selected entrypoint, an observed dependency is not
approved, or requested evidence exceeds the safe allowlist.

This workflow performs no image build, network access, publication, target
selection, provider read, or target mutation.

## Output

Produce a report-only JSON result containing the contract ID, validation scope,
verdict, and stable diagnostic codes. Do not include candidate evidence values
in the report.
