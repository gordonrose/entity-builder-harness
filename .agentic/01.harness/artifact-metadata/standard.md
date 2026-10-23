<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.standard.artifact-metadata
version: 3
status: active
created_on: "2026-06-24"
updated_on: "2026-10-23"
layer: 01.harness
domain: metadata
disciplines:
  - agentic
  - architecture
kind: standard
purpose: Define the versioned artifact metadata model used for agent navigation, migration planning, and repo indexing.
portability:
  class: required
  targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
used_by:
  - id: harness.standard.artifact-metadata-headers-v1
    path: .agentic/01.harness/standards/artifact-metadata-headers.md
  - id: harness.adr.versioned-artifact-metadata
    path: docs/01.harness/adrs/0021-use-versioned-artifact-metadata-for-agent-navigation.md
  - id: harness.script.artifact-metadata.check-headers
    path: scripts/01.harness/artifact-metadata/check-headers/script.sh
-->

# Artifact Metadata Standard

## Purpose

Use artifact metadata to make harness artifacts self-describing and indexable.
The metadata should let agents and humans locate relevant files by stable
identity, layer, domain, discipline, purpose, portability target, and
relationship without reading every file in full.

## Compatibility

Existing v1 and `agentic-artifact/v2` headers remain valid during migration.
New artifacts and intentionally migrated artifacts use `agentic-artifact/v3`.
Legacy files do not require a bulk rewrite to pass ordinary commit checks.
An explicit unknown schema must fail validation rather than fall back to v1.

Do not bulk-migrate historical artifacts only to modernize headers. Backfill in
focused batches with validation evidence.

## V3 Lifecycle Contract

`schema.v3.yml` extends the v2 fields with lifecycle dates and replacement
references. This standard is its companion guide; the schema includes structured
field explanations. Dates are quoted strings in `YYYY-MM-DD` format, interpreted
as UTC calendar dates. Unquoted YAML dates and impossible or future dates fail.

```yaml
schema: agentic-artifact/v3
id: harness.example.lifecycle
version: 1
status: active
created_on: "2026-10-20"
updated_on: "2026-10-20"
```

The remaining v2 identity, ownership, portability and relationship fields are
still required. Use the same comment wrapper as v2 for Markdown, YAML and scripts.

| Field | Rule |
| --- | --- |
| `created_on` | Required; creation date, immutable after migration, including renames. |
| `updated_on` | Required; UTC date of the latest body or metadata edit, including formatting and schema migration. |
| `deprecated_on` | Required for `deprecated`; may be retained in `superseded` or `retired`. |
| `superseded_on` | Required for `superseded`; may be retained in `retired`. |
| `superseded_by` | Non-empty list of `{id, path}` references paired with `superseded_on`. |

`deprecated` means continued use is discouraged without asserting a complete
replacement. `superseded` means the artifact has been replaced by the listed
artifacts. `retired` remains a separate inactive state. Draft and active artifacts
do not carry deprecation or supersession metadata. Reactivation removes obsolete
transition fields; Git preserves the historical transitions.

Dates must satisfy `created_on <= updated_on`. Each transition date must lie
between those dates; deprecation must not follow supersession when both exist.
A transition made now uses today's UTC date, not a guessed historical date.

Replacement paths are repository-relative files whose header IDs match the
reference IDs. References cannot point to the same artifact or form cycles.
Multiple replacements support documents split into several successors. Keep
replacement paths current when files move; the ID remains the durable identity.
A superseded Markdown document also carries a visible notice after its title,
linking to the replacements with relative Markdown links, because its metadata
comment is invisible in rendered documentation. Supersession does not authorize
file removal; path retirement still uses `migrate-artifact-paths.md`.

A lifecycle-only change does not automatically increment artifact `version`.
The existing semantic version policy still applies to changed guidance or
behavior. Refreshing dates alone must not cause a daily update loop.

## Lifecycle Maintenance And Backfill

