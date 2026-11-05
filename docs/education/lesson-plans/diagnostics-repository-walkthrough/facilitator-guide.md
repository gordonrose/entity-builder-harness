<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.facilitator
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Provide source-backed patient teaching and progress rules for every folder lesson.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# How we will work through the course

[Course start](README.md)

## Purpose and audience

The learner owns this repository and wants to understand it, not memorize diagnostic names. Start from a concrete responsibility and its failure before introducing a pattern. Explain a term when first needed. “A callback we invoke” is usually clearer than an unexplained “boundary port.”

Each folder lesson has a worked example, source links and a separate before/after/why entry for every changed file. The shared timing below avoids copying a long identical workshop template into 187 documents. A folder with many files takes several meetings; the timebox covers a coherent example, not a claim that all its files have been taught.

## 30-minute core

| Time | What I do | What you do |
| --- | --- | --- |
| 0–3 min | State the folder's real responsibility and show its concrete failure example. | Predict what we can and cannot know. |
| 3–8 min | Show the old outcome and the baseline/source comparison for one file. | Explain which useful distinction was lost. |
| 8–13 min | Follow the actual guard/call and the allowed new detail. Explain the first necessary term. | Point to the evidence behind each claimed fact. |
| 13–20 min | Trace that observation to its real consumer or selected reporter/reader. | Identify who owns meaning versus wiring. |
| 20–27 min | Change one condition conceptually: missing vs unreadable, rejected vs uncertain, or reporting unavailable. | Predict the outcome, privacy boundary and test that should distinguish it. |
| 27–30 min | Ask for a plain-language explanation and record unresolved questions. | Explain the before/after/why without code in front of you. |

## 50-minute extension

| Time | Extension | Expected output |
| --- | --- | --- |
| 30–38 min | Compare remaining file entries in the same responsibility. | Mark individually discussed files, not the whole folder automatically. |
| 38–45 min | Inspect one rejecting and one successful/counterexample assertion. | Explain why weakening the implementation would make the intended test fail. |
| 45–50 min | Follow one neighboring folder dependency and summarize the handoff. | Name the known fact, remaining uncertainty and next permitted investigation. |

## Questions for every file

1. What does it do when diagnostics are not involved? For a schema/test/doc, what does it constrain or prove instead of performing work?
2. What was already present at the baseline? Is this file new, or is an existing operation being observed more precisely?
3. What exact condition/call supports the diagnostic? A broad catch does not establish a specific cause.
4. What is included, and which values stay private? Check logical names, counts and positions separately from user/provider values.
5. Where does the result go next? Does a wrapper preserve it? Does a reader validate the same versioned meaning?
6. Does reporting preserve the old return/throw, call order, retry and cleanup behavior? Name any explicitly approved compatibility change.
7. Which actual assertion checks that? Which stage remains unproved?

## Reading before and after safely

The file checklist names the baseline. A read-only comparison for an existing file is:

```sh
git diff d94da2b9401d3abcf86618b5d497e9b93903490a -- path/to/file
git show d94da2b9401d3abcf86618b5d497e9b93903490a:path/to/file
```

These are patterns: replace path/to/file with a listed path and use the recorded October 27 worktree. Do not run them in a different checkout. For an added untracked file, git diff alone will not show its contents; open the current source link. git show failing because a file was absent is not proof the surrounding feature was absent.

No checkout, reset, installation, deployment, administration, recovery or cloud command is part of a lesson. Source reading and reasoning come first. If we later want an executed experiment, agree its exact scope and authority separately.

## Facilitator script and answer guide

Say: “Let's first ask what this operation was trying to do. Now, where exactly did it stop? What did it actually learn before it stopped?” Show the specific condition or call, then the corresponding record constructor and assertion. Ask for a prediction before showing the answer.

A strong answer sounds like: “Validation rejected this logical field, so the provider call was not reached,” or “The call was invoked but did not return; its external effect is not established.” A weak answer jumps from an exception to “the database is down” without evidence. Ask which additional observation would support that claim; do not treat uncertainty as the learner's mistake.

For a pure constructor/test/doc, stop at its actual boundary. Do not invent a deployed service just to make a vertical diagram longer. For a generated export, trace its source, exporter and reader instead of pretending the JSON runs a workload.

## Worksheet and progress

Use [the learning notes](learning-notes.md) with one row per question or file group. Check the corresponding [file entry](file-index.md) only after discussion. Mark a folder complete only when all its file entries have been covered and its explain-back question answered.

If the source disagrees with an annotation, record the exact path, symbol and disagreement. The annotation is a teaching aid, not authority to change code or dismiss an unexpected behavior. If source hashes have changed since the course snapshot, reconcile that lesson before using its before/after explanation.

## Teaching audits

**Specificity:** each lesson names an actual folder and all its actual changed files, includes current reading anchors and links to the baseline/proof boundary. Source-backed review notes support explanation but are not independent proof that implementation is perfect.

**Audience:** assume intelligence, explain terminology, invite questions without rushing, and wait for an explicit “next” before changing topics during our guided conversation.

**Learning:** require prediction, source inspection and retrieval. The 30-minute core stands alone; the extension deepens the same responsibility rather than starting unrelated capability work.

**Writing:** avoid claims that every failure is covered, that the whole repo was rebuilt, or that more diagnostics necessarily means more truth. Explain the particular improvement and its limits.

## Sources for the teaching method

The structure follows [the repo lesson-plan template](../../../../.agentic/education/templates/lesson-plan.md), [teaching principles](../../../../.agentic/education/references/teaching-principles.md), and the [audience](../../../../.agentic/education/profiles/audience-profile.md), [voice](../../../../.agentic/education/profiles/voice-profile.md) and [structure](../../../../.agentic/education/profiles/structure-profile.md) profiles. This is an internal source-based course, not a public article or a ChatGPT Page.
