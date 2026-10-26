# Chat Session: 2026-10-05-09-59 target-alignment-preflight-folders

<!-- agentic-session
id: 2026-10-05-09-59-can-you-walk-me-through-which-part-of-my-repo-work-on-the-fo
task: can you walk me through which part of my repo work on the following stages
branch: chat/2026-10-05-09-59-can-you-walk-me-through-which-part-of-my-repo-work-on-the-fo
worktree: /home/owner/projects/.chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-10-05-09-59-can-you-walk-me-through-which-part-of-my-repo-work-on-the-fo-2898599584
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-10-05T08:59:29Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-10-26T13:28:56Z
latest_commit_sha: 8bc53dd8
chat_duration: 1830567s (21:04:29:27)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

can you walk me through which part of my repo work on the following stages

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Current Execution Authority

- 2026-10-23: The user granted standing authority for the bounded
  `kanbien-core-platform/core-server-persistence` slice: local implementation,
  target-scoped AWS PostgreSQL/secrets/IAM/network/logging/native-backup
  configuration, image publication, governed deployment and recovery
  rehearsals, cleanup of synthetic exercise data/resources, and normal
  commit/integration/push. The ceiling remains the existing USD 100 monthly
  target budget; do not touch staging, add a waiver, or use unrelated
  resources. Technical gates and protected GitHub Environment approval remain
  mandatory.

## Issues Raised



- Raised: Docker daemon unavailable for local core image smoke
  Resolution: Static payload and negative-fixture proof pass. The build and smoke scripts fail closed by default and only report an explicit skip with --allow-skip-without-engine; Docker runtime proof remains required before release qualification.


- Raised: Core-server image command wrapper exited cleanly without starting the server
  Resolution: The real Docker smoke exposed that the generated wrapper only required the compiled entrypoint. It now invokes runKanbienCoreServerMain; a new pre-Docker runtime command proof and real container smoke verify liveness, readiness, and safe release identity.


- Raised: E0 candidate network is not yet viable for an isolated private container workload
  Resolution: Read-only candidate inspection found no core-target naming conflict in account 337159794548/eu-west-1 and found a project VPC with two private subnets, but they have only an S3 gateway endpoint and no NAT/ECR/CloudWatch route. Runtime, registry, verifier placement, cost guard, roles, and rollback custody remain unresolved. No AWS state changed.


- Raised: E1 cannot yet become executable
  Resolution: Read-only cost evidence shows only USD 25 monthly staging budgets. The selected two-AZ interface-endpoint topology has recurring cost, so a target-specific monthly ceiling, alert destination, and GitHub Environment protection owner remain required before an exact CloudFormation change set can be approved.


- Raised: Target-scoped cost guard is not yet feasible
  Resolution: Read-only Cost Explorer inspection returned no active Target cost-allocation tag. The proposed USD 100 budget would not reliably isolate kanbien-core-platform cost until account-level tag activation is approved and completed. No AWS billing setting or resource was changed.


- Raised: AWS rejected cost-allocation tag activation without mutation
  Resolution: The approved Cost Explorer activation command failed with Tag keys not found: Target. AWS requires the user-defined tag to exist on a resource before it can be activated. No account setting or target resource changed; the foundation sequence must introduce a target-tagged low-risk resource, then activate and wait for propagation before relying on the USD 100 target budget.


- Raised: E2b account tag discovery is still propagating
  Resolution: E2a created only the empty immutable Target-tagged core image repository. AWS Cost Explorer still returns Tag keys not found for Target, so no guarded foundation has been created.


- Raised: The live alignment gate rejected a healthy foundation after an output-only stack update.
  Resolution: The AWS adapter recognised CREATE_COMPLETE but not UPDATE_COMPLETE, despite both being stable CloudFormation success states.


- Raised: Runtime change-set creation failed before creating the stack because the template rejected the qualified ECR repository URI.
  Resolution: The ImageRepositoryUri AllowedPattern used double escaping in YAML single quotes, which made the regex require literal backslashes.


- Raised: The deploy control rejected a reviewed initial change set because CloudFormation omitted ChangeSetType from its describe response.
  Resolution: The stack was absent and the change set was CREATE_COMPLETE and AVAILABLE, but the control incorrectly required a field AWS did not return.


- Raised: The deploy control still rejected the initial change set because CloudFormation creates an empty REVIEW_IN_PROGRESS stack while the change set awaits execution.
  Resolution: No runtime resources existed; the review stack is CloudFormation’s normal create-change-set lifecycle state.


- Raised: CloudFormation rejected the ECS service registry binding because the target service-discovery resource uses A records.
  Resolution: The runtime template incorrectly supplied container-name and container-port fields that apply to SRV-style registration, and the deploy wrapper then misreported the successful execute response because it was empty.


- Raised: The corrected service failed to launch because the private CloudWatch Logs endpoint policy denied CreateLogStream.
  Resolution: The endpoint policy appended log-stream syntax to LogGroup.Arn, producing an ARN shape that did not match the actual log stream resource.


- Raised: After correcting the Logs endpoint policy, task startup still failed because the task execution role had its own malformed log-stream ARN.
  Resolution: The endpoint and identity policies are evaluated independently; both must match the exact log-stream resource.


- Raised: AWS omitted ChangeSetType from a reviewed existing-stack UPDATE change set.
  Resolution: The deployment control now accepts that documented omission only with independent healthy-stack proof; smoke tests reject CREATE and non-stable lifecycle states.


- Raised: A terminally interrupted restoration command could cause an agent to launch a second private verifier task despite the first verifier having already accepted.
  Resolution: The verifier now reuses only current-deployment completed evidence with a successful exit and safe acceptance log; otherwise it blocks. The rehearsal evidence records the incident and remediation.


- Raised: Generic harness migration ADR was missing before the first active generic move
  Resolution: Resolution: added ADR 0037 to make the lifecycle-first placement decision explicit, record the prior target-alignment move as a no-cloud, no-public-compatibility corrective case, and govern all remaining generic-harness moves. Runnable-program migration remains paused until this ADR is committed.


- Raised: Controlled replacement command returned no terminal report despite completing AWS actions
  Resolution: Safe AWS inspection proved the original accepted task stopped at 15:55:42Z, ECS started and stabilised a healthy replacement at 15:55:55Z, and a fresh verifier completed successfully at 15:56:42Z. The outcome is recorded from provider facts; do not repeat the stop action.


- Raised: Budget provisioning change-set initially rolled back
  Resolution: The Foundation CostAlertEmail parameter was blank; the new bounded provisioning route now requires an operation-only alert address, recognises stable rollback completion, and verifies AWS monetary values numerically.


- Raised: Closed the secret-declaration review findings.
  Resolution: Workload-aware failures and startup-only rotation are enforced; unsafe values beneath non-string keys are scanned; malformed access classes return structured results; shared runtime server/worker credentials pass without permitting migration/admin access or mixed failure families.


- Raised: Malformed migration credential cross-check could raise TypeError
  Resolution: Validator now cross-checks only structurally valid credential entries; null, boolean, and numeric authorised_workloads fixtures produce structured failures.


- Raised: Persistence failures had generic diagnostic primitives but no scope-level, workload-aware declaration or automatic inventory enforcement.
  Resolution: Added a provider-neutral controlled diagnostic taxonomy, safe-record standard, declaration workflow, validator, regression fixtures, and active-scope inventory routing. The dependency-free bootstrap scope truthfully records persistence diagnostics as not applicable. No PostgreSQL provider operation, runtime adapter mapping, or live diagnostic observation was asserted.


- Raised: The initial persistence diagnostic validator accepted false non-applicability, unsafe free-form record fields, incorrect migration timeout handling, and malformed enum values.
  Resolution: The corrective pass adds explicit `dependencies.persistence` classification tied to migration/server-mediated use, closed diagnostic records with controlled summaries and next checks, write-aware server uncertainty, separate transport/trust treatment, migration timeout release blocking, and structured malformed-input findings. Regression fixtures reproduce every finding; provider translation and live proof remain deferred.


- Raised: A scope could still declare `persistence_writes: true` while claiming persistence diagnostics were not applicable.
  Resolution: A declared persistence write is now authoritative workload usage for the not-applicable cross-check. It blocks that verdict without being mistaken for a dependency identifier in an otherwise valid declared scope; a focused regression fixture proves the rule.


- Raised: Corrected isolated restore verifier reconciliation
  Resolution: Live restore check exposed two controller defects before acceptance: ECS task-definition fields are lower-case and list-tasks defaults to running tasks. The controller now parses the actual AWS response and searches running plus stopped tasks before submitting any verifier. Two read-only verifier attempts already exist for the current restored copy, so it will be cleaned up and repeated from the immutable snapshot after this correction is recorded.


- Raised: Bound restore verifier identity to database incarnation
  Resolution: A fresh restore from the same snapshot correctly exposed that a snapshot-date-only ECS started-by value collides with historical tasks. The restore controller now derives a bounded identity from the restored RDS DbiResourceId, so only tasks for the current isolated database incarnation are reconciled.


- Raised: Credential revocation terminated an idle PostgreSQL pool client and crashed the local server instead of leaving it live but not ready.
  Resolution: The reusable PostgreSQL pool adapter now consumes idle-client provider errors without logging raw provider detail; the next readiness probe reports the governed state. Adapter, composition, TLS package, harness, target, and release gates passed.


- Raised: The persistence release transition omitted the required RestoreVerifierImageDigest CloudFormation parameter, so AWS rejected change-set creation before any update.
  Resolution: Both clean-create and update controllers now bind the restoration verifier to the same qualified immutable persistence image digest as the server.


- Raised: Acceptance required every historical ECS stopped-task record to remain queryable at the end of a multi-step rehearsal. ECS retention then aged out an already-proved replacement task and would have forced unrelated rehearsals.
  Resolution: Each completed persistence proof now writes an allowlisted, integrity-checked durable receipt before reporting success. Acceptance consumes those retained receipts for historical proof while independently observing current service, database, recovery-point, cleanup, and budget state. One narrowly necessary replacement was repeated only after the old provider record had already expired; no migration, credential lifecycle, image update, or restore was repeated.


- Raised: The isolated restore verifier reached the post-TLS database handshake boundary but returned no allowlisted PostgreSQL machine code.
  Resolution: Preserved the closed rejected result as a governed operation diagnostic, cleaned up the isolated restore and its temporary instance-specific IAM policy, and added bounded causal/aggregate machine-code classification plus automatic safe rejection-record retention. The source database and revision-32 service remain healthy; no recovery proof was accepted or replayed.


- Raised: The upgraded restore verifier again reached a post-TLS database handshake failure without an allowlisted PostgreSQL machine code.
  Resolution: Qualified and deployed the closed-classification image, retained its rejected verifier operation diagnostic, and removed the isolated copy and temporary IAM policy. The result confirms that a target-governed, safe server-side diagnostic route is required before another recovery rehearsal; raw RDS log download is not an authorised or safe substitute.


- Raised: Corrected current release-reference hash mismatch before package qualification
  Resolution: The immutable historical record had two trailing newlines while current-accepted-release.yml named the canonical one-newline rendering. The release-succession gate blocked safely before AWS/ECR actions. Preserved the history; updated only the current pointer to its actual retained SHA-256; validate-current and target smoke pass.


- Raised: Fixed package source-closure copy of a nonexistent protobuf scope
  Resolution: CI package build reached Docker assembly after every declaration/target/receipt gate passed, then failed before AWS mutation because Dockerfile copied node_modules/@protobufjs even though the lockfile provides unscoped protobufjs. Removed only that nonexistent copy. Local governed build reached the known Docker Desktop/WSL credential-helper failure before Docker could build; CI remains the package authority.


- Raised: Removed unnecessary unscoped OpenTelemetry closure copies
  Resolution: The second hosted build reached the Docker payload closure and established that protobufjs, long and related packages are not installed for the selected OpenTelemetry exporter. The supported runtime closure is pg plus the @opentelemetry tree. A clean temporary copied closure loads pg, sdk-metrics and exporter-metrics-otlp-proto.


- Raised: Corrected observability collector delivery path
  Resolution: The target template treated an OTLP HTTP URL as a CloudWatch exporter. AWS ADOT's supported application-metric route is OTLP to a task-local collector, then the awsemf exporter through the existing private Logs endpoint. Removed the unused monitoring endpoint design, narrowed collector task-role permissions to one EMF log stream, and require a target-owned SNS topic plus external confirmation before live acceptance.


- Raised: Classified absent named change sets as a reconciled lifecycle state
  Resolution: CloudFormation can report ChangeSetNotFoundException without the generic phrases recognized by the provider adapter. The preparation adapter now maps only that explicit condition to aws-resource-missing; target-control regression proves it. A change-set must still be reviewed before creation or execution.


- Raised: Target-private collector custody was not yet an executable package route.
  Resolution: Added a contract-pinned ADOT collector package workflow; it mirrors only the immutable public source into the existing target-private ECR repository, validates non-secret startup configuration, scan/SBOM/provenance, and emits a custody receipt before it can be selected by a deployment.


- Raised: The collector route was developed on a chat branch that diverged from newer accepted persistence work on local main.
  Resolution: Resolved the integration by retaining main's newer accepted implementation for overlapping persistence controllers and entrypoints, preserving nonconflicting observability/collector custody artifacts, then rerunning collector, target, and deployment-control gates.


- Raised: Collector package workflow mirrored the qualified image but its scan selector assumed an OCI index.
  Resolution: ECR returned a valid single OCI manifest. Added a deterministic resolver that accepts either the published runnable manifest or exactly one amd64 child of an OCI index; it rejects ambiguous or malformed responses. The existing mirrored digest was read-only verified; no deployment occurred.


- Raised: ECR Basic scanning cannot inspect the mirrored ADOT collector image.
  Resolution: AWS reported UnsupportedImageError for the image's OS/package-manager. The custody requirement remains mandatory: a dedicated unprivileged job now runs a pinned portable scanner against the same pinned public source before the protected AWS publication job can run.


- Raised: The unprivileged portable scanner was rate-limited by Public ECR before it could inspect the pinned image.
  Resolution: Changed the route so the protected mirror job exports the exact target-private digest as a short-retention scan-input artifact; a separate unprivileged job scans that local artifact, and final custody/attestation waits for the scan. No failed run produced an accepted receipt or deployment.


- Raised: Corrected collector qualification after public layer throttling
  Resolution: The protected collector custody job authenticated to AWS but its anonymous public registry layer pull returned Data limit exceeded before any mirror, scan, receipt, or workload action. Read-only OCI metadata established that public index sha256:7968... selects Linux/AMD64 manifest sha256:d0a..., which already exists identically in target-private ECR from the earlier protected mirror. The custody route now verifies the public index bytes, requires that identical private digest, qualifies and scans that payload, then issues custody only after the unprivileged scan.


- Raised: Corrected IAM lifecycle semantics and package recovery boundary
  Resolution: Runtime access now uses task-role renewal plus per-connection RDS IAM tokens; normal token expiry does not replace a healthy server. Recovery restores only bounded IAM login/membership after termination proof; local tests use disposable constrained PostgreSQL and do not claim RDS IAM proof.


- Raised: Corrected permission-surface change-set allowlist against the active stack baseline
  Resolution: CloudFormation correctly exposed an existing-stack UPDATE delta that differed from the controller's stale CREATE-era allowlist. The controller now admits only the reviewed four task-role additions and exact IAM/RDS/secret/task/service modifications; it continues to reject network expansion and unrelated resources. No change set was executed while the guard was invalid.


- Raised: IAM bootstrap rejected legacy non-elevated role
  Resolution: The first governed bootstrap task stopped with the safe PERSISTENCE_ADMINISTRATION_BOOTSTRAP_IDENTITY_BOUNDARY_NOT_CONFIRMED result because the pre-existing runtime role retained PostgreSQL INHERIT. Corrected the role helper to reject elevated legacy roles but safely converge a non-elevated legacy identity to NOINHERIT without any credential SQL; local composition and target declaration checks pass.


- Raised: Package qualification exposed over-broad role convergence
  Resolution: Hosted package run 40225491937 failed before AWS credentials, ECR, scan, or publication because the first convergence implementation rewrote already-bounded fixture roles under a constrained administrator. Narrowed convergence to only the legacy INHERIT attribute; bootstrap now refuses to reactivate NOLOGIN, reserving activation for explicit restore-runtime. Local Docker remains unavailable due host credential-helper failure; hosted package qualification remains authoritative.


- Raised: Prevented historical ECS task expiry from forcing unrelated rehearsals.
  Resolution: Acceptance now uses integrity-checked, durable controller receipts and a closed restore-verifier-only applicability record; the collector still independently observes current service, database, cleanup, and budget state.


- Raised: Restore verifier could not reach the isolated restored database.
  Resolution: Read-only provider facts showed the deployed stack lacks the declared RestorationVerifierRestoredDatabaseEgress resource. Added a governed egress-only correction mode that accepts exactly that one CloudFormation addition and no broader surface change.


- Raised: Restore verifier connection result was too coarse
  Resolution: A rejected isolated-restore verifier emitted only CONNECTION_UNAVAILABLE even after provider facts disproved the suspected missing egress rule. Added a bounded TCP preflight before PostgreSQL credential use so the next governed proof distinguishes a closed transport path from a post-transport database handshake failure without exposing provider text, endpoints, SQL, or credentials.


- Raised: Restore verifier reached TCP but not a classified PostgreSQL handshake
  Resolution: Live recovery proof established the private TCP route works, then returned the closed DATABASE_HANDSHAKE_UNAVAILABLE result. The failed isolated copy is governed for cleanup. Added a credential-free PostgreSQL SSLRequest/TLS certificate preflight so the next image can distinguish TLS negotiation/trust from post-TLS authentication/protocol failure without exposing raw provider text.


- Raised: Promoted isolated restore controller hardening
  Resolution: Verified normal fast-forward promotion of 820185f1e5dd207e38fe8b392bf11c6c53bdfe96 to origin/main after clean-worktree restore, composition, and deployment-diagnostic regressions; source and target state were rechecked.

## Decisions Made

- Established `.agentic/04.deploy/` as the provider-neutral deployment
  governance layer without moving `.agentic/aws/`.
- Kept `.agentic/aws/` authoritative for AWS operations and PostgreSQL Stage 6
  during the planned transition.
- Defined Target Alignment Preflight as a draft provider-neutral workflow and
  standard. It has no executable provider adapter or AWS operation yet.
- Adopted a numbered deployment lifecycle map: Target Alignment, development,
  build, test, package, deploy, and run. Existing capabilities retain their
  current paths until individually migrated.
- Placed Declaration Coverage before Target Alignment: it accounts for each
  declared requirement and proof path before any provider inspection begins.


- Decision: Adopt the kanbien-core-platform bootstrap lifecycle proof
  Rationale: The first controlled slice must establish a private target from an absent baseline as immutable release A, then verify one planned update to release B. A rejected B preserves A and must not trigger automatic redeployment. Existing kanbien/staging remains read-only reference evidence.


- Decision: Adopt a dedicated core-server package boundary
  Rationale: The planned kanbien-core-server.main.ts uses existing platform-server startup and transport, gains generic release-verification and visible configuration contracts, and is packaged in a dedicated core-server image. Generic observability must be separated from its optional persistence bridge. Technical infrastructure permissions are grouped under technical-access; the verifier route remains bootstrap-scope-owned.


- Decision: Adopt lifecycle-owned core release rehearsal layout
  Rationale: The first core-server rehearsal uses numbered build, package, deploy, and run script homes; it keeps generic rules in .agentic, factual selection in platform and infra, and safe run receipts in GitHub Actions without altering staging.


- Decision: Approve the target-scoped script structure for the rehearsal
  Rationale: Build and package scripts remain lifecycle-owned and target-neutral; deploy and run scripts are nested under the exact target and scope so no staging script can be repointed by a free-form flag.


- Decision: Adopt generic runnable-program contract control
  Rationale: R1 supplies provider-neutral runnable-program, image-command, candidate-identity, dependency-boundary, and safe-evidence declaration governance with deterministic report-only failure fixtures before package construction.


- Decision: Adopt persistence-owned observability integration and server configuration boundary
  Rationale: Generic observability now contains only reusable signals; persistence owns the optional bridge. Platform server owns safe runtime configuration resolution and release identity shaping. The change implements the approved core-server boundary without adding a target, image, AWS resource, or deployment.


- Decision: Adopt persistence-owned observability integration and server configuration boundary
  Rationale: Generic observability now contains only reusable signals; persistence owns the optional bridge. Platform server owns safe runtime configuration resolution and release identity shaping. The change implements the approved core-server boundary without adding a target, image, AWS resource, or deployment.


- Decision: Adopt the core-server runnable-program boundary and dependency proof
  Rationale: The bootstrap program reuses platform-server, exposes only a safe release-verification operation, and is rejected if its source or compiled output includes a forbidden dependency. No target, image, provider, or cloud choice is made.


- Decision: Adopt a dedicated local core-server image boundary
  Rationale: The image is built from an explicit minimal source closure, runs as node with one command, and package proof rejects forbidden compiled dependencies before any target or registry operation. A missing Docker daemon records a skip rather than a false image-success claim.


- Decision: Adopt controlled persistence diagnostic mappings for dependency-bearing scopes
  Rationale: A target scope must explicitly exclude persistence or declare a complete safe mapping for every indexed workload. The mapping ties a stable, provider-neutral diagnostic code to applicable lifecycle stage, workload effect, retryability, safe summary, and next check; active scope inventory rejects omission. Provider-specific classification and live proof remain the responsibility of the later selected adapter and target scope.


- Decision: Make persistence diagnostic applicability and record shape explicit
  Rationale: Dependency identifiers are not a safe type system. Scopes classify persistence dependencies directly and the validator cross-checks actual migration/server-mediated usage. Closed record fields and controlled messages prevent repository-level mappings from becoming a carrier for raw provider detail; runtime adapter tests still prove emitted-error containment.


- Decision: Define core-server-persistence as a gated successor, not an in-place bootstrap extension
  Rationale: The accepted dependency-free bootstrap runtime must remain available while a persistence-capable program, declarations, package proof, and release route are built. The future scope will become a candidate only when those prerequisites exist; it then follows the existing lifecycle transition and cannot inherit undeclared dependencies or live authority from bootstrap-runtime.


- Decision: Adopt the planned-not-live-selected kanbien-core-platform target declaration
  Rationale: The repository records the target’s scope, safe configuration shapes, technical-access intent, private verifier requirement, receipt and rollback requirements, and all E0 selection gaps. It blocks target mutation until live facts are inspected and an approved change set exists.


- Decision: Adopt fixed target-bound R6 control surfaces
  Rationale: Prepare, deploy, and verify commands are permanently bound to kanbien-core-platform/bootstrap-runtime, reject free-form target selection, emit safe diagnostics, and cannot contact a provider until E0/E1 facts and approvals exist.


- Decision: Promote the accepted core-server-persistence successor and retain durable proof receipts
  Rationale: The active persistence scope now owns the live server, verifier, migration, and restoration-verifier workloads. Bootstrap remains accepted historical evidence. Scope-local receipts preserve validated terminal proof facts beyond ECS stopped-task retention, while final acceptance continues to require fresh current-state observation.


- Decision: Selected private ECS Fargate candidate design for kanbien-core-platform E1
  Rationale: The candidate uses the existing private VPC/subnets as a limited shared-foundation exception; all workload, IAM, ECR, logging, service-discovery, and verifier resources remain target-owned. No AWS mutation was performed.


- Decision: User approved bounded kanbien-core-platform E1-E7 execution packet
  Rationale: Authority covers reviewed repository changes, commits, main promotion and push; selected kanbien-dev/eu-west-1 target resources; USD 100/month target guard; protected GitHub Environment; one B-to-A rollback; cost-tag propagation wait; and stops only for unexpected security risk, extra cost/resource category, AWS/GitHub denial, or an out-of-bound result. Alert email is execution-only and must not be recorded.


- Decision: Completed E2a tag bootstrap and GitHub Environment guard
  Rationale: The ECR tag-bootstrap stack is CREATE_COMPLETE with no image or workload. GitHub Environment kanbien-core-platform now requires the repository owner and accepts only main deployments. Cost-tag activation remains pending AWS discovery.


- Decision: Implemented E3/E4 repository controls while E2b propagates
  Rationale: Added package custody receipt governance and a protected manual-only target image workflow; added a private immutable-digest runtime and verifier stack; hardened the E2 foundation. No E2c+ AWS resource was created.


- Decision: Accepted temporary waiver of the target-specific budget activation gate
  Rationale: User explicitly accepts only the delay in Target cost-allocation tag discovery. E2c-E7 may proceed with one task, no autoscaling, no NAT, no public ingress, no data services, and no new cost categories. The USD 100 Target-filtered budget must be activated and verified once AWS exposes the tag.


- Decision: Adopt reusable delivery-control layering
  Rationale: Provider-neutral validators now consume contracts and safe normalized evidence; AWS adapters own policy parsing and ECR probes; fixed target wrappers provide Kanbien choices without permitting arbitrary substitution.


- Decision: Promoted the verified deployment-control source to origin/main.
  Rationale: Remote promotion was a normal fast-forward from 1b56931d to 81abadac after the inventory, target-declaration, fixed runtime-control, package-custody, alignment-validation, and whitespace gates passed in the isolated integration worktree.


- Decision: Alignment now recognises the stable successful CloudFormation lifecycle states explicitly.
  Rationale: The adapter accepts only CREATE_COMPLETE and UPDATE_COMPLETE; its new regression test rejects in-progress and rollback states.


- Decision: Runtime template parameter patterns must be tested against a representative valid provider identifier.
  Rationale: The fixed bootstrap-runtime smoke test now validates the exact ECR repository URI shape, and the change-set control maps provider parameter-pattern failures to aws-parameter-invalid without exposing values.


- Decision: Cloud-mutating controls now have a standard metadata effect category.
  Rationale: aws-mutation is added to the central metadata taxonomy, documented standard, and checker fallback; it distinguishes provider state changes from ordinary network reads.


- Decision: Initial create review accepts an omitted ChangeSetType only with independent proof that the runtime stack is absent.
  Rationale: The deploy control accepts CREATE_COMPLETE with type CREATE or omitted only when describe-stacks proves absence; it rejects update types and existing stacks.


- Decision: Initial runtime deployment recognises CloudFormation REVIEW_IN_PROGRESS as an empty review boundary, not a deployed runtime.
  Rationale: The control accepts only absent or REVIEW_IN_PROGRESS stacks with the expected create change set, and continues to reject CREATE_COMPLETE or any update type.


- Decision: The runtime template and deploy control now model the A-record service-discovery contract explicitly.
  Rationale: A-record registry bindings provide only RegistryArn; regression coverage rejects container fields and accepts empty successful mutation responses.


- Decision: CloudWatch Logs endpoint policies must use an explicitly constructed log-stream ARN, tested against the endpoint block.
  Rationale: The shared foundation policy now uses partition, region, account, log-group name, and log-stream wildcard directly; the task role policy remains separate.


- Decision: Both endpoint and task execution-role logging permissions now use the same exact log-stream ARN contract.
  Rationale: The regression requires two exact policy occurrences and rejects the malformed LogGroup.Arn-derived stream expression everywhere in the foundation template.


- Decision: Private immutable image pull also requires object-store layer retrieval, not only registry endpoints.
  Rationale: Declare and enforce TCP/443 egress to the provider-managed object-store prefix list for both workload and verifier security groups; broad internet egress remains prohibited.


- Decision: The ECS task definition overrode the image runtime identity with a nonexistent node account.
  Rationale: Preserve the distroless image-declared nonroot account; regression checks reject all task-definition User overrides for this immutable core image.


- Decision: The running container logged successful server startup, but ECS health checks invoked node through PATH, which distroless does not provide.
  Rationale: Bind the health check to the image-declared /nodejs/bin/node executable and reject PATH-dependent health check commands in target controls.


- Decision: The corrected readiness command still used CMD-SHELL, but the distroless image contains no shell.
  Rationale: Use ECS CMD form with the image-declared Node binary and arguments as separate tokens; static controls reject CMD-SHELL for the core distroless image.


- Decision: The private verifier inherited the distroless image Node entrypoint but duplicated node in its ECS Command, which made Node resolve /app/node as a script.
  Rationale: Verifier commands must pass only Node arguments to the image-declared entrypoint; target controls reject duplicated node command tokens.


- Decision: The kanbien-core-platform bootstrap runtime deployed from the qualified immutable digest and its private verifier accepted the expected release identity.
  Rationale: Live evidence: ECS rollout completed with one healthy task; verifier reported runtime-digest-and-private-verifier-accepted after the verifier-only task-definition update.


- Decision: Promoted governed core-platform release controls to origin/main
  Rationale: The isolated integration worktree at 8ed5c337 passed the release-control and metadata checks; origin/main was verified at that exact commit after a normal fast-forward push. The live B-to-A rehearsal remains blocked only by renewed cost-waiver authority and GitHub Environment approval.


- Decision: Qualified Release B locally
  Rationale: The exact committed B revision ab80e2e1 passed runnable-program, dependency-boundary, release-contract, and real Docker liveness, readiness, and release-identity smoke checks. Publication remains a separate protected workflow and no AWS target mutation has occurred.


- Decision: Reconciled Release B rehearsal evidence with restored accepted Release A.
  Rationale: B remains a verified rehearsal candidate, while the accepted-release record names A's actual restored runtime and verifier task definitions; the static declaration gate checks the link.


- Decision: Adopt placement-before-creation governance
  Rationale: Future deployment artifacts must choose infra, agentic, or scripts ownership; name their lifecycle phase and clear purpose; validate new canonical proposed paths before addition or move. No ADR is needed yet because this sets a governed migration direction without changing the durable active namespace.


- Decision: Adopt ordered deployment placement and naming migration
  Rationale: The approved migration makes target declarations scanable in lifecycle order. Batch 2 moved only active kanbien-core-platform target declarations to 00-target, 10-foundation, 20-scopes, 30-provider-realization/aws, and 40-package-custody; all active consumers, fixtures, GitHub metadata, and generated recognition sources now use the canonical locations. Old paths have no active aliases or consumers.


- Decision: Keep one AWS release workflow while making lifecycle sections explicit
  Rationale: The AWS bootstrap-runtime procedure is one coherent release route, so splitting it would duplicate operational authority. It now lives at the planned target-and-scope deploy path and explicitly separates preconditions, 50-deploy update, 60-run verification, and 60-run restoration.


- Decision: Move reusable target-alignment authority without creating empty schema artifacts
  Rationale: The generic target-alignment workflow and standard now live in 00-target-alignment with names that say what they do. They remain singular reusable authority. The canonical layout's alignment schema is intentionally deferred because no such contract schema currently exists; creating one without a real consumer would create false governance.


- Decision: Adopt lifecycle-first deployment authority paths
  Rationale: ADR 0037 establishes the durable folder and naming rule: folders say when or where, filenames say what, and target/scope says what is affected. Generic authority stays singular; provider workflows and scripts remain lifecycle-first with binding where necessary.


- Decision: Keep runnable-program contract material with the build phase
  Rationale: The runnable workflow, standard, schema, template, and guide are one build capability: they prove a program's dependency boundary and command before package construction. They now live together under 20-build; package publication and deploy controls remain separate.


- Decision: Keep package custody with the package phase
  Rationale: The package workflow, standard, receipt schema, and guide now live under 40-package. They govern immutable package qualification and publication only; target selection, deployment, verification, and restoration remain later target-bound controls.


