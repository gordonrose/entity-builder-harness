<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.rules.pointer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: compatibility-pointer
purpose: Point older prototype rule references toward owner-aligned corpus rule roots during the domain split.
portability:
  class: source-only
  targets: []
used_by:
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# Prototype Rules Moved

The prototype architecture rules root has been split by owner corpus.

Canonical structured rules now live under numbered corpus roots:

- `docs/01.harness/rules/`
- `docs/03.product/rules/`
- `docs/04.deploy/rules/`
- `docs/06.shared/rules/`

This compatibility pointer exists while the prototype architecture corpus is
split into numbered owner-aligned homes.
