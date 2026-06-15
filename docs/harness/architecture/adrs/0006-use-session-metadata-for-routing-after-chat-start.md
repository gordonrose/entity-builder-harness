# 0006 Use Session Metadata For Routing After Chat Start

Status: accepted
Date: 2026-06-16

## Context

The harness classifies each chat by task, layer, mode, and workflow at startup.
Agents can also infer classification from the latest user message, open files,
or surrounding repo context. Reclassifying opportunistically can look helpful,
but it risks changing the workflow, gates, or permission posture after the
session has already been created.

The session log is durable state for the current branch. It is the only place
where startup classification, branch identity, and selected workflow are
recorded together.

## Decision

After chat startup, agents use the current branch's session metadata as the
source of truth for layer, mode, and workflow.

Agents must not reclassify unless the session metadata is missing, incomplete,
or marked `unknown`. If a later user request adds a new phase, the agent should
treat that as a phase within the current chat and still follow the selected
workflow's gates unless the session metadata itself is invalid.

The routing order remains:

```txt
task -> layer -> mode -> workflow -> gates
```

## Consequences

Workflow selection becomes stable and auditable for the lifetime of a chat
branch. Agents are less likely to bypass gates by reinterpreting the task after
startup.

This makes session metadata quality more important. Startup classification
errors must be corrected explicitly instead of silently overridden by later
agent judgment.
