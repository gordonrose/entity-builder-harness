<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.agents.readme
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Education Agents.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Education Agents

Agents define bounded review or execution roles for education work.

Use an agent when a role improves the work more than a workflow, prompt, or
checklist would. Agents should have narrow responsibility, explicit inputs,
clear outputs, allowed scope, review posture, and handoff expectations.

## Agents

- [Article Editor Agent](article-editor.md) - commissioning editor and reader
  advocate for public article candidates before drafting.
- [Article Writer Agent](article-writer.md) - executes an approved article
  editor brief and approved opening lab as a fresh public-facing draft.
- [Article Reporter Agent](article-reporter.md) - develops source packets and
  reader-world research packets, source packets, and scene cards before a
  public article can be commissioned.

## Public Article Loop

Use the agents in this order:

1. Article Reporter Agent creates or blocks the reader-world research packet,
   source packet, and scene cards.
2. Article Editor Agent creates or approves the article brief from the source
   packet.
3. Article Writer Agent creates an opening lab from the approved packet and
   brief.
4. Article Editor Agent approves or blocks the opening lab.
5. Article Writer Agent drafts only from the approved reader-world research
   packet, source packet, scene cards, brief, and opening.
6. Article Editor Agent reviews the draft before publication.

`No publishable article this cycle` is a valid outcome.
