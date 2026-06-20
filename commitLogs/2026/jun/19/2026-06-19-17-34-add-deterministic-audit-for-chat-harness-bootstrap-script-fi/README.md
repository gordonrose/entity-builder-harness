# Chat Session: 2026-06-19-17-34 add-deterministic-audit-for-chat-harness-bootstrap-script-fi

<!-- agentic-session
id: 2026-06-19-17-34-add-deterministic-audit-for-chat-harness-bootstrap-script-fi
task: add deterministic audit for chat harness bootstrap script file set
branch: chat/2026-06-19-17-34-add-deterministic-audit-for-chat-harness-bootstrap-script-fi
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-19-17-34-add-deterministic-audit-for-chat-harness-bootstrap-script-fi-176453623
layer: harness
mode: implementation
workflow: .agentic/harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-19T16:34:46Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/19/rollout-2026-06-19T15-57-23-019ee062-f943-71b2-a975-e5a9172decbe.jsonl
latest_commit_at_utc: 2026-06-19T23:59:39Z
latest_commit_sha: 7217f55
chat_duration: 26693s (00:07:24:53)
estimated_chat_tokens: 4486674 estimated from chat transcript bytes (17946694 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/19/rollout-2026-06-19T15-57-23-019ee062-f943-71b2-a975-e5a9172decbe.jsonl)
estimated_chat_cost: USD 134.60 estimated from estimated_chat_tokens
estimated_chat_cost_basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing
-->

## Initial Intent

add deterministic audit for chat harness bootstrap script file set

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- The chat workbench bootstrap file set was previously prose-only, so it did
  not give a deterministic answer to which `scripts/` files are runtime
  required, validation/compatibility candidates, or unclassified.
- Metadata ownership initially used fake layer labels such as `shared-git` and
  `shared-harness`, which blurred real layer ownership with implementation
  domains.

## Decisions Made

- Add a chat bootstrap file-set audit that starts from public chat commands,
  chat workflows, shared process artifacts, and the governed runner, then
  follows source-side `scripts/chat/` and `scripts/shared/` references.
- Treat future upstream product-shell scripts such as `scripts/install.sh` and
  `scripts/uninstall.sh` as target files, not source repo dependencies.
- Keep validation helpers visible as candidates instead of silently excluding
  them from the bootstrap decision.
- Backfill script metadata in folder batches, starting with the public
  `scripts/chat/` alias surface.
- Keep `owner` limited to real harness layers and use `domain` for mechanisms
  such as `git`, `startup`, `session-log`, `governance`, and `validation`.
- Bias Git-shaped chat workbench behavior toward `owner: 00.chat` unless a
  non-chat owner is clear.
- Plan a script layout migration organized by owner layer, domain, and
  capability folder, with old paths retained as wrappers during migration.

## Activity Log

### 2026-06-19T16:34:46Z - Session started

Initial intent: add deterministic audit for chat harness bootstrap script file set


### 2026-06-19T16:53:29Z - Commit recorded

Commit: `3c0fc14`

Message: Add chat bootstrap file set audit

Summary: Added a governed audit that derives required chat bootstrap scripts and separates validation and unclassified candidates before upstream copying.

ADR impact: Existing ADR 0015 covers bootstrap productization; no new ADR.


### 2026-06-19T16:57:05Z - Commit recorded

Commit: `1f1e19c`

Message: Require metadata for new harness artifacts

Summary: Added the artifact metadata header standard, governed metadata checker, and commit-gate enforcement for newly added scripts and harness Markdown artifacts.

ADR impact: No new ADR; this implements the metadata governance plan in standards and gates.


### 2026-06-19T16:58:18Z - Commit recorded

Commit: `ed40b10`

Message: Backfill metadata for chat script aliases

Summary: Added agentic-script metadata headers to the public scripts/chat alias commands and verified them with the alias smoke test.

ADR impact: No ADR impact; metadata backfill follows the new standard.


### 2026-06-19T17:00:17Z - Commit recorded

Commit: `1b8a15a`

Message: Backfill metadata for shared chat scripts

Summary: Added metadata headers to root scripts/shared/chat helpers and validation scripts, and fixed metadata checking for JavaScript comment headers.

ADR impact: No ADR impact; metadata backfill follows the new standard.


### 2026-06-19T17:01:49Z - Commit recorded

Commit: `f6ff62c`

Message: Backfill metadata for chat startup scripts

Summary: Added metadata headers to chat command and request-initialization scripts, verified classifier fixtures, chat-command smoke, and chat-worktree startup smoke.

ADR impact: No ADR impact; metadata backfill follows the new standard.


### 2026-06-19T17:04:24Z - Commit recorded

Commit: `df1e872`

Message: Backfill metadata for shared git scripts

Summary: Added metadata headers to shared Git runtime scripts, approved mutators, compatibility helpers, and Git smoke tests after running the Git smoke suite and prepare gate.

ADR impact: No ADR impact; metadata backfill follows the new standard.


### 2026-06-19T17:05:34Z - Commit recorded

Commit: `58a269d`

Message: Backfill metadata for harness scripts

Summary: Added metadata headers to shared harness checks, governed runner, and harness smoke tests, then verified the full script tree metadata check.

ADR impact: No ADR impact; metadata backfill follows the new standard.


### 2026-06-19T17:22:54Z - Commit recorded

Commit: `2e1008b`

Message: Clarify metadata owners and domains

Summary: Restricted metadata owners to real harness layers, added domain to headers, and reclassified Git-shaped chat workbench scripts under owner 00.chat with domain git.

ADR impact: No ADR impact; this corrects the metadata standard and backfill model.


### 2026-06-19T17:32:59Z - Commit recorded

Commit: `2c6e0bc`

Message: Plan script capability folder migration

Summary: Added proposed ADR 0017 defining the owner/domain/capability script layout migration plan, including compatibility wrappers and a cleanup-empty-chat-branches pilot.

ADR impact: ADR 0017 proposed; records the planned script layout migration.


### 2026-06-19T17:38:30Z - Commit recorded

Commit: `b015295`

Message: Pilot cleanup script capability folder

Summary: Moved cleanup-empty-chat-branches into scripts/00.chat/git/cleanup-empty-chat-branches with script and smoke-test colocated, retained old shared paths as wrappers, and updated bootstrap audit classification for capability folders.

ADR impact: ADR 0017 accepted after the cleanup-empty-chat-branches pilot passed direct and compatibility checks.


### 2026-06-19T17:48:40Z - Commit recorded

Commit: `db84985`

Message: Point cleanup references at canonical script

Summary: Updated cleanup workflow, startup cleanup, public alias, smoke fixtures, and bootstrap audit behavior so normal references use scripts/00.chat/git/cleanup-empty-chat-branches/script.sh while old shared paths remain compatibility-only.

ADR impact: ADR 0017 migration rule reinforced: canonical paths by default, old paths only for compatibility notes and wrappers.


### 2026-06-19T18:04:15Z - Commit recorded

Commit: `e627fbe`

Message: Move chat command dispatcher capability

Summary: Moved the chat command dispatcher and smoke test into scripts/00.chat/command/dispatcher, added a capability README explaining dispatcher behavior, kept old shared paths as compatibility wrappers, and updated normal command references to the canonical path.

ADR impact: ADR 0017 now records the dispatcher as a second capability-folder pilot.


