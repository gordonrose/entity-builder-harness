<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.lesson-plans.0002-entity-smoke-release-retrospective
  version: 2
  status: draft
  created_on: "2026-11-14"
  updated_on: "2026-11-15"
  layer: 05.education
  domain: education
  disciplines: [agentic, architecture, sre]
  kind: guide
  purpose: Track a user-led review of the 34 release mistakes with questions, answers, evidence and separately recorded follow-up decisions.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Entity smoke release retrospective lesson plan

We will review the 34 mistakes from the preceding conversation one at a time.
The aim is to understand what I did wrong, how it delayed the release, what
should have happened, and what evidence would demonstrate an improvement.
The responsibility for those mistakes remains mine; these lessons are not a
list of things you should have known or supervised.

## Progress

- Current position: lesson 1, discussing reuse of the PostgreSQL release route.
- Lessons reviewed: 0 of 34.
- Questions recorded: 2, answered awaiting your confirmation.
- Next discussion: your follow-ups on what was already proved, what was tied
  to the original workload, and what would demonstrate safe reuse next time.
- Pace: one lesson at a time, with as many questions as you need. No deadline
  and no automatic progression.

## How we will work

For each lesson I will:

1. Describe the actual incident in plain language and define unfamiliar terms.
2. Show the relevant example from this repo before explaining the wider idea.
3. Explain the cause, consequence and what I should have done differently.
4. Take your questions and record them with their answers and supporting evidence.
5. Separate what was fixed from what is still unknown or only proposed.
6. Record a short takeaway and move on when you say you are ready.

The questions in the roadmap are suggested starting prompts, not questions
you have already asked. Your actual questions belong in the question log below.
An answer from me does not automatically mean a question is resolved for you.

Lesson status: **Not started**, **Discussing**, **Questions open**, or **Reviewed**.
Reviewed means you are ready to move on; it does not mean any proposed engineering
work has been approved, implemented or verified. We can reopen a lesson later.

## Roadmap

The numbering matches the 34-item mistake list in our conversation. Lesson 1
is being discussed; mentioning related topics does not mark later lessons reviewed.

| No. | Mistake to examine | Suggested starting prompt | Status |
| --- | --- | --- | --- |
| 1 | No complete release path established upfront | What should have been connected and checked before starting? | Discussing |
| 2 | Local success treated as stronger evidence than it was | What does a local test prove, and what does it not prove? | Not started |
| 3 | Missing compiler mapping and runtime shim | What must be included to turn working source code into a runnable package? | Not started |
| 4 | Diagnostic identifier did not match its owner | What is diagnostic ownership, and why did this mismatch block a check? | Not started |
| 5 | Confused explanations of existing diagnostics | What was already present, and what did I wrongly suggest was missing? | Not started |
| 6 | Established feature organisation not followed initially | How do contract, transport, domain, persistence and services fit together? | Not started |
| 7 | Contradictory preflight prerequisites | How can a prerequisite become impossible under its own rules? | Not started |
| 8 | Wrong administrator and runtime access assumption | Who sets permissions, and who should prove runtime access? | Not started |
| 9 | Expected failure states not governed upfront | Why must recovery tests deliberately observe an unhealthy dependency? | Not started |
| 10 | No usable restore environment cleanup path | How should we prove recovery and safely remove disposable resources? | Not started |
| 11 | Collector and acceptance created a deadlock | Why did generated proof files prevent acceptance? | Not started |
| 12 | Tool changes unnecessarily required new application images | When does a correction actually require rebuilding the application? | Not started |
| 13 | Test changes altered controller identity | Which changes should invalidate which evidence? | Not started |
| 14 | AWS fixtures missed real response shapes | Why did simulated success fail to predict real provider behaviour? | Not started |
| 15 | Private ECR endpoint dependency missed | Why could a task have permissions but still fail to download its image? | Not started |
| 16 | PostgreSQL authentication and permission assumptions wrong | How do administrator access, runtime login and database permissions differ? | Not started |
| 17 | Historical proof treated as a fresh observation | Which facts must be checked again, and which should remain valid history? | Not started |
| 18 | Interruption recovery designed piecemeal | How should execution resume without repeating an uncertain operation? | Not started |
| 19 | Collector could not combine legitimate evidence | How should evidence from different images, tasks and controllers fit together? | Not started |
| 20 | Controller consumed its readiness window | Why did successful readiness evidence expire before it could be used? | Not started |
| 21 | Failures investigated and fixed too serially | How should one failure trigger a bounded review of related consumers? | Not started |
| 22 | Excessive feature-specific deployment machinery | What should be shared platform tooling rather than copied per feature? | Not started |
| 23 | Fast verification loop not delivered | When should focused tests, integration checks and live proof run? | Not started |
| 24 | Fixtures did not survive the accepted state | Why did accepting a real release break temporary test repositories? | Not started |
| 25 | Related fixture copy sites missed during correction | How could the same defect have been found and fixed together? | Not started |
| 26 | Changed test left its diagnostic review stale | What is that review protecting, and why was it missed? | Not started |
| 27 | Failed checks retained insufficient failure detail | What information should survive a failure without exposing sensitive data? | Not started |
| 28 | Credential lifetime poorly planned | What expires, what can refresh, and what requires a new sign-in? | Not started |
| 29 | Continuation relied too heavily on the assistant | What should one durable resume command remember and show? | Not started |
| 30 | Already-authorised work prompted repeated approvals | How should existing authority be distinguished from genuinely new scope? | Not started |
| 31 | Remaining-work explanations were unreliable | What evidence is needed to give a trustworthy progress update? | Not started |
| 32 | A gate was reported passed before it finished | What constitutes an actual terminal success result? | Not started |
| 33 | Avoidable local execution mistakes | Which checks prevent wrong paths, wrong journals and misleading output? | Not started |
| 34 | Coordination burden transferred back to you | What should the agent own without making you manage every continuation? | Not started |

