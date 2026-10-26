<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.script.artifact-metadata.update-lifecycle.readme
version: 3
status: active
created_on: "2026-10-20"
updated_on: "2026-10-26"
layer: 01.harness
domain: metadata
disciplines: [agentic]
kind: capability-readme
purpose: Explain bounded artifact lifecycle reporting and updates.
portability:
  class: required
  targets: [llm-workbench, entity-builder, design-system-builder]
used_by:
  - id: harness.capability.artifact-metadata
    path: .agentic/01.harness/artifact-metadata/README.md
-->
# Update Artifact Lifecycle

Use this helper to migrate explicit v2 files to v3, refresh v3 update dates
after edits, or mark artifacts deprecated or superseded. The governing contract
is `.agentic/01.harness/artifact-metadata/standard.md`.

Explicit paths may be outside traditional harness directories and use any file
extension. The helper shares leading-header parsing with the checker and index,
including Python, TypeScript and Dockerfile comments. It preserves file bodies
and prologues; embedded header examples and raw bootstrap scaffolds are not
lifecycle update targets.

## Report Before Applying

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/update-lifecycle/script.sh --paths .agentic/04.deploy/plans/migration/aws-provider-neutral-transition.md
```

The default JSON report describes proposed changes and creation-date evidence.
It does not write files. First Git addition establishes repository introduction,
not original authorship of imported files. Dates use UTC. Shallow or ambiguous
history requires a confirmed `--created-on YYYY-MM-DD`; never substitute a file's
checkout timestamp. Record reviewed source commits and reasoning alongside any
explicit date override. Untracked new artifacts may use today's creation date.
For uncommitted moves, the helper follows a detected rename or one unambiguous
deleted artifact with the same stable ID. It preserves creation dates and reports
`head_baseline_path` when comparing content to the original file.

Append `--apply` to apply the reviewed batch. The command prepares and validates
all requested artifacts before writing, preserves existing content, and checks
for concurrent edits. It never stages, commits, deletes artifacts or changes
branches. No-op runs do not rewrite headers or advance dates.

For a bounded task-preparation sweep, use `--changed --apply`. It considers
only changed v2/v3 `agentic-artifact` files, leaves headerless and legacy files
alone, and never stages anything. It is safe to repeat: once the lifecycle
headers match the current task state, the second invocation makes no write.
Use explicit `--paths ... --skip-non-artifacts --apply` when the task scope is
already known and includes both ordinary source and metadata-bearing artifacts.
`--changed` is intentionally not a lifecycle-transition shortcut: deprecation,
supersession, and historical-date decisions remain explicit-path operations.

## Lifecycle Transitions

Deprecate an artifact:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/update-lifecycle/script.sh --paths <old-file> --status deprecated
```

Replace it with another artifact:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/update-lifecycle/script.sh --paths <old-file> --status superseded --replacement <replacement-file>
```

Repeat `--replacement` for a split into multiple successors. Replacement IDs
come from the target headers. Inspect the report, then add `--apply`.
New transitions use today's date. `--deprecated-on` and `--superseded-on` are
only for explicitly confirmed historical dates on existing matching states;
they must not backdate a new transition. Migration of an old deprecated artifact
without historical event evidence is blocked until its date is confirmed.

For superseded Markdown, the helper adds a visible relative link after the
title. Status metadata does not authorize file removal or deployment actions.

## Checks

```bash
bash scripts/01.harness/artifact-metadata/update-lifecycle/smoke-test.sh
bash scripts/01.harness/artifact-metadata/check-headers/script.sh --paths <file>
bash scripts/01.harness/artifact-metadata/generate-index/script.sh --all --strict --check-coverage
```

Commit gates use `check-headers/script.sh --staged` to validate staged lifecycle
changes. Run the helper after content changes and before staging; checks remain
read-only. Temporary-repository smoke tests cover history, transitions,
all-or-nothing planning and repeated-run stability.
