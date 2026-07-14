# Chat Session: 2026-07-13-17-07 continue-platform-shell-first-deploy-blockers-from-pushed-ma

<!-- agentic-session
id: 2026-07-13-17-07-continue-platform-shell-first-deploy-blockers-from-pushed-ma
task: Continue platform shell first-deploy blockers from pushed main
branch: chat/2026-07-13-17-07-continue-platform-shell-first-deploy-blockers-from-pushed-ma
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-13-17-07-continue-platform-shell-first-deploy-blockers-from-pushed-ma-2925720926
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-07-13T16:07:37Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-07-14T10:32:40Z
latest_commit_sha: 0467182db26e767361584f85177e1172da37447e
chat_duration: 66303s (00:18:25:03)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

Continue platform shell first-deploy blockers from pushed main

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.
- Continued from pushed `main` at merge commit `f2cba0e4fe47f607bff7958a9f7f3f784b425678`.
- Selected the next blocker-reduction slice: make the GitHub/OIDC image build path concrete without running an ECS deployment.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- Treat this slice as deployment-path preparation, not live AWS deployment execution.
- Add `.github/workflows/deploy-platform-shell-staging.yml` as the selected manual staging workflow from the target profile.
- Keep the workflow environment-gated as `staging`, restricted to `refs/heads/main`, and OIDC-enabled with `id-token: write`.
- Have the workflow build and optionally publish the `platform-shell` image, resolve a digest-pinned base image for the run, resolve the immutable ECR image digest, read ECR scan counts, and write the evidence to the GitHub step summary.
- Leave ECS service creation, ALB target group/rule, DNS proof, deployed smoke, and rollback proof blocked for the next runtime-target slice.

## Context Hygiene

- Used root `main` only for startup and source-of-truth inspection; task edits are in the chat-owned worktree.
- Re-read `.agentic/00.chat/workflows/chat-start.md`, `.agentic/product/workflows/platform-runtime-implementation.md`, `.agentic/aws/workflows/execute-approved-aws-change.md`, the platform runtime plan, target profile, deploy-readiness manifest, existing RAG deploy workflow, platform-shell image scripts, and deploy-readiness verifier before editing.
- Memory quick-pass found prior platform-runtime continuation notes and the warning to re-check live deploy-readiness state before assuming blockers.

## Activity Log

### 2026-07-13T16:07:37Z - Session started

Initial intent: Continue platform shell first-deploy blockers from pushed main

### 2026-07-13T16:12:37Z - GitHub/OIDC image workflow slice

- Added the manual `Deploy Platform Shell Staging` workflow at `.github/workflows/deploy-platform-shell-staging.yml`.
- Updated the Kanbien staging deploy-readiness manifest to record `remote-main` source policy and confirmed workflow OIDC permission.
- Updated the platform-shell deploy-readiness verifier to require the referenced GitHub workflow file, `workflow_dispatch`, `id-token: write`, and the protected `staging` environment.
- Updated verifier README coverage text.
- Validation:
  - `git diff --check` passed.
  - Workflow YAML parsed with Python/PyYAML.
  - `bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh --manifest infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml --allow-blocked --caller-intent planning --json` passed with blocked planning status and 7 blockers.
  - `bash scripts/04.deploy/verify-platform-shell-deploy-readiness/smoke-test.sh` passed.
  - `bash scripts/04.deploy/validate-container-boundaries/script.sh` passed.
  - `npm run platform:server:check` initially failed before dependencies were installed because `tsc` was missing, then passed after `npm ci --ignore-scripts`.
  - `npm run product:kanbien-platform:check` initially failed before dependencies were installed because `tsc` was missing, then passed after `npm ci --ignore-scripts`.

### 2026-07-13T16:13:20Z - Recognition metadata refresh

- Ran `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --write-all`.
- Generated artifact recognition metadata now indexes `.github/workflows/deploy-platform-shell-staging.yml`.


### 2026-07-14T10:32:40Z - Commit recorded

Commit: `0467182db26e767361584f85177e1172da37447e`

Message: Add platform shell staging image workflow

Summary: Added the manual GitHub/OIDC staging image workflow for platform-shell, updated deploy-readiness source/OIDC evidence, taught the readiness verifier to validate workflow presence and OIDC permissions, refreshed generated recognition metadata, and recorded validation evidence.

ADR impact: No ADR change; this implements the selected GitHub/OIDC image provenance path without changing runtime family, auth provider, or live AWS topology.

## Sub-Agent Activity

- None recorded yet.

## Commits



- Commit: `0467182db26e767361584f85177e1172da37447e`
  Time UTC: 2026-07-14T10:32:40Z
  Message: Add platform shell staging image workflow
  Summary: Added the manual GitHub/OIDC staging image workflow for platform-shell, updated deploy-readiness source/OIDC evidence, taught the readiness verifier to validate workflow presence and OIDC permissions, refreshed generated recognition metadata, and recorded validation evidence.
  ADR impact: No ADR change; this implements the selected GitHub/OIDC image provenance path without changing runtime family, auth provider, or live AWS topology.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This slice implements the previously selected GitHub/OIDC staging image path and does not change the durable runtime, auth, or AWS family decisions.

## Session Metrics

Raised at UTC: 2026-07-13T16:07:37Z
Latest commit at UTC: 2026-07-14T10:32:40Z
Latest commit SHA: 0467182db26e767361584f85177e1172da37447e
Chat duration: 66303s (00:18:25:03)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- None recorded yet.
