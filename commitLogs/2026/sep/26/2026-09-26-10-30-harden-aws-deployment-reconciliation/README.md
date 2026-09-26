# Chat Session: 2026-09-26-10-30 harden-aws-deployment-reconciliation

<!-- agentic-session
id: 2026-09-26-10-30-go
task: go
branch: chat/2026-09-26-10-30-go
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-09-26-10-30-go-1559333672
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-09-26T09:30:58Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-09-26T15:41:48Z
latest_commit_sha: 2ab8dacddeeb25b910e65c65a0fb9c764baf6740
chat_duration: 22250s (00:06:10:50)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

go

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised



- Raised: Foundation template exceeded CloudFormation's inline size limit
  Resolution: Defined a separate private target-owned CloudFormation artifact store instead of reusing legacy, audit, or cross-environment storage.


- Raised: Artifact-store review change set failed CloudFormation property validation
  Resolution: No resource was created. Verified the AWS CloudFormation S3 lifecycle-rule schema, replaced unsupported Filter syntax with direct Prefix syntax, and passed local plus AWS template validation.


- Raised: Foundation change-set shorthand input could not preserve the comma-separated subnet value
  Resolution: No change set was created by the rejected local request. Used an uncommitted JSON deployment-parameter file so CloudFormation received one exact PrivateSubnetIds value.


- Raised: GitHub reconciliation proof showed CloudFormation drift-status lookup cannot be constrained to the reviewed stack ARN
  Resolution: Did not broaden IAM. Replaced that lookup with a fresh LastCheckTimestamp plus IN_SYNC stack-status check using only the existing scoped DescribeStacks permission.


- Raised: The first GitHub reconciliation proof returned only aws-verification-unavailable after its dedicated role successfully assumed and issued declared read requests; the failure could not identify the owning safe control.
  Resolution: Reconciliation now attributes an unavailable provider call to its owning safe check while preserving the no-response-output policy. Focused source, static policy, infrastructure, and live administrator reconciliation checks passed.


- Raised: The hardened GitHub reconciliation run still blocks at artifact-stack drift despite exact-resource IAM simulation and successful administrator reconciliation.
  Resolution: Drift verification now reports whether the bounded failure occurs when starting detection or reading the fresh stack summary, without exposing AWS provider payloads or widening IAM.

- Raised: CloudFormation active drift detection requires provider-dependent reads that the narrow GitHub reconciliation identity cannot safely own.
  Resolution: Kept GitHub passive, added a complete target resource-type inventory and a source/live role-policy alignment check, and planned a separate detector behind a reviewed permission and cost boundary.

- Raised: The narrowed GitHub role passed source/live policy alignment and IAM simulation, but its first live reconciliation blocked at the grouped artifact-bucket control.
  Resolution: Did not add a permission. Split every artifact-bucket provider read into an independently attributable, fail-closed safe control so the next live proof identifies the exact unavailable operation without exposing a provider response.

## Decisions Made

- Stage 4 defines the private PostgreSQL reference target in source and stops at a reviewed CloudFormation change set; it does not provision the target until AWS SSO is restored and the change set is inspected.
- The reference target has no public endpoint, uses encrypted private RDS storage, narrowly scoped network paths, generated secrets, and non-secret SSM configuration.


- Decision: Use a separate target-owned artifact-store bootstrap stack
  Rationale: It removes the template-transport circular dependency while retaining least-privilege, encryption, public-access blocks, TLS-only access, and bounded lifecycle controls.


- Decision: Require fail-closed staging deployment reconciliation before infrastructure mutation
  Rationale: A dedicated source policy, static verifier, local/live reconciliation command, and read-only GitHub OIDC workflow now guard source/live agreement; any mismatch blocks the change set.


- Decision: Preserve scoped CloudFormation reconciliation without wildcard drift-status permission
  Rationale: Fresh stack drift timestamps provide the required fail-closed evidence while keeping the GitHub role restricted to the two declared stack ARNs.


