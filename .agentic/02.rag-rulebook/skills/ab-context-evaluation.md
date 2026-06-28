<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.skills.ab-context-evaluation
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: skill
purpose: Compare RAG-derived context with direct repo source verification for planning and discovery tasks.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.workflows.default
  path: .agentic/02.rag-rulebook/workflows/default.md
- id: rag-rulebook.script.query-local-context
  path: scripts/02.rag-rulebook/query-local-context/script.sh
-->
# A/B Context Evaluation Skill

## Use When

Use this skill when the user asks for a plan, design direction, discovery, or
investigation and the answer should be grounded in repo rulebook knowledge.

Typical prompts include:

- "How should we build ...?"
- "What is the right architecture for ...?"
- "Investigate whether ..."
- "Discover what we already have for ..."
- "Can we plan how to ..."

Do not use this skill as the sole authority for destructive actions, deploy
execution, git history changes, secret handling, or AWS mutation. Those require
the owning execution workflow and explicit approval.

## Purpose

Run two evidence paths before answering:

1. RAG path: query the local RAG/rulebook runtime and inspect the returned
   context packet.
2. Source path: read the repo directly with targeted source verification.

Then compare the two paths before giving the user a recommendation.

The goal is to dogfood the RAG runtime while keeping source verification as the
current authority until the hosted service and evaluations are mature.

## Required Inputs

- User request text.
- Current session layer, mode, and workflow when known.
- Focused paths from the user or IDE when relevant.
- Local runtime path, defaulting to `.cache/02.rag-rulebook`.

## RAG Path

Build or refresh the local runtime if required by the current workflow before
querying.

Use `query-local-context` with the request text, session metadata, focused
paths, and a small chunk budget:

```bash
bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --request-text "<user request>" \
  --session-layer "<layer>" \
  --session-mode "<mode>" \
  --session-workflow "<workflow>" \
  --focused-path "<path>" \
  --max-chunks 8 \
  --pretty
```

If the runtime is stale, record that as a RAG-path failure and either rebuild
through the governed runtime workflow or answer from source verification with a
clear note that RAG could not be evaluated.

Capture:

- selected chunks
- citations
- gaps
- stop conditions
- confidence
- required checks
- any missing corpus or stale-runtime signals

## Source Verification Path

Use targeted repo inspection. Prefer `rg`, `rg --files`, and narrow `sed`
ranges over broad reads.

Verify:

- source files named by the RAG packet
- source files named by the user
- workflow, rule, schema, or guide files implied by the request
- whether important repo facts exist outside the RAG packet

Do not treat broad source reading as better by default. Its role is to catch
misses, stale chunks, absent corpora, and overconfident retrieval.

## Comparison Report

Before the final recommendation, produce a compact comparison with these
sections when useful:

- `Agreement`: facts or guidance both paths support.
- `Disagreement`: places where RAG and source verification point in different
  directions.
- `Missed By RAG`: relevant source facts absent from the packet.
- `Missed By Source Pass`: useful RAG packet context the targeted source pass
  did not naturally surface.
- `Improve RAG`: candidate corpus, recognition-source, chunking, policy,
  evaluation, or freshness changes that would improve the RAG answer.
- `Token Estimate`: rough estimate of tokens saved by using the RAG packet
  instead of direct source verification.

If the report would distract from a simple answer, keep it short, but still
name the important comparison result.

## Token Estimate

Use an approximate, non-billing estimate:

- RAG tokens: serialized context packet characters divided by 4.
- Source tokens: inspected source-output characters divided by 4.
- Estimated saved tokens: `max(source_tokens - rag_tokens, 0)`.
- Estimated saving percent: saved tokens divided by source tokens when source
  tokens are greater than zero.

State that this is an approximation. Do not present it as exact billing or
provider usage data.

## Authority Rules

- Source files remain authoritative when RAG and source verification conflict.
- RAG misses should become reviewable improvements, not silent assumptions.
- New important terms should become recognition candidates before curated
  source changes.
- Missing domain coverage should become corpus gaps before pretending the RAG
  can answer fully.
- Repeated misses should become evaluation fixtures.

## Output Rule

The user-facing answer should make the decision clear first, then include the
A/B report. Do not bury the recommendation under process detail.
