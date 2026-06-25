<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.standards.evaluation-fixtures
version: 1
status: active
layer: 01.harness
domain: governance
disciplines:
- agentic
kind: standard
purpose: Define how harness evaluation fixtures are authored, owned, validated, and evolved.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
- id: harness.standards.agentic-artifact-standards
  path: .agentic/01.harness/standards/agentic-artifact-standards.md
- id: rag-rulebook.standard.retrieval-selector-evaluations
  path: .agentic/02.rag-rulebook/standards/retrieval-selector-evaluations.md
-->
# Evaluation Fixtures

## Purpose

Use evaluation fixtures when harness behavior depends on interpreting an input
and producing the right structured outcome.

Examples include routing, classification, retrieval selection, context-packet
construction, output shape, stop-condition handling, and confidence behavior.

Evaluation fixtures are not just smoke tests. A smoke test proves a command can
run. An evaluation fixture proves the behavior is right for a named case.

## Core Rule

Every evaluation fixture must make the expected behavior reviewable.

The fixture must say:

- what input is being tested
- what output must happen
- what output must not happen
- which behavior, policy, standard, or bug it protects
- which command or validator decides pass or fail
- when the fixture should be updated

If a fixture needs human judgment, the judgment criteria must be explicit
enough that two reviewers can discuss the same evidence.

## Required Fields

Machine-readable evaluation fixtures should include these fields or equivalent
sections:

- `fixture_id`: stable lower-dot ID.
- `status`: `draft`, `active`, `superseded`, or `retired`.
- `owner_layer`: layer responsible for maintaining the fixture.
- `purpose`: behavior the fixture protects.
- `input`: prompt, metadata, files, command arguments, or state under test.
- `expected`: required outputs, fields, matches, side effects, or decisions.
- `banned`: outputs, matches, side effects, or decisions that must not happen.
- `acceptance`: deterministic pass/fail rules.
- `validator`: script, gate, or review process that evaluates the fixture.
- `source_refs`: standards, policies, ADRs, bugs, or examples that justify it.
- `update_triggers`: changes that require reviewing or updating the fixture.

Free-form examples may omit field names only when the same information is
plainly present and a validator is not yet available.

## Fixture Types

Use positive fixtures to prove desired behavior.

Use negative fixtures to prove unsafe behavior is rejected, downgraded, or
reported as a gap.

Use regression fixtures when a surprising miss, false positive, or user
correction reveals a durable behavior requirement.

Use calibration fixtures when thresholds, ranking, confidence, or trimming need
stable examples.

## Expected Outcomes

Expected outcomes should test the public contract, not incidental
implementation details.

Good expected outcomes name stable facts such as:

- selected layer, mode, workflow, or corpus
- required output fields
- required gap or stop condition
- required citation or source reference
- required check or gate
- forbidden action
- confidence band or threshold result

Avoid expecting fragile ordering unless order is part of the behavior under
test.

## Update Rules

Do not silently rewrite an expected outcome to make a failing fixture pass.

When changing an active fixture expectation, record why one of these is true:

- the old expected behavior was wrong
- the governed policy changed
- the underlying corpus or source artifact moved
- the fixture was over-specific
- the behavior is intentionally retired

Repeated fixture changes for the same behavior should trigger a standard,
policy, schema, or validator review.

## Governance Rules

Evaluation fixtures should live near the capability they protect.

Harness-wide fixture rules live in this standard. Layer-specific fixture rules
may add stricter requirements, but they must not weaken these rules.

When a behavior becomes commit-critical, add its evaluation command to the
owning layer gate. Until then, keep the fixture runnable by an explicit command
and document why it is not yet gating commits.

## Banned Behavior

Evaluation fixtures must not:

- hide ambiguous behavior behind broad expected text
- rely on unreviewed LLM judgment for pass/fail when deterministic checks are
  possible
- update expected outcomes without rationale
- test only happy paths for routing, retrieval, safety, or governance behavior
- allow fixture data to become an ungoverned source of truth
- replace standards, schemas, or policies with examples alone

## Relationship To Other Artifacts

Standards define durable expectations.

Policies define selectable behavior.

Schemas define machine-readable contracts.

Scripts and gates evaluate fixtures.

Fixtures provide concrete examples that prove the above are working together.