- Decision: Run staging reconciliation AWS calls serially, with three bounded retries, instead of launching CloudFormation, S3, and Budgets checks concurrently.
  Rationale: The GitHub role can perform each exact read in IAM simulation and administrator reconciliation succeeds. Serial bounded calls remove avoidable provider burst and timing instability while retaining fail-closed output and no added permissions.

- Decision: Separate active CloudFormation drift detection from GitHub reconciliation.
  Rationale: The GitHub role must prove only the operations it safely owns. A detector may be introduced only after every stack resource type has an authoritative provider-read contract, a separate role, a cost review, and a controlled live proof.

- Decision: Require operation-level safe diagnostics for grouped provider controls.
  Rationale: Source policy and IAM simulation are useful preflight evidence, but neither proves an operational identity's live request path. A grouped provider check cannot guide a least-privilege repair without risking speculative permission expansion.

## Context Hygiene

- Summary: Stage 4 source is locally validated; only the AWS SSO-expired change-set review remains operationally unresolved.
  Durable evidence: Durable source and readiness evidence: infra/04.deploy/03.product/targets/kanbien/staging/ and docs/aws/kanbien-staging-postgresql-relational-reference-v1-deployment-plan.md


- Summary: Stage 4 source is extended with the artifact-store prerequisite; artifact store and Foundation change sets remain independently reviewed.
  Durable evidence: ADR 0034, target CloudFormation source, and the PostgreSQL deployment plan


- Summary: The retry has one narrowly scoped source correction and preserves the two-resource review boundary.
  Durable evidence: The corrected artifact-store template, its static verifier, ADR 0034, and the current session log.


- Summary: Stage 4 now has source checks, a deployed hardened artifact store, and an available but unexecuted relational Foundation change set.
  Durable evidence: Target profile, readiness record, PostgreSQL deployment plan, product plan, static verifiers, and this session log; no secret, endpoint, record, message, or provider payload was recorded.


- Summary: The live budget uses the canonical name kanbien-staging-platform-shell-monthly; the prior source-only suffix was stale and would have caused a deployment mismatch.
  Durable evidence: Target profile, reconciliation command and policy checker, ADR 0035, PostgreSQL plan, staging deployment plan, and readiness record.


- Summary: The first GitHub reconciliation run failed safely because DescribeStackDriftDetectionStatus was not authorisable against a stack ARN. The corrected design uses only scoped DescribeStacks plus DetectStackDrift and has passed locally against staging.
  Durable evidence: Reconciliation command, IAM source, static verifier, target profile/readiness, ADR 0035, and the GitHub workflow run evidence.

- Summary: The source now prevents GitHub from starting provider-dependent drift scans, validates the full target resource-type inventory, and compares the live inline role policy to reviewed source before a Foundation change can execute.
  Durable evidence: ADR 0036, the AWS change reliability programme, target drift-detection contract, reconciliation command, and static infrastructure checks. The separate detector has not been deployed.

## Activity Log

### 2026-09-26T09:30:58Z - Session started

Initial intent: go

### 2026-09-26T10:00:00Z - PostgreSQL Stage 4 source checkpoint

- Added the private relational persistence, access, workload-configuration, and operations CloudFormation fragments.
- Added static source verification and incorporated it into the platform-shell infrastructure verifier.
- Passed adapter checks, disposable PostgreSQL integration proof, image build, full infrastructure checks, and whitespace validation.
- AWS SSO was found expired before any AWS change-set operation. No AWS resources were changed.


### 2026-09-26T10:05:04Z - Context hygiene

Summary: Stage 4 source is locally validated; only the AWS SSO-expired change-set review remains operationally unresolved.

Durable evidence: Durable source and readiness evidence: infra/04.deploy/03.product/targets/kanbien/staging/ and docs/aws/kanbien-staging-postgresql-relational-reference-v1-deployment-plan.md