- Decision: Implemented the reusable health, failure, and recovery declaration capability before persistence. The core bootstrap scope is its first fixture; local/package proof is passed and the unperformed live fault/replacement rehearsal is explicitly deferred with ownership and review boundary.
  Rationale: .agentic/04.deploy/plans/implementation/health-failure-and-recovery-declaration.md and .agentic/04.deploy/60-run/ now govern the reusable requirement; scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/ enforces it; the core target/release checks invoke it.


- Decision: Goal-authorized bounded live health/recovery rehearsal starts by committing the reusable health/failure/recovery declaration capability. The live exercise must prove final accepted immutable release health and private verification, and stops on identity, permission, cost, alignment, uncertainty, or wider-impact risk.
  Rationale: Goal objective in this chat; .agentic/04.deploy/plans/implementation/health-failure-and-recovery-declaration.md; .agentic/04.deploy/60-run/.


- Decision: Adopt controlled accepted-task replacement rehearsal
  Rationale: The fixed 60-run command validates the accepted baseline, target alignment and active cost exception; with --execute it stops only the one accepted task, proves same-definition ECS replacement, and demands post-stop private verification. It does not claim readiness-detector or circuit-breaker proof.


- Decision: Accept live ECS replacement evidence with explicit proof boundary
  Rationale: The bootstrap runtime now has passed live workload-recovery evidence. It proves ECS replacement of a deliberately stopped accepted dependency-free task and fresh private verification; it does not claim application-readiness-failure detection, circuit-breaker rollback, or dependency-bearing recovery.


- Decision: Complete bounded live workload recovery rehearsal
  Rationale: Final audit confirmed account 337159794548, active service desired/running 1, completed rollout on task definition kanbien-core-platform-bootstrap-runtime:10, healthy /readyz-backed container digest sha256:0992b48fdd66bb53c08d621e871b2e8975f40b8e6bbaa62816803f755d55d5d5, and fresh verifier exit 0 with KANBIEN_CORE_RELEASE_VERIFIED. Proof remains bounded: readiness-failure and circuit-breaker rollback were not rehearsed.


- Decision: Select PostgreSQL as the first kanbien-core-platform persistence reference
  Rationale: The existing provider-neutral persistence contracts and AWS PostgreSQL adapter can be composed through a new isolated target scope; legacy staging persistence is not inherited.


- Decision: User authorised commit, merge to main, and remote push of the completed secret-management work.
  Rationale: Preserve the existing recovery commits and current main history through governed non-rewriting refresh; no cloud execution or credential access.


- Decision: Adopt reusable persistence-safety declaration controls
  Rationale: Before defining the PostgreSQL scope, add reusable lifecycle ownership, workload-aware health/recovery, server-mediated verifier, migration, recovery, idempotency/cleanup, and credential lifecycle controls; distinguish local declaration checks from provider and live proof.


- Decision: Authorize end-to-end core-server-persistence execution
  Rationale: The user supplied standing authorization for the bounded kanbien-core-platform persistence slice: repository and target changes, AWS provisioning, publication, deployment, live recovery proofs, commits, integration with main, and push. The work remains limited to this target, the USD 100 monthly ceiling, and existing protected gates.


- Decision: Repair mutable release reference without rewriting accepted history
  Rationale: Current release references must hash the exact immutable bytes they name. A pointer-only correction restores validation while preserving historical acceptance truth.


- Decision: Adopt target-private collector package custody.
  Rationale: The collector remains a sidecar dependency, not a deployment authority: its protected manual GitHub workflow may qualify and publish one pinned digest only. The persistence deploy controller will remain blocked until that receipt and digest are supplied.


- Decision: Integrate collector custody on top of the accepted persistence baseline.
  Rationale: Conflicting controller and runtime files take the newer main implementation; collector custody remains separately package-owned and its target gate verifies that it cannot be silently omitted.


- Decision: Separate third-party vulnerability scanning from cloud credentials.
  Rationale: The scanner job has only contents-read permission and the public immutable source reference. It has no OIDC permission, AWS role, target Environment, or private ECR URI. The protected publication job depends on its successful result. Custody receipts accept exactly one explicit scanner proof: legacy ECR-native or portable vulnerability scan.


- Decision: Scan the exact mirrored collector payload out of band from AWS credentials.
  Rationale: The artifact handoff ties the scanner to the exact digest produced by the protected mirror job while keeping the third-party scanner unprivileged. The final protected job may issue receipt and attestations only after the scan-job dependency passes.


- Decision: Use manifest-identity requalification for the retained collector mirror
  Rationale: No delivery-role permission expansion or public image-layer retry is required. The collector workflow proves the immutable public OCI index and selected platform manifest, requires the same content-addressed digest in private ECR, and qualifies/scans only that private payload. This is a bounded custody correction; no ADR is required because it changes an in-flight target package route rather than the architecture.


- Decision: Closed isolated restore cleanup before correcting failure classification; retained proof is accepted only from a closed, allowlisted result envelope and all synthetic regression diagnostics stay outside durable evidence.
  Rationale: Existing PostgreSQL persistence/recovery design; no new ADR required.


- Decision: Promoted durable evidence controls to remote main.
  Rationale: After focused checks in a clean integration worktree, main advanced fast-forward from c60e55d4 to f0e0d23a; remote main was read back at that exact commit. The remaining live restore proof will use this governed version.


- Decision: Use safe transport preflight before restore verifier authentication
  Rationale: The preflight opens and immediately closes only a TCP socket to the declared private database address. PostgreSQL TLS, IAM authentication, and query proof remain in the existing driver path. Unknown post-preflight driver failures map to a new closed handshake result; raw provider detail remains excluded.


- Decision: Bind proof reuse to the immutable image input closure
  Rationale: The new diagnostic image differs from the previously qualified image only in the restoration verifier among package inputs. Target controllers, durable-evidence artifacts and acceptance checks remain in the full audited source delta but do not change the executable image. The applicability control now rejects every changed package input except that verifier and records the full delta for review.


- Decision: Promoted private observability collector implementation
  Rationale: Remote main fast-forwarded from 92adeab0 to d52e7ffd through the clean governed integration worktree after declaration and controller gates passed; server and collector package qualification is the next boundary.


- Decision: Promoted verified observability evidence controls to origin/main
  Rationale: Fast-forwarded origin/main from 67798a47 to 089f63c9 through isolated integration branch agentic/remote-promotion/chat_2026-10-05-09-59-can-you-walk-me-through-which-part-of-my-repo-work-on-the-fo-20261026T114630Z after receipt, controller, acceptance-route, and target-declaration checks passed. SNS delivery remains PendingConfirmation; no live credential revocation or rehearsal was submitted.

## Context Hygiene



- Summary: Deployment governance baseline ready for checkpoint
  Durable evidence: The active October 5 worktree contains the provider-neutral deployment layer, lifecycle/declaration-preflight foundations, deploy-control inventory, session-continuity safeguard, and the draft platform-to-target chain plan. PostgreSQL and AWS execution controls remain unchanged; the next step is a reviewed Phase 0 evidence map.


- Summary: Scope/pipeline model and drift-evidence gap captured
  Durable evidence: The deployment-chain plan now defines scope records, scope governance, pipeline catalogues, staged full-coverage adoption, and a separate AWS-governed drift-evidence producer before target-alignment automation. GitHub run 37510472773 showed reconciliation authentication/account/artifact-stack status pass but fail-closed stale artifact-stack drift evidence because its planned separate producer is not deployed. Local image smoke, ingress smoke, and controlled smoke are existing proof surfaces; they remain scattered until the first scope links them.


- Summary: Captured the provider-neutral deployment learning and planning decisions: scope versus foundation ownership, configuration-surface visibility, provider selection, workload access, coverage states, and safe future tree migration.
  Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md; teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md.


- Summary: Expanded the draft platform-to-target plan with repo-wide agentic change governance, generic harness portability rules, and product-to-deployment impact routing.
  Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. The plan now defines .agentic as the authority for how agents change the repository, with source/infra as factual implementation and READMEs/docs as linked explanation.


- Summary: Expanded the draft plan and teaching handbook with a concern-control matrix, dependency availability and observation governance, operation-and-promise scope declarations, safe diagnostics, networking, and source-of-truth lessons.
  Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. Teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md.


- Summary: Expanded the deployment-control plan and teaching handbook with dependency lifecycle, network relationship, workload identity/access, credential rotation, and safe failure-handling lessons.
  Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. Teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md.


- Summary: Refreshed the active chat branch from local main through a governed rehearsal after merge verification reported one incoming main commit and two chat-only commits. The rehearsal had no overlapping paths or conflicts; stash was not used.
  Durable evidence: Refresh source head: 18d9bb031b3ec6d709b1d5fd3018233cb1b18830; applied tested merge commit: d479bece947e091737fe27e729a9f12b33eb2b27; preflight branch/worktree were removed by the governed apply script; documentation header validation passed afterward.


- Summary: Refined the deployment learning model: the public server is the bootstrap runtime slice, not the complete platform foundation. The agreed staged foundation order is bootstrap runtime/release evidence, persistence, application security, fuller observability, then product capabilities. Existing platform and core code remains factual source material and will be brought into scope incrementally.
  Durable evidence: Durable evidence: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md and docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md. The next approved activity is a read-only inventory of modules composed by the bootstrap server.


- Summary: Refreshed the active chat branch from local main through a governed rehearsal after local promotion verification reported divergence. The rehearsal had no conflicts; stash was not used.
  Durable evidence: Refresh source head: c4b01422ba10dfabf3111a88c693c186abae0a2e; applied tested merge commit: 02d0e7909b9dff9d492ff38a8a64a2e99208bfc3; temporary preflight branch/worktree were removed by the governed apply script; documentation header validation passed afterward.


- Summary: Recorded the controlled first-target lifecycle, private verifier boundary, configuration/access/network separation, safe verifier diagnostics, and A-to-B recovery evidence. No AWS, target directory, runtime, secret, or PostgreSQL change occurred.
  Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. Teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md. Validation: artifact metadata headers and git diff --check passed.


- Summary: Recorded runnable-program selection, generic release-verification ownership, package versus runtime dependency distinction, optional observability-persistence bridge, technical-access naming, and dedicated core-image boundary. No source implementation, AWS resource, target directory, secret, or PostgreSQL state changed.
  Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. Teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md. Artifact metadata and whitespace checks passed.


- Summary: Core rehearsal blueprint is ready to commit
  Durable evidence: Plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md; teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md. The planned target remains absent; implementation begins with generic rules and report-only local checks, not AWS mutation.


- Summary: Target-specific release rehearsal plan ready
  Durable evidence: Durable review plan: docs/aws/kanbien-core-platform-release-rehearsal-plan.md. It defines R1-R6 repository packages, E0-E7 AWS gates, isolation from staging, and requires exact future approval before any AWS mutation.


- Summary: R1 runnable-program contract control is ready to commit
  Durable evidence: Generic standard/workflow/schema/template/guide are under .agentic/04.deploy; report-only checker and fixtures are at scripts/04.deploy/lifecycle/20-build/runnable-program-contract/. It passed its smoke, metadata, drift, and whitespace checks; no AWS or runtime change occurred.


- Summary: R2 passed the server, persistence, and observability package checks. The persistence observer was moved out of generic observability, and server configuration/release identity are now explicit exported contracts.
  Durable evidence: Durable implementation: platform/observability, platform/persistence/src/observability, and platform/server/src/{configuration,verification}; plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md.


- Summary: R3 proves the core server route and dependency graph locally: release verification responds safely, product routes are absent, and a compiled persistence import fails closed.
  Durable evidence: Durable code: infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts and runnable-program-index.yml; local proof: scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/.


- Summary: R4 adds a minimal core-server Dockerfile, image contract, package payload verifier, and smoke capability. The machine has Docker CLI but no daemon; no image was built or started.
  Durable evidence: Durable artifacts: infra/04.deploy/03.product/image/core-server/ and scripts/04.deploy/lifecycle/40-package/{build-core-server-image,smoke-test-core-server-image}/.


- Summary: Refreshed the active chat branch from local and fetched origin/main through a governed rehearsal. The preflight cleanly merged the single incoming main commit; no conflicts or stash were used. R1-R4 focused checks passed in the preflight, with Docker runtime smoke still an explicit skip because no daemon is available.
  Durable evidence: Refresh source head: e5d13305; applied preflight merge: dedeeef0675f49a655ebbb9773e9f3ed78b83f69; temporary preflight worktree and branch were removed by the governed apply script.


- Summary: Refreshed from the accepted local-main merge through a clean rehearsal, then added R5’s static planned-target declarations. The target checker passes only repository-declaration completeness; live alignment remains not checked and all E0 facts remain unresolved blockers.
  Durable evidence: Durable artifacts: infra/04.deploy/03.product/targets/kanbien-core-platform/ and scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/.


- Summary: R6 adds target-bound prepare/deploy/verify entrypoints with no provider clients or external commands. They pass smoke tests, reject target override, and report unresolved E0 facts plus external_access_attempted false.
  Durable evidence: Durable controls: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/ and scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/.


- Summary: Docker became available during the full proof run. It built the local core image and exposed a start-command defect, which was repaired and confirmed by actual restricted container health/readiness/release-verification smoke.
  Durable evidence: Durable repair: scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs and smoke-test-core-server-image/runtime-command-test.mjs.


- Summary: Completed E0 read-only discovery against available profile kanbien-dev (account 337159794548, eu-west-1). The candidate account has a GitHub Actions OIDC provider and staging-only budgets but no core target resource conflict. Its private network is insufficient for container image pull/logging without an approved network design change.
  Durable evidence: Safe evidence is in this session log; live target declaration remains intentionally unresolved in infra/04.deploy/03.product/targets/kanbien-core-platform/target-profile.yml. No resource, setting, secret, registry, or target was changed.


- Summary: Refreshed the active chat branch cleanly from accepted local main through a rehearsed preflight; recorded E1 candidate topology and budget evidence.
  Durable evidence: Durable design: docs/aws/architecture/adrs/0003-private-ecs-bootstrap-target-for-kanbien-core-platform.md and docs/aws/kanbien-core-platform-e1-foundation-change-set.md. Read-only provider evidence only; no AWS mutation.


- Summary: E2a created one empty immutable ECR repository under the approved target prefix; the account Target allocation tag is not yet discoverable by Cost Explorer. Foundation template was corrected locally to consume this repository rather than recreate it.
  Durable evidence: AWS stack kanbien-core-platform-tag-bootstrap; repo files infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/foundation.yml and docs/aws/kanbien-core-platform-e1-foundation-change-set.md


- Summary: E2a is complete; E2b Target tag remains undiscoverable by Cost Explorer. E3/E4 are now repository-defined, static-validated controls awaiting guarded foundation creation and a real workflow run.
  Durable evidence: Target paths: infra/04.deploy/03.product/targets/kanbien-core-platform; package controls: .agentic/04.deploy and scripts/04.deploy/lifecycle/40-package; workflow: .github/workflows/publish-kanbien-core-platform-core-server.yml


- Summary: Completed reusable delivery hardening package
  Durable evidence: Durable controls: .agentic/04.deploy plans, standards, and schemas; target declarations under infra/04.deploy; generic validators and AWS adapters under scripts/04.deploy/lifecycle. Selected smoke, metadata, inventory, and whitespace checks passed. No AWS mutation occurred in this package.


- Summary: Refreshed chat branch from current local main before promotion
  Durable evidence: Preflight branch agentic/preflight/chat-2026-10-05-09-59-can-you-walk-me-through-wh-09a8fc533584/20261020171513 merged cleanly; applied commit 0b7768e9aa3e5f3ff60c6ae1f7635b304fbb939a; temporary preflight worktree and branch were removed; no stash or conflicts; post-refresh delivery controls passed.


- Summary: Recorded the approved short-lived cost-control waiver as target-local evidence and made it an executable pre-mutation gate; generic validation now rejects expired waivers.
  Durable evidence: Durable evidence is in foundation/evidence/target-cost-allocation-tag.yml, the fixed target cost-condition wrapper, static declaration test, and AWS release workflow.


- Summary: Release B publication run 39571727355 qualified digest sha256:721466…224ec2, deployed and privately verified. The target was restored to accepted A digest sha256:0992b…5d5d5 and private verification accepted.
  Durable evidence: Authoritative target evidence: bootstrap-runtime/accepted-release.yml and rehearsals/release-b-to-a-2026-10-21.yml; reusable verifier rule in verify-candidate and AWS workflow.


- Summary: Created a deployment placement-and-naming standard, proposed-path validator, and migration plan; no active paths or cloud state changed.
  Durable evidence: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md and .agentic/04.deploy/standards/deployment-artifact-placement-and-naming.md


- Summary: Batch 2 target declaration migration verification
  Durable evidence: Durable migration authority: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md. Validation passed: target declaration, package custody, and release contract smoke suites; all nine path-migration checks; generated recognition-source refresh and validation; staged metadata check. No cloud or GitHub mutation occurred. Next planned batch: AWS target workflow migration after consumer review.


- Summary: Batch 3 AWS workflow migration verification
  Durable evidence: Durable migration authority: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md. Moved the one AWS workflow only; active consumers and generated recognition sources now use its lifecycle-first target/scope path. Path-migration checker, target declaration, package custody, release-control, and migration-helper smoke tests passed. No AWS or GitHub mutation occurred.


- Summary: Batch 4 generic target-alignment migration verification
  Durable evidence: Durable migration authority: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md. Both reusable alignment artifacts moved to lifecycle-first clear-action paths; declaration coverage, implementation-plan metadata, and script README consumers were updated. Generated recognition sources, both path-migration checks, metadata, and migration-helper smoke passed. No provider mutation occurred.


- Summary: Runnable-program build-capability migration verification
  Durable evidence: Durable migration authority: ADR 0037 and .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md. Moved five runnable-program authority artifacts into 20-build and updated all active consumers. Passed runnable-program and core dependency-boundary smoke suites, five path-migration checks, generated recognition-source validation, metadata, and migration-helper smoke. No provider action occurred.


- Summary: Package-custody migration verification
  Durable evidence: Moved four package-custody authority artifacts into 40-package, updated active target pipeline and declaration checker consumers, refreshed recognition sources, and passed package-custody receipt, target package workflow, target declaration, four path-migration, and metadata checks. No provider action occurred.


- Summary: The proven core bootstrap route is active and has normal health, private verification, immutable update, and B-to-A restoration evidence; it has not yet exercised deliberate live health failure, ECS unhealthy-task replacement, or automatic health-triggered rollback. The next package is a reusable health/failure/recovery contract before persistence.
  Durable evidence: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md; .agentic/04.deploy/plans/execution/kanbien-core-platform-bootstrap.md; docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md; infra/04.deploy/03.product/targets/kanbien-core-platform/


- Summary: The reusable health/failure/recovery package is implemented locally and has passed its validator, core declaration/release route regressions, package custody check, platform-server check, placement, metadata, and diff checks. It is not yet committed; a generated Python cache was removed.
  Durable evidence: .agentic/04.deploy/60-run/; scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/; infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/.


- Summary: Current rehearsal control requires a fresh verifier boundary and does not mutate image, task definition, service configuration, network or IAM.
  Durable evidence: AWS-specific workflow: .agentic/aws/60-run/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/rehearse-accepted-workload-replacement.md; command: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.sh


- Summary: Live target final state: one healthy replacement task on task definition :10 and digest sha256:0992…d5d5d5; verifier exited 0 with KANBIEN_CORE_RELEASE_VERIFIED.
  Durable evidence: Evidence: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/rehearsals/accepted-workload-replacement-2026-10-21.yml


- Summary: Accepted bootstrap evidence remains valid; the foundation now has a verified USD 100 monthly target-filtered budget and the normal cost gate passes.
  Durable evidence: Budget declaration/evidence: infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/; governed provisioner: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/; live AWS evidence checked 2026-10-22T20:21:54Z.


- Summary: Carry forward the portable secret contract and executable inventory enforcement, with synthetic regression evidence.
  Durable evidence: Four regression suites, actual target/release gates, metadata and whitespace checks passed. Provider references, IAM, target isolation, secret delivery and live rotation remain PostgreSQL work; no new CI result or cloud proof is claimed.


- Summary: Implemented reusable persistence-safety harness controls and corrective credential lifecycle pass; live PostgreSQL/AWS work remains unstarted.
  Durable evidence: .agentic/04.deploy/00-target-alignment, .agentic/04.deploy/60-run, scripts/04.deploy/lifecycle, implementation plan, teaching handbook, and focused smoke/gate output.


- Summary: Persistence slice baseline established
  Durable evidence: Fresh AWS identity is account 337159794548 in eu-west-1; bootstrap-runtime is ACTIVE with desired/running one on task definition revision 10; no target RDS instance or Secrets Manager secret exists; target budget kanbien-core-platform-monthly is USD 100 filtered by Target=kanbien-core-platform with USD 0.7839062758 estimated spend through 2026-10-23. Local diagnostics, lifecycle inventory, health/recovery, secret-dependency, target declaration, release contract, and persistence-composition checks passed.


- Summary: Keep only the durable recovery evidence
  Durable evidence: RDS restore kanbien-core-platform-persistence-restore-20261023 became available, passed the governed restore posture check, and the first verifier task 559dcbbd4be74a9893d62f0ecf4f5e1a exited 0. A controller defect submitted a second read-only verifier attempt because stopped tasks were omitted. The harness correction and smoke test are the durable source; raw AWS task output need not be retained.


- Summary: Preserve recovery controller identity evidence
  Durable evidence: Current restore DbiResourceId is db-7AQ3CU3PEWLSGTNPUMPKEFODM4. Earlier restore-verifier task history remains intentionally excluded by the corrected incarnation-bound started-by identity. The test proves task lookup includes stopped tasks and restore incarnations receive distinct identities.


- Summary: The current packet adds governed runtime credential rotation/revocation operations, verifier health modes and package/live-controller coverage. The local Docker PostgreSQL/TLS proof initially exposed unhandled pg idle-client errors on revoke; the reusable adapter now handles that boundary and all relevant local gates pass.
  Durable evidence: Durable source: core-server-persistence entrypoints, lifecycle controls, adapter connection test, package smoke; generated local evidence is not a release receipt.


- Summary: Workflow 40197069234 failed before AWS mutation at release-succession validation; actual history SHA is 91bbb624... and original current pointer incorrectly declared f26dec40...
  Durable evidence: Exact proof root: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/. The next workflow must qualify and publish an immutable support image before retained-image compatibility can proceed.


- Summary: Workflow 40197461616 passed all repository gates, then Docker build failed at cp node_modules/@protobufjs/.; package closure now copies protobufjs unscoped. Local Docker is externally blocked at dockerfile frontend credential helper with WSL UtilAcceptVsock timeout.
  Durable evidence: Next required evidence is a successful CI package workflow on the source-closure fix; no ECR image or AWS target resource changed in either failed workflow.


- Summary: Workflow 40197714861 passed repository gates and failed before AWS/ECR action at unsupported unscoped OTel dependency copies. Current closure test passes using only pg dependencies plus node_modules/@opentelemetry.
  Durable evidence: Dockerfile infra/04.deploy/03.product/image/core-server-persistence/Dockerfile now contains only actual installed runtime package copies. Hosted CI remains needed for end-to-end image smoke/publication.


- Summary: Actual private support image sha256:bc9080d4ed02ad422100bd31ef17b213012de27bbb5a7c75f6b14ef77847a166 contains the administration program. The retained image sha256:30ae014c800769d9929db265ada4efd06c4712ca2e48d73c7ba455e55b25b4e3 passed the governed disposable PostgreSQL/TLS compatibility qualifier with it. Current stack has no observability parameters or target-owned SNS topic; only a staging topic exists and must not be reused.
  Durable evidence: Package provenance is GitHub Actions run 40197961821; local qualification is governed by scripts/04.deploy/lifecycle/40-package/qualify-retained-persistence-rollback-image/script.sh; current stack facts were read from CloudFormation in eu-west-1.


- Summary: A public ADOT OCI index is pinned by contract and package-tested structurally; the target catalogue now routes the collector through protected private custody. Static checks pass; publication and live observability proof remain pending.
  Durable evidence: Collector contract and config live under infra/04.deploy/03.product/image/core-server-persistence-observability-collector; workflow and guard live under .github/workflows and scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform.


- Summary: The merge base was c884c321. Main contained newer accepted scope/recovery controls; the chat branch contained permissions and observability corrections plus collector custody. The final tree has no conflicts and targeted package, declaration, target, and deployment-control regressions pass.
  Durable evidence: Durable details are in Git merge parents, collector custody artifacts, and this chat session log.


- Summary: Collector run 40200948509 qualified startup, private mirror, and then failed only before scan acceptance due to manifest-shape selection. The target-private digest sha256:d0a012... is not accepted as custody evidence yet. Resolver tests and the actual ECR response prove the corrective selector.
  Durable evidence: Workflow, resolver, and regression live in the collector package-custody directory; GitHub run 40200948509 remains the factual failed attempt.


- Summary: Collector GitHub runs 40200948509 and 40201291933 both reached private mirroring but failed only at ECR Basic Scan: UnsupportedImageError. The trusted fix uses pinned Trivy action ed142fd in an unprivileged public-source job and keeps credentialed package publication separate. Local package receipt, collector guard, declaration, and privilege-boundary tests pass.
  Durable evidence: Scanner boundary lives in the collector workflow; generic receipt vocabulary and regression live under .agentic/04.deploy/40-package and scripts/04.deploy/lifecycle/40-package/package-custody-receipt.


- Summary: Runs 40200948509 and 40201291933 established successful collector startup/mirror but ECR Basic scan unsupported; run 40201922054 established portable scanner cannot anonymously pull Public ECR due rate limit. The new three-job workflow scans a short-retention Docker-save artifact of the private immutable image with no AWS access, then finalizes custody only on scan success.
  Durable evidence: Workflow contract and static boundary guard remain under collector package custody; generic receipt validation records only safe scan verdict vocabulary.


- Summary: Collector run 40202249108 failed at public layer download only. The exact Linux/AMD64 public manifest and retained private ECR image share sha256:d0a012252142c0999982fc34cddc88e2f9ce8c6b2bdf2c53e8e489a49dfbac31.
  Durable evidence: Durable target contract and workflow are in infra/04.deploy/03.product/image/core-server-persistence-observability-collector and .github/workflows/publish-kanbien-core-platform-observability-collector.yml; run logs remain GitHub Actions evidence.


- Summary: Retained current implementation evidence: identity lifecycle, role-boundary recovery, restricted admin package smoke, restore/rollback qualifier, durable acceptance receipts, target and generic identity validators. Diagnostics commit a4eb4337 is already integrated at HEAD.
  Durable evidence: Authoritative current contracts: core-server-persistence declaration and acceptance route; current executable evidence: composition/package smoke, controller regressions, acceptance rehearsal; historic accepted-release remains immutable legacy evidence.


- Summary: Safe restore verifier mapping, controller receipt handling, 24 validated live receipts, two validated operation diagnostics, and rollback compatibility record are the active carry-forward facts.
  Durable evidence: Commits 8ff26fd6, 1b3d81cd, ed781c64; retained artifacts under infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/.


- Summary: Retained-package receipts from GitHub runs 40243828846 and 40247863444 are now preserved under the persistence scope; their source delta is mechanically limited to the restore verifier and its direct harness support.
  Durable evidence: The target-owned proof-applicability record is infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-applicability/restore-verifier-only-3edd9ac3002f.json; fresh current state and isolated-restore proof still remain required.


- Summary: The failed restored copy has been deleted and its temporary inline IAM policy is absent. The deployed service remains healthy. The next necessary live operation is a new qualified verifier image plus one fresh isolated restore proof; do not retry the expired DB incarnation.
  Durable evidence: Current task evidence is in AWS ECS/RDS and durable accepted proof receipts remain under the core-server-persistence target release-evidence directory.


- Summary: GitHub run 40252659734 qualified source 2a7a3d11 and immutable image sha256:5a7be9c80dea97a46d319058218ddc32788c8d1fcee617a4bedadf083376e3ba. Its custody receipt and a restore-verifier-only applicability record are target evidence. The failed temporary restored database and its temporary policy are absent; do not retry that incarnation.
  Durable evidence: Package receipt: core-server-persistence/30-release-evidence/package-receipts/package-custody-40252659734.json. Applicability: .../proof-applicability/restore-verifier-only-5a7be9c80dea.json. GitHub custody artifact run 40252659734 remains upstream evidence.


- Summary: The live observability activation completed with both ECS services healthy, but CloudWatch could not find the readiness metric because the collector selector was over-escaped and the alarm dimensions omitted readiness. The corrected declaration/template is commit 6accf269; this commit adds a change-set-reviewed collector-only repair controller and regression coverage.
  Durable evidence: Provider facts are in the kanbien-core-platform stack/ECS services; the governed repair controller, declaration validator, target smoke test, and AWS workflow are the durable repository evidence.


- Summary: Observability activation is healthy after a collector-only metric repair. The target still lacks confirmed SNS email delivery, so no revocation/recovery is repeated until the receipt controller can retain failure, notification, and recovery evidence.
  Durable evidence: Controller: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/. Receipt validator: .../observability-receipts.py. Acceptance collector/route now consume the three receipt references; AWS SNS read-only observation remains PendingConfirmation.

## Activity Log

### 2026-10-05T08:59:29Z - Session started

Initial intent: can you walk me through which part of my repo work on the following stages

### 2026-10-05 - Provider-neutral deployment layer bootstrap

- Added the `.agentic/04.deploy/` layer, transition plan, provider-adapter
  boundary, and Target Alignment Preflight workflow and standard.
- Added the non-executable capability home at
  `scripts/04.deploy/target-alignment-preflight/`.
- Regenerated and validated RAG recognition sources after adding the workflow.
- No AWS operation, PostgreSQL source change, target-definition change, or
  deployment execution occurred.

### 2026-10-05 - Lifecycle-map phase one

- Added the provider-neutral deployment lifecycle map and stage-ownership
  standard.
- Moved only the untracked Target Alignment capability placeholder to
  `scripts/04.deploy/lifecycle/00-target-alignment/`; no established script
  moved.
- Replaced the manual `aa` through `ag` empty phase folders with the numbered
  lifecycle taxonomy documented by the map.

### 2026-10-05 - Declaration Coverage foundation

- Added a draft Declaration Coverage standard, workflow, schema, field guide,
  and non-executable capability home under `00-target-alignment`.
- Added a bounded staging platform-shell contract covering only its runtime
  image, immutable image identity, health boundary, required non-secret app
  configuration, and rollback declaration.
- Explicitly excluded PostgreSQL Stage 6, queues/workers, identity, ingress,
  observability, and related dependencies from that first contract.
- Added `.agentic/04.deploy/` to the default YAML syntax-validation roots and
  refreshed the generated recognition sources.
- No AWS operation, PostgreSQL source change, target-definition mutation,
  secret read, or deployment execution occurred.

### 2026-10-06 - Inventory capability transfer

- Transferred the read-only deploy-control inventory capability from an
  accidental separate chat worktree into this active worktree.
- Preserved the existing preflight work; merged the shared deploy-script index
  entry manually and regenerated discovery sources from this combined state.
- Verified the four transferred capability files are byte-for-byte identical
  to their source worktree versions. The separate worktree remains untouched
  as a recovery copy.


### 2026-10-06T16:53:19Z - Context hygiene

Summary: Deployment governance baseline ready for checkpoint

Durable evidence: The active October 5 worktree contains the provider-neutral deployment layer, lifecycle/declaration-preflight foundations, deploy-control inventory, session-continuity safeguard, and the draft platform-to-target chain plan. PostgreSQL and AWS execution controls remain unchanged; the next step is a reviewed Phase 0 evidence map.


### 2026-10-06T16:56:32Z - ADR disposition

ADR needed: no