### 2026-06-19T18:14:18Z - Commit recorded

Commit: `ef10b3e`

Message: Move chat reporting capabilities

Summary: Moved chat workspace reporting and commit log summary generation into scripts/00.chat/reporting capability folders, retained old shared paths as compatibility wrappers, updated public aliases, reporting docs, smoke fixtures, and ADR 0017.

ADR impact: ADR 0017 now records the reporting batch and the temporary governed-runner wrapper exception.


### 2026-06-19T18:18:49Z - Commit recorded

Commit: `bfdc0fe`

Message: Move chat audit capabilities

Summary: Moved chat layer migration and bootstrap file-set audits into scripts/00.chat capability folders, retained old shared paths as compatibility wrappers, updated public aliases, bootstrap docs, migration docs, and ADR 0017.

ADR impact: ADR 0017 now records the audit batch and the temporary governed-runner wrapper exception.


### 2026-06-19T18:23:04Z - Commit recorded

Commit: `0fd6780`

Message: Move chat classification capability

Summary: Moved chat task classification, fixture check, and fixtures into scripts/00.chat/classification/classify-task, retained old executable paths as compatibility wrappers, and updated startup, docs, and smoke fixtures to use canonical classifier paths.

ADR impact: ADR 0017 now records the classification batch.


### 2026-06-19T18:35:50Z - Commit recorded

Commit: `b0130c3`

Message: Move chat session-log executable helpers

Summary: Moved executable session-log helpers into scripts/00.chat/session-log capability folders, retained old executable paths as compatibility wrappers, updated canonical references, smoke fixtures, and the bootstrap audit surface; left the sourced session-log-paths library for a separate migration pass.

ADR impact: ADR 0017 records the session-log executable batch and the deferred sourced-library/governed-runner exceptions.


### 2026-06-19T18:42:56Z - Commit recorded

Commit: `d4b1186`

Message: Move chat transcript and metrics helpers

Summary: Moved Codex transcript discovery, transcript registration, and chat cost estimation into scripts/00.chat transcript/metrics capability folders; retained old shared paths as compatibility wrappers and updated direct callers, smoke fixtures, and the bootstrap audit.

ADR impact: ADR 0017 records the transcript and metrics batch result.


### 2026-06-19T18:47:26Z - Commit recorded

Commit: `0457a48`

Message: Retire obsolete chat compatibility wrappers

Summary: Removed unreferenced shared chat command and smoke-test compatibility wrappers after proving public aliases and canonical smoke tests still pass; retained governed-runner compatibility wrappers for a later path-policy migration.

ADR impact: ADR 0017 now distinguishes retired wrappers from compatibility wrappers that remain due to governed-runner allowlist dependencies.


### 2026-06-19T18:55:47Z - Commit recorded

Commit: `c4b40b6`

Message: Move chat session-log path library

Summary: Moved the session-log path helper library to scripts/00.chat/session-log/paths/lib.sh, kept scripts/shared/chat/session-log-paths.sh as a source-compatible shim, updated canonical chat callers, and taught smoke fixtures to copy the canonical library with the shim.

ADR impact: ADR 0017 now records the source-library migration and remaining compatibility-shim boundary.


### 2026-06-19T19:03:48Z - Commit recorded

Commit: `670dfc6`

Message: Move chat worktree path library

Summary: Moved chat worktree path helpers to scripts/00.chat/worktree/paths/lib.sh, kept scripts/shared/chat/chat-worktree-paths.sh as a source-compatible shim, updated the canonical reporting caller, and adjusted smoke fixtures to copy the canonical library with the shim.

ADR impact: ADR 0017 now records the worktree source-library migration and remaining compatibility-shim boundary.


### 2026-06-19T19:11:52Z - Commit recorded

Commit: `fc0fe5d`

Message: Move chat worktree ensure helper

Summary: Moved ensure-chat-worktree into scripts/00.chat/worktree/ensure-chat-worktree/script.sh, kept the old shared path as a compatibility wrapper, updated workflows to point to the canonical helper, and adjusted smoke fixtures.

ADR impact: ADR 0017 records the canonical worktree helper and remaining compatibility wrapper boundary.


### 2026-06-19T19:15:26Z - Commit recorded

Commit: `95b19c1`

Message: Move chat closeout command

Summary: Moved the chat closeout prompt command to scripts/00.chat/closeout/build-closeout-prompt/script.sh, kept the shared command path as a dispatcher-compatible wrapper, and updated smoke fixtures and ADR 0017.

ADR impact: ADR 0017 records the closeout command batch and remaining command-discovery compatibility wrapper.


### 2026-06-19T19:20:39Z - Commit recorded

Commit: `b05a045`

Message: Move chat new-session command

Summary: Moved the chat new-session command launcher to scripts/00.chat/startup/start-new-chat/script.sh, kept the shared command path as a dispatcher-compatible wrapper, and updated smoke fixtures plus start-chat-session metadata.

ADR impact: ADR 0017 records the new-session command batch and remaining command-discovery compatibility wrapper.


### 2026-06-19T19:24:46Z - Commit recorded

Commit: `7372552`

Message: Move chat auto-start helper

Summary: Moved opening-prompt auto-start into scripts/00.chat/startup/auto-start-missing-session/script.sh, kept the old request-initialization path as a governed-runner-compatible wrapper, and updated dispatcher metadata, smoke fixtures, and ADR 0017.

ADR impact: ADR 0017 records the auto-start helper batch and the remaining governed-runner path-policy exception.


### 2026-06-19T19:31:26Z - Commit recorded

Commit: `4a91c54`

Message: Move chat session startup engine

Summary: Moved start-chat-session into scripts/00.chat/startup/start-chat-session with a capability README, kept the old request-initialization path as a compatibility wrapper, and updated startup callers and smoke fixtures.

ADR impact: ADR 0017 records the startup engine migration and remaining compatibility boundary.


### 2026-06-19T19:35:09Z - Commit recorded

Commit: `0b09130`

Message: Expand chat startup README

Summary: Expanded the start-chat-session capability README into an educational guide that explains the chat startup mental model, each startup action, and what the script deliberately does not do.

ADR impact: The README now teaches why startup creates a branch, worktree, session log, first prompt, and cleanup pass before agent work begins.


### 2026-06-19T19:45:07Z - Commit recorded

Commit: `4136277`

Message: Clarify terminal prompt handoff

Summary: Clarified that CHAT_COPY_PROMPT is terminal handoff convenience rather than the startup contract, and documented that IDE/app integrations should consume startup data directly.

ADR impact: Added an ADR 0017 follow-up to revisit the terminal prompt handoff interface after the current script organization stream.


### 2026-06-19T19:48:20Z - Commit recorded

Commit: `3775644`

Message: Move chat startup smoke test

Summary: Moved the chat startup worktree smoke test beside the start-chat-session capability, kept the old shared git smoke path as a compatibility wrapper, and documented the smoke coverage in the capability README and ADR 0017.

ADR impact: Validated both the canonical smoke path and old wrapper path, plus the bootstrap file-set audit, metadata headers, governed drift, and pre-commit gate.


### 2026-06-19T19:51:12Z - Commit recorded

Commit: `64e4cbc`

Message: Document chat auto-start capability