### 2026-09-26T10:05:04Z - ADR disposition

ADR needed: no

Reason: Stage 4 implements the already-approved PostgreSQL relational-reference plan without making a new durable architectural choice.



### 2026-09-26T10:06:31Z - Commit recorded

Commit: `9d78962d`

Message: feat(persistence): define PostgreSQL staging target

Summary: Defined and statically verified the private encrypted PostgreSQL relational-reference target; AWS change-set review remains pending an SSO refresh.

ADR impact: No new ADR; implements the approved relational-reference programme.


### 2026-09-26T11:07:12Z - Issue

Raised: Foundation template exceeded CloudFormation's inline size limit

Resolution: Defined a separate private target-owned CloudFormation artifact store instead of reusing legacy, audit, or cross-environment storage.


### 2026-09-26T11:07:12Z - Decision

Decision: Use a separate target-owned artifact-store bootstrap stack

Rationale: It removes the template-transport circular dependency while retaining least-privilege, encryption, public-access blocks, TLS-only access, and bounded lifecycle controls.


### 2026-09-26T11:07:12Z - Context hygiene

Summary: Stage 4 source is extended with the artifact-store prerequisite; artifact store and Foundation change sets remain independently reviewed.

Durable evidence: ADR 0034, target CloudFormation source, and the PostgreSQL deployment plan


### 2026-09-26T11:07:13Z - ADR disposition

ADR needed: yes

ADR path: docs/04.deploy/adrs/0034-use-private-target-owned-cloudformation-artifact-stores.md

Reason: The target's CloudFormation transport boundary is a durable deployment architecture decision.


### 2026-09-26T11:08:54Z - Commit recorded

Commit: `faedcb71`

Message: feat(deploy): add private template artifact store

Summary: Added a separately reviewed private encrypted CloudFormation template store to bridge AWS's inline-template limit without reusing unrelated storage.

ADR impact: ADR 0034 records the target-owned template-transport boundary.


### 2026-09-26T11:11:16Z - Commit recorded

Commit: `568c6551`

Message: fix(deploy): clean up failed artifact store bootstrap

Summary: Use RetainExceptOnCreate so a failed first artifact-store deployment leaves no retained bucket while successful evidence remains protected.

ADR impact: No new ADR; strengthens the ADR 0034 rollback behavior.


### 2026-09-26T11:16:08Z - Issue

Raised: Artifact-store review change set failed CloudFormation property validation

Resolution: No resource was created. Verified the AWS CloudFormation S3 lifecycle-rule schema, replaced unsupported Filter syntax with direct Prefix syntax, and passed local plus AWS template validation.


### 2026-09-26T11:16:08Z - Context hygiene

Summary: The retry has one narrowly scoped source correction and preserves the two-resource review boundary.

Durable evidence: The corrected artifact-store template, its static verifier, ADR 0034, and the current session log.


### 2026-09-26T11:16:50Z - Commit recorded

Commit: `bef454ce`

Message: fix(deploy): correct artifact-store lifecycle schema

Summary: Corrected the S3 lifecycle-rule property shape after a review-only CloudFormation validation failure; no resources were created before the fix.

ADR impact: No new ADR; implements the target-owned artifact-store decision in ADR 0034.


### 2026-09-26T11:25:30Z - Issue

Raised: Foundation change-set shorthand input could not preserve the comma-separated subnet value

Resolution: No change set was created by the rejected local request. Used an uncommitted JSON deployment-parameter file so CloudFormation received one exact PrivateSubnetIds value.


### 2026-09-26T11:25:30Z - Context hygiene

Summary: Stage 4 now has source checks, a deployed hardened artifact store, and an available but unexecuted relational Foundation change set.

Durable evidence: Target profile, readiness record, PostgreSQL deployment plan, product plan, static verifiers, and this session log; no secret, endpoint, record, message, or provider payload was recorded.


### 2026-09-26T11:26:20Z - Commit recorded

