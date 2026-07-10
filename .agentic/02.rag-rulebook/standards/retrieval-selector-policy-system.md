<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.retrieval-selector-policy-system
version: 2
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
place where prompt interpretation, request context, session metadata trust,
corpus selection, graph expansion, trimming, confidence, or gap behavior is
defined.

The policy system exists so context augmentation can become smaller, more
accurate, and more reliable over time while remaining inspectable.

## Mental Model

The selector sits between generated chunks and the final context packet:

```txt
prompt
+ request context
+ evidence bundles
+ chat/session metadata
+ prompt-level layer/mode/workflow candidates
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

Prompt interpretation should run for each prompt and be grounded in governed recognition sources. The
selector should not invent nouns, actions, risk words, aliases, or targets from
raw language alone. It should match prompt text against generated and curated
lookup sources, then combine those matches into request context before comparing
them with session, corpus, and graph signals.

Do not classify the chat as one stable layer, mode, or workflow. A chat is the
lifecycle container for branch, worktree, commit-log, metrics, and transcript
state. The selector resolves layer, mode, workflow, and corpus candidates for
the current prompt so it can choose the right context packet. The next prompt
must be resolved again.

## Chunk Purpose And Authority

Selectors must distinguish why a chunk is selected from what authority the
chunk carries.

Chunk purpose answers why the chunk is useful for the prompt. Valid purposes
include binding rules, source explanation, ADR decisions, plan milestones,
guides, artifact summaries, and retrieval profiles.

Chunk authority answers what the consumer may do with the chunk. Valid
authority families include execution authority, explanation support, decision
history, implementation planning, and orientation.

Explanation-support chunks can teach a human and can help an agent explain
source-backed rationale. They cannot authorize side effects. For write, commit,
deploy, destructive, or cloud-mutating requests, the selector may include
explanation chunks as background, but readiness and authorization must come
from governed workflows, explicit approvals, structured rules, required checks,
stop conditions, and execution-authority chunks.

## Required Dimensions

Every active selector policy pack must address these dimensions.

| Dimension | Controls | Evolves By |
| --- | --- | --- |
| prompt | How raw user language becomes intent signals and task terms. | Adding task vocabulary, synonyms, disambiguation rules, or prompt red flags. |
| request context | How the current prompt, exact identifiers, recognized concepts, and side-effect class become the retrieval target for this request. | Adding request forms, side-effect classes, expected evidence bundles, or confidence penalties. |
| evidence bundles | Which canonical evidence families are required for recognized question categories. | Adding question categories, evidence-family terms, canonical source paths, or missing-evidence confidence penalties. |
| chat/session metadata | How current session, branch, worktree, context-packet references, and recorded metadata preserve provenance, continuity, and execution safety. | Updating trust rules for session fields, context-packet continuity, and continuation state. |
| layer/mode/workflow | Which prompt-level layer and workflow boundaries constrain retrieval. | Adding new layers, modes, or workflow ownership rules. |
| corpus ownership | Which numbered corpora and subcorpora may provide context. | Adding corpus manifests, subcorpus relationships, or cross-corpus permission rules. |
| rule graph | Which graph edges may expand retrieval beyond the first match. | Adding edge types, hop limits, and expansion priority. |
| required checks | Which checks must survive ranking and trimming. | Adding task-specific or risk-specific checks. |
| stop conditions | Which ambiguity, ownership, or governance gaps block packet readiness. | Adding new stop conditions and gap categories. |
| token budget | How much context can be selected and how trimming behaves. | Tuning budgets per consumer, task risk, and context window. |
| confidence thresholds | When low confidence becomes a gap instead of a guessed answer. | Tuning thresholds by layer, mode, corpus, and task type. |
| validation handoff | Which validator must pass before the packet is usable. | Adding stricter packet, citation, or policy validators. |
| chunk purpose and authority | Which chunk purposes are eligible for the prompt and which selected chunks carry binding authority. | Adding purpose labels, authority labels, side-effect restrictions, or intent-specific ranking rules. |

Future dimensions may be added when they are versioned and validated. They must
not silently change existing dimension meaning.

Typed request anchors, such as active editor files, web UI routes, selected
entities, user/org context, or journey state, are intentionally deferred until
clients can provide governed provenance, freshness, and trust levels. Until
then, exact paths should appear in the prompt text and flow through generated
recognition sources.

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

The prompt dimension must also define recognition sources, extraction rules,
term categories, and classification outputs. That keeps prompt parsing
inspectable and fast enough to run before retrieval selection.

## Runtime Policy Compilation

Runtime selector behavior must be compiled from governed inputs, not hidden in
selector code.

The compiled selector configuration should be derived from:

- the active retrieval policy pack
- imported policy dimensions
- generated recognition sources
- curated recognition sources
- corpus manifests and ownership maps
- rulebook index and graph metadata
- enabled selector feature flags

Hard-coded precedence tables, intent resolution maps, evidence bundle mappings,
or corpus-routing exceptions are allowed only in prototype fixture scripts and
must be treated as temporary. A production selector, local runtime, hosted
service, or MCP-facing context API must load compiled policy output instead of
duplicating policy behavior in code.

Adding a question category, evidence bundle, request form, corpus mapping, or
confidence rule should require changing governed YAML and regenerated compiled
policy. It should not require editing selector runtime code unless the schema
or engine capability changes.

Compiled policy output must preserve enough provenance for validators and A/B
evaluation to explain which policy pack, dimensions, recognition sources, and
generated inputs produced a selection decision.

## Precedence

When policies conflict, use this order:

1. Stop conditions beat every retrieval score.
2. Explicit request context beats session continuity for retrieval target
   selection.
3. Evidence bundles define required evidence families for recognized question
   categories.
4. Side-effecting requests require execution-authority evidence for readiness
   and may use explanation-support chunks only as background.
5. Session metadata governs provenance, continuity, branch/worktree ownership,
   and execution safety.
6. Focused paths and artifact ownership beat broad semantic similarity.
7. Corpus ownership boundaries beat cross-corpus convenience.
8. Required checks and mandatory rulesets must survive trimming.
9. Rule graph expansion should be bounded before ranking.
10. Ranking should prefer deterministic matches before semantic/vector recall.
11. Low confidence must produce a gap; it must not be hidden behind fluent text.
12. Validation failure means the packet is unusable.

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
- selected chunk purposes
- selected chunk authorities
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
