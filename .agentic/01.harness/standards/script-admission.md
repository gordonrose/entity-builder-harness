<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.standards.script-admission
version: 3
status: active
created_on: "2026-11-23"
updated_on: "2026-11-26"
layer: 01.harness
domain: scripts.governance
disciplines: [agentic, architecture, sre]
kind: standard
purpose: Require a small evidence-backed decision before adding a repository script.
portability: { class: source-only, targets: [] }
used_by:
- id: shared.plan.script-library-simplification
  path: .agentic/shared/plans/implementation/script-library-simplification.md
- id: harness.workflows.build-capability-workflow
  path: .agentic/01.harness/workflows/build-capability-workflow.md
-->

# Script Admission

## Purpose

Create a script only when it is the smallest useful owner of a deterministic
operation or proof. This standard makes that decision visible before code is
added. It does not create a second catalogue, selector, wrapper layer, or
scheduler.

Use it when proposing a new executable file under `scripts/`, including a
script, helper, test program, fixture, wrapper, or selector change. It does
not require a retrospective record for every existing script.

## First decide whether a script is needed

Before creating a script, check the relevant existing capability and answer:

1. Is there a deterministic action or assertion that cannot be expressed by
   the existing implementation, test, workflow, or standard?
2. Does an existing capability already own the same action, risk, or public
   route? If so, extend that capability rather than adding another script.
3. Is the proposed file temporary investigation code? If so, do not add it to
   the repository unless the task explicitly needs durable, repeatable proof.

If the answer to the first question is no, use the appropriate existing
artifact type instead. The artifact decision table in
[`agentic-artifact-standards.md`](agentic-artifact-standards.md) owns that
choice.

## Required admission record

Record the following in the existing task plan, implementation plan, or
session record before creating the script. Do not create a separate register
for these records.

```text
Proposed path:
Role: operation | helper | test | fixture | wrapper | selector
Owner and capability:
Purpose:
Direct consumer(s):
Named risk:
Proof lane: local change | commit | merge | package/deploy | runtime smoke | scheduled hygiene
Execution boundary and actual child effects:
Relevant inputs and evidence invalidation:
Expected cost and measurement:
Retained manual/deferred route (if applicable):
Existing capability considered:
Reuse decision: extend | reuse unchanged | new bounded capability
Why a script is necessary:
```

The record may be short, but each field must have a concrete answer. “Useful
to have” is not a named risk, and “all scripts” is not a consumer.

## Role and execution boundary

Choose one primary role:

| Role | Owns | Does not own |
| --- | --- | --- |
| Operation | A declared local, package, deploy, or runtime action. | Broad selection policy. |
| Helper | Mechanics called by an operation or test. | Direct lifecycle execution. |
| Test | Proof of one named risk for its capability. | Unrelated hygiene scanning. |
| Fixture | Controlled input for a named test. | Direct execution. |
| Wrapper | A stable requested route to an operation or test. | New policy or duplicated logic. |
| Selector | A declared decision about which existing checks run. | The checks' implementation or a second scheduler. |

Give the script a primary proof lane and declare any required later-stage
consumer through the existing check catalogue. A new check is not selected by
default merely because it exists. Broad architecture, topology, catalogue and
periodic regression work remains manually available or deferred unless a direct
changed-input risk requires it in an ordinary lane. A scheduled lane is active
only when its owning schedule exists; this standard does not create one.
A selector, wrapper, or registry with a new
cross-capability scheduling effect requires explicit approval before it is
created or changed.

## Owner and path decision

Identify the real owner from responsibility and direct consumers, not from the
nearest current directory. The intended long-term script shape is:

```text
scripts/<owner-layer>/<domain>/<capability>/
```

Use the implemented owner and approved migration manifest for the affected
family. A proposal in a plan does not become an executable home until the files
and their callers move together. For families whose migration is incomplete:

