<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.retrieval-selector-policy-system
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: standard
purpose: Define the evolvable policy system for multi-dimensional RAG/rulebook context selection.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
- id: rag-rulebook.schema.retrieval-policy-pack
  path: .agentic/02.rag-rulebook/schemas/retrieval-policy-pack.schema.yml
- id: rag-rulebook.policy.retrieval-selector.v1
  path: .agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml
-->
# Retrieval Selector Policy System

## Purpose

Define how the RAG/rulebook retrieval selector should evolve without burying
selection behavior inside code.

Selector code should execute governed policy packs. It should not be the only
place where prompt interpretation, session metadata trust, corpus selection,
graph expansion, trimming, confidence, or gap behavior is defined.

The policy system exists so context augmentation can become smaller, more
accurate, and more reliable over time while remaining inspectable.

## Mental Model

The selector sits between generated chunks and the final context packet:

```txt
prompt
+ chat/session metadata
+ layer/mode/workflow
+ focused paths
+ corpus ownership
+ rule graph
+ required checks
+ stop conditions
+ token budget
+ confidence thresholds
+ generated chunks
= selected evidence
= validated context packet
```

The selector has two parts:

- engine: deterministic code that reads indexes, chunks, policies, and inputs
- policy pack: versioned instructions that say how dimensions affect selection

The engine should be boring. The policy pack should be where retrieval behavior
is allowed to mature.

The active policy pack is a manifest. Each dimension should live in its own
imported file so the dimension can be reviewed, taught, validated, and evolved
without turning the pack into one large prose document.

## Required Dimensions

Every active selector policy pack must address these dimensions.

| Dimension | Controls | Evolves By |
| --- | --- | --- |
| prompt | How raw user language becomes intent signals and task terms. | Adding task vocabulary, synonyms, disambiguation rules, or prompt red flags. |
| chat/session metadata | How current session, branch, workflow, and recorded metadata influence routing. | Updating trust rules for session fields and continuation state. |
| layer/mode/workflow | Which layer and workflow boundaries constrain retrieval. | Adding new layers, modes, or workflow ownership rules. |
| focused paths | How open files, changed files, and user-named paths narrow retrieval. | Adding path ownership maps and path-to-corpus rules. |
| corpus ownership | Which numbered corpora and subcorpora may provide context. | Adding corpus manifests, subcorpus relationships, or cross-corpus permission rules. |
| rule graph | Which graph edges may expand retrieval beyond the first match. | Adding edge types, hop limits, and expansion priority. |
| required checks | Which checks must survive ranking and trimming. | Adding task-specific or risk-specific checks. |
| stop conditions | Which ambiguity, ownership, or governance gaps block packet readiness. | Adding new stop conditions and gap categories. |
| token budget | How much context can be selected and how trimming behaves. | Tuning budgets per consumer, task risk, and context window. |
| confidence thresholds | When low confidence becomes a gap instead of a guessed answer. | Tuning thresholds by layer, mode, corpus, and task type. |
| validation handoff | Which validator must pass before the packet is usable. | Adding stricter packet, citation, or policy validators. |

Future dimensions may be added when they are versioned and validated. They must
not silently change existing dimension meaning.

Every imported dimension file must define:

- required inputs
- expected actions
- banned actions
- output obligations
- gap or stop conditions
- ranking effects
- validation examples
- allowed change paths

The banned-actions section is not optional. It is how the policy prevents the
selector from turning vague natural language, semantic similarity, or token
trimming into hidden governance bypasses.

## Precedence

When policies conflict, use this order:

1. Stop conditions beat every retrieval score.
2. Explicit session metadata beats inferred prompt meaning when metadata is
   complete and current.
3. Focused paths and artifact ownership beat broad semantic similarity.
4. Corpus ownership boundaries beat cross-corpus convenience.
5. Required checks and mandatory rulesets must survive trimming.
6. Rule graph expansion should be bounded before ranking.
7. Ranking should prefer deterministic matches before semantic/vector recall.
8. Token-budget trimming may remove helpful context, but not required checks,
   blocking stops, citations, or provenance.
9. Low confidence must produce a gap; it must not be hidden behind fluent text.
10. Validation failure means the packet is unusable.

These precedence rules should be duplicated into policy packs so future
selectors can validate that the active pack still honors them.

## Policy Pack Lifecycle

Policy packs are versioned artifacts.

Use these statuses:

- `draft`: proposed behavior that must not drive production retrieval
- `active`: default behavior for a selector version
- `superseded`: replaced by a newer policy pack
- `retired`: no longer valid for new selectors

Every policy pack should include:

- schema version
- policy pack ID
- policy pack version
- status
- selector version
- supported context-packet schema
- supported chunk-set schema
- corpus scope
- change reason
- superseded policy ID when relevant
- dimensions
- precedence
- thresholds
- validation requirements
- examples or smoke fixtures

Policy packs should import dimensions by stable ID and repo-relative path. The
dimension file must identify the policy pack it applies to. Selector code should
compile the pack and its imported dimensions before selecting chunks.

## Evolution Rules

Policy changes are safe when they:

- add vocabulary without changing existing meaning
- add a more specific corpus or path rule
- tighten a stop condition with tests
- reduce context size without dropping mandatory evidence
- add a validation requirement with a migration path

Policy changes need extra review when they:

- lower confidence thresholds
- allow cross-corpus retrieval
- change precedence order
- change required checks or stop-condition severity
- increase token budgets
- introduce semantic or embedding recall before deterministic filters
- change packet readiness behavior

Breaking changes should either create a new policy pack version or a new schema
version.

## Selector Output Requirements

A selector may output an intermediate selection report, but the usable handoff
must be a validated `rag-rulebook/context-packet/v1` packet.

The selector must preserve:

- selected chunk IDs
- citation IDs
- corpus IDs
- artifact IDs
- rule IDs and rule-pack IDs where available
- required checks
- forbidden actions
- stop conditions
- confidence scores
- gaps
- token-budget decisions
- retrieval order
- policy pack ID and version in provenance

## Non-Goals

This standard does not build the selector runtime.

It does not require embeddings, vector storage, reranking models, or a network
service. Those may be added later only after deterministic policy behavior is
defined, validated, and small enough to inspect.
