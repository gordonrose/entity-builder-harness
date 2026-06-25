<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.recognition-source-system
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: standard
purpose: Define governed lookup sources used to recognize prompt intent before retrieval selection.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.schema.recognition-source
  path: .agentic/02.rag-rulebook/schemas/recognition-source.schema.yml
- id: rag-rulebook.policy.retrieval-selector.v1.dimension.prompt
  path: .agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/prompt.yml
-->
# Recognition Source System

## Purpose

Define how a selector recognizes what a user prompt is talking about before it
chooses retrieval chunks.

Recognition sources are lookup vocabularies. They help turn raw language into
structured signals such as artifact IDs, file paths, schemas, layers, workflows,
action verbs, risk words, and aliases.

Recognition sources are not context chunks. Chunks are evidence the LLM may
read. Recognition sources are inputs the selector uses to understand the
request well enough to choose evidence.

## Runtime Rule

Runtime recognition must be fast.

Prompt-time code should use prebuilt recognition sources or compiled indexes.
It should not rebuild artifact inventories, scan every file, or perform
expensive semantic parsing on every user message.

Generation and validation happen offline, during governed maintenance or
commit-time checks. Runtime lookup should be a small deterministic match step.

## Ownership

The RAG/Rulebook layer owns the reusable recognition-source machinery:

- recognition-source schemas
- source generation rules
- source validation rules
- compiled recognition indexes
- curated vocabulary governance

The chat layer may consume recognition sources opportunistically. Chat startup
must keep its deterministic fallback classifier so repositories without
`02.rag-rulebook` still work.

<!-- deterministic-check: allow reason="standard defines optional future chat consumption policy; executable bridge must still be implemented by a governed script or workflow change" -->
If `02.rag-rulebook` exists and a compiled recognition source is available,
chat may use it after the fast deterministic classifier, especially when
classification is ambiguous, unknown, or high risk.

## Source Kinds

Generated sources come from repo artifacts and should usually be refreshed by
script:

- artifact IDs
- file paths
- schema names
- corpus IDs
- layer names
- workflow names
- rule IDs
- rule-pack IDs

Curated sources are human-authored and need tighter review:

- action verbs
- risk words
- domain nouns
- aliases
- synonyms
- stop-condition words
- check names

Generated sources are safer because they are derived from committed artifacts.
Curated sources are powerful because they teach language, but they can drift or
over-classify if not reviewed.

## Recognition Flow

Use this order:

1. Normalize prompt text into tokens and simple phrases.
2. Match exact paths, artifact IDs, schema names, corpus IDs, workflow names,
   and rule IDs first.
3. Match curated action, risk, domain, and alias terms second.
4. Compare prompt-derived signals with session metadata.
5. Report conflicts or low confidence as gaps instead of silently changing
   routing.

Exact governed identifiers should beat broad natural language.

## Maintenance Rules

Each recognition source should state:

- source ID
- source kinds
- generation mode
- owner layer
- term categories
- match priority
- used-by dimensions
- refresh policy
- validation rules

Generated sources should identify the command or artifact inventory that
produced them.

Curated sources should identify why the vocabulary exists and which examples or
fixtures prove it is safe.

## Banned Behavior

Recognition sources must not:

- override complete session metadata by themselves
- classify a prompt from one vague word
- use broad aliases to cross corpus boundaries without supporting evidence
- hide prompt/session conflicts
- require a slow full-repo scan during prompt-time lookup

## First Use

The prompt retrieval dimension should use recognition sources to explain how it
finds:

- nouns and domain terms
- action verbs
- file names and paths
- artifact IDs
- schemas
- risks and stop words

The first generated source should probably come from artifact metadata and file
paths. Curated action/risk vocabulary should come later, with examples.
