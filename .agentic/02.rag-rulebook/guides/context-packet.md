<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.guide.context-packet
version: 1
status: active
layer: 02.rag-rulebook
domain: context-packets
disciplines:
- agentic
- architecture
kind: guide
purpose: Teach humans how to understand and use the RAG/Rulebook context-packet contract.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
-->
# Context Packet Guide

## What A Context Packet Is

A context packet is the handoff from the RAG/rulebook service to a consuming
workbench.

It is not the final answer, the final plan, or permission to act. It is the
smallest governed bundle of context the consuming workflow needs before it
decides what to do.

The packet answers five questions:

- What does the user appear to be trying to do?
- Which layer, workflow, and corpus own the relevant rules?
- Which exact chunks, checks, prohibitions, and stop conditions matter?
- Where did each piece of context come from?
- Is anything missing, ambiguous, stale, or too risky to proceed?

## Why It Exists

Without a packet, RAG can become a pile of vaguely relevant text. That makes the
model sound informed while hiding weak retrieval, missing governance, or
conflicting ownership.

The packet makes retrieval auditable. It keeps context augmentation small,
accurate, and explainable.

## How To Read One

Start with `intent`.

Intent translates the user's natural language into a deterministic task shape.
It should say what the task is, how confident the service is, and whether that
classification came from deterministic evidence or inference.

Then read `routing`.

Routing tells the consuming workbench which layer, mode, and workflow should
own the task. If routing is `blocked` or `needs-clarification`, the consumer
should not pretend the packet is ready.

For side-effecting requests, read `action_authorization`.

This field makes permission explicit for actions such as deploy, commit, write,
or destructive work. It should say what action was requested, whether execution
is allowed, and which blocking gaps prevent execution. A consumer should not
infer deployment permission from relevant deploy chunks alone.

Then read `matched_corpora`, `matched_rule_packs`, and `matched_rulesets`.

These fields explain why the service selected a corpus or rule source. They are
the bridge between broad ownership and specific selected chunks.

Then read `selected_chunks`.

These are the only text fragments that should be injected into the consuming
model's working context. Each chunk should have a selection reason and at least
one citation.

Finally read `required_checks`, `forbidden_actions`, `stop_conditions`,
`confidence`, and `gaps`.

These fields say what must be verified, what must not happen, when to stop, and
how much trust to place in the packet.

## Schema Versus Guide

The schema is the machine-readable contract. It defines field names, required
fields, allowed values, validation rules, and a structured `field_guide`.

The guide is the human-readable explanation. It teaches the mental model and
how to reason about a packet.

Do not put the main teaching content only in YAML comments. Comments disappear
when parsed and cannot be indexed or validated reliably. Put concise field
explanations in structured schema fields, and put longer teaching material in
this guide.

## Field Families

`request` preserves the original request and the normalized summary used for
retrieval.

`intent` turns natural language into a deterministic workflow funnel.

`action_authorization` states whether a requested side-effecting action is
allowed, blocked, or not actually an executable intent.

`routing` tells the consumer which layer, mode, and workflow should govern the
task.

`matched_corpora` names the modular corpus packages involved. This prevents the
RAG system from blending harness, product, design-system, deploy, education,
and shared rules into one blurred instruction set.

`matched_rule_packs` and `matched_rulesets` explain which higher-level rule
sources were selected before chunking.

`selected_chunks` carries the actual text sent to the model. This should be
small and cited.

`required_checks` converts retrieved governance into validation obligations.

`forbidden_actions` carries negative rules. This is as important as positive
guidance because it prevents confident but unsafe action.

`stop_conditions` tells the consumer when to pause instead of improvising.

`citations` makes every important packet entry traceable.

`confidence` gives an honest read on the strength of routing and retrieval.

`gaps` names missing or ambiguous knowledge.

Blocking gaps should cite the exact selected chunks that justify the block.
This makes a denial auditable instead of merely descriptive.

`budgets` keeps context small.

`provenance` records how the packet was generated.

## What Good Looks Like

A good packet is small. It selects the few chunks that matter and explains why.

A good packet is cited. Checks, stop conditions, selected chunks, and forbidden
actions point back to source.

A good packet is honest. If intent, ownership, or references are unclear, it
reports a gap instead of filling the gap with model judgment.

A good packet is deterministic first. Semantic recall can help find candidates,
but it should not override path ownership, artifact metadata, graph expansion,
or governance stop conditions.

## What Bad Looks Like

A bad packet includes broad source dumps without explaining why each chunk is
needed.

A bad packet hides uncertainty inside polished prose.

A bad packet mixes domain corpora without naming ownership.

A bad packet contains required checks or forbidden actions without citations.

A bad packet lets a high retrieval score override a blocking stop condition.

A bad packet retrieves deployment evidence but leaves the execution decision
implicit.

## How An LLM Should Use It

Use the packet as evidence and governance, not as a script to blindly execute.

If `routing.status` is `ready`, load the selected workflow and proceed within
the consuming workbench's rules.

If `routing.status` is `needs-clarification`, ask a narrow question or request
missing deterministic input.

If `routing.status` is `blocked`, stop and explain the gap.

If `action_authorization.execution_allowed` is `false`, do not perform the
named side-effecting action even when the selected chunks look relevant.

Use `selected_chunks` as the context payload. Use `citations` when explaining
why a rule applies. Use `required_checks` before claiming work is complete. Use
`forbidden_actions` and `stop_conditions` as hard boundaries.

## Relationship To Future Validators

The current schema is a design contract. A future validator should check that:

- required fields exist
- citation IDs resolve
- action authorization does not allow execution when routing is blocked
- blocking gaps affect routing status
- blocking gaps cite selected evidence chunks when available
- selected token estimates fit the budget
- corpus IDs follow the numbered corpus vocabulary
- selected chunks are cited
- checks, prohibitions, and stop conditions are cited

The validator should report gaps instead of silently repairing the packet.
