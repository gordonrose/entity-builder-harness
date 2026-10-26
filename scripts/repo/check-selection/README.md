<!-- agentic-artifact:
schema: agentic-artifact/v3
id: repo.check-selection.readme
version: 5
status: active
created_on: '2026-10-24'
updated_on: "2026-10-26"
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
The default scheduling boundary is `integration`. `--boundary commit` requires
only checks scheduled for commit preparation. The catalogue's `boundary` field
is independent of `stage`, `effects` and evidence class: an integration check
does not acquire network, provider or publication permission. CI retains its
protected command and uses the integration default. Direct local-main promotion
runs the same integration selection in the clean chat worktree after confirming
that it contains the base; failure or branch/input drift blocks promotion.
Promotion also reconciles the independent current delivery census before receipt
reuse, as CI does. The structural selector regression binds repository-wide
governance, metadata and script owners because its fixtures inspect the real graph.
`--execute-local` runs only catalogued local checks whose effects agree with the
command metadata and contain only `read-only` and/or `writes-files`. This flag
requires task authorization for local execution. It never executes package,
provider, secret, publication or acceptance operations, even when `--stage`
selects a later boundary. Commands are argument arrays passed without a shell.

Checks with identical resolved argv execute once, provided their effects, stage
and evidence class agree. A scope proof must bind its program, image and applicable
target/scope, or use a genuine generic command capability. Generic owners declare
an adjacent `check-capability.yml` binding their artifact identity, exact argv,
contract schema and consumed context parameters. Appending a context argument to
an unrelated fixed command cannot make it generic. The canonical runnable
program's `local_proof` must remain a selected local check.

Ordinary `--execute-local` runs, including the repository commit hook, reuse only
successful local runner receipts under the current worktree's private Git
metadata directory, `agentic-local-checks`. The report exposes `local_report_path`
for the latest JSON report. Writes are atomic, directory/file ownership and
permissions are checked, and symlink cache paths are refused. The boundary trusts
the local operating-system user who owns that Git metadata; it is neither signed
portable evidence nor protection from that same user editing their own cache.
`--evidence` reports are explicitly rejected as authority and never create cache
receipts. Failed, pending, uncertain and nonzero results never qualify reuse.
Each report has an `execution_summary` naming reused, executed and deferred
checks, selected check IDs and elapsed/execution seconds. A rerun after a previous trusted receipt records concrete
`invalidated_checks` reasons: verified input bytes changed, the declared runtime
identity changed, or the verification contract changed. These reasons explain
why a new local run is needed; they never make an old receipt acceptable.

`--record-preparation` stores the exact selected preparation identities in the same
private worktree cache, without executing checks. The chat pre-verification
sequence uses it before final verification. `--require-preparation` is limited
to `--staged`: it rejects a relevant commit-boundary check until its recorded
identity matches, reporting `verification-preparation-missing` or
`verification-preparation-inputs-changed` and the affected check IDs before
any execution. This prevents late lifecycle metadata edits from silently
turning commit preparation into a new verification cycle.
Preparation identities bind declared input bytes and the complete verification
contract. Deferred integration checks do not probe installed runtimes during
commit preparation; runtime identity is established at their verification
boundary. The lifecycle owner retains exact prepared artifact hashes/modes in
that same private preparation record, allowing unchanged content to retain its
date across UTC rollover. Modified content must be prepared again.

Impact references and `repository_inputs` mappings select obligations; they are
not automatically consumed proof inputs. Audited checks declare `scope_inputs:
false` and their complete `inputs`, including implementation helpers. Structural
scope validators and legacy subject-bound checks retain scope references until
their inputs are explicitly audited. Command/capability identity, runtime/config
bindings and transitive workspace package dependencies remain part of audited
proofs. Metadata consumer edges still select affected checks; consumed schemas
and contracts must be declared as proof inputs.

