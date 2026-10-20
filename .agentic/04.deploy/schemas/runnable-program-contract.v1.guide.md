<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.runnable-program-contract.v1.guide
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
kind: guide
purpose: Explain how to author and interpret a provider-neutral runnable-program contract.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.schema.runnable-program-contract.v1
  path: .agentic/04.deploy/schemas/runnable-program-contract.v1.schema.yml
-->
# Runnable Program Contract v1 Guide

Start with the program that will actually start in the package. Give it one
stable ID and a relative entrypoint. The approved dependencies are the reviewed
boundary; the observed dependencies are supplied by a deterministic report.
The checker rejects a difference rather than guessing whether it is harmless.

An image contract then selects that program and gives the image one exec-form
start command. An exec-form command is a list of literal tokens, such as a
runtime executable and an entrypoint. It avoids a shell that could interpret
variables, operators, or unreviewed input.

A package candidate selects that image contract. Before publication, its
identity is `runtime-bound-sha256`: later package evidence must bind it to one
content digest. The contract deliberately does not contain a registry name,
location, target, provider value, or digest that does not yet exist.

Candidate verification lists only safe receipt field names. The later receipt
may prove which source revision, package digest, and release identity were
checked, but this contract never stores their values or any sensitive material.
