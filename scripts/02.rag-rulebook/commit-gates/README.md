<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.commit-gates.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: validation
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the RAG/rulebook commit-boundary validation gate.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.commit-gates
  path: scripts/02.rag-rulebook/commit-gates/script.sh
-->
# RAG/Rulebook Commit Gates

`script.sh` runs the RAG/rulebook checks that must pass before a chat task
commit when `.agentic/02.rag-rulebook` exists in the repository.

## Purpose

Chat owns the commit boundary. The RAG/rulebook layer owns its own validation.
This command is the bridge between those responsibilities: chat calls one
layer-level gate, and this gate decides which RAG/rulebook validators are
required.

## Current Checks

- Validate the current retrieval selector policy pack.
- If recognition sources exist, require and run the recognition-source
  validator.

## Maintenance Rule

When a new generated RAG/rulebook artifact becomes commit-critical, add its
validator here. Do not add each RAG/rulebook validator directly to the chat
commit script.

## Effects

This command is read-only. It does not generate recognition sources, rebuild
chunks, update indexes, stage files, or create commits.