Reason: This commit establishes a draft, provider-neutral governance transition while leaving AWS execution authority and PostgreSQL controls unchanged. The existing migration plan records the transition; a separate ADR is required if a later change makes a durable provider-authority or deployment-architecture decision.


### 2026-10-06T16:57:10Z - Commit recorded

Commit: `9868be3a9bede808dd5bf3872d1a89fa64c62503`

Message: feat(deploy): add target alignment governance foundation

Summary: Added the provider-neutral deployment governance foundation, bounded declaration coverage and target-alignment planning, lifecycle map, deploy-control inventory, session-continuity safeguard, and the draft platform-to-target chain plan. No AWS, target, secret, or PostgreSQL Stage 6 mutation occurred.

ADR impact: No ADR: draft transition only; the existing migration plan retains AWS authority and any durable authority change needs separate review.


### 2026-10-06T23:15:16Z - Context hygiene

Summary: Scope/pipeline model and drift-evidence gap captured

Durable evidence: The deployment-chain plan now defines scope records, scope governance, pipeline catalogues, staged full-coverage adoption, and a separate AWS-governed drift-evidence producer before target-alignment automation. GitHub run 37510472773 showed reconciliation authentication/account/artifact-stack status pass but fail-closed stale artifact-stack drift evidence because its planned separate producer is not deployed. Local image smoke, ingress smoke, and controlled smoke are existing proof surfaces; they remain scattered until the first scope links them.


### 2026-10-06T23:16:09Z - Commit recorded

Commit: `f994270373f9703f1ebe1ce5c03d016ccfe91f53`

Message: docs(deploy): refine scope and pipeline control plan

Summary: Expanded the draft plan with scope criteria, target-local scope and pipeline catalogues, the first public-server scope path, package-publication custody, scope-qualified alignment, staged full-repository coverage, and an AWS-governed drift-evidence producer track based on verified reconciliation failures.

ADR impact: No ADR: this remains a draft planning refinement; AWS authority and target changes remain separately governed.


### 2026-10-07T15:38:27Z - Context hygiene

Summary: Captured the provider-neutral deployment learning and planning decisions: scope versus foundation ownership, configuration-surface visibility, provider selection, workload access, coverage states, and safe future tree migration.

Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md; teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md.


### 2026-10-07T15:43:45Z - ADR disposition

ADR needed: no

Reason: No ADR required: this commit refines a draft implementation plan and teaching note only; it makes no live provider-authority, target, or deployed-architecture decision. The plan retains review gates before implementation, provider selection, target-resource records, or AWS mutation.


### 2026-10-07T15:47:49Z - Commit recorded

Commit: `6572d8b5`

Message: docs(deploy): expand target control plan

Summary: Expanded the draft deployment-control plan with module configuration surfaces, foundation-resource ownership, provider-selection and workload-access contracts, complete-estate coverage states, lifecycle change/retirement rules, and safe future tree migration. Added a living packaging and deployment learning handbook.

ADR impact: No ADR: planning and education artifacts only; no live provider, target, or deployed-architecture decision.


### 2026-10-07T23:04:16Z - Context hygiene

Summary: Expanded the draft platform-to-target plan with repo-wide agentic change governance, generic harness portability rules, and product-to-deployment impact routing.

Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. The plan now defines .agentic as the authority for how agents change the repository, with source/infra as factual implementation and READMEs/docs as linked explanation.


### 2026-10-07T23:04:19Z - ADR disposition

ADR needed: no

Reason: This commit changes a draft governance plan only. It makes no live provider authority, target configuration, or deployed architecture decision.


### 2026-10-07T23:06:05Z - Commit recorded

Commit: `4a1ee583`

Message: docs(agentic): govern product-to-target changes

Summary: Expanded the draft plan with repo-wide agentic governance, generic harness portability rules, a migration path for scattered mandatory instructions, product-module contract controls, and explicit product-to-deployment impact routing. No AWS, target, secret, or PostgreSQL mutation occurred.

ADR impact: No ADR: draft plan and governance guidance only; no live provider authority, target configuration, or deployed architecture decision.


### 2026-10-08T16:30:49Z - ADR disposition

ADR needed: no

Reason: This commit updates a draft plan and teaching material only. It creates no live target, provider-authority, or deployed-architecture decision.


### 2026-10-08T16:30:59Z - Context hygiene

Summary: Expanded the draft plan and teaching handbook with a concern-control matrix, dependency availability and observation governance, operation-and-promise scope declarations, safe diagnostics, networking, and source-of-truth lessons.

Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. Teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md.


### 2026-10-08T16:32:57Z - Commit recorded

Commit: `82ac95eb`

Message: docs(deploy): plan dependency behaviour controls

Summary: Added concern-control governance, dependency availability and observation artifacts, operation-and-promise scope declarations, and durable teaching lessons for dependency behaviour, networking, safe diagnostics, and source-of-truth ownership. No AWS, target, secret, or PostgreSQL mutation occurred.

ADR impact: No ADR: draft governance and education only; no live provider authority, target configuration, or deployed architecture decision.


### 2026-10-17T21:12:27Z - Context hygiene

Summary: Expanded the deployment-control plan and teaching handbook with dependency lifecycle, network relationship, workload identity/access, credential rotation, and safe failure-handling lessons.

Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. Teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md.


### 2026-10-17T21:12:35Z - ADR disposition

ADR needed: no

Reason: This change refines a draft provider-neutral governance plan and teaching material only. It makes no live target, provider-authority, or deployed-architecture decision.


### 2026-10-17T21:14:01Z - Commit recorded

Commit: `a6e69078`

Message: docs(deploy): govern dependency identity lifecycle

Summary: Expanded the deployment-control plan and teaching handbook with dependency lifecycle, network relationship, workload identity/access, credential rotation, and safe failure-handling governance. No AWS, target, secret, or runtime changes occurred.

ADR impact: No ADR: draft provider-neutral governance and education only; no live provider, target, or deployed-architecture decision.

### 2026-10-18T21:01:46Z - Context hygiene

Summary: Continued the deployment learning and draft control design without
mutating AWS, targets, secrets, runtime code, or PostgreSQL. The uncommitted
plan and handbook now cover health and release verification, recovery and
rollback evidence, safe observability and alerting, target alignment and
drift, scope responsibility inventories, and package publication, custody,
promotion, and policy exceptions.

Durable evidence: `.agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md`
and `docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md`.
Both files are intentionally uncommitted pending the user's later review and
explicit commit request. The plan defines future provider-neutral artifact
sets only; it does not authorise target inspection, AWS mutation, deployment,
or automatic remediation.


### 2026-10-18T21:04:40Z - Commit recorded

Commit: `49f12712`

Message: docs(deploy): govern release and package control

Summary: Expanded the draft deployment-control plan and teaching handbook with scope responsibility inventories; health, release-verification, rollback and recovery controls; safe observability and alerting; target alignment; and immutable package custody, promotion, and exception governance. No AWS, target, secret, runtime, or PostgreSQL mutation occurred.

ADR impact: No ADR: this remains draft provider-neutral governance and education material; it makes no live provider-authority, target-configuration, or deployed-architecture decision.


### 2026-10-18T21:05:58Z - Context hygiene

Summary: Refreshed the active chat branch from local main through a governed rehearsal after merge verification reported one incoming main commit and two chat-only commits. The rehearsal had no overlapping paths or conflicts; stash was not used.

Durable evidence: Refresh source head: 18d9bb031b3ec6d709b1d5fd3018233cb1b18830; applied tested merge commit: d479bece947e091737fe27e729a9f12b33eb2b27; preflight branch/worktree were removed by the governed apply script; documentation header validation passed afterward.


### 2026-10-18T22:40:12Z - Context hygiene

Summary: Refined the deployment learning model: the public server is the bootstrap runtime slice, not the complete platform foundation. The agreed staged foundation order is bootstrap runtime/release evidence, persistence, application security, fuller observability, then product capabilities. Existing platform and core code remains factual source material and will be brought into scope incrementally.

Durable evidence: Durable evidence: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md and docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md. The next approved activity is a read-only inventory of modules composed by the bootstrap server.


### 2026-10-18T22:40:52Z - Commit recorded

Commit: `cfb65999`

Message: docs(deploy): stage platform foundation controls

Summary: Defined the bootstrap runtime slice, staged persistence/security/observability foundation order, and incremental product/core integration path. Existing platform and core code remains factual source material; no AWS, target, secret, runtime, or PostgreSQL mutation occurred.

ADR impact: No ADR: this refines the draft provider-neutral governance and education model without making a live target, provider-authority, or deployed-architecture decision.


### 2026-10-18T22:41:35Z - Context hygiene

Summary: Refreshed the active chat branch from local main through a governed rehearsal after local promotion verification reported divergence. The rehearsal had no conflicts; stash was not used.

Durable evidence: Refresh source head: c4b01422ba10dfabf3111a88c693c186abae0a2e; applied tested merge commit: 02d0e7909b9dff9d492ff38a8a64a2e99208bfc3; temporary preflight branch/worktree were removed by the governed apply script; documentation header validation passed afterward.


### 2026-10-18T23:48:58Z - Decision

Decision: Adopt the kanbien-core-platform bootstrap lifecycle proof

Rationale: The first controlled slice must establish a private target from an absent baseline as immutable release A, then verify one planned update to release B. A rejected B preserves A and must not trigger automatic redeployment. Existing kanbien/staging remains read-only reference evidence.


### 2026-10-18T23:49:03Z - Context hygiene

Summary: Recorded the controlled first-target lifecycle, private verifier boundary, configuration/access/network separation, safe verifier diagnostics, and A-to-B recovery evidence. No AWS, target directory, runtime, secret, or PostgreSQL change occurred.

Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. Teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md. Validation: artifact metadata headers and git diff --check passed.


### 2026-10-18T23:50:23Z - Commit recorded

Commit: `8315f1d1`

Message: docs(deploy): define bootstrap target lifecycle

Summary: Defined the planned private kanbien-core-platform bootstrap target lifecycle: clean creation from absent baseline A, one controlled candidate update B, safe verifier/configuration/access/network boundaries, receipts, and recovery without automatic redeployment. Updated the deployment plan and teaching handbook; no AWS, target, secret, runtime, or PostgreSQL mutation occurred.

ADR impact: No ADR: this is a draft governance and education refinement. It does not create a live target, change provider authority, or decide a deployed architecture.


### 2026-10-19T06:49:54Z - Decision

Decision: Adopt a dedicated core-server package boundary

Rationale: The planned kanbien-core-server.main.ts uses existing platform-server startup and transport, gains generic release-verification and visible configuration contracts, and is packaged in a dedicated core-server image. Generic observability must be separated from its optional persistence bridge. Technical infrastructure permissions are grouped under technical-access; the verifier route remains bootstrap-scope-owned.


### 2026-10-19T06:49:54Z - Context hygiene

Summary: Recorded runnable-program selection, generic release-verification ownership, package versus runtime dependency distinction, optional observability-persistence bridge, technical-access naming, and dedicated core-image boundary. No source implementation, AWS resource, target directory, secret, or PostgreSQL state changed.

Durable evidence: Durable plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md. Teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md. Artifact metadata and whitespace checks passed.


### 2026-10-19T06:51:03Z - Commit recorded

Commit: `39d4a649`

Message: docs(deploy): define core server package boundary

Summary: Recorded the planned kanbien-core-server entrypoint family, generic release-verification/configuration ownership, technical-access naming, optional observability-persistence bridge, and dedicated core-server image boundary. No source implementation, AWS resource, target directory, secret, runtime, or PostgreSQL state changed.

ADR impact: No ADR: this remains a draft governance and education refinement; it creates no live target or deployed architecture.


### 2026-10-19T19:37:55Z - Decision

Decision: Adopt lifecycle-owned core release rehearsal layout

Rationale: The first core-server rehearsal uses numbered build, package, deploy, and run script homes; it keeps generic rules in .agentic, factual selection in platform and infra, and safe run receipts in GitHub Actions without altering staging.


### 2026-10-19T19:37:56Z - ADR disposition

ADR needed: no

Reason: This commits a planning and teaching refinement only. It creates no durable target, provider-authority, or runtime architecture decision; those require later reviewed implementation and target-design work.


### 2026-10-19T19:37:56Z - Context hygiene

Summary: Core rehearsal blueprint is ready to commit

Durable evidence: Plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md; teaching record: docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md. The planned target remains absent; implementation begins with generic rules and report-only local checks, not AWS mutation.


### 2026-10-19T19:38:57Z - Commit recorded

Commit: `fa4fcaae`

Message: docs(deploy): map core release rehearsal

Summary: Recorded the core-server release rehearsal layout, lifecycle-owned check locations, persistence-owned observability integration, safe evidence locations, and staged implementation order. No runtime, AWS, target, or GitHub mutation occurred.

ADR impact: No ADR: documentation-only planning refinement; target and provider decisions remain subject to later review.


### 2026-10-19T19:58:27Z - Decision

Decision: Approve the target-scoped script structure for the rehearsal

Rationale: Build and package scripts remain lifecycle-owned and target-neutral; deploy and run scripts are nested under the exact target and scope so no staging script can be repointed by a free-form flag.


### 2026-10-19T19:58:27Z - ADR disposition

ADR needed: no

Reason: The rehearsal plan remains review-only, leaves target/provider decisions unselected, and authorizes no AWS change. A later approved target design may require an ADR.


### 2026-10-19T19:58:27Z - Context hygiene

Summary: Target-specific release rehearsal plan ready

Durable evidence: Durable review plan: docs/aws/kanbien-core-platform-release-rehearsal-plan.md. It defines R1-R6 repository packages, E0-E7 AWS gates, isolation from staging, and requires exact future approval before any AWS mutation.


### 2026-10-19T19:59:23Z - Commit recorded

Commit: `f6256292`

Message: docs(aws): plan core platform release rehearsal

Summary: Added the review-only, target-specific Kanbien core-platform rehearsal plan. It defines isolated R1-R6 implementation packages, E0-E7 execution gates, stage-plus-target script ownership, safe receipts, and explicit future AWS approval requirements.

ADR impact: No ADR: no target/provider decision is selected or executed by this plan.


### 2026-10-19T20:11:17Z - Decision

Decision: Adopt generic runnable-program contract control

Rationale: R1 supplies provider-neutral runnable-program, image-command, candidate-identity, dependency-boundary, and safe-evidence declaration governance with deterministic report-only failure fixtures before package construction.


### 2026-10-19T20:11:17Z - ADR disposition

ADR needed: no

Reason: R1 is generic provider-neutral governance and a report-only check; it creates no target-specific architecture or external state.


### 2026-10-19T20:11:17Z - Context hygiene

Summary: R1 runnable-program contract control is ready to commit

Durable evidence: Generic standard/workflow/schema/template/guide are under .agentic/04.deploy; report-only checker and fixtures are at scripts/04.deploy/lifecycle/20-build/runnable-program-contract/. It passed its smoke, metadata, drift, and whitespace checks; no AWS or runtime change occurred.


### 2026-10-19T20:12:10Z - Commit recorded

Commit: `e9fbc711`

Message: feat(deploy): add runnable program contract gate

Summary: Added provider-neutral runnable-program and package-candidate governance, contract schema/template/guide, and report-only checker fixtures that fail closed for missing records, invalid commands, unapproved dependencies, and unsafe evidence fields. No runtime, target, AWS, or GitHub change occurred.

ADR impact: No ADR: generic governance and a local report-only gate only.


### 2026-10-19T20:33:22Z - Decision

Decision: Adopt persistence-owned observability integration and server configuration boundary

Rationale: Generic observability now contains only reusable signals; persistence owns the optional bridge. Platform server owns safe runtime configuration resolution and release identity shaping. The change implements the approved core-server boundary without adding a target, image, AWS resource, or deployment.


### 2026-10-19T20:33:28Z - Decision

Decision: Adopt persistence-owned observability integration and server configuration boundary

Rationale: Generic observability now contains only reusable signals; persistence owns the optional bridge. Platform server owns safe runtime configuration resolution and release identity shaping. The change implements the approved core-server boundary without adding a target, image, AWS resource, or deployment.


### 2026-10-19T20:33:29Z - ADR disposition

ADR needed: no

Reason: This applies the already-approved core release boundary; it does not select a provider, target, runtime, networking design, or authority model.


### 2026-10-19T20:33:29Z - Context hygiene

Summary: R2 passed the server, persistence, and observability package checks. The persistence observer was moved out of generic observability, and server configuration/release identity are now explicit exported contracts.

Durable evidence: Durable implementation: platform/observability, platform/persistence/src/observability, and platform/server/src/{configuration,verification}; plan: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md.


### 2026-10-19T20:35:28Z - Commit recorded

Commit: `2a96d7f2`

Message: feat(platform): separate persistence observability

Summary: Moved persistence-specific observation integration into platform/persistence; removed persistence from generic observability; made server runtime configuration and safe release identity explicit, tested platform contracts.

ADR impact: No ADR: implements the approved package boundary without provider or target selection.


### 2026-10-19T20:49:42Z - Decision

Decision: Adopt the core-server runnable-program boundary and dependency proof

Rationale: The bootstrap program reuses platform-server, exposes only a safe release-verification operation, and is rejected if its source or compiled output includes a forbidden dependency. No target, image, provider, or cloud choice is made.


### 2026-10-19T20:49:42Z - ADR disposition

ADR needed: no

Reason: This implements the approved bootstrap-program boundary without a durable provider, target, network, or authority decision.


### 2026-10-19T20:49:42Z - Context hygiene

Summary: R3 proves the core server route and dependency graph locally: release verification responds safely, product routes are absent, and a compiled persistence import fails closed.

Durable evidence: Durable code: infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts and runnable-program-index.yml; local proof: scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/.


### 2026-10-19T20:50:37Z - Commit recorded

Commit: `8c110812`

Message: feat(deploy): add core server runnable program

Summary: Added the core-server entrypoint, factual runnable-program declaration, isolated compile configuration, and deterministic dependency-boundary proof that rejects forbidden package payloads.

ADR impact: No ADR: implements the approved bootstrap boundary without selecting a target or provider.


### 2026-10-19T21:02:49Z - Decision

Decision: Adopt a dedicated local core-server image boundary

Rationale: The image is built from an explicit minimal source closure, runs as node with one command, and package proof rejects forbidden compiled dependencies before any target or registry operation. A missing Docker daemon records a skip rather than a false image-success claim.


### 2026-10-19T21:02:49Z - ADR disposition

ADR needed: no

Reason: The dedicated package boundary was approved in the existing core release plan; no provider, target, registry, or runtime selection is made.


### 2026-10-19T21:02:49Z - Issue

Raised: Docker daemon unavailable for local core image smoke

Resolution: Static payload and negative-fixture proof pass. The build and smoke scripts fail closed by default and only report an explicit skip with --allow-skip-without-engine; Docker runtime proof remains required before release qualification.


### 2026-10-19T21:02:49Z - Context hygiene

Summary: R4 adds a minimal core-server Dockerfile, image contract, package payload verifier, and smoke capability. The machine has Docker CLI but no daemon; no image was built or started.

Durable evidence: Durable artifacts: infra/04.deploy/03.product/image/core-server/ and scripts/04.deploy/lifecycle/40-package/{build-core-server-image,smoke-test-core-server-image}/.


### 2026-10-19T21:04:22Z - Commit recorded

Commit: `bb539fe3`

Message: feat(deploy): add core server image boundary

Summary: Added the dedicated core-server image contract, minimal Dockerfile, payload verifier, and local smoke scripts. Static package proof passed; Docker build/run remains explicitly skipped because this environment has no running daemon.

ADR impact: No ADR: implements approved package boundary; no registry, provider, or target was selected.


### 2026-10-20T03:27:40Z - Context hygiene

Summary: Refreshed the active chat branch from local and fetched origin/main through a governed rehearsal. The preflight cleanly merged the single incoming main commit; no conflicts or stash were used. R1-R4 focused checks passed in the preflight, with Docker runtime smoke still an explicit skip because no daemon is available.

Durable evidence: Refresh source head: e5d13305; applied preflight merge: dedeeef0675f49a655ebbb9773e9f3ed78b83f69; temporary preflight worktree and branch were removed by the governed apply script.


### 2026-10-20T03:36:12Z - Decision

Decision: Adopt the planned-not-live-selected kanbien-core-platform target declaration

Rationale: The repository records the target’s scope, safe configuration shapes, technical-access intent, private verifier requirement, receipt and rollback requirements, and all E0 selection gaps. It blocks target mutation until live facts are inspected and an approved change set exists.


### 2026-10-20T03:36:12Z - ADR disposition

ADR needed: no

Reason: This is a fail-closed repository declaration; it does not choose an AWS account, region, runtime, network, role, registry, or provider resource.


### 2026-10-20T03:36:12Z - Context hygiene

Summary: Refreshed from the accepted local-main merge through a clean rehearsal, then added R5’s static planned-target declarations. The target checker passes only repository-declaration completeness; live alignment remains not checked and all E0 facts remain unresolved blockers.

Durable evidence: Durable artifacts: infra/04.deploy/03.product/targets/kanbien-core-platform/ and scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/.


### 2026-10-20T03:36:52Z - Commit recorded

Commit: `60891e4b`

Message: feat(deploy): declare core platform target

Summary: Added the planned-not-live-selected kanbien-core-platform target, bootstrap scope, foundation/access/network/pipeline declarations, and fail-closed static coverage verifier. Every live provider fact remains explicit E0-required and target mutation is blocked.

ADR impact: No ADR: no AWS/provider selection or live resource decision was made.


### 2026-10-20T03:46:06Z - Decision

Decision: Adopt fixed target-bound R6 control surfaces

Rationale: Prepare, deploy, and verify commands are permanently bound to kanbien-core-platform/bootstrap-runtime, reject free-form target selection, emit safe diagnostics, and cannot contact a provider until E0/E1 facts and approvals exist.


### 2026-10-20T03:46:06Z - ADR disposition

ADR needed: no

Reason: The controls implement the already-approved rehearsal boundary; they do not select or mutate any provider resource.


### 2026-10-20T03:46:06Z - Context hygiene

Summary: R6 adds target-bound prepare/deploy/verify entrypoints with no provider clients or external commands. They pass smoke tests, reject target override, and report unresolved E0 facts plus external_access_attempted false.

Durable evidence: Durable controls: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/ and scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/.


### 2026-10-20T03:46:39Z - Commit recorded

Commit: `25014ff9`

Message: feat(deploy): add core target control surfaces

Summary: Added fixed prepare/deploy/verify control commands for kanbien-core-platform/bootstrap-runtime. They reject target overrides, validate static evidence, and fail closed with unresolved E0 facts before any external access.

ADR impact: No ADR: no provider selection or target mutation occurred.


### 2026-10-20T03:54:24Z - Issue

Raised: Core-server image command wrapper exited cleanly without starting the server

Resolution: The real Docker smoke exposed that the generated wrapper only required the compiled entrypoint. It now invokes runKanbienCoreServerMain; a new pre-Docker runtime command proof and real container smoke verify liveness, readiness, and safe release identity.


### 2026-10-20T03:54:24Z - Context hygiene

Summary: Docker became available during the full proof run. It built the local core image and exposed a start-command defect, which was repaired and confirmed by actual restricted container health/readiness/release-verification smoke.

Durable evidence: Durable repair: scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs and smoke-test-core-server-image/runtime-command-test.mjs.


### 2026-10-20T03:54:43Z - Commit recorded

Commit: `ad6cf1e8`

Message: fix(deploy): start core image command

Summary: Fixed the generated image command wrapper to invoke the core server. Added a command-runtime test; the actual local Docker image now passes liveness, readiness, and safe release-verification smoke under restricted runtime settings.

ADR impact: No ADR: repair within the existing image contract.


### 2026-10-20T08:08:38Z - Issue

Raised: E0 candidate network is not yet viable for an isolated private container workload

Resolution: Read-only candidate inspection found no core-target naming conflict in account 337159794548/eu-west-1 and found a project VPC with two private subnets, but they have only an S3 gateway endpoint and no NAT/ECR/CloudWatch route. Runtime, registry, verifier placement, cost guard, roles, and rollback custody remain unresolved. No AWS state changed.


### 2026-10-20T08:08:38Z - Context hygiene

Summary: Completed E0 read-only discovery against available profile kanbien-dev (account 337159794548, eu-west-1). The candidate account has a GitHub Actions OIDC provider and staging-only budgets but no core target resource conflict. Its private network is insufficient for container image pull/logging without an approved network design change.

Durable evidence: Safe evidence is in this session log; live target declaration remains intentionally unresolved in infra/04.deploy/03.product/targets/kanbien-core-platform/target-profile.yml. No resource, setting, secret, registry, or target was changed.


### 2026-10-20T08:46:15Z - Decision

Decision: Selected private ECS Fargate candidate design for kanbien-core-platform E1

Rationale: The candidate uses the existing private VPC/subnets as a limited shared-foundation exception; all workload, IAM, ECR, logging, service-discovery, and verifier resources remain target-owned. No AWS mutation was performed.


### 2026-10-20T08:46:15Z - Issue

Raised: E1 cannot yet become executable

Resolution: Read-only cost evidence shows only USD 25 monthly staging budgets. The selected two-AZ interface-endpoint topology has recurring cost, so a target-specific monthly ceiling, alert destination, and GitHub Environment protection owner remain required before an exact CloudFormation change set can be approved.


### 2026-10-20T08:46:15Z - Context hygiene

Summary: Refreshed the active chat branch cleanly from accepted local main through a rehearsed preflight; recorded E1 candidate topology and budget evidence.

Durable evidence: Durable design: docs/aws/architecture/adrs/0003-private-ecs-bootstrap-target-for-kanbien-core-platform.md and docs/aws/kanbien-core-platform-e1-foundation-change-set.md. Read-only provider evidence only; no AWS mutation.


### 2026-10-20T09:01:30Z - Issue

Raised: Target-scoped cost guard is not yet feasible

Resolution: Read-only Cost Explorer inspection returned no active Target cost-allocation tag. The proposed USD 100 budget would not reliably isolate kanbien-core-platform cost until account-level tag activation is approved and completed. No AWS billing setting or resource was changed.


### 2026-10-20T09:21:41Z - Issue

Raised: AWS rejected cost-allocation tag activation without mutation

Resolution: The approved Cost Explorer activation command failed with Tag keys not found: Target. AWS requires the user-defined tag to exist on a resource before it can be activated. No account setting or target resource changed; the foundation sequence must introduce a target-tagged low-risk resource, then activate and wait for propagation before relying on the USD 100 target budget.


### 2026-10-20T10:06:41Z - Decision

Decision: User approved bounded kanbien-core-platform E1-E7 execution packet

Rationale: Authority covers reviewed repository changes, commits, main promotion and push; selected kanbien-dev/eu-west-1 target resources; USD 100/month target guard; protected GitHub Environment; one B-to-A rollback; cost-tag propagation wait; and stops only for unexpected security risk, extra cost/resource category, AWS/GitHub denial, or an out-of-bound result. Alert email is execution-only and must not be recorded.


### 2026-10-20T10:07:39Z - Commit recorded

Commit: `ca639258dab1c423d7d8ac7c2045223bbbb358fe`

Message: docs(deploy): phase core platform cost controls

Summary: Recorded the E1 private ECS target design, phased cost-tag bootstrap, review-only foundation templates, and bounded execution authority. No AWS resource was created; the first AWS mutation remains the separately controlled empty ECR tag bootstrap.

ADR impact: ADR 0003 records the private ECS bootstrap topology and shared-VPC exception.


### 2026-10-20T10:32:22Z - Issue

Raised: E2b account tag discovery is still propagating

Resolution: E2a created only the empty immutable Target-tagged core image repository. AWS Cost Explorer still returns Tag keys not found for Target, so no guarded foundation has been created.


### 2026-10-20T10:32:22Z - Decision

Decision: Completed E2a tag bootstrap and GitHub Environment guard

Rationale: The ECR tag-bootstrap stack is CREATE_COMPLETE with no image or workload. GitHub Environment kanbien-core-platform now requires the repository owner and accepts only main deployments. Cost-tag activation remains pending AWS discovery.


### 2026-10-20T10:32:23Z - Context hygiene

Summary: E2a created one empty immutable ECR repository under the approved target prefix; the account Target allocation tag is not yet discoverable by Cost Explorer. Foundation template was corrected locally to consume this repository rather than recreate it.

Durable evidence: AWS stack kanbien-core-platform-tag-bootstrap; repo files infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/foundation.yml and docs/aws/kanbien-core-platform-e1-foundation-change-set.md


### 2026-10-20T10:33:20Z - Commit recorded

Commit: `60a59af366eea2ceed84ea83cd960e2a6d4a350a`

Message: fix(deploy): consume core tag bootstrap repository

Summary: Recorded E2a creation evidence and corrected the E2c foundation to consume the immutable ECR repository created by tag bootstrap instead of attempting a duplicate; added explicit Target tags to target-owned foundation resources.

ADR impact: ADR 0003 unchanged; execution evidence supports its phased private target decision.


### 2026-10-20T10:52:01Z - Decision

Decision: Implemented E3/E4 repository controls while E2b propagates

Rationale: Added package custody receipt governance and a protected manual-only target image workflow; added a private immutable-digest runtime and verifier stack; hardened the E2 foundation. No E2c+ AWS resource was created.


### 2026-10-20T10:52:01Z - Context hygiene

Summary: E2a is complete; E2b Target tag remains undiscoverable by Cost Explorer. E3/E4 are now repository-defined, static-validated controls awaiting guarded foundation creation and a real workflow run.

Durable evidence: Target paths: infra/04.deploy/03.product/targets/kanbien-core-platform; package controls: .agentic/04.deploy and scripts/04.deploy/lifecycle/40-package; workflow: .github/workflows/publish-kanbien-core-platform-core-server.yml


### 2026-10-20T10:53:24Z - Commit recorded

Commit: `7ea7371fd10ad2bcb3fd7b6c147b774fc75e99fa`

Message: feat(deploy): add core platform custody and runtime controls

Summary: Added target-bound package custody workflow and safe receipt validation, private immutable-digest runtime/verifier CloudFormation, and hardened foundation network and ECR controls. All local static, receipt, workflow, target declaration, whitespace and CloudFormation validation checks passed; E2c remains blocked by AWS Target cost-tag propagation.

ADR impact: ADR 0003 remains the applicable private ECS target decision.


### 2026-10-20T11:32:15Z - Decision

Decision: Accepted temporary waiver of the target-specific budget activation gate

Rationale: User explicitly accepts only the delay in Target cost-allocation tag discovery. E2c-E7 may proceed with one task, no autoscaling, no NAT, no public ingress, no data services, and no new cost categories. The USD 100 Target-filtered budget must be activated and verified once AWS exposes the tag.


### 2026-10-20T11:40:36Z - Commit recorded

Commit: `7720422a1fca3b267ebf6925cc29c1c5887fb979`

Message: feat(deploy): create private core platform foundation

Summary: Recorded temporary cost-budget waiver and corrected CloudFormation parameter validation after it rejected valid private VPC inputs. The approved kanbien-core-platform foundation stack is CREATE_COMPLETE; target-specific budget remains deferred until AWS exposes Target.

ADR impact: ADR 0003 remains applicable.


### 2026-10-20T17:12:54Z - Decision

Decision: Adopt reusable delivery-control layering

Rationale: Provider-neutral validators now consume contracts and safe normalized evidence; AWS adapters own policy parsing and ECR probes; fixed target wrappers provide Kanbien choices without permitting arbitrary substitution.


### 2026-10-20T17:12:54Z - Context hygiene

Summary: Completed reusable delivery hardening package