Commit: `1c47ce5109997139064d7a1efb623f3e932e2794`

Message: docs(persistence): record relational change-set review

Summary: Recorded the passed Stage 4 artifact-store bootstrap and the available but unexecuted relational Foundation change set with its strictly bounded scope.

ADR impact: No new ADR; evidence completes the Stage 4 review gate under the existing relational-reference and artifact-store decisions.


### 2026-09-26T11:52:12Z - Decision

Decision: Require fail-closed staging deployment reconciliation before infrastructure mutation

Rationale: A dedicated source policy, static verifier, local/live reconciliation command, and read-only GitHub OIDC workflow now guard source/live agreement; any mismatch blocks the change set.


### 2026-09-26T11:52:13Z - Context hygiene

Summary: The live budget uses the canonical name kanbien-staging-platform-shell-monthly; the prior source-only suffix was stale and would have caused a deployment mismatch.

Durable evidence: Target profile, reconciliation command and policy checker, ADR 0035, PostgreSQL plan, staging deployment plan, and readiness record.


### 2026-09-26T11:52:22Z - ADR disposition

ADR needed: yes

ADR path: docs/04.deploy/adrs/0035-require-fail-closed-staging-deployment-reconciliation.md

Reason: A pre-mutation and recurring live reconciliation boundary is a durable deployment architecture decision.


### 2026-09-26T12:03:47Z - Commit recorded

Commit: `0b6576e2b72fa9fc93ab6f099a75eb25d3b6eb77`

Message: feat(deploy): require staging reconciliation gate

Summary: Added a fail-closed source/live AWS reconciliation control, canonicalized the staging budget declaration, and proved both continuous and exact pre-change-set checks without provisioning resources.

ADR impact: ADR 0035 records the durable pre-mutation and recurring reconciliation boundary.


### 2026-09-26T12:08:43Z - Issue

Raised: GitHub reconciliation proof showed CloudFormation drift-status lookup cannot be constrained to the reviewed stack ARN

Resolution: Did not broaden IAM. Replaced that lookup with a fresh LastCheckTimestamp plus IN_SYNC stack-status check using only the existing scoped DescribeStacks permission.


### 2026-09-26T12:08:43Z - Decision

Decision: Preserve scoped CloudFormation reconciliation without wildcard drift-status permission

Rationale: Fresh stack drift timestamps provide the required fail-closed evidence while keeping the GitHub role restricted to the two declared stack ARNs.


### 2026-09-26T12:08:43Z - Context hygiene

Summary: The first GitHub reconciliation run failed safely because DescribeStackDriftDetectionStatus was not authorisable against a stack ARN. The corrected design uses only scoped DescribeStacks plus DetectStackDrift and has passed locally against staging.

Durable evidence: Reconciliation command, IAM source, static verifier, target profile/readiness, ADR 0035, and the GitHub workflow run evidence.


### 2026-09-26T12:24:12Z - Commit recorded

Commit: `1f090d6f`

Message: fix(deploy): retain scoped reconciliation drift checks

Summary: Replaced a drift-status lookup that would require wildcard IAM with a fresh stack drift timestamp check through existing stack-scoped read permission.

ADR impact: ADR 0035 remains the reconciliation decision; this correction preserves its least-privilege intent.


### 2026-09-26T12:32:31Z - Issue

Raised: The first GitHub reconciliation proof returned only aws-verification-unavailable after its dedicated role successfully assumed and issued declared read requests; the failure could not identify the owning safe control.

Resolution: Reconciliation now attributes an unavailable provider call to its owning safe check while preserving the no-response-output policy. Focused source, static policy, infrastructure, and live administrator reconciliation checks passed.


### 2026-09-26T12:59:05Z - Commit recorded

Commit: `d7fb1da3`

Message: fix(deploy): identify failed reconciliation control

Summary: When a bounded AWS verification call is unavailable, emit the owning safe reconciliation control instead of a generic provider-unavailable result.

