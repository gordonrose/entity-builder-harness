<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.migration.shared-persistence-entrypoints
version: 2
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

## Follow-on: retire the workload-specific ECS configuration adapter

This additional slice belongs to Batch A of the linked consolidation plan.
Old path: `scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/entity-smoke-runtime-configuration.py`.
Surviving owner: `scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py`.
Disposition: **retired**, after migrating active callers. This is a merge into
an inspected existing implementation, not a move overwriting that destination.
No external/public API, namespace or bootstrap contract changes; no ADR needed.
Existing local-checkpoint authority covers this checked plan before retirement.
Checkpoint `8c425ce6` committed this slice before active references changed.

The reference planner completed with exit 0: both paths exist; nine exact old
path references were found. Three are dormant generated recognition entries;
four are active scripts/catalog/review references; two are declaration/binding
references. Basename review additionally finds the pinned historical inventory
and the implementation plan. Preserve the inventory's historical finding,
but explicitly mark the adapter recommendation superseded. Remove only the
obsolete generated recognition entry, without running dormant RAG machinery.

The shared adapter now accepts a per-workload sibling `provider_template`,
defaulting to the caller's template. Entity-smoke's restore-reader binding
declares its different template; all other callers keep existing defaults.
Reject invalid paths, symlinks, duplicate IDs and missing resources. Retain the
runtime-configuration caller's safe invalid-provider-configuration diagnostic.
The old adapter's error text is private to that caller and one fixture; migrate
the fixture, not historical receipts. Package projection is unchanged.

Validate the two real workload bindings, differently named multi-template
fixtures, invalid selections and existing package projection. Update registered
input closures and source review records. Run the migration checker with this
plan and no compatibility allowance, plus scoped metadata/whitespace checks.
Historical evidence remains untouched. Recovery is an inverse patch restoring
the old adapter and its callers together, never a worktree reset.

## Scope and execution boundary

This is the C03 path-migration slice of the existing
[consolidation plan](../implementation/consolidate-core-platform-deployment-routes.md),
not a second consolidation programme. Both workloads already consume these
helpers. Their canonical home should express that ownership without making
the feature depend on baseline application composition.

The migration workflow requires this plan to be committed before active callers
move. On 2026-11-15 the user approved local checkpoints for this checked plan
and the verified consolidation and follow-on changes. Checkpoint `29e5f1a3`
committed this plan before the canonical migration recorded below. Publication, AWS
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

## Executed migration and connected catalog correction

The migration plan was committed in local checkpoint `29e5f1a3` before canonical
source edits. The three implementation bodies now live in shared/persistence;
the old paths retain export-only compatibility wrappers. Current callers and
build/test references use the canonical implementations.

Fresh isolated catalog compilation on 2026-11-15 passed in 19.581 seconds, but
actual export from `/tmp/c03-catalog-build.gVTW2Sq0` failed in 1.555 seconds:
the declared project root set omitted the existing PostgreSQL adapter, so the
derived runtime payload had no shim for that imported package. The previous
repository-local output location permits upward workspace-module resolution,
which can mask this omission; that is an explanation from the resolution
layout, not a claim of a measured previous isolated pass. Configuration already
imported the adapter before this ownership migration.

The bounded correction adds the existing PostgreSQL adapter public entrypoint
to the catalog project's explicit roots, asserts its selected public export in
the actual project-selection fixture, and repeats fresh compilation and actual
export outside the repository without NODE_PATH. No generic resolver expansion,
automatic import approval or new dependency mapping is needed.

## C03 focused outcome — 2026-11-15

Implementation is ready for the parent's final registered verification and
checkpoint, not claimed image-qualified or deployed. The three canonical
implementation bodies retain the old exports and diagnostic definitions; the
parent independently compared bodies against `29e5f1a3`. Old modules are
export-only compatibility wrappers, excluded from the feature's normal source,
compiled and Docker COPY closure. Actual baseline callers, feature callers,
program/declaration inputs, both Docker contexts, catalog exporter, copied
fixtures and selector input references now point to the shared owner.

The configuration fixture compiles the three real wrappers separately with the
actual declared compiler inputs, checks each contains only its canonical export,
and proves every old export is the identical canonical object. This does not
silently put historical wrappers back into production payloads. Feature boundary
counterexamples reject missing canonical files, copies and context allowances,
and reject the old wrappers and baseline application/runtime sources.

| Focused observation | Result and elapsed |
| --- | --- |
| Fresh baseline compile; configuration fixture; restore diagnostic fixture | Passed, 10.880s; 10.129s; 8.845s. Configuration includes 577 failure-before-pool cases and wrapper identity. |
| Fresh feature compile; actual source boundary | Passed, 10.074s; 9.099s. Boundary observed 255 sources; installed dependency preparation copied 40 packages. |
| Feature runtime, access-control, preflight, database-proof fixtures | Passed, 1.040s; 0.459s; 0.500s; 0.484s. Controlled local dependencies, not live PostgreSQL/AWS. |
| Three governed path-migration checks, configuration / role / operation | Passed, 13.075s / 11.128s / 9.235s, with justified compatibility-wrapper allowance. Existing migration-helper smoke also passed. |
| Actual payload fixture | Assembly positive, 13 broken payload and six omitted-source cases passed; publication qualification fixture passed. Final recovery pin check initially failed; parent subsequently refreshed reviewed COPY-only owner pin and all 47 bounded recovery cases passed. Whole registered payload check still pending. |
| Corrected catalog project selection | Seven tests passed, 1.433s; actual declaration asserts PostgreSQL root/export/source inclusion. |
| Fresh corrected catalog compile | Passed, 11.377s outside repository. |
| Actual isolated catalog export | Passed, 2.347s in `/tmp/c03-catalog-isolation.eXIDgv/payload`, NODE_PATH unset. The existing installed-lock copier prepared 42 external packages selected from the actual project declaration into an isolated parent node_modules. No workspace links or repository upward resolution. |
| Three canonical inputs across six registered consumer closures | All 18 mutation/omission fingerprint cases passed; existing full impact-plan fixture now includes these paths but was not rerun independently. |
| Two edited README local links; whitespace | 79 links passed; diff check passed. One pre-existing maintenance test link corrected from integration to its actual unit folder. |

Isolation setup failures are retained rather than counted as passes: after the
workspace-root correction, a payload without external packages failed on `pg`.
An attempted copier invocation aimed at the existing compiled directory was
correctly rejected as `existing-or-overlapping`; the setup was corrected to its
documented new-directory-only destination. Neither required weakening the
copier, adding production fallback resolution, or changing external dependency
policy. The final isolated export passed with the actual declared external set.

Remaining old references are intentional compatibility metadata/exports,
explicit negative tests, published catalog filenames and historical plans,
session logs, education snapshots or accepted receipts. Current README links
and executable callers use canonical paths. Published JSON catalogs and accepted
histories were not rewritten. Parent independently validated both accepted
reference readers and byte-identical release-evidence trees.

Parent owns final source review bindings, metadata/preparation, registered
affected checks, full integration and committed-source image qualification.
These focused observations do not replace those obligations or establish new
live proof. No child commit, publication or AWS operation was performed.