Durable evidence: Durable controls: .agentic/04.deploy plans, standards, and schemas; target declarations under infra/04.deploy; generic validators and AWS adapters under scripts/04.deploy/lifecycle. Selected smoke, metadata, inventory, and whitespace checks passed. No AWS mutation occurred in this package.


### 2026-10-20T17:12:54Z - ADR disposition

ADR needed: no

Reason: The generic validator/adapter/wrapper split is an implementation of the existing provider-neutral deployment architecture, not a new repository-wide architectural decision.


### 2026-10-20T17:14:39Z - Commit recorded

Commit: `02405b56499ba30f928aaad539df27756167c5cf`

Message: feat(deploy): harden reusable package delivery controls

Summary: Separated reusable delivery validators from AWS adapters and fixed target wrappers; added safe asynchronous-condition evidence, delivery policy coverage, package qualification, execution-state enforcement, and diagnostics. All selected repository checks passed; no AWS mutation occurred.

ADR impact: No ADR needed: implements the existing provider-neutral deployment architecture.


### 2026-10-20T17:15:58Z - Context hygiene

Summary: Refreshed chat branch from current local main before promotion

Durable evidence: Preflight branch agentic/preflight/chat-2026-10-05-09-59-can-you-walk-me-through-wh-09a8fc533584/20261020171513 merged cleanly; applied commit 0b7768e9aa3e5f3ff60c6ae1f7635b304fbb939a; temporary preflight worktree and branch were removed; no stash or conflicts; post-refresh delivery controls passed.


### 2026-10-20T18:53:06Z - Commit recorded

Commit: `b34c211e`

Message: feat(deploy): add live core runtime control chain

Summary: Added reusable alignment, reviewed change-set, deployment, and private-verification controls; added the output-only foundation contract required for the core runtime.

ADR impact: No new ADR; implements the existing deployment control plan.


### 2026-10-20T18:53:06Z - Commit recorded

Commit: `85cdd2d2`

Message: chore(deploy): remove generated bytecode

Summary: Removed accidental generated Python bytecode from the deployment-control commit.

ADR impact: No ADR impact.


### 2026-10-20T18:53:06Z - Commit recorded

Commit: `139d26db`

Message: chore(repo): ignore python bytecode

Summary: Prevented generated Python bytecode from being tracked in future deployment work.

ADR impact: No ADR impact.


### 2026-10-20T18:55:19Z - Decision

Decision: Promoted the verified deployment-control source to origin/main.

Rationale: Remote promotion was a normal fast-forward from 1b56931d to 81abadac after the inventory, target-declaration, fixed runtime-control, package-custody, alignment-validation, and whitespace gates passed in the isolated integration worktree.


### 2026-10-20T18:58:21Z - Issue

Raised: The live alignment gate rejected a healthy foundation after an output-only stack update.

Resolution: The AWS adapter recognised CREATE_COMPLETE but not UPDATE_COMPLETE, despite both being stable CloudFormation success states.


### 2026-10-20T18:58:21Z - Decision

Decision: Alignment now recognises the stable successful CloudFormation lifecycle states explicitly.

Rationale: The adapter accepts only CREATE_COMPLETE and UPDATE_COMPLETE; its new regression test rejects in-progress and rollback states.


### 2026-10-20T19:04:38Z - Commit recorded

Commit: `8a0ffd8f`

Message: fix(deploy): accept stable foundation update state

Summary: Accepted only stable successful CloudFormation states in AWS alignment and added a regression test; repaired metadata coverage for the related target-alignment controls.

ADR impact: No new ADR; corrects the implementation of the approved alignment control.


### 2026-10-20T19:10:05Z - Issue

Raised: Runtime change-set creation failed before creating the stack because the template rejected the qualified ECR repository URI.

Resolution: The ImageRepositoryUri AllowedPattern used double escaping in YAML single quotes, which made the regex require literal backslashes.


### 2026-10-20T19:10:05Z - Decision

Decision: Runtime template parameter patterns must be tested against a representative valid provider identifier.

Rationale: The fixed bootstrap-runtime smoke test now validates the exact ECR repository URI shape, and the change-set control maps provider parameter-pattern failures to aws-parameter-invalid without exposing values.


### 2026-10-20T19:11:43Z - Decision

Decision: Cloud-mutating controls now have a standard metadata effect category.

Rationale: aws-mutation is added to the central metadata taxonomy, documented standard, and checker fallback; it distinguishes provider state changes from ordinary network reads.


### 2026-10-20T19:12:51Z - Commit recorded

Commit: `5fd8014c`

Message: fix(deploy): validate runtime provider parameters

Summary: Corrected the runtime ECR URI contract, added representative provider-identifier regression coverage, mapped parameter failures safely, and added aws-mutation to the shared metadata taxonomy.

ADR impact: No new ADR; corrects reusable deployment and harness metadata controls.


### 2026-10-20T19:16:03Z - Issue

Raised: The deploy control rejected a reviewed initial change set because CloudFormation omitted ChangeSetType from its describe response.

Resolution: The stack was absent and the change set was CREATE_COMPLETE and AVAILABLE, but the control incorrectly required a field AWS did not return.


### 2026-10-20T19:16:03Z - Decision

Decision: Initial create review accepts an omitted ChangeSetType only with independent proof that the runtime stack is absent.

Rationale: The deploy control accepts CREATE_COMPLETE with type CREATE or omitted only when describe-stacks proves absence; it rejects update types and existing stacks.


### 2026-10-20T19:16:57Z - Commit recorded

Commit: `e517670c`

Message: fix(deploy): verify initial change-set state

Summary: Corrected initial change-set review to use stable AWS evidence when ChangeSetType is omitted, with regression coverage for absent versus existing runtime stacks.

ADR impact: No new ADR; corrects reusable deployment-control interpretation.


### 2026-10-20T19:19:36Z - Issue

Raised: The deploy control still rejected the initial change set because CloudFormation creates an empty REVIEW_IN_PROGRESS stack while the change set awaits execution.

Resolution: No runtime resources existed; the review stack is CloudFormation’s normal create-change-set lifecycle state.


### 2026-10-20T19:19:36Z - Decision

Decision: Initial runtime deployment recognises CloudFormation REVIEW_IN_PROGRESS as an empty review boundary, not a deployed runtime.

Rationale: The control accepts only absent or REVIEW_IN_PROGRESS stacks with the expected create change set, and continues to reject CREATE_COMPLETE or any update type.


### 2026-10-20T19:20:33Z - Commit recorded

Commit: `2928e1e956adc1cb8c81b3d0c9f92d4727d9fdec`

Message: fix(deploy): recognise initial review stack

Summary: Recognised CloudFormation REVIEW_IN_PROGRESS as the only permitted initial change-set review stack, with regression coverage that rejects a real deployed runtime.

ADR impact: No new ADR; corrects reusable deployment-control interpretation.


### 2026-10-20T19:24:01Z - Issue

Raised: CloudFormation rejected the ECS service registry binding because the target service-discovery resource uses A records.

Resolution: The runtime template incorrectly supplied container-name and container-port fields that apply to SRV-style registration, and the deploy wrapper then misreported the successful execute response because it was empty.


### 2026-10-20T19:24:01Z - Decision

Decision: The runtime template and deploy control now model the A-record service-discovery contract explicitly.

Rationale: A-record registry bindings provide only RegistryArn; regression coverage rejects container fields and accepts empty successful mutation responses.


### 2026-10-20T19:25:00Z - Commit recorded

Commit: `28b9fcd8a18bab342c0160943d5460b8f60d80db`

Message: fix(deploy): align service discovery binding

Summary: Removed SRV-only fields from the A-record ECS registry binding and made successful empty AWS mutation responses valid, with regression coverage.

ADR impact: No new ADR; corrects reusable deployment-control interpretation.


### 2026-10-20T19:46:08Z - Issue

Raised: The corrected service failed to launch because the private CloudWatch Logs endpoint policy denied CreateLogStream.

Resolution: The endpoint policy appended log-stream syntax to LogGroup.Arn, producing an ARN shape that did not match the actual log stream resource.


### 2026-10-20T19:46:08Z - Decision

Decision: CloudWatch Logs endpoint policies must use an explicitly constructed log-stream ARN, tested against the endpoint block.

Rationale: The shared foundation policy now uses partition, region, account, log-group name, and log-stream wildcard directly; the task role policy remains separate.


### 2026-10-20T19:47:04Z - Commit recorded

Commit: `56a7952d874c094bb0dfcabb3c104bacfb32b87b`

Message: fix(deploy): permit logs endpoint streams

Summary: Corrected the private Logs endpoint policy to allow exact log-stream ARNs and added a focused foundation policy regression test.

ADR impact: No new ADR; corrects reusable deployment-control interpretation.


### 2026-10-20T19:58:27Z - Issue

Raised: After correcting the Logs endpoint policy, task startup still failed because the task execution role had its own malformed log-stream ARN.

Resolution: The endpoint and identity policies are evaluated independently; both must match the exact log-stream resource.


### 2026-10-20T19:58:27Z - Decision

Decision: Both endpoint and task execution-role logging permissions now use the same exact log-stream ARN contract.

Rationale: The regression requires two exact policy occurrences and rejects the malformed LogGroup.Arn-derived stream expression everywhere in the foundation template.


### 2026-10-20T19:59:20Z - Commit recorded

Commit: `4ddad06f033d6eac10a48ade42f0d72e9c3e7b89`

Message: fix(deploy): allow task log streams

Summary: Corrected the task execution-role CloudWatch Logs ARN to match the endpoint policy and strengthened the shared foundation regression.

ADR impact: No new ADR; corrects reusable deployment-control interpretation.


### 2026-10-20T20:20:17Z - Decision

Decision: Private immutable image pull also requires object-store layer retrieval, not only registry endpoints.

Rationale: Declare and enforce TCP/443 egress to the provider-managed object-store prefix list for both workload and verifier security groups; broad internet egress remains prohibited.


### 2026-10-20T20:32:24Z - Decision

Decision: The ECS task definition overrode the image runtime identity with a nonexistent node account.

Rationale: Preserve the distroless image-declared nonroot account; regression checks reject all task-definition User overrides for this immutable core image.


### 2026-10-20T20:40:28Z - Decision

Decision: The running container logged successful server startup, but ECS health checks invoked node through PATH, which distroless does not provide.

Rationale: Bind the health check to the image-declared /nodejs/bin/node executable and reject PATH-dependent health check commands in target controls.


### 2026-10-20T20:55:36Z - Decision

Decision: The corrected readiness command still used CMD-SHELL, but the distroless image contains no shell.

Rationale: Use ECS CMD form with the image-declared Node binary and arguments as separate tokens; static controls reject CMD-SHELL for the core distroless image.


### 2026-10-20T21:12:11Z - Decision

Decision: The private verifier inherited the distroless image Node entrypoint but duplicated node in its ECS Command, which made Node resolve /app/node as a script.

Rationale: Verifier commands must pass only Node arguments to the image-declared entrypoint; target controls reject duplicated node command tokens.


### 2026-10-20T21:15:49Z - Decision

Decision: The kanbien-core-platform bootstrap runtime deployed from the qualified immutable digest and its private verifier accepted the expected release identity.

Rationale: Live evidence: ECS rollout completed with one healthy task; verifier reported runtime-digest-and-private-verifier-accepted after the verifier-only task-definition update.


### 2026-10-20T22:10:46Z - Commit recorded

Commit: `832e709a`

Message: feat(deploy): govern core platform release updates

Summary: Recorded accepted release A; implemented update and restoration controls, cross-component release checks, and authoritative release workflows. Live B-to-A rehearsal remains gated on cost-waiver renewal and GitHub Environment approval.

ADR impact: ADR not required: bounded release-control governance under existing deployment architecture.


### 2026-10-20T22:14:04Z - Decision

Decision: Promoted governed core-platform release controls to origin/main

Rationale: The isolated integration worktree at 8ed5c337 passed the release-control and metadata checks; origin/main was verified at that exact commit after a normal fast-forward push. The live B-to-A rehearsal remains blocked only by renewed cost-waiver authority and GitHub Environment approval.


### 2026-10-20T22:19:51Z - Commit recorded

Commit: `2d13367c`

Message: chore(core-server): label bootstrap release

Summary: Prepared harmless Release B by changing only the private bootstrap app display label. Declared source and dependency checks passed; the real image smoke will be rebuilt against this exact source revision before publication.

ADR impact: ADR not required: bounded rehearsal-only source metadata change under the accepted release workflow.


### 2026-10-20T22:22:10Z - Decision

Decision: Qualified Release B locally

Rationale: The exact committed B revision ab80e2e1 passed runnable-program, dependency-boundary, release-contract, and real Docker liveness, readiness, and release-identity smoke checks. Publication remains a separate protected workflow and no AWS target mutation has occurred.


### 2026-10-21T08:40:59Z - Context hygiene

Summary: Recorded the approved short-lived cost-control waiver as target-local evidence and made it an executable pre-mutation gate; generic validation now rejects expired waivers.

Durable evidence: Durable evidence is in foundation/evidence/target-cost-allocation-tag.yml, the fixed target cost-condition wrapper, static declaration test, and AWS release workflow.


### 2026-10-21T08:43:38Z - Commit recorded

Commit: `2000f119`

Message: fix(deploy): enforce core-platform cost waiver gate

Summary: Recorded the approved expiring cost waiver as target-local evidence and enforced its status and expiry before every core-platform runtime change-set creation or execution.

ADR impact: No ADR: this implements the existing release-control policy.


### 2026-10-21T08:53:59Z - Issue

Raised: AWS omitted ChangeSetType from a reviewed existing-stack UPDATE change set.

Resolution: The deployment control now accepts that documented omission only with independent healthy-stack proof; smoke tests reject CREATE and non-stable lifecycle states.


### 2026-10-21T08:54:40Z - Commit recorded

Commit: `d2762553`

Message: fix(deploy): accept proven AWS update change sets

Summary: Accepted an omitted AWS ChangeSetType only for independently proven healthy existing stacks; the change remains bounded to task-definition and service updates.

ADR impact: No ADR: this corrects adapter handling under the existing release-control architecture.


### 2026-10-21T09:19:42Z - Issue

Raised: A terminally interrupted restoration command could cause an agent to launch a second private verifier task despite the first verifier having already accepted.

Resolution: The verifier now reuses only current-deployment completed evidence with a successful exit and safe acceptance log; otherwise it blocks. The rehearsal evidence records the incident and remediation.


### 2026-10-21T09:19:42Z - Decision

Decision: Reconciled Release B rehearsal evidence with restored accepted Release A.

Rationale: B remains a verified rehearsal candidate, while the accepted-release record names A's actual restored runtime and verifier task definitions; the static declaration gate checks the link.


### 2026-10-21T09:19:42Z - Context hygiene

Summary: Release B publication run 39571727355 qualified digest sha256:721466…224ec2, deployed and privately verified. The target was restored to accepted A digest sha256:0992b…5d5d5 and private verification accepted.

Durable evidence: Authoritative target evidence: bootstrap-runtime/accepted-release.yml and rehearsals/release-b-to-a-2026-10-21.yml; reusable verifier rule in verify-candidate and AWS workflow.


### 2026-10-21T09:22:03Z - Commit recorded

Commit: `3fcc0180`

Message: fix(deploy): reuse completed verifier evidence

Summary: Recorded the successful B-to-A rehearsal, reconciled the live accepted baseline, and made repeated private verification reuse current-deployment acceptance evidence instead of launching another task.

ADR impact: No ADR: this strengthens the existing governed release-verification control.


### 2026-10-21T11:32:07Z - Context hygiene

Summary: Created a deployment placement-and-naming standard, proposed-path validator, and migration plan; no active paths or cloud state changed.

Durable evidence: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md and .agentic/04.deploy/standards/deployment-artifact-placement-and-naming.md


### 2026-10-21T11:32:07Z - Decision

Decision: Adopt placement-before-creation governance

Rationale: Future deployment artifacts must choose infra, agentic, or scripts ownership; name their lifecycle phase and clear purpose; validate new canonical proposed paths before addition or move. No ADR is needed yet because this sets a governed migration direction without changing the durable active namespace.


### 2026-10-21T11:34:39Z - Commit recorded

Commit: `b10fc32f`

Message: feat(deploy): govern artifact placement and naming

Summary: Added the deployment artifact placement-and-naming standard, proposed-path validator with regression proof, lifecycle ownership linkage, and the governed ordered-layout migration plan. No active paths or provider state changed.

ADR impact: No ADR: the commit establishes a migration standard and plan, but does not change the active durable namespace or compatibility promise.


### 2026-10-21T11:47:10Z - Decision

Decision: Adopt ordered deployment placement and naming migration

Rationale: The approved migration makes target declarations scanable in lifecycle order. Batch 2 moved only active kanbien-core-platform target declarations to 00-target, 10-foundation, 20-scopes, 30-provider-realization/aws, and 40-package-custody; all active consumers, fixtures, GitHub metadata, and generated recognition sources now use the canonical locations. Old paths have no active aliases or consumers.


### 2026-10-21T11:47:10Z - Context hygiene

Summary: Batch 2 target declaration migration verification

Durable evidence: Durable migration authority: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md. Validation passed: target declaration, package custody, and release contract smoke suites; all nine path-migration checks; generated recognition-source refresh and validation; staged metadata check. No cloud or GitHub mutation occurred. Next planned batch: AWS target workflow migration after consumer review.


### 2026-10-21T11:48:26Z - Commit recorded

Commit: `d5cb0c54`

Message: refactor(deploy): order core platform target declarations

Summary: Completed migration batch 2: canonical target declaration hierarchy, updated active consumers and fixtures, refreshed recognition sources, and passed declaration, package-custody, release-control, metadata, migration, and repository commit gates. No cloud or GitHub state changed.

ADR impact: covered by session ADR disposition


### 2026-10-21T11:51:37Z - Decision

Decision: Keep one AWS release workflow while making lifecycle sections explicit

Rationale: The AWS bootstrap-runtime procedure is one coherent release route, so splitting it would duplicate operational authority. It now lives at the planned target-and-scope deploy path and explicitly separates preconditions, 50-deploy update, 60-run verification, and 60-run restoration.


### 2026-10-21T11:51:37Z - Context hygiene

Summary: Batch 3 AWS workflow migration verification

Durable evidence: Durable migration authority: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md. Moved the one AWS workflow only; active consumers and generated recognition sources now use its lifecycle-first target/scope path. Path-migration checker, target declaration, package custody, release-control, and migration-helper smoke tests passed. No AWS or GitHub mutation occurred.


### 2026-10-21T11:52:32Z - Commit recorded

Commit: `5240b9a0`

Message: refactor(deploy): route core AWS workflow by lifecycle

Summary: Completed migration batch 3: rehomed the single AWS bootstrap-runtime release workflow to the lifecycle-first target/scope route, clarified deploy, verification, and restoration sections, updated consumers and generated recognition sources, and passed required metadata, path, target, package, release, and helper-smoke gates. No cloud or GitHub state changed.

ADR impact: covered by session ADR disposition


### 2026-10-21T11:55:24Z - Decision

Decision: Move reusable target-alignment authority without creating empty schema artifacts

Rationale: The generic target-alignment workflow and standard now live in 00-target-alignment with names that say what they do. They remain singular reusable authority. The canonical layout's alignment schema is intentionally deferred because no such contract schema currently exists; creating one without a real consumer would create false governance.


### 2026-10-21T11:55:25Z - Context hygiene

Summary: Batch 4 generic target-alignment migration verification

Durable evidence: Durable migration authority: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md. Both reusable alignment artifacts moved to lifecycle-first clear-action paths; declaration coverage, implementation-plan metadata, and script README consumers were updated. Generated recognition sources, both path-migration checks, metadata, and migration-helper smoke passed. No provider mutation occurred.


### 2026-10-21T11:56:22Z - Commit recorded

Commit: `ab738224`

Message: refactor(deploy): clarify target alignment harness

Summary: Completed migration batch 4: moved reusable target-alignment workflow and standard into lifecycle-first clear-action paths, updated active consumers and generated recognition sources, passed both migration checks and required commit gates, and deliberately deferred a nonexistent alignment schema. No cloud or GitHub state changed.

ADR impact: covered by session ADR disposition


### 2026-10-21T11:58:51Z - Issue

Raised: Generic harness migration ADR was missing before the first active generic move

Resolution: Resolution: added ADR 0037 to make the lifecycle-first placement decision explicit, record the prior target-alignment move as a no-cloud, no-public-compatibility corrective case, and govern all remaining generic-harness moves. Runnable-program migration remains paused until this ADR is committed.


### 2026-10-21T11:58:51Z - Decision

Decision: Adopt lifecycle-first deployment authority paths

Rationale: ADR 0037 establishes the durable folder and naming rule: folders say when or where, filenames say what, and target/scope says what is affected. Generic authority stays singular; provider workflows and scripts remain lifecycle-first with binding where necessary.


### 2026-10-21T11:59:54Z - Commit recorded

Commit: `ee8d5746`

Message: docs(deploy): record lifecycle-first path decision

Summary: Corrected the migration governance gap with ADR 0037. It records the lifecycle-first authority-path decision, the no-cloud corrective disposition for the earlier generic move, and the rule governing remaining generic migrations. Runnable-program migration may now continue under this ADR.

ADR impact: covered by session ADR disposition


### 2026-10-21T12:05:24Z - Decision

Decision: Keep runnable-program contract material with the build phase

Rationale: The runnable workflow, standard, schema, template, and guide are one build capability: they prove a program's dependency boundary and command before package construction. They now live together under 20-build; package publication and deploy controls remain separate.


### 2026-10-21T12:05:25Z - Context hygiene

Summary: Runnable-program build-capability migration verification

Durable evidence: Durable migration authority: ADR 0037 and .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md. Moved five runnable-program authority artifacts into 20-build and updated all active consumers. Passed runnable-program and core dependency-boundary smoke suites, five path-migration checks, generated recognition-source validation, metadata, and migration-helper smoke. No provider action occurred.


### 2026-10-21T12:06:20Z - Commit recorded

Commit: `ac504bff`

Message: refactor(deploy): group runnable program build controls

Summary: Completed the runnable-program migration: workflow, standard, schema, template, and guide now sit under 20-build with all consumers updated. Passed runnable-program and core dependency-boundary smoke suites, five migration checks, generated recognition-source validation, metadata, and commit gates. No cloud or GitHub action occurred.

ADR impact: covered by session ADR disposition


### 2026-10-21T12:09:18Z - Decision

Decision: Keep package custody with the package phase

Rationale: The package workflow, standard, receipt schema, and guide now live under 40-package. They govern immutable package qualification and publication only; target selection, deployment, verification, and restoration remain later target-bound controls.


### 2026-10-21T12:09:18Z - Context hygiene

Summary: Package-custody migration verification

Durable evidence: Moved four package-custody authority artifacts into 40-package, updated active target pipeline and declaration checker consumers, refreshed recognition sources, and passed package-custody receipt, target package workflow, target declaration, four path-migration, and metadata checks. No provider action occurred.


### 2026-10-21T12:10:09Z - Commit recorded

Commit: `66e5cb57`

Message: refactor(deploy): group package custody controls

Summary: Completed package-custody migration: workflow, standard, receipt schema, and guide now sit under 40-package with target pipeline and checker consumers updated. Passed package receipt, package workflow, target declaration, migration, generated-index, metadata, and commit gates. No cloud or GitHub action occurred.

ADR impact: covered by session ADR disposition


### 2026-10-21T14:54:40Z - Context hygiene

Summary: The proven core bootstrap route is active and has normal health, private verification, immutable update, and B-to-A restoration evidence; it has not yet exercised deliberate live health failure, ECS unhealthy-task replacement, or automatic health-triggered rollback. The next package is a reusable health/failure/recovery contract before persistence.

Durable evidence: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md; .agentic/04.deploy/plans/execution/kanbien-core-platform-bootstrap.md; docs/education/teaching-notes/0003-packaging-and-deployment-learning-handbook.md; infra/04.deploy/03.product/targets/kanbien-core-platform/


### 2026-10-21T14:57:37Z - Commit recorded

Commit: `5c29a0a3a2c81f7b3b70fa155f4b62f8449bc8fc`

Message: docs(deploy): record proven core release route

Summary: Activated the proven core route metadata, documented the normal health/update/restoration evidence and its deliberate-failure proof boundary, and updated the generic plan and teaching handbook before the reusable health/recovery package.

ADR impact: No ADR: this records and routes existing architecture without changing the durable deployment architecture.


### 2026-10-21T15:13:38Z - Decision

Decision: Implemented the reusable health, failure, and recovery declaration capability before persistence. The core bootstrap scope is its first fixture; local/package proof is passed and the unperformed live fault/replacement rehearsal is explicitly deferred with ownership and review boundary.

Rationale: .agentic/04.deploy/plans/implementation/health-failure-and-recovery-declaration.md and .agentic/04.deploy/60-run/ now govern the reusable requirement; scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/ enforces it; the core target/release checks invoke it.


### 2026-10-21T15:35:35Z - Decision

Decision: Goal-authorized bounded live health/recovery rehearsal starts by committing the reusable health/failure/recovery declaration capability. The live exercise must prove final accepted immutable release health and private verification, and stops on identity, permission, cost, alignment, uncertainty, or wider-impact risk.

Rationale: Goal objective in this chat; .agentic/04.deploy/plans/implementation/health-failure-and-recovery-declaration.md; .agentic/04.deploy/60-run/.


### 2026-10-21T15:35:35Z - Context hygiene

Summary: The reusable health/failure/recovery package is implemented locally and has passed its validator, core declaration/release route regressions, package custody check, platform-server check, placement, metadata, and diff checks. It is not yet committed; a generated Python cache was removed.

Durable evidence: .agentic/04.deploy/60-run/; scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/; infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/.


### 2026-10-21T15:37:01Z - Commit recorded

Commit: `e559c8cee3b434978fd7abb8cb9f8d414f47cfbc`

Message: feat(deploy): require declared health recovery

Summary: Added reusable Run-stage health/failure/recovery declarations and validation, wired them into product, target alignment, and release controls, and recorded the core scope's truthful live-recovery proof boundary.

ADR impact: No ADR: this implements the existing lifecycle-first placement decision and documented implementation packet.


### 2026-10-21T15:52:15Z - Decision

Decision: Adopt controlled accepted-task replacement rehearsal

Rationale: The fixed 60-run command validates the accepted baseline, target alignment and active cost exception; with --execute it stops only the one accepted task, proves same-definition ECS replacement, and demands post-stop private verification. It does not claim readiness-detector or circuit-breaker proof.


### 2026-10-21T15:52:15Z - Context hygiene

Summary: Current rehearsal control requires a fresh verifier boundary and does not mutate image, task definition, service configuration, network or IAM.

Durable evidence: AWS-specific workflow: .agentic/aws/60-run/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/rehearse-accepted-workload-replacement.md; command: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.sh


### 2026-10-21T15:54:02Z - Commit recorded

Commit: `585bd3456cb85d95b24b85b862a3f5e7d3e9b3bb`

Message: feat(aws): rehearse accepted workload replacement

Summary: Added a fixed, target-bound 60-run control that proves ECS replaces one deliberately stopped accepted task and requires private verifier evidence newer than the stop boundary. Static declaration, release, placement, metadata, and target-control checks passed.

ADR impact: No ADR: this extends the existing lifecycle-first release and recovery control.


### 2026-10-21T16:02:45Z - Issue

Raised: Controlled replacement command returned no terminal report despite completing AWS actions

Resolution: Safe AWS inspection proved the original accepted task stopped at 15:55:42Z, ECS started and stabilised a healthy replacement at 15:55:55Z, and a fresh verifier completed successfully at 15:56:42Z. The outcome is recorded from provider facts; do not repeat the stop action.


### 2026-10-21T16:02:45Z - Decision

Decision: Accept live ECS replacement evidence with explicit proof boundary

Rationale: The bootstrap runtime now has passed live workload-recovery evidence. It proves ECS replacement of a deliberately stopped accepted dependency-free task and fresh private verification; it does not claim application-readiness-failure detection, circuit-breaker rollback, or dependency-bearing recovery.


### 2026-10-21T16:02:45Z - Context hygiene

Summary: Live target final state: one healthy replacement task on task definition :10 and digest sha256:0992…d5d5d5; verifier exited 0 with KANBIEN_CORE_RELEASE_VERIFIED.

Durable evidence: Evidence: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/rehearsals/accepted-workload-replacement-2026-10-21.yml


### 2026-10-21T16:03:59Z - Commit recorded

Commit: `2a58ab882c12c7210e30d272721745da3adcaea2`

Message: docs(deploy): record workload recovery rehearsal

Summary: Recorded the live controlled-stop ECS replacement outcome, advanced the scope proof to passed, required passed proof evidence to exist, taught the remaining proof boundary, and validated both restoration and replacement evidence against the accepted release.

ADR impact: No ADR: this is evidence-driven completion of the existing health/recovery design.


### 2026-10-21T16:05:12Z - Decision

Decision: Complete bounded live workload recovery rehearsal

Rationale: Final audit confirmed account 337159794548, active service desired/running 1, completed rollout on task definition kanbien-core-platform-bootstrap-runtime:10, healthy /readyz-backed container digest sha256:0992b48fdd66bb53c08d621e871b2e8975f40b8e6bbaa62816803f755d55d5d5, and fresh verifier exit 0 with KANBIEN_CORE_RELEASE_VERIFIED. Proof remains bounded: readiness-failure and circuit-breaker rollback were not rehearsed.


### 2026-10-22T20:29:18Z - Issue

Raised: Budget provisioning change-set initially rolled back

Resolution: The Foundation CostAlertEmail parameter was blank; the new bounded provisioning route now requires an operation-only alert address, recognises stable rollback completion, and verifies AWS monetary values numerically.


### 2026-10-22T20:29:19Z - Decision

Decision: Select PostgreSQL as the first kanbien-core-platform persistence reference

Rationale: The existing provider-neutral persistence contracts and AWS PostgreSQL adapter can be composed through a new isolated target scope; legacy staging persistence is not inherited.


### 2026-10-22T20:29:19Z - Context hygiene

Summary: Accepted bootstrap evidence remains valid; the foundation now has a verified USD 100 monthly target-filtered budget and the normal cost gate passes.

Durable evidence: Budget declaration/evidence: infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/; governed provisioner: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/; live AWS evidence checked 2026-10-22T20:21:54Z.


### 2026-10-22T20:29:20Z - ADR disposition

ADR needed: no

Reason: The budget bootstrap route is a bounded operational control under the existing deployment architecture, not a new durable architecture decision.


### 2026-10-22T20:33:24Z - Commit summary

Commit: Add workload-aware recovery and target budget controls

Summary: Adds typed workload health and recovery validation, provider-evidence freshness checks, release rehearsal controls, and a governed 00 target-budget provisioning path with recorded live budget evidence. PostgreSQL is selected as the first future persistence reference; no persistence infrastructure has been created.

ADR impact: covered by session ADR disposition


### 2026-10-22T20:39:44Z - Commit recorded

Commit: `4021fbf2`

Message: feat(deploy): govern workload recovery and target budget

Summary: Adds workload-aware health and recovery contracts, active-workload validation, evidence freshness enforcement, bounded rehearsal controls, and verified 00 target-budget governance. PostgreSQL is selected as the next persistence reference; no persistence infrastructure is created.

ADR impact: not-needed: bounded operational controls follow existing deployment architecture


### 2026-10-22T22:20:13Z - Decision

Decision: User authorised commit, merge to main, and remote push of the completed secret-management work.

Rationale: Preserve the existing recovery commits and current main history through governed non-rewriting refresh; no cloud execution or credential access.


### 2026-10-22T22:20:14Z - Issue

Raised: Closed the secret-declaration review findings.

