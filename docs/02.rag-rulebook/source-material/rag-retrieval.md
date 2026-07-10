<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.source-material.rag-retrieval
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: source-material
purpose: Record the repo-level RAG retrieval runtime path, prompt payloads, context-packet assembly model, source-of-truth hierarchy, intent handling, and update expectations before structured rulebook derivation.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.corpus-gap.02-rag-rulebook.rag-retrieval-source-of-truth
  path: .agentic/02.rag-rulebook/corpus-gaps/02.rag-rulebook/rag-retrieval-source-of-truth.yml
- id: rag-rulebook.source-projections.v1
  path: .agentic/02.rag-rulebook/source-projections/v1.yml
-->
# RAG Retrieval Source Of Truth

## Purpose

This document is the human-readable source material for how this repository's
RAG and rulebook system works now, how it should keep evolving, and why the
pieces are shaped this way.

It is meant to be printed, studied, reviewed, updated, and then projected into
structured rules, generated chunks, selector fixtures, and context-packet
behavior. It records the model that future agents should use when they need to
teach, decide, plan, or implement based on repo intent.

This file is not itself the runtime. The runtime proof comes from structured
rules, generated recognition sources, generated indexes, generated chunks,
selector evaluations, freshness checks, and validated context packets.

## Core Decision

RAG retrieval in this repo should be source-of-truth driven.

Durable knowledge starts in reviewed source material, governed standards,
workflows, schemas, rules, ADRs, and artifact metadata. The retrieval pipeline
turns that repo evidence into small, cited context packets for the current
prompt.

The model is:

```text
repo source of truth
-> artifact metadata index
-> generated and curated recognition sources
-> rulebook index
-> generated chunks and retrieval profiles
-> retrieval selector
-> validated context packet
-> agent action under the current workflow gates
```

The context packet helps an agent reason. It does not grant permission to edit,
commit, deploy, call cloud APIs, or bypass governance.

## Actual Runtime Path

The current local and hosted RAG path is deterministic. It does not run live
embeddings, call a vector database, perform network retrieval, or let the
model browse files at query time.

The current path is:

```text
source files and metadata
-> build-local-runtime
-> .cache/02.rag-rulebook/
   -> rulebook-index.json
   -> rulebook-chunks.json
   -> compiled-retrieval-policy.json
   -> manifest.json
   -> validation-report.json
-> /context/query or query-local-context
-> check-runtime-freshness
-> generate-retrieval-selector-fixture
-> validate-context-packet
-> full or compact context packet
```

The important point is that query time reads a built runtime package. Query
time should not quietly rebuild the world, fetch remote facts, or accept stale
runtime files as good enough.

`build-local-runtime` currently:

1. Validates the retrieval policy pack.
2. Validates recognition sources.
3. Validates recognition candidates.
4. Refreshes generated recognition sources if they are stale or missing.
5. Generates a rulebook index.
6. Validates the rulebook index.
7. Generates rulebook chunks.
8. Compiles retrieval policy.
9. Writes a manifest and validation report with source fingerprints.

The runtime cache records fingerprints for retrieval policy, recognition
sources, recognition candidates, corpus gaps, source material, structured
rules, source derivations, source projections, index inputs, chunk generation,
and validation machinery. Freshness checks compare the current repo against
those fingerprints before any packet is trusted.

## Prompt Payloads

The HTTP service accepts `POST /context/query`.

The preferred payload shape is:

```json
{
  "requestText": "Explain how /context/query assembles a RAG context packet for docs/02.rag-rulebook/source-material/rag-retrieval.md.",
  "format": "compact",
  "maxChunks": 6,
  "session": {
    "id": "chat_2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after-531603960",
    "branch": "chat/2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after",
    "worktree": "/tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after-531603960",
    "latestContextPacketId": "packet.selector-fixture.previous",
    "latestContextPacketRoutingSummary": "Previous prompt routed to 02.rag-rulebook discovery."
  }
}
```