Summary: Added an educational README for the auto-start-missing-session startup capability, explaining opening-prompt recovery startup, routing decisions, validation coverage, and the compatibility wrapper boundary.

ADR impact: ADR 0017 now records the auto-start README and notes that dispatcher smoke covers opening-prompt auto-start behavior.


### 2026-06-19T20:01:01Z - Commit recorded

Commit: `0cdbc73`

Message: Move chat commit recording capability

Summary: Moved record-chat-commit and its metrics smoke test into scripts/00.chat/session-log/record-chat-commit, added a capability README, kept old shared git paths as compatibility wrappers, and updated helper metadata plus ADR 0017.

ADR impact: Validated canonical and compatibility smoke paths, bootstrap file-set audit, metadata headers, governed command drift, syntax checks, and the pre-commit gate.


### 2026-06-19T20:06:11Z - Commit recorded

Commit: `3d822d7`

Message: Move chat session checkpoint capability

Summary: Moved checkpoint-chat-session-log into scripts/00.chat/session-log/checkpoint-chat-session-log, added a capability README, kept the old governed shared path as a compatibility wrapper, and updated ADR 0017 plus session-log helper metadata.

ADR impact: Validated canonical and wrapper dry-run behavior in a throwaway repo, bootstrap file-set audit, metadata headers, governed command drift and smoke, syntax checks, and pre-commit gate.


### 2026-06-19T20:13:26Z - Commit recorded

Commit: `7a7c0c7`

Message: Move chat commit readiness gate

Summary: Moved prepare-chat-session-before-commit into scripts/00.chat/session-log/prepare-chat-session-before-commit, added a capability README, kept the old governed shared path as a compatibility wrapper, and updated ADR 0017 plus metadata references.

ADR impact: Validated syntax, bootstrap file-set audit, metadata headers, governed command drift, and the approved wrapper path through the governed runner.


### 2026-06-19T20:18:13Z - Commit recorded

Commit: `007941c`

Message: Move chat commit prerequisite gate

Summary: Moved check-commit-prerequisites and its smoke test into scripts/00.chat/session-log/check-commit-prerequisites, added a capability README, kept old shared git paths as compatibility wrappers, and updated the prepare gate plus ADR metadata.

ADR impact: Validated canonical and wrapper smoke paths, bootstrap audit, metadata headers, governed command drift, syntax checks, and the approved prepare gate path.


### 2026-06-19T20:20:16Z - Commit recorded

Commit: `97c25cf`

Message: Move chat commit log deletion gate

Summary: Moved check-commitlog-deletions and its smoke test into scripts/00.chat/session-log/check-commitlog-deletions, added a capability README, kept old shared git paths as compatibility wrappers, and updated the prepare gate plus ADR 0017.

ADR impact: Validated canonical and wrapper smoke paths, bootstrap audit, metadata headers, governed command drift, syntax checks, and the approved prepare gate path.


### 2026-06-19T20:22:11Z - Commit recorded

Commit: `5b746e0`

Message: Move chat write-location gate

Summary: Moved check-write-location into scripts/00.chat/worktree/check-write-location, added a capability README, kept the old shared git path as a compatibility wrapper, and updated the prepare gate, worktree metadata, and ADR 0017.

ADR impact: Validated canonical and wrapper outputs, bootstrap audit, metadata headers, governed command drift, syntax checks, and the approved prepare gate path.


### 2026-06-19T20:23:56Z - Commit recorded

Commit: `8ae71e4`

Message: Move chat dirty worktree gate

Summary: Moved dirty-worktree-check into scripts/00.chat/worktree/dirty-worktree-check, added a capability README, kept the old shared git path as a compatibility wrapper, and updated ADR 0017.

ADR impact: Validated clean, bookkeeping-only, wrapper, and mixed-dirty failure behavior in a throwaway repo, plus bootstrap audit, metadata headers, governed command drift, and syntax checks.


### 2026-06-19T20:27:14Z - Commit recorded

Commit: `a06b99e`

Message: Document remaining shared git migration inventory

Summary: Added an ADR 0017 inventory classifying remaining scripts/shared/git files into moved compatibility wrappers, chat refresh/local convergence candidates, and isolated chat branch execution helpers.

ADR impact: The inventory records that remaining shared git files are still owner 00.chat by metadata and recommends migrating refresh/local convergence before isolated chat branch execution helpers.


### 2026-06-19T20:50:22Z - Commit recorded

Commit: `ece9f31`

Message: Add governed recovery import for active worktree paths

Summary: Added a governed recovery capability to import explicit paths from an active worktree into the session chat-owned worktree, converted the old staging helper into a compatibility wrapper, documented ADR supersession boundaries, and added smoke coverage.

ADR impact: ADR 0009 now records recovery-only successor behavior; ADR 0011 documents recovery import for wrong-worktree edits; ADR 0017 records the recovery import batch.


### 2026-06-19T21:03:27Z - Commit recorded

Commit: `24e0087`

Message: Move main refresh status checks to readable capability names

Summary: Moved main-refresh status and readiness checks to human-readable canonical capability folders, retained old shared git paths as wrappers, updated refresh workflow and callers, and added capability READMEs.

ADR impact: ADR 0017 records the main refresh status/readiness batch; ADR 0011 now points to the readable freshness check.


### 2026-06-19T21:11:44Z - Commit recorded

Commit: `4e080db`

Message: Move main refresh rehearse and apply scripts

Summary: Moved main-refresh rehearsal and apply operations into readable canonical capability folders, kept old shared git paths as compatibility wrappers, updated refresh workflow/cleanup/conflict docs, and retained end-to-end smoke coverage.

ADR impact: ADR 0017 records the main refresh rehearse/apply batch and notes the destructive apply path remains outside the always-approved runner surface.


### 2026-06-19T21:16:42Z - Commit recorded

Commit: `b76d05c`

Message: Move local merge readiness verifier

Summary: Moved the local-main merge readiness verifier and smoke test into a readable local-merge capability folder, retained shared git compatibility wrappers, updated the promote-to-main workflow, and switched the verifier to canonical session/worktree helper libraries.

ADR impact: ADR 0017 records the local merge readiness batch; ADR 0011 now describes local merge verification as the explicit path into main.


### 2026-06-19T21:22:35Z - Commit recorded

Commit: `7b756a6`

Message: Move local merge visibility reports

Summary: Moved local-merge visibility reports to canonical 00.chat paths, added READMEs, retained compatibility wrappers, and updated workflow, runner, and ADR references.

ADR impact: covered by session ADR disposition


### 2026-06-19T21:28:08Z - Commit recorded

Commit: `219c37f`

Message: Classify isolated worktree helpers as superseded

Summary: Marked the old isolated worktree command runner and staging adapter as superseded compatibility helpers, clarified ADR guidance, and kept retirement review separate from canonical migration.

ADR impact: covered by session ADR disposition


### 2026-06-19T21:33:15Z - Commit recorded

Commit: `6a00306`

Message: Document compatibility wrapper retirement rules

Summary: Added a wrapper retirement map to ADR 0017 and updated the public chat alias README to point at canonical 00.chat implementations.

ADR impact: covered by session ADR disposition


### 2026-06-19T21:42:11Z - Commit recorded

Commit: `61f07ce`

Message: Advertise canonical chat paths in governed runner