Resolution: Workload-aware failures and startup-only rotation are enforced; unsafe values beneath non-string keys are scanned; malformed access classes return structured results; shared runtime server/worker credentials pass without permitting migration/admin access or mixed failure families.


### 2026-10-22T22:20:14Z - Context hygiene

Summary: Carry forward the portable secret contract and executable inventory enforcement, with synthetic regression evidence.

Durable evidence: Four regression suites, actual target/release gates, metadata and whitespace checks passed. Provider references, IAM, target isolation, secret delivery and live rotation remain PostgreSQL work; no new CI result or cloud proof is claimed.


### 2026-10-22T22:20:14Z - ADR disposition

ADR needed: yes

ADR path: docs/04.deploy/adrs/0041-select-postgresql-for-core-platform-persistence-proof.md

Reason: Record the PostgreSQL selection already stated in the programme for this target; staging ADR 0033 does not cover it. Resource design and live authority remain deferred.


### 2026-10-22T22:20:14Z - Commit summary

Commit: feat(deploy): govern workload secret dependencies

Summary: Add portable secret declarations, workload-aware validation and inventory enforcement; include corrective regressions and PostgreSQL preparation guidance.

ADR impact: ADR 0041 records the existing PostgreSQL reference selection.


### 2026-10-22T22:22:12Z - Commit recorded

Commit: `6ada7e35`

Message: feat(deploy): govern workload secret dependencies

Summary: Implemented portable secret declarations, inventory enforcement and type-aware failure contracts; closed all reviewed validator defects with synthetic regressions. Required commit and recognition gates passed; included PostgreSQL preparation guidance without provider execution.

ADR impact: ADR 0041 records the PostgreSQL reference selection for kanbien-core-platform.


### 2026-10-22T22:25:56Z - Main refresh conflict recorded

Path: `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`

Type: `generated-artifact-conflict`

Mode: deterministic

Action: Regenerated recognition outputs from combined source metadata and retained authored changes from both branches. Trimmed four empty metadata-field trailing spaces in the incoming Oct22 session log for staged whitespace validation.


### 2026-10-22T22:26:46Z - Commit recorded

Commit: `bca7af432d405f666b281ad990defe8a69205503`

Message: Merge main through governed refresh rehearsal

Summary: Applied the tested non-rewriting refresh from main. Regenerated the sole conflicting generated artifact index, recorded its audit, and retained both branches authored changes. Four regression suites, recognition validation and repository commit gates passed in preflight; target and release gates passed again after apply. No stash or cloud action used.

ADR impact: No new architectural decision; refresh preserves ADR0041 and main governance.


### 2026-10-23T16:08:09Z - Decision

Decision: Adopt reusable persistence-safety declaration controls

Rationale: Before defining the PostgreSQL scope, add reusable lifecycle ownership, workload-aware health/recovery, server-mediated verifier, migration, recovery, idempotency/cleanup, and credential lifecycle controls; distinguish local declaration checks from provider and live proof.


### 2026-10-23T16:08:10Z - Issue

Raised: Malformed migration credential cross-check could raise TypeError

Resolution: Validator now cross-checks only structurally valid credential entries; null, boolean, and numeric authorised_workloads fixtures produce structured failures.


### 2026-10-23T16:08:10Z - Context hygiene

Summary: Implemented reusable persistence-safety harness controls and corrective credential lifecycle pass; live PostgreSQL/AWS work remains unstarted.

Durable evidence: .agentic/04.deploy/00-target-alignment, .agentic/04.deploy/60-run, scripts/04.deploy/lifecycle, implementation plan, teaching handbook, and focused smoke/gate output.


### 2026-10-23T16:12:47Z - Commit recorded

Commit: `13fe5145`

Message: feat(deploy): govern persistence safety declarations

Summary: Adds reusable scope lifecycle, workload ownership, health/recovery, migration safety and credential lifecycle declaration controls; corrects secret-validation fail-closed behaviour; and records PostgreSQL persistence prerequisites.

ADR impact: No new ADR; extends the existing deployment implementation plan and generic harness controls.


### 2026-10-23T18:23:13Z - Decision

Decision: Establish a provider-neutral persistence-capable server composition before selecting PostgreSQL.

Rationale: The new target-composition factory injects an abstract persistence runtime and is proved with a local fake. It preserves release verification, separates process liveness from dependency readiness, exposes only controlled server-mediated acceptance outcomes, and closes the injected runtime during shutdown. It does not create a `core-server-persistence` scope, choose an adapter, read a secret, build an image, or change a target.


### 2026-10-23T18:23:13Z - Context hygiene

Summary: Local composition proof passed for both unavailable and ready dependency states.

Durable evidence: `infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts` and `scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/`. The remaining next step is reviewed PostgreSQL adapter selection and composition; no cloud or target mutation occurred.


### 2026-10-23T18:38:58Z - Decision

Decision: Authorize end-to-end core-server-persistence execution

Rationale: The user supplied standing authorization for the bounded kanbien-core-platform persistence slice: repository and target changes, AWS provisioning, publication, deployment, live recovery proofs, commits, integration with main, and push. The work remains limited to this target, the USD 100 monthly ceiling, and existing protected gates.


### 2026-10-23T18:38:58Z - Context hygiene

Summary: Persistence slice baseline established

Durable evidence: Fresh AWS identity is account 337159794548 in eu-west-1; bootstrap-runtime is ACTIVE with desired/running one on task definition revision 10; no target RDS instance or Secrets Manager secret exists; target budget kanbien-core-platform-monthly is USD 100 filtered by Target=kanbien-core-platform with USD 0.7839062758 estimated spend through 2026-10-23. Local diagnostics, lifecycle inventory, health/recovery, secret-dependency, target declaration, release contract, and persistence-composition checks passed.


### 2026-10-23T18:40:35Z - Commit recorded

Commit: `39f8bbc4d07a044cd5285836f4ca0842d16d85c9`

Message: feat(deploy): add persistence composition controls

Summary: Adds reusable persistence diagnostic enforcement, lifecycle and secret/recovery controls, and a fake-backed provider-neutral persistence-capable core-server composition. No PostgreSQL resource, secret, adapter binding, image, or target mutation is included.

ADR impact: No ADR: this checkpoint applies the already-recorded PostgreSQL selection without selecting a provider binding or changing deployed architecture.


### 2026-10-23T18:57:57Z - Commit recorded

Commit: `9149d30d`

Message: feat(deploy): add persistence candidate programs

Summary: Added the candidate server, server-mediated verifier, migration executable, PostgreSQL binding, migration lock, image definition, and local composition checks.

ADR impact: none


### 2026-10-23T19:02:47Z - Commit recorded

Commit: `f6cd5fbe`

Message: feat(deploy): declare persistence candidate scope

Summary: Registered core-server-persistence as a validated candidate successor with separate runtime and migration credentials, a server-mediated verifier boundary, diagnostics, recovery declarations, and a local image-build command.

ADR impact: none


### 2026-10-23T19:22:16Z - Commit recorded

Commit: `bbf19a21`

Message: feat(deploy): add hosted persistence image qualification

Summary: Added the protected-main GitHub Actions route for real Docker qualification, immutable persistence candidate publication, and ECR scan enforcement; corrected the image dependency closure.

ADR impact: none


### 2026-10-23T19:36:23Z - Commit recorded

Commit: `b4abc8cd`

Message: feat(deploy): add persistence provider candidate controls

Summary: Added the private PostgreSQL candidate template, migration/runtime-principal contract, package closure checks, and OCI-child-manifest scan gate.

ADR impact: covered by session ADR disposition


### 2026-10-23T19:37:26Z - Commit recorded

Commit: `7ab8d070`

Message: feat(deploy): add persistence provider candidate controls

Summary: Rebased checkpoint: private PostgreSQL candidate template, migration/runtime-principal contract, package closure checks, and OCI-child-manifest scan gate.

ADR impact: covered by session ADR disposition


### 2026-10-23T19:44:52Z - Commit recorded

Commit: `d9262f46`

Message: test(deploy): qualify persistence image against tls postgres

Summary: Added the hosted disposable TLS PostgreSQL package qualification for migration, runtime DML, readiness, and runtime DDL denial.

ADR impact: covered by session ADR disposition


### 2026-10-23T19:47:16Z - Commit recorded

Commit: `c0815790`

Message: fix(deploy): complete postgres driver image closure

Summary: Added pg-int8 and a build-stage require check after hosted TLS package qualification exposed the missing transitive dependency.

ADR impact: covered by session ADR disposition


### 2026-10-23T19:52:09Z - Commit recorded

Commit: `6132d8af8aca00b876cab1b79403da4fd82410a6`

Message: fix(persistence): allow bounded migration statement timeout

Summary: Allows the declared bounded 240-second migration statement timeout while retaining one-minute connection and idle limits; adds acceptance and rejection regression coverage.

ADR impact: covered by session ADR disposition


### 2026-10-23T20:07:58Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): govern persistence image qualification

Summary: Repairs the real TLS PostgreSQL package smoke and adds an enforced persistence-candidate package-custody route with delivery-access proof, scan, SBOM, provenance, and receipt.

ADR impact: covered by session ADR disposition


### 2026-10-23T20:08:12Z - Commit recorded

Commit: `52601cd98c8dacdecfafc78bd09328d24c24c3a8`

Message: fix(deploy): govern persistence image qualification

Summary: Repairs the real TLS PostgreSQL package smoke and adds an enforced persistence-candidate package-custody route with delivery-access proof, scan, SBOM, provenance, and receipt.

ADR impact: covered by session ADR disposition


### 2026-10-23T20:27:30Z - Commit recorded

Commit: `d8ff3f8c0f5fdf6421e0245391ad5c74135447d5`

Message: feat(deploy): govern persistence candidate creation

Summary: Added a fixed, target-bound persistence candidate route: live preflight, reviewable CloudFormation creation, one-shot migration, and server-mediated verification; local gates and live read-only preflight pass.

ADR impact: covered by session ADR disposition


### 2026-10-23T20:28:31Z - Commit recorded

Commit: `9225b536adec6a9273d37fa59413b545eb524681`

Message: fix(deploy): wire persistence inventory gate

Summary: Corrected the candidate creation route so its automatic active-scope inventory gate receives the canonical scope-root path; the focused gate and target-control smoke pass.

ADR impact: covered by session ADR disposition


### 2026-10-23T20:30:31Z - Commit recorded

Commit: `0645e298789fb7cfd3f36ecea06f496b7f5cf3c3`

Message: fix(deploy): reconcile empty aws acknowledgements

Summary: Updated the shared persistence AWS response decoder and regression suite so an empty successful CloudFormation acknowledgement is reconciled through its named operation instead of treated as a reason to retry.

ADR impact: covered by session ADR disposition


### 2026-10-23T20:47:24Z - Commit recorded

Commit: `f9baa91fc7afaf28c52e4cb3a42e0180f6efbb0c`

Message: fix(deploy): allow private persistence image layers

Summary: Captured the live candidate image-pull failure and added the managed S3 artifact prefix-list preflight, CloudFormation parameter, server/migration egress rules, and regression proof alongside existing ECR endpoint controls.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:15:53Z - Commit recorded

Commit: `6c6d9ecaa18706675a2348f1af0950c82e08aaf6`

Message: fix(deploy): govern failed persistence candidate retirement

Summary: Added a fixed failed-candidate retirement control, repaired target package metadata gating, and preserved final snapshot retention before retrying the persistence candidate.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:16:12Z - Commit recorded

Commit: `253b4eace9d59b80cf36d231fcf0517cbbfa4ea4`

Message: fix(deploy): govern failed persistence candidate retirement

Summary: Rebased task commit onto origin/main; adds the fixed failed-candidate retirement control, target package metadata repair, and regression coverage.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:16:33Z - Commit recorded

Commit: `253b4eacf463f2e3fd52f3c7f0a2ed6ce225bb39`

Message: fix(deploy): govern failed persistence candidate retirement

Summary: Corrected rebased task SHA: fixed failed-candidate retirement control, target package metadata repair, and regression coverage.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:39:37Z - Commit recorded

Commit: `284df87b8e02b84a5b72478002e94e46079ed7cd`

Message: fix(deploy): reconcile interrupted persistence migrations

Summary: Added a current-deployment, no-replay reconciliation route for an interrupted migration controller and regression coverage for identity and terminal-state refusal.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:39:47Z - Commit recorded

Commit: `cc866c67e8c76c1e1bdee3f8b68d1de38a6028b5`

Message: fix(deploy): reconcile interrupted persistence migrations

Summary: Rebased task commit adds the current-deployment, no-replay migration reconciliation control and its regression coverage.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:43:39Z - Commit recorded

Commit: `0259d4c09210ae45a4f1c6e13c6648bc9c5f5b53`

Message: fix(deploy): connect private persistence verifier

Summary: Added the explicit verifier-to-current-server egress rule and a no-replay verifier reconciliation route after the first verifier safely exposed the missing route.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:43:48Z - Commit recorded

Commit: `a1d6de9a7f97f0755864b72d53488c2602bc9160`

Message: fix(deploy): connect private persistence verifier

Summary: Rebased task commit adds explicit verifier-to-current-server egress and no-replay verifier reconciliation after the safe route failure.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:48:23Z - Commit recorded

Commit: `ae4ea090`

Message: fix(deploy): govern private verifier route updates

Summary: Adds a constrained reviewed CloudFormation UPDATE route allowing only the current verifier-to-server egress security-group rule, with focused smoke coverage.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:48:41Z - Commit recorded

Commit: `6cd61e15`

Message: fix(deploy): govern private verifier route updates

Summary: Rebased task commit: constrained reviewed CloudFormation UPDATE route allowing only the verifier-to-server egress security-group rule.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:51:55Z - Commit recorded

Commit: `c7a84aa0`

Message: fix(deploy): reconcile verifier route change sets

Summary: Makes the bounded verifier route correction reuse its deterministic change set and await CloudFormation review visibility rather than rejecting a normal propagation gap.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:52:03Z - Commit recorded

Commit: `94272a0d`

Message: fix(deploy): reconcile verifier route change sets

Summary: Rebased task commit: the fixed route control awaits the existing bounded change set becoming reviewable and never creates a duplicate.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:58:24Z - Commit recorded

Commit: `ea645943`

Message: feat(deploy): govern persistence server replacement

Summary: Adds a fixed target-scoped replacement rehearsal that records the old/new server task and requires a separate fresh private read proof.

ADR impact: covered by session ADR disposition


### 2026-10-23T21:58:32Z - Commit recorded

Commit: `74756f9b`

Message: feat(deploy): govern persistence server replacement

Summary: Rebased task commit: fixed target-scoped server replacement with a required subsequent read proof.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:00:46Z - Commit recorded

Commit: `d47f1fd2`

Message: fix(deploy): reconcile persistence replacements

Summary: Adds a no-replay reconciliation route for a replacement controller interrupted after it stopped the original task.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:00:55Z - Commit recorded

Commit: `b9f30372`

Message: fix(deploy): reconcile persistence replacements

Summary: Rebased task commit: reconciles only an exact stopped task with the governed replacement reason and a distinct healthy replacement.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:09:28Z - Commit recorded

Commit: `5dced535`

Message: feat(deploy): govern persistence release transitions

Summary: Adds a receipt-bound UPDATE/rollback route that permits only persistence ECS task-definition and service changes.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:24:21Z - Commit recorded

Commit: `dae6f542`

Message: feat(deploy): govern persistence recovery points

Summary: Adds a fixed target-bound encrypted recovery-point snapshot command with live service, database and budget checks.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:24:31Z - Commit recorded

Commit: `14f57f56`

Message: feat(deploy): govern persistence recovery points

Summary: Rebased task commit: fixed encrypted target recovery-point control.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:42:00Z - Commit recorded

Commit: `001014b6`

Message: govern isolated persistence restore proof

Summary: Added a qualified restore-verifier image entrypoint, isolated restored-database network surface, workload declarations, recovery rehearsal control, and shared-runtime-secret validation rule; local and Docker PostgreSQL/TLS checks pass.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:42:31Z - Commit recorded

Commit: `2772a57e`

Message: govern isolated persistence restore proof

Summary: Rebased onto current origin/main; restore-verifier task commit now resolves to 2772a57e.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:46:34Z - Commit recorded

Commit: `d424ec82`

Message: bound persistence restoration surface update

Summary: Added a restore-specific image parameter and change-set control that permits only new isolated restoration verifier resources; it cannot modify the live ECS service or existing task definitions.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:46:42Z - Commit recorded

Commit: `f8a320c0`

Message: bound persistence restoration surface update

Summary: Rebased onto current main; exact bounded restoration-surface task commit is f8a320c0.

ADR impact: covered by session ADR disposition


### 2026-10-23T22:47:20Z - Commit recorded

Commit: `140e42c3`

Message: govern restoration surface command wrapper

Summary: Added the required artifact header after the governed runner correctly rejected the wrapper.

ADR impact: covered by session ADR disposition


### 2026-10-24T09:01:27Z - Issue

Raised: Corrected isolated restore verifier reconciliation

Resolution: Live restore check exposed two controller defects before acceptance: ECS task-definition fields are lower-case and list-tasks defaults to running tasks. The controller now parses the actual AWS response and searches running plus stopped tasks before submitting any verifier. Two read-only verifier attempts already exist for the current restored copy, so it will be cleaned up and repeated from the immutable snapshot after this correction is recorded.


### 2026-10-24T09:01:28Z - Context hygiene

Summary: Keep only the durable recovery evidence

Durable evidence: RDS restore kanbien-core-platform-persistence-restore-20261023 became available, passed the governed restore posture check, and the first verifier task 559dcbbd4be74a9893d62f0ecf4f5e1a exited 0. A controller defect submitted a second read-only verifier attempt because stopped tasks were omitted. The harness correction and smoke test are the durable source; raw AWS task output need not be retained.


### 2026-10-24T09:04:27Z - Commit recorded

Commit: `14798019`

Message: fix(deploy): reconcile stopped restore verifiers

Summary: Correct the isolated restore controller to validate AWS lower-case task-definition fields and reconcile stopped verifier tasks before submitting another; add focused regression coverage.

ADR impact: No ADR: this repairs an existing control's AWS response parsing and reconciliation behavior without changing the architecture.


### 2026-10-24T09:04:58Z - Commit summary

Commit: e3c7a09e

Summary: Rebased restore-controller task commit from 14798019 onto origin/main; current durable task SHA is e3c7a09e.

ADR impact: covered by session ADR disposition


### 2026-10-24T09:17:13Z - Issue

Raised: Bound restore verifier identity to database incarnation

Resolution: A fresh restore from the same snapshot correctly exposed that a snapshot-date-only ECS started-by value collides with historical tasks. The restore controller now derives a bounded identity from the restored RDS DbiResourceId, so only tasks for the current isolated database incarnation are reconciled.


### 2026-10-24T09:17:13Z - Context hygiene

Summary: Preserve recovery controller identity evidence

Durable evidence: Current restore DbiResourceId is db-7AQ3CU3PEWLSGTNPUMPKEFODM4. Earlier restore-verifier task history remains intentionally excluded by the corrected incarnation-bound started-by identity. The test proves task lookup includes stopped tasks and restore incarnations receive distinct identities.


### 2026-10-24T09:17:50Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): isolate restore verifier task identity

Summary: Derive the isolated restore verifier ECS identity from the restored database resource, preventing historical tasks from a prior restore of the same snapshot from blocking reconciliation.

ADR impact: No ADR: this is a bounded controller identity correction.


### 2026-10-24T09:50:40Z - Issue

Raised: Credential revocation terminated an idle PostgreSQL pool client and crashed the local server instead of leaving it live but not ready.

Resolution: The reusable PostgreSQL pool adapter now consumes idle-client provider errors without logging raw provider detail; the next readiness probe reports the governed state. Adapter, composition, TLS package, harness, target, and release gates passed.


### 2026-10-24T09:50:40Z - Context hygiene

Summary: The current packet adds governed runtime credential rotation/revocation operations, verifier health modes and package/live-controller coverage. The local Docker PostgreSQL/TLS proof initially exposed unhandled pg idle-client errors on revoke; the reusable adapter now handles that boundary and all relevant local gates pass.

Durable evidence: Durable source: core-server-persistence entrypoints, lifecycle controls, adapter connection test, package smoke; generated local evidence is not a release receipt.


### 2026-10-24T09:51:39Z - Commit recorded

Commit: `adc9c83655f4da156b785c506b8b70e58d608d25`

Message: feat(deploy): rehearse persistence credential lifecycle

Summary: Adds governed runtime credential rotation/revocation rehearsal, server health verification, migration operation controls, lower-case ECS verifier isolation parsing, local package proof, and reusable pg idle-client error handling. Adapter, composition, package, harness, target and release-contract gates passed locally.

ADR impact: No ADR: applies existing persistence lifecycle and recovery decisions.


### 2026-10-24T09:57:26Z - Issue

Raised: The persistence release transition omitted the required RestoreVerifierImageDigest CloudFormation parameter, so AWS rejected change-set creation before any update.

Resolution: Both clean-create and update controllers now bind the restoration verifier to the same qualified immutable persistence image digest as the server.


### 2026-10-24T09:58:17Z - Commit recorded

Commit: `aee8bad27be41aa90dfb627a20a42fb4464e5ef2`

Message: fix(deploy): bind persistence restore verifier digest

Summary: Corrects the clean-create and healthy-stack update release controls to provide the template-required RestoreVerifierImageDigest from the same qualified immutable candidate digest; Python compile and pre-commit gates passed.

ADR impact: No ADR: repairs an existing target-template/controller contract.


### 2026-10-24T10:27:48Z - Commit recorded

Commit: `--commit`

Message: 427847f6

Summary: --summary

ADR impact: Bound persistence observer commands and corrected verifier-role smoke-test boundary.


### 2026-10-24T10:28:16Z - Commit recorded

Commit: `427847f6`

Message: fix(deploy): bound persistence controller observations

Summary: Bound persistence observer commands and corrected verifier-role smoke-test boundary.

ADR impact: No ADR: bounded controller and regression correction.


### 2026-10-24T10:57:38Z - Commit recorded

Commit: `f3d89cd5`

Message: fix(deploy): bound credential recovery continuation

Summary: Adds a non-replaying recovery-secret boundary and bounded AWS observer handling for persistence lifecycle controllers.

ADR impact: No ADR: repairs governed continuation and observer behavior.


### 2026-10-24T11:27:11Z - Commit recorded

Commit: `f10d6cd2`

Message: feat: prove runtime postgres privilege live

Summary: Added a receipt-governed migration-task operation that verifies runtime DML succeeds and PostgreSQL rejects structural DDL in rolled-back transactions.

ADR impact: covered by session ADR disposition


### 2026-10-24T13:58:38Z - Commit recorded

Commit: `5942afe2`

Message: fix(deploy): fail closed on persistence revocation

Summary: Added fail-closed runtime-session termination evidence, bounded fresh restore naming, and target-bound acceptance evidence collection.

ADR impact: covered by session ADR disposition


### 2026-10-24T16:05:00Z - Commit recorded

Commit: `21d02a53`

Message: feat(deploy): retain persistence acceptance proofs

Summary: Record durable task-proof receipts, accepted persistence release evidence, and lifecycle promotion without relying on aged ECS task records.

ADR impact: No ADR: bounded evidence-retention and lifecycle-control completion within the approved PostgreSQL persistence slice.


### 2026-10-25T13:23:15Z - Issue

Raised: Corrected current release-reference hash mismatch before package qualification

Resolution: The immutable historical record had two trailing newlines while current-accepted-release.yml named the canonical one-newline rendering. The release-succession gate blocked safely before AWS/ECR actions. Preserved the history; updated only the current pointer to its actual retained SHA-256; validate-current and target smoke pass.


### 2026-10-25T13:23:15Z - Decision

Decision: Repair mutable release reference without rewriting accepted history

Rationale: Current release references must hash the exact immutable bytes they name. A pointer-only correction restores validation while preserving historical acceptance truth.


### 2026-10-25T13:23:15Z - Context hygiene

Summary: Workflow 40197069234 failed before AWS mutation at release-succession validation; actual history SHA is 91bbb624... and original current pointer incorrectly declared f26dec40...

Durable evidence: Exact proof root: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/. The next workflow must qualify and publish an immutable support image before retained-image compatibility can proceed.


### 2026-10-25T13:24:11Z - Commit recorded

Commit: `a7d45b7a`

Message: fix(deploy): reconcile current release reference

Summary: Corrected only the mutable current accepted-release pointer to hash the exact immutable history bytes; succession validation and target smoke now pass.

ADR impact: No ADR: this is an integrity-pointer correction under existing release-succession design.


### 2026-10-25T13:26:58Z - Issue

Raised: Fixed package source-closure copy of a nonexistent protobuf scope

Resolution: CI package build reached Docker assembly after every declaration/target/receipt gate passed, then failed before AWS mutation because Dockerfile copied node_modules/@protobufjs even though the lockfile provides unscoped protobufjs. Removed only that nonexistent copy. Local governed build reached the known Docker Desktop/WSL credential-helper failure before Docker could build; CI remains the package authority.


### 2026-10-25T13:26:59Z - Context hygiene

Summary: Workflow 40197461616 passed all repository gates, then Docker build failed at cp node_modules/@protobufjs/.; package closure now copies protobufjs unscoped. Local Docker is externally blocked at dockerfile frontend credential helper with WSL UtilAcceptVsock timeout.

Durable evidence: Next required evidence is a successful CI package workflow on the source-closure fix; no ECR image or AWS target resource changed in either failed workflow.


### 2026-10-25T13:27:35Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): correct persistence image closure

Summary: Removed the nonexistent @protobufjs copy from the persistence image source closure after CI caught it before any AWS or ECR mutation.

ADR impact: No ADR: narrow package assembly correction.


### 2026-10-25T13:30:03Z - Issue

Raised: Removed unnecessary unscoped OpenTelemetry closure copies

Resolution: The second hosted build reached the Docker payload closure and established that protobufjs, long and related packages are not installed for the selected OpenTelemetry exporter. The supported runtime closure is pg plus the @opentelemetry tree. A clean temporary copied closure loads pg, sdk-metrics and exporter-metrics-otlp-proto.


### 2026-10-25T13:30:03Z - Context hygiene

Summary: Workflow 40197714861 passed repository gates and failed before AWS/ECR action at unsupported unscoped OTel dependency copies. Current closure test passes using only pg dependencies plus node_modules/@opentelemetry.

Durable evidence: Dockerfile infra/04.deploy/03.product/image/core-server-persistence/Dockerfile now contains only actual installed runtime package copies. Hosted CI remains needed for end-to-end image smoke/publication.


### 2026-10-25T13:30:47Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): trim persistence image runtime closure

Summary: Removed nonexistent unscoped dependency copies; isolated runtime closure now loads actual pg and OpenTelemetry modules.

ADR impact: No ADR: package source-closure correction.


### 2026-10-25T13:50:13Z - Issue

Raised: Corrected observability collector delivery path

Resolution: The target template treated an OTLP HTTP URL as a CloudWatch exporter. AWS ADOT's supported application-metric route is OTLP to a task-local collector, then the awsemf exporter through the existing private Logs endpoint. Removed the unused monitoring endpoint design, narrowed collector task-role permissions to one EMF log stream, and require a target-owned SNS topic plus external confirmation before live acceptance.


### 2026-10-25T13:50:13Z - Issue

Raised: Classified absent named change sets as a reconciled lifecycle state

Resolution: CloudFormation can report ChangeSetNotFoundException without the generic phrases recognized by the provider adapter. The preparation adapter now maps only that explicit condition to aws-resource-missing; target-control regression proves it. A change-set must still be reviewed before creation or execution.


### 2026-10-25T13:50:13Z - Context hygiene

Summary: Actual private support image sha256:bc9080d4ed02ad422100bd31ef17b213012de27bbb5a7c75f6b14ef77847a166 contains the administration program. The retained image sha256:30ae014c800769d9929db265ada4efd06c4712ca2e48d73c7ba455e55b25b4e3 passed the governed disposable PostgreSQL/TLS compatibility qualifier with it. Current stack has no observability parameters or target-owned SNS topic; only a staging topic exists and must not be reused.

Durable evidence: Package provenance is GitHub Actions run 40197961821; local qualification is governed by scripts/04.deploy/lifecycle/40-package/qualify-retained-persistence-rollback-image/script.sh; current stack facts were read from CloudFormation in eu-west-1.


### 2026-10-25T13:52:02Z - Commit recorded

Commit: `f8a16e683911c6906ca834e45f48ee70025601f1`

Message: fix(deploy): correct observability delivery route

Summary: Corrected ADOT delivery to use EMF through the existing private Logs endpoint, declared target-owned notification binding, and classified named absent change sets safely; local target and observability gates pass.

ADR impact: covered by session ADR disposition


### 2026-10-25T14:04:31Z - Issue

Raised: Target-private collector custody was not yet an executable package route.

Resolution: Added a contract-pinned ADOT collector package workflow; it mirrors only the immutable public source into the existing target-private ECR repository, validates non-secret startup configuration, scan/SBOM/provenance, and emits a custody receipt before it can be selected by a deployment.


### 2026-10-25T14:04:31Z - Decision

Decision: Adopt target-private collector package custody.

Rationale: The collector remains a sidecar dependency, not a deployment authority: its protected manual GitHub workflow may qualify and publish one pinned digest only. The persistence deploy controller will remain blocked until that receipt and digest are supplied.


### 2026-10-25T14:04:32Z - Context hygiene

Summary: A public ADOT OCI index is pinned by contract and package-tested structurally; the target catalogue now routes the collector through protected private custody. Static checks pass; publication and live observability proof remain pending.

Durable evidence: Collector contract and config live under infra/04.deploy/03.product/image/core-server-persistence-observability-collector; workflow and guard live under .github/workflows and scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform.


### 2026-10-25T14:06:16Z - Commit recorded

Commit: `df2ca76296f4ccae7d5b752d7ae0725c1a689e07`

Message: feat(deploy): add private collector custody route

Summary: Added the target-private ADOT collector package contract, protected manual custody workflow, static guard and negative regression, plus target catalogue and declaration-gate routing. Local package, target, deployment-control, and retained-acceptance checks passed; publication and live observability proof remain pending.

ADR impact: covered by session ADR disposition


### 2026-10-25T14:08:13Z - Issue

Raised: The collector route was developed on a chat branch that diverged from newer accepted persistence work on local main.

Resolution: Resolved the integration by retaining main's newer accepted implementation for overlapping persistence controllers and entrypoints, preserving nonconflicting observability/collector custody artifacts, then rerunning collector, target, and deployment-control gates.


### 2026-10-25T14:08:13Z - Decision

Decision: Integrate collector custody on top of the accepted persistence baseline.

Rationale: Conflicting controller and runtime files take the newer main implementation; collector custody remains separately package-owned and its target gate verifies that it cannot be silently omitted.


### 2026-10-25T14:08:13Z - Context hygiene

Summary: The merge base was c884c321. Main contained newer accepted scope/recovery controls; the chat branch contained permissions and observability corrections plus collector custody. The final tree has no conflicts and targeted package, declaration, target, and deployment-control regressions pass.

Durable evidence: Durable details are in Git merge parents, collector custody artifacts, and this chat session log.


### 2026-10-25T14:09:06Z - Commit recorded

Commit: `0360770f7c82b090716c445dba31e7226b1de95a`

Message: Merge main into chat branch

Summary: Integrated the newer accepted persistence implementation from main with the collector custody route. Resolved only genuine overlaps by retaining main's newer controller/runtime implementation and reran collector, observability, target, and fixed deployment-controller checks successfully.

ADR impact: covered by session ADR disposition


### 2026-10-25T14:13:24Z - Issue

