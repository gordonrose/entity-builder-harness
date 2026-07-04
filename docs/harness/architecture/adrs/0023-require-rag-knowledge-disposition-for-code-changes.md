<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.adr.0023-require-rag-knowledge-disposition-for-code-changes
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - agentic
  - architecture
  kind: adr
  purpose: Record the decision to require RAG knowledge disposition for knowledge-bearing code changes.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: repo.script.commit-gates
    path: scripts/repo/commit-gates/script.sh
  - id: rag-rulebook.script.check-code-change-knowledge-coverage
    path: scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh
  - id: rag-rulebook.script.record-knowledge-disposition
    path: scripts/02.rag-rulebook/record-knowledge-disposition/script.sh
-->
# ADR 0023: Require RAG Knowledge Disposition For Code Changes

## Status

Accepted.

## Context

The repo is starting to add platform and core code while also relying on the
RAG/rulebook layer to explain how those layers should be used. If code changes
move faster than source material, rules, selector fixtures, and corpus gaps,
future prompts can retrieve stale or incomplete guidance.

At the same time, `00.chat` must remain portable and standalone. It should not
know about this repo's product, platform, deployment, or RAG/rulebook layers.

## Decision

Knowledge-bearing code changes require an explicit RAG knowledge disposition in
the current chat session log before commit:

- `covered`: source material, rule, derivation, selector, or other evidence was
  updated and listed.
- `no-impact`: the code change does not change retrieval guidance, with a
  reason.
- `deferred-with-gap`: the gap is intentional and a corpus-gap path is listed.

The portable chat commit gate calls only a neutral repository extension hook:
`scripts/repo/commit-gates/script.sh`.

The repository hook owns repo-specific gate selection. The RAG/rulebook layer
owns the RAG knowledge-disposition recorder and validator.

## Consequences

`00.chat` keeps its standalone nature. Repos that do not have a RAG/rulebook
layer do not inherit RAG-specific checks.

Repos that do have knowledge-bearing layers get a deterministic stop before
committing code that would make the RAG layer stale or silent.

Agents must update source material and projection evidence as part of
meaningful layer changes, or explicitly record why no RAG update is needed.