ADR impact: No ADR change; ADR 0035 still governs least-privilege deployment reconciliation.


### 2026-09-26T13:04:17Z - Decision

Decision: Run staging reconciliation AWS calls serially, with three bounded retries, instead of launching CloudFormation, S3, and Budgets checks concurrently.

Rationale: The GitHub role can perform each exact read in IAM simulation and administrator reconciliation succeeds. Serial bounded calls remove avoidable provider burst and timing instability while retaining fail-closed output and no added permissions.


### 2026-09-26T13:11:03Z - Commit recorded

Commit: `02437631`

Message: fix(deploy): serialize reconciliation verification

Summary: Serialize bounded staging verification calls and retry each transient AWS verification failure up to three times; retain safe owning-control error identifiers.

ADR impact: ADR 0035 remains the governing reconciliation decision; no privilege or mutation scope changes.


### 2026-09-26T13:13:40Z - Issue

Raised: The hardened GitHub reconciliation run still blocks at artifact-stack drift despite exact-resource IAM simulation and successful administrator reconciliation.

Resolution: Drift verification now reports whether the bounded failure occurs when starting detection or reading the fresh stack summary, without exposing AWS provider payloads or widening IAM.


### 2026-09-26T13:20:48Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): identify drift verification phase

Summary: Separate safe drift-detection-start and fresh-summary-unavailable results so the live reconciliation proof identifies the exact CloudFormation boundary without emitting provider errors.

ADR impact: ADR 0035 remains unchanged; no IAM or mutation scope change.


### 2026-09-26T13:21:07Z - Commit recorded

Commit: `939d0f69`

Message: fix(deploy): identify drift verification phase

Summary: Separate safe drift-detection-start and fresh-summary-unavailable results so the live reconciliation proof identifies the exact CloudFormation boundary without emitting provider errors.

ADR impact: ADR 0035 remains unchanged; no IAM or mutation scope change.

### 2026-09-26T15:28:47Z - Drift-detection reliability checkpoint

- Recorded the runtime dependency finding: GitHub's narrow role cannot safely be treated as an active CloudFormation detector.
- Added source-only guardrails, a target resource-read inventory, and a safe administrator-only source/live role-policy alignment check.
- Read the live policy action names only; it differs from desired source by the one redundant `cloudformation:DetectStackDrift` permission.
- No AWS resource, detector, secret, endpoint, or persistent-data change was made at this checkpoint.


### 2026-09-26T15:30:55Z - Commit recorded

Commit: `52ba62859ba071c4a833875b1f5b0db829e02122`

Message: feat(deploy): harden staging reconciliation boundary

Summary: Separated active drift detection from the GitHub reconciler, added a complete resource-type dependency inventory and fast policy gates, and required a safe source/live role-policy alignment check before Foundation mutation.

ADR impact: ADR 0036 records the new detector boundary; ADR 0035 is amended for passive reconciliation.

### 2026-09-26T15:36:20Z - Live reconciliation boundary proof

- Confirmed the GitHub OIDC role could assume its identity and complete the source-policy, account, stack-status, and passive drift-evidence checks.
- Confirmed the source/live inline-policy alignment after removing only the redundant active-drift action.
- The workflow failed closed at the grouped artifact-bucket verification boundary. No role broadening, detector invocation, resource mutation, or sensitive provider output occurred.

### 2026-09-26T15:40:00Z - Operation-level diagnostic correction

- Split each declared artifact-bucket read into an independently attributable safe control and updated the reliability programme.
- Local reconciliation, policy, infrastructure, and whitespace checks passed.
- Next step: promote this diagnostic-only correction, run one read-only GitHub reconciliation proof, and resolve only the exact reported control if it remains blocked.


### 2026-09-26T15:41:48Z - Commit recorded

Commit: `2ab8dacddeeb25b910e65c65a0fb9c764baf6740`

Message: fix(deploy): isolate reconciliation control probes