Summary: Updated the governed runner to advertise canonical 00.chat paths, retained compatibility acceptance, updated agent-facing examples, and expanded governed command drift checks for canonical approved-action references.

ADR impact: covered by session ADR disposition


### 2026-06-19T21:46:55Z - Commit recorded

Commit: `8dab55e`

Message: Move chat command discovery to canonical folders

Summary: Moved chat command discovery to canonical 00.chat command folders, added canonical new and close command entrypoints, retained shared command wrappers, and updated command docs, smoke tests, and ADR guidance.

ADR impact: covered by session ADR disposition


### 2026-06-19T21:50:47Z - Commit recorded

Commit: `074600e`

Message: Classify bootstrap install compatibility paths

Summary: Documented bootstrap audit semantics and classified public install surfaces, shared governance primitives, required old-path wrappers, superseded legacy paths, and validation-only compatibility candidates in ADR 0017.

ADR impact: covered by session ADR disposition


### 2026-06-19T21:57:00Z - Commit recorded

Commit: `902b139`

Message: Move llm-workbench upstream helper to canonical path

Summary: Moved the llm-workbench upstream availability helper to scripts/00.chat/upstream, kept the old shared path as a compatibility wrapper, updated governed runner advertising, smoke coverage, metadata, and ADR 0017.

ADR impact: covered by session ADR disposition


### 2026-06-19T21:59:58Z - Commit recorded

Commit: `54300d0`

Message: Classify validation smoke wrappers for retirement

Summary: Recorded that the old shared git smoke-test wrappers are validation-only compatibility wrappers with canonical scripts/00.chat smoke-test targets, and split them out from broader bootstrap compatibility candidates.

ADR impact: ADR 0017 now separates validation-only smoke wrapper retirement candidates from bootstrap/install compatibility paths.


### 2026-06-19T22:03:04Z - Commit recorded

Commit: `8703814`

Message: Retire validation-only smoke wrappers

Summary: Removed eight old shared git smoke-test compatibility wrappers after canonical scripts/00.chat smoke tests passed and the bootstrap audit stayed clean.

ADR impact: ADR 0017 now records the validation-only smoke wrappers as retired historical paths with canonical replacements.


### 2026-06-19T22:06:48Z - Commit recorded

Commit: `c8bdc1c`

Message: Retire validation-only chat helper wrappers

Summary: Removed four old shared chat transcript/session-log compatibility wrappers after confirming canonical scripts/00.chat replacements, no live old-path references, and a clean bootstrap audit.

ADR impact: ADR 0017 now records the retired chat helper wrappers and their canonical transcript/session-log replacements.


### 2026-06-19T22:09:44Z - Commit recorded

Commit: `5d51c4b`

Message: Retire validation-only classification wrappers

Summary: Removed two old request-initialization classification compatibility wrappers after confirming canonical classification paths, no live old-path references, and a clean bootstrap audit.

ADR impact: ADR 0017 now records the retired classification wrappers and their canonical classification replacements.


### 2026-06-19T22:22:42Z - Commit recorded

Commit: `5faa9c8`

Message: Replace chat aliases with package scripts

Summary: Replaced the public scripts/chat alias surface with package.json chat:* commands, added package-script smoke coverage, updated bootstrap and migration docs/audits, and removed the old scripts/chat aliases.

ADR impact: ADR 0017 now records package.json chat scripts as the public command surface and scripts/chat aliases as retired historical paths.


### 2026-06-19T22:28:07Z - Commit recorded

Commit: `c0e163d`

Message: Retire remaining validation compatibility wrappers

Summary: Removed the remaining Track A validation-only wrappers after moving startup and command smoke fixtures to canonical scripts/00.chat paths and confirming bootstrap audit stayed clean.

ADR impact: ADR 0017 now records the remaining validation compatibility wrappers as retired Track A paths with canonical replacements.


### 2026-06-19T22:31:27Z - Commit recorded

Commit: `c9a384f`

Message: Retire shared command wrappers

Summary: Removed old shared chat command compatibility wrappers after command and package smoke fixtures moved to canonical command scripts and package scripts.

ADR impact: ADR 0017 now records shared command wrappers as retired historical paths.


### 2026-06-19T22:34:35Z - Commit recorded

Commit: `25f068e`

Message: Retire read-only governed runner wrappers

Summary: Removed four old shared read-only/reporting wrappers from the governed runner compatibility surface after canonical runner paths remained green and old paths were rejected as intended.

ADR impact: ADR 0017 now records the read-only governed runner wrappers as retired historical paths.


### 2026-06-19T22:39:55Z - Commit recorded

Commit: `26264d6`

Message: Retire read-only shared git wrappers

Summary: Removed the remaining read-only shared git compatibility wrappers for local merge visibility/readiness and main-refresh status/readiness, kept canonical scripts/00.chat paths as the operative entrypoints, updated ADR 0017 and source-packet references, and removed the old paths from the governed runner allowlist.

ADR impact: ADR 0017 now records these shared git wrappers as retired compatibility paths.


### 2026-06-19T23:26:18Z - Commit recorded

Commit: `47a61c4`

Message: Retire shared chat command wrappers

Summary: Removed the remaining executable scripts/shared/chat compatibility wrappers for upstream repo setup, chat-log rename, and auto-start. Updated the governed runner, smoke tests, and capability docs so canonical scripts/00.chat paths are the only operative command entrypoints.

ADR impact: ADR 0017 now records these shared chat command wrappers as retired compatibility paths.


### 2026-06-19T23:34:14Z - Commit recorded

Commit: `1accd0a`

Message: Retire shared chat source shims

Summary: Removed the final scripts/shared/chat source shims after migrating runtime callers and smoke fixtures to canonical scripts/00.chat session-log and worktree path libraries. Updated chat workflows, command docs, bootstrap guidance, ADR 0017, and runner path acceptance to reflect the canonical-only chat layout.

ADR impact: ADR 0017 now records the source shims as retired compatibility paths.


### 2026-06-19T23:43:03Z - Commit recorded

Commit: `b3897eb`

Message: Retire shared git gate wrappers

Summary: Migrated active chat gate workflows, checklists, READMEs, smoke tests, and governed runner allowlists to canonical scripts/00.chat paths, then removed the old scripts/shared/git gate wrappers.

ADR impact: ADR 0017 now records the shared git gate wrappers as retired compatibility paths.


### 2026-06-19T23:49:40Z - Commit recorded

Commit: `94117e5`

Message: Retire main refresh preflight wrapper

Summary: Removed the obsolete shared git preflight-main-refresh compatibility wrapper after confirming main-refresh rehearsal is owned by the canonical scripts/00.chat/main-refresh/rehearse-refresh-from-main path and the bootstrap audit no longer needs the wrapper.

ADR impact: ADR 0017 now records preflight-main-refresh as retired compatibility.


### 2026-06-19T23:54:33Z - Commit recorded

Commit: `358cab4`

Message: Retire isolated chat branch helpers

Summary: Removed the superseded shared git isolated-command runner, active-worktree staging wrapper, and legacy smoke test after proving canonical chat-owned worktrees plus the recovery import cover the useful behavior and no active bootstrap, install, workflow, or governed runner surface depends on the old paths.

ADR impact: ADR 0009 now records the isolated-runner model as historical, and ADR 0017 records the legacy trio as retired superseded paths.


### 2026-06-19T23:59:39Z - Commit recorded

