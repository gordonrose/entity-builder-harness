<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: repo.script.commit-gates.readme
  version: 3
  status: active
  created_on: "2026-07-04"
  updated_on: "2026-10-25"
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

The portable chat hook already validates staged lifecycle edits, deterministic
process drift and governed command drift. This extension does not repeat those
checks. It requires `generate-index --all --strict --check-coverage` against the
working-tree artifact inventory, then runs `check-selection --staged
--execute-local` for affected scope consumers. Coverage includes declared headers outside required-header paths;
malformed or omitted declarations fail before commit. The hook does not edit
headers or stage files.

Required commands fail closed if missing. Unknown implementation impact remains
an explicit gap. Package/live proof obligations remain deferred to their owning
stages and cannot be satisfied by local check success.