`--reuse-from-worktree <path>` reads only the private cache of a registered
worktree sharing the same Git common directory. It validates receipt contents
against their key and compares the target's own inputs, contract and runtime.
Matching local receipts are retained in the target's existing cache; arbitrary
JSON reports and package/live proofs remain ineligible. The refresh apply owner
uses this route before removing a clean preflight worktree. Repository-installed
tools bind their relative location plus actual bytes, modes and versions;
external installations retain absolute identity. A final identity sweep rejects
a pass invalidated by a later command in the same invocation.

Each receipt binds the complete catalog definitions of its selected check and
all aliases sharing that command. An unrelated check definition does not revoke
that receipt. Catalogue-only changes compare check contracts with staged HEAD
or the validated CI/promotion base. Existing scope and repository mappings select
the changed identities; an unchanged sibling on the same repository rule is not
selected solely by that contract change. Checks that explicitly consume the catalog still bind its complete
bytes. Every invocation validates the current catalog and selection; a catalog
change during planning or execution makes the invocation uncertain. This drift
barrier is separate from the reusable proof identity, so the next fresh plan can
reuse unaffected evidence. Staged execution still requires the catalog authority
to match the staged version.

The key includes relevant input bytes and file modes, transitive package and
metadata dependencies, owner capability, argv/effects/stage/evidence class,
resolved declared Bash/Python/PyYAML/Node/npm/TypeScript identities, declared
configuration paths and hashes of declared environment values. Missing optional
configuration files are fingerprinted, so creating one invalidates proof. The
catalog declares the supported tool/config/environment boundary; this is not
universal inference of arbitrary external tools, imports or machine settings.
Node checks explicitly declare `runtime.node_packages` (an empty list is valid
for checks using only built-in modules). The installation fingerprint resolves
each package's required, optional and peer dependency closure using bounded
Node resolution, and hashes actual installed paths, bytes and permissions.
Optional absence is recorded. In-repository workspace links include link and
target identity plus target contents; external targets, cycles and unsupported
file types fail closed. Removing or changing installed `pg`, `@types/node` or a
transitive package invalidates proof even when the lockfile is unchanged. No
installation or dependency code execution occurs during this fingerprint.
Inputs and runtime identities are recomputed after execution; changes during a
check yield uncertain evidence. Source revision is provenance, not a reuse key:
unrelated commits and session records do not invalidate unchanged local proof.

`--staged` rejects relevant unstaged or untracked selected inputs before running
or reusing checks. This prevents proving working-tree bytes while committing
different index bytes. Unrelated unstaged work remains untouched. Later-stage
commands are always deferred or reported as owning-controller gaps; symbolic
runtime receipt parameters are not required during local checks and cannot be
used to execute those commands here.

Supported source impact uses explicit scope inputs and workspace package
edges. Artifact metadata consumer relationships are followed transitively for
both scope checks and repository check mappings. The catalog may declare
`dormant_impact_roots`: metadata `used_by` edges into or out of those roots are
excluded from ordinary impact traversal, while direct repository-input mappings
continue to select the owning checks when that dormant surface is changed
explicitly. Authoritative schemas,
contracts and configuration need executable coverage; an unmapped definition is
`changed-input-uncovered`. Ordinary prose and nonexecutable session records
remain covered by their mandatory metadata/process checks. Scope requirements
cannot omit mandatory inventory/runnable checks, and unsupported impact is
reported explicitly.

The repository commit hook adds inventory coverage and focused local checks.
The preparation wrapper and repository hook both declare their local-test write
effects so the governed runner requires applicable execution approval.
The portable chat hook remains the sole owner of staged header validation,
deterministic process drift and governed command drift; these three checks are
not repeated here. No checker commits or stages files.

The regression suite creates a second dependency-bearing synthetic scope under a
disposable target. Existing generic validators accept its valid persistence
non-applicability. The same selector discovers it and executes its local proof
without a target name in generic code; missing/unsupported proof requirements,
wrong program/image binding, unsupported generic arguments, unsafe effects, stale evidence and unclassified impact fail closed. A temporary repository exercises the actual commit hook twice for reuse, a relevant unstaged mismatch, and rerun after staging. The fixture also proves unrelated revision changes retain valid proof.
