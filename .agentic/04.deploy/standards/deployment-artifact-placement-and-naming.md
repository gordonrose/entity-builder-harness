<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.deployment-artifact-placement-and-naming
version: 1
status: active
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.governance
disciplines:
- agentic
- architecture
- sre
kind: standard
purpose: Define how agents choose the owner, lifecycle phase, target and scope path, and clear name for future deployment artifacts.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: harness.workflows.change-harness
  path: .agentic/01.harness/workflows/change-harness.md
- id: deploy.standards.lifecycle-stage-ownership
  path: .agentic/04.deploy/standards/lifecycle-stage-ownership.md
- id: deploy.plan.migration.ordered-deployment-harness-and-target-layout
  path: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md
- id: deploy.script.validate-artifact-placement
  path: scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/script.py
-->
# Deployment Artifact Placement and Naming

## Purpose

Use this standard before creating, moving, or materially renaming a deployment
artifact. It answers three separate questions in order:

```text
What kind of thing is this?
→ Where is it used or what does it describe?
→ What should its path and name say to a reader?
```

Do not use a folder merely because it has a familiar name. Choose the owner and
purpose first, then the path.

## The Three Homes

<!-- deterministic-check: allow reason="The placement validator checks canonical path shapes; classifying a new artifact's semantic owner remains a human and workflow decision." -->
| If the artifact… | It belongs in… | Example |
| --- | --- | --- |
| declares what software, a package, or a selected target must contain | `infra/04.deploy/` | a scope declaration or AWS template |
| tells an agent how, when, or under what durable rule to perform work | `.agentic/04.deploy/` or active provider governance | an update workflow or immutable-image rule |
| executes or deterministically validates an action | `scripts/04.deploy/` | create-change-set or image smoke command |

README files explain a nearby tree to people. They must link to the governing
workflow, standard, contract, or script; they must not become a competing
source of mandatory procedure.

## Placement Decision

Apply these questions in order.

1. **Is it a fact or requirement about a target?** Put it in `infra/`.
   Examples: expected network route, required configuration name, selected
   workload shape, accepted release identity, or CloudFormation template.
2. **Is it a reusable instruction or rule for agents?** Put it in `.agentic/`.
   Examples: how to compare a target, what an accepted release requires, or
   how to classify a dependency.
3. **Can a tool perform or check it deterministically?** Put its executable
   part in `scripts/`, even when a workflow or standard also describes when to
   run it.
4. **Does it apply across providers and targets?** Keep it once in
   `.agentic/04.deploy/`.
5. **Does it require AWS-specific meaning, permissions, or provider response
   handling?** Keep it in `.agentic/aws/` until the provider-neutral migration
   explicitly moves it.
6. **Does it apply only to one target or scope?** Include that target and scope
   in the path beneath the relevant provider and lifecycle phase. Do not copy a
   generic rule into that target directory.

If more than one answer appears true, separate the artifacts. For example, a
scope's required network is an `infra` declaration; the reusable alignment
procedure is a generic workflow; AWS inspection is an AWS adapter; and the
actual inspection command is a script.

## Lifecycle Phase

Use the phase names defined by
`.agentic/04.deploy/lifecycle/README.md`. The phase answers **when** the
artifact is primarily used:

| Phase | Use for |
| --- | --- |
| `00-target-alignment` | target selection and safe comparison before implementation |
| `10-development` | local runtime, configuration, and dependency preparation |
| `20-build` | compilation and runtime-payload construction |
| `30-test` | non-package deterministic tests |
| `40-package` | image/package build, qualification, custody, scan, and attestation |
| `50-deploy` | target readiness, reviewed change set, and approved mutation |
| `60-run` | live verification, monitoring, acceptance, restoration, and recovery |

A capability has one primary phase. It may link to upstream or downstream
work, but it must not be copied into several phase folders merely because it
is relevant to each.

## Canonical Target Declaration Layout