The same payload may use snake case names such as `request_text`,
`max_chunks`, `session_id`, `previous_packet_id`, and
`latest_context_packet_id`. Prefer camel case for the service examples and
keep CLI examples in flag form.

`requestText` is required. It is the current prompt and primary retrieval
signal. Exact paths should be placed in `requestText`, not in retired
`focusedPaths` fields.

`format` may be `compact` or `full`. The HTTP service defaults to `compact`
because normal consumers usually need selected evidence, not every selector
diagnostic. The CLI defaults to `full` because local debugging often needs
provenance and selector trace.

`maxChunks` must be between 3 and 12. Smaller packets are easier for agents to
use and audit; larger packets should be requested only when the task genuinely
needs more evidence.

`session` is provenance, not authority. `id`, `branch`, `worktree`, previous
packet ID, and previous routing summary help the packet explain continuity.
Client-supplied `session.layer`, `session.mode`, and `session.workflow` are
legacy routing hints and should normally be omitted. The HTTP surface never
marks those hints trusted.

The equivalent local CLI query is:

```bash
bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --request-text "Explain how /context/query assembles a RAG context packet for docs/02.rag-rulebook/source-material/rag-retrieval.md." \
  --session-id chat_2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after-531603960 \
  --session-branch chat/2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after \
  --session-worktree /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after-531603960 \
  --previous-packet-id packet.selector-fixture.previous \
  --previous-routing-summary "Previous prompt routed to 02.rag-rulebook discovery." \
  --max-chunks 6 \
  --format compact \
  --pretty
```

Only a governed local session resolver should add `--trust-session-routing`,
and only after proving session ownership. That path requires session ID,
branch, worktree, layer, mode, and workflow. It exists for local governed
tools, not for arbitrary HTTP clients.

## HTTP Service Behavior

The service exposes:

```text
GET  /health
GET  /version
POST /context/query
```

`/health` checks whether the runtime cache exists and is fresh.

`/version` reports service name, service version, commit identity, start time,
and runtime file presence.

`/context/query`:

1. Requires JSON content.
2. Requires `requestText` or `request_text`.
3. Rejects `focusedPaths`, `focused_paths`, `noFocusedPaths`, and
   `no_focused_paths` because typed request anchors are not governed yet.
4. Validates `format` and `maxChunks`.
5. Validates optional session fields for size, control characters, and basic
   shape.
6. Requires bearer authorization when `RAG_SERVICE_TOKEN` is configured.
7. Delegates to `scripts/02.rag-rulebook/query-local-context/script.sh`.

The service is a small HTTP shell around the deterministic local runtime. It
should not grow an independent retrieval engine. If the HTTP path and CLI path
answer differently for the same runtime, that is a bug.

## Runtime Files

The local runtime directory is `.cache/02.rag-rulebook` by default.

The important files are:

- `rulebook-index.json`: corpus packages, artifacts, rules, rule packs, graph
  edges, source references, path mappings, chunk candidates, unresolved
  references, diagnostics, and provenance.
- `rulebook-chunks.json`: selector-facing chunk objects and citations derived
  from the index.
- `compiled-retrieval-policy.json`: the active retrieval policy after
  dimensions and policy pack validation are compiled into selector-ready JSON.
- `manifest.json`: runtime identity, source fingerprints, output hashes,
  counts, and constraints.
- `validation-report.json`: evidence that the runtime inputs passed validation
  when the cache was built.

The manifest matters because it lets a caller ask: "Did this packet come from
the same source material, rules, recognition sources, and selector machinery I
am editing now?"

## Chunk Shape

Chunks are the text units the selector can place in a packet.

A chunk currently looks like this:

```json
{
  "chunk_id": "chunk.example.rag-rulebook.query-local-context.summary",
  "corpus_id": "corpus.02.rag-rulebook",
  "artifact_id": "artifact.rag-rulebook.script.query-local-context",
  "artifact_ref": "artifact.rag-rulebook.script.query-local-context",
  "source_path": "scripts/02.rag-rulebook/query-local-context/script.sh",
  "content_kind": "artifact-summary",
  "section_path": "artifact.summary",
  "rule_ids": [],
  "rule_refs": [],
  "pack_refs": [],
  "content": "Query the local RAG/rulebook runtime cache for a validated context packet.",
  "rank": 12,
  "token_estimate": 18,
  "selection_reason": "Generated from a structured rulebook index chunk candidate.",
  "citation_ids": [
    "source.rag-rulebook.script.query-local-context"
  ],
  "source_ref_ids": [
    "source.rag-rulebook.script.query-local-context"
  ],
  "retrieval_profile": {
    "retrieval_roles": [
      "runtime-query"
    ],
    "answers_questions_about": [
      "how RAG queries the built runtime",
      "how context packets are produced"
    ],
    "produces": [
      "context packet",
      "compact context packet"
    ],
    "consumes": [
      "local runtime cache",
      "request text",
      "session metadata"
    ],
    "validates": [
      "runtime freshness",
      "context packet"
    ]
  }
}
```

Exact IDs vary by generated index and source path. The fields above are the
important contract. A chunk must be small enough to select, cite, and trim, but
complete enough that an agent can understand why it was included.

`content_kind` is important because the selector treats chunk families
differently. Current families include artifact summaries, rules, required
checks, source excerpts, retrieval profiles, and gap evidence. Required
evidence can be boosted so it survives packet trimming.

## Context Packet Shape

A full packet uses `rag-rulebook/context-packet/v1`.

The required field families are:

```json
{
  "schema": "rag-rulebook/context-packet/v1",
  "packet_id": "packet.selector-fixture.example",
  "generated_at": "2026-07-10T12:00:00Z",
  "request": {},
  "intent": {},
  "action_authorization": {},
  "selector_trace": {},
  "routing": {},
  "matched_corpora": [],
  "matched_rule_packs": [],
  "matched_rulesets": [],
  "selected_chunks": [],
  "required_checks": [],
  "forbidden_actions": [],
  "stop_conditions": [],
  "citations": [],
  "confidence": {},
  "gaps": [],
  "budgets": {},
  "provenance": {}
}
```

The compact packet uses `rag-rulebook/context-packet-compact/v1`. It is a
derived view of the same validated full packet:

```json
{
  "schema": "rag-rulebook/context-packet-compact/v1",
  "source_schema": "rag-rulebook/context-packet/v1",
  "packet_id": "packet.selector-fixture.example",
  "request": {
    "raw_text": "Explain how /context/query assembles a RAG context packet.",
    "normalized_summary": "Generate a deterministic retrieval selector fixture from governed policy, request context, recognition sources, session safety metadata, and chunks.",
    "open_artifact_ids": [
      "artifact.rag-rulebook.script.query-local-context"
    ],
    "previous_packet_id": "packet.selector-fixture.previous"
  },
  "intent": {
    "id": "intent.explanation.question",
    "mode": "discovery",
    "layer": "02.rag-rulebook",
    "workflow": ".agentic/02.rag-rulebook/workflows/default.md",
    "confidence": 0.91
  },
  "routing": {
    "layer": "02.rag-rulebook",
    "mode": "discovery",
    "workflow": ".agentic/02.rag-rulebook/workflows/default.md",
    "status": "ready",
    "classification_source": "request-context-plus-recognition-sources",
    "scope": "prompt"
  },
  "selected_chunks": [
    {
      "rank": 1,
      "chunk_id": "chunk.example.rag-rulebook.query-local-context.summary",
      "corpus_id": "corpus.02.rag-rulebook",
      "artifact_id": "artifact.rag-rulebook.script.query-local-context",
      "source_path": "scripts/02.rag-rulebook/query-local-context/script.sh",
      "section_path": "artifact.summary",
      "retrieval_score": 1.0,
      "token_estimate": 18,
      "selection_reason": "Selected by deterministic retrieval-selector fixture using request context, recognition-source matches, and session safety context.",
      "citation_ids": [
        "source.rag-rulebook.script.query-local-context"
      ],
      "rule_ids": [],
      "content": "Query the local RAG/rulebook runtime cache for a validated context packet."
    }
  ],
  "citations": [
    {
      "id": "source.rag-rulebook.script.query-local-context",
      "corpus_id": "corpus.02.rag-rulebook",
      "artifact_id": "artifact.rag-rulebook.script.query-local-context",
      "source_path": "scripts/02.rag-rulebook/query-local-context/script.sh",
      "source_type": "source",
      "source_ref": "source.rag-rulebook.script.query-local-context"
    }
  ],
  "gaps": [],
  "required_checks": [],
  "forbidden_actions": [],
  "stop_conditions": [],
  "budgets": {
    "max_context_tokens": 6000,
    "selected_context_tokens": 1200
  },
  "debug": {
    "full_packet_available_with": "--format full",
    "selector_trace_available_in_full_packet": true,
    "selector_strategy_id": "retrieval-selector.v1",
    "selector_stage_statuses": []
  },
  "packet_summary": {
    "selected_chunk_count": 6,
    "citation_count": 6,
    "gap_count": 0,
    "required_check_count": 1,
    "stop_condition_count": 1
  }
}
```

