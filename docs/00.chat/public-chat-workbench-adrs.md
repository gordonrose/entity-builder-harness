<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.public-chat-workbench-adrs
  version: 1
  status: active
  layer: 00.chat
  domain: bootstrap
  disciplines:
  - agentic
  kind: doc
  purpose: Define which harness ADRs are copied into the public chat workbench repo.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.upstream.bootstrap-llm-workbench-repo
    path: scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh
  - id: chat.workflows.bootstrap-chat-workbench-repo
    path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
-->
# Public Chat Workbench ADRs

This file is the export manifest for ADRs copied into the public
`llm-workbench` repo.

ADRs are not runtime dependencies. They are copied only when they help a public
reader understand the current reusable chat workbench shape.

## Selection Rule

Add a future ADR to this list when all of these are true:

- it explains reusable chat workbench behavior
- it affects the public bootstrap, install, governance, command, script layout,
  session lifecycle, worktree model, or upstream promotion model
- a public maintainer would need the decision to understand why the workbench is
  shaped this way

Do not add an ADR when it is primarily about:

- source-repo-only history
- non-chat layers such as AWS, education, product, or customer-specific work
- temporary migration mechanics that no longer affect public usage
- private paths, local environment details, or internal-only workflows

## Manifest

Keep this list path-based so the bootstrap planner can copy exactly these ADRs.

```txt
docs/harness/architecture/adrs/0013-create-chat-layer-and-on-demand-session-summary.md
docs/harness/architecture/adrs/0014-promote-reusable-lessons-upstream.md
docs/harness/architecture/adrs/0015-use-shared-upstream-repo-bootstrap-standard.md
docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
docs/harness/architecture/adrs/0018-govern-artifact-path-migrations.md
docs/harness/architecture/adrs/0019-use-chat-docs-namespace.md
```