Summary: Split the artifact-store reconciliation reads into independent fail-closed safe controls after the live GitHub proof blocked at the former group boundary; no AWS permission was added.

ADR impact: No new ADR; implements the AWS change reliability programme's operation-level diagnostic rule.

## Sub-Agent Activity

- None recorded yet.

## Commits



- Commit: `9d78962d`
  Time UTC: 2026-09-26T10:06:31Z
  Message: feat(persistence): define PostgreSQL staging target
  Summary: Defined and statically verified the private encrypted PostgreSQL relational-reference target; AWS change-set review remains pending an SSO refresh.
  ADR impact: No new ADR; implements the approved relational-reference programme.


- Commit: `faedcb71`
  Time UTC: 2026-09-26T11:08:54Z
  Message: feat(deploy): add private template artifact store
  Summary: Added a separately reviewed private encrypted CloudFormation template store to bridge AWS's inline-template limit without reusing unrelated storage.
  ADR impact: ADR 0034 records the target-owned template-transport boundary.


- Commit: `568c6551`
  Time UTC: 2026-09-26T11:11:16Z
  Message: fix(deploy): clean up failed artifact store bootstrap
  Summary: Use RetainExceptOnCreate so a failed first artifact-store deployment leaves no retained bucket while successful evidence remains protected.
  ADR impact: No new ADR; strengthens the ADR 0034 rollback behavior.


- Commit: `bef454ce`
  Time UTC: 2026-09-26T11:16:50Z
  Message: fix(deploy): correct artifact-store lifecycle schema
  Summary: Corrected the S3 lifecycle-rule property shape after a review-only CloudFormation validation failure; no resources were created before the fix.
  ADR impact: No new ADR; implements the target-owned artifact-store decision in ADR 0034.


- Commit: `1c47ce5109997139064d7a1efb623f3e932e2794`
  Time UTC: 2026-09-26T11:26:20Z
  Message: docs(persistence): record relational change-set review
  Summary: Recorded the passed Stage 4 artifact-store bootstrap and the available but unexecuted relational Foundation change set with its strictly bounded scope.
  ADR impact: No new ADR; evidence completes the Stage 4 review gate under the existing relational-reference and artifact-store decisions.


- Commit: `0b6576e2b72fa9fc93ab6f099a75eb25d3b6eb77`
  Time UTC: 2026-09-26T12:03:47Z
  Message: feat(deploy): require staging reconciliation gate
  Summary: Added a fail-closed source/live AWS reconciliation control, canonicalized the staging budget declaration, and proved both continuous and exact pre-change-set checks without provisioning resources.
  ADR impact: ADR 0035 records the durable pre-mutation and recurring reconciliation boundary.


- Commit: `1f090d6f`
  Time UTC: 2026-09-26T12:24:12Z
  Message: fix(deploy): retain scoped reconciliation drift checks
  Summary: Replaced a drift-status lookup that would require wildcard IAM with a fresh stack drift timestamp check through existing stack-scoped read permission.
  ADR impact: ADR 0035 remains the reconciliation decision; this correction preserves its least-privilege intent.


- Commit: `d7fb1da3`
  Time UTC: 2026-09-26T12:59:05Z
  Message: fix(deploy): identify failed reconciliation control
  Summary: When a bounded AWS verification call is unavailable, emit the owning safe reconciliation control instead of a generic provider-unavailable result.
  ADR impact: No ADR change; ADR 0035 still governs least-privilege deployment reconciliation.


- Commit: `02437631`
  Time UTC: 2026-09-26T13:11:03Z
  Message: fix(deploy): serialize reconciliation verification
  Summary: Serialize bounded staging verification calls and retry each transient AWS verification failure up to three times; retain safe owning-control error identifiers.
  ADR impact: ADR 0035 remains the governing reconciliation decision; no privilege or mutation scope changes.