The exact IDs and chunks depend on the built runtime and request text. The
shape is stable: selected chunks carry the content to inject; citations explain
where it came from; checks, forbidden actions, stop conditions, and gaps tell
the agent what must happen or must not happen next.

## How A Context Packet Is Assembled

The selector currently assembles a packet in this order:

1. Load the compiled retrieval policy.
2. Validate compiled policy provenance.
3. Load generated chunks.
4. Match prompt text against recognition sources.
5. Match trusted local session metadata against recognition sources only when
   the governed caller explicitly uses trusted session routing.
6. Resolve intent forms before deciding whether a side-effecting action is
   blocked.
7. Resolve prompt-level route from request context and recognition matches.
8. Build allowed corpus IDs from recognition matches, trusted local routing
   hints, and matching corpus gaps.
9. Add required evidence paths from recognition candidates, evidence bundles,
   generated retrieval profiles, question frames, and matched corpus gaps.
10. Rank all chunks using deterministic path, artifact, corpus, rule,
    recognition-source, content-kind, and token signals.
11. Filter candidates by allowed corpus IDs and required evidence paths when
    the filter still leaves enough candidates.
12. Add graph-expanded related rule paths from artifact-summary signals.
13. Preserve required evidence chunks and required source paths.
14. Prefer required-check, rule, and artifact-summary coverage where
    available.
15. Select between 3 and `maxChunks` chunks.
16. Attach citations for selected chunks.
17. Derive required checks from selected required-check chunks, or add the
    packet validator check when no required-check chunk is selected.
18. Add gaps for prompt/session conflicts, missing recognition matches,
    low-confidence prompts, missing side-effect session ownership, planned
    corpus gaps, and missing evidence bundles.
19. Enrich gaps with selected evidence chunk IDs and citation IDs when
    possible.
20. Compute confidence, budgets, selector trace, provenance, and action
    authorization.
21. Validate the packet against the generated chunk set before output.

This is why the packet is more than a ranked search result. It contains
selected evidence, but it also contains the safety and audit information needed
to decide whether the agent can continue.

## How Ranking Currently Works

The selector scoring is deterministic and weighted.

It starts by tokenizing the prompt and recognition matches. Then it scores each
chunk against the prompt, recognition matches, source path, artifact ID, rule
IDs, corpus ID, content kind, and intra-source rule fields.

Important current weights and behaviors:

- Exact artifact IDs and exact file paths are strong signals.
- Corpus IDs, rule IDs, and rule-pack IDs are stronger than broad words.
- Prompt matches count more than session metadata.
- Example-context matches are weaker than real prompt targets unless they are
  exact IDs or paths.
- Trusted session corpus adds a small boost only when the caller has proven
  session ownership.
- `required-check`, `rule`, `artifact-summary`, and `retrieval-profile` chunks
  get content-kind boosts for matching prompt terms.
