<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0002-the-workbench-behind-ai-work.source-packet
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Article Source Packet.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Article Source Packet

## Metadata

- Working title: AI Work Needs A Workbench
- Source window: 2026-06-16 through 2026-06-18 harness sessions, plus public reader-world research gathered on 2026-06-19
- Source logs or artifacts:
  - `content-mining-report.md`
  - `reader-world-research-packet.md`
  - `commitLogs/2026/jun/16/2026-06-16-14-19-local-chat-worktree-strategy/README.md`
  - `commitLogs/2026/jun/16/2026-06-16-18-59-missing-governance-stop-condition/README.md`
  - `commitLogs/2026/jun/16/2026-06-16-22-23-main-refresh-recovery-design/README.md`
  - `commitLogs/2026/jun/16/2026-06-16-22-32-govern-local-convergence/README.md`
  - `commitLogs/2026/jun/18/2026-06-18-16-11-clipboard-copy-fallback/README.md`
- Reader-world research packet: `reader-world-research-packet.md`
- Requested audience: hype-adjacent, non-technical or lightly technical AI readers
- Reporter: Codex
- Status: sufficient

## Core Incident

The author had multiple AI-assisted chats recorded as committed, but the root
checkout still showed about 15 staged changes. The question was simple: if the
chats had been committed, why did the workspace still look unfinished?

That exposed the real problem. The harness had isolated commit actions, but it
had not yet fully separated the chat actor's workspace from the root workspace.
Branch movement, root index state, session evidence, and local integration were
being mixed together.

The repair was to treat each chat as a work actor with its own branch,
chat-owned worktree, index, and session log, while treating the root checkout as
a local integration console. Later sessions added the governance around that
model: no improvised recovery, no default stash, preflight refresh, local
convergence verification, and resilient chat-start handoff.

## Human Protagonist

- Who wanted something? The author, building a harness for reliable AI-assisted work.
- What did they want? To know whether AI chat work had actually been committed and handed off safely.
- What pressure were they under? Parallel chats could make the repo look clean from one angle and dirty from another.
- What would failure cost? Work could be duplicated, overwritten, committed from the wrong place, or merged without reliable evidence.

## Exact Moment

The revealing moment is recorded in the local-chat-worktree session:

- Initial intent: "i have about 15 staged changes -are they not committed yet, given all my chats are committed?"
- Issue: "The active root worktree had stale staged entries after commits made from an isolated worktree advanced the same chat branch."
- Decision: "Treat the root repository worktree as a local integration console, not as the default place for chat task writes."

The author thought the question was whether the commits had happened. The real
question was where the work actor was allowed to stand.

## Visible Artifacts

- Root checkout staged entries after chat commits.
- Chat branch.
- Chat-owned worktree under `/tmp/agentic-chat-worktrees/...`.
- Session log under `commitLogs/`.
- `scripts/00.chat/worktree/check-write-location/script.sh`.
- `.agentic/00.chat/workflows/chat-refresh-from-main.md`.
- `scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh`.
- Main-refresh preflight worktree under `/tmp/agentic-main-refresh-preflight/...`.
- Clipboard failure log showing `clip.exe` failure after core artifacts existed.
- Public coding-agent artifacts: virtual machine, cloned repo, draft pull request, session logs, review tag.

## Artifact Availability

- Local harness artifacts: available in this repository.
- The Verge GitHub Copilot coding agent article: public, direct URL in reader-world packet.
- Business Insider Replit article: public, direct URL in reader-world packet.
- AIDev arXiv preprint: public, direct URL in reader-world packet.
- Ehsani et al. failed agentic PR preprint: public, direct URL in reader-world packet.

## Reader-World Bridge

The bridge is not "Git worktrees are useful." The bridge is that AI coding
agents are becoming work actors in public tools. GitHub's agent can be assigned
a task, boot a virtual machine, clone a repository, save changes, record
reasoning in session logs, and tag the developer for review. Research on
agent-authored pull requests now treats those contributions as a large body of
software work. Replit's database incident shows the cost of giving a coding
agent powerful access without strong enough boundaries.

The author's harness is a small, local version of the same problem: when the AI
can act, the environment has to say where it acts, what it touched, what it is
allowed to do next, and how the work returns to the human-controlled baseline.

## Stakes

The downside is false completion.

If ignored, a user can believe work is finished because a chat says it is, while
the repository still contains staged residue, branch divergence, dirty
bookkeeping, or unreviewed changes. At larger scale, the same pattern becomes
AI-generated pull requests that reviewers cannot easily reason about, or
autonomous coding tools acting in the wrong environment.

## Counterpoint Or Objection

"Isn't this just over-engineering around a personal workflow?"

The article answers that the personal workflow is the smallest place where the
agentic work problem becomes visible. If one person running parallel chats needs
workspace ownership, handoff, and stop rules, teams using cloud coding agents
will need those things even more.

## Surprise Or Turn

The surprise is that the solution was not to make the assistant smarter. It was
to give it a workbench.

## Only-I-Could-Write-This Details

- The source problem began with "about 15 staged changes" after committed chats.
- The root checkout became "a local integration console."
- Each chat became a "local developer-like work actor" with its own branch,
  worktree, index, and session log.
- Missing governance became a stop condition after an ungoverned stash-based
  recovery.
- Stash was excluded from default main refresh because the stash stack is shared
  across repo worktrees.
- Main refresh moved to checkpoint, classifier, preflight worktree, and
  promotion.
- Clipboard copy became a best-effort convenience after WSL `clip.exe` failed
  even though branch, worktree, and session log already existed.

## Scene Cards

- `scene-cards/001-staged-changes-after-committed-chats.md`
- `scene-cards/002-coding-agent-work-actor.md`
- `scene-cards/003-missing-governance-stop.md`
- `scene-cards/004-preflight-before-promotion.md`
- `scene-cards/005-clipboard-handoff-failure.md`

## Example Ledger Check

Checked `docs/education/articles/example-ledger.md`.

No major anecdote from the prior article is reused as opening, main evidence,
or primary reader bridge.

## Quality Gate

- Is there enough material for a short magazine-standard article? Yes.
- Would the piece need an invented opening or generic bridge to work? No.
- Does the material support a fresh thesis? Yes.
- Are named public artifacts linked or marked? Yes.
- Can a cold reader understand the world, object under pressure, AI temptation,
  downside, and personal relevance by roughly line 30? Yes.

Decision: sufficient.