Commit: `7217f55`

Message: Reconcile chat docs after shared git retirement

Summary: Updated chat-layer README, migration plan, and bootstrap workflow so human instructions point at canonical scripts/00.chat capabilities and shared harness governance instead of the retired scripts/shared/git surface; also removed stale empty shared-git fixture directories from canonical smoke tests.

ADR impact: No new ADR; this reconciles docs and validation fixtures after ADR 0017 retired the shared git compatibility paths.

## Commits



- Commit: `3c0fc14`
  Time UTC: 2026-06-19T16:53:29Z
  Message: Add chat bootstrap file set audit
  Summary: Added a governed audit that derives required chat bootstrap scripts and separates validation and unclassified candidates before upstream copying.
  ADR impact: Existing ADR 0015 covers bootstrap productization; no new ADR.


- Commit: `1f1e19c`
  Time UTC: 2026-06-19T16:57:05Z
  Message: Require metadata for new harness artifacts
  Summary: Added the artifact metadata header standard, governed metadata checker, and commit-gate enforcement for newly added scripts and harness Markdown artifacts.
  ADR impact: No new ADR; this implements the metadata governance plan in standards and gates.


- Commit: `ed40b10`
  Time UTC: 2026-06-19T16:58:18Z
  Message: Backfill metadata for chat script aliases
  Summary: Added agentic-script metadata headers to the public scripts/chat alias commands and verified them with the alias smoke test.
  ADR impact: No ADR impact; metadata backfill follows the new standard.


- Commit: `1b8a15a`
  Time UTC: 2026-06-19T17:00:17Z
  Message: Backfill metadata for shared chat scripts
  Summary: Added metadata headers to root scripts/shared/chat helpers and validation scripts, and fixed metadata checking for JavaScript comment headers.
  ADR impact: No ADR impact; metadata backfill follows the new standard.


- Commit: `f6ff62c`
  Time UTC: 2026-06-19T17:01:49Z
  Message: Backfill metadata for chat startup scripts
  Summary: Added metadata headers to chat command and request-initialization scripts, verified classifier fixtures, chat-command smoke, and chat-worktree startup smoke.
  ADR impact: No ADR impact; metadata backfill follows the new standard.


- Commit: `df1e872`
  Time UTC: 2026-06-19T17:04:24Z
  Message: Backfill metadata for shared git scripts
  Summary: Added metadata headers to shared Git runtime scripts, approved mutators, compatibility helpers, and Git smoke tests after running the Git smoke suite and prepare gate.
  ADR impact: No ADR impact; metadata backfill follows the new standard.


- Commit: `58a269d`
  Time UTC: 2026-06-19T17:05:34Z
  Message: Backfill metadata for harness scripts
  Summary: Added metadata headers to shared harness checks, governed runner, and harness smoke tests, then verified the full script tree metadata check.
  ADR impact: No ADR impact; metadata backfill follows the new standard.


- Commit: `2e1008b`
  Time UTC: 2026-06-19T17:22:54Z
  Message: Clarify metadata owners and domains
  Summary: Restricted metadata owners to real harness layers, added domain to headers, and reclassified Git-shaped chat workbench scripts under owner 00.chat with domain git.
  ADR impact: No ADR impact; this corrects the metadata standard and backfill model.


- Commit: `2c6e0bc`
  Time UTC: 2026-06-19T17:32:59Z
  Message: Plan script capability folder migration
  Summary: Added proposed ADR 0017 defining the owner/domain/capability script layout migration plan, including compatibility wrappers and a cleanup-empty-chat-branches pilot.
  ADR impact: ADR 0017 proposed; records the planned script layout migration.


- Commit: `b015295`
  Time UTC: 2026-06-19T17:38:30Z
  Message: Pilot cleanup script capability folder
  Summary: Moved cleanup-empty-chat-branches into scripts/00.chat/git/cleanup-empty-chat-branches with script and smoke-test colocated, retained old shared paths as wrappers, and updated bootstrap audit classification for capability folders.
  ADR impact: ADR 0017 accepted after the cleanup-empty-chat-branches pilot passed direct and compatibility checks.


- Commit: `db84985`
  Time UTC: 2026-06-19T17:48:40Z
  Message: Point cleanup references at canonical script
  Summary: Updated cleanup workflow, startup cleanup, public alias, smoke fixtures, and bootstrap audit behavior so normal references use scripts/00.chat/git/cleanup-empty-chat-branches/script.sh while old shared paths remain compatibility-only.
  ADR impact: ADR 0017 migration rule reinforced: canonical paths by default, old paths only for compatibility notes and wrappers.


- Commit: `e627fbe`
  Time UTC: 2026-06-19T18:04:15Z
  Message: Move chat command dispatcher capability
  Summary: Moved the chat command dispatcher and smoke test into scripts/00.chat/command/dispatcher, added a capability README explaining dispatcher behavior, kept old shared paths as compatibility wrappers, and updated normal command references to the canonical path.
  ADR impact: ADR 0017 now records the dispatcher as a second capability-folder pilot.


- Commit: `ef10b3e`
  Time UTC: 2026-06-19T18:14:18Z
  Message: Move chat reporting capabilities
  Summary: Moved chat workspace reporting and commit log summary generation into scripts/00.chat/reporting capability folders, retained old shared paths as compatibility wrappers, updated public aliases, reporting docs, smoke fixtures, and ADR 0017.
  ADR impact: ADR 0017 now records the reporting batch and the temporary governed-runner wrapper exception.


- Commit: `bfdc0fe`
  Time UTC: 2026-06-19T18:18:49Z
  Message: Move chat audit capabilities
  Summary: Moved chat layer migration and bootstrap file-set audits into scripts/00.chat capability folders, retained old shared paths as compatibility wrappers, updated public aliases, bootstrap docs, migration docs, and ADR 0017.
  ADR impact: ADR 0017 now records the audit batch and the temporary governed-runner wrapper exception.


- Commit: `0fd6780`
  Time UTC: 2026-06-19T18:23:04Z
  Message: Move chat classification capability
  Summary: Moved chat task classification, fixture check, and fixtures into scripts/00.chat/classification/classify-task, retained old executable paths as compatibility wrappers, and updated startup, docs, and smoke fixtures to use canonical classifier paths.
  ADR impact: ADR 0017 now records the classification batch.


- Commit: `b0130c3`
  Time UTC: 2026-06-19T18:35:50Z
  Message: Move chat session-log executable helpers
  Summary: Moved executable session-log helpers into scripts/00.chat/session-log capability folders, retained old executable paths as compatibility wrappers, updated canonical references, smoke fixtures, and the bootstrap audit surface; left the sourced session-log-paths library for a separate migration pass.
  ADR impact: ADR 0017 records the session-log executable batch and the deferred sourced-library/governed-runner exceptions.


- Commit: `d4b1186`
  Time UTC: 2026-06-19T18:42:56Z
  Message: Move chat transcript and metrics helpers
  Summary: Moved Codex transcript discovery, transcript registration, and chat cost estimation into scripts/00.chat transcript/metrics capability folders; retained old shared paths as compatibility wrappers and updated direct callers, smoke fixtures, and the bootstrap audit.
  ADR impact: ADR 0017 records the transcript and metrics batch result.


