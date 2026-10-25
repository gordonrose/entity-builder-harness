<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.change-impact.v1.guide
version: 1
status: active
created_on: '2026-10-24'
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.declaration-coverage
disciplines:
- agentic
- security
- sre
kind: documentation
purpose: Explain the additive bridge between existing scope contracts and declaration
  requirement chains.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: repo.command.check-selection
  path: scripts/repo/check-selection/script.sh
-->
# Change Impact Declaration

Add `change_impact` to an existing `deploy/target-scope-contract/v1` declaration.
This implements the requirement chain from the [Declaration Coverage Standard](../standards/declaration-coverage.md), using the actual indexed scope format.
It does not create a competing scope inventory or replace workload contracts.

`inputs` contains exact repository-relative files or directories. A directory
matches itself and descendants at a slash boundary. Include supported source,
configuration, package and provider definition inputs. Normal TypeScript source
need not acquire harness headers: workspace `package.json` dependencies supply
consumer edges, while explicit input mappings cover entrypoints and compiler
path aliases. The selector reports unmatched changes as gaps. It does not claim
to infer every arbitrary dynamic import or external consumer.

Each requirement uses the existing chain fields `id`, `purpose`, `owner`,
`required_by`, `declarations` and `expectation`. Each proof list names stable
IDs from the repository check catalog. `local_proofs` must retain `scope-inventory` and `runnable-program`; an empty
package, target or run proof list needs a reason in `not_applicable` under that
field. Requirement-level non-applicability cannot erase the scope’s package,
target or run obligations: every supported deployable scope must retain at least
one check for each of those stages. Synthetic scopes retain those obligations
as deferred and can prove genuine dependency-specific non-applicability (for
example no persistence). No required check or existing declaration can be waived.

The executable coverage checker verifies paths, unique requirement identities,
proof references, category/stage agreement, consumer references and established
program/binding execution sources. It binds the selected runnable program and
standalone image to the index identities and compiled entrypoint, accepts the
image command suffix supplied after a runtime base entrypoint, and checks
workload program/image/provider-template references. Unsupported contract
schemas are explicit gaps. The current provider-neutral scope validators
continue to validate dependency and health semantics. A newly required proof
without an implemented catalog command is an explicit unsupported requirement.

The repository catalog owns commands once as argument arrays. Metadata effects
must match the catalog. Only local-stage checks with `read-only` and/or
`writes-files` effects can run through `--execute-local`. Provider access,
secrets, publication and later-stage operations stay with their owning workflows.
Local completion reports later proofs as deferred. A requested later stage
reports external proof obligations for the owning controller to enforce;
aggregate reports cannot satisfy a container or live requirement.

Run declaration coverage and selection as documented in
[scripts/repo/check-selection/README.md](../../../scripts/repo/check-selection/README.md).
