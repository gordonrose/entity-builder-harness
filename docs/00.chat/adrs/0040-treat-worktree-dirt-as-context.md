<!-- agentic-artifact:
schema: agentic-artifact/v3
id: chat.adr.0040-treat-worktree-dirt-as-context
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 00.chat
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Replace blanket dirty-worktree confirmation with existing-change inspection and operation-specific safeguards.
portability:
  class: source-only
  targets: []
used_by:
- id: chat.adrs.readme
  path: docs/00.chat/adrs/README.md
-->
# 0040 Treat Worktree Dirt As Context

Status: accepted
Date: 2026-10-22
Supersedes: [ADR 0005](0005-preserve-bootstrap-dirty-worktree-before-workflow-loading.md)

## Context

The original startup gate protected edits inherited when a new chat switched
branches in one checkout. Chats now use separate worktrees. Startup still
captures the source checkout's status before creating the chat worktree, so
unrelated source changes can trigger a blanket pause in an isolated chat.

Dirty status identifies changed paths. It cannot establish ownership, conflict,
or whether the next action would overwrite existing work. Expected task edits
and session bookkeeping should not repeatedly require confirmation.

## Decision

Use the existing-change policy in
[chat-start](../../../.agentic/00.chat/workflows/chat-start.md#existing-changes)
as the canonical rule. Inspect changes in the active chat worktree, preserve
unrelated work, and proceed within the user's authorization. Ask when a concrete
conflict, unclear ownership, or overwrite decision cannot be resolved safely
within that authorization. Dirt alone does not establish such a conflict.

Startup status remains informational, including in JSON handoff packets. The
clean/bookkeeping-only/dirty helper keeps its classification and exit semantics.
Merge readiness, main refresh, cleanup, write-location checks, and approvals
for commits and destructive actions retain their operation-specific protections.

Implement reusable behavior in llm-workbench first. Integrate reviewed policy
changes downstream while preserving local improvements and recording source
provenance in the session log. A scoped source integration is not an npm release
or a wholesale package update.

## Consequences

Ordinary work can continue with existing edits. Agents must inspect and preserve
those edits instead of treating a dirty bit as proof of an unsafe operation.
Tests cover dirty-source startup, both handoff formats, and preservation of
source changes; merge, refresh, and cleanup checks remain independent.