- Commit: `0457a48`
  Time UTC: 2026-06-19T18:47:26Z
  Message: Retire obsolete chat compatibility wrappers
  Summary: Removed unreferenced shared chat command and smoke-test compatibility wrappers after proving public aliases and canonical smoke tests still pass; retained governed-runner compatibility wrappers for a later path-policy migration.
  ADR impact: ADR 0017 now distinguishes retired wrappers from compatibility wrappers that remain due to governed-runner allowlist dependencies.


- Commit: `c4b40b6`
  Time UTC: 2026-06-19T18:55:47Z
  Message: Move chat session-log path library
  Summary: Moved the session-log path helper library to scripts/00.chat/session-log/paths/lib.sh, kept scripts/shared/chat/session-log-paths.sh as a source-compatible shim, updated canonical chat callers, and taught smoke fixtures to copy the canonical library with the shim.
  ADR impact: ADR 0017 now records the source-library migration and remaining compatibility-shim boundary.


- Commit: `670dfc6`
  Time UTC: 2026-06-19T19:03:48Z
  Message: Move chat worktree path library
  Summary: Moved chat worktree path helpers to scripts/00.chat/worktree/paths/lib.sh, kept scripts/shared/chat/chat-worktree-paths.sh as a source-compatible shim, updated the canonical reporting caller, and adjusted smoke fixtures to copy the canonical library with the shim.
  ADR impact: ADR 0017 now records the worktree source-library migration and remaining compatibility-shim boundary.


- Commit: `fc0fe5d`
  Time UTC: 2026-06-19T19:11:52Z
  Message: Move chat worktree ensure helper
  Summary: Moved ensure-chat-worktree into scripts/00.chat/worktree/ensure-chat-worktree/script.sh, kept the old shared path as a compatibility wrapper, updated workflows to point to the canonical helper, and adjusted smoke fixtures.
  ADR impact: ADR 0017 records the canonical worktree helper and remaining compatibility wrapper boundary.


- Commit: `95b19c1`
  Time UTC: 2026-06-19T19:15:26Z
  Message: Move chat closeout command
  Summary: Moved the chat closeout prompt command to scripts/00.chat/closeout/build-closeout-prompt/script.sh, kept the shared command path as a dispatcher-compatible wrapper, and updated smoke fixtures and ADR 0017.
  ADR impact: ADR 0017 records the closeout command batch and remaining command-discovery compatibility wrapper.


- Commit: `b05a045`
  Time UTC: 2026-06-19T19:20:39Z
  Message: Move chat new-session command
  Summary: Moved the chat new-session command launcher to scripts/00.chat/startup/start-new-chat/script.sh, kept the shared command path as a dispatcher-compatible wrapper, and updated smoke fixtures plus start-chat-session metadata.
  ADR impact: ADR 0017 records the new-session command batch and remaining command-discovery compatibility wrapper.


- Commit: `7372552`
  Time UTC: 2026-06-19T19:24:46Z
  Message: Move chat auto-start helper
  Summary: Moved opening-prompt auto-start into scripts/00.chat/startup/auto-start-missing-session/script.sh, kept the old request-initialization path as a governed-runner-compatible wrapper, and updated dispatcher metadata, smoke fixtures, and ADR 0017.
  ADR impact: ADR 0017 records the auto-start helper batch and the remaining governed-runner path-policy exception.


- Commit: `4a91c54`
  Time UTC: 2026-06-19T19:31:26Z
  Message: Move chat session startup engine
  Summary: Moved start-chat-session into scripts/00.chat/startup/start-chat-session with a capability README, kept the old request-initialization path as a compatibility wrapper, and updated startup callers and smoke fixtures.
  ADR impact: ADR 0017 records the startup engine migration and remaining compatibility boundary.


- Commit: `0b09130`
  Time UTC: 2026-06-19T19:35:09Z
  Message: Expand chat startup README
  Summary: Expanded the start-chat-session capability README into an educational guide that explains the chat startup mental model, each startup action, and what the script deliberately does not do.
  ADR impact: The README now teaches why startup creates a branch, worktree, session log, first prompt, and cleanup pass before agent work begins.


- Commit: `4136277`
  Time UTC: 2026-06-19T19:45:07Z
  Message: Clarify terminal prompt handoff
  Summary: Clarified that CHAT_COPY_PROMPT is terminal handoff convenience rather than the startup contract, and documented that IDE/app integrations should consume startup data directly.
  ADR impact: Added an ADR 0017 follow-up to revisit the terminal prompt handoff interface after the current script organization stream.


- Commit: `3775644`
  Time UTC: 2026-06-19T19:48:20Z
  Message: Move chat startup smoke test
  Summary: Moved the chat startup worktree smoke test beside the start-chat-session capability, kept the old shared git smoke path as a compatibility wrapper, and documented the smoke coverage in the capability README and ADR 0017.
  ADR impact: Validated both the canonical smoke path and old wrapper path, plus the bootstrap file-set audit, metadata headers, governed drift, and pre-commit gate.


- Commit: `64e4cbc`
  Time UTC: 2026-06-19T19:51:12Z
  Message: Document chat auto-start capability
  Summary: Added an educational README for the auto-start-missing-session startup capability, explaining opening-prompt recovery startup, routing decisions, validation coverage, and the compatibility wrapper boundary.
  ADR impact: ADR 0017 now records the auto-start README and notes that dispatcher smoke covers opening-prompt auto-start behavior.


- Commit: `0cdbc73`
  Time UTC: 2026-06-19T20:01:01Z
  Message: Move chat commit recording capability
  Summary: Moved record-chat-commit and its metrics smoke test into scripts/00.chat/session-log/record-chat-commit, added a capability README, kept old shared git paths as compatibility wrappers, and updated helper metadata plus ADR 0017.
  ADR impact: Validated canonical and compatibility smoke paths, bootstrap file-set audit, metadata headers, governed command drift, syntax checks, and the pre-commit gate.


- Commit: `3d822d7`
  Time UTC: 2026-06-19T20:06:11Z
  Message: Move chat session checkpoint capability
  Summary: Moved checkpoint-chat-session-log into scripts/00.chat/session-log/checkpoint-chat-session-log, added a capability README, kept the old governed shared path as a compatibility wrapper, and updated ADR 0017 plus session-log helper metadata.
  ADR impact: Validated canonical and wrapper dry-run behavior in a throwaway repo, bootstrap file-set audit, metadata headers, governed command drift and smoke, syntax checks, and pre-commit gate.


- Commit: `7a7c0c7`
  Time UTC: 2026-06-19T20:13:26Z
  Message: Move chat commit readiness gate
  Summary: Moved prepare-chat-session-before-commit into scripts/00.chat/session-log/prepare-chat-session-before-commit, added a capability README, kept the old governed shared path as a compatibility wrapper, and updated ADR 0017 plus metadata references.
  ADR impact: Validated syntax, bootstrap file-set audit, metadata headers, governed command drift, and the approved wrapper path through the governed runner.


- Commit: `007941c`
  Time UTC: 2026-06-19T20:18:13Z
  Message: Move chat commit prerequisite gate
  Summary: Moved check-commit-prerequisites and its smoke test into scripts/00.chat/session-log/check-commit-prerequisites, added a capability README, kept old shared git paths as compatibility wrappers, and updated the prepare gate plus ADR metadata.
  ADR impact: Validated canonical and wrapper smoke paths, bootstrap audit, metadata headers, governed command drift, syntax checks, and the approved prepare gate path.


