<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: repo.script.commit-gates.readme
  version: 1
  status: active
  layer: 06.shared
  domain: validation
  disciplines:
  - agentic
  kind: readme
  purpose: Document the repository-owned commit extension hook called by portable chat commit checks.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: repo.script.commit-gates
    path: scripts/repo/commit-gates/script.sh
-->
# Repository Commit Gates

This hook is the repository-owned extension point for checks that should run at
the chat commit boundary but do not belong inside portable `00.chat`.

`00.chat` may call this hook when it exists. The hook owns the selection of
repo-specific, harness-specific, RAG/rulebook, deployment, or product checks.
