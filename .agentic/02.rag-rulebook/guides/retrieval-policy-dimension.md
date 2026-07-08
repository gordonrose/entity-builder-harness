<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.guide.retrieval-policy-dimension
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: guide
purpose: Teach humans how to read and author imported retrieval policy dimensions.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.schema.retrieval-policy-dimension
  path: .agentic/02.rag-rulebook/schemas/retrieval-policy-dimension.schema.yml
- id: rag-rulebook.standard.retrieval-selector-policy-system
  path: .agentic/02.rag-rulebook/standards/retrieval-selector-policy-system.md
-->
# Retrieval Policy Dimension Guide

## Mental Model

A retrieval policy pack says which dimensions belong to a selector. A dimension
file says exactly how one of those dimensions should behave.

Each dimension should answer six plain questions:

- What information does this dimension need?
- What should it do with that information?
- What must it never do?
- What must it preserve or output?
- When should it create a gap or stop?
- How can we prove it behaves correctly?

## Good Shape

A good dimension is specific enough for deterministic selector code to execute
without inventing policy.

For example, a future typed request-anchor dimension should not merely say
"use context." It should say which anchor kinds are governed, how provenance
and freshness affect trust, when exact prompt paths beat broad similarity, and
when ambiguous ownership creates a blocking gap.

## Bad Shape

A weak dimension hides important behavior in vague prose:

```yml
expected_actions:
  - Use context intelligently.
```

That does not tell a selector what to rank, what to preserve, or when to stop.

A stronger version is:

```yml
expected_actions:
  - Rank exact prompt-path matches above broad concept matches.
banned_actions:
  - Do not infer ownership when multiple corpora claim the same path.
gap_or_stop_conditions:
  - Stop when exact path ownership is ambiguous.
```

## Authoring Rules

- Keep one dimension per file.
- Keep the top-level policy pack as the single active manifest.
- Use expected actions for positive behavior.
- Use banned actions for failure modes the selector must avoid.
- Use output obligations for anything downstream packet validation must see.
- Use gap or stop conditions when confidence, ownership, routing, validation,
  or governance is insufficient.
- Use validation examples as seed cases for future selector fixtures.

## Relationship To Selector Code

Selector code should read the policy pack, resolve imported dimensions, and
execute the compiled policy.

If selector code needs to invent a behavior that is not in a dimension file, the
policy is incomplete. Update the dimension first, then update the selector.