For a target adopted under the ordered layout, use:

```text
targets/<target>/
  00-target/                         # what destination is selected
  10-foundation/                     # shared facilities before workloads
  20-scopes/<scope>/
    00-declaration/                  # what the workload needs
    10-workload-binding/             # selected workload shape
    20-alignment/                    # fresh facts required before mutation
    30-release-evidence/             # accepted release and rehearsals
  30-provider-realization/<provider>/ # provider templates and bindings
  40-package-custody/<pipeline>/     # trusted package publication route
```

The numbered target folders are a conceptual ownership map. They do not replace
the routed release workflow as the executable order of operations.

## Harness and Script Layout

For new provider-neutral harness artifacts, the intended canonical form is:

```text
.agentic/04.deploy/<phase>/<artifact-type>/<clear-action-or-requirement>.<ext>
```

For AWS-specific target procedures during the transition:

```text
.agentic/aws/<phase>/workflows/targets/<target>/20-scopes/<scope>/<clear-action>.md
```

For executable deployment capabilities:

```text
scripts/04.deploy/lifecycle/<phase>/targets/<target>/<scope>/<clear-action>/
```

Generic scripts omit `targets/<target>/<scope>` only when they truly accept no
target-specific facts. Do not give a target-bound script a free-form target
argument merely to avoid this path.

Existing paths remain valid until a governed migration moves them. This standard
does not authorise a blanket rename.

## Naming Rules

Use lowercase kebab case for folders and filenames. Names must be meaningful
without prior harness vocabulary.

| Artifact | Name pattern | Good example | Avoid |
| --- | --- | --- | --- |
| workflow | verb + object + outcome | `review-and-execute-target-update.md` | `release-flow.md` |
| standard | durable requirement | `require-immutable-package-identity.md` | `package-rules.md` |
| schema | represented noun + version | `package-custody-receipt.v1.schema.yml` | `receipt.yml` |
| script folder | verb + object + outcome | `privately-verify-release/` | `verify/` |
| target declaration | declared noun + role | `runtime-alignment-contract.yml` | `runtime.yml` |
| provider template | provider resource purpose | `bootstrap-runtime.yml` | `stack.yml` |
| evidence | dated event or stable accepted state | `release-b-to-a-2026-10-21.yml` | `latest.yml` |

Use a name such as `runnable-program` only when the file itself defines that
term or its parent folder makes its purpose obvious. Do not use internal labels
such as `control`, `flow`, `utility`, `manager`, or `helper` as the principal
name without saying what they control, flow through, manage, or help.

## Required Links

Every new or moved active deployment artifact must identify its relationship to
the other homes through metadata or a nearby index:

- an `infra` declaration identifies its governing workflow and executable
  validation where they exist;
- a workflow identifies the relevant declaration, provider procedure, and
  script it routes;
- a script identifies the workflow or standard that authorises it and its
  effect category;
- a target-specific procedure identifies its exact target and scope;
- an evidence record identifies the accepted declaration or event it proves.

One fact, rule, command, and evidence record each have one canonical source.
Links do not authorise duplication.

## Required Checks

For a new deployment artifact, run the placement validator before adding it:

```bash
python3 scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/script.py \
  --kind <kind> --path <proposed-relative-path>
```

Then run the metadata-header check, the owning workflow checks, and
`git diff --check`. For moves or renames, also follow the artifact-path
migration workflow and its reference checker.

The validator checks path shape and naming only. It cannot decide whether the
artifact's content is correct, whether a scope is needed, or whether a provider
operation is authorised; those remain human and workflow decisions.

## Stop Conditions

Stop and resolve the design before creating a file when:

- no owner home is clear;
- a proposed file would duplicate a generic rule for one target;
- a target-specific procedure has no target or scope boundary;
- a new dependency, permission, configuration, network path, health condition,
  recovery condition, or operational signal does not fit an existing declared
  scope;
- a move would leave active consumers behind without a compatibility choice.