- Required chunk IDs and required source paths get a large preservation boost
  before trimming.
- The final order is score first, source rank second, chunk ID third.

The goal is not semantic cleverness. The goal is predictable retrieval that a
human can debug from the selected chunks and selector trace.

## Why The System Works This Way

The current design optimizes for governed, auditable context instead of
maximal recall.

It uses a runtime cache so one query cannot accidentally change the corpus
while another query is reading it.

It uses source fingerprints so stale packets are rejected instead of silently
mixing old chunks with new rules.

It uses recognition sources so human terms, exact paths, layers, workflows,
and intent forms can become deterministic retrieval signals.

It uses chunks instead of full files so the model receives only the few pieces
of evidence needed for the prompt.

It uses citations so every selected chunk, check, gap, and stop condition can
be traced back to a repo source.

It uses prompt-level routing because a single chat can move from teaching, to
planning, to implementation, to commit handoff. The chat lifecycle is not the
same thing as the current prompt's retrieval route.

It uses action authorization because relevant evidence is not permission.
Deployment, commits, destructive git, cloud actions, and broad edits still
belong to their owning workflows and approval gates.

## Current Limitations

This repo's current RAG runtime is deterministic and local-first. It is not yet
a production semantic retrieval system.

Current limitations include:

- no live embeddings
- no vector database
- no independent HTTP retrieval engine
- no governed typed request anchors beyond prompt text
- no trusted HTTP session-routing path
- source-material-only coverage remains a gap until rules are derived
- compact packets intentionally hide full selector trace details
- generated chunks come from structured index candidates, not arbitrary
  markdown splitting
- runtime identity is only as strong as the build manifest, fingerprints, and
  deployed commit/image metadata supplied to the caller

## Source Of Truth Hierarchy

When sources disagree, prefer the more governed and more specific source.

The rough hierarchy is:

1. Active workflows, standards, schemas, and executable gates under
   `.agentic/` and `scripts/`.
2. Structured corpus rules under `docs/**/rules/`.
3. Accepted ADRs and accepted review records.
4. Governed source material under `docs/**/source-material/`.
5. Source projection manifests, derivation reports, corpus gaps, and retrieval
   selector evaluations.
6. Artifact metadata headers and generated artifact indexes.
7. Commit logs as session evidence, not as the final rulebook.
8. Plans as migration state, not permanent truth unless promoted into source
   material, rules, ADRs, standards, or workflows.

Commit logs are valuable evidence for what was decided during a chat. A durable
architecture or retrieval decision should not live only in a commit log. If a
decision changes how RAG should retrieve, rank, chunk, cite, teach, plan, or
block work, it should be promoted into source material, structured rules, an
ADR, a standard, a workflow, or an explicit corpus gap.

## Repo Layers And Corpus Ownership

The RAG layer does not own every topic. It owns retrieval machinery and context
delivery.

- `00.chat` owns chat lifecycle, worktrees, commit logs, transcript metadata,
  chat refresh, local promotion, and git handoff behavior.
- `01.harness` owns artifact metadata, validation, harness standards,
  governed scripts, agent contracts, and repo process primitives.
- `02.rag-rulebook` owns corpus packaging, recognition sources, retrieval
  policy, rulebook indexes, chunks, context packets, selector evaluations,
  source-to-rule derivation, and RAG service contracts.
- `03.product` owns product and runtime contract guidance, including
  `packages/core/` and `platform/contracts/` surfaces.
- `04.deploy` owns deployment source material, deploy rules, AWS runtime
  boundaries, readiness, provenance, rollback, and deploy stop conditions.
- `05.education` owns teaching outputs that are derived from repo work.
- `06.shared` owns shared process standards and cross-layer primitives.

RAG should retrieve the owning corpus instead of flattening all layers into one
instruction pile. A platform prompt should not be answered from deploy-only
rules unless deployment is actually part of the request. A chat lifecycle
prompt should not use RAG internals as authority for git behavior unless the
question is about the RAG service's relationship to chat lifecycle.

