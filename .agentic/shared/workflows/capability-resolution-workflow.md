# Capability Resolution Workflow

## Purpose

Resolve a user request into the smallest safe execution path for the harness.

Capability resolution happens after chat-start session discovery and before any workflow-specific gates are executed.

The resolution order is:

```text
task -> layer -> mode -> workflow -> gates
```

## Resolution Fields

### Layer

Layer identifies the ownership area affected by the request.

Allowed values:

- `shared`
- `harness`
- `education`
- `product`
- `mixed`
- `unknown`

Use `.agentic/routing-policy.yaml` as the source of truth for layer
definitions.

### Mode

Mode identifies the kind of work the user is asking the agent to perform.

Mode is independent of layer. The same mode can apply to shared, harness, or product work.

Allowed values:

- `discovery`
- `planning`
- `execution`
- `implementation`
- `unknown`

## Mode Definitions

### discovery

Use when the user wants explanation, discussion, brainstorming, conceptual guidance, or read-only inspection of files, logs, repository state, runtime state, or configuration.

Default action: read-only response or inspection.

### planning

Use when the user wants a proposal, architecture, implementation plan, migration plan, or ordered change list.

Default action: read-only planning.

### execution

Use when the user wants the agent to use an existing capability, workflow, gate, script, tool, or documented process without changing or adding capabilities.

Default action: follow the selected workflow's gates before running the existing capability.

### implementation

Use when the user wants the agent to create, edit, move, delete, format, or otherwise modify files, or add/change capabilities, workflows, gates, scripts, tools, documentation, or process rules.

Default action: require explicit write permission for the current chat before editing.

### unknown

Use when the mode cannot be classified with enough confidence.

Default action: stop and ask one clarifying question before selecting a workflow or editing files.

## Workflow Selection

Select a workflow only after both layer and mode are known.

Workflow selection must respect both dimensions:

- Layer determines ownership.
- Mode determines posture and permissions.

Examples:

```text
Layer: harness
Mode: planning
Workflow: .agentic/harness/workflows/build-capability-workflow.md
```

```text
Layer: product
Mode: implementation
Workflow: .agentic/product/workflows/default.md
```

## Gates

Gates run after workflow selection and before action.

At minimum:

- `execution` must use an existing capability, workflow, gate, script, tool, or documented process. If the capability must be created or changed first, reclassify as `implementation`.
- `implementation` requires explicit write permission for the current chat.
- `unknown` must not proceed to edits or commands that mutate state.

Workflows may define stricter gates.

## Ambiguity

Stop if any of these are ambiguous:

- layer
- mode
- workflow
- required permissions
- whether a requested action mutates state

Ask exactly one clarifying question, then resume resolution from the earliest ambiguous field.

If a request contains more than one mode, split it into ordered phases and resolve each phase separately.

Example:

```text
Phase 1: discovery
Phase 2: implementation
```

## Classifier Fixtures

Classifier examples live in:

```text
scripts/shared/chat/request-initialization/classify-task.fixtures.tsv
```

Check them with:

```bash
bash scripts/shared/chat/request-initialization/check-classify-task-fixtures.sh
```

Add a fixture when:

- classification behavior surprises the user or agent
- a classifier bug is fixed
- a new layer or mode concept is introduced
- classifier rules are changed and existing behavior should be preserved

## Session Metadata

Chat session metadata should include all resolved fields:

```yaml
layer: harness
mode: planning
```

If existing session metadata lacks `mode`, classify mode from the current user request or session task before selecting a workflow.
