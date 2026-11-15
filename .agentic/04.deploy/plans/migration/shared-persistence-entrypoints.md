<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.migration.shared-persistence-entrypoints
version: 1
status: draft
created_on: "2026-11-15"
updated_on: "2026-11-15"
layer: 04.deploy
domain: migration
disciplines: [architecture, security, sre]
kind: migration-plan
purpose: Move shared persistence entrypoint helpers to their thematic owner without changing runtime or historical diagnostic contracts.
portability: {class: internal, targets: []}
used_by:
- id: deploy.plan.consolidate-core-platform-deployment-routes
  path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
-->
# Shared persistence entrypoint migration

## Scope and execution boundary

This is the C03 path-migration slice of the existing
[consolidation plan](../implementation/consolidate-core-platform-deployment-routes.md),
not a second consolidation programme. Both workloads already consume these
helpers. Their canonical home should express that ownership without making
the feature depend on baseline application composition.

The migration workflow requires this plan to be committed before active callers
move. On 2026-11-15 the user approved local checkpoints for this checked plan
and the verified consolidation and follow-on changes. No canonical path or
active import has been changed by preparing this plan. Publication, AWS
execution and changes to accepted evidence remain outside this migration's
authority.

All paths below are relative to `infra/04.deploy/03.product/entrypoints/`.

| Current implementation | Canonical implementation | Old-path disposition |
| --- | --- | --- |
| `kanbien-core-server-persistence-configuration.ts` | `shared/persistence/configuration.ts` | Thin export wrapper |
| `kanbien-core-server-persistence-role-credential.ts` | `shared/persistence/role-credential.ts` | Thin export wrapper |
| `kanbien-core-server-persistence-operation-diagnostics.ts` | `shared/persistence/operation-diagnostics.ts` | Thin export wrapper |

Compatibility wrappers retain direct-file imports and historical source links;
they contain only re-exports, not duplicated logic. All current production
callers, build configuration and diagnostic tooling migrate to canonical paths.
Keep the old artifact identities on compatibility files and assign distinct
identities to canonical implementations. Diagnostic IDs, catalog owners,
versions, messages and public exports do not change with filesystem ownership.
No new public package surface, layer namespace, bootstrap route or compatibility
promise is introduced; this is internal ownership extraction, with no ADR needed.

## Reference inventory

On 2026-11-15 the existing planner completed with exit 0 for each pair:

```bash
bash scripts/01.harness/plan-artifact-path-migration.sh infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts infra/04.deploy/03.product/entrypoints/shared/persistence/configuration.ts
bash scripts/01.harness/plan-artifact-path-migration.sh infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-role-credential.ts infra/04.deploy/03.product/entrypoints/shared/persistence/role-credential.ts
bash scripts/01.harness/plan-artifact-path-migration.sh infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-operation-diagnostics.ts infra/04.deploy/03.product/entrypoints/shared/persistence/operation-diagnostics.ts
```

All reported `old_exists=yes`, `new_exists=no`; no new-path references existed.
The planner's large historical lines exceeded terminal output limits for the
first two files. An independent literal-line scan of Git tracked and untracked,
nonignored files confirmed the following counts before this plan was added:

| Helper | Workflow | Script | Session history | Other | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Configuration | 9 | 7 | 165 | 18 | 199 |
| Role credential | 3 | 2 | 89 | 7 | 101 |
| Operation diagnostics | 3 | 7 | 0 | 6 | 16 |

These are matching lines, not consumer counts. A supplementary basename and
relative-import search found consumers that the full-path planner cannot see.

| Reference family | Disposition |
| --- | --- |
| Baseline main, migration, administration, verifier, restore verifier, IAM authentication and runtime credential entrypoints | Move their helper imports; preserve workload-specific composition and credentials. |
| Feature administration, preflight and diagnostics | Import canonical shared helpers; reject accidental baseline application dependencies. |
| Shared configuration selector and Core sourcing-issues metadata | Update canonical dependency references without changing selection or error contracts. |
| Runnable-program index and baseline declaration contract | Update owned source paths; do not change authorized dependency boundaries or program identity. |
| Both Dockerfiles and feature Docker ignore allowances | Copy canonical modules and all parent directories; do not rely on checkout files missing from image context. Compatibility wrappers must resolve if copied. |
| Composition configuration/restore tests, feature dependency boundary, process-diagnostic test and payload-copy fixture | Update compiled imports and interception targets; retain omitted-file and failure-before-pool counterexamples. |
| Diagnostic coverage tsconfig, catalog exporter, runtime reader, smoke tests and source review bindings | Follow canonical implementations and preserve exact published diagnostic contracts; do not hide implementation behind wrapper-only review. |
| Check selector and verifier operation tests | Register canonical input closure and keep changed/missing-input invalidation assertions. |
| Core config and platform maintenance READMEs | Point current instructions at canonical files; retain useful old links through wrappers. |
| Existing product/shared implementation plans and deployment diagnostic schema | Separate historical path examples from current source links; preserve code identifiers that merely resemble paths. |
| Dormant RAG generated recognition | Retain existing references to compatibility wrappers; do not reactivate generation. |
| Session logs, recorded source hashes, accepted receipts and education snapshots | Preserve unchanged; wrappers maintain old source-link compatibility. |

## Implementation and validation

After the plan checkpoint, move implementation bodies once, adjusting relative
imports for the deeper directory. Preserve configuration precedence/cache,
TLS, migration deadlines, SQL permissions, no implicit role reactivation,
diagnostic projection and all observed failure conditions. Update callers and
tests in the same slice. Never rewrite accepted source or image hashes to match
new files.

For each table pair, run the existing migration checker with this plan and
`--allow-active-old-path`, justified only by its retained export wrapper. Also
inspect relative imports so this allowance cannot conceal an unmigrated current
production caller. Verify old and canonical exports are equivalent, and both
fresh compilation and real Docker COPY dependency closure remain complete.

<!-- deterministic-check: allow reason="this migration plan records evidence selected by the reviewed caller inventory; execution remains owned by the existing selector, metadata preparation and artifact migration checks" -->
Run affected configuration, diagnostic projection, role/maintenance, feature
boundary and payload omission tests; select their registered integration checks
through the existing selector. Refresh source-matched diagnostic review bindings
after independent review. Run scoped metadata, link and whitespace checks and
the existing migration-helper smoke test. Batch full affected local checks only
on stable reviewed inputs. Actual image qualification requires its separate
committed-source gate; local compilation is not qualification or AWS proof.

Recovery is a scoped inverse patch restoring the three implementation bodies,
their imports and their build/test references together. Preserve unrelated
changes and accepted history; do not use a worktree reset. Record actual check
results and migration status in the consolidation plan and session log before
claiming C03 complete.
