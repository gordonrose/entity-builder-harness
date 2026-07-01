<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0002-the-workbench-behind-ai-work.writer-notes
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Writer Notes.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Writer Notes

## Source Packet

Used `source-packet.md`.

## Reader-World Research Packet

Used `reader-world-research-packet.md`.

## Opening Lab

Used approved Candidate 1 from `opening-lab.md`.

## Source Scene Used

The opening uses the author-owned scene where committed chats still left about
15 staged changes visible in the root checkout.

## Selected Thesis Followed

AI work needs a workbench: once a chat can act like a worker, it needs owned
space, visible state, permission boundaries, and a handoff path.

## Reader-World Examples Used

- GitHub Copilot coding agent task assignment, VM, cloned repo, session logs,
  and review handoff.
- Replit AI coding agent database deletion as a boundary failure.
- Agent-authored pull request research as scale/context.
- Failed agentic PR research as review/handoff complication.

## Examples Avoided

- KPMG AI report.
- Air Canada chatbot.
- meeting-recap examples.
- fake legal citations.

These are ledgered for article 0001 and are not needed here.

## Artifact Availability Notes

Public sources are linked in `reader-world-research-packet.md`. The article
refers to them through plain descriptions and does not imply access to private
or unavailable artifacts.

## Terms Translated Or Delayed

- `branch`: introduced as a line of work.
- `worktree`: introduced as a separate checkout where files live.
- `index`: translated as local preparation state and used sparingly.
- `local convergence`: translated as bringing finished work back into main.
- `stash`: explained as shared repo machinery, not assumed knowledge.

## Self-Critique Against Editor Brief

- Third draft applies user correction that the previous version drifted too far
  into engineering-workflow exposition.
- Recentered thesis on "AI output at the speed of human accountability":
  balancing content/work generation speed with control and inspectability.
- Rewrote the workbench transition to clarify that each chat is not naturally
  its own accountable individual; the harness has to create that separateness
  upstream through branch, worktree, session log, and write guards.
- Public examples now demonstrate output outrunning boundaries and review
  capacity, rather than becoming the topic.
- Workbench is framed as the counterweight that preserves speed while keeping
  accountability possible.
- Second draft applies user feedback from `AI needs a workbench feedback.docx`.
- Opening now translates staged changes immediately and centers human
  accountability: the assistant is not accountable, the user is.
- Added exposition on normal engineering team flow: local branch, `origin`,
  `main`, pull request, review, and convergence.
- Made the workbench idea grow from chats becoming local developer-like actors
  rather than stating it as an abstract frame.
- Explained `preprint` in the article body.
- Added cost and benchmark framing around review time, failed checks, duplicate
  work, and handoff reconstruction.
- Public reader-world bridge appears early enough to prevent an internal-only
  article.
- Article preserves the stronger workbench arc rather than narrowing to a Git
  tutorial.
- The Replit example is used as boundary evidence, not sensational opening.
- Voice has practical authority and some dry bluntness.
- Residual risk: the phrase "speed of human accountability" is strong enough
  that title and packet metadata should be reconsidered if this draft becomes
  the selected version.