The governed helper owns date maintenance and bounded migration:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/update-lifecycle/script.sh --paths <file> [<file>...]
```

The default is a read-only JSON report. After reviewing it, append `--apply`
to apply only those explicit files. The helper neither stages nor commits.
Use `--status deprecated` or `--status superseded --replacement <file>` for a
current transition; repeat `--replacement` when multiple artifacts replace one.
These status changes require the task's ordinary write permission. Apply must
prepare and validate the entire batch before writing and preserve concurrent
edits. Do not invoke the historical auto-committing v2 backfill for this work.

Backfill uses Git history with rename following. The first observed addition is
evidence of repository introduction, not proof that an imported document was
originally authored that day. Report the source commit and basis with the
proposed dates. Refuse incomplete or ambiguous history; `--created-on` supplies
an explicitly confirmed date when automatic history inference cannot establish it.
Confirmation may come from reviewed Git copy/rename/merge evidence; record the
exact source commit and reasoning with the batch report. The override reports
`basis: explicit-date` and never implies original-author confirmation. If repo
evidence remains ambiguous, obtain the date from the user rather than guess.
For an existing inactive state, `--deprecated-on` or `--superseded-on` can supply an explicitly
confirmed historical event date; these flags cannot backdate a new transition.
Do not infer old deprecation or supersession dates from the current file modification time.
Migration itself is a metadata update, so `updated_on` becomes today's UTC date;
the report retains the prior last-commit date as evidence. Work in focused batches.

A malformed historical v2 header may be repaired during migration. HEAD
comparison may recover only an unambiguous top-level v2 schema, stable ID and
legacy status; current and proposed headers still require full validation.
Ambiguous history and malformed v3 baselines remain errors, except for one
bounded repair: an existing v3 header that omitted `created_on` may add it only
when it exactly matches the artifact's earliest recorded Git history date. An existing
creation date remains immutable. This narrow recovery must not bypass immutable
v3 dates or allow stale migration dates.

After content edits, run the helper for the affected v3 files. Creation dates
remain fixed. No-op runs must not rewrite files or advance dates. The helper's
status-transition convenience path does not replace historical lifecycle review.

## Discovery And Required Headers

A file that declares a leading `agentic-artifact` or legacy `agentic-script`
header participates in validation and indexing regardless of its path or
extension. This includes infrastructure YAML, TypeScript, Python, Dockerfiles
and platform documentation. A declaration's `kind` determines its metadata
contract; being discovered does not automatically make a file a script.

Discovery uses the shared `header_discovery.py` module. It recognizes only
file-level headers in leading comments, allowing ordinary script prologues.
Embedded examples, fenced code, patch text and strings in executable bodies are
not additional artifact declarations. Malformed leading declarations are errors,
not silently skipped files. Binary files and symlink targets are not followed.

Full working-tree discovery includes tracked files and unignored untracked files.
Source archives without Git use a filesystem scan that excludes repository
internals and build/dependency directories. Staged validation reads Git blobs;
a previous declaration remains in scope when a modification or rename removes
its header. Removing or downgrading an existing v3 header cannot evade checks.

This discovery rule does not expand the existing path and extension rules that
require headers on new files. Headerless files outside those rules remain
headerless. Existing ordinary legacy modifications retain their grandfathering.

Three raw bootstrap scaffolds contain placeholders instead of artifact values:
`docs/00.chat/bootstrap/llm-workbench-template/root/scripts/install.sh.template`,
`docs/00.chat/bootstrap/llm-workbench-template/root/scripts/uninstall.sh.template`,
and `docs/00.chat/bootstrap/llm-workbench-template/root/.github/workflows/portability.yml.template`.
Only these exact paths are excluded from source-header discovery; their rendered
outputs are validated by bootstrap and portability checks. Other templates,
including CloudFormation templates, remain discoverable. The v2 compatibility
examples are real declared artifacts and remain indexed.

Run the inventory coverage gate after changing discovery or migrating headers:

```bash
bash scripts/01.harness/artifact-metadata/generate-index/script.sh --all --strict --check-coverage
```

It compares declared artifact paths with emitted index entries and fails on
missing entries or malformed headers. The repository commit hook runs this
working-tree coverage check alongside staged lifecycle validation. Keep the
checker, index, helper and public checker distribution on the same discovery
implementation; test new file types and negative embedded examples together.

## Enforcement And Consumers

The header checker supports v1, v2 and v3 and validates the staged blobs in
`--staged` mode, including replacement targets. It also checks supersession
links from unchanged indexed artifacts, so a target move, removal, or identity
change cannot leave dangling references. Unchanged sources retain their dates.
It checks added/copied/renamed and modified artifact files; missing legacy headers on ordinary modifications
remain grandfathered. Existing v3 artifacts cannot downgrade to bypass lifecycle
checks. For v3 changes, compare against HEAD (including rename sources), preserve
creation dates and require today's update date for body or non-date metadata
changes. New deprecation/supersession transitions require today's event date.
Retained transition dates are immutable; reactivation removes obsolete event
fields rather than rewriting history. The check reports errors without editing
or staging files. The helper uses the checker's read-only `--proposed` JSON
path-to-text overlay to validate a whole proposed batch and its references
before writing.

Use `--paths` or `--all` for standalone structural validation; they do not claim
to prove historical date accuracy. `--staged-added` remains a compatibility mode.
Legacy v2 retains its original four statuses; `superseded` belongs to v3.

Indexes preserve v3 identity, dates and replacement references. Superseded IDs
remain discoverable as history; inactive documents must not become active RAG
guidance. Header generators preserve v3 creation dates and keep no-op output
stable; existing generated v2 artifacts may remain v2 during migration. Newly
generated artifacts use v3. Refresh recognition sources through the existing
`generate-recognition-sources` command after inventory changes, then validate
freshness. Never hand-edit generated recognition inventories.

Validate this contract with checker, index and lifecycle-helper smoke tests,
including invalid dates, missing replacements, cycles, staged-content isolation,
legacy compatibility and repeat-run stability. New comment syntax and consumers
must be migrated together before publishing a new schema version.

## V2 Compatibility Header

Markdown artifacts should use this shape at the top of the file:

```markdown
<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.metadata.artifact-headers
version: 1
status: active
layer: 01.harness
domain: metadata
disciplines:
  - agentic
  - architecture