## Question log

Add one entry for each question you ask, preserving your wording. Cross-topic
questions can reference several lessons. Status may be Open, Answered awaiting
your confirmation, Resolved, or Reopened.

### L01 Q01 Why the PostgreSQL route was not sufficient

- Asked on: 2026-11-14.
- Lesson: 1; related lessons 7–20 and 22.
- Your question: “why was the route we used for our postgresql deployment not
  sufficient for the feature deployment?”
- Status: Answered awaiting your confirmation.

The prior route had already proved much more than creating a database. Its
accepted evidence includes migration, effective runtime privileges, server
replacement and readback, credential revocation/recovery, rollback, and isolated
database restoration/cleanup. It would be wrong to explain the difference as
“we only had a database before.”

However, a working route for a named workload is not automatically a reusable
release tool. The existing preparation script explicitly selects the
`core-server-persistence` stack, the `core-server` image repository, and that
specific candidate/package/program. Its receipts also identify that workload.
Those identities correctly prevent another feature from claiming its proof,
but the execution machinery was not sufficiently separated from them to make
another workload straightforward to configure.

The approved feature plan deliberately preserved the accepted baseline rather
than mounting test-entity into its image. The isolated feature therefore needed
its own application package, entrypoint, schema migration, database identities,
permissions and actual feature behaviour checks. It reused the target foundation,
existing PostgreSQL adapter, migration runner and Core helpers. The old release's
success could not prove the new package or new grants automatically worked.

My error was not that new feature-specific evidence was required. It was failing
to distinguish those necessary additions from common deployment/recovery logic
that should have been reusable. I then discovered gaps in that reuse during the
live run and accumulated another workload-specific controller. The earlier
success proved its workload; we had not established repeatability across workloads.

Evidence:

- [Earlier PostgreSQL accepted proof set](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/accepted-release.yml),
  including the `provider_observation.proofs` entries. This is historical proof, not a new live observation.
- [Current baseline release reference](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/current-accepted-release.yml).
- [Fixed workload selection in preparation](../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py),
  especially `STACK`, `REPOSITORY`, `EXPECTED` and scope-specific contract paths.
- [Feature plan](../../../.agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md),
  especially Authority and boundaries, Implementation and consumer inventory,
  and Required feature proof.

