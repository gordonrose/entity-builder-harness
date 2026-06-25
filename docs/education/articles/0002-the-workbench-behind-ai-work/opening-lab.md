<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0002-the-workbench-behind-ai-work.opening-lab
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Article Opening Lab.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Article Opening Lab

## Metadata

- Article: AI Work Needs A Workbench
- Source packet: `source-packet.md`
- Editor brief: `editor-brief.md`
- Writer: Codex
- Editor decision: Candidate 1 approved

## Opening Candidate 1: Human-Consequence Opening

I had the faintly unpleasant experience of being told two true things at once.

The chats had been committed. Git still showed about 15 staged changes.

This is not a dramatic problem in the cinematic sense. Nobody kicked down a
door. No database caught fire. But if you have ever tried to work out whether a
piece of AI-assisted work is finished, duplicated, stale, or sitting in the
wrong place, you will recognize the feeling. The assistant says the work is
done. The workspace quietly disagrees.

### Test

- Stakes by line seven: yes, work may be finished or not and the workspace contradicts the claim.
- Cold reader can retell: yes.
- Human consequence before vocabulary: yes.
- Weakness: "about 15 staged changes" may need immediate translation for non-Git readers.

Decision: approved.

## Opening Candidate 2: Scene-First Opening

The root checkout was supposed to be clean.

I had a set of AI chats, each with its own little record of work, and those
chats had been committed. Then I looked at the repository and saw roughly 15
changes still staged, waiting as if nobody had finished anything at all.

For a few seconds, the whole workflow sat in that awkward gap between "done" and
"apparently not."

### Test

- Stakes by line seven: yes.
- Cold reader can retell: yes, but needs "root checkout" translation.
- Human consequence before vocabulary: partial.
- Weakness: starts with Git vocabulary.

Decision: usable fallback, not selected.

## Opening Candidate 3: Mechanism-First Opening

An AI chat that can edit files, run commands, and commit work needs an isolated
worktree, a branch, a session log, and a governed convergence path.

That is the clean version.

I learned it by looking at a checkout that still had about 15 staged changes
after the chats had supposedly been committed.

### Test

- Stakes by line seven: delayed.
- Cold reader can retell: no, too much internal vocabulary.
- Human consequence before vocabulary: no.
- Weakness: proves why mechanism-first is blocked.

Decision: blocked.

## Approved Opening

Use Candidate 1.