<!-- deterministic-check: allow reason="choosing a new capability home requires source-backed ownership judgment while the legacy path migration remains incomplete; automatic classification would create the prohibited path classifier" -->
1. extend the existing canonical capability home when one exists;
2. do not infer ownership from a legacy path alone;
3. if no valid existing home exists, state the proposed owner, domain, and
   capability boundary in the admission record and obtain approval before
   creating a new folder; and
4. use the path-migration workflow for a move or rename rather than adding a
   compatibility copy.

This standard deliberately does not decide paths automatically. It prevents an
unexplained folder decision while preserving the evidence needed for a later,
bounded folder migration.

`shared` is reserved for a mechanism with evidence of more than one real
consumer. It is not a temporary holding area for work whose owner is unknown.

## Implementation and proof

New files require the repository metadata header. Follow the
[metadata standard](artifact-metadata-headers.md) for its exact shape.
New source files with more than 50 lines of code, excluding the header, require
prior approval.

Keep source, helpers, tests, fixtures, wrappers, and selection logic separate
where they have different roles. A capability does not need every subfolder;
small, single-purpose work should remain small.

Verify only the named risk and direct consumer boundary in the admission
record. Record any intentionally deferred proof and its manual or scheduled
route. Changing a script's role, owner, consumer set, or execution lane is a
new admission decision, not a silent metadata edit.

Execution effects describe the operation and its actual children, independently
of when a check is selected. Follow the canonical metadata taxonomy and
[governed permissions](governed-script-permissions.md); neither a folder name,
test label nor approval flag makes an external mutation locally safe. Reuse
matching evidence only while the declared inputs, tool versions and required
execution context still match. Keep failures attributable to the existing owner
instead of adding a new wrapper or retry policy.

## Recorded authoring example: package-check input helper

The approved 2026-11-26 transfer of `check-inputs.mjs` demonstrates this
workflow with existing code, not a speculative new capability:

- **Need and home:** deriving which files a package check actually depends on
  belongs to `scripts/repo/check-selection/`. The existing compiler owner,
  `scripts/repo/workspace-build/`, remains responsible for compilation. Reuse
  its declaration and compiler readers instead of creating another resolver.
- **Primary role and consumers:** this is a helper, called by the existing
  `workspace_context.py` and its separate `check-inputs-test.mjs`. It is not
  a build operation, scheduler or new public command. The original metadata
  identity is retained; a path transfer is not a second implementation.
- **Risk and boundary:** wrong dependency discovery can omit necessary proof
  or invalidate unrelated proof. The helper reads declarations and, when
  required, the local package-manager setting; it does not run the package
  commands it inspects. Its seven existing cases use disposable files and
  reject unsupported commands, cycles and missing inputs with bounded reasons.
- **Proof and invalidation:** the existing catalogue identity
  `check-selection-workspace-inputs` uses the existing selector wrapper's
  `workspace-inputs` branch. Its declared helper, test, compiler readers,
  wrapper, runtime and configuration inputs govern proof reuse. Real package
  checks separately retain their resolved source, dependency and context inputs.
  The package wrapper no longer runs these selector tests; its five compiler
  groups and connected packaging proof remain.
- **Cost and admission:** the recorded focused run passed all seven cases in
  23.462259 seconds total, including 6.201902 seconds of child execution. The
  catalogue's 15-second estimate is advisory, not a timeout or a guarantee.
  This approved move reused existing files and headers; it did not authorise
  a new source file above 50 code lines or add a second execution system.

The [programme record](../../shared/plans/implementation/script-library-simplification.md#autonomous-p6-continuation--2026-11-26)
retains the run reference and direct-consumer results. This bounded example
does not establish the final combined candidate's integration, deployment or
publication proof, and does not activate nightly checks.

## Non-goals

This is not a requirement to:

- reorganise the existing script tree;
- create an inventory, registry, scheduler, or automatic path classifier;
- select all tests on commits or merges; or
- create a test for prose-only changes.

Those decisions remain with their existing owners and approved bounded slices.