kind: standard
purpose: Define metadata headers for harness artifacts.
portability:
  class: reusable
  targets:
    - llm-workbench
    - entity-builder
used_by:
  - id: harness.check.artifact-metadata-headers
    path: scripts/01.harness/artifact-metadata/check-headers/script.sh
-->
```

YAML artifacts should use the same fields as YAML comments:

```yaml
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.rule.layer.packages-core
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: packages.core
#   disciplines:
#     - architecture
#   kind: ruleset
#   purpose: Define packages/core architecture placement rules for agents.
#   portability:
#     class: source-only
#     targets: []
#   used_by:
#     - id: harness.rulepack.add-core-module
#       path: docs/03.product/rule-packs/core/add-core-module.yml
```

Script artifacts are also in scope for v2. They should eventually use the same
`agentic-artifact/v2` shape with `kind: script` and an `effects` array:

```bash
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.artifact-metadata.check-headers
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Check artifact metadata headers.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#   effects:
#     - read-only
#   used_by:
#     - id: harness.checklist.before-commit
#       path: .agentic/00.chat/checklists/before-commit.md
```

Existing scripts with `agentic-script` v1 headers remain valid during migration.
New or intentionally migrated scripts use `agentic-artifact/v3`. The v2
examples above demonstrate compatibility only.

## Fields

`schema` is required. Use `agentic-artifact/v3`; v2 is retained for compatibility.

`id` is required. It is the stable identity of the artifact and must not encode
the current file path. Use lowercase dot-separated segments.

`version` is required. It is an integer that tracks meaningful changes to the
artifact contract or guidance.

`status` is required. V3 uses `draft`, `active`, `deprecated`, `superseded`, or
`retired`. V2 retains its original statuses without `superseded`.

`layer` is required. Use a numbered layer from `taxonomy.yml`.

`domain` is required and extensible. Use dot-separated values for nested areas,
such as `packages.design-system`, `apps.persistence`, or `infra.ci-cd`.

`disciplines` is required for v2. Use one or more controlled values from
`taxonomy.yml`.

`kind` is required and extensible. Use the narrowest artifact type, such as
`workflow`, `standard`, `checklist`, `adr`, `readme`, `rule-pack`, `ruleset`,
`manifest`, `config`, `script`, or `index`.

`effects` is required when `kind: script`. Use one or more controlled script
effects from `taxonomy.yml`.

`purpose` is required. Use one concise sentence that explains why the artifact
exists.

`portability` is required. It contains a `class` and a `targets` array.

`used_by` is required. Prefer ID-first references with a path hint:

```yaml
used_by:
  - id: harness.workflow.change-harness
    path: .agentic/01.harness/workflows/change-harness.md
```

## Identity Rules

Artifact IDs must be stable across path moves and file renames. Change an ID
only when the artifact is replaced by a different concept.

When one artifact splits into multiple durable artifacts, keep the old ID on the
continuing artifact only if the original concept remains intact. Otherwise mark
the old artifact `deprecated` or `retired` and create new IDs for the new
concepts.

## Version Policy

Bump `version` when the artifact changes its contract, behavior, required
inputs, output shape, or durable guidance.

Do not bump `version` for typo fixes, formatting-only changes, path moves, or
non-semantic wording cleanup.

Use generated index fields such as `content_hash`, `indexed_at`, and
`git_commit` for exact content reconciliation. Do not rely on humans to bump
`version` for every byte-level change.

## Portability Policy

Use `portability.class` to describe how the artifact should be treated during
cross-repo extraction:

- `required` means the target repo needs the artifact to function.
- `reusable` means the artifact is intended to be copied or adapted.
- `compatible` means the artifact can be used when the target supports the same
  capability.
- `source-only` means the artifact should remain in this source repo by default.
- `internal` means the artifact is private to local process or state.

Use `portability.targets` for repo or product targets such as `llm-workbench`,
`entity-builder`, or `design-system-builder`. Leave it empty when no target is
known or when the artifact is source-only.

## Used-By Policy

Use `used_by.id` as the durable relationship. Use `used_by.path` as a current
path hint and migration aid.

The checker should eventually validate that referenced IDs resolve in the
artifact index. During migration it may warn instead of fail when a referenced
ID is not yet indexed.

Path-only v1 `used_by` entries remain valid until their artifacts are migrated
to v2.

## Index Policy

The artifact index should be generated from metadata headers, not maintained by
hand. The first index should map stable IDs to current paths and metadata.

The generator should emit JSON to stdout by default. Existing v1 artifacts may
appear as legacy entries with provisional IDs until they are migrated to v2.

Historical path reconciliation can come later from Git history after v2 IDs are
widely adopted.
