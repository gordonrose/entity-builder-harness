<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.public-chat-workbench-adrs
  version: 1
  status: deprecated
  layer: 00.chat
  domain: bootstrap
  disciplines:
  - agentic
  kind: doc
  purpose: Preserve the retired public ADR export manifest for source-side maintainer
    history.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.docs.llm-workbench-acceptance-matrix
    path: docs/00.chat/llm-workbench-acceptance-matrix.md
-->
# Retired Public Chat Workbench ADR Manifest

This source-side note preserves the retired ADR export manifest for maintainer
history. It is not copied into generated public `llm-workbench` repos or
installed target repos.

ADRs are not runtime dependencies. Public users should be able to understand,
install, run, validate, and uninstall `llm-workbench` from current public docs:

- `docs/install.md`
- `docs/workflows.md`
- `docs/concepts.md`
- `docs/adapting-to-your-repo.md`
- `docs/public-beta-contract.md`

## Retired Selection Rule

This list used to accept a future ADR when all of these were true:

- it explains reusable chat workbench behavior
- it affects the public bootstrap, install, governance, command, script layout,
  session lifecycle, worktree model, or upstream promotion model
- a public maintainer would need the decision to understand why the workbench is
  shaped this way

It avoided ADRs that were primarily about:

- source-repo-only history
- non-chat layers such as AWS, education, product, or customer-specific work
- temporary migration mechanics that no longer affect public usage
- private paths, local environment details, or internal-only workflows

## Retired Manifest

The bootstrap planner no longer reads or copies this list.

```txt
docs/harness/architecture/adrs/0013-create-chat-layer-and-on-demand-session-summary.md
docs/harness/architecture/adrs/0014-promote-reusable-lessons-upstream.md
docs/harness/architecture/adrs/0015-use-shared-upstream-repo-bootstrap-standard.md
docs/harness/architecture/adrs/0018-govern-artifact-path-migrations.md
docs/harness/architecture/adrs/0019-use-chat-docs-namespace.md
```
