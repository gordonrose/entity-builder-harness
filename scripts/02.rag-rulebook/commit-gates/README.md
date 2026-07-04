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
- Require a current RAG knowledge disposition when staged code changes affect
  knowledge-bearing runtime, platform, product, infra, or workflow paths.
- Validate governed YAML syntax under RAG/rulebook and deploy roots.
- If recognition sources exist, require and run the recognition-source
  validator.
- If recognition candidates exist, require and run the recognition-candidate
  validator.
- If source-to-rule derivation reports exist, require and run the
  derivation-report validator.
- If retirement records exist, require and run the retirement-record validator
  so removed, renamed, superseded, or retained-retired RAG artifacts remain
  auditable.
- Require and run the corpus-root change detector so deleted or renamed
  governed files have accepted retirement records and changed rule files still
  reach the generated index and chunk set.
- Require and run the source-material coverage checker so non-README source
  Markdown under governed source roots has a structured rule, derivation
  report, or corpus gap outcome.
- If generated recognition sources exist, require and run the generator
  freshness check.
- Require and run the retrieval selector fixture smoke test so policy,
  recognition sources, generated chunks, and context-packet validation remain
  wired together.
- Require and run the retrieval selector evaluation fixture smoke test so
  expected and banned packet behaviors remain pinned.
- Require and run the local runtime build smoke test so index, chunks,
  manifest, and validation-report generation remain wired together.
- Require and run the local runtime freshness smoke test so fresh, missing,
  stale, and corrupt runtime states fail or pass deterministically.
- Require and run the deploy-layer container boundary validator when
  `infra/` exists so Dockerfiles cannot sprawl outside governed image
  directories.
- Require and run the source-material coverage smoke test so orphan source
  material fails deterministically.
- Require and run the retirement-record smoke test so missing prior hashes,
  unresolved references, bad replacement paths, and mismatched review state
  fail deterministically.
- Require and run the corpus-root change smoke test so deleted governed paths
  without retirement records and added orphan sources fail deterministically.
- Require and run the code-change knowledge coverage smoke test so missing
  knowledge disposition fails deterministically.
- Require and run the local context query smoke test so the runtime cache can
  still produce a validated context packet.

## Maintenance Rule

When a new generated RAG/rulebook artifact becomes commit-critical, add its
validator here. Do not add each RAG/rulebook validator directly to the chat
commit script.

## Effects

This command is read-only. It checks generated recognition sources for
freshness and recognition candidates for review-record validity, but does not
rewrite them. It parses YAML syntax, validates derivation reports, and checks
source-material coverage without updating rules, chunks, or evaluations. It
validates retirement records without deleting files or rewriting references. It
does not stage files or create commits, except transient fixture chunks, local
runtime outputs, and temporary smoke-test source files during smoke validation.
