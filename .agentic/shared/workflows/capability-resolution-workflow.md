<!-- agentic-artifact:
schema: agentic-artifact/v2
id: shared.workflows.capability-resolution-workflow
version: 1
status: active
layer: 06.shared
domain: governance
disciplines:
- agentic
kind: workflow
purpose: Govern the Capability Resolution Workflow workflow.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: repo.agents
  path: AGENTS.md
-->

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
- `chat`
- `harness`
- `education`
- `product`
- `mixed`
- `unknown`

Use `.agentic/routing-policy.yaml` as the source of truth for layer
definitions.

### Mode

Mode identifies the kind of work the user is asking the agent to perform.

Mode is independent of layer. The same mode can apply to chat, shared,
harness, education, or product work.

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

Use when the mode cannot be resolved with enough confidence.

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
Workflow: upstream llm-workbench harness-maintenance process
```

```text
Layer: chat
Mode: implementation
Workflow: .agentic/00.chat/workflows/chat-refresh-from-main.md
```

```text
Layer: product
Mode: implementation
Workflow: .agentic/product/workflows/default.md
```

## Gates

Gates run after workflow selection and before action.

At minimum:

- `execution` must use an existing capability, workflow, gate, script, tool, or documented process. If the capability must be created or changed first, treat the request as `implementation`.
- `implementation` requires explicit write permission for the current chat.
- `unknown` must not proceed to edits or commands that mutate state.
- If a required action, recovery path, workaround, or substitution is not
  governed by the selected workflow, gate, script, or standard, stop and report
  the missing governance gap before acting.

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

## Prompt Routing Fixtures

Prompt-level routing examples belong to the repo's context router when one
exists. Use that router's fixtures and context-packet checks when prompt
routing behavior changes.

Add or update routing fixtures when:

- prompt routing behavior surprises the user or agent
- a prompt selector bug is fixed
- a new layer or mode concept is introduced
- routing rules are changed and existing behavior should be preserved

## Session Metadata

Chat session metadata records lifecycle continuity: session log, branch,
worktree, transcript metrics, and latest context-packet references.

Do not write durable chat-session `layer`, `mode`, or `workflow` fields. When a
prompt needs those values, resolve them for the current prompt through this
repo's assistant instructions and any repo-provided context router, then retain
the packet reference as continuity evidence if a router returns one.