- Commit: `97c25cf`
  Time UTC: 2026-06-19T20:20:16Z
  Message: Move chat commit log deletion gate
  Summary: Moved check-commitlog-deletions and its smoke test into scripts/00.chat/session-log/check-commitlog-deletions, added a capability README, kept old shared git paths as compatibility wrappers, and updated the prepare gate plus ADR 0017.
  ADR impact: Validated canonical and wrapper smoke paths, bootstrap audit, metadata headers, governed command drift, syntax checks, and the approved prepare gate path.


- Commit: `5b746e0`
  Time UTC: 2026-06-19T20:22:11Z
  Message: Move chat write-location gate
  Summary: Moved check-write-location into scripts/00.chat/worktree/check-write-location, added a capability README, kept the old shared git path as a compatibility wrapper, and updated the prepare gate, worktree metadata, and ADR 0017.
  ADR impact: Validated canonical and wrapper outputs, bootstrap audit, metadata headers, governed command drift, syntax checks, and the approved prepare gate path.


- Commit: `8ae71e4`
  Time UTC: 2026-06-19T20:23:56Z
  Message: Move chat dirty worktree gate
  Summary: Moved dirty-worktree-check into scripts/00.chat/worktree/dirty-worktree-check, added a capability README, kept the old shared git path as a compatibility wrapper, and updated ADR 0017.
  ADR impact: Validated clean, bookkeeping-only, wrapper, and mixed-dirty failure behavior in a throwaway repo, plus bootstrap audit, metadata headers, governed command drift, and syntax checks.


- Commit: `a06b99e`
  Time UTC: 2026-06-19T20:27:14Z
  Message: Document remaining shared git migration inventory
  Summary: Added an ADR 0017 inventory classifying remaining scripts/shared/git files into moved compatibility wrappers, chat refresh/local convergence candidates, and isolated chat branch execution helpers.
  ADR impact: The inventory records that remaining shared git files are still owner 00.chat by metadata and recommends migrating refresh/local convergence before isolated chat branch execution helpers.


- Commit: `ece9f31`
  Time UTC: 2026-06-19T20:50:22Z
  Message: Add governed recovery import for active worktree paths
  Summary: Added a governed recovery capability to import explicit paths from an active worktree into the session chat-owned worktree, converted the old staging helper into a compatibility wrapper, documented ADR supersession boundaries, and added smoke coverage.
  ADR impact: ADR 0009 now records recovery-only successor behavior; ADR 0011 documents recovery import for wrong-worktree edits; ADR 0017 records the recovery import batch.


- Commit: `24e0087`
  Time UTC: 2026-06-19T21:03:27Z
  Message: Move main refresh status checks to readable capability names
  Summary: Moved main-refresh status and readiness checks to human-readable canonical capability folders, retained old shared git paths as wrappers, updated refresh workflow and callers, and added capability READMEs.
  ADR impact: ADR 0017 records the main refresh status/readiness batch; ADR 0011 now points to the readable freshness check.


- Commit: `4e080db`
  Time UTC: 2026-06-19T21:11:44Z
  Message: Move main refresh rehearse and apply scripts
  Summary: Moved main-refresh rehearsal and apply operations into readable canonical capability folders, kept old shared git paths as compatibility wrappers, updated refresh workflow/cleanup/conflict docs, and retained end-to-end smoke coverage.
  ADR impact: ADR 0017 records the main refresh rehearse/apply batch and notes the destructive apply path remains outside the always-approved runner surface.


- Commit: `b76d05c`
  Time UTC: 2026-06-19T21:16:42Z
  Message: Move local merge readiness verifier
  Summary: Moved the local-main merge readiness verifier and smoke test into a readable local-merge capability folder, retained shared git compatibility wrappers, updated the promote-to-main workflow, and switched the verifier to canonical session/worktree helper libraries.
  ADR impact: ADR 0017 records the local merge readiness batch; ADR 0011 now describes local merge verification as the explicit path into main.


- Commit: `7b756a6`
  Time UTC: 2026-06-19T21:22:35Z
  Message: Move local merge visibility reports
  Summary: Moved local-merge visibility reports to canonical 00.chat paths, added READMEs, retained compatibility wrappers, and updated workflow, runner, and ADR references.
  ADR impact: covered by session ADR disposition


- Commit: `219c37f`
  Time UTC: 2026-06-19T21:28:08Z
  Message: Classify isolated worktree helpers as superseded
  Summary: Marked the old isolated worktree command runner and staging adapter as superseded compatibility helpers, clarified ADR guidance, and kept retirement review separate from canonical migration.
  ADR impact: covered by session ADR disposition


- Commit: `6a00306`
  Time UTC: 2026-06-19T21:33:15Z
  Message: Document compatibility wrapper retirement rules
  Summary: Added a wrapper retirement map to ADR 0017 and updated the public chat alias README to point at canonical 00.chat implementations.
  ADR impact: covered by session ADR disposition


- Commit: `61f07ce`
  Time UTC: 2026-06-19T21:42:11Z
  Message: Advertise canonical chat paths in governed runner
  Summary: Updated the governed runner to advertise canonical 00.chat paths, retained compatibility acceptance, updated agent-facing examples, and expanded governed command drift checks for canonical approved-action references.
  ADR impact: covered by session ADR disposition


- Commit: `8dab55e`
  Time UTC: 2026-06-19T21:46:55Z
  Message: Move chat command discovery to canonical folders
  Summary: Moved chat command discovery to canonical 00.chat command folders, added canonical new and close command entrypoints, retained shared command wrappers, and updated command docs, smoke tests, and ADR guidance.
  ADR impact: covered by session ADR disposition


- Commit: `074600e`
  Time UTC: 2026-06-19T21:50:47Z
  Message: Classify bootstrap install compatibility paths
  Summary: Documented bootstrap audit semantics and classified public install surfaces, shared governance primitives, required old-path wrappers, superseded legacy paths, and validation-only compatibility candidates in ADR 0017.
  ADR impact: covered by session ADR disposition


- Commit: `902b139`
  Time UTC: 2026-06-19T21:57:00Z
  Message: Move llm-workbench upstream helper to canonical path
  Summary: Moved the llm-workbench upstream availability helper to scripts/00.chat/upstream, kept the old shared path as a compatibility wrapper, updated governed runner advertising, smoke coverage, metadata, and ADR 0017.
  ADR impact: covered by session ADR disposition


- Commit: `54300d0`
  Time UTC: 2026-06-19T21:59:58Z
  Message: Classify validation smoke wrappers for retirement
  Summary: Recorded that the old shared git smoke-test wrappers are validation-only compatibility wrappers with canonical scripts/00.chat smoke-test targets, and split them out from broader bootstrap compatibility candidates.
  ADR impact: ADR 0017 now separates validation-only smoke wrapper retirement candidates from bootstrap/install compatibility paths.


- Commit: `8703814`
  Time UTC: 2026-06-19T22:03:04Z
  Message: Retire validation-only smoke wrappers
  Summary: Removed eight old shared git smoke-test compatibility wrappers after canonical scripts/00.chat smoke tests passed and the bootstrap audit stayed clean.
  ADR impact: ADR 0017 now records the validation-only smoke wrappers as retired historical paths with canonical replacements.