Raised: Collector package workflow mirrored the qualified image but its scan selector assumed an OCI index.

Resolution: ECR returned a valid single OCI manifest. Added a deterministic resolver that accepts either the published runnable manifest or exactly one amd64 child of an OCI index; it rejects ambiguous or malformed responses. The existing mirrored digest was read-only verified; no deployment occurred.


### 2026-10-25T14:13:24Z - Context hygiene

Summary: Collector run 40200948509 qualified startup, private mirror, and then failed only before scan acceptance due to manifest-shape selection. The target-private digest sha256:d0a012... is not accepted as custody evidence yet. Resolver tests and the actual ECR response prove the corrective selector.

Durable evidence: Workflow, resolver, and regression live in the collector package-custody directory; GitHub run 40200948509 remains the factual failed attempt.


### 2026-10-25T14:14:09Z - Commit recorded

Commit: `c15677c2b50a92b3d835050c374818d7e0a20a9a`

Message: fix(deploy): scan single-manifest collector images

Summary: Corrected the collector scan selector to resolve either a single OCI manifest or exactly one amd64 child of an OCI index. Regression coverage and a read-only check against the actual mirrored digest passed; the failed first workflow remains unaccepted evidence.

ADR impact: covered by session ADR disposition


### 2026-10-25T14:21:27Z - Issue

Raised: ECR Basic scanning cannot inspect the mirrored ADOT collector image.

Resolution: AWS reported UnsupportedImageError for the image's OS/package-manager. The custody requirement remains mandatory: a dedicated unprivileged job now runs a pinned portable scanner against the same pinned public source before the protected AWS publication job can run.


### 2026-10-25T14:21:27Z - Decision

Decision: Separate third-party vulnerability scanning from cloud credentials.

Rationale: The scanner job has only contents-read permission and the public immutable source reference. It has no OIDC permission, AWS role, target Environment, or private ECR URI. The protected publication job depends on its successful result. Custody receipts accept exactly one explicit scanner proof: legacy ECR-native or portable vulnerability scan.


### 2026-10-25T14:21:27Z - Context hygiene

Summary: Collector GitHub runs 40200948509 and 40201291933 both reached private mirroring but failed only at ECR Basic Scan: UnsupportedImageError. The trusted fix uses pinned Trivy action ed142fd in an unprivileged public-source job and keeps credentialed package publication separate. Local package receipt, collector guard, declaration, and privilege-boundary tests pass.

Durable evidence: Scanner boundary lives in the collector workflow; generic receipt vocabulary and regression live under .agentic/04.deploy/40-package and scripts/04.deploy/lifecycle/40-package/package-custody-receipt.


### 2026-10-25T14:22:11Z - Commit recorded

Commit: `db4cb76763a905ce6be2b7efd9ec8325a670b87b`

Message: fix(deploy): isolate collector vulnerability scan

Summary: Replaced unsupported ECR Basic scanning with a pinned portable scanner in a separate unprivileged public-source job, while preserving protected OIDC publication as a dependent job. Receipt validation now allows exactly one explicit native or portable scanner proof.

ADR impact: covered by session ADR disposition


### 2026-10-25T14:25:22Z - Issue

Raised: The unprivileged portable scanner was rate-limited by Public ECR before it could inspect the pinned image.

Resolution: Changed the route so the protected mirror job exports the exact target-private digest as a short-retention scan-input artifact; a separate unprivileged job scans that local artifact, and final custody/attestation waits for the scan. No failed run produced an accepted receipt or deployment.


### 2026-10-25T14:25:22Z - Decision

Decision: Scan the exact mirrored collector payload out of band from AWS credentials.

Rationale: The artifact handoff ties the scanner to the exact digest produced by the protected mirror job while keeping the third-party scanner unprivileged. The final protected job may issue receipt and attestations only after the scan-job dependency passes.


### 2026-10-25T14:25:22Z - Context hygiene

Summary: Runs 40200948509 and 40201291933 established successful collector startup/mirror but ECR Basic scan unsupported; run 40201922054 established portable scanner cannot anonymously pull Public ECR due rate limit. The new three-job workflow scans a short-retention Docker-save artifact of the private immutable image with no AWS access, then finalizes custody only on scan success.

Durable evidence: Workflow contract and static boundary guard remain under collector package custody; generic receipt validation records only safe scan verdict vocabulary.


### 2026-10-25T14:26:24Z - Commit recorded

Commit: `7defa885fb1fece769b15f170af298953c25adfd`

Message: fix(deploy): scan mirrored collector payload

Summary: Collector custody now mirrors the pinned source, exports the exact private image as a one-day scan input, scans that payload in an unprivileged job, and only afterward issues the protected SBOM/provenance/receipt. No scan result or failed attempt is accepted as custody evidence.

ADR impact: covered by session ADR disposition


### 2026-10-25T14:38:10Z - Issue

Raised: Corrected collector qualification after public layer throttling

Resolution: The protected collector custody job authenticated to AWS but its anonymous public registry layer pull returned Data limit exceeded before any mirror, scan, receipt, or workload action. Read-only OCI metadata established that public index sha256:7968... selects Linux/AMD64 manifest sha256:d0a..., which already exists identically in target-private ECR from the earlier protected mirror. The custody route now verifies the public index bytes, requires that identical private digest, qualifies and scans that payload, then issues custody only after the unprivileged scan.


### 2026-10-25T14:38:10Z - Decision

Decision: Use manifest-identity requalification for the retained collector mirror

Rationale: No delivery-role permission expansion or public image-layer retry is required. The collector workflow proves the immutable public OCI index and selected platform manifest, requires the same content-addressed digest in private ECR, and qualifies/scans only that private payload. This is a bounded custody correction; no ADR is required because it changes an in-flight target package route rather than the architecture.


### 2026-10-25T14:38:10Z - Context hygiene

Summary: Collector run 40202249108 failed at public layer download only. The exact Linux/AMD64 public manifest and retained private ECR image share sha256:d0a012252142c0999982fc34cddc88e2f9ce8c6b2bdf2c53e8e489a49dfbac31.

Durable evidence: Durable target contract and workflow are in infra/04.deploy/03.product/image/core-server-persistence-observability-collector and .github/workflows/publish-kanbien-core-platform-observability-collector.yml; run logs remain GitHub Actions evidence.


### 2026-10-25T15:18:21Z - Commit recorded

Commit: `d9cd2362`

Message: fix(deploy): build minimal observability collector

Summary: Replaced the vulnerable vendor collector mirror with a pinned minimal source build, archive-integrity handoff, unprivileged scan, and private publication only after scan success.

ADR impact: covered by session ADR disposition


### 2026-10-25T15:33:22Z - Commit recorded

Commit: `7d9aef87`

Message: fix(deploy): validate collector custody receipt

Summary: Corrected collector receipt check vocabulary so the final custody gate accepts the governed generic receipt.

ADR impact: covered by session ADR disposition


### 2026-10-25T15:39:53Z - Commit recorded

Commit: `8c06510178790fdabc0fd3a8899085f867f947e8`

Message: fix(deploy): bind permissions update to collector custody

Summary: Require the reviewed permissions update to bind qualified collector custody and a non-retained alert recipient.

ADR impact: covered by session ADR disposition


### 2026-10-25T15:41:53Z - Commit recorded

Commit: `50009a89da1782ad7575d1346a0de88dcf3b0466`

Message: fix(deploy): accept governed alert address

Summary: Corrected the CloudFormation alert-address regex after AWS rejected the POSIX character-class form before change-set creation.

ADR impact: covered by session ADR disposition


### 2026-10-25T15:43:22Z - Commit recorded

Commit: `1cd616751f0658eca485411b2a942d0c29668d8b`

Message: fix(deploy): use portable alert address pattern

Summary: Replaced the double-escaped CloudFormation alert pattern after AWS validated it as a literal backslash requirement.

ADR impact: covered by session ADR disposition


### 2026-10-25T15:54:11Z - Commit recorded

Commit: `b12f2d75`

Message: fix(deploy): recover failed permissions change sets

Summary: Corrected the permission update change-set allowlist and added safe failed-change-set retirement with regression coverage.

ADR impact: covered by session ADR disposition


### 2026-10-25T16:00:07Z - Commit recorded

Commit: `535815b0`

Message: refactor(deploy): phase persistence observability rollout

Summary: Separated the database-permission update from conditional observability activation so each is independently reviewed and recoverable.

ADR impact: covered by session ADR disposition


### 2026-10-25T16:04:28Z - Commit recorded

Commit: `324e0680`

Message: fix(deploy): validate phased observability declaration

Summary: Validated explicit observability activation separately from the database-permission phase and repaired its regression fixture topology.

ADR impact: covered by session ADR disposition


### 2026-10-25T18:48:32Z - Issue

Raised: Corrected IAM lifecycle semantics and package recovery boundary

Resolution: Runtime access now uses task-role renewal plus per-connection RDS IAM tokens; normal token expiry does not replace a healthy server. Recovery restores only bounded IAM login/membership after termination proof; local tests use disposable constrained PostgreSQL and do not claim RDS IAM proof.


### 2026-10-25T18:48:33Z - Context hygiene

Summary: Retained current implementation evidence: identity lifecycle, role-boundary recovery, restricted admin package smoke, restore/rollback qualifier, durable acceptance receipts, target and generic identity validators. Diagnostics commit a4eb4337 is already integrated at HEAD.

Durable evidence: Authoritative current contracts: core-server-persistence declaration and acceptance route; current executable evidence: composition/package smoke, controller regressions, acceptance rehearsal; historic accepted-release remains immutable legacy evidence.


### 2026-10-25T18:51:14Z - Commit recorded

Commit: `dadc6360`

Message: feat(deploy): harden persistence IAM lifecycle

Summary: Implements provider-neutral workload-identity lifecycle contracts and validators, RDS IAM token-per-connection adapter path, bounded administrator/revocation/recovery operations, isolated restore IAM binding, restricted disposable package qualification, durable retained proof acceptance, and diagnostics integration. Local declaration, target, composition, controller, acceptance, diagnostics, observability, check-selection, metadata, and staged gates passed; AWS IAM and incident closure remain live-proof work.

ADR impact: No ADR: bounded implementation and corrective integration under the existing PostgreSQL persistence and observability decisions.


### 2026-10-25T19:01:59Z - Issue

Raised: Corrected permission-surface change-set allowlist against the active stack baseline

Resolution: CloudFormation correctly exposed an existing-stack UPDATE delta that differed from the controller's stale CREATE-era allowlist. The controller now admits only the reviewed four task-role additions and exact IAM/RDS/secret/task/service modifications; it continues to reject network expansion and unrelated resources. No change set was executed while the guard was invalid.


### 2026-10-25T19:03:10Z - Commit recorded

Commit: `be024ef9`

Message: fix(deploy): align persistence permission update review

Summary: Replaces the stale CREATE-era permission-surface allowlist with the exact reviewed UPDATE delta for the active stack: four task-role additions plus explicit RDS/IAM/secret/task/service modifications. Fixed-control and controller regressions pass; the previously created change set remains unexecuted.

ADR impact: No ADR: narrow safety correction to an existing governed controller.


### 2026-10-25T19:17:42Z - Issue

Raised: IAM bootstrap rejected legacy non-elevated role

Resolution: The first governed bootstrap task stopped with the safe PERSISTENCE_ADMINISTRATION_BOOTSTRAP_IDENTITY_BOUNDARY_NOT_CONFIRMED result because the pre-existing runtime role retained PostgreSQL INHERIT. Corrected the role helper to reject elevated legacy roles but safely converge a non-elevated legacy identity to NOINHERIT without any credential SQL; local composition and target declaration checks pass.


### 2026-10-25T19:18:27Z - Commit recorded

Commit: `6c33ab8f`

Message: fix(deploy): converge legacy IAM runtime role

Summary: Normalizes only a non-elevated inherited password-era runtime role to the bounded no-inherit IAM login profile; retains rejection of elevated roles and proves no password or verifier SQL is emitted.

ADR impact: No ADR: bounded implementation correction under the existing IAM lifecycle decision.


### 2026-10-25T19:25:39Z - Issue

Raised: Package qualification exposed over-broad role convergence

Resolution: Hosted package run 40225491937 failed before AWS credentials, ECR, scan, or publication because the first convergence implementation rewrote already-bounded fixture roles under a constrained administrator. Narrowed convergence to only the legacy INHERIT attribute; bootstrap now refuses to reactivate NOLOGIN, reserving activation for explicit restore-runtime. Local Docker remains unavailable due host credential-helper failure; hosted package qualification remains authoritative.


### 2026-10-25T19:26:24Z - Commit recorded

Commit: `cfa2bd60`

Message: fix(deploy): preserve IAM revocation boundary

Summary: Narrows legacy role convergence to INHERIT only, retains fail-closed elevated-role checks, and prevents bootstrap from undoing NOLOGIN revocation; adds regression coverage.

ADR impact: No ADR: a focused correction within the existing IAM lifecycle model.


### 2026-10-25T19:34:55Z - Commit recorded

Commit: `52b0a15c`

Message: fix(deploy): bind persistence support image

Summary: Binds the persistence server, support program, and restoration verifier to one qualified immutable digest for create and update paths; change-set review and reconciliation now reject a support-image mismatch.

ADR impact: No ADR: bounded correction to the existing qualified-release controller.


### 2026-10-25T19:40:11Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): preserve update parameter state

Summary: Makes qualified persistence update review verify all controller-owned parameters and preserve every unowned CloudFormation parameter from the healthy stack, including template defaults.

ADR impact: No ADR: bounded correction to the existing qualified-release controller.


### 2026-10-25T19:43:31Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): reconcile executed update change sets

Summary: Recognizes CloudFormation's removed executed change set only when the current stack proves the exact candidate parameter identity; retains no-retry and mismatch uncertainty.

ADR impact: No ADR: bounded reconciliation correction for an existing provider lifecycle.


### 2026-10-25T19:51:46Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): classify migration task failures

Summary: Parses only closed migration rejection codes and failure classes from terminal task logs; raw task output and sensitive fields remain excluded from controller reports.

ADR impact: No ADR: bounded safe-diagnostics correction under existing deployment standards.


### 2026-10-25T20:06:29Z - Commit recorded

Commit: `HEAD`

Message: Require a read-only, receipt-backed migration-history observation before a failed persistence migration can be replayed.

Summary: Adds the state observer across the runnable administration program, reusable health contract, exact AWS workflow, package proof, and controller regression coverage.

ADR impact: covered by session ADR disposition


### 2026-10-25T20:24:33Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): observe migration state as owner

Summary: Repaired the migration-state observer so the constrained administrator assumes the migration owner only within a read-only transaction. Local composition, lifecycle controller, health/recovery, secret and diagnostic validations passed; Docker Desktop credential-helper failure prevents local package build before Docker starts.

ADR impact: covered by session ADR disposition


### 2026-10-25T20:45:16Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): retain applied migration state evidence

Summary: Accepted migration-state observation distinguishes replay permission from already-applied evidence and routes the durable receipt into acceptance.

ADR impact: covered by session ADR disposition


### 2026-10-25T20:58:11Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): classify persistence privilege probe outcomes

Summary: Preserve allowlisted privilege-probe outcomes while continuing to suppress provider detail.

ADR impact: covered by session ADR disposition


### 2026-10-25T22:32:56Z - Commit recorded

Commit: `HEAD`

Message: --summary

Summary: Retained governed persistence proof receipts, added qualified rollback-predecessor compatibility records, and made isolated restore verification safe and lifecycle-aware.

ADR impact: covered by session ADR disposition


### 2026-10-25T23:11:55Z - Decision

Decision: Closed isolated restore cleanup before correcting failure classification; retained proof is accepted only from a closed, allowlisted result envelope and all synthetic regression diagnostics stay outside durable evidence.

Rationale: Existing PostgreSQL persistence/recovery design; no new ADR required.


### 2026-10-25T23:11:55Z - Context hygiene

Summary: Safe restore verifier mapping, controller receipt handling, 24 validated live receipts, two validated operation diagnostics, and rollback compatibility record are the active carry-forward facts.

Durable evidence: Commits 8ff26fd6, 1b3d81cd, ed781c64; retained artifacts under infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/.


### 2026-10-25T23:11:55Z - Commit recorded

Commit: `8ff26fd6`

Message: fix: classify isolated restore verifier failures safely

Summary: Added closed allowlisted restore failure mapping, causal machine-code handling, controller rejection receipts, and focused regression coverage.

ADR impact: No ADR: bounded safe-diagnostic correction under the current persistence recovery decision.


### 2026-10-25T23:11:55Z - Commit recorded

Commit: `1b3d81cd`

Message: test: isolate synthetic deployment diagnostics

Summary: Kept controller-regression diagnostics in a temporary directory so synthetic tests cannot contaminate retained live-evidence storage.

ADR impact: No ADR: test isolation correction.


### 2026-10-25T23:11:55Z - Commit recorded

Commit: `ed781c64`

Message: evidence: retain persistence proof receipts

Summary: Committed 24 integrity-validated live proof receipts, two safe operation diagnostics, and immutable qualified rollback-compatibility records.

ADR impact: No ADR: durable evidence under the existing acceptance model.


### 2026-10-25T23:56:16Z - Commit recorded

Commit: `b154eea4`

Message: fix(deploy): stabilize isolated restore identity

Summary: Added a bounded, policy-stability recheck before the isolated restore verifier launches and retained five current-image live proof receipts for migration state, effective privilege, runtime IAM access, health, and read.

ADR impact: No ADR: bounded recovery-controller correction under the existing persistence IAM and restore design.


### 2026-10-26T00:05:21Z - Commit recorded

Commit: `aee7340b`

Message: fix(deploy): classify isolated restore boundaries

Summary: Separated restore IAM-token, connection and query failures into closed safe diagnostic categories; added composition and controller regression coverage; confirmed temporary restore cleanup.

ADR impact: covered by session ADR disposition


### 2026-10-26T00:31:24Z - Context hygiene

Summary: Retained-package receipts from GitHub runs 40243828846 and 40247863444 are now preserved under the persistence scope; their source delta is mechanically limited to the restore verifier and its direct harness support.

Durable evidence: The target-owned proof-applicability record is infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-applicability/restore-verifier-only-3edd9ac3002f.json; fresh current state and isolated-restore proof still remain required.


### 2026-10-26T00:31:24Z - Issue

Raised: Prevented historical ECS task expiry from forcing unrelated rehearsals.

Resolution: Acceptance now uses integrity-checked, durable controller receipts and a closed restore-verifier-only applicability record; the collector still independently observes current service, database, cleanup, and budget state.


### 2026-10-26T00:33:06Z - Commit recorded

Commit: `5a962e64858476e87fb793f7c2b55233c584d0ca`

Message: feat(deploy): retain persistence proof evidence

Summary: Added integrity-checked retained package receipts and a closed restore-verifier-only proof applicability route; acceptance keeps current-state checks and isolated restore fresh.

ADR impact: No ADR required: this is a bounded correction to the existing release-evidence architecture.


### 2026-10-26T00:34:49Z - Decision

Decision: Promoted durable evidence controls to remote main.

Rationale: After focused checks in a clean integration worktree, main advanced fast-forward from c60e55d4 to f0e0d23a; remote main was read back at that exact commit. The remaining live restore proof will use this governed version.


### 2026-10-26T00:50:50Z - Issue

Raised: Restore verifier could not reach the isolated restored database.

Resolution: Read-only provider facts showed the deployed stack lacks the declared RestorationVerifierRestoredDatabaseEgress resource. Added a governed egress-only correction mode that accepts exactly that one CloudFormation addition and no broader surface change.


### 2026-10-26T01:03:24Z - Issue

Raised: Restore verifier connection result was too coarse

Resolution: A rejected isolated-restore verifier emitted only CONNECTION_UNAVAILABLE even after provider facts disproved the suspected missing egress rule. Added a bounded TCP preflight before PostgreSQL credential use so the next governed proof distinguishes a closed transport path from a post-transport database handshake failure without exposing provider text, endpoints, SQL, or credentials.


### 2026-10-26T01:03:24Z - Decision

Decision: Use safe transport preflight before restore verifier authentication

Rationale: The preflight opens and immediately closes only a TCP socket to the declared private database address. PostgreSQL TLS, IAM authentication, and query proof remain in the existing driver path. Unknown post-preflight driver failures map to a new closed handshake result; raw provider detail remains excluded.


### 2026-10-26T01:03:24Z - Context hygiene

Summary: The failed restored copy has been deleted and its temporary inline IAM policy is absent. The deployed service remains healthy. The next necessary live operation is a new qualified verifier image plus one fresh isolated restore proof; do not retry the expired DB incarnation.

Durable evidence: Current task evidence is in AWS ECS/RDS and durable accepted proof receipts remain under the core-server-persistence target release-evidence directory.


### 2026-10-26T01:05:07Z - Commit recorded

Commit: `408d7734`

Message: fix(deploy): classify isolated restore transport boundary

Summary: Adds a credential-free bounded TCP preflight to the isolated restoration verifier, distinguishes a closed transport boundary from an opaque post-transport PostgreSQL/TLS handshake, accepts only those closed result codes in the governed restore controller, and proves the classification plus transport fixture locally.

ADR impact: No ADR: this is an implementation refinement within the existing isolated-restore diagnostic and recovery decision.


### 2026-10-26T01:15:37Z - Decision

Decision: Bind proof reuse to the immutable image input closure

Rationale: The new diagnostic image differs from the previously qualified image only in the restoration verifier among package inputs. Target controllers, durable-evidence artifacts and acceptance checks remain in the full audited source delta but do not change the executable image. The applicability control now rejects every changed package input except that verifier and records the full delta for review.


### 2026-10-26T01:15:37Z - Context hygiene

Summary: GitHub run 40252659734 qualified source 2a7a3d11 and immutable image sha256:5a7be9c80dea97a46d319058218ddc32788c8d1fcee617a4bedadf083376e3ba. Its custody receipt and a restore-verifier-only applicability record are target evidence. The failed temporary restored database and its temporary policy are absent; do not retry that incarnation.

Durable evidence: Package receipt: core-server-persistence/30-release-evidence/package-receipts/package-custody-40252659734.json. Applicability: .../proof-applicability/restore-verifier-only-5a7be9c80dea.json. GitHub custody artifact run 40252659734 remains upstream evidence.


### 2026-10-26T01:16:35Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): bind proof reuse to image inputs

Summary: Retains package custody receipt 40252659734 and its target proof-applicability record. Applicability now compares actual core-server-persistence package input paths, rejects any non-restore verifier image input change, and retains the full source delta for audit.

ADR impact: No ADR: this corrects the existing durable-evidence applicability control rather than changing the release architecture.


### 2026-10-26T01:41:45Z - Issue

Raised: Restore verifier reached TCP but not a classified PostgreSQL handshake

Resolution: Live recovery proof established the private TCP route works, then returned the closed DATABASE_HANDSHAKE_UNAVAILABLE result. The failed isolated copy is governed for cleanup. Added a credential-free PostgreSQL SSLRequest/TLS certificate preflight so the next image can distinguish TLS negotiation/trust from post-TLS authentication/protocol failure without exposing raw provider text.


### 2026-10-26T01:42:24Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): probe restore verifier TLS boundary

Summary: Adds a credential-free PostgreSQL SSL/TLS preflight to the isolated restore verifier. It retains closed transport, TLS negotiation, TLS trust and post-TLS handshake outcomes, with composition and restore-controller checks passing.

ADR impact: No ADR: focused diagnostic refinement within the established isolated recovery proof.


### 2026-10-26T02:41:35Z - Commit recorded

Commit: `1ab65b6c`

Message: evidence(deploy): retain restore handshake rejection

Summary: Retained the qualified package receipt, image-input applicability record, and closed isolated restore rejection after source-safe cleanup; recovery acceptance remains unproven.

ADR impact: No ADR: factual live evidence under the existing durable proof model.


### 2026-10-26T02:45:13Z - Commit recorded

Commit: `HEAD`

Message: fix(deploy): require restore PostgreSQL log export

Summary: Requires each isolated restore to enable and prove the existing PostgreSQL CloudWatch log export before a verifier can run.

ADR impact: No ADR: bounded recovery diagnostic source correction.


### 2026-10-26T02:56:39Z - Commit recorded

Commit: `ca0d679f`

Message: fix(deploy): classify isolated restore server logs safely

Summary: Require PostgreSQL export on derived restores and retain only a bounded server-log classification for a rejected verifier.

ADR impact: No ADR impact; target-scoped recovery diagnostic hardening.


### 2026-10-26T07:19:16Z - Commit recorded

Commit: `b3c8e547`

Message: fix(deploy): recognize RDS log export configuration

Summary: Treat RDS configuring-log-exports as an ordinary in-flight restore state and prove it in restore-controller regression.

ADR impact: No ADR impact; provider lifecycle-state correction.


### 2026-10-26T07:40:59Z - Commit recorded

Commit: `ed63c025`

Message: fix(deploy): resume restore identity stabilization

Summary: Replaced the controller's blocking identity-propagation delay with a bounded exact CloudTrail observation before the one allowed restore verifier launch.

ADR impact: No ADR impact; governed isolated-restore reconciliation remains target-specific.


### 2026-10-26T07:41:28Z - Commit recorded

Commit: `3bcfe650`

Message: test(deploy): harden restore identity observation

Summary: Added malformed, stale, and mismatched CloudTrail observation regressions; retained the closed historical restore rejection diagnostic after source-health and cleanup reconciliation.

ADR impact: No ADR impact; this is a target-specific recovery-controller safety correction.


### 2026-10-26T07:44:45Z - Issue

Raised: Promoted isolated restore controller hardening

Resolution: Verified normal fast-forward promotion of 820185f1e5dd207e38fe8b392bf11c6c53bdfe96 to origin/main after clean-worktree restore, composition, and deployment-diagnostic regressions; source and target state were rechecked.


### 2026-10-26T08:57:51Z - Commit recorded

Commit: `749e869827d7a7e3affbf93899f60f43b5c0b6d7`

Message: feat(deploy): compose private observability collector

Summary: Added a dedicated private OTLP collector, target declaration and guarded update controller; local composition, adapter, declaration, package-workflow, target and template checks pass.

ADR impact: No new ADR: this implements the established separate-identity collector decision.


### 2026-10-26T08:59:13Z - Decision

Decision: Promoted private observability collector implementation

Rationale: Remote main fast-forwarded from 92adeab0 to d52e7ffd through the clean governed integration worktree after declaration and controller gates passed; server and collector package qualification is the next boundary.


### 2026-10-26T09:58:26Z - Context hygiene

Summary: The live observability activation completed with both ECS services healthy, but CloudWatch could not find the readiness metric because the collector selector was over-escaped and the alarm dimensions omitted readiness. The corrected declaration/template is commit 6accf269; this commit adds a change-set-reviewed collector-only repair controller and regression coverage.

Durable evidence: Provider facts are in the kanbien-core-platform stack/ECS services; the governed repair controller, declaration validator, target smoke test, and AWS workflow are the durable repository evidence.


### 2026-10-26T09:59:19Z - Commit recorded

Commit: `e5bbda7c`

Message: fix(deploy): govern collector metric delivery repair

Summary: Adds a healthy-baseline, exact-change-set controller mode for the corrected readiness metric configuration. It permits only collector task-definition and service modification, with regression tests and workflow guidance.

ADR impact: No ADR: this is an implementation correction within the accepted observability deployment boundary.


### 2026-10-26T10:44:12Z - Context hygiene

Summary: Observability activation is healthy after a collector-only metric repair. The target still lacks confirmed SNS email delivery, so no revocation/recovery is repeated until the receipt controller can retain failure, notification, and recovery evidence.

Durable evidence: Controller: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/. Receipt validator: .../observability-receipts.py. Acceptance collector/route now consume the three receipt references; AWS SNS read-only observation remains PendingConfirmation.


### 2026-10-26T10:49:35Z - Commit recorded

Commit: `962cddd1`

Message: feat(deploy): retain observability readiness proof

Summary: Added durable, integrity-checked readiness failure, notification, and recovery receipts; wired acceptance to retained receipts while preserving fresh current-state checks.

ADR impact: No ADR: this is a bounded target-scoped extension of existing receipt and acceptance controls.


### 2026-10-26T11:47:27Z - Decision

Decision: Promoted verified observability evidence controls to origin/main

Rationale: Fast-forwarded origin/main from 67798a47 to 089f63c9 through isolated integration branch agentic/remote-promotion/chat_2026-10-05-09-59-can-you-walk-me-through-which-part-of-my-repo-work-on-the-fo-20261026T114630Z after receipt, controller, acceptance-route, and target-declaration checks passed. SNS delivery remains PendingConfirmation; no live credential revocation or rehearsal was submitted.


### 2026-10-26T13:28:56Z - Commit recorded

Commit: `8bc53dd8`

Message: fix(deploy): retain persistence acceptance evidence

Summary: Added durable retained proof receipts and candidate acceptance evidence, corrected isolated-restore observation handling, and preserved the rejected restore result without repeating it.

ADR impact: Covered by existing deployment evidence and recovery governance; no ADR change.

## Sub-Agent Activity

- None recorded yet.

## Commits

- Commit: `3536df5a9a6461f35f02d7ca3e02e2337efa55ec`
  Time UTC: 2026-10-25T14:53:24Z
  Message: fix(deploy): retain collector scan evidence
  Summary: The unprivileged scanner now retains its JSON result whether clean or failing, then fails the job explicitly when the scan verdict is not clean. This makes vendor findings inspectable while preserving fail-closed custody.
  ADR impact: No ADR: bounded evidence-retention correction to the active target package custody route.

- Commit: `f5890f9a82cae7e8c46a24c8b01acf9dee234c50`
  Time UTC: 2026-10-25T14:49:53Z
  Message: fix(deploy): scan exact collector payload
  Summary: Replaced the scanner action's ineffective tar-input route with an explicitly pinned Trivy installation and command that scans the exported private image tar. Final custody remains blocked until that exact scan passes.
  ADR impact: No ADR: bounded correction to the active target package custody route.

- Commit: `5ca0d67e4735c955bcb9ef59b6002e2d21b42785`
  Time UTC: 2026-10-25T14:45:34Z
  Message: fix(deploy): pin collector platform manifest
  Summary: Replaced the rate-limited runtime public registry metadata lookup with the already observed, reviewed public-index-to-Linux/AMD64 manifest mapping. The protected workflow now requires the exact private content digest, starts it safely, scans that payload without cloud credentials, then records custody only after a clean scan.
  ADR impact: No ADR: bounded reliability correction to the active target package custody route.

- Commit: `7977430ab8ad19f9956125bdcd94e9ff153eb69c`
  Time UTC: 2026-10-25T14:40:03Z
  Message: fix(deploy): qualify retained collector mirror
  Summary: Replaced anonymous public collector layer pulls with an immutable OCI index-to-private manifest identity proof, then qualifies and scans the retained exact private payload before custody evidence.
  ADR impact: No ADR: bounded correction to an active target package custody route.



- Commit: `9868be3a9bede808dd5bf3872d1a89fa64c62503`
  Time UTC: 2026-10-06T16:57:10Z
  Message: feat(deploy): add target alignment governance foundation
  Summary: Added the provider-neutral deployment governance foundation, bounded declaration coverage and target-alignment planning, lifecycle map, deploy-control inventory, session-continuity safeguard, and the draft platform-to-target chain plan. No AWS, target, secret, or PostgreSQL Stage 6 mutation occurred.
  ADR impact: No ADR: draft transition only; the existing migration plan retains AWS authority and any durable authority change needs separate review.


