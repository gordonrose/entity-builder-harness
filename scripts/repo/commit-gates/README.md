<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: repo.script.commit-gates.readme
  version: 2
  status: active
  created_on: "2026-07-04"
  updated_on: "2026-10-20"
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
repo-specific, harness-specific, deployment, or product checks.

The metadata gates validate staged lifecycle edits and run
`generate-index --all --strict --check-coverage` against the working-tree artifact
inventory. Coverage includes declared headers outside required-header paths;
malformed or omitted declarations fail before commit. The hook does not edit
headers or stage files.
