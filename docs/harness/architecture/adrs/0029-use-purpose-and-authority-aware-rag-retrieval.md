<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.adr.0029-use-purpose-and-authority-aware-rag-retrieval
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the decision to separate RAG retrieval chunk purpose from chunk authority.
portability:
  class: source-only
  targets: []
used_by:
- id: rag-rulebook.plan.explanation-aware-chunking-and-retrieval
  path: .agentic/02.rag-rulebook/plans/explanation-aware-chunking-and-retrieval.md
- id: rag-rulebook.policy.retrieval-selector.v1
  path: .agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml
- id: rag-rulebook.schema.rulebook-index
  path: .agentic/02.rag-rulebook/schemas/rulebook-index.schema.yml
- id: rag-rulebook.schema.context-packet
  path: .agentic/02.rag-rulebook/schemas/context-packet.schema.yml
-->
# ADR 0029: Use Purpose And Authority Aware RAG Retrieval

## Status

Accepted.

## Context

The RAG/rulebook layer needs to support two different uses of repository
knowledge:

- helping an agent execute governed work safely;
- helping a human understand the mental model, rationale, examples, and
  boundaries behind that work.

Before this decision, the retrieval path was strongest for execution:
structured rules, required checks, stop conditions, and compact context
packets. That is useful for safe action, but it is not sufficient for prompts
such as "walk me through this" or "teach me what this slice does."

If all rich source material must become structured YAML rules to be retrieved,
rule chunks become bloated with teaching prose. If source material is not
retrieved directly, human explanation prompts can miss the source-backed
rationale that was written for learning.

At the same time, explanation material must not become permission to write,
commit, deploy, mutate cloud resources, or bypass governed workflows.

## Decision

RAG retrieval separates chunk purpose from chunk authority.

Chunk purpose describes why a chunk may be selected. Purpose labels include
rules, source explanations, ADR decisions, plan milestones, guides, artifact
summaries, and retrieval profiles.

Chunk authority describes what a consumer may do with the chunk. Authority
labels include execution authority, explanation support, decision history,
implementation planning, and orientation.

Explanation, tutor, and "walk me through" prompts should prefer
source-explanation chunks, guides, ADR decision context, and supporting rules.

Implementation, deploy, git, write, and other side-effecting prompts should
prefer binding rules, execution-authority chunks, required checks, stop
conditions, workflows, and relevant ADRs.

Source material, guides, ADRs, and plans may be retrieved directly for
explanation without requiring every useful paragraph to become a YAML rule.
Structured rules remain the compact execution layer.

Explanation-support chunks cannot authorize side effects. Authorization still
comes from applicable workflows, explicit approval, executable gates, and
execution-authority evidence.

## Consequences

Human-facing answers can use richer source-backed explanations without
polluting binding rule chunks.

Implementation prompts retain compact, high-signal execution guidance and stop
conditions.

Context packets must expose enough purpose and authority metadata for agents to
distinguish teaching material from binding instructions.

Existing source material, guides, ADRs, and plans should be accounted for by
purpose-aware chunking or visible retrieval gaps.

Side-effecting prompts may use explanation chunks as background, but they must
not treat those chunks as permission to act.

## Non-Goals

This ADR does not select a hosted vector database, model, embedding provider,
MCP server, or cloud deployment shape.

This ADR does not make source-material prose a structured rule without a
source-to-rule derivation.