- Commit: `f994270373f9703f1ebe1ce5c03d016ccfe91f53`
  Time UTC: 2026-10-06T23:16:09Z
  Message: docs(deploy): refine scope and pipeline control plan
  Summary: Expanded the draft plan with scope criteria, target-local scope and pipeline catalogues, the first public-server scope path, package-publication custody, scope-qualified alignment, staged full-repository coverage, and an AWS-governed drift-evidence producer track based on verified reconciliation failures.
  ADR impact: No ADR: this remains a draft planning refinement; AWS authority and target changes remain separately governed.


- Commit: `6572d8b5`
  Time UTC: 2026-10-07T15:47:49Z
  Message: docs(deploy): expand target control plan
  Summary: Expanded the draft deployment-control plan with module configuration surfaces, foundation-resource ownership, provider-selection and workload-access contracts, complete-estate coverage states, lifecycle change/retirement rules, and safe future tree migration. Added a living packaging and deployment learning handbook.
  ADR impact: No ADR: planning and education artifacts only; no live provider, target, or deployed-architecture decision.


- Commit: `4a1ee583`
  Time UTC: 2026-10-07T23:06:05Z
  Message: docs(agentic): govern product-to-target changes
  Summary: Expanded the draft plan with repo-wide agentic governance, generic harness portability rules, a migration path for scattered mandatory instructions, product-module contract controls, and explicit product-to-deployment impact routing. No AWS, target, secret, or PostgreSQL mutation occurred.
  ADR impact: No ADR: draft plan and governance guidance only; no live provider authority, target configuration, or deployed architecture decision.


- Commit: `82ac95eb`
  Time UTC: 2026-10-08T16:32:57Z
  Message: docs(deploy): plan dependency behaviour controls
  Summary: Added concern-control governance, dependency availability and observation artifacts, operation-and-promise scope declarations, and durable teaching lessons for dependency behaviour, networking, safe diagnostics, and source-of-truth ownership. No AWS, target, secret, or PostgreSQL mutation occurred.
  ADR impact: No ADR: draft governance and education only; no live provider authority, target configuration, or deployed architecture decision.


- Commit: `a6e69078`
  Time UTC: 2026-10-17T21:14:01Z
  Message: docs(deploy): govern dependency identity lifecycle
  Summary: Expanded the deployment-control plan and teaching handbook with dependency lifecycle, network relationship, workload identity/access, credential rotation, and safe failure-handling governance. No AWS, target, secret, or runtime changes occurred.
  ADR impact: No ADR: draft provider-neutral governance and education only; no live provider, target, or deployed-architecture decision.


- Commit: `49f12712`
  Time UTC: 2026-10-18T21:04:40Z
  Message: docs(deploy): govern release and package control
  Summary: Expanded the draft deployment-control plan and teaching handbook with scope responsibility inventories; health, release-verification, rollback and recovery controls; safe observability and alerting; target alignment; and immutable package custody, promotion, and exception governance. No AWS, target, secret, runtime, or PostgreSQL mutation occurred.
  ADR impact: No ADR: this remains draft provider-neutral governance and education material; it makes no live provider-authority, target-configuration, or deployed-architecture decision.


- Commit: `cfb65999`
  Time UTC: 2026-10-18T22:40:52Z
  Message: docs(deploy): stage platform foundation controls
  Summary: Defined the bootstrap runtime slice, staged persistence/security/observability foundation order, and incremental product/core integration path. Existing platform and core code remains factual source material; no AWS, target, secret, runtime, or PostgreSQL mutation occurred.
  ADR impact: No ADR: this refines the draft provider-neutral governance and education model without making a live target, provider-authority, or deployed-architecture decision.


- Commit: `8315f1d1`
  Time UTC: 2026-10-18T23:50:23Z
  Message: docs(deploy): define bootstrap target lifecycle
  Summary: Defined the planned private kanbien-core-platform bootstrap target lifecycle: clean creation from absent baseline A, one controlled candidate update B, safe verifier/configuration/access/network boundaries, receipts, and recovery without automatic redeployment. Updated the deployment plan and teaching handbook; no AWS, target, secret, runtime, or PostgreSQL mutation occurred.
  ADR impact: No ADR: this is a draft governance and education refinement. It does not create a live target, change provider authority, or decide a deployed architecture.


- Commit: `39d4a649`
  Time UTC: 2026-10-19T06:51:03Z
  Message: docs(deploy): define core server package boundary
  Summary: Recorded the planned kanbien-core-server entrypoint family, generic release-verification/configuration ownership, technical-access naming, optional observability-persistence bridge, and dedicated core-server image boundary. No source implementation, AWS resource, target directory, secret, runtime, or PostgreSQL state changed.
  ADR impact: No ADR: this remains a draft governance and education refinement; it creates no live target or deployed architecture.


- Commit: `fa4fcaae`
  Time UTC: 2026-10-19T19:38:57Z
  Message: docs(deploy): map core release rehearsal
  Summary: Recorded the core-server release rehearsal layout, lifecycle-owned check locations, persistence-owned observability integration, safe evidence locations, and staged implementation order. No runtime, AWS, target, or GitHub mutation occurred.
  ADR impact: No ADR: documentation-only planning refinement; target and provider decisions remain subject to later review.


- Commit: `f6256292`
  Time UTC: 2026-10-19T19:59:23Z
  Message: docs(aws): plan core platform release rehearsal
  Summary: Added the review-only, target-specific Kanbien core-platform rehearsal plan. It defines isolated R1-R6 implementation packages, E0-E7 execution gates, stage-plus-target script ownership, safe receipts, and explicit future AWS approval requirements.
  ADR impact: No ADR: no target/provider decision is selected or executed by this plan.


- Commit: `e9fbc711`
  Time UTC: 2026-10-19T20:12:10Z
  Message: feat(deploy): add runnable program contract gate
  Summary: Added provider-neutral runnable-program and package-candidate governance, contract schema/template/guide, and report-only checker fixtures that fail closed for missing records, invalid commands, unapproved dependencies, and unsafe evidence fields. No runtime, target, AWS, or GitHub change occurred.
  ADR impact: No ADR: generic governance and a local report-only gate only.


- Commit: `2a96d7f2`
  Time UTC: 2026-10-19T20:35:28Z
  Message: feat(platform): separate persistence observability
  Summary: Moved persistence-specific observation integration into platform/persistence; removed persistence from generic observability; made server runtime configuration and safe release identity explicit, tested platform contracts.
  ADR impact: No ADR: implements the approved package boundary without provider or target selection.


- Commit: `8c110812`
  Time UTC: 2026-10-19T20:50:37Z
  Message: feat(deploy): add core server runnable program
  Summary: Added the core-server entrypoint, factual runnable-program declaration, isolated compile configuration, and deterministic dependency-boundary proof that rejects forbidden package payloads.
  ADR impact: No ADR: implements the approved bootstrap boundary without selecting a target or provider.


- Commit: `bb539fe3`
  Time UTC: 2026-10-19T21:04:22Z
  Message: feat(deploy): add core server image boundary
  Summary: Added the dedicated core-server image contract, minimal Dockerfile, payload verifier, and local smoke scripts. Static package proof passed; Docker build/run remains explicitly skipped because this environment has no running daemon.
  ADR impact: No ADR: implements approved package boundary; no registry, provider, or target was selected.


- Commit: `60891e4b`
  Time UTC: 2026-10-20T03:36:52Z
  Message: feat(deploy): declare core platform target
  Summary: Added the planned-not-live-selected kanbien-core-platform target, bootstrap scope, foundation/access/network/pipeline declarations, and fail-closed static coverage verifier. Every live provider fact remains explicit E0-required and target mutation is blocked.
  ADR impact: No ADR: no AWS/provider selection or live resource decision was made.


- Commit: `25014ff9`
  Time UTC: 2026-10-20T03:46:39Z
  Message: feat(deploy): add core target control surfaces
  Summary: Added fixed prepare/deploy/verify control commands for kanbien-core-platform/bootstrap-runtime. They reject target overrides, validate static evidence, and fail closed with unresolved E0 facts before any external access.
  ADR impact: No ADR: no provider selection or target mutation occurred.


- Commit: `ad6cf1e8`
  Time UTC: 2026-10-20T03:54:43Z
  Message: fix(deploy): start core image command
  Summary: Fixed the generated image command wrapper to invoke the core server. Added a command-runtime test; the actual local Docker image now passes liveness, readiness, and safe release-verification smoke under restricted runtime settings.
  ADR impact: No ADR: repair within the existing image contract.


- Commit: `ca639258dab1c423d7d8ac7c2045223bbbb358fe`
  Time UTC: 2026-10-20T10:07:39Z
  Message: docs(deploy): phase core platform cost controls
  Summary: Recorded the E1 private ECS target design, phased cost-tag bootstrap, review-only foundation templates, and bounded execution authority. No AWS resource was created; the first AWS mutation remains the separately controlled empty ECR tag bootstrap.
  ADR impact: ADR 0003 records the private ECS bootstrap topology and shared-VPC exception.


- Commit: `60a59af366eea2ceed84ea83cd960e2a6d4a350a`
  Time UTC: 2026-10-20T10:33:20Z
  Message: fix(deploy): consume core tag bootstrap repository
  Summary: Recorded E2a creation evidence and corrected the E2c foundation to consume the immutable ECR repository created by tag bootstrap instead of attempting a duplicate; added explicit Target tags to target-owned foundation resources.
  ADR impact: ADR 0003 unchanged; execution evidence supports its phased private target decision.


- Commit: `7ea7371fd10ad2bcb3fd7b6c147b774fc75e99fa`
  Time UTC: 2026-10-20T10:53:24Z
  Message: feat(deploy): add core platform custody and runtime controls
  Summary: Added target-bound package custody workflow and safe receipt validation, private immutable-digest runtime/verifier CloudFormation, and hardened foundation network and ECR controls. All local static, receipt, workflow, target declaration, whitespace and CloudFormation validation checks passed; E2c remains blocked by AWS Target cost-tag propagation.
  ADR impact: ADR 0003 remains the applicable private ECS target decision.


- Commit: `7720422a1fca3b267ebf6925cc29c1c5887fb979`
  Time UTC: 2026-10-20T11:40:36Z
  Message: feat(deploy): create private core platform foundation
  Summary: Recorded temporary cost-budget waiver and corrected CloudFormation parameter validation after it rejected valid private VPC inputs. The approved kanbien-core-platform foundation stack is CREATE_COMPLETE; target-specific budget remains deferred until AWS exposes Target.
  ADR impact: ADR 0003 remains applicable.


- Commit: `02405b56499ba30f928aaad539df27756167c5cf`
  Time UTC: 2026-10-20T17:14:39Z
  Message: feat(deploy): harden reusable package delivery controls
  Summary: Separated reusable delivery validators from AWS adapters and fixed target wrappers; added safe asynchronous-condition evidence, delivery policy coverage, package qualification, execution-state enforcement, and diagnostics. All selected repository checks passed; no AWS mutation occurred.
  ADR impact: No ADR needed: implements the existing provider-neutral deployment architecture.


- Commit: `b34c211e`
  Time UTC: 2026-10-20T18:53:06Z
  Message: feat(deploy): add live core runtime control chain
  Summary: Added reusable alignment, reviewed change-set, deployment, and private-verification controls; added the output-only foundation contract required for the core runtime.
  ADR impact: No new ADR; implements the existing deployment control plan.


- Commit: `85cdd2d2`
  Time UTC: 2026-10-20T18:53:06Z
  Message: chore(deploy): remove generated bytecode
  Summary: Removed accidental generated Python bytecode from the deployment-control commit.
  ADR impact: No ADR impact.


- Commit: `139d26db`
  Time UTC: 2026-10-20T18:53:06Z
  Message: chore(repo): ignore python bytecode
  Summary: Prevented generated Python bytecode from being tracked in future deployment work.
  ADR impact: No ADR impact.


- Commit: `8a0ffd8f`
  Time UTC: 2026-10-20T19:04:38Z
  Message: fix(deploy): accept stable foundation update state
  Summary: Accepted only stable successful CloudFormation states in AWS alignment and added a regression test; repaired metadata coverage for the related target-alignment controls.
  ADR impact: No new ADR; corrects the implementation of the approved alignment control.


- Commit: `5fd8014c`
  Time UTC: 2026-10-20T19:12:51Z
  Message: fix(deploy): validate runtime provider parameters
  Summary: Corrected the runtime ECR URI contract, added representative provider-identifier regression coverage, mapped parameter failures safely, and added aws-mutation to the shared metadata taxonomy.
  ADR impact: No new ADR; corrects reusable deployment and harness metadata controls.


- Commit: `e517670c`
  Time UTC: 2026-10-20T19:16:57Z
  Message: fix(deploy): verify initial change-set state
  Summary: Corrected initial change-set review to use stable AWS evidence when ChangeSetType is omitted, with regression coverage for absent versus existing runtime stacks.
  ADR impact: No new ADR; corrects reusable deployment-control interpretation.


- Commit: `2928e1e956adc1cb8c81b3d0c9f92d4727d9fdec`
  Time UTC: 2026-10-20T19:20:33Z
  Message: fix(deploy): recognise initial review stack
  Summary: Recognised CloudFormation REVIEW_IN_PROGRESS as the only permitted initial change-set review stack, with regression coverage that rejects a real deployed runtime.
  ADR impact: No new ADR; corrects reusable deployment-control interpretation.


- Commit: `28b9fcd8a18bab342c0160943d5460b8f60d80db`
  Time UTC: 2026-10-20T19:25:00Z
  Message: fix(deploy): align service discovery binding
  Summary: Removed SRV-only fields from the A-record ECS registry binding and made successful empty AWS mutation responses valid, with regression coverage.
  ADR impact: No new ADR; corrects reusable deployment-control interpretation.


- Commit: `56a7952d874c094bb0dfcabb3c104bacfb32b87b`
  Time UTC: 2026-10-20T19:47:04Z
  Message: fix(deploy): permit logs endpoint streams
  Summary: Corrected the private Logs endpoint policy to allow exact log-stream ARNs and added a focused foundation policy regression test.
  ADR impact: No new ADR; corrects reusable deployment-control interpretation.


- Commit: `4ddad06f033d6eac10a48ade42f0d72e9c3e7b89`
  Time UTC: 2026-10-20T19:59:20Z
  Message: fix(deploy): allow task log streams
  Summary: Corrected the task execution-role CloudWatch Logs ARN to match the endpoint policy and strengthened the shared foundation regression.
  ADR impact: No new ADR; corrects reusable deployment-control interpretation.


- Commit: `832e709a`
  Time UTC: 2026-10-20T22:10:46Z
  Message: feat(deploy): govern core platform release updates
  Summary: Recorded accepted release A; implemented update and restoration controls, cross-component release checks, and authoritative release workflows. Live B-to-A rehearsal remains gated on cost-waiver renewal and GitHub Environment approval.
  ADR impact: ADR not required: bounded release-control governance under existing deployment architecture.


- Commit: `2d13367c`
  Time UTC: 2026-10-20T22:19:51Z
  Message: chore(core-server): label bootstrap release
  Summary: Prepared harmless Release B by changing only the private bootstrap app display label. Declared source and dependency checks passed; the real image smoke will be rebuilt against this exact source revision before publication.
  ADR impact: ADR not required: bounded rehearsal-only source metadata change under the accepted release workflow.


- Commit: `2000f119`
  Time UTC: 2026-10-21T08:43:38Z
  Message: fix(deploy): enforce core-platform cost waiver gate
  Summary: Recorded the approved expiring cost waiver as target-local evidence and enforced its status and expiry before every core-platform runtime change-set creation or execution.
  ADR impact: No ADR: this implements the existing release-control policy.


- Commit: `d2762553`
  Time UTC: 2026-10-21T08:54:40Z
  Message: fix(deploy): accept proven AWS update change sets
  Summary: Accepted an omitted AWS ChangeSetType only for independently proven healthy existing stacks; the change remains bounded to task-definition and service updates.
  ADR impact: No ADR: this corrects adapter handling under the existing release-control architecture.


- Commit: `3fcc0180`
  Time UTC: 2026-10-21T09:22:03Z
  Message: fix(deploy): reuse completed verifier evidence
  Summary: Recorded the successful B-to-A rehearsal, reconciled the live accepted baseline, and made repeated private verification reuse current-deployment acceptance evidence instead of launching another task.
  ADR impact: No ADR: this strengthens the existing governed release-verification control.


- Commit: `b10fc32f`
  Time UTC: 2026-10-21T11:34:39Z
  Message: feat(deploy): govern artifact placement and naming
  Summary: Added the deployment artifact placement-and-naming standard, proposed-path validator with regression proof, lifecycle ownership linkage, and the governed ordered-layout migration plan. No active paths or provider state changed.
  ADR impact: No ADR: the commit establishes a migration standard and plan, but does not change the active durable namespace or compatibility promise.


- Commit: `d5cb0c54`
  Time UTC: 2026-10-21T11:48:26Z
  Message: refactor(deploy): order core platform target declarations
  Summary: Completed migration batch 2: canonical target declaration hierarchy, updated active consumers and fixtures, refreshed recognition sources, and passed declaration, package-custody, release-control, metadata, migration, and repository commit gates. No cloud or GitHub state changed.
  ADR impact: covered by session ADR disposition


- Commit: `5240b9a0`
  Time UTC: 2026-10-21T11:52:32Z
  Message: refactor(deploy): route core AWS workflow by lifecycle
  Summary: Completed migration batch 3: rehomed the single AWS bootstrap-runtime release workflow to the lifecycle-first target/scope route, clarified deploy, verification, and restoration sections, updated consumers and generated recognition sources, and passed required metadata, path, target, package, release, and helper-smoke gates. No cloud or GitHub state changed.
  ADR impact: covered by session ADR disposition


- Commit: `ab738224`
  Time UTC: 2026-10-21T11:56:22Z
  Message: refactor(deploy): clarify target alignment harness
  Summary: Completed migration batch 4: moved reusable target-alignment workflow and standard into lifecycle-first clear-action paths, updated active consumers and generated recognition sources, passed both migration checks and required commit gates, and deliberately deferred a nonexistent alignment schema. No cloud or GitHub state changed.
  ADR impact: covered by session ADR disposition


- Commit: `ee8d5746`
  Time UTC: 2026-10-21T11:59:54Z
  Message: docs(deploy): record lifecycle-first path decision
  Summary: Corrected the migration governance gap with ADR 0037. It records the lifecycle-first authority-path decision, the no-cloud corrective disposition for the earlier generic move, and the rule governing remaining generic migrations. Runnable-program migration may now continue under this ADR.
  ADR impact: covered by session ADR disposition


- Commit: `ac504bff`
  Time UTC: 2026-10-21T12:06:20Z
  Message: refactor(deploy): group runnable program build controls
  Summary: Completed the runnable-program migration: workflow, standard, schema, template, and guide now sit under 20-build with all consumers updated. Passed runnable-program and core dependency-boundary smoke suites, five migration checks, generated recognition-source validation, metadata, and commit gates. No cloud or GitHub action occurred.
  ADR impact: covered by session ADR disposition


- Commit: `66e5cb57`
  Time UTC: 2026-10-21T12:10:09Z
  Message: refactor(deploy): group package custody controls
  Summary: Completed package-custody migration: workflow, standard, receipt schema, and guide now sit under 40-package with target pipeline and checker consumers updated. Passed package receipt, package workflow, target declaration, migration, generated-index, metadata, and commit gates. No cloud or GitHub action occurred.
  ADR impact: covered by session ADR disposition


- Commit: `5c29a0a3a2c81f7b3b70fa155f4b62f8449bc8fc`
  Time UTC: 2026-10-21T14:57:37Z
  Message: docs(deploy): record proven core release route
  Summary: Activated the proven core route metadata, documented the normal health/update/restoration evidence and its deliberate-failure proof boundary, and updated the generic plan and teaching handbook before the reusable health/recovery package.
  ADR impact: No ADR: this records and routes existing architecture without changing the durable deployment architecture.


- Commit: `e559c8cee3b434978fd7abb8cb9f8d414f47cfbc`
  Time UTC: 2026-10-21T15:37:01Z
  Message: feat(deploy): require declared health recovery
  Summary: Added reusable Run-stage health/failure/recovery declarations and validation, wired them into product, target alignment, and release controls, and recorded the core scope's truthful live-recovery proof boundary.
  ADR impact: No ADR: this implements the existing lifecycle-first placement decision and documented implementation packet.


- Commit: `585bd3456cb85d95b24b85b862a3f5e7d3e9b3bb`
  Time UTC: 2026-10-21T15:54:02Z
  Message: feat(aws): rehearse accepted workload replacement
  Summary: Added a fixed, target-bound 60-run control that proves ECS replaces one deliberately stopped accepted task and requires private verifier evidence newer than the stop boundary. Static declaration, release, placement, metadata, and target-control checks passed.
  ADR impact: No ADR: this extends the existing lifecycle-first release and recovery control.


- Commit: `2a58ab882c12c7210e30d272721745da3adcaea2`
  Time UTC: 2026-10-21T16:03:59Z
  Message: docs(deploy): record workload recovery rehearsal
  Summary: Recorded the live controlled-stop ECS replacement outcome, advanced the scope proof to passed, required passed proof evidence to exist, taught the remaining proof boundary, and validated both restoration and replacement evidence against the accepted release.
  ADR impact: No ADR: this is evidence-driven completion of the existing health/recovery design.


- Commit: Add workload-aware recovery and target budget controls
  Summary: Adds typed workload health and recovery validation, provider-evidence freshness checks, release rehearsal controls, and a governed 00 target-budget provisioning path with recorded live budget evidence. PostgreSQL is selected as the first future persistence reference; no persistence infrastructure has been created.
  ADR impact: covered by session ADR disposition


- Commit: `4021fbf2`
  Time UTC: 2026-10-22T20:39:44Z
  Message: feat(deploy): govern workload recovery and target budget
  Summary: Adds workload-aware health and recovery contracts, active-workload validation, evidence freshness enforcement, bounded rehearsal controls, and verified 00 target-budget governance. PostgreSQL is selected as the next persistence reference; no persistence infrastructure is created.
  ADR impact: not-needed: bounded operational controls follow existing deployment architecture


- Commit: feat(deploy): govern workload secret dependencies
  Summary: Add portable secret declarations, workload-aware validation and inventory enforcement; include corrective regressions and PostgreSQL preparation guidance.
  ADR impact: ADR 0041 records the existing PostgreSQL reference selection.


- Commit: `6ada7e35`
  Time UTC: 2026-10-22T22:22:12Z
  Message: feat(deploy): govern workload secret dependencies
  Summary: Implemented portable secret declarations, inventory enforcement and type-aware failure contracts; closed all reviewed validator defects with synthetic regressions. Required commit and recognition gates passed; included PostgreSQL preparation guidance without provider execution.
  ADR impact: ADR 0041 records the PostgreSQL reference selection for kanbien-core-platform.


- Commit: `bca7af432d405f666b281ad990defe8a69205503`
  Time UTC: 2026-10-22T22:26:46Z
  Message: Merge main through governed refresh rehearsal
  Summary: Applied the tested non-rewriting refresh from main. Regenerated the sole conflicting generated artifact index, recorded its audit, and retained both branches authored changes. Four regression suites, recognition validation and repository commit gates passed in preflight; target and release gates passed again after apply. No stash or cloud action used.
  ADR impact: No new architectural decision; refresh preserves ADR0041 and main governance.


- Commit: `13fe5145`
  Time UTC: 2026-10-23T16:12:47Z
  Message: feat(deploy): govern persistence safety declarations
  Summary: Adds reusable scope lifecycle, workload ownership, health/recovery, migration safety and credential lifecycle declaration controls; corrects secret-validation fail-closed behaviour; and records PostgreSQL persistence prerequisites.
  ADR impact: No new ADR; extends the existing deployment implementation plan and generic harness controls.


- Commit: `39f8bbc4d07a044cd5285836f4ca0842d16d85c9`
  Time UTC: 2026-10-23T18:40:35Z
  Message: feat(deploy): add persistence composition controls
  Summary: Adds reusable persistence diagnostic enforcement, lifecycle and secret/recovery controls, and a fake-backed provider-neutral persistence-capable core-server composition. No PostgreSQL resource, secret, adapter binding, image, or target mutation is included.
  ADR impact: No ADR: this checkpoint applies the already-recorded PostgreSQL selection without selecting a provider binding or changing deployed architecture.


- Commit: `9149d30d`
  Time UTC: 2026-10-23T18:57:57Z
  Message: feat(deploy): add persistence candidate programs
  Summary: Added the candidate server, server-mediated verifier, migration executable, PostgreSQL binding, migration lock, image definition, and local composition checks.
  ADR impact: none


- Commit: `f6cd5fbe`
  Time UTC: 2026-10-23T19:02:47Z
  Message: feat(deploy): declare persistence candidate scope
  Summary: Registered core-server-persistence as a validated candidate successor with separate runtime and migration credentials, a server-mediated verifier boundary, diagnostics, recovery declarations, and a local image-build command.
  ADR impact: none


- Commit: `bbf19a21`
  Time UTC: 2026-10-23T19:22:16Z
  Message: feat(deploy): add hosted persistence image qualification
  Summary: Added the protected-main GitHub Actions route for real Docker qualification, immutable persistence candidate publication, and ECR scan enforcement; corrected the image dependency closure.
  ADR impact: none


- Commit: `b4abc8cd`
  Time UTC: 2026-10-23T19:36:23Z
  Message: feat(deploy): add persistence provider candidate controls
  Summary: Added the private PostgreSQL candidate template, migration/runtime-principal contract, package closure checks, and OCI-child-manifest scan gate.
  ADR impact: covered by session ADR disposition


- Commit: `7ab8d070`
  Time UTC: 2026-10-23T19:37:26Z
  Message: feat(deploy): add persistence provider candidate controls
  Summary: Rebased checkpoint: private PostgreSQL candidate template, migration/runtime-principal contract, package closure checks, and OCI-child-manifest scan gate.
  ADR impact: covered by session ADR disposition


- Commit: `d9262f46`
  Time UTC: 2026-10-23T19:44:52Z
  Message: test(deploy): qualify persistence image against tls postgres
  Summary: Added the hosted disposable TLS PostgreSQL package qualification for migration, runtime DML, readiness, and runtime DDL denial.
  ADR impact: covered by session ADR disposition


- Commit: `c0815790`
  Time UTC: 2026-10-23T19:47:16Z
  Message: fix(deploy): complete postgres driver image closure
  Summary: Added pg-int8 and a build-stage require check after hosted TLS package qualification exposed the missing transitive dependency.
  ADR impact: covered by session ADR disposition


- Commit: `6132d8af8aca00b876cab1b79403da4fd82410a6`
  Time UTC: 2026-10-23T19:52:09Z
  Message: fix(persistence): allow bounded migration statement timeout
  Summary: Allows the declared bounded 240-second migration statement timeout while retaining one-minute connection and idle limits; adds acceptance and rejection regression coverage.
  ADR impact: covered by session ADR disposition


- Commit: `HEAD`
  Time UTC: 2026-10-23T20:07:58Z
  Message: fix(deploy): govern persistence image qualification
  Summary: Repairs the real TLS PostgreSQL package smoke and adds an enforced persistence-candidate package-custody route with delivery-access proof, scan, SBOM, provenance, and receipt.
  ADR impact: covered by session ADR disposition


- Commit: `52601cd98c8dacdecfafc78bd09328d24c24c3a8`
  Time UTC: 2026-10-23T20:08:12Z
  Message: fix(deploy): govern persistence image qualification
  Summary: Repairs the real TLS PostgreSQL package smoke and adds an enforced persistence-candidate package-custody route with delivery-access proof, scan, SBOM, provenance, and receipt.
  ADR impact: covered by session ADR disposition


- Commit: `d8ff3f8c0f5fdf6421e0245391ad5c74135447d5`
  Time UTC: 2026-10-23T20:27:30Z
  Message: feat(deploy): govern persistence candidate creation
  Summary: Added a fixed, target-bound persistence candidate route: live preflight, reviewable CloudFormation creation, one-shot migration, and server-mediated verification; local gates and live read-only preflight pass.
  ADR impact: covered by session ADR disposition


- Commit: `9225b536adec6a9273d37fa59413b545eb524681`
  Time UTC: 2026-10-23T20:28:31Z
  Message: fix(deploy): wire persistence inventory gate
  Summary: Corrected the candidate creation route so its automatic active-scope inventory gate receives the canonical scope-root path; the focused gate and target-control smoke pass.
  ADR impact: covered by session ADR disposition


- Commit: `0645e298789fb7cfd3f36ecea06f496b7f5cf3c3`
  Time UTC: 2026-10-23T20:30:31Z
  Message: fix(deploy): reconcile empty aws acknowledgements
  Summary: Updated the shared persistence AWS response decoder and regression suite so an empty successful CloudFormation acknowledgement is reconciled through its named operation instead of treated as a reason to retry.
  ADR impact: covered by session ADR disposition


- Commit: `f9baa91fc7afaf28c52e4cb3a42e0180f6efbb0c`
  Time UTC: 2026-10-23T20:47:24Z
  Message: fix(deploy): allow private persistence image layers
  Summary: Captured the live candidate image-pull failure and added the managed S3 artifact prefix-list preflight, CloudFormation parameter, server/migration egress rules, and regression proof alongside existing ECR endpoint controls.
  ADR impact: covered by session ADR disposition


- Commit: `6c6d9ecaa18706675a2348f1af0950c82e08aaf6`
  Time UTC: 2026-10-23T21:15:53Z
  Message: fix(deploy): govern failed persistence candidate retirement
  Summary: Added a fixed failed-candidate retirement control, repaired target package metadata gating, and preserved final snapshot retention before retrying the persistence candidate.
  ADR impact: covered by session ADR disposition


- Commit: `253b4eace9d59b80cf36d231fcf0517cbbfa4ea4`
  Time UTC: 2026-10-23T21:16:12Z
  Message: fix(deploy): govern failed persistence candidate retirement
  Summary: Rebased task commit onto origin/main; adds the fixed failed-candidate retirement control, target package metadata repair, and regression coverage.
  ADR impact: covered by session ADR disposition


- Commit: `253b4eacf463f2e3fd52f3c7f0a2ed6ce225bb39`
  Time UTC: 2026-10-23T21:16:33Z
  Message: fix(deploy): govern failed persistence candidate retirement
  Summary: Corrected rebased task SHA: fixed failed-candidate retirement control, target package metadata repair, and regression coverage.
  ADR impact: covered by session ADR disposition


- Commit: `284df87b8e02b84a5b72478002e94e46079ed7cd`
  Time UTC: 2026-10-23T21:39:37Z
  Message: fix(deploy): reconcile interrupted persistence migrations
  Summary: Added a current-deployment, no-replay reconciliation route for an interrupted migration controller and regression coverage for identity and terminal-state refusal.
  ADR impact: covered by session ADR disposition


- Commit: `cc866c67e8c76c1e1bdee3f8b68d1de38a6028b5`
  Time UTC: 2026-10-23T21:39:47Z
  Message: fix(deploy): reconcile interrupted persistence migrations
  Summary: Rebased task commit adds the current-deployment, no-replay migration reconciliation control and its regression coverage.
  ADR impact: covered by session ADR disposition


- Commit: `0259d4c09210ae45a4f1c6e13c6648bc9c5f5b53`
  Time UTC: 2026-10-23T21:43:39Z
  Message: fix(deploy): connect private persistence verifier
  Summary: Added the explicit verifier-to-current-server egress rule and a no-replay verifier reconciliation route after the first verifier safely exposed the missing route.
  ADR impact: covered by session ADR disposition


- Commit: `a1d6de9a7f97f0755864b72d53488c2602bc9160`
  Time UTC: 2026-10-23T21:43:48Z
  Message: fix(deploy): connect private persistence verifier
  Summary: Rebased task commit adds explicit verifier-to-current-server egress and no-replay verifier reconciliation after the safe route failure.
  ADR impact: covered by session ADR disposition