- Commit: `HEAD`
  Time UTC: 2026-09-26T13:20:48Z
  Message: fix(deploy): identify drift verification phase
  Summary: Separate safe drift-detection-start and fresh-summary-unavailable results so the live reconciliation proof identifies the exact CloudFormation boundary without emitting provider errors.
  ADR impact: ADR 0035 remains unchanged; no IAM or mutation scope change.


- Commit: `939d0f69`
  Time UTC: 2026-09-26T13:21:07Z
  Message: fix(deploy): identify drift verification phase
  Summary: Separate safe drift-detection-start and fresh-summary-unavailable results so the live reconciliation proof identifies the exact CloudFormation boundary without emitting provider errors.
  ADR impact: ADR 0035 remains unchanged; no IAM or mutation scope change.


- Commit: `52ba62859ba071c4a833875b1f5b0db829e02122`
  Time UTC: 2026-09-26T15:30:55Z
  Message: feat(deploy): harden staging reconciliation boundary
  Summary: Separated active drift detection from the GitHub reconciler, added a complete resource-type dependency inventory and fast policy gates, and required a safe source/live role-policy alignment check before Foundation mutation.
  ADR impact: ADR 0036 records the new detector boundary; ADR 0035 is amended for passive reconciliation.


- Commit: `2ab8dacddeeb25b910e65c65a0fb9c764baf6740`
  Time UTC: 2026-09-26T15:41:48Z
  Message: fix(deploy): isolate reconciliation control probes
  Summary: Split the artifact-store reconciliation reads into independent fail-closed safe controls after the live GitHub proof blocked at the former group boundary; no AWS permission was added.
  ADR impact: No new ADR; implements the AWS change reliability programme's operation-level diagnostic rule.

## Main Refresh Conflicts

- 2026-09-26: refresh readiness was `clean`; the chat branch had two task and
  checkpoint commits while fetched `origin/main` had advanced by five commits.
  Changed-path overlap was empty. A no-stash, no-rewrite rehearsal merged
  `main` cleanly in
  `agentic/preflight/chat-2026-09-26-10-30-go-694f38599269/20260926153307`
  at `/tmp/agentic-main-refresh-preflight/chat-2026-09-26-10-30-go-694f38599269-20260926153307`.
  The deployment boundary, reconciliation, policy, infrastructure, and
  whitespace checks passed on preflight commit `574e7a27be58934b9bee6fb85f024a5c4903d0c4`.
  The tested result was fast-forwarded to the chat branch and the clean
  preflight worktree and branch were removed. No conflict classification was
  needed.

## ADR Disposition

ADR needed: yes
ADR paths:
- docs/04.deploy/adrs/0035-require-fail-closed-staging-deployment-reconciliation.md
- docs/04.deploy/adrs/0036-separate-active-drift-detection-from-github-reconciliation.md
Reason: The existing reconciliation boundary is amended so active provider-dependent drift detection has a separate target identity and an explicit permission-analysis gate.

## Session Metrics

Raised at UTC: 2026-09-26T09:30:58Z
Latest commit at UTC: 2026-09-26T15:41:48Z
Latest commit SHA: 2ab8dacddeeb25b910e65c65a0fb9c764baf6740
Chat duration: 22250s (00:06:10:50)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- Next operational step: review and apply the small artifact-store change set;
  then create and inspect the larger relational Foundation change set.

## RAG Knowledge Disposition

Status: covered
Reason: The Stage 4 PostgreSQL reference and its separate template-transport
store apply the established deployment boundaries for provider-specific
infrastructure: private encrypted data services, least-privilege access,
explicit configuration/secrets separation, target-owned operations, and
evidence-first deployment.
Evidence:
- docs/04.deploy/adrs/0029-use-task-local-otel-collector-for-cloudwatch-metrics.md
- docs/04.deploy/adrs/0034-use-private-target-owned-cloudformation-artifact-stores.md
- docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md
- .agentic/03.product/plans/implementation/platform-runtime-implementation.md
Corpus gaps:
- None.