Remaining uncertainty: this comparison does not quantify the exact fraction
of implementation that could have been reused unchanged. Follow-up questions
and your confirmation remain pending; no corrective implementation is authorised
merely by this explanation.

### L01 Q02 Whether the next feature will hit the same problems

- Asked on: 2026-11-14.
- Lesson: 1; related lessons 18, 21–25 and 29.
- Your question: “and are we going to run into the same issues with the next feature?”
- Status: Answered awaiting your confirmation.
- Related proposal: D01 below.

There is still a real risk of similar friction. Known defects were corrected
for the accepted entity-smoke path, but its acceptance does not demonstrate a
generic, fast or unattended release route for the next feature. Some bindings
are intentionally feature-specific, and historical recovery exceptions are
specific to this run. A new image repository or workload identity also needs its
own correct access configuration; an allowlist fix for entity-smoke does not
automatically grant a future repository access.

For another feature using the same private runtime and PostgreSQL pattern, I
would expect feature code, schema changes, configuration and behaviour tests to
change. I would not expect a new deployment state machine, acceptance mechanism
or repeated repair of shared recovery rules. That is a proposed reuse standard,
not a capability demonstrated by this first feature's success.

Evidence: the [retrospective](../../../commitLogs/2026/nov/06/2026-11-06-17-07-new-chat-session/README.md)
explicitly records controller/test identity coupling, incident-specific recovery
code, expensive verification and the absence of a clean unattended repeat.
Whether a second workload can complete through the same machinery without
controller edits remains unproved. No precise duration guarantee is justified.
Your follow-ups and confirmation remain pending.

When an answer changes, retain a short correction note rather than silently
rewriting the history. Do not invent a user question to fill this section.

## Lesson takeaways

None recorded yet. After each discussion, add:

```text
Lesson:
What happened and why:
What should have happened:
One-sentence takeaway:
Question IDs still open:
Ready to move on: only record after your confirmation
```

## Decisions and possible repo changes

No new remediation decisions or implementation tasks have been agreed through
this lesson plan. Learning about a fix is separate from deciding to implement it.

- **D01 — Proposed, not agreed or implemented:** before describing the route as
  reusable, demonstrate a second differently named feature using the same private
  runtime/PostgreSQL pattern through the same release machinery. Feature code,
  migrations, declared configuration and feature tests may change; common
  controller code should not require feature-specific edits. Include interrupted
  resumption and record actual timings. A missing configuration value is different
  from having to patch the delivery engine. Linked question: L01-Q02.

For any proposed change, record its ID, linked lesson/question, proposal,
your decision, affected repo area, implementation status and verification evidence.
Keep **Proposed**, **Agreed**, **Implemented** and **Verified** distinct. Any
existing fix discussed in a lesson needs its source evidence before being called
implemented or verified. An explanation alone is not evidence of a fix.

## Lesson 1 preparation

### Learning outcome

By the end of this discussion, you should be able to distinguish working feature
code from a complete release path and identify the missing connection in a
release claim. The optional extension applies the same distinction to a future
feature; it does not introduce lesson 2 before you are ready.

### Source story

The feature had local implementation and tests, but packaging was missing its
compiler mapping and runtime shim. Later, the acceptance collector generated
files that promotion rejected. These were different breaks in the same route
from source code to accepted deployment. See the source retrospective, points
1 and 2. We will use these as examples, not unpack all their technical details
at once.

### Worked example

Incomplete release claim: “The feature tests pass, so the feature is ready to
release.” This only establishes what those tests actually exercised.

More complete claim: “We know how this exact source becomes a runnable package,
how that package reaches AWS, how the service gets its database access, how we
check its behaviour, and how the final evidence is accepted. Each connection has
an owner and an executable check; unproved connections are still outstanding.”

The missing idea is the connection between stages. Writing down the stages does
not prove those connections work, and a successful release does not by itself
prove that the next release will be fast or unattended.

### Optional 30 minute core

These timings are a facilitation guide, not a timer imposed on our chat.