- Commit: `ae4ea090`
  Time UTC: 2026-10-23T21:48:23Z
  Message: fix(deploy): govern private verifier route updates
  Summary: Adds a constrained reviewed CloudFormation UPDATE route allowing only the current verifier-to-server egress security-group rule, with focused smoke coverage.
  ADR impact: covered by session ADR disposition


- Commit: `6cd61e15`
  Time UTC: 2026-10-23T21:48:41Z
  Message: fix(deploy): govern private verifier route updates
  Summary: Rebased task commit: constrained reviewed CloudFormation UPDATE route allowing only the verifier-to-server egress security-group rule.
  ADR impact: covered by session ADR disposition


- Commit: `c7a84aa0`
  Time UTC: 2026-10-23T21:51:55Z
  Message: fix(deploy): reconcile verifier route change sets
  Summary: Makes the bounded verifier route correction reuse its deterministic change set and await CloudFormation review visibility rather than rejecting a normal propagation gap.
  ADR impact: covered by session ADR disposition


- Commit: `94272a0d`
  Time UTC: 2026-10-23T21:52:03Z
  Message: fix(deploy): reconcile verifier route change sets
  Summary: Rebased task commit: the fixed route control awaits the existing bounded change set becoming reviewable and never creates a duplicate.
  ADR impact: covered by session ADR disposition


- Commit: `ea645943`
  Time UTC: 2026-10-23T21:58:24Z
  Message: feat(deploy): govern persistence server replacement
  Summary: Adds a fixed target-scoped replacement rehearsal that records the old/new server task and requires a separate fresh private read proof.
  ADR impact: covered by session ADR disposition


- Commit: `74756f9b`
  Time UTC: 2026-10-23T21:58:32Z
  Message: feat(deploy): govern persistence server replacement
  Summary: Rebased task commit: fixed target-scoped server replacement with a required subsequent read proof.
  ADR impact: covered by session ADR disposition


- Commit: `d47f1fd2`
  Time UTC: 2026-10-23T22:00:46Z
  Message: fix(deploy): reconcile persistence replacements
  Summary: Adds a no-replay reconciliation route for a replacement controller interrupted after it stopped the original task.
  ADR impact: covered by session ADR disposition


- Commit: `b9f30372`
  Time UTC: 2026-10-23T22:00:55Z
  Message: fix(deploy): reconcile persistence replacements
  Summary: Rebased task commit: reconciles only an exact stopped task with the governed replacement reason and a distinct healthy replacement.
  ADR impact: covered by session ADR disposition


- Commit: `5dced535`
  Time UTC: 2026-10-23T22:09:28Z
  Message: feat(deploy): govern persistence release transitions
  Summary: Adds a receipt-bound UPDATE/rollback route that permits only persistence ECS task-definition and service changes.
  ADR impact: covered by session ADR disposition


- Commit: `dae6f542`
  Time UTC: 2026-10-23T22:24:21Z
  Message: feat(deploy): govern persistence recovery points
  Summary: Adds a fixed target-bound encrypted recovery-point snapshot command with live service, database and budget checks.
  ADR impact: covered by session ADR disposition


- Commit: `14f57f56`
  Time UTC: 2026-10-23T22:24:31Z
  Message: feat(deploy): govern persistence recovery points
  Summary: Rebased task commit: fixed encrypted target recovery-point control.
  ADR impact: covered by session ADR disposition


- Commit: `001014b6`
  Time UTC: 2026-10-23T22:42:00Z
  Message: govern isolated persistence restore proof
  Summary: Added a qualified restore-verifier image entrypoint, isolated restored-database network surface, workload declarations, recovery rehearsal control, and shared-runtime-secret validation rule; local and Docker PostgreSQL/TLS checks pass.
  ADR impact: covered by session ADR disposition


- Commit: `2772a57e`
  Time UTC: 2026-10-23T22:42:31Z
  Message: govern isolated persistence restore proof
  Summary: Rebased onto current origin/main; restore-verifier task commit now resolves to 2772a57e.
  ADR impact: covered by session ADR disposition


- Commit: `d424ec82`
  Time UTC: 2026-10-23T22:46:34Z
  Message: bound persistence restoration surface update
  Summary: Added a restore-specific image parameter and change-set control that permits only new isolated restoration verifier resources; it cannot modify the live ECS service or existing task definitions.
  ADR impact: covered by session ADR disposition


- Commit: `f8a320c0`
  Time UTC: 2026-10-23T22:46:42Z
  Message: bound persistence restoration surface update
  Summary: Rebased onto current main; exact bounded restoration-surface task commit is f8a320c0.
  ADR impact: covered by session ADR disposition


- Commit: `140e42c3`
  Time UTC: 2026-10-23T22:47:20Z
  Message: govern restoration surface command wrapper
  Summary: Added the required artifact header after the governed runner correctly rejected the wrapper.
  ADR impact: covered by session ADR disposition


- Commit: `14798019`
  Time UTC: 2026-10-24T09:04:27Z
  Message: fix(deploy): reconcile stopped restore verifiers
  Summary: Correct the isolated restore controller to validate AWS lower-case task-definition fields and reconcile stopped verifier tasks before submitting another; add focused regression coverage.
  ADR impact: No ADR: this repairs an existing control's AWS response parsing and reconciliation behavior without changing the architecture.


- Commit: e3c7a09e
  Summary: Rebased restore-controller task commit from 14798019 onto origin/main; current durable task SHA is e3c7a09e.
  ADR impact: covered by session ADR disposition


- Commit: `HEAD`
  Time UTC: 2026-10-24T09:17:50Z
  Message: fix(deploy): isolate restore verifier task identity
  Summary: Derive the isolated restore verifier ECS identity from the restored database resource, preventing historical tasks from a prior restore of the same snapshot from blocking reconciliation.
  ADR impact: No ADR: this is a bounded controller identity correction.


- Commit: `adc9c83655f4da156b785c506b8b70e58d608d25`
  Time UTC: 2026-10-24T09:51:39Z
  Message: feat(deploy): rehearse persistence credential lifecycle
  Summary: Adds governed runtime credential rotation/revocation rehearsal, server health verification, migration operation controls, lower-case ECS verifier isolation parsing, local package proof, and reusable pg idle-client error handling. Adapter, composition, package, harness, target and release-contract gates passed locally.
  ADR impact: No ADR: applies existing persistence lifecycle and recovery decisions.


- Commit: `aee8bad27be41aa90dfb627a20a42fb4464e5ef2`
  Time UTC: 2026-10-24T09:58:17Z
  Message: fix(deploy): bind persistence restore verifier digest
  Summary: Corrects the clean-create and healthy-stack update release controls to provide the template-required RestoreVerifierImageDigest from the same qualified immutable candidate digest; Python compile and pre-commit gates passed.
  ADR impact: No ADR: repairs an existing target-template/controller contract.



- Commit: `427847f6`
  Time UTC: 2026-10-24T10:28:16Z
  Message: fix(deploy): bound persistence controller observations
  Summary: Bound persistence observer commands and corrected verifier-role smoke-test boundary.
  ADR impact: No ADR: bounded controller and regression correction.


- Commit: `f3d89cd5`
  Time UTC: 2026-10-24T10:57:38Z
  Message: fix(deploy): bound credential recovery continuation
  Summary: Adds a non-replaying recovery-secret boundary and bounded AWS observer handling for persistence lifecycle controllers.
  ADR impact: No ADR: repairs governed continuation and observer behavior.


- Commit: `f10d6cd2`
  Time UTC: 2026-10-24T11:27:11Z
  Message: feat: prove runtime postgres privilege live
  Summary: Added a receipt-governed migration-task operation that verifies runtime DML succeeds and PostgreSQL rejects structural DDL in rolled-back transactions.
  ADR impact: covered by session ADR disposition


- Commit: `5942afe2`
  Time UTC: 2026-10-24T13:58:38Z
  Message: fix(deploy): fail closed on persistence revocation
  Summary: Added fail-closed runtime-session termination evidence, bounded fresh restore naming, and target-bound acceptance evidence collection.
  ADR impact: covered by session ADR disposition


- Commit: pending
  Summary: Record durable persistence proof receipts, collect accepted release evidence without depending on aged ECS tasks, and promote core-server-persistence to the active scope.
  ADR impact: No ADR: bounded evidence-retention and lifecycle-control completion within the approved PostgreSQL persistence slice.


- Commit: `21d02a53`
  Time UTC: 2026-10-24T16:05:00Z
  Message: feat(deploy): retain persistence acceptance proofs
  Summary: Record durable task-proof receipts, accepted persistence release evidence, and lifecycle promotion without relying on aged ECS task records.
  ADR impact: No ADR: bounded evidence-retention and lifecycle-control completion within the approved PostgreSQL persistence slice.


- Commit: `a7d45b7a`
  Time UTC: 2026-10-25T13:24:11Z
  Message: fix(deploy): reconcile current release reference
  Summary: Corrected only the mutable current accepted-release pointer to hash the exact immutable history bytes; succession validation and target smoke now pass.
  ADR impact: No ADR: this is an integrity-pointer correction under existing release-succession design.


- Commit: `HEAD`
  Time UTC: 2026-10-25T13:27:35Z
  Message: fix(deploy): correct persistence image closure
  Summary: Removed the nonexistent @protobufjs copy from the persistence image source closure after CI caught it before any AWS or ECR mutation.
  ADR impact: No ADR: narrow package assembly correction.


- Commit: `HEAD`
  Time UTC: 2026-10-25T13:30:47Z
  Message: fix(deploy): trim persistence image runtime closure
  Summary: Removed nonexistent unscoped dependency copies; isolated runtime closure now loads actual pg and OpenTelemetry modules.
  ADR impact: No ADR: package source-closure correction.


- Commit: `f8a16e683911c6906ca834e45f48ee70025601f1`
  Time UTC: 2026-10-25T13:52:02Z
  Message: fix(deploy): correct observability delivery route
  Summary: Corrected ADOT delivery to use EMF through the existing private Logs endpoint, declared target-owned notification binding, and classified named absent change sets safely; local target and observability gates pass.
  ADR impact: covered by session ADR disposition


- Commit: `df2ca76296f4ccae7d5b752d7ae0725c1a689e07`
  Time UTC: 2026-10-25T14:06:16Z
  Message: feat(deploy): add private collector custody route
  Summary: Added the target-private ADOT collector package contract, protected manual custody workflow, static guard and negative regression, plus target catalogue and declaration-gate routing. Local package, target, deployment-control, and retained-acceptance checks passed; publication and live observability proof remain pending.
  ADR impact: covered by session ADR disposition


- Commit: `0360770f7c82b090716c445dba31e7226b1de95a`
  Time UTC: 2026-10-25T14:09:06Z
  Message: Merge main into chat branch
  Summary: Integrated the newer accepted persistence implementation from main with the collector custody route. Resolved only genuine overlaps by retaining main's newer controller/runtime implementation and reran collector, observability, target, and fixed deployment-controller checks successfully.
  ADR impact: covered by session ADR disposition


- Commit: `c15677c2b50a92b3d835050c374818d7e0a20a9a`
  Time UTC: 2026-10-25T14:14:09Z
  Message: fix(deploy): scan single-manifest collector images
  Summary: Corrected the collector scan selector to resolve either a single OCI manifest or exactly one amd64 child of an OCI index. Regression coverage and a read-only check against the actual mirrored digest passed; the failed first workflow remains unaccepted evidence.
  ADR impact: covered by session ADR disposition


- Commit: `db4cb76763a905ce6be2b7efd9ec8325a670b87b`
  Time UTC: 2026-10-25T14:22:11Z
  Message: fix(deploy): isolate collector vulnerability scan
  Summary: Replaced unsupported ECR Basic scanning with a pinned portable scanner in a separate unprivileged public-source job, while preserving protected OIDC publication as a dependent job. Receipt validation now allows exactly one explicit native or portable scanner proof.
  ADR impact: covered by session ADR disposition


- Commit: `7defa885fb1fece769b15f170af298953c25adfd`
  Time UTC: 2026-10-25T14:26:24Z
  Message: fix(deploy): scan mirrored collector payload
  Summary: Collector custody now mirrors the pinned source, exports the exact private image as a one-day scan input, scans that payload in an unprivileged job, and only afterward issues the protected SBOM/provenance/receipt. No scan result or failed attempt is accepted as custody evidence.
  ADR impact: covered by session ADR disposition


- Commit: `d9cd2362`
  Time UTC: 2026-10-25T15:18:21Z
  Message: fix(deploy): build minimal observability collector
  Summary: Replaced the vulnerable vendor collector mirror with a pinned minimal source build, archive-integrity handoff, unprivileged scan, and private publication only after scan success.
  ADR impact: covered by session ADR disposition


- Commit: `7d9aef87`
  Time UTC: 2026-10-25T15:33:22Z
  Message: fix(deploy): validate collector custody receipt
  Summary: Corrected collector receipt check vocabulary so the final custody gate accepts the governed generic receipt.
  ADR impact: covered by session ADR disposition


- Commit: `8c06510178790fdabc0fd3a8899085f867f947e8`
  Time UTC: 2026-10-25T15:39:53Z
  Message: fix(deploy): bind permissions update to collector custody
  Summary: Require the reviewed permissions update to bind qualified collector custody and a non-retained alert recipient.
  ADR impact: covered by session ADR disposition


- Commit: `50009a89da1782ad7575d1346a0de88dcf3b0466`
  Time UTC: 2026-10-25T15:41:53Z
  Message: fix(deploy): accept governed alert address
  Summary: Corrected the CloudFormation alert-address regex after AWS rejected the POSIX character-class form before change-set creation.
  ADR impact: covered by session ADR disposition


- Commit: `1cd616751f0658eca485411b2a942d0c29668d8b`
  Time UTC: 2026-10-25T15:43:22Z
  Message: fix(deploy): use portable alert address pattern
  Summary: Replaced the double-escaped CloudFormation alert pattern after AWS validated it as a literal backslash requirement.
  ADR impact: covered by session ADR disposition


- Commit: `b12f2d75`
  Time UTC: 2026-10-25T15:54:11Z
  Message: fix(deploy): recover failed permissions change sets
  Summary: Corrected the permission update change-set allowlist and added safe failed-change-set retirement with regression coverage.
  ADR impact: covered by session ADR disposition


- Commit: `535815b0`
  Time UTC: 2026-10-25T16:00:07Z
  Message: refactor(deploy): phase persistence observability rollout
  Summary: Separated the database-permission update from conditional observability activation so each is independently reviewed and recoverable.
  ADR impact: covered by session ADR disposition


- Commit: `324e0680`
  Time UTC: 2026-10-25T16:04:28Z
  Message: fix(deploy): validate phased observability declaration
  Summary: Validated explicit observability activation separately from the database-permission phase and repaired its regression fixture topology.
  ADR impact: covered by session ADR disposition


- Commit: `dadc6360`
  Time UTC: 2026-10-25T18:51:14Z
  Message: feat(deploy): harden persistence IAM lifecycle
  Summary: Implements provider-neutral workload-identity lifecycle contracts and validators, RDS IAM token-per-connection adapter path, bounded administrator/revocation/recovery operations, isolated restore IAM binding, restricted disposable package qualification, durable retained proof acceptance, and diagnostics integration. Local declaration, target, composition, controller, acceptance, diagnostics, observability, check-selection, metadata, and staged gates passed; AWS IAM and incident closure remain live-proof work.
  ADR impact: No ADR: bounded implementation and corrective integration under the existing PostgreSQL persistence and observability decisions.


- Commit: `be024ef9`
  Time UTC: 2026-10-25T19:03:10Z
  Message: fix(deploy): align persistence permission update review
  Summary: Replaces the stale CREATE-era permission-surface allowlist with the exact reviewed UPDATE delta for the active stack: four task-role additions plus explicit RDS/IAM/secret/task/service modifications. Fixed-control and controller regressions pass; the previously created change set remains unexecuted.
  ADR impact: No ADR: narrow safety correction to an existing governed controller.


- Commit: `6c33ab8f`
  Time UTC: 2026-10-25T19:18:27Z
  Message: fix(deploy): converge legacy IAM runtime role
  Summary: Normalizes only a non-elevated inherited password-era runtime role to the bounded no-inherit IAM login profile; retains rejection of elevated roles and proves no password or verifier SQL is emitted.
  ADR impact: No ADR: bounded implementation correction under the existing IAM lifecycle decision.


- Commit: `cfa2bd60`
  Time UTC: 2026-10-25T19:26:24Z
  Message: fix(deploy): preserve IAM revocation boundary
  Summary: Narrows legacy role convergence to INHERIT only, retains fail-closed elevated-role checks, and prevents bootstrap from undoing NOLOGIN revocation; adds regression coverage.
  ADR impact: No ADR: a focused correction within the existing IAM lifecycle model.


- Commit: `52b0a15c`
  Time UTC: 2026-10-25T19:34:55Z
  Message: fix(deploy): bind persistence support image
  Summary: Binds the persistence server, support program, and restoration verifier to one qualified immutable digest for create and update paths; change-set review and reconciliation now reject a support-image mismatch.
  ADR impact: No ADR: bounded correction to the existing qualified-release controller.


- Commit: `HEAD`
  Time UTC: 2026-10-25T19:40:11Z
  Message: fix(deploy): preserve update parameter state
  Summary: Makes qualified persistence update review verify all controller-owned parameters and preserve every unowned CloudFormation parameter from the healthy stack, including template defaults.
  ADR impact: No ADR: bounded correction to the existing qualified-release controller.


- Commit: `HEAD`
  Time UTC: 2026-10-25T19:43:31Z
  Message: fix(deploy): reconcile executed update change sets
  Summary: Recognizes CloudFormation's removed executed change set only when the current stack proves the exact candidate parameter identity; retains no-retry and mismatch uncertainty.
  ADR impact: No ADR: bounded reconciliation correction for an existing provider lifecycle.


- Commit: `HEAD`
  Time UTC: 2026-10-25T19:51:46Z
  Message: fix(deploy): classify migration task failures
  Summary: Parses only closed migration rejection codes and failure classes from terminal task logs; raw task output and sensitive fields remain excluded from controller reports.
  ADR impact: No ADR: bounded safe-diagnostics correction under existing deployment standards.


- Commit: `HEAD`
  Time UTC: 2026-10-25T20:06:29Z
  Message: Require a read-only, receipt-backed migration-history observation before a failed persistence migration can be replayed.
  Summary: Adds the state observer across the runnable administration program, reusable health contract, exact AWS workflow, package proof, and controller regression coverage.
  ADR impact: covered by session ADR disposition


- Commit: `HEAD`
  Time UTC: 2026-10-25T20:24:33Z
  Message: fix(deploy): observe migration state as owner
  Summary: Repaired the migration-state observer so the constrained administrator assumes the migration owner only within a read-only transaction. Local composition, lifecycle controller, health/recovery, secret and diagnostic validations passed; Docker Desktop credential-helper failure prevents local package build before Docker starts.
  ADR impact: covered by session ADR disposition


- Commit: `HEAD`
  Time UTC: 2026-10-25T20:45:16Z
  Message: fix(deploy): retain applied migration state evidence
  Summary: Accepted migration-state observation distinguishes replay permission from already-applied evidence and routes the durable receipt into acceptance.
  ADR impact: covered by session ADR disposition


- Commit: `HEAD`
  Time UTC: 2026-10-25T20:58:11Z
  Message: fix(deploy): classify persistence privilege probe outcomes
  Summary: Preserve allowlisted privilege-probe outcomes while continuing to suppress provider detail.
  ADR impact: covered by session ADR disposition


- Commit: `HEAD`
  Time UTC: 2026-10-25T22:32:56Z
  Message: --summary
  Summary: Retained governed persistence proof receipts, added qualified rollback-predecessor compatibility records, and made isolated restore verification safe and lifecycle-aware.
  ADR impact: covered by session ADR disposition


- Commit: `8ff26fd6`
  Time UTC: 2026-10-25T23:11:55Z
  Message: fix: classify isolated restore verifier failures safely
  Summary: Added closed allowlisted restore failure mapping, causal machine-code handling, controller rejection receipts, and focused regression coverage.
  ADR impact: No ADR: bounded safe-diagnostic correction under the current persistence recovery decision.


- Commit: `1b3d81cd`
  Time UTC: 2026-10-25T23:11:55Z
  Message: test: isolate synthetic deployment diagnostics
  Summary: Kept controller-regression diagnostics in a temporary directory so synthetic tests cannot contaminate retained live-evidence storage.
  ADR impact: No ADR: test isolation correction.


- Commit: `ed781c64`
  Time UTC: 2026-10-25T23:11:55Z
  Message: evidence: retain persistence proof receipts
  Summary: Committed 24 integrity-validated live proof receipts, two safe operation diagnostics, and immutable qualified rollback-compatibility records.
  ADR impact: No ADR: durable evidence under the existing acceptance model.


- Commit: `b154eea4`
  Time UTC: 2026-10-25T23:56:16Z
  Message: fix(deploy): stabilize isolated restore identity
  Summary: Added a bounded, policy-stability recheck before the isolated restore verifier launches and retained five current-image live proof receipts for migration state, effective privilege, runtime IAM access, health, and read.
  ADR impact: No ADR: bounded recovery-controller correction under the existing persistence IAM and restore design.


- Commit: `aee7340b`
  Time UTC: 2026-10-26T00:05:21Z
  Message: fix(deploy): classify isolated restore boundaries
  Summary: Separated restore IAM-token, connection and query failures into closed safe diagnostic categories; added composition and controller regression coverage; confirmed temporary restore cleanup.
  ADR impact: covered by session ADR disposition


- Commit: `5a962e64858476e87fb793f7c2b55233c584d0ca`
  Time UTC: 2026-10-26T00:33:06Z
  Message: feat(deploy): retain persistence proof evidence
  Summary: Added integrity-checked retained package receipts and a closed restore-verifier-only proof applicability route; acceptance keeps current-state checks and isolated restore fresh.
  ADR impact: No ADR required: this is a bounded correction to the existing release-evidence architecture.


- Commit: `408d7734`
  Time UTC: 2026-10-26T01:05:07Z
  Message: fix(deploy): classify isolated restore transport boundary
  Summary: Adds a credential-free bounded TCP preflight to the isolated restoration verifier, distinguishes a closed transport boundary from an opaque post-transport PostgreSQL/TLS handshake, accepts only those closed result codes in the governed restore controller, and proves the classification plus transport fixture locally.
  ADR impact: No ADR: this is an implementation refinement within the existing isolated-restore diagnostic and recovery decision.


- Commit: `HEAD`
  Time UTC: 2026-10-26T01:16:35Z
  Message: fix(deploy): bind proof reuse to image inputs
  Summary: Retains package custody receipt 40252659734 and its target proof-applicability record. Applicability now compares actual core-server-persistence package input paths, rejects any non-restore verifier image input change, and retains the full source delta for audit.
  ADR impact: No ADR: this corrects the existing durable-evidence applicability control rather than changing the release architecture.


- Commit: `HEAD`
  Time UTC: 2026-10-26T01:42:24Z
  Message: fix(deploy): probe restore verifier TLS boundary
  Summary: Adds a credential-free PostgreSQL SSL/TLS preflight to the isolated restore verifier. It retains closed transport, TLS negotiation, TLS trust and post-TLS handshake outcomes, with composition and restore-controller checks passing.
  ADR impact: No ADR: focused diagnostic refinement within the established isolated recovery proof.


- Commit: `1ab65b6c`
  Time UTC: 2026-10-26T02:41:35Z
  Message: evidence(deploy): retain restore handshake rejection
  Summary: Retained the qualified package receipt, image-input applicability record, and closed isolated restore rejection after source-safe cleanup; recovery acceptance remains unproven.
  ADR impact: No ADR: factual live evidence under the existing durable proof model.


- Commit: `HEAD`
  Time UTC: 2026-10-26T02:45:13Z
  Message: fix(deploy): require restore PostgreSQL log export
  Summary: Requires each isolated restore to enable and prove the existing PostgreSQL CloudWatch log export before a verifier can run.
  ADR impact: No ADR: bounded recovery diagnostic source correction.


- Commit: `ca0d679f`
  Time UTC: 2026-10-26T02:56:39Z
  Message: fix(deploy): classify isolated restore server logs safely
  Summary: Require PostgreSQL export on derived restores and retain only a bounded server-log classification for a rejected verifier.
  ADR impact: No ADR impact; target-scoped recovery diagnostic hardening.


- Commit: `b3c8e547`
  Time UTC: 2026-10-26T07:19:16Z
  Message: fix(deploy): recognize RDS log export configuration
  Summary: Treat RDS configuring-log-exports as an ordinary in-flight restore state and prove it in restore-controller regression.
  ADR impact: No ADR impact; provider lifecycle-state correction.


- Commit: `ed63c025`
  Time UTC: 2026-10-26T07:40:59Z
  Message: fix(deploy): resume restore identity stabilization
  Summary: Replaced the controller's blocking identity-propagation delay with a bounded exact CloudTrail observation before the one allowed restore verifier launch.
  ADR impact: No ADR impact; governed isolated-restore reconciliation remains target-specific.


- Commit: `3bcfe650`
  Time UTC: 2026-10-26T07:41:28Z
  Message: test(deploy): harden restore identity observation
  Summary: Added malformed, stale, and mismatched CloudTrail observation regressions; retained the closed historical restore rejection diagnostic after source-health and cleanup reconciliation.
  ADR impact: No ADR impact; this is a target-specific recovery-controller safety correction.


- Commit: `749e869827d7a7e3affbf93899f60f43b5c0b6d7`
  Time UTC: 2026-10-26T08:57:51Z
  Message: feat(deploy): compose private observability collector
  Summary: Added a dedicated private OTLP collector, target declaration and guarded update controller; local composition, adapter, declaration, package-workflow, target and template checks pass.
  ADR impact: No new ADR: this implements the established separate-identity collector decision.


- Commit: `e5bbda7c`
  Time UTC: 2026-10-26T09:59:19Z
  Message: fix(deploy): govern collector metric delivery repair
  Summary: Adds a healthy-baseline, exact-change-set controller mode for the corrected readiness metric configuration. It permits only collector task-definition and service modification, with regression tests and workflow guidance.
  ADR impact: No ADR: this is an implementation correction within the accepted observability deployment boundary.


- Commit: `962cddd1`
  Time UTC: 2026-10-26T10:49:35Z
  Message: feat(deploy): retain observability readiness proof
  Summary: Added durable, integrity-checked readiness failure, notification, and recovery receipts; wired acceptance to retained receipts while preserving fresh current-state checks.
  ADR impact: No ADR: this is a bounded target-scoped extension of existing receipt and acceptance controls.


- Commit: `8bc53dd8`
  Time UTC: 2026-10-26T13:28:56Z
  Message: fix(deploy): retain persistence acceptance evidence
  Summary: Added durable retained proof receipts and candidate acceptance evidence, corrected isolated-restore observation handling, and preserved the rejected restore result without repeating it.
  ADR impact: Covered by existing deployment evidence and recovery governance; no ADR change.

## Main Refresh Conflicts



- Path: `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`
  Type: `generated-artifact-conflict`
  Mode: deterministic
  Reason: Generator-owned recognition index. The classifier fell back to normal-repo-conflict; file metadata and the governed generator establish reproducible generated output.
  Action: Regenerated recognition outputs from combined source metadata and retained authored changes from both branches. Trimmed four empty metadata-field trailing spaces in the incoming Oct22 session log for staged whitespace validation.
  Preflight branch: `agentic/preflight/chat-2026-10-05-09-59-can-you-walk-me-through-wh-57bd4c6fdbdb/20261022222226`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-10-05-09-59-can-you-walk-me-through-wh-57bd4c6fdbdb-20261022222226`
  Files changed by resolution: Generated artifact index; this session conflict audit; incoming Oct22 log whitespace only.
  Checks: Secret, active inventory, target declaration and release-contract suites passed. Recognition freshness/validity and repository commit extension passed; staged whitespace rechecked after empty-field normalization.

## ADR Disposition

ADR needed: yes
ADR path: docs/04.deploy/adrs/0041-select-postgresql-for-core-platform-persistence-proof.md
Reason: Record the PostgreSQL selection already stated in the programme for this target; staging ADR 0033 does not cover it. Resource design and live authority remain deferred.

## Session Metrics

Raised at UTC: 2026-10-05T08:59:29Z
Latest commit at UTC: 2026-10-26T13:28:56Z
Latest commit SHA: 8bc53dd8
Chat duration: 1830567s (21:04:29:27)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- 2026-10-26: The target alert subscription was confirmed and a delivery was
  confirmed by the user.  The persistence candidate remains unaccepted while
  the final isolated native-restore proof is in progress.  A fresh encrypted
  recovery snapshot, `kanbien-core-platform-persistence-recovery-20261026-r1`,
  was created after the retained accepted record proof and its isolated,
  private restore was submitted.  It has no connection to the source service.
  The verifier and cleanup will be reconciled from the exact provider state;
  they must not be duplicated if a controller call is interrupted.
- 2026-10-26: Acceptance succession was corrected before final collection.
  Each candidate now integrity-binds the package custody, source-record,
  observability, compatibility/applicability where present, and terminal proof
  receipts below allowlisted durable evidence folders.  The generic successor
  controller rejects mismatched receipt counts and altered retained evidence;
  historical accepted-release records remain immutable.
- 2026-10-26: The isolated restore against recovery snapshot
  `kanbien-core-platform-persistence-recovery-20261026-r1` reached a verified
  private, encrypted, IAM-authenticated restored instance.  Its one permitted
  restoration verifier rejected with the closed code
  `KANBIEN_CORE_PERSISTENCE_RESTORE_DATABASE_HANDSHAKE_UNAVAILABLE`.  The
  target-owned RDS export yielded only the safe
  `persistence-restore-server-log-no-classified-event` classification.  The
  rejected operation diagnostic is retained; no restore proof was accepted or
  replayed.  The temporary instance-specific IAM policy was removed and the
  restored instance was confirmed absent.  The source database and candidate
  ECS service remain healthy.
- 2026-10-26: The restore controller initially checked CloudTrail in
  `eu-west-1` for a global IAM `PutRolePolicy` event.  Event History holds the
  exact event in `us-east-1`; the controller now uses an explicit regional
  adapter for that global-event observation, with a regression fixture.  This
  allowed reconciliation of the already-submitted policy without recreating
  it.
- 2026-10-26: Promoted the verified isolated-restore TLS-boundary correction
  to `origin/main` by normal fast-forward. The source and promoted commit is
  `5c00b8f211c0bef7519cae05a08c0134eeda0030`; the clean promotion worktree
  ran the restore-controller, proof-applicability, and persistence-composition
  regression suites before the final fetch, eligibility check, and push.
- 2026-10-21: Refreshed this clean chat branch by rebasing it onto local `main`
  (`c1ad31a0`) after fetching remote references. The branch moved from
  `3bfce6a8` to `c1ad31a0`; Git reported no conflicts, no stash was used, and
  the final comparison with local `main` is `0 behind, 0 ahead`. This was a
  user-approved history rewrite; no task commit, merge to `main`, or remote
  push occurred.
- 2026-10-21: Promoted the proven `kanbien-core-platform/bootstrap-runtime`
  route and its factual declarations from `draft` to `active`. The implementation
  plan now routes readers to the adopted lifecycle-first tree and explicitly
  treats its earlier provisional layout as historical context. Metadata, target
  declaration, runnable-program, package-custody, release-contract, and fixed
  target-control smoke checks passed. No cloud or GitHub mutation occurred.