## Source Material And Rule Projection

Source material is human-authored corpus input. It is allowed to explain,
teach, frame tradeoffs, and name unresolved questions.

Structured YAML rules are projected from source material after review. They
are more compact, testable, and chunkable than prose. They should carry
`source_derivation` provenance so the repo can prove which source material and
source hash produced each rule.

The active registry for source-to-rule relationships is:

```text
.agentic/02.rag-rulebook/source-projections/v1.yml
```

Every governed source-material markdown file should be declared there as
active, planned, or retired. If source exists but the rule projection is not
ready, the repo should name a corpus gap instead of pretending coverage is
complete.

## Artifact Metadata And Retrieval Profiles

`agentic-artifact/v2` headers are the human-authored identity and governance
contract for repo artifacts.

Headers should answer stable questions such as:

- What is this artifact?
- Which layer owns it?
- Which domain and discipline does it belong to?
- What kind of artifact is it?
- What is its purpose?
- Which artifacts use it?
- Is it portable?

Headers should not become hand-authored RAG prompt engineering for every file.
RAG-specific retrieval profiles should be generated from headers, paths,
artifact kind, purpose, effects, relationships, neighboring artifacts, and
stable script or rule roles.

The target flow is:

```text
agentic-artifact/v2 header
-> artifact metadata index
-> generated recognition source terms
-> generated retrieval profile
-> retrieval-profile chunk
-> selector-ranked context packet
```

If generated profiles cannot recover an important fact, first decide whether
the fact is useful outside RAG. If it is generally useful, consider extending
artifact metadata. If it is only a retrieval hint, derive it in RAG-owned
generators or add a recognition candidate.

## Recognition Sources

Recognition sources help the selector identify relevant artifacts, layers,
corpora, workflows, risks, actions, and question shapes.

Generated recognition sources come from repo facts such as artifact metadata,
routing policy, workflow files, corpus ownership, and rules. They should be
regenerated and freshness-checked, not hand-edited.

Curated recognition sources exist for reviewed human-language terms, aliases,
actions, risks, intent forms, and question categories. Curated terms should
not override ownership, stop conditions, or validation. They should help the
selector notice the right evidence and then let governed rules decide what is
safe.

## Rulebook Index And Chunks

The rulebook index describes the corpus graph: artifacts, rule roots, source
roots, corpus packages, source projections, generated retrieval profiles, and
relationships between them.

Chunks are the selector-facing units of evidence. A good chunk is small enough
to fit a context packet, but complete enough to carry meaning with citations.

Chunk families include:

- structured rule chunks
- source-derivation and provenance chunks
- retrieval-profile chunks
- corpus-gap chunks
- required-check chunks
- stop-condition chunks
- context-packet and schema guidance chunks

Do not rely on long undifferentiated file dumps when a smaller cited chunk can
answer the prompt.

## Intent And Question Handling

The selector should treat every prompt as current intent, not as a permanent
classification of the chat.

Useful intent families include:

- teach or explain
- decide or compare options
- plan a change
- implement an approved change
- review or audit
- retrieve context
- execute deploy or other side-effecting work

The same chat can move between these intents. Session metadata gives
provenance, continuity, branch/worktree ownership, and execution-safety
context. It should not silently override the current prompt.

Explicit request text, exact paths, and current side-effect intent should beat
old chat continuity when choosing retrieval evidence.

## Example Context Deprioritization

Prompts often include examples. Example paths and artifact IDs are useful
evidence, but they are weaker than the actual request target.

Paths, IDs, and schemas inside phrases such as `e.g.`, `i.e.`, `for example`,
or `such as` should be classified as illustrative context. They may be kept for
provenance, but they should not become primary target anchors, corpus-gap
seeds, or broad ranking signals unless the rest of the request confirms that
they are the real target.

This protects agents from overfitting to an example while missing the actual
question.

## Context Packet Contract

A context packet is the handoff from RAG to the consuming agent.

It should include:

