<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: repo.script.commit-gates.readme
  version: 7
  status: active
  created_on: "2026-07-04"
  updated_on: "2026-10-26"
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
checks. It runs `check-selection --staged --execute-local --require-preparation` for affected scope
consumers. The complete artifact inventory audit is intentionally separate:

```bash
bash scripts/repo/audit-artifact-inventory/script.sh
```

This keeps an expensive whole-repository scan out of ordinary task commits.
Staged metadata headers still fail at the commit boundary when malformed or
missing. The hook does not edit headers or stage files.

Required commands fail closed if missing. Unknown implementation impact remains
an explicit gap. Package/live proof obligations remain deferred to their owning
stages and cannot be satisfied by local check success.

The ordinary selector invocation automatically retains and reuses successful local
runner evidence in private per-worktree Git metadata. Its JSON output includes
`local_report_path`. Relevant staged inputs must match the working tree before
execution or reuse. Imported reports never grant proof, and unrelated source
revision/session bookkeeping changes do not invalidate unchanged local checks.
The selector rejects a relevant staged check when no matching pre-verification
record exists or its input identity changed; the report names the changed staged
inputs and affected check IDs before any local execution begins.
The `execution_summary` names reused, executed and deferred checks. When a
previous local proof cannot be reused, `invalidated_checks` reports whether the
verified inputs, runtime identity, or verification contract changed. Package
checks remain deferred at this boundary: a commit or merge request never
rebuilds an image merely to repeat package qualification.
