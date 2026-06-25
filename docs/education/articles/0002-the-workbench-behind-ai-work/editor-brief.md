<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0002-the-workbench-behind-ai-work.editor-brief
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Article Editor Brief.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Article Editor Brief

## Metadata

- Candidate title: AI Work Needs A Workbench
- Source packet: `source-packet.md`
- Reader-world research packet: `reader-world-research-packet.md`
- Scene cards:
  - `scene-cards/001-staged-changes-after-committed-chats.md`
  - `scene-cards/002-coding-agent-work-actor.md`
  - `scene-cards/003-missing-governance-stop.md`
  - `scene-cards/004-preflight-before-promotion.md`
  - `scene-cards/005-clipboard-handoff-failure.md`
- Audience: hype-adjacent, non-technical or lightly technical AI readers
- Draft readiness: approved for opening lab and draft

## Material Sufficiency

The source packet is sufficient.

The article has a real source scene, public reader-world bridge, visible
artifacts, a human actor under pressure, and a fresh thesis. It does not need a
hypothetical bridge.

## Article Premise

As AI agents move from suggestion boxes into work actors, the next advantage is
not simply giving them more autonomy. It is giving them a workbench: owned
space, visible state, permission boundaries, recorded evidence, and a governed
handoff back to the human-controlled baseline.

## Central Story

The author thought the problem was whether chat work had been committed. The
root checkout still showed about 15 staged changes, so the social claim "the
chats are committed" collided with the tool state.

That awkward Git moment forced the real design change. Each chat became a
developer-like work actor with its own branch, worktree, index, and session log.
Then the harness grew the process around that model: missing-governance stop
condition, no stash by default, preflight refresh, local convergence, and
resilient chat-start handoff.

## Source Scene Inventory

| Scene | Use | Reason |
|---|---|---|
| Staged changes after committed chats | Opening | Concrete, author-owned, human pressure |
| GitHub coding agent virtual machine | Reader-world bridge | Shows public AI agents as work actors |
| Replit database deletion | Boundary warning | Shows cost of agent acting in wrong environment |
| Missing governance stop | Moral turn | Distinguishes capability from authority |
| Preflight worktree | Practical mechanism | Shows how the harness makes risky actions observable |
| Clipboard fallback | Late supporting beat | Distinguishes core setup from convenience handoff |

## Reader Tension

The reader wants AI agents to do more work. They may already like the idea of
assigning tasks and getting a finished artifact back. The article should make
them feel more sophisticated: the impressive version of autonomy is the one
where state and handoff are clear.

## Real Stakes And Downside

False completion. Work looks done before anyone can safely say where it
happened, what changed, what remains dirty, and who is allowed to merge it.

## Selected Thesis

AI work needs a workbench: once a chat can act like a worker, it needs owned
space, visible state, permission boundaries, and a handoff path.

## Rejected Weaker Theses

- Git worktrees are useful for AI.
- Agentic workflows need governance.
- Better process makes better AI work.
- AI coding is risky.

## Opening Scene Candidates

### Candidate A: Staged Changes After Committed Chats

Approved.

The author looks at the checkout and sees staged changes after the chats have
supposedly been committed. This gives the reader a concrete contradiction
before any vocabulary appears.

### Candidate B: Replit Database Deletion

Use as supporting bridge, not opening.

It is vivid, but it would pull the article toward catastrophe commentary. The
article is better when it opens from a smaller working contradiction and then
widens.

## Nut Graf

When an AI chat can change files, run commands, create branches, and hand work
back, it is no longer just a conversation. It is a work actor. And work actors
need a workbench: a place to stand, a record of what they touched, rules about
what they may do, and a clear path for handing finished work back.

## Terms To Teach

| Term | Plain-language need before term appears | Treatment |
|---|---|---|
| branch | Reader understands parallel versions of work | Explain as a line of work |
| worktree | Reader understands a worker needs a physical place to work | Explain as separate checkout |
| index | Reader sees staged residue contradiction | Mention once, translate as local preparation state |
| local convergence | Reader understands handoff into accepted baseline | Translate as merge lane |
| stash | Reader understands tempting broad cleanup | Explain as shared shelf that is too easy to contaminate |

## Quality Rubric Scores

| Category | Score | Note |
|---|---:|---|
| Source material density | 5 | Strong logs, visible artifacts, public bridge |
| Artifact availability | 5 | Public artifacts linked or local |
| Opening scene | 4 | Concrete, could use exact command output if available |
| Felt stakes | 4 | False completion is clear |
| Reader orientation | 4 | Needs careful vocabulary delay |
| Reader-world setting | 5 | GitHub, Replit, PR studies |
| Line 30 gate | 4 | Achievable if public bridge arrives early |
| Thesis freshness | 5 | Stronger than generic AI governance |
| Structure and tension chain | 5 | Scene -> bridge -> workbench -> stop -> handoff |
| Voice match | 5 | Fits practical authority and dry precision |
| Sentence craft and specificity | 4 | To verify after draft |
| Ending | 4 | Should land on workbench/worker consequence |

## Draft Readiness Decision

Approved for opening lab and draft.
