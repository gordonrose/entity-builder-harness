<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.corpus-gaps.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: guide
purpose: Explain where durable corpus coverage gaps are recorded before source material, rules, chunks, and evaluations exist.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.generate-retrieval-selector-fixture
  path: scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# Corpus Gaps

Corpus gap records describe subject-matter coverage that is known to be missing
or incomplete.

They are not source material and they are not curated vocabulary. They are
planning records that let local context queries explain why a prompt can be
recognized while still lacking enough corpus depth for reliable guidance.

Use a corpus gap when:

- a prompt term is meaningful enough to route or evaluate
- existing chunks do not yet cover the domain deeply enough
- the missing coverage belongs to a specific numbered corpus
- the next work should be source material, structured rules, chunks, or
  evaluation proof rather than prompt-time guessing

Corpus gap records are read by the retrieval selector fixture generator and may
appear as `missing-corpus` gaps in a validated context packet.
