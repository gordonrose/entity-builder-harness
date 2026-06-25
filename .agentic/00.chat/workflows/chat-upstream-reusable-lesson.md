<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.workflows.chat-upstream-reusable-lesson
  version: 1
  status: active
  layer: 00.chat
  domain: chat
  disciplines:
  - agentic
  kind: workflow
  purpose: Document Chat Upstream Reusable Lesson Workflow.
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
# Chat Upstream Reusable Lesson Workflow

## Use When

Use this when work in a product or downstream repo reveals a reusable chat
harness lesson that should be promoted to an upstream workbench repo such as
`llm-workbench`.

## Purpose

Create a governed handoff from the source repo where the lesson was discovered
to the upstream workbench repo that owns reusable chat harness behavior.

The workflow documents and opens the upstream task. It does not silently copy
files, edit the source repo, push to remotes, or mutate both repos in one step.

Architecture decision: `docs/harness/architecture/adrs/0014-promote-reusable-lessons-upstream.md`.

## Ownership Model

- The source repo provides evidence from real work.
- The upstream workbench repo owns reusable chat harness workflows, scripts,
  checklists, standards, and installer behavior.
- Product, deployment, domain, and customer-specific rules stay in the source
  repo.
- If ownership is ambiguous, stop and ask whether the lesson is reusable or
  source-repo-specific.

## Required Source Packet

Before opening the upstream chat, collect:

- source repo absolute path
- source branch
- source chat worktree absolute path
- source session log absolute or repo-relative path
- source Codex transcript path when recorded in session metadata
- target upstream repo absolute path
- reusable lesson summary
- source evidence paths or commands
- source-repo-specific details that must not be promoted

## Required Boundaries

The upstream handoff prompt must include:

```txt
Inspect the source paths read-only.
Do not edit the source repo.
Do not copy source-repo-specific product, deployment, customer, or domain rules
into the upstream workbench.
Extract only the reusable chat harness lesson.
If reusable ownership is ambiguous, stop and ask.
Do not push unless explicitly approved separately.
```

## Opening The Upstream Chat

From the upstream workbench repo, start a normal chat session using the existing
chat startup path. The source repo may prepare the prompt, but the upstream repo
must own the implementation chat.

The prompt should include:

```txt
Task: Promote reusable chat harness lesson into llm-workbench

Source repo: <absolute-path>
Source branch: <branch>
Source chat worktree: <absolute-path>
Source session log: <path>
Source transcript: <path-or-blank>
Target repo: <absolute-path>

Reusable lesson:
<summary>

Evidence:
<paths, commands, failure mode, decisions>

Keep out of upstream:
<source-repo-specific details>

Boundaries:
Inspect the source paths read-only.
Do not edit the source repo.
Do not copy source-repo-specific product, deployment, customer, or domain rules
into the upstream workbench.
Extract only the reusable chat harness lesson.
If reusable ownership is ambiguous, stop and ask.
Do not push unless explicitly approved separately.
```

## Later Script

A later command may prepare this source packet and open the upstream chat, but
the command must preserve the boundaries above. Do not script cross-repo copying
until this workflow has been exercised manually.
