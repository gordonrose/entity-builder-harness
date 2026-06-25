<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.readme
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Define harness ADR naming, status, creation, and public export guidance.
portability:
  class: source-only
  targets: []
used_by:
- id: chat.doc.public-chat-workbench-adrs
  path: docs/00.chat/public-chat-workbench-adrs.md
- id: chat.script.upstream.bootstrap-llm-workbench-repo
  path: scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh
-->

# Harness Architecture Decision Records

Harness ADRs record durable decisions about the agentic harness: workflows,
gates, scripts, routing, session state, and agent operating rules.

ADRs explain why the harness is shaped a certain way. They do not replace
workflows, checklists, gates, scripts, or `AGENTS.md` instructions.

## Public Chat Workbench Export

Only ADRs listed in
`docs/00.chat/public-chat-workbench-adrs.md` are copied into the
public `llm-workbench` bootstrap.

When creating a future ADR, add it to that manifest only if it explains current
public chat workbench behavior. Do not add ADRs that are source-repo-only,
non-chat layer decisions, temporary migration history, or private operational
details.

## Naming

Use sequential, zero-padded filenames:

```txt
0001-short-kebab-title.md
```

## Status

Use one of:

- `proposed`
- `accepted`
- `superseded`

When an ADR is superseded, link to the replacement ADR.

## Template

```md
# 0001 Short Title

Status: accepted
Date: YYYY-MM-DD

## Context

What problem or tradeoff led to this decision?

## Decision

What did we decide?

## Consequences

What does this make easier, harder, safer, or more constrained?
```

## ADR-Worthy Decisions

Create or update a harness ADR when a chat decides to:

- add or change a harness layer, workflow, gate, script family, or lifecycle rule
- change how agents classify, route, commit, merge, escalate, or preserve context
- accept a tradeoff where future agents may ask why the harness works this way
- reject a plausible alternative that future work may reconsider

An ADR is usually not needed for typo fixes, narrow bug fixes, fixture-only
updates, or mechanical documentation changes. In those cases, record the
reason in the session log ADR disposition.
