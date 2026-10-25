<!-- agentic-artifact:
schema: agentic-artifact/v3
id: repo.check-selection.readme
version: 1
status: active
created_on: '2026-10-24'
updated_on: "2026-10-25"
layer: 06.shared
domain: validation
disciplines:
- agentic
- security
- sre
kind: documentation
purpose: Explain supported impact discovery, focused checks, evidence reuse and permission-preserving
  stage boundaries.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: repo.command.check-selection
  path: scripts/repo/check-selection/script.sh
-->
# Focused Repository Verification

This repository extension connects existing scope declarations, artifact
`used_by` references and workspace package dependencies to existing checks. It
uses `20-scopes/scope-index.yml` for discovery and the generic scope validators
for health, secrets and persistence applicability. It does not infer unsupported
consumers or treat incomplete coverage as a pass.

```bash
bash scripts/repo/check-selection/script.sh --paths platform/adapters/aws/persistence/postgresql/src/index.ts --json
bash scripts/repo/check-selection/script.sh --paths platform/adapters/aws/persistence/postgresql/src/index.ts --execute-local --json
bash scripts/repo/check-selection/script.sh --all --stage deploy --json
bash scripts/repo/check-selection/smoke-test.sh
```

`--staged` selects both sides of renames and reports deleted paths.
`--all` selects all discovered scope requirements. `--paths` accepts exact
repository-relative changed paths, including paths deleted by the change.
Directory input matching observes slash boundaries, so `src-extra` cannot
silently match an input declared as `src`.

The default is a plan, with pending checks and explicit later-stage obligations.
`--execute-local` runs only catalogued local checks whose effects agree with the
command metadata and contain only `read-only` and/or `writes-files`. This flag
requires task authorization for local execution. It never executes package,
provider, secret, publication or acceptance operations, even when `--stage`
selects a later boundary. Commands are argument arrays passed without a shell.

Checks with identical resolved argv execute once. Each result identifies the
stable check ID, argv key, scopes, effects, stage, evidence class, source revision
and digest of current declared inputs plus upstream package/metadata dependencies. `--evidence <report.json>` can reuse
matching successful local results. Changed bytes, commands, catalog entries, effects
or stages invalidate reuse. A nonzero exit remains failed evidence. A later
stage remains a gap requiring its owning controller. Aggregate reports cannot
satisfy package, deploy or acceptance checks, even when they contain a passed
entry; provider-specific receipt validity, freshness and live acceptance remain
enforced by the owning controller.

Supported source impact uses explicit scope input paths and actual workspace
package dependency edges. Artifact metadata adds declared consumer edges.
Unmatched code, configuration or deployment inputs are reported as
`changed-input-uncovered`, including deleted inputs. Governance/docs/session
paths are classified separately because mandatory metadata/process checks own
them. New selectors and coverage implementations select this regression suite.
Scope requirements cannot omit the mandatory scope-inventory and runnable-program
checks. This does not claim a complete language-level import graph.

The repository commit hook adds inventory coverage and focused local checks.
The preparation wrapper and repository hook both declare their local-test write
effects so the governed runner requires applicable execution approval.
The portable chat hook remains the sole owner of staged header validation,
deterministic process drift and governed command drift; these three checks are
not repeated here. No checker commits or stages files.

The regression suite creates a second dependency-free synthetic scope under a
disposable target. Existing generic validators accept its valid persistence
non-applicability. The same selector discovers it and executes its local proof
without a target name in generic code; missing/unsupported proof requirements,
unsafe effects, stale evidence and unclassified impact fail closed.