- Commit: `c8bdc1c`
  Time UTC: 2026-06-19T22:06:48Z
  Message: Retire validation-only chat helper wrappers
  Summary: Removed four old shared chat transcript/session-log compatibility wrappers after confirming canonical scripts/00.chat replacements, no live old-path references, and a clean bootstrap audit.
  ADR impact: ADR 0017 now records the retired chat helper wrappers and their canonical transcript/session-log replacements.


- Commit: `5d51c4b`
  Time UTC: 2026-06-19T22:09:44Z
  Message: Retire validation-only classification wrappers
  Summary: Removed two old request-initialization classification compatibility wrappers after confirming canonical classification paths, no live old-path references, and a clean bootstrap audit.
  ADR impact: ADR 0017 now records the retired classification wrappers and their canonical classification replacements.


- Commit: `5faa9c8`
  Time UTC: 2026-06-19T22:22:42Z
  Message: Replace chat aliases with package scripts
  Summary: Replaced the public scripts/chat alias surface with package.json chat:* commands, added package-script smoke coverage, updated bootstrap and migration docs/audits, and removed the old scripts/chat aliases.
  ADR impact: ADR 0017 now records package.json chat scripts as the public command surface and scripts/chat aliases as retired historical paths.


- Commit: `c0e163d`
  Time UTC: 2026-06-19T22:28:07Z
  Message: Retire remaining validation compatibility wrappers
  Summary: Removed the remaining Track A validation-only wrappers after moving startup and command smoke fixtures to canonical scripts/00.chat paths and confirming bootstrap audit stayed clean.
  ADR impact: ADR 0017 now records the remaining validation compatibility wrappers as retired Track A paths with canonical replacements.


- Commit: `c9a384f`
  Time UTC: 2026-06-19T22:31:27Z
  Message: Retire shared command wrappers
  Summary: Removed old shared chat command compatibility wrappers after command and package smoke fixtures moved to canonical command scripts and package scripts.
  ADR impact: ADR 0017 now records shared command wrappers as retired historical paths.


- Commit: `25f068e`
  Time UTC: 2026-06-19T22:34:35Z
  Message: Retire read-only governed runner wrappers
  Summary: Removed four old shared read-only/reporting wrappers from the governed runner compatibility surface after canonical runner paths remained green and old paths were rejected as intended.
  ADR impact: ADR 0017 now records the read-only governed runner wrappers as retired historical paths.


- Commit: `26264d6`
  Time UTC: 2026-06-19T22:39:55Z
  Message: Retire read-only shared git wrappers
  Summary: Removed the remaining read-only shared git compatibility wrappers for local merge visibility/readiness and main-refresh status/readiness, kept canonical scripts/00.chat paths as the operative entrypoints, updated ADR 0017 and source-packet references, and removed the old paths from the governed runner allowlist.
  ADR impact: ADR 0017 now records these shared git wrappers as retired compatibility paths.


- Commit: `47a61c4`
  Time UTC: 2026-06-19T23:26:18Z
  Message: Retire shared chat command wrappers
  Summary: Removed the remaining executable scripts/shared/chat compatibility wrappers for upstream repo setup, chat-log rename, and auto-start. Updated the governed runner, smoke tests, and capability docs so canonical scripts/00.chat paths are the only operative command entrypoints.
  ADR impact: ADR 0017 now records these shared chat command wrappers as retired compatibility paths.


- Commit: `1accd0a`
  Time UTC: 2026-06-19T23:34:14Z
  Message: Retire shared chat source shims
  Summary: Removed the final scripts/shared/chat source shims after migrating runtime callers and smoke fixtures to canonical scripts/00.chat session-log and worktree path libraries. Updated chat workflows, command docs, bootstrap guidance, ADR 0017, and runner path acceptance to reflect the canonical-only chat layout.
  ADR impact: ADR 0017 now records the source shims as retired compatibility paths.


- Commit: `b3897eb`
  Time UTC: 2026-06-19T23:43:03Z
  Message: Retire shared git gate wrappers
  Summary: Migrated active chat gate workflows, checklists, READMEs, smoke tests, and governed runner allowlists to canonical scripts/00.chat paths, then removed the old scripts/shared/git gate wrappers.
  ADR impact: ADR 0017 now records the shared git gate wrappers as retired compatibility paths.


- Commit: `94117e5`
  Time UTC: 2026-06-19T23:49:40Z
  Message: Retire main refresh preflight wrapper
  Summary: Removed the obsolete shared git preflight-main-refresh compatibility wrapper after confirming main-refresh rehearsal is owned by the canonical scripts/00.chat/main-refresh/rehearse-refresh-from-main path and the bootstrap audit no longer needs the wrapper.
  ADR impact: ADR 0017 now records preflight-main-refresh as retired compatibility.


- Commit: `358cab4`
  Time UTC: 2026-06-19T23:54:33Z
  Message: Retire isolated chat branch helpers
  Summary: Removed the superseded shared git isolated-command runner, active-worktree staging wrapper, and legacy smoke test after proving canonical chat-owned worktrees plus the recovery import cover the useful behavior and no active bootstrap, install, workflow, or governed runner surface depends on the old paths.
  ADR impact: ADR 0009 now records the isolated-runner model as historical, and ADR 0017 records the legacy trio as retired superseded paths.


- Commit: `7217f55`
  Time UTC: 2026-06-19T23:59:39Z
  Message: Reconcile chat docs after shared git retirement
  Summary: Updated chat-layer README, migration plan, and bootstrap workflow so human instructions point at canonical scripts/00.chat capabilities and shared harness governance instead of the retired scripts/shared/git surface; also removed stale empty shared-git fixture directories from canonical smoke tests.
  ADR impact: No new ADR; this reconciles docs and validation fixtures after ADR 0017 retired the shared git compatibility paths.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: The existing upstream bootstrap ADR already owns this productization
direction; this change adds deterministic enforcement support rather than a new
architecture decision.

## Session Metrics

Raised at UTC: 2026-06-19T16:34:46Z
Latest commit at UTC: 2026-06-19T23:59:39Z
Latest commit SHA: 7217f55
Chat duration: 26693s (00:07:24:53)
Estimated chat tokens: 4486674 estimated from chat transcript bytes (17946694 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/19/rollout-2026-06-19T15-57-23-019ee062-f943-71b2-a975-e5a9172decbe.jsonl)
Estimated chat cost: USD 134.60 estimated from estimated_chat_tokens
Estimated chat cost basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing

## Notes

- Current audit output reports no unclassified candidates.
- Public `scripts/chat/*.sh` files are thin aliases and are tagged as
  `llm-workbench-required`.
- Root `scripts/shared/chat/` scripts were classified as required,
  validation, source-only, or internal based on workflow references and smoke
  test usage.
- `scripts/shared/chat/commands/` and `request-initialization/` scripts were
  classified as chat startup command/runtime files.
- `scripts/shared/git/` scripts were classified as required Git gates,
  approved mutators, refresh helpers, compatibility helpers, or validation
  smoke tests.
- `scripts/shared/harness/` scripts were classified as required harness gates,
  runner infrastructure, or validation smoke tests.
- Added proposed ADR 0017 for organizing scripts by owner, domain, and
  capability folder before moving files.