| Time | Discussion | My role | Your role |
| --- | --- | --- | --- |
| 0–3 minutes | What does “released” mean here? | Explain the distinction between code working locally and a feature accepted on AWS. | Describe what result you expected. |
| 3–8 minutes | The actual incident | Show the packaging gap and acceptance deadlock from the retrospective. | Ask about any unfamiliar word or missing step. |
| 8–13 minutes | The release path | Walk through code, package, deployment, runtime behaviour and acceptance in plain language. | Point out which connections are unclear. |
| 13–20 minutes | Worked example | Compare the two release claims above and their evidence. | Ask what each claim lets us conclude. |
| 20–27 minutes | Apply the distinction | Offer the activity below, or use this time for your questions. | Identify a missing connection or continue questions. |
| 27–30 minutes | Debrief | Record the takeaway and unanswered questions. | Decide whether to continue this lesson or move on. |

### Optional 50 minute extension

Add 20 minutes to the same lesson: eight minutes examining one connection in
more detail, seven minutes applying it to a future feature, and five minutes
recording the questions and evidence that would be needed. Do not use the
extension to rush into another mistake.

### Activity and debrief

Optional activity: suppose our local feature test passes but the image does not
include a required runtime module. What has passed, what remains unproved, and
where should that gap have been discovered? This is a simplified exercise based
on the recorded packaging incident, not a new observation about the current repo.

Listen for: the local behaviour tested may be correct, but the packaged runtime
has not been shown to work. Packaging needs its own connected check. The answer
is not “run every possible test after every edit” or “remove the safety checks.”

I will say: “I should have checked this connection before relying on local
success as evidence that release was ready.” I will show the two claims above,
ask which evidence is missing, and clarify the distinction without turning the
discussion into a quiz. If the explanation does not click, I will use a smaller
repo example and record the remaining question.

## Sources and teaching notes

- Primary sequence: the assistant's 34-item mistake list immediately preceding
  this request. Its numbering is preserved above.
- Incident evidence: [deployment retrospective and accepted result](../../../commitLogs/2026/nov/06/2026-11-06-17-07-new-chat-session/README.md).
- Supporting checkpoints: `f3b6afbd` retains accepted evidence, fixture repairs
  and the retrospective; `eecf0c50` records final verification bookkeeping.
- Education workflow: [create educational resource](../../../.agentic/education/workflows/create-educational-resource.md).
- Shape adapted from the [lesson template](../../../.agentic/education/templates/lesson-plan.md)
  and [structure profile](../../../.agentic/education/profiles/structure-profile.md).
- Relevant teaching principles: [one idea at a time and concrete examples](../../../.agentic/education/references/teaching-principles.md).
- Audience: you, reviewing this repo, with no assumed AWS or deployment expertise.
  The [audience profile](../../../.agentic/education/profiles/audience-profile.md)
  informs plain-language orientation, not assumptions about your personality.
- Voice and humor: direct, accountable explanation; no jokes or imitation of your voice.
- Adaptation: this is a private, question-led series, not a public article or an
  exam. For a technical deep dive, inspect the relevant code when that lesson is
  reached; for a shorter discussion, keep the example and questions and omit timings.

## Review and revision notes

- Specificity: lesson 1 uses the recorded packaging gap and acceptance deadlock;
  the roadmap preserves all 34 incidents rather than substituting a generic course.
- Audience and voice: explain terms before using them, keep responsibility with
  me, and do not treat your questions as evidence that you caused the problems.
- Teaching: one main idea per discussion, a worked example before abstraction,
  an optional activity, and a standalone core with a deeper optional extension.
- AI wording audit: no promises that this plan itself fixes deployment, no claims
  of understanding on your behalf, and no invented answers or confirmed decisions.
- Initial revision, 2026-11-14: created the roadmap and empty tracking sections.
  Lesson 1 is prepared, not delivered or marked reviewed. Later lessons will be
  expanded when reached, using your questions rather than prewritten lectures.
- Discussion update, 2026-11-14: began lesson 1 and recorded L01-Q01 and L01-Q02.
  Answers await your confirmation; no lesson is marked reviewed and no proposed
  engineering work is approved. The earlier PostgreSQL proof is explicitly
  distinguished from reusable deployment machinery and new feature proof.
