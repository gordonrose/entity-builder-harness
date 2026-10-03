<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.migration.controlled-source-recovery-2026-10-03
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines: [architecture, sre]
kind: migration-plan
purpose: Govern the explicitly approved local source reversal to the preserved baseline and its exact validation boundary.
portability: {class: source-only, targets: []}
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
-->
# Controlled source recovery

The owner approved local preservation and preparation on 3 October 2026.
Shared publication, merge, AWS changes and deployment remain unapproved.
This plan precedes the source reversal; it does not implement the proposed
replacement deployment mechanism or supersede the baseline deployment gates.

## Fixed source scope

The baseline is `0da085b50aac2b13dfb15aaac9351efea860926e`.
Live GitHub main was freshly verified as
`ec4744fcb2481365eeb54fb0ecd383b8b63c6e1e` by both Git and the branches API.
The preparation branch starts at that exact live tip, not the old local main.
The 40 later linear commits contain 424 changed paths. The exact inventory is
[the programme manifest](../../../../commitLogs/2026/oct/03/2026-10-03-prepare-source-recovery/recovery-evidence/programme-file-manifest.json).

Retire the 387 programme-added source files and restore the 36 modified files
to their baseline path, mode and blob. Preserve the one programme session log
named in the manifest unchanged. Existing baseline files inside expanded
directories remain; an entire mixed directory is never a removal target.
The prepared binary inverse SHA-256 is
`077a0bdd05d61699b0701fc91214a7857ee4244ef3531b0ad30cf1e17c406f6b`.

Compatibility choice is `retired` for each added source path: there is no new
replacement path, wrapper or alias. Restored pre-existing callers revert with
the inverse. Historical logs and this migration evidence may retain old names.
Active references to removed paths must be absent after the change. The path
planner inventory records routing, workflow, script, bootstrap, architecture,
other and session-history references before removal. All 177 safe retirement
surfaces passed the existing planner (521 seconds). The complete inventory has
1,721 matching lines: 828 in removed files, 68 in restored files and 825 in
preserved historical sessions. No active reference lies outside the inverse;
none survives in the baseline content of the 36 restored files. Exact planner
outputs are preserved in durable evidence/path-migration-audit; the auxiliary
session also retains the reference inventory and completion record.

The broad Operational Realization Gate already existed at baseline. It remains
in this source restoration. The separate replacement proposal must identify and
explicitly supersede conflicting gate instructions in a later approved change;
this recovery must not quietly remove baseline requirements.

## Preservation and ownership

The clean baseline checkout is
`/home/owner/projects/entity-builder-recovery-2026-10-03/baseline`.
The auxiliary chat branch is `chat/2026-10-03-prepare-source-recovery`.
Its session README records the canonical worktree and continuation of the
original investigation. Use the supported `AGENTIC_CHAT_WORKTREE_ROOT` setting
for its durable worktree location; do not edit lifecycle scripts or root work.

Four new refs under `refs/recovery/2026-10-03/` preserve `root-main`,
`cached-origin-main`, `verified-live-main` and `baseline`. All original refs
remain unchanged. The owner's 13 existing changed/untracked files and original
refs were verified before backup. Their private archive, source patch and
203 evidence and backup files are retained under
`/home/owner/projects/entity-builder-recovery-2026-10-03/evidence/`, with a
SHA-256 preservation manifest in its parent. These local backups are not
published in the PR. This is durable local storage, not an off-machine backup.

The approved one-off exception covers historical workspaces, preservation refs
and local inverse preparation. It is recorded in the investigation and auxiliary
session logs, with the governance gap and rationale. It creates no precedent and
does not waive commit checks or authorize external effects.

## Validation and commits

Commit this scope plan and its session/manifest before applying the inverse.
Check the patch against the clean prepared source; apply it only to the new
recovery worktree. Verify the full resulting path/mode/blob map against baseline.
Use an exact file allowlist for the retained historical log, named recovery
documents, session evidence and reviewed generated recognition catalogue.
Never exclude all commit logs or arbitrary documentation from equality checks.

Reassess recognition checks in this branch. The old investigation workspace's
missing-workflow catalogue entry is not part of the baseline catalogue. If new
recovery metadata makes recognition stale, regenerate only the affected derived
catalogue with the existing generator, review its diff and rerun its checks.
Do not restore an absent workflow or repair unrelated governance.

Run artifact metadata, recognition generation/validation, whitespace and the
existing commit readiness gate. Run the restored operational-realization smoke,
deployment workflow and infrastructure policies, candidate and PostgreSQL smoke
wrapper fixtures, container-boundary and PostgreSQL reference checks. Validate
restored runtime/packaging paths with their existing local checks when supported.
Record each command, result and any dependency limitation. No live deployment,
database effect test, image publication or active AWS drift assessment is part
of this preparation.

Create ordinary local commits after the checks pass. Present the exact branch,
base/head commits, applied diff, allowed baseline differences and test results
before requesting publication/merge. Recheck remote main before any later
approved shared action; classify new commits instead of overwriting them.

## Recovery and completion

The original branches, worktrees, cloud resources and backups remain available.
If local validation fails, retain the prepared branch and evidence for repair;
do not reset shared history or discard work. Reversing a later shared recovery
commit would itself require reviewed ordinary Git changes and approval.

No new architecture is adopted: this restores source to an existing baseline
and preserves history. The replacement plan remains a proposal. Completion of
local preparation is not completion of shared recovery or permission to resume
the unfinished PostgreSQL deployment.
