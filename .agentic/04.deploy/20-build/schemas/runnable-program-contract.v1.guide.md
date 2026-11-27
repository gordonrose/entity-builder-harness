<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.runnable-program-contract.v1.guide
version: 3
status: draft
created_on: "2026-10-19"
updated_on: "2026-11-27"
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
  path: .agentic/04.deploy/20-build/schemas/runnable-program-contract.v1.schema.yml
-->
# Runnable Program Contract v1 Guide

Start with the program that will actually start in the package. Give it one
stable ID and a relative entrypoint. The approved dependencies are the reviewed
boundary; the observed dependencies are supplied by a deterministic report.
The checker rejects a difference rather than guessing whether it is harmless.

An image contract then selects that program and gives a process image one exec-form
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

For a process, `runtime_executable` must name a supported interpreter; its image
command begins with that interpreter and the exact entrypoint. A shell, echo,
or an interpreter evaluation flag mentioning the entrypoint is not execution.

A managed function uses `execution_kind: managed-handler`, `runtime_executable:
node`, a compiled `.js`, `.cjs` or `.mjs` entrypoint and one `handler_export`
identifier. Its image contract uses `command_mode: handler`; for
`artifacts/worker.js` and export `handler`, the exact command is
`[artifacts/worker.handler]`. The provider owns and proves the managed runtime
bootstrap separately. This alternative does not turn process commands into
handlers or permit shell syntax, extra tokens or undeclared exports.

## Declaration-derived workspace builds

For a Node workspace-TypeScript program, add `build.kind: workspace-typescript`
and `build.typescript_project` to the existing program record. In the same
contract, `dependency_bindings` connects its existing logical approval IDs to
either one `workspace_package` name or a list of `external_packages`. For example,
`core: {workspace_package: '@kanbien/core'}` binds the existing `core` approval;
it does not copy Core's directory, exports or dependencies.

The [build-input reader](../../../../scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs)
resolves the selected approved workspace packages from root workspaces and their
package manifests. Their runtime dependency closure must stay inside those
approvals, and external roots must be allowed by the selected external bindings.
Discovery cannot approve another package. Test-only development dependencies are
not added to a program image. An absent binding, unresolved workspace package or
unapproved transitive dependency fails before compilation or packaging.

This build reader does not replace the existing whole-contract checker, observed
source-boundary proof, image qualification or publication/acceptance checks.
Non-workspace and non-TypeScript programs retain their existing declarations.
The current resolver explicitly rejects unsupported conditional/wildcard/type-only
exports and workspace optional/peer dependencies instead of guessing semantics;
the installed external-package resolver still owns its supported optional/peer
closure. Extend and prove the owning mechanism before adopting such a declaration.