- prompt-level route and confidence
- matched corpora
- selected chunks with citations
- required checks
- forbidden actions
- stop conditions
- gaps
- token budget and trimming evidence
- selector trace or compact trace
- session provenance when supplied

The packet should be validated before use. If validation fails, the caller
should receive a gap, not a best-effort pile of context.

The packet is evidence for the next agent step. The owning workflow still
controls edits, commits, deploys, approvals, and destructive actions.

## Teaching, Planning, And Decision Behavior

For teaching prompts, retrieve concept-defining source material, guides,
rules, and compact examples. Prefer a plain mental model first, then exact
paths and checks.

For planning prompts, retrieve ownership rules, workflow gates, source
material, active plans, corpus gaps, and required checks. The output should
separate what is already governed from what needs a new gap, rule, workflow, or
approval.

For decision prompts, retrieve the narrow rule families, ADRs, source material,
and known gaps that explain the tradeoff. The output should name the decision
owner and the evidence boundary.

For implementation prompts, retrieve the exact workflow, standards, scripts,
rules, and checks required for that layer. Do not let broad semantic recall
override deterministic ownership or stop conditions.

For review prompts, retrieve the current contract, tests, gates, expected
failure modes, and prior corpus gaps. Findings should cite repo evidence.

## Gaps And Stop Conditions

RAG should surface gaps instead of inventing missing authority.

Use gaps when:

- source material exists but structured rules are missing
- chunks or selector fixtures are missing
- corpus ownership is ambiguous
- the prompt asks for side effects not governed by the selected workflow
- hosted or local runtime freshness cannot be proven
- auth, deployment, data-boundary, or audit evidence is missing

Use stop conditions when the next action would be unsafe without resolving the
gap. Planning and explanation can often continue with visible gaps. Execution,
deployment, destructive git, or broad mutation should stop when required
governance is missing.

## Freshness And Runtime Identity

Local and hosted RAG should prove freshness before returning usable context.

Freshness should account for:

- source material
- structured rules
- source projections
- recognition sources
- retrieval policy
- corpus gaps
- generated indexes
- generated chunks
- selector fixtures when behavior changes

Hosted RAG also needs runtime identity evidence: service version, image digest
or runtime artifact identity, repo commit, corpus package hash, index/chunk
hash, compiled policy hash, and recognition-source hash. Without that, callers
cannot tell whether hosted context matches the repo state they are editing.

## Evaluation Expectations

RAG behavior should be tested with retrieval selector fixtures.

Good fixtures assert:

- expected corpora
- expected selected chunk families
- expected citations
- required checks
- required gaps or stop conditions
- banned corpora or chunks
- confidence and budget behavior

Fixtures should cover real prompt shapes, not only idealized exact-path
queries. A healthy fixture set includes teaching, planning, decision,
implementation, review, cross-session, low-confidence, and misleading-example
prompts.

When a retrieval miss exposes a durable knowledge gap, update source material,
rules, recognition candidates, curated recognition sources, generated profile
logic, or selector fixtures. Do not hide misses with one-off prompt wording.

## Update Rules

Keep this source material current when:

- artifact metadata semantics change
- generated retrieval-profile logic changes
- recognition-source ownership changes
- retrieval policy dimensions change
- rulebook index or chunk generation changes
- context packet schema changes
- hosted/local provider behavior changes
- source-material projection rules change
- commit-log audit finds RAG decisions that live only in session history

When this file changes, rerun source-material coverage and source-projection
checks. If the change affects structured rules or retrieval behavior, create or
update a derivation report, structured rules, selector fixtures, generated
sources, generated chunks, and corpus gaps as needed.

## Current Coverage Status

This document records the current RAG retrieval mechanics, payload examples,
context-packet assembly model, intended governance direction, and source of
truth hierarchy.

The immediate coverage state is source-material present with a corpus gap for
rule derivation. Structured rule projection, accepted derivation report,
generated chunks derived from this source, and selector evaluations for this
specific source are still pending.

Until those outputs exist, this document should be used as source evidence and
study material, not as proof that runtime RAG behavior is complete.
